from probe.crawl.fetcher_adapter import FetcherAdapter


def test_fetcher_adapter_monkeypatch(monkeypatch):
    adapter = FetcherAdapter()

    def fake_fetch(url, **kwargs):
        return {"url": url, "status_code": 200, "text": "ok"}

    monkeypatch.setattr(adapter._fetcher, "fetch", fake_fetch)

    res = adapter.fetch_url("http://example.local")
    assert res["status_code"] == 200
    assert res["url"] == "http://example.local"
