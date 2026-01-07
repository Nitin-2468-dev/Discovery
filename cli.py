#!/usr/bin/env python
"""
cli.py

Probe CLI: Command-line interface for the deep research engine.

Commands:
- init: Initialize the database
- add-entity: Manually add an entity
- show: Display entity information
- domains: Show high-yield domains
- summary: Display map statistics
"""

import click
import sys
from pathlib import Path

# Add probe package to path
sys.path.insert(0, str(Path(__file__).parent))

from probe.core.schema import initialize_schema, validate_schema
from probe.core.map import Map, Entity, Document, Edge


@click.group()
def cli():
    """Probe: A deep research engine for discovering buried information."""
    pass


@cli.command()
@click.option('--db', default='probe.db', help='Database file path')
def init(db):
    """Initialize the knowledge map database."""
    click.echo(f"Initializing Probe database at {db}...")
    
    conn = initialize_schema(db)
    
    if validate_schema(conn):
        click.echo("✓ Database initialized successfully")
        
        # Show table count
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        click.echo(f"✓ Created {len(tables)} tables: {', '.join(tables)}")
    else:
        click.echo("✗ Database initialization failed", err=True)
        sys.exit(1)
    
    conn.close()


@cli.command()
@click.argument('entity_name')
@click.option('--type', 'entity_type', default='unknown', help='Entity type (engine, regulation, company, etc.)')
@click.option('--confidence', default=0.5, type=float, help='Confidence score (0.0-1.0)')
@click.option('--db', default='probe.db', help='Database file path')
def add_entity(entity_name, entity_type, confidence, db):
    """Manually add an entity to track."""
    m = Map(db)
    
    entity = Entity(
        id=None,
        name=entity_name,
        type=entity_type,
        confidence_score=confidence
    )
    
    entity_id = m.add_entity(entity)
    click.echo(f"✓ Added entity '{entity_name}' (ID: {entity_id}, Type: {entity_type})")
    
    m.close()


@cli.command()
@click.argument('entity_name')
@click.option('--db', default='probe.db', help='Database file path')
def show(entity_name, db):
    """Show what we know about an entity."""
    m = Map(db)
    
    entity = m.get_entity(entity_name)
    if not entity:
        click.echo(f"❌ No knowledge of '{entity_name}' yet.")
        click.echo(f"   Try: probe add-entity \"{entity_name}\"")
        m.close()
        return
    
    # Display entity info
    click.echo(f"\n📍 Entity: {entity.name}")
    click.echo(f"   Type: {entity.type or 'unknown'}")
    click.echo(f"   Confidence: {entity.confidence_score:.2f}")
    click.echo(f"   First seen: {entity.created_at}")
    click.echo(f"   Last seen: {entity.last_seen_at}")
    
    # Get linked documents
    docs = m.get_entity_documents(entity_name)
    if docs:
        click.echo(f"\n📄 Documents ({len(docs)}):")
        for doc in docs:
            click.echo(f"   • {doc.title}")
            click.echo(f"     Type: {doc.doc_type}")
            click.echo(f"     URL: {doc.url}")
            if doc.publication_date:
                click.echo(f"     Published: {doc.publication_date}")
    else:
        click.echo("\n📄 No documents found yet.")
    
    # Get related entities
    related = m.get_related_entities(entity_name)
    if related:
        click.echo(f"\n🔗 Related Entities ({len(related)}):")
        for rel in related:
            click.echo(f"   • {rel.name} ({rel.type or 'unknown'})")
    
    m.close()


@cli.command()
@click.option('--limit', default=10, type=int, help='Maximum domains to show')
@click.option('--min-pages', default=3, type=int, help='Minimum pages crawled')
@click.option('--db', default='probe.db', help='Database file path')
def domains(limit, min_pages, db):
    """Show high-yield domains."""
    m = Map(db)
    domains = m.get_high_yield_domains(limit=limit, min_pages=min_pages)
    
    if not domains:
        click.echo("No domains tracked yet.")
        click.echo(f"(Showing domains with at least {min_pages} pages crawled)")
        m.close()
        return
    
    click.echo(f"\n🌐 High-Yield Domains (min {min_pages} pages):\n")
    for d in domains:
        yield_pct = d.yield_score * 100
        click.echo(f"  {d.domain_name}")
        click.echo(f"    Yield: {yield_pct:.1f}% ({d.documents_found} docs / {d.pages_crawled} pages)")
        click.echo(f"    Trust: {d.trust_score:.2f}")
        if d.last_crawled_at:
            click.echo(f"    Last crawled: {d.last_crawled_at}")
        click.echo()
    
    m.close()


