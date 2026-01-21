from probe.threaded_crawler import ThreadedCrawler


def test_threaded_crawler_respects_per_domain_delay(monkeypatch):
    # fake time and sleep
    fake_time = {"t": 0.0}

    def time_func():
        return fake_time["t"]

    def sleep_func(s):
        # advance fake time
        fake_time["t"] += s

    calls = []

    def fake_fetch(url):
        calls.append((url, time_func()))
        return {"status_code": 200, "content_type": "text/html", "links": []}

    def fake_score(page):
        return 0.0

    tc = ThreadedCrawler(
        fake_fetch,
        fake_score,
        concurrency=2,
        per_domain_delay=1.0,
        time_func=time_func,
        sleep_func=sleep_func,
    )

    seeds = ["http://same.example/a", "http://same.example/b"]
    res = tc.crawl(seeds, max_depth=0, max_pages=10)

    assert res["pages_fetched"] == 2
    # calls should show timestamps separated by at least per_domain_delay
    assert len(calls) == 2
    t0 = calls[0][1]
    t1 = calls[1][1]
    assert t1 - t0 >= 1.0


def test_threaded_crawler_fetches_multiple_domains(monkeypatch):
    calls = []

    def fake_fetch(url):
        calls.append(url)
        return {"status_code": 200, "content_type": "text/html", "links": []}

    def fake_score(page):
        return 0.0

    tc = ThreadedCrawler(fake_fetch, fake_score, concurrency=2, per_domain_delay=0.0)
    seeds = ["http://a.example/x", "http://b.example/y"]
    res = tc.crawl(seeds, max_depth=0, max_pages=10)

    assert res["pages_fetched"] == 2
    assert set(calls) == set(seeds)
