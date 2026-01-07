"""Helpers to ingest fetcher results into the Map."""
from hashlib import sha256
from urllib.parse import urlparse
from typing import Dict, Any

from probe.core.map import Map, Page, Document


def ingest_fetch_result(map_obj: Map, fetch_result: Dict[str, Any]) -> Dict[str, int]:
    """Ingest a fetch result into the provided Map.

    Returns a dict with created ids e.g. {"page_id": 1, "document_id": None}
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
        doc_id = map_obj.add_document(doc)
        map_obj.update_domain_stats(domain, found_document=True)
        return {"page_id": None, "document_id": doc_id}

    # Otherwise ingest as a page
    h = sha256((raw or fetch_result.get("text", "")).encode("utf-8") if isinstance(raw, str) else (raw or b""))
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
    page_id = map_obj.add_page(page)
    map_obj.update_domain_stats(domain, found_document=False)
    return {"page_id": page_id, "document_id": None}
