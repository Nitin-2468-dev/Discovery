import os
from datetime import datetime, timedelta


from probe.crawl import state
from probe.threaded_crawler import ThreadedCrawler


def test_persistent_politeness_respects_state(tmp_path):
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        domain = "same.example"
        # set last crawled to now - 0.5s
        state.set_last_crawled(domain, datetime.utcnow() - timedelta(seconds=0.5))

        import time as _time

        # Align fake monotonic baseline with real monotonic clock so persistent wall-clock state maps correctly
        fake_time = {"t": _time.monotonic()}

        def time_func():
            return fake_time["t"]

        def sleep_func(s):
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
            concurrency=1,
            per_domain_delay=1.0,
            time_func=time_func,
            sleep_func=sleep_func,
            persistent_politeness=True,
        )

        seeds = [f"http://{domain}/a", f"http://{domain}/b"]
        res = tc.crawl(seeds, max_depth=0, max_pages=10)

        assert res["pages_fetched"] == 2
        assert len(calls) == 2
        t0 = calls[0][1]
        t1 = calls[1][1]
        # Because last_crawled was 0.5s ago, the first call should be at time 0 and second at >= 1.0
        assert t0 >= 0.0
        assert t1 - t0 >= 1.0
    finally:
        os.chdir(cwd)
