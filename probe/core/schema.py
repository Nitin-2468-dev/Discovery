"""
probe/core/schema.py

Database schema definition for the Probe knowledge graph.
This is the single source of truth for table structure.

Design Principles:
- Nodes: entities, documents, pages, domains
- Edges: relationships between any node types
- JSON fields for flexibility (avoid premature normalization)
- Idempotent (safe to run multiple times)
"""

import sqlite3


def initialize_schema(db_path: str = "probe.db") -> sqlite3.Connection:
    """
    Initialize the database schema.
    Creates all tables and indexes if they don't exist.

    Returns the connection for immediate use.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # ============================================================
    # NODES
    # ============================================================

    # Entities: Things being investigated (engines, regulations, companies)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        type TEXT,  -- engine, regulation, company, concept
        confidence_score REAL DEFAULT 0.5,
        metadata TEXT,  -- JSON string for flexible attributes
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Documents: Terminal evidence nodes (PDFs, manuals, bulletins)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        doc_type TEXT,  -- manual, bulletin, spec, report
        hash TEXT NOT NULL UNIQUE,  -- SHA256 of content for deduplication
        url TEXT NOT NULL,
        domain TEXT NOT NULL,
        file_size INTEGER,  -- bytes
        publication_date TEXT,  -- ISO format YYYY-MM-DD
        metadata TEXT,  -- JSON string
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_accessed_at TIMESTAMP
    )
    """)

    # Pages: Navigational nodes (HTML pages)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL UNIQUE,
        domain TEXT NOT NULL,
        title TEXT,
        content_hash TEXT,  -- hash of cleaned content
        relevance_score REAL,  -- 0.0-1.0
        metadata TEXT,  -- JSON string
        last_crawled_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Domains: Source tracking (yield and trust scores)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS domains (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain_name TEXT NOT NULL UNIQUE,
        yield_score REAL DEFAULT 0.0,  -- documents_found / pages_crawled
        trust_score REAL DEFAULT 0.5,  -- 0.0-1.0, can be manually adjusted
        pages_crawled INTEGER DEFAULT 0,
        documents_found INTEGER DEFAULT 0,
        metadata TEXT,  -- JSON string
        first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_crawled_at TIMESTAMP
    )
    """)

    # ============================================================
    # EDGES (Relationships)
    # ============================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS edges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_type TEXT NOT NULL,  -- entity, document, page, domain
        from_id INTEGER NOT NULL,
        to_type TEXT NOT NULL,  -- entity, document, page, domain
        to_id INTEGER NOT NULL,
        relation TEXT NOT NULL,  -- mentions, links_to, variant_of, cites, etc.
        confidence REAL DEFAULT 1.0,  -- 0.0-1.0
        metadata TEXT,  -- JSON string
        source_page_id INTEGER,  -- which page led to this discovery
        discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        -- Prevent duplicate edges
        UNIQUE(from_type, from_id, to_type, to_id, relation)
    )
    """)

    # ============================================================
    # INDEXES (for common query patterns)
    # ============================================================

    # Entity lookups
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_entities_name
    ON entities(name)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_entities_type
    ON entities(type)
    """)

    # Document lookups
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_documents_hash
    ON documents(hash)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_documents_domain
    ON documents(domain)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_documents_type
    ON documents(doc_type)
    """)

    # Page lookups
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_pages_url
    ON pages(url)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_pages_domain
    ON pages(domain)
    """)

    # Domain lookups
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_domains_name
    ON domains(domain_name)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_domains_yield
    ON domains(yield_score DESC)
    """)

    # Edge lookups (critical for graph traversal)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_edges_from
    ON edges(from_type, from_id)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_edges_to
    ON edges(to_type, to_id)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_edges_relation
    ON edges(relation)
    """)

    # ============================================================
    # Scoring Reports: store per-page/component scoring snapshots
    # ============================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scoring_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page_id INTEGER,  -- nullable when scoring an external URL
        url TEXT,
        score REAL,
        components TEXT,  -- JSON string with per-component scores
        metadata TEXT,    -- JSON string for extra info
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_scoring_reports_page
    ON scoring_reports(page_id)
    """)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_scoring_reports_url
    ON scoring_reports(url)
    """)

    conn.commit()

    return conn


def get_schema_version(conn: sqlite3.Connection) -> str:
    """
    Get the current schema version.
    Useful for future migrations.
    """
    return "v0.1.1"


def validate_schema(conn: sqlite3.Connection) -> bool:
    """
    Validate that all expected tables exist.
    Returns True if schema is valid.
    """
    cursor = conn.cursor()

    expected_tables = ["entities", "documents", "pages", "domains", "edges"]

    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """)

    actual_tables = [row[0] for row in cursor.fetchall()]

    for table in expected_tables:
        if table not in actual_tables:
            return False

    return True


if __name__ == "__main__":
    # Test schema initialization
    print("Initializing Probe database schema...")

    conn = initialize_schema("probe.db")

    if validate_schema(conn):
        print("✓ Schema initialized successfully")
        print(f"✓ Schema version: {get_schema_version(conn)}")

        # Print table summary
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✓ Created {len(tables)} tables: {', '.join(tables)}")
    else:
        print("✗ Schema validation failed")

    conn.close()
