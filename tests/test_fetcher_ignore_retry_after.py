import httpx

from probe.crawl.fetcher import fetch


def test_fetcher_honors_flag_to_ignore_retry_after(monkeypatch):
    calls = []
    sleeps = []

    def handler(request):
        if len(calls) == 0:
            calls.append("first")
            return httpx.Response(429, headers={"Retry-After": "5"})
        else:
            calls.append("second")
            return httpx.Response(
                200,
                headers={"content-type": "text/html; charset=utf-8"},
                content=b"<html></html>",
            )

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client", lambda *args, **kwargs: original_client(transport=transport)
    )

    def fake_sleep(s):
        sleeps.append(s)

    # When honoring is disabled, first sleep should be backoff (0.5)
    res = fetch(
        "https://example.com/x",
        max_retries=1,
        backoff_factor=0.5,
        honor_retry_after=False,
        sleep_func=fake_sleep,
    )
    assert res.get("status_code") == 200
    assert len(sleeps) == 1
    assert abs(sleeps[0] - 0.5) < 1e-6

    # Reset and test honoring enabled -> sleep should be ~5 seconds
    calls.clear()
    sleeps.clear()
    res = fetch(
        "https://example.com/x",
        max_retries=1,
        backoff_factor=0.5,
        honor_retry_after=True,
        sleep_func=fake_sleep,
    )
    assert res.get("status_code") == 200
    assert len(sleeps) == 1
    assert sleeps[0] >= 4.5
