"""Compatibility helpers that attach convenience methods to `Map` at import time.

Some environments may have an older `Map` class loaded; this module ensures the small
helpers `get_entity_document_types` and `get_entity_document_count` are available
on the `Map` class regardless.
"""

from typing import List, Optional

from .map import Map


def get_entity_document_types(self, entity_name: str) -> List[str]:
    cursor = self.conn.execute(
        """
        SELECT DISTINCT d.doc_type FROM documents d
        JOIN edges e ON e.to_id = d.id AND e.to_type = 'document'
        JOIN entities en ON en.id = e.from_id AND e.from_type = 'entity'
        WHERE en.name = ?
        """,
        (entity_name,),
    )
    return [row[0] for row in cursor.fetchall()]


def get_entity_document_count(
    self, entity_name: str, doc_type: Optional[str] = None
) -> int:
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
    return cursor.fetchone()[0]


# Attach methods if not present
if not hasattr(Map, "get_entity_document_types"):
    Map.get_entity_document_types = get_entity_document_types  # type: ignore[attr-defined]

if not hasattr(Map, "get_entity_document_count"):
    Map.get_entity_document_count = get_entity_document_count  # type: ignore[attr-defined]


def get_domains_with_doc_type(self, doc_type: str, limit: int = 5):
    """Return domains that have documents of a given `doc_type`, ordered by count and yield."""
    cursor = self.conn.execute(
        """
        SELECT dom.* FROM domains dom
        JOIN (
            SELECT domain, COUNT(*) AS cnt FROM documents WHERE doc_type = ? GROUP BY domain
        ) sub ON sub.domain = dom.domain_name
        ORDER BY sub.cnt DESC, dom.yield_score DESC
        LIMIT ?
        """,
        (doc_type, limit),
    )
    # Build Domain objects lazily to avoid import cycles
    from .map import Domain

    return [Domain(**dict(row)) for row in cursor.fetchall()]


# Attach domain helper if missing
if not hasattr(Map, "get_domains_with_doc_type"):
    Map.get_domains_with_doc_type = get_domains_with_doc_type  # type: ignore[attr-defined]