@cli.command()
@click.option('--db', default='probe.db', help='Database file path')
def summary(db):
    """Display map statistics."""
    m = Map(db)
    stats = m.get_map_summary()
    
    click.echo("\n📊 Probe Map Summary:\n")
    click.echo(f"  Entities:  {stats['entities']:>6}")
    click.echo(f"  Documents: {stats['documents']:>6}")
    click.echo(f"  Pages:     {stats['pages']:>6}")
    click.echo(f"  Domains:   {stats['domains']:>6}")
    click.echo(f"  Edges:     {stats['edges']:>6}")
    click.echo()
    
    # Show high-yield domains if any exist
    domains = m.get_high_yield_domains(limit=3, min_pages=1)
    if domains:
        click.echo("Top 3 Domains:")
        for d in domains:
            yield_pct = d.yield_score * 100
            click.echo(f"  • {d.domain_name} ({yield_pct:.0f}% yield)")
        click.echo()
    
    m.close()


@cli.command()
@click.argument('url')
@click.option('--ingest/--no-ingest', default=False, help='Persist fetched content into the Map')
@click.option('--db', default='probe.db', help='Database file path')
@click.option('--timeout', default=10, type=float, help='Request timeout in seconds')
@click.option('--max-retries', default=3, type=int, help='Maximum retry attempts for transient errors')
@click.option('--backoff-factor', default=0.5, type=float, help='Backoff factor in seconds')
def fetch_cmd(url, ingest, db, timeout, max_retries, backoff_factor):
    """Fetch a URL and optionally ingest into the Map."""
    click.echo(f"Fetching: {url}")
    res = None
    try:
        res = __import__('probe.crawl.fetcher', fromlist=['fetch']).fetch(
            url, timeout=timeout, max_retries=max_retries, backoff_factor=backoff_factor
        )
    except Exception as exc:
        click.echo(f"✗ Fetch failed: {exc}")
        raise

    click.echo(f"Status: {res.get('status_code')}, Type: {res.get('content_type')}")
    click.echo(f"Title: {res.get('title')}")
    click.echo(f"Links: {len(res.get('links', []))}")

    if ingest:
        m = Map(db)
        out = __import__('probe.crawl.ingest', fromlist=['ingest_fetch_result']).ingest_fetch_result(m, res)
        click.echo(f"Ingested: {out}")
        m.close()

@cli.command()
@click.argument('entity_name')
@click.argument('document_title')
@click.argument('document_url')
@click.option('--type', 'doc_type', default='manual', help='Document type')
@click.option('--hash', 'doc_hash', required=True, help='Content hash (SHA256)')
@click.option('--relation', default='mentions', help='Relation type')
@click.option('--db', default='probe.db', help='Database file path')
def link(entity_name, document_title, document_url, doc_type, doc_hash, relation, db):
    """Link an entity to a document."""
    m = Map(db)
    
    # Get or create entity
    entity = m.get_entity(entity_name)
    if not entity:
        click.echo(f"Creating entity '{entity_name}'...")
        entity = Entity(id=None, name=entity_name)
        entity_id = m.add_entity(entity)
        entity = m.get_entity(entity_name)
    
    # Extract domain from URL
    from urllib.parse import urlparse
    domain = urlparse(document_url).netloc
    
    # Create document
    doc = Document(
        id=None,
        title=document_title,
        doc_type=doc_type,
        hash=doc_hash,
        url=document_url,
        domain=domain
    )
    doc_id = m.add_document(doc)
    
    # Create edge
    edge = Edge(
        id=None,
        from_type='entity',
        from_id=entity.id,
        to_type='document',
        to_id=doc_id,
        relation=relation
    )
    edge_id = m.add_edge(edge)
    
    click.echo(f"✓ Linked '{entity_name}' → '{document_title}'")
    click.echo(f"  Relation: {relation}")
    click.echo(f"  Document ID: {doc_id}")
    click.echo(f"  Edge ID: {edge_id}")
    
    m.close()


@cli.group()
def seeds():
    """Seed related utilities (loader, runners)."""
    pass


