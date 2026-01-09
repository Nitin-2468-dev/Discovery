"""Helpers to ingest fetcher results into the Map.

Provides an Ingestor class with richer features than the legacy helper.
- Creates Page or Document entries
- Creates edges for extracted links (page -> page)
- Returns created ids and counts
"""
from hashlib import sha256
from urllib.parse import urlparse
from typing import Dict, Any

from probe.core.map import Map, Page, Document, Edge


class Ingestor:
    """Ingest fetched results into the Map and create edges for discovered links."""

    def __init__(self, map_obj: Map):
        self.map = map_obj

    def ingest_fetch_result(self, fetch_result: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest a fetch result and return summary dict with ids and counts.

        Returns e.g. {"page_id": 1, "document_id": None, "link_count": 3, "edges_created": 3}
        """
        url = fetch_result.get("url")
        parsed = urlparse(url)
        domain = parsed.netloc

        raw = fetch_result.get("raw_bytes")

        if fetch_result.get("is_pdf"):
            # Create Document
            h = sha256(raw or b"").hexdigest()
            doc = Document(
                id=None,
                title=fetch_result.get("title") or "",
                doc_type="pdf",
                hash=h,
                url=url,
                domain=domain,
                file_size=len(raw) if raw else None,
                publication_date=None,
                metadata=fetch_result.get("metadata"),
            )
            doc_id = self.map.add_document(doc)
            self.map.update_domain_stats(domain, found_document=True)
            return {"page_id": None, "document_id": doc_id, "link_count": 0, "edges_created": 0}

        # Otherwise ingest as a page
        raw_text = fetch_result.get("text", "")
        # If raw is bytes and text absent, use bytes for hashing
        if isinstance(raw, (bytes, bytearray)):
            h = sha256(raw)
        else:
            h = sha256((raw_text or "").encode("utf-8"))
        content_hash = h.hexdigest()
        page = Page(
            id=None,
            url=url,
            domain=domain,
            title=fetch_result.get("title"),
            content_hash=content_hash,
            relevance_score=None,
            metadata=fetch_result.get("metadata"),
        )
        page_id = self.map.add_page(page)
        self.map.update_domain_stats(domain, found_document=False)

        # Create pages for links and edges
        links = fetch_result.get("links") or []
        edges_created = 0
        for l in links:
            link_url = l.get("url")
            if not link_url:
                continue
            link_parsed = urlparse(link_url)
            link_domain = link_parsed.netloc
            # Create a minimal page record for the linked URL (idempotent)
            link_page = Page(id=None, url=link_url, domain=link_domain, title=l.get("text"))
            link_page_id = self.map.add_page(link_page)
            # create an edge page -> page
            edge = Edge(id=None, from_type="page", from_id=page_id, to_type="page", to_id=link_page_id, relation="links_to", source_page_id=page_id)
            self.map.add_edge(edge)
            edges_created += 1

        return {"page_id": page_id, "document_id": None, "link_count": len(links), "edges_created": edges_created}


# Backwards-compatible helper
def ingest_fetch_result(map_obj: Map, fetch_result: Dict[str, Any]) -> Dict[str, int]:
    """Legacy helper that delegates to the Ingestor class for richer behavior."""
    ing = Ingestor(map_obj)
    return ing.ingest_fetch_result(fetch_result)
