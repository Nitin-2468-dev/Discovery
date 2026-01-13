"""
probe/core/map.py

The Map: Knowledge graph interface.
All queries and updates go through this class.

Design Principles:
- Single interface to the knowledge graph
- All operations are atomic (commit after each)
- Returns dataclasses, not raw SQL rows
- Handles all SQL internally (no leaky abstractions)
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass


# ============================================================
# DATA MODELS
# ============================================================


@dataclass
class Entity:
    id: Optional[int]
    name: str
    type: Optional[str] = None
    confidence_score: float = 0.5
    metadata: Optional[Dict] = None
    created_at: Optional[str] = None
    last_seen_at: Optional[str] = None


@dataclass
class Document:
    id: Optional[int]
    title: str
    doc_type: str
    hash: str
    url: str
    domain: str
    file_size: Optional[int] = None
    publication_date: Optional[str] = None
    metadata: Optional[Dict] = None
    created_at: Optional[str] = None
    last_accessed_at: Optional[str] = None


@dataclass
class Page:
    id: Optional[int]
    url: str
    domain: str
    title: Optional[str] = None
    content_hash: Optional[str] = None
    relevance_score: Optional[float] = None
    metadata: Optional[Dict] = None
    last_crawled_at: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class Domain:
    id: Optional[int]
    domain_name: str
    yield_score: float = 0.0
    trust_score: float = 0.5
    pages_crawled: int = 0
    documents_found: int = 0
    metadata: Optional[Dict] = None
    first_seen_at: Optional[str] = None
    last_crawled_at: Optional[str] = None


@dataclass
class Edge:
    id: Optional[int]
    from_type: str
    from_id: int
    to_type: str
    to_id: int
    relation: str
    confidence: float = 1.0
    metadata: Optional[Dict] = None
    source_page_id: Optional[int] = None
    discovered_at: Optional[str] = None


# ============================================================
# THE MAP
# ============================================================


class Map:
    """The persistent knowledge graph."""

    def __init__(self, db_path: str = "probe.db"):
        self.db_path = db_path
        # Ensure schema exists and return a ready-to-use connection
        from probe.core.schema import initialize_schema

        self.conn = initialize_schema(db_path)
        self.conn.row_factory = sqlite3.Row  # Access columns by name

    def close(self):
        """Close the database connection."""
        self.conn.close()

    # ============================================================
    # ENTITIES
    # ============================================================

    def get_entity(self, name: str) -> Optional[Entity]:
        """Retrieve an entity by exact name."""
        cursor = self.conn.execute("SELECT * FROM entities WHERE name = ?", (name,))
        row = cursor.fetchone()

        if row:
            return Entity(
                id=row["id"],
                name=row["name"],
                type=row["type"],
                confidence_score=row["confidence_score"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                created_at=row["created_at"],
                last_seen_at=row["last_seen_at"],
            )
        return None

    def add_entity(self, entity: Entity) -> int:
        """
        Add or update an entity. Returns entity ID.
        If entity exists, updates last_seen_at and confidence_score (keeps max).
        """
        metadata_json = json.dumps(entity.metadata) if entity.metadata else None

        cursor = self.conn.execute(
            """
            INSERT INTO entities (name, type, confidence_score, metadata)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                last_seen_at = CURRENT_TIMESTAMP,
                confidence_score = MAX(confidence_score, excluded.confidence_score),
                type = COALESCE(excluded.type, type),
                metadata = COALESCE(excluded.metadata, metadata)
            RETURNING id
            """,
            (entity.name, entity.type, entity.confidence_score, metadata_json),
        )
        entity_id = cursor.fetchone()[0]
        self.conn.commit()
        return entity_id

    def get_entity_documents(
        self, entity_name: str, doc_type: Optional[str] = None
    ) -> List[Document]:
        """Get all documents linked to an entity, optionally filtered by type."""
        query = """
            SELECT d.* FROM documents d
            JOIN edges e ON e.to_id = d.id AND e.to_type = 'document'
            JOIN entities en ON en.id = e.from_id AND e.from_type = 'entity'
            WHERE en.name = ?
        """
        params = [entity_name]

        if doc_type:
            query += " AND d.doc_type = ?"
            params.append(doc_type)

        query += " ORDER BY d.created_at DESC"

        cursor = self.conn.execute(query, params)
        return [self._row_to_document(row) for row in cursor.fetchall()]

    def get_related_entities(
        self, entity_name: str, relation: Optional[str] = None
    ) -> List[Entity]:
        """Get entities related to this entity (e.g., variants, related_to)."""
        query = """
            SELECT e2.* FROM entities e2
            JOIN edges ed ON ed.to_id = e2.id AND ed.to_type = 'entity'
            JOIN entities e1 ON e1.id = ed.from_id AND ed.from_type = 'entity'
            WHERE e1.name = ?
        """
        params = [entity_name]

        if relation:
            query += " AND ed.relation = ?"
            params.append(relation)

        cursor = self.conn.execute(query, params)
        return [self._row_to_entity(row) for row in cursor.fetchall()]

    # ============================================================
    # DOCUMENTS
    # ============================================================

    def add_document(self, doc: Document) -> int:
        """
        Add a document if not already present (by hash). Returns doc ID.
        If document exists, updates last_accessed_at.
        """
        metadata_json = json.dumps(doc.metadata) if doc.metadata else None

        cursor = self.conn.execute(
            """
            INSERT INTO documents (title, doc_type, hash, url, domain,
                                   file_size, publication_date, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hash) DO UPDATE SET
                last_accessed_at = CURRENT_TIMESTAMP
            RETURNING id
            """,
            (
                doc.title,
                doc.doc_type,
                doc.hash,
                doc.url,
                doc.domain,
                doc.file_size,
                doc.publication_date,
                metadata_json,
            ),
        )
        doc_id = cursor.fetchone()[0]
        self.conn.commit()
        return doc_id

    def get_document_by_hash(self, hash: str) -> Optional[Document]:
        """Retrieve a document by content hash."""
        cursor = self.conn.execute("SELECT * FROM documents WHERE hash = ?", (hash,))
        row = cursor.fetchone()
        return self._row_to_document(row) if row else None

    # ============================================================
    # PAGES
    # ============================================================

    def add_page(self, page: Page) -> int:
        """
        Add or update a page. Returns page ID.
        If page exists, updates last_crawled_at and relevance_score.
        """
        metadata_json = json.dumps(page.metadata) if page.metadata else None

        cursor = self.conn.execute(
            """
            INSERT INTO pages (url, domain, title, content_hash,
                               relevance_score, metadata, last_crawled_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                last_crawled_at = excluded.last_crawled_at,
                relevance_score = excluded.relevance_score,
                content_hash = excluded.content_hash,
                title = COALESCE(excluded.title, title),
                metadata = COALESCE(excluded.metadata, metadata)
            RETURNING id
            """,
            (
                page.url,
                page.domain,
                page.title,
                page.content_hash,
                page.relevance_score,
                metadata_json,
                page.last_crawled_at or datetime.now().isoformat(),
            ),
        )
        page_id = cursor.fetchone()[0]
        self.conn.commit()
        return page_id

    # ============================================================
    # DOMAINS
    # ============================================================

    def get_high_yield_domains(
        self, limit: int = 10, min_pages: int = 3
    ) -> List[Domain]:
        """
        Get domains with highest yield scores.
        Only includes domains that have crawled at least min_pages.
        """
        cursor = self.conn.execute(
            """
            SELECT * FROM domains
            WHERE pages_crawled >= ?
            ORDER BY yield_score DESC
            LIMIT ?
            """,
            (min_pages, limit),
        )
        return [self._row_to_domain(row) for row in cursor.fetchall()]

    def update_domain_stats(self, domain_name: str, found_document: bool):
        """
        Update domain statistics after crawling a page.
        Automatically recalculates yield_score.
        """
        self.conn.execute(
            """
            INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score)
            VALUES (?, 1, ?, ?)
            ON CONFLICT(domain_name) DO UPDATE SET
                pages_crawled = pages_crawled + 1,
                documents_found = documents_found + ?,
                yield_score = CAST(documents_found AS REAL) / pages_crawled,
                last_crawled_at = CURRENT_TIMESTAMP
            """,
            (
                domain_name,
                1 if found_document else 0,
                1.0 if found_document else 0.0,
                1 if found_document else 0,
            ),
        )
        self.conn.commit()

    def increment_domain_documents(self, domain_name: str, delta: int = 1):
        """Increment documents_found for a domain without changing pages_crawled.

        Recalculates yield_score safely (pages_crawled may be zero).
        """
        # Ensure domain row exists
        cursor = self.conn.execute(
            "INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score)\n            VALUES (?, 0, ?, 0.0)\n            ON CONFLICT(domain_name) DO UPDATE SET documents_found = documents_found + ?\n            RETURNING id, pages_crawled, documents_found",
            (domain_name, max(0, delta), delta)
        )
        # Recalculate yield_score if pages_crawled > 0
        try:
            cursor = self.conn.execute("SELECT pages_crawled, documents_found FROM domains WHERE domain_name = ?", (domain_name,))
            pr = cursor.fetchone()
            pages = pr[0] or 0
            docs = pr[1] or 0
            if pages > 0:
                ys = float(docs) / pages
            else:
                ys = float(docs)
            self.conn.execute("UPDATE domains SET yield_score = ? WHERE domain_name = ?", (ys, domain_name))
            self.conn.commit()
        except Exception:
            self.conn.commit()
    def get_domain(self, domain_name: str) -> Optional[Domain]:
        """Retrieve a domain by name."""
        cursor = self.conn.execute(
            "SELECT * FROM domains WHERE domain_name = ?", (domain_name,)
        )
        row = cursor.fetchone()
        return self._row_to_domain(row) if row else None

    # ============================================================
    # EDGES (Relationships)
    # ============================================================

    def add_edge(self, edge: Edge) -> int:
        """
        Create a relationship between nodes.
        Returns edge ID. Silently ignores duplicates.
        """
        metadata_json = json.dumps(edge.metadata) if edge.metadata else None

        cursor = self.conn.execute(
            """
            INSERT OR IGNORE INTO edges
            (from_type, from_id, to_type, to_id, relation, confidence,
             metadata, source_page_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                edge.from_type,
                edge.from_id,
                edge.to_type,
                edge.to_id,
                edge.relation,
                edge.confidence,
                metadata_json,
                edge.source_page_id,
            ),
        )
        edge_id = cursor.lastrowid
        self.conn.commit()
        return edge_id if edge_id != 0 else None

    def get_edges_from(
        self, from_type: str, from_id: int, relation: Optional[str] = None
    ) -> List[Edge]:
        """Get all edges originating from a node."""
        query = "SELECT * FROM edges WHERE from_type = ? AND from_id = ?"
        params = [from_type, from_id]

        if relation:
            query += " AND relation = ?"
            params.append(relation)

        cursor = self.conn.execute(query, params)
        return [self._row_to_edge(row) for row in cursor.fetchall()]

    # ============================================================
    # QUERIES (High-level)
    # ============================================================

    def has_documents_for_entity(
        self, entity_name: str, doc_type: Optional[str] = None
    ) -> bool:
        """Check if we already have documents for this entity."""
        query = """
            SELECT COUNT(*) FROM documents d
            JOIN edges e ON e.to_id = d.id AND e.to_type = 'document'
            JOIN entities en ON en.id = e.from_id AND e.from_type = 'entity'
            WHERE en.name = ?
        """
        params = [entity_name]

        if doc_type:
            query += " AND d.doc_type = ?"
            params.append(doc_type)

        cursor = self.conn.execute(query, params)
        count = cursor.fetchone()[0]
        return count > 0

    def get_map_summary(self) -> Dict[str, int]:
        """Get counts of all node types."""
        cursor = self.conn.cursor()

        summary = {}
        for table in ["entities", "documents", "pages", "domains", "edges"]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            summary[table] = cursor.fetchone()[0]
        # scoring_reports may not exist on older DBs; check safely
        try:
            cursor.execute("SELECT COUNT(*) FROM scoring_reports")
            summary["scoring_reports"] = cursor.fetchone()[0]
        except Exception:
            summary["scoring_reports"] = 0

        return summary

    def add_scoring_report(
        self,
        page_id: int,
        url: str,
        score: float,
        components: dict,
        metadata: dict = None,
    ) -> int:
        """Persist a scoring report and return its ID."""
        import json

        comps_json = json.dumps(components) if components is not None else None
        meta_json = json.dumps(metadata) if metadata is not None else None
        cursor = self.conn.execute(
            """
            INSERT INTO scoring_reports (page_id, url, score, components, metadata)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id
            """,
            (page_id, url, score, comps_json, meta_json),
        )
        row = cursor.fetchone()
        self.conn.commit()
        return row[0]

    def get_scoring_reports_for_page(self, page_id: int):
        """Return all scoring reports for a given page id, newest first."""
        cursor = self.conn.execute(
            "SELECT * FROM scoring_reports WHERE page_id = ? ORDER BY created_at DESC",
            (page_id,),
        )
        rows = cursor.fetchall()
        return rows

    def get_latest_scoring_report_for_url(self, url: str):
        """Return the latest scoring report for a url, or None."""
        cursor = self.conn.execute(
            "SELECT * FROM scoring_reports WHERE url = ? ORDER BY created_at DESC LIMIT 1",
            (url,),
        )
        row = cursor.fetchone()
        return row

    def get_scoring_reports(
        self, url: str = None, page_id: int = None, since: str = None, until: str = None
    ):
        """Query scoring reports with optional filters.

        Args:
            url: exact URL to filter
            page_id: integer page id
            since: ISO datetime string inclusive (e.g., '2026-01-01T00:00:00')
            until: ISO datetime string inclusive

        Returns:
            List[sqlite3.Row]
        """
        query = "SELECT * FROM scoring_reports"
        conditions = []
        params = []
        if url:
            conditions.append("url = ?")
            params.append(url)
        if page_id is not None:
            conditions.append("page_id = ?")
            params.append(page_id)
        if since:
            conditions.append("created_at >= ?")
            params.append(since)
        if until:
            conditions.append("created_at <= ?")
            params.append(until)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at DESC"
        cursor = self.conn.execute(query, tuple(params))
        return cursor.fetchall()

    def get_page_by_id(self, page_id: int):
        """Retrieve a page row by id."""
        cursor = self.conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,))
        row = cursor.fetchone()
        return row

    # ============================================================
    # HELPERS (Internal)
    # ============================================================

    def _row_to_entity(self, row: sqlite3.Row) -> Entity:
        """Convert database row to Entity dataclass."""
        return Entity(
            id=row["id"],
            name=row["name"],
            type=row["type"],
            confidence_score=row["confidence_score"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            created_at=row["created_at"],
            last_seen_at=row["last_seen_at"],
        )

    def _row_to_document(self, row: sqlite3.Row) -> Document:
        """Convert database row to Document dataclass."""
        return Document(
            id=row["id"],
            title=row["title"],
            doc_type=row["doc_type"],
            hash=row["hash"],
            url=row["url"],
            domain=row["domain"],
            file_size=row["file_size"],
            publication_date=row["publication_date"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            created_at=row["created_at"],
            last_accessed_at=row["last_accessed_at"],
        )

    def _row_to_domain(self, row: sqlite3.Row) -> Domain:
        """Convert database row to Domain dataclass."""
        return Domain(
            id=row["id"],
            domain_name=row["domain_name"],
            yield_score=row["yield_score"],
            trust_score=row["trust_score"],
            pages_crawled=row["pages_crawled"],
            documents_found=row["documents_found"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            first_seen_at=row["first_seen_at"],
            last_crawled_at=row["last_crawled_at"],
        )

    def _row_to_edge(self, row: sqlite3.Row) -> Edge:
        """Convert database row to Edge dataclass."""
        return Edge(
            id=row["id"],
            from_type=row["from_type"],
            from_id=row["from_id"],
            to_type=row["to_type"],
            to_id=row["to_id"],
            relation=row["relation"],
            confidence=row["confidence"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            source_page_id=row["source_page_id"],
            discovered_at=row["discovered_at"],
        )
