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
@click.option('--max-size', default=10000000, type=int, help='Max response size in bytes')
@click.option('--max-retries', default=3, type=int, help='Maximum retry attempts for transient errors')
@click.option('--backoff-factor', default=0.5, type=float, help='Backoff factor in seconds')
@click.option('--ignore-retry-after', is_flag=True, default=False, help='Ignore Retry-After headers and use backoff instead')
def fetch_cmd(url, ingest, db, timeout, max_size, max_retries, backoff_factor, ignore_retry_after):
    """Fetch a URL and optionally ingest into the Map."""
    click.echo(f"Fetching: {url}")
    res = None
    try:
        res = __import__('probe.crawl.fetcher', fromlist=['fetch']).fetch(
            url, timeout=timeout, max_size=max_size, max_retries=max_retries, backoff_factor=backoff_factor, honor_retry_after=(not ignore_retry_after)
        )
    except Exception as exc:
        click.echo(f"✗ Fetch failed: {exc}")
        raise

    if res.get('error'):
        click.echo(f"✗ {res.get('error')}")
        return

    click.echo(f"Status: {res.get('status_code')}, Type: {res.get('content_type')}")
    click.echo(f"Title: {res.get('title')}")
    click.echo(f"Links: {len(res.get('links', []))}")

    if ingest:
        m = Map(db)
        out = __import__('probe.crawl.ingest', fromlist=['ingest_fetch_result']).ingest_fetch_result(m, res)
        click.echo(f"Ingested: {out}")
        m.close()


