import logging
import httpx
from probe.crawl.fetcher import fetch


def test_retry_after_parsing_is_logged(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    calls = []

    # Use a numeric Retry-After to make expected sleep deterministic
    def handler(request):
        if len(calls) == 0:
            calls.append('first')
            return httpx.Response(429, headers={'Retry-After': '2'})
        else:
            calls.append('second')
            return httpx.Response(200, headers={'content-type': 'text/html; charset=utf-8'}, content=b"<html></html>")

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: original_client(transport=transport))

    def fake_sleep(s):
        # no-op, just to keep test fast
        pass

    with caplog.at_level(logging.DEBUG):
        res = fetch("https://example.com/x", max_retries=1, backoff_factor=0.5, sleep_func=fake_sleep)

    # Ensure a debug message about Retry-After parsing exists
    found = any("Retry-After header" in rec.getMessage() for rec in caplog.records)
    assert found
