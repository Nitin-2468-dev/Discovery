from probe.crawl.fetcher import fetch
from probe.crawl.ingest import ingest_fetch_result
from probe.core.map import Map
import httpx


def test_ingest_html_adds_page(monkeypatch, tmp_path):
    html = "<html><head><title>Hi</title></head><body><p>Hi</p></body></html>"

    def handler(request):
        return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, content=html.encode("utf-8"))

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: client)

    res = fetch("https://example.org/")

    m = Map(db_path=":memory:")
    out = ingest_fetch_result(m, res)
    summary = m.get_map_summary()
    assert summary["pages"] == 1
    assert summary["documents"] == 0


def test_ingest_pdf_adds_document(monkeypatch):
    pdf_bytes = b"%PDF-1.4 fake pdf content"

    def handler(request):
        return httpx.Response(200, headers={"content-type": "application/pdf"}, content=pdf_bytes)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: client)

    # fake pdfplumber to return a single page text
    import sys, types

    class DummyPage:
        def extract_text(self):
            return "Doc page"

    class DummyPDF:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        @property
        def pages(self):
            return [DummyPage()]

    fake = types.SimpleNamespace(open=lambda f: DummyPDF())
    monkeypatch.setitem(sys.modules, "pdfplumber", fake)

    res = fetch("https://example.org/doc.pdf")
    m = Map(db_path=":memory:")
    out = ingest_fetch_result(m, res)
    summary = m.get_map_summary()
    assert summary["documents"] == 1
    assert summary["pages"] == 0
