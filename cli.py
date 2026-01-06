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


if __name__ == "__main__":
    cli()