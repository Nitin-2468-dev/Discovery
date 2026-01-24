import json
from pathlib import Path

from probe.core.map import Document, Map, Page
from probe.core.map_adapter import MapAdapter


def test_map_adapter_basic(tmp_path: Path):
    db = tmp_path / "map_adapter.db"
    m = Map(str(db))
    adapter = MapAdapter(m)

    # add a page
    page = Page(id=None, url="http://example.local/index", domain="example.local")
    pid = adapter.add_page(page)
    assert isinstance(pid, int)
    assert pid >= 0

    # add a document
    doc = Document(
        id=None,
        title="Doc",
        doc_type="pdf",
        hash="h1",
        url="http://example.local/doc.pdf",
        domain="example.local",
    )
    did = adapter.add_document(doc)
    assert isinstance(did, int)
    assert did >= 0

    summary = adapter.get_map_summary()
    assert summary["pages"] >= 1
    assert summary["documents"] >= 1


def test_map_adapter_preserves_metadata(tmp_path: Path):
    db = tmp_path / "map_adapter_meta.db"
    m = Map(str(db))
    adapter = MapAdapter(m)

    metadata = {"crawl_run_id": "abc123", "foo": "bar"}
    page = Page(
        id=None,
        url="http://example.local/withmeta",
        domain="example.local",
        metadata=metadata,
    )
    pid = adapter.add_page(page)
    assert pid >= 0

    cur = adapter.conn.execute("SELECT metadata FROM pages WHERE url = ?", (page.url,))
    row = cur.fetchone()
    assert row is not None
    raw_meta = row["metadata"] if row and row["metadata"] else None
    stored = json.loads(raw_meta) if raw_meta else {}
    assert stored.get("crawl_run_id") == "abc123"
