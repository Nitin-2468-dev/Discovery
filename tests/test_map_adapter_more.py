import json
from pathlib import Path

from probe.core.map import Map, Page, Document
from probe.core.map_adapter import MapAdapter


def test_delegate_get_map_summary(tmp_path: Path):
    db = tmp_path / "map_adapter_more.db"
    m = Map(str(db))
    adapter = MapAdapter(m)

    p = Page(id=None, url="http://a.local/p", domain="a.local")
    d = Document(id=None, title="Doc", doc_type="pdf", hash="h1", url="http://a.local/d.pdf", domain="a.local")

    pid = adapter.add_page(p)
    did = adapter.add_document(d)

    summary = adapter.get_map_summary()
    assert isinstance(summary, dict)
    assert summary.get("pages", 0) >= 1
    assert summary.get("documents", 0) >= 1


def test_document_metadata_stored_and_parseable(tmp_path: Path):
    db = tmp_path / "map_adapter_more_meta.db"
    m = Map(str(db))
    adapter = MapAdapter(m)

    meta = {"crawl_run_id": "run-xyz", "note": "test"}
    d = Document(id=None, title="Doc", doc_type="pdf", hash="h2", url="http://a.local/d2.pdf", domain="a.local", metadata=meta)

    did = adapter.add_document(d)

    cur = adapter.conn.execute("SELECT metadata FROM documents WHERE id = ?", (did,))
    row = cur.fetchone()
    assert row is not None
    raw = row[0]
    parsed = json.loads(raw) if raw else None
    assert parsed == meta


def test_get_high_yield_domains_returns_list(tmp_path: Path):
    db = tmp_path / "map_adapter_high.db"
    m = Map(str(db))
    adapter = MapAdapter(m)

    domain = "dom.local"
    # Simulate a few crawled pages and found documents
    m.update_domain_stats(domain, found_document=True)
    m.update_domain_stats(domain, found_document=False)
    m.update_domain_stats(domain, found_document=True)

    res = adapter.get_high_yield_domains(min_pages=1)
    assert isinstance(res, list)
    assert any(d.domain_name == domain for d in res)
