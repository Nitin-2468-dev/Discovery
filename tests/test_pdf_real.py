import io

import httpx
import pytest

from probe.crawl.fetcher import fetch


def test_real_pdf_extraction(tmp_path, monkeypatch):
    # Skip if reportlab not available
    pytest.importorskip("reportlab")
    from reportlab.pdfgen import canvas

    # Create a simple PDF in memory
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, "Real PDF Text for testing")
    c.showPage()
    c.save()
    pdf_bytes = buf.getvalue()

    def handler(request):
        return httpx.Response(
            200, headers={"content-type": "application/pdf"}, content=pdf_bytes
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)

    # Patch httpx.Client used inside fetch to our client
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: client)

    res = fetch("https://example.org/doc.pdf")
    assert res["is_pdf"] is True
    assert "Real PDF Text for testing" in res["text"]