@cli.command()
@click.argument('url', required=False)
@click.option('--from-db', 'from_db', default=None, type=int, help='Score an existing page by page_id from the DB')
@click.option('--persist/--no-persist', default=False, help='Persist scoring report to the DB')
@click.option('--db', default='probe.db', help='Database file path')
@click.option('--timeout', default=10, type=float, help='Request timeout in seconds')
@click.option('--max-size', default=10000000, type=int, help='Max response size in bytes')
@click.option('--max-retries', default=3, type=int, help='Maximum retry attempts for transient errors')
@click.option('--backoff-factor', default=0.5, type=float, help='Backoff factor in seconds')
@click.option('--keywords', default=None, help='Comma-separated keywords to use for keyword density scoring')
def score(url, from_db, persist, db, timeout, max_size, max_retries, backoff_factor, keywords):
    """Fetch a URL or score an existing page in DB and run the RelevanceScorer.

    If `--from-db PAGE_ID` is provided, the page is loaded from the DB and scored using stored text/metadata.
    Otherwise `url` must be provided and will be fetched live.
    """
    if from_db is None and not url:
        click.echo("✗ Provide a URL or use --from-db PAGE_ID")
        return

    click.echo(f"Scoring: {url or f'page_id={from_db}'}")

    m = Map(db)
    page = None
    fetched_url = url

    if from_db is not None:
        row = m.get_page_by_id(from_db)
        if not row:
            click.echo(f"✗ No page with id {from_db}")
            m.close()
            return
        fetched_url = row['url']
        # Extract text and boilerplate from metadata if available
        import json
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        page = {
            'text': metadata.get('text') or '',
            'boilerplate_ratio': metadata.get('boilerplate_ratio', 0.0),
        }
    else:
        try:
            res = __import__('probe.crawl.fetcher', fromlist=['fetch']).fetch(
                url, timeout=timeout, max_size=max_size, max_retries=max_retries, backoff_factor=backoff_factor
            )
        except Exception as exc:
            click.echo(f"✗ Fetch failed: {exc}")
            m.close()
            raise

        if res.get('error'):
            click.echo(f"✗ {res.get('error')}")
            m.close()
            return

        # Build page dict suitable for scorer
        try:
            cleaned = __import__('probe.crawl.cleaner', fromlist=['clean_html']).clean_html(res.get('raw_bytes').decode('utf-8', errors='ignore'), url)
        except Exception:
            cleaned = { 'text': '', 'boilerplate_ratio': 0.0 }

        page = dict(res)
        page.update(cleaned)

    # Instantiate a simple scorer: KeywordDensity + Boilerplate
    kws = []
    if keywords:
        kws = [k.strip() for k in keywords.split(',') if k.strip()]

    from probe.crawl.scorer import RelevanceScorer, KeywordDensityScorer, BoilerplateDetector

    components = [KeywordDensityScorer(keywords=kws, weight=1.0), BoilerplateDetector(weight=1.0)]
    scorer = RelevanceScorer(components=components)

    comps = scorer.score_components(page)
    total = scorer.score(page)

    click.echo("Component scores:")
    for k, v in comps.items():
        click.echo(f"  {k}: {v:.3f}")
    click.echo(f"=> Total score: {total:.3f}")

    if persist:
        # Persist the scoring report into DB
        meta = {'keywords': kws}
        report_id = m.add_scoring_report(from_db if from_db is not None else None, fetched_url, float(total), comps, meta)
        click.echo(f"Persisted scoring report id: {report_id}")

    m.close()
    return total

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
@click.option('--max-size', default=10000000, type=int, help='Max response size in bytes')
@click.option('--max-retries', default=3, type=int, help='Maximum retry attempts')
@click.option('--backoff-factor', default=0.5, type=float, help='Backoff factor seconds')
@click.option('--concurrency', default=1, type=int, help='Number of concurrent workers for seed runner')
@click.option('--per-domain-delay', default=0.25, type=float, help='Minimum delay (seconds) between requests to the same domain')
@click.option('--min-delay', default=0.0, type=float, help='Minimum delay (seconds) enforced by fetcher between requests to the same domain (in-memory)')
@click.option('--ignore-retry-after', is_flag=True, default=False, help='Ignore Retry-After headers returned by servers')
@click.option('--persistent-politeness/--no-persistent-politeness', default=False, help='Enable persistent per-domain politeness (store last-crawl timestamps)')
@click.option('--ignore-robots', is_flag=True, default=False, help='Ignore robots.txt rules (use with caution)')
@click.option('--score/--no-score', default=False, help='Compute relevance score for each fetched page')
@click.option('--persist-scores', is_flag=True, default=False, help='Persist scoring reports to the Map DB')
@click.option('--score-keywords', default=None, help='Comma-separated keywords to supply to the KeywordDensityScorer/EntityRegexScorer')
@click.option('--blocked-domains', default='blocked_domains.txt', help='Path to blocked domains file (one domain per line). Use "" to disable')
@click.option('--no-progress', is_flag=True, default=False, help='Disable tqdm progress bars (useful for CI)')
@click.option('--summary-dir', default='run_reports', help='Directory to write CSV and logs')
@click.option('--summary-csv', default=None, help='Write summary CSV to an explicit path (overrides --summary-dir)')
@click.option('--no-log-failures', is_flag=True, default=False, help='Disable appending failed seeds to constraints.log')
def seeds_run(file, limit, ingest, db, timeout, max_size, max_retries, backoff_factor, concurrency, per_domain_delay, min_delay, ignore_retry_after, persistent_politeness, ignore_robots, score, persist_scores, score_keywords, blocked_domains, no_progress, summary_dir, summary_csv, no_log_failures):
    """
    Options:
    - `--concurrency` number of worker threads
    - `--per-domain-delay` minimum delay between requests to the same domain
    - `--ignore-robots` skip robots.txt checks
    - `--persistent-politeness` (enabled via flag) will store last-crawl timestamps across runs
    """
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
    # If either ingest or score persistence is requested, open the DB
    if ingest or persist_scores:
        m = Map(db)

    # Optional tqdm progress bar (import if available)
    try:
        from tqdm import tqdm
    except Exception:
        tqdm = None

    # Load blocked domains file if provided (skip if empty string or missing)
    blocked_set = set()
    try:
        if blocked_domains:
            p = Path(blocked_domains)
            if p.exists():
                for line in p.read_text(encoding='utf-8').splitlines():
                    d = line.strip()
                    if d:
                        blocked_set.add(d)
    except Exception:
        blocked_set = set()

    # Concurrent fetching: use ThreadPoolExecutor if concurrency > 1
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading

    # use CLI-provided concurrency/per-domain-delay
    try:
        concurrency = int(concurrency)
    except Exception:
        concurrency = 1
    try:
        per_domain_delay = float(per_domain_delay)
    except Exception:
        per_domain_delay = 0.0

    if concurrency <= 1:
        # existing sequential flow
        domain_last_time = {}
        # wrap the iterator with tqdm if available and not disabled
        seq_iter = urls
        if not no_progress and tqdm is not None:
            try:
                seq_iter = tqdm(urls, desc="Seeds", unit="seed")
            except Exception:
                seq_iter = urls

        for u in seq_iter:
            click.echo(f"Fetching: {u}")

            # domain blocklist check
            try:
                from urllib.parse import urlparse
                domain = urlparse(u).netloc
                if domain in blocked_set:
                    rows.append({
                        'timestamp': __import__('datetime').datetime.now().isoformat(),
                        'url': u,
                        'domain': domain,
                        'status_code': 0,
                        'success': 'False',
                        'error_message': 'blocked_by_blocklist',
                        'content_type': '',
                        'content_length': 0,
                        'fetch_duration_ms': 0,
                        'redirect_count': 0,
                        'final_url': '',
                        'link_count': 0,
                        'has_pdf_links': False,
                        'retry_count': 0,
                        'user_agent': '',
                    })
                    if not no_log_failures:
                        append_failure_log(u, 'blocked_by_blocklist', file, f"cli seeds run {file} --limit {limit}")
                    failures += 1
                    click.echo("  ✗ blocked_by_blocklist")
                    continue
            except Exception:
                pass

            # robots.txt check (unless ignored)
            if not ignore_robots:
                try:
                    from probe.crawl.robots import can_fetch, crawl_delay
                    ua = 'probe/0.1'
                    allowed = can_fetch(ua, u)
                    if not allowed:
                        # record as skipped due to robots
                        rows.append({
                            'timestamp': __import__('datetime').datetime.now().isoformat(),
                            'url': u,
                            'domain': __import__('urllib.parse', fromlist=['urlparse']).urlparse(u).netloc,
                            'status_code': 0,
                            'success': 'False',
                            'error_message': 'blocked_by_robots',
                            'content_type': '',
                            'content_length': 0,
                            'fetch_duration_ms': 0,
                            'redirect_count': 0,
                            'final_url': '',
                            'link_count': 0,
                            'has_pdf_links': False,
                            'retry_count': 0,
                            'user_agent': ua,
                        })
                        if not no_log_failures:
                            append_failure_log(u, 'blocked_by_robots', file, f"cli seeds run {file} --limit {limit}")
                        failures += 1
                        click.echo("  ✗ blocked_by_robots")
                        continue
                except Exception:
                    # on errors parsing robots, be permissive
                    pass

            # per-domain / persistent politeness for sequential runs
            try:
                domain = __import__('urllib.parse', fromlist=['urlparse']).urlparse(u).netloc
                last = domain_last_time.get(domain, 0)
                if persistent_politeness and last == 0:
                    try:
                        from probe.crawl.state import get_last_crawled
                        last_dt = get_last_crawled(domain)
                        if last_dt:
                            now_mon = __import__('time').monotonic()
                            now_epoch = __import__('time').time()
                            last_epoch = last_dt.timestamp()
                            last_mon = now_mon - (now_epoch - last_epoch)
                            last = last_mon
                            domain_last_time[domain] = last
                    except Exception:
                        pass

                now = __import__('time').monotonic()
                wait = max(0, per_domain_delay - (now - last))
                if wait > 0:
                    __import__('time').sleep(wait)
                domain_last_time[domain] = __import__('time').monotonic()
            except Exception:
                pass

            try:
                res = __import__('probe.crawl.fetcher', fromlist=['fetch']).fetch(
                    u,
                    timeout=timeout,
                    max_size=max_size,
                    max_retries=max_retries,
                    backoff_factor=backoff_factor,
                    min_delay=min_delay,
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
                    'retry_count': res.get('retry_count') or 0,
                    'user_agent': res.get('user_agent') or '',
                    'score': '',
                    'top_component': '',
                    'component_scores': '',
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
                    # compute scoring if requested
                    if score:
                        try:
                            cleaned = __import__('probe.crawl.cleaner', fromlist=['clean_html']).clean_html(res.get('raw_bytes').decode('utf-8', errors='ignore'), u)
                        except Exception:
                            cleaned = {'text': '', 'boilerplate_ratio': 0.0}

                        page = dict(res)
                        page.update(cleaned)

                        kws = []
                        if score_keywords:
                            kws = [k.strip() for k in score_keywords.split(',') if k.strip()]

                        from probe.crawl.scorer import RelevanceScorer, KeywordDensityScorer, BoilerplateDetector, LinkDensityScorer, EntityRegexScorer

                        components = [KeywordDensityScorer(keywords=kws, weight=1.0), BoilerplateDetector(weight=1.0), LinkDensityScorer(weight=1.0)]
                        if kws:
                            components.append(EntityRegexScorer(patterns=kws, weight=1.0))

                        scorer = RelevanceScorer(components=components)
                        comps = scorer.score_components(page)
                        total = scorer.score(page)

                        # attach to row
                        row['score'] = float(total)
                        # top component is the highest-scoring component
                        top = max(comps.items(), key=lambda kv: kv[1])[0] if comps else ''
                        row['top_component'] = top
                        import json
                        row['component_scores'] = json.dumps(comps)

                        # persist if requested
                        if persist_scores and m:
                            meta = {'keywords': kws}
                            rpt_id = m.add_scoring_report(None, u, float(total), comps, meta)
                            click.echo(f"    Persisted scoring report id: {rpt_id}")

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
                    'retry_count': 0,
                    'user_agent': ''
                })
    else:
        # concurrent mode
        click.echo(f"Running with concurrency={concurrency}, per_domain_delay={per_domain_delay}")
        domain_locks = {}
        domain_last_time = {}
        domain_lock = threading.Lock()

        def worker(u):
                # enforce per-domain delay (including persistent politeness if enabled)
                parsed = __import__('urllib.parse', fromlist=['urlparse']).urlparse(u)
                d = parsed.netloc
                with domain_lock:
                    if d not in domain_locks:
                        domain_locks[d] = threading.Lock()
                with domain_locks[d]:
                    # compute wait based on in-memory last time
                    now = __import__('time').monotonic()
                    last = domain_last_time.get(d, 0)

                    # if persistent politeness enabled, consult persistent state for initial baseline
                    if persistent_politeness and last == 0:
                        try:
                            from probe.crawl.state import get_last_crawled
                            last_dt = get_last_crawled(d)
                            if last_dt:
                                # convert stored epoch-based timestamp into monotonic timescale
                                now_mon = __import__('time').monotonic()
                                now_epoch = __import__('time').time()
                                last_epoch = last_dt.timestamp()
                                # compute last in monotonic reference: last_mon = now_mon - (now_epoch - last_epoch)
                                last_mon = now_mon - (now_epoch - last_epoch)
                                last = last_mon
                                domain_last_time[d] = last
                        except Exception:
                            pass

                    wait = max(0, per_domain_delay - (now - last))
                    if wait > 0:
                        __import__('time').sleep(wait)
                    # update last time
                    domain_last_time[d] = __import__('time').monotonic()
                # domain blocklist check inside worker
                if d in blocked_set:
                    # short-circuit with an error-like result; main loop will record the failure and append to log
                    return u, {"status_code": 0, "error": "blocked_by_blocklist", "content_type": "", "content_length": 0}

                # perform fetch
                u_ret, res = u, __import__('probe.crawl.fetcher', fromlist=['fetch']).fetch(u, timeout=timeout, max_size=max_size, max_retries=max_retries, backoff_factor=backoff_factor, min_delay=min_delay)
                # persist domain last-crawled if enabled
                if persistent_politeness:
                    try:
                        from probe.crawl.state import set_last_crawled
                        set_last_crawled(d, __import__('datetime').datetime.now())
                    except Exception:
                        pass
                return u_ret, res
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            futures = {ex.submit(worker, u): u for u in urls}
            for fut in as_completed(futures):
                u = futures[fut]
                try:
                    u_ret, res = fut.result()
                    domain = __import__('urllib.parse', fromlist=['urlparse']).urlparse(u_ret).netloc
                    try:
                        sc = int(res.get('status_code') or 0)
                        success_flag = (sc >= 200 and sc < 400) and not bool(res.get('error'))
                    except Exception:
                        success_flag = False

                    row = {
                        'timestamp': __import__('datetime').datetime.now().isoformat(),
                        'url': u_ret,
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
                        'retry_count': res.get('retry_count') or 0,
                        'user_agent': res.get('user_agent') or '',
                        'score': '',
                        'top_component': '',
                        'component_scores': '',
                    }

                    rows.append(row)

                    if res.get('error'):
                        click.echo(f"  ✗ {res.get('error')}")
                        failures += 1
                        if not no_log_failures:
                            append_failure_log(u_ret, res.get('error'), file, f"cli seeds run {file} --limit {limit}")
                    else:
                        click.echo(f"  ✓ {res.get('status_code')} {res.get('content_type')}")
                        successes += 1
                        # compute scoring if requested
                        if score:
                            try:
                                cleaned = __import__('probe.crawl.cleaner', fromlist=['clean_html']).clean_html(res.get('raw_bytes').decode('utf-8', errors='ignore'), u_ret)
                            except Exception:
                                cleaned = {'text': '', 'boilerplate_ratio': 0.0}

                            page = dict(res)
                            page.update(cleaned)

                            kws = []
                            if score_keywords:
                                kws = [k.strip() for k in score_keywords.split(',') if k.strip()]

                            from probe.crawl.scorer import RelevanceScorer, KeywordDensityScorer, BoilerplateDetector, LinkDensityScorer, EntityRegexScorer

                            components = [KeywordDensityScorer(keywords=kws, weight=1.0), BoilerplateDetector(weight=1.0), LinkDensityScorer(weight=1.0)]
                            if kws:
                                components.append(EntityRegexScorer(patterns=kws, weight=1.0))

                            scorer = RelevanceScorer(components=components)
                            comps = scorer.score_components(page)
                            total = scorer.score(page)

                            # attach to row
                            row['score'] = float(total)
                            # top component is the highest-scoring component
                            top = max(comps.items(), key=lambda kv: kv[1])[0] if comps else ''
                            row['top_component'] = top
                            import json
                            row['component_scores'] = json.dumps(comps)

                            # persist if requested
                            if persist_scores and m:
                                meta = {'keywords': kws}
                                rpt_id = m.add_scoring_report(None, u_ret, float(total), comps, meta)
                                click.echo(f"    Persisted scoring report id: {rpt_id}")

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
                        'retry_count': 0,
                        'user_agent': ''
                    })

    if m:
        m.close()

    # Write CSV summary
    try:
        if summary_csv:
            p = write_csv_report(file, rows, file_path=Path(summary_csv))
        else:
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


