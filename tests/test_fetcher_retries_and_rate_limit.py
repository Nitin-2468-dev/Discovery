import time
import httpx
from probe.crawl.fetcher import fetch


def test_fetch_retries_on_429_uses_retry_after_and_backoff(monkeypatch):
    calls = []
    sleeps = []

    def handler(request):
        # First call returns 429 with Retry-After header, second call 200
        if len(calls) == 0:
            calls.append('first')
            return httpx.Response(429, headers={'retry-after': '1'})
        else:
            calls.append('second')
            return httpx.Response(200, headers={'content-type': 'text/html; charset=utf-8'}, content=b"<html><title>OK</title></html>")

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: original_client(transport=transport))

    def fake_sleep(s):
        sleeps.append(s)

    res = fetch("https://example.com/resource", max_retries=2, backoff_factor=0.5, sleep_func=fake_sleep)
    assert res.get('status_code') == 200
    # ensure at least one sleep occurred and retry-after (1) or backoff was used
    assert any(s >= 1 or abs(s - 1.0) < 1e-6 for s in sleeps)


def test_per_domain_min_delay_enforced(monkeypatch):
    sleeps = []

    def handler(request):
        return httpx.Response(200, headers={'content-type': 'text/html; charset=utf-8'}, content=b"<html></html>")

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: original_client(transport=transport))

    def fake_sleep(s):
        sleeps.append(s)

    # First call should not sleep; second call to same domain with min_delay should sleep
    res1 = fetch("https://example.com/a", min_delay=1.5, sleep_func=fake_sleep)
    res2 = fetch("https://example.com/b", min_delay=1.5, sleep_func=fake_sleep)

    assert res1.get('status_code') == 200
    assert res2.get('status_code') == 200
    assert len(sleeps) >= 1
    assert sleeps[0] >= 1.5 * 0.6
