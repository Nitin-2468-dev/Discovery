from probe.core.map import Map
from probe.crawl.ingest import Ingestor


def test_ingest_separates_internal_and_external_links(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)
    ing = Ingestor(m)

    fetch_result = {
        "url": "https://example.com/page.html",
        "title": "Page",
        "text": "Some text",
        "links": [
            {"url": "https://example.com/about", "text": "About"},
            {"url": "https://external.com/x", "text": "External"},
            {"url": "mailto:foo@example.com", "text": "Mail"},
        ],
    }

    res = ing.ingest_fetch_result(fetch_result)

    # One internal edge should be created (to /about)
    assert res["edges_created"] == 1
    assert "https://external.com/x" in res["external_links"]
    assert "https://example.com/about" in res["outgoing_links"]

    m.close()
