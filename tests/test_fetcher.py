import httpx

from probe.crawl.fetcher import fetch


def test_fetch_html_returns_text_and_links(monkeypatch):
    html = """
    <html>
      <head><title>Test</title></head>
      <body>
        <h1>Heading</h1>
        <a href="/about">About us</a>
        <script>var secret = 1</script>
      </body>
    </html>
    """

    def handler(request):
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=html.encode("utf-8"),
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)

    # Patch httpx.Client used inside fetch to our client
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: client)

    res = fetch("https://example.com/")
    assert res["status_code"] == 200
    assert "Heading" in res["text"]
    assert any(link["url"] == "https://example.com/about" for link in res["links"])
    assert "var secret" not in res["text"]


def test_fetch_handles_404(monkeypatch):
    def handler(request):
        return httpx.Response(
            404,
            headers={"content-type": "text/html; charset=utf-8"},
            content=b"Not Found",
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: client)

    res = fetch("https://example.com/missing")
    assert res["status_code"] == 404
    assert res["error"] == "http_404"


def test_fetch_timeout_reports_error(monkeypatch):
    def handler(request):
        raise httpx.ReadTimeout("timeout")

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: client)

    res = fetch("https://example.com/slow", timeout=0.001)
    assert res["error"] == "timeout"


def test_fetch_429_retries_until_success(monkeypatch):
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(
                429, headers={"retry-after": "0"}, content=b"Too Many Requests"
            )
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=b'<html><body><p>OK</p><a href="/next">Next</a></body></html>',
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: client)

    # Avoid sleeping in tests
    res = fetch("https://example.com/", timeout=1)
    assert res["status_code"] == 200
    assert any(link["url"] == "https://example.com/next" for link in res["links"])


def test_fetch_max_size_exceeded(monkeypatch):
    big = b"a" * 1025

    def handler(request):
        return httpx.Response(
            200, headers={"content-type": "text/html; charset=utf-8"}, content=big
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: client)

    res = fetch("https://example.com/large", max_size=1000)
    assert res["error"] == "max_size_exceeded"


def test_fetch_pdf_extraction_success(monkeypatch):
    pdf_bytes = b"%PDF-1.4 fake pdf content"

    def handler(request):
        return httpx.Response(
            200, headers={"content-type": "application/pdf"}, content=pdf_bytes
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: client)

    # Provide a fake pdfplumber module
    import sys
    import types

    class DummyPage:
        def extract_text(self):
            return "Page one"

    class DummyPDF:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        @property
        def pages(self):
            return [DummyPage()]

    fake = types.SimpleNamespace(open=lambda f: DummyPDF())
    monkeypatch.setitem(sys.modules, "pdfplumber", fake)

    res = fetch("https://example.com/doc.pdf")
    assert res["is_pdf"] is True
    assert "Page one" in res["text"]
