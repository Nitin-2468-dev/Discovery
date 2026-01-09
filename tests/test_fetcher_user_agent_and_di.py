import httpx
from probe.crawl.fetcher import Fetcher


def test_user_agent_rotation(monkeypatch):
    uas = ["UA-A", "UA-B"]
    seen = []

    def handler(request):
        seen.append(request.headers.get("user-agent"))
        return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, content=b"<html></html>")

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: original_client(transport=transport, **kwargs))

    f = Fetcher(user_agents=uas)
    f.fetch("https://example.com/a")
    f.fetch("https://example.com/b")

    assert seen[0] != seen[1]
    assert seen[0] in uas and seen[1] in uas


def test_metrics_injection(monkeypatch):
    class Recorder:
        def __init__(self):
            self.calls = []
        def increment(self, name, value=1):
            self.calls.append(("inc", name, value))
        def observe(self, name, value):
            self.calls.append(("obs", name, value))

    rec = Recorder()

    transport = httpx.MockTransport(lambda req: httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, content=b"<html></html>"))
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: original_client(transport=transport))

    f = Fetcher(user_agents=["x"], metrics_obj=rec)
    f.fetch("https://example.com/test")

    assert any(c for c in rec.calls if c[0] == 'inc' and c[1] == 'fetch_total')
