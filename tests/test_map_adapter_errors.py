import sqlite3
from pathlib import Path
import json

import pytest

from probe.core.map import Map
from probe.core.map_adapter import MapAdapter


def test_extract_metadata_malformed(tmp_path: Path):
    db = tmp_path / "map_adapter_malformed.db"
    m = Map(str(db))
    adapter = MapAdapter(m)

    # Insert a page row with non-json metadata string
    adapter.conn.execute(
        "INSERT INTO pages (url, domain, metadata, last_crawled_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
        ("http://example.local/bad", "example.local", "not-a-json"),
    )
    adapter.conn.commit()

    cur = adapter.conn.execute("SELECT metadata FROM pages WHERE url = ?", ("http://example.local/bad",))
    row = cur.fetchone()
    assert row is not None

    md = adapter.extract_metadata(row)
    assert md == {}


def test_extract_metadata_none(tmp_path: Path):
    db = tmp_path / "map_adapter_none.db"
    m = Map(str(db))
    adapter = MapAdapter(m)

    # Insert a page with no metadata
    adapter.conn.execute(
        "INSERT INTO pages (url, domain, last_crawled_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        ("http://example.local/none", "example.local"),
    )
    adapter.conn.commit()

    cur = adapter.conn.execute("SELECT metadata FROM pages WHERE url = ?", ("http://example.local/none",))
    row = cur.fetchone()
    assert row is not None

    md = adapter.extract_metadata(row)
    assert md == {}


def test_add_page_propagates_db_errors(tmp_path: Path):
    db = tmp_path / "map_adapter_err.db"
    m = Map(str(db))
    adapter = MapAdapter(m)

    # Monkeypatch underlying map to raise an OperationalError when adding a page
    def fail_add_page(page):
        raise sqlite3.OperationalError("disk full")

    adapter._map.add_page = fail_add_page

    from probe.core.map import Page

    page = Page(id=None, url="http://example.local/x", domain="example.local")
    with pytest.raises(sqlite3.OperationalError):
        adapter.add_page(page)
