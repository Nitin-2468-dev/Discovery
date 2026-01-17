from pathlib import Path

import httpx

from probe.crawl.fetcher import fetch


def test_committed_pdf_fixture_works():
    fixture = Path("tests/fixtures/sample.pdf").read_bytes()

    def handler(request):
        return httpx.Response(
            200, headers={"content-type": "application/pdf"}, content=fixture
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)

    # patch httpx.Client inside fetcher
    import httpx as _httpx

    _orig_client = _httpx.Client
    _httpx.Client = lambda *args, **kwargs: client

    try:
        res = fetch("https://example.org/doc.pdf")
        assert res["is_pdf"] is True
        assert "Sample fixture PDF text" in res["text"]
    finally:
        _httpx.Client = _orig_client
