from probe.core.map import Map
from probe.orchestrator import BreadthFirstCrawler, Orchestrator
from probe.policy import Mode, PolicyEngine


def test_bfs_follows_links_and_scores(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # Simple fetcher that returns a page with two links and content-type
    def fake_fetch(url):
        return {
            "status_code": 200,
            "content_type": "text/html",
            "links": ["http://a.example/p1", "http://b.example/p2"],
        }

    # Scorer giving moderate score to all pages
    def fake_score(page):
        return 0.5

    crawler = BreadthFirstCrawler(m, fake_fetch, fake_score)
    out = crawler.crawl(["http://start.example/"], max_depth=1, max_pages=10)

    assert out["pages_fetched"] >= 1
    # Links should be followed (2 pages follow) within depth 1
    assert out["pages_fetched"] >= 3


def test_policy_blocks_denied_domains(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # fetcher that would return a page if called
    def fake_fetch(url):
        return {"status_code": 200, "content_type": "text/html", "links": []}

    def fake_score(page):
        return 0.9

    pe = PolicyEngine(mode=Mode.PUBLIC_GUARDED)

    crawler = BreadthFirstCrawler(m, fake_fetch, fake_score, policy_engine=pe)

    # malicious.example is deny-listed in PolicyEngine defaults
    out = crawler.crawl(["http://malicious.example/doc.pdf"], max_depth=1, max_pages=10)

    # should have skipped the page entirely
    assert out["pages_fetched"] == 0
    assert out["documents_found"] == 0


def test_orchestrator_runs_and_returns_summary(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    def fake_fetch(url):
        # single pdf page
        return {"status_code": 200, "content_type": "application/pdf", "links": []}

    def fake_score(page):
        return 1.0

    orch = Orchestrator(m, fake_fetch, fake_score)
    res = orch.run(["http://example.com/manual.pdf"], max_depth=0, max_pages=5)
    assert res["pages_fetched"] == 1
    assert res["documents_found"] == 1
