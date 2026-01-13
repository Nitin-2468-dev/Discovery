import sys
import types

from scripts.deep_crawl_domain import run_deep_crawl


def test_run_deep_crawl_basic(monkeypatch):
    # Replace fetcher module with a fake module that returns simple results
    fetch_calls = []

    def fake_fetch(url, timeout=10, max_retries=2, max_size=2000000):
        fetch_calls.append(url)
        # return a link to another page on the same domain the first time
        if len(fetch_calls) == 1:
            return {"links": [{"url": "https://example.com/next"}]}
        # second fetch returns no links
        return {"links": []}

    fake_fetcher_mod = types.SimpleNamespace(fetch=fake_fetch)
    monkeypatch.setitem(sys.modules, "probe.crawl.fetcher", fake_fetcher_mod)

    # Prevent DB access by monkeypatching get_pages_for_domain to return empty
    monkeypatch.setattr("scripts.deep_crawl_domain.get_pages_for_domain", lambda m, d: [])

    # Stub Map to avoid DB dependency
    class DummyMap:
        def __init__(self, *args, **kwargs):
            pass

        def close(self):
            pass

    monkeypatch.setattr("scripts.deep_crawl_domain.Map", DummyMap)

    # Stub ingest to simply record calls
    ingested = []

    def fake_ingest(m, res):
        ingested.append(res)

    monkeypatch.setattr("scripts.deep_crawl_domain.ingest_fetch_result", fake_ingest)

    n = run_deep_crawl("ignored.db", "example.com", depth=1, limit=10)

    assert n == 2
    assert len(fetch_calls) == 2
    assert len(ingested) == 2
