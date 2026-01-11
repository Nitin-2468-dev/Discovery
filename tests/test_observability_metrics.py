from probe.observability import Metrics


def test_metrics_dummy_behavior():
    # Ensure that metrics object has counters and gauges usable without prometheus
    m = Metrics()
    m.increment("fetch_total")
    m.increment("fetch_retries", 2)
    m.observe("fetch_duration_seconds", 0.5)
    m.observe("fetch_backoff_seconds", 1.2)

    # DummyCounter offers get()
    assert hasattr(m.fetch_total, "get") or hasattr(m.fetch_total, "collect")


def test_fetcher_emits_metrics(monkeypatch):
    # Replace the observability.metrics with a dummy that records calls
    class Recorder:
        def __init__(self):
            self.calls = []

        def increment(self, name, value=1):
            self.calls.append(("inc", name, value))

        def observe(self, name, value):
            self.calls.append(("obs", name, value))

    rec = Recorder()
    # Ensure DEFAULT_FETCHER uses our recorder so module-level fetch uses it
    import probe.crawl.fetcher as fetcher_mod

    fetcher_mod.DEFAULT_FETCHER.metrics = rec

    # Now call fetch that will succeed
    import httpx

    transport = httpx.MockTransport(
        lambda req: httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=b"<html></html>",
        )
    )
    original_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client", lambda *args, **kwargs: original_client(transport=transport)
    )

    from probe.crawl.fetcher import fetch

    fetch("https://example.com/test", max_retries=0, backoff_factor=0.1)

    # Recorder should have seen at least a fetch_total increment and duration observed
    assert any(c for c in rec.calls if c[0] == "inc" and c[1] == "fetch_total")
    assert any(
        c for c in rec.calls if c[0] == "obs" and c[1] == "fetch_duration_seconds"
    )
