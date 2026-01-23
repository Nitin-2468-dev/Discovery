"""A small adapter to normalize Map API access and make integration easier.

This adapter is intentionally minimal and delegates to an underlying `Map` or
`Map`-compatible object. It centralizes the small compatibility surface we use
from orchestrators and tests and makes it easier to replace/normalize Map
implementations in one place.
"""

from typing import Any, Dict, List, Optional

from probe.core.map import Document, Domain, Map, Page


class MapAdapter:
    """Thin adapter around a `Map` instance.

    Methods mirror the common Map API used across orchestrator and tests.
    """

    def __init__(self, map_obj: Map):
        self._map = map_obj

    @property
    def conn(self):
        return self._map.conn

    def add_page(self, page: Page) -> int:
        return self._map.add_page(page)

    def add_document(self, doc: Document) -> int:
        return self._map.add_document(doc)

    def get_map_summary(self) -> Dict[str, int]:
        return self._map.get_map_summary()

    def get_domain(self, domain_name: str) -> Optional[Domain]:
        return self._map.get_domain(domain_name)

    def get_high_yield_domains(
        self, limit: int = 10, min_pages: int = 3
    ) -> List[Domain]:
        return self._map.get_high_yield_domains(limit=limit, min_pages=min_pages)

    # Provide a small defensive helper to safely read metadata from rows
    def extract_metadata(self, row) -> Dict[str, Any]:
        if not row:
            return {}
        try:
            md = row["metadata"] if row and row["metadata"] else None
            return {} if md is None else md if isinstance(md, dict) else {}
        except Exception:
            return {}