@cli.command(name='analyze-crawl')
@click.option('--url', default=None, help='Filter reports for a specific URL')
@click.option('--page-id', default=None, type=int, help='Filter reports for a specific page id')
@click.option('--since', default=None, help='ISO datetime (inclusive) to filter from')
@click.option('--until', default=None, help='ISO datetime (inclusive) to filter until')
@click.option('--format', 'fmt', default='csv', type=click.Choice(['csv','md']), help='Output format')
@click.option('--out', default=None, help='Output path (file)')
@click.option('--db', default='probe.db', help='Database file path')
def analyze_crawl(url, page_id, since, until, fmt, out, db):
    """Export scoring reports to CSV or markdown with optional filters."""
    click.echo("Analyzing scoring reports...")
    m = Map(db)
    rows = m.get_scoring_reports(url=url, page_id=page_id, since=since, until=until)
    # Convert sqlite3.Row objects to plain dicts and enrich with top_component
    import json
    out_rows = []
    for r in rows:
        comps = r['components']
        if isinstance(comps, str):
            try:
                comps_obj = json.loads(comps)
            except Exception:
                comps_obj = {}
        else:
            comps_obj = comps or {}
        top = max(comps_obj.items(), key=lambda kv: kv[1])[0] if comps_obj else ''
        out_rows.append({
            'id': r['id'],
            'page_id': r['page_id'],
            'url': r['url'],
            'score': r['score'],
            'components': comps_obj,
            'metadata': r['metadata'],
            'created_at': r['created_at'],
            'top_component': top,
        })

    from probe.crawl.reporting import write_scoring_export
    ap = Path(out) if out else None
    p = write_scoring_export(out_rows, file_path=ap, fmt=fmt)
    click.echo(f"Wrote scoring export: {p}")

    m.close()


if __name__ == "__main__":
    cli()