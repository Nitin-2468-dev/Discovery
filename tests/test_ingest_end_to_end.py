from probe.crawl.ingest import Ingestor
from probe.core.map import Map


def test_ingestor_creates_link_pages_and_edges(tmp_path):
    db = str(tmp_path / "test.db")
    m = Map(db_path=db)

    fetch_res = {
        "url": "https://example.com/page",
        "text": "Hello world",
        "title": "Example Page",
        "links": [
            {"url": "https://example.com/about", "text": "About"},
            {"url": "https://other.com/who", "text": "Who"},
        ],
        "raw_bytes": b"<html>...",
    }

    ing = Ingestor(m)
    out = ing.ingest_fetch_result(fetch_res)

    assert isinstance(out.get("page_id"), int)
    assert out.get("link_count") == 2
    assert out.get("edges_created") == 2

    summary = m.get_map_summary()
    # main page + 2 linked pages
    assert summary["pages"] >= 3
    assert summary["edges"] >= 2

    # verify edges from the main page
    page_id = out.get("page_id")
    edges = m.get_edges_from("page", page_id, relation="links_to")
    assert len(edges) == 2

    m.close()