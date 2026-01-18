from probe.orchestrator import BreadthFirstCrawler
from probe.crawl.link_signals import LinkContextStore


def test_link_signals_prioritize_links(tmp_path):
    # fake fetcher that returns a page containing two links, one with strong driver context
    calls = []

    def fake_fetch(url):
        calls.append(url)
        if url == "http://start/":
            text = "Intro\nSome docs\nDownload driver for RTL8111\nLink anchor here"
            return {
                "url": url,
                "status_code": 200,
                "text": text,
                "links": [
                    {"url": "http://example.com/a", "text": "Download driver for RTL8111"},
                    {"url": "http://example.com/b", "text": "Other link"},
                ],
                "content_type": "text/html",
            }
        else:
            return {"url": url, "status_code": 200, "text": "leaf", "links": [], "content_type": "text/html"}

    store = LinkContextStore(str(tmp_path / "lc.db"))
    crawler = BreadthFirstCrawler(fetch_fn=fake_fetch, scorer_fn=lambda r: 1.0, link_signals_enabled=True, link_signals_store=store, link_signals_threshold=0.2)
    crawler.crawl(["http://start/"], max_depth=1, max_pages=10)

    # Order of fetches: start -> prioritized link (a) -> other link (b)
    assert calls[0] == "http://start/"
    assert calls[1] == "http://example.com/a"
    assert calls[2] == "http://example.com/b"

    # Ensure link_context stored for the prioritized link
    rows = store.list_recent(10)
    assert any(r.to_url == "http://example.com/a" for r in rows)
