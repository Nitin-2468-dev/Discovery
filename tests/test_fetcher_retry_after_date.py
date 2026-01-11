from datetime import datetime, timezone, timedelta
import httpx
from probe.crawl.fetcher import fetch


def test_retry_after_http_date_parsing(monkeypatch):
    calls = []
    sleeps = []

    # build a Retry-After date a few seconds in the future
    future = (datetime.now(timezone.utc) + timedelta(seconds=2)).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    def handler(request):
        # first call returns 429 with HTTP-date Retry-After, second returns 200
        if len(calls) == 0:
            calls.append("first")
            return httpx.Response(429, headers={"Retry-After": future})
        else:
            calls.append("second")
            return httpx.Response(
                200,
                headers={"content-type": "text/html; charset=utf-8"},
                content=b"<html><title>OK</title></html>",
            )

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client", lambda *args, **kwargs: original_client(transport=transport)
    )

    def fake_sleep(s):
        sleeps.append(s)

    res = fetch(
        "https://example.com/resource",
        max_retries=2,
        backoff_factor=0.5,
        sleep_func=fake_sleep,
    )
    assert res.get("status_code") == 200
    # ensure at least one sleep occurred and value is at least ~1s (allow scheduling leeway)
    assert len(sleeps) >= 1
    assert any(s >= 1.0 for s in sleeps)