@seeds.command(name="run")
@click.argument('file')
@click.option('--limit', default=10, type=int, help='Limit number of seeds to run')
@click.option('--ingest/--no-ingest', default=False, help='Persist fetched content into the Map')
@click.option('--db', default='probe.db', help='Database file path')
@click.option('--timeout', default=10, type=float, help='Request timeout in seconds')
@click.option('--max-retries', default=3, type=int, help='Maximum retry attempts')
@click.option('--backoff-factor', default=0.5, type=float, help='Backoff factor seconds')
@click.option('--summary-dir', default='run_reports', help='Directory to write CSV and logs')
@click.option('--no-log-failures', is_flag=True, default=False, help='Disable appending failed seeds to constraints.log')
def seeds_run(file, limit, ingest, db, timeout, max_retries, backoff_factor, summary_dir, no_log_failures):
    """Run seeds from a file using the fetcher and optionally ingest into the Map."""
    from probe.crawl.seed_loader import load_file, summarize
    from probe.crawl.reporting import write_csv_report, append_failure_log
    click.echo(f"Loading seeds from: {file}")
    urls = load_file(file)[:limit]
    click.echo(f"Loaded {len(urls)} seeds")
    click.echo("Summary:")
    s = summarize(urls)
    for d, c in s.items():
        click.echo(f"  {d}: {c}")

    successes = 0
    failures = 0
    rows = []

    m = None
    if ingest:
        m = Map(db)

    for u in urls:
        click.echo(f"Fetching: {u}")
        try:
            res = __import__('probe.crawl.fetcher', fromlist=['fetch']).fetch(
                u, timeout=timeout, max_retries=max_retries, backoff_factor=backoff_factor
            )

            domain = __import__('urllib.parse', fromlist=['urlparse']).urlparse(u).netloc
            # compute success robustly
            try:
                sc = int(res.get('status_code') or 0)
                success_flag = (sc >= 200 and sc < 400) and not bool(res.get('error'))
            except Exception:
                success_flag = False

            row = {
                'timestamp': __import__('datetime').datetime.now().isoformat(),
                'url': u,
                'domain': domain,
                'status_code': res.get('status_code') or 0,
                'success': 'True' if success_flag else 'False',
                'error_message': res.get('error') or '',
                'content_type': res.get('content_type') or '',
                'content_length': res.get('content_length') or 0,
                'fetch_duration_ms': res.get('fetch_duration_ms') or 0,
                'redirect_count': res.get('redirect_count') or 0,
                'final_url': res.get('final_url') or '',
                'link_count': res.get('link_count') or 0,
                'has_pdf_links': res.get('has_pdf_links') or False,
            }

            rows.append(row)

            if res.get('error'):
                click.echo(f"  ✗ {res.get('error')}")
                failures += 1
                if not no_log_failures:
                    append_failure_log(u, res.get('error'), file, f"cli seeds run {file} --limit {limit}")
            else:
                click.echo(f"  ✓ {res.get('status_code')} {res.get('content_type')}")
                successes += 1
                if ingest and m:
                    out = __import__('probe.crawl.ingest', fromlist=['ingest_fetch_result']).ingest_fetch_result(m, res)
                    click.echo(f"    Ingested: {out}")
        except Exception as exc:
            click.echo(f"  ✗ Exception: {exc}")
            failures += 1
            if not no_log_failures:
                append_failure_log(u, str(exc), file, f"cli seeds run {file} --limit {limit}")
            rows.append({
                'timestamp': __import__('datetime').datetime.now().isoformat(),
                'url': u,
                'domain': __import__('urllib.parse', fromlist=['urlparse']).urlparse(u).netloc,
                'status_code': 0,
                'success': False,
                'error_message': str(exc),
                'content_type': '',
                'content_length': 0,
                'fetch_duration_ms': 0,
                'redirect_count': 0,
                'final_url': '',
                'link_count': 0,
                'has_pdf_links': False,
            })

    if m:
        m.close()

    # Write CSV summary
    try:
        p = write_csv_report(file, rows, dir_path=Path(summary_dir))
        click.echo(f"Wrote summary CSV: {p}")
    except Exception as exc:
        click.echo(f"Warning: failed to write CSV summary: {exc}")

    click.echo(f"Done. Successes: {successes}. Failures: {failures}.")


@cli.command()
@click.argument('url')
@click.option('--timeout', default=10, type=float, help='Request timeout in seconds')
@click.option('--max-retries', default=1, type=int, help='Maximum retry attempts')
@click.option('--backoff-factor', default=0.5, type=float, help='Backoff factor seconds')
def health_check(url, timeout, max_retries, backoff_factor):
    """Lightweight health-check: fetch url and report basic status and extraction success."""
    click.echo(f"Health-check: {url}")
    res = __import__('probe.crawl.fetcher', fromlist=['fetch']).fetch(
        url, timeout=timeout, max_retries=max_retries, backoff_factor=backoff_factor
    )
    click.echo(f"Status: {res.get('status_code')}, Type: {res.get('content_type')}, Error: {res.get('error')}")
    if res.get('is_pdf'):
        click.echo(f"PDF pages: {res.get('metadata', {}).get('pages')}, text_len: {len(res.get('text',''))}")


if __name__ == "__main__":
    cli()