import httpx
from probe.crawl.fetcher import Fetcher


def test_pdf_ocr_fallback(monkeypatch):
    # simulate pdfplumber.open raising, and ensure _ocr_pdf is called
    pdf_bytes = b"%PDF-1.4 fake pdf content"

    def handler(request):
        return httpx.Response(200, headers={"content-type": "application/pdf"}, content=pdf_bytes)

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: original_client(transport=transport))

    # make pdfplumber.open raise
    import types, sys
    fake_pdfplumber = types.SimpleNamespace(open=lambda f: (_ for _ in ()).throw(Exception("fail")))
    monkeypatch.setitem(sys.modules, "pdfplumber", fake_pdfplumber)

    # monkeypatch _ocr_pdf to return OCR text without needing external deps
    import probe.crawl.fetcher as fetcher_mod
    monkeypatch.setattr(fetcher_mod, "_ocr_pdf", lambda b: "OCR TEXT")

    f = Fetcher()
    res = f.fetch("https://example.com/doc.pdf")
    assert res.get("is_pdf")
    assert res.get("text") == "OCR TEXT"
    assert res.get("metadata", {}).get("ocr_used") is True
