import hashlib

from probe.core.map import Map
from probe.crawl.ingest import Ingestor


def test_ingest_uses_cleaned_text_for_hash(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)
    ing = Ingestor(m)

    text = "Normalized text with spacing"
    fetch_result = {
        "url": "https://example.com/page.html",
        "title": "Page",
        "text": text,
        "links": [],
    }

    res = ing.ingest_fetch_result(fetch_result)
    page_id = res["page_id"]

    # Fetch page row directly from DB to inspect content_hash
    cur = m.conn.execute(
        "SELECT content_hash, metadata FROM pages WHERE id = ?", (page_id,)
    )
    row = cur.fetchone()
    expected_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert row["content_hash"] == expected_hash

    m.close()
