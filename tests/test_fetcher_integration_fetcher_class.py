import httpx

from probe.core.map import Map
from probe.crawl.cleaner import clean_html
from probe.crawl.fetcher import Fetcher
from probe.crawl.ingest import Ingestor
from probe.crawl.seed_loader import SeedLoader


def test_fetcher_integration_end_to_end(
    monkeypatch, tmp_path
):  # noqa: C901 - integration test; can be split later
    # Prepare seeds file
    seeds_file = tmp_path / "s.txt"
    seeds_file.write_text(
        "https://site1.example/a\nhttps://site2.example/b\nhttps://site1.example/c\n"
    )

    # Simple responses: site1 a and c are HTML, site2 b is PDF
    def handler(request):
        url = str(request.url)
        if url.endswith("/a"):
            html = '<html><head><title>A</title></head><body><p>Page A</p><a href="/about">About</a></body></html>'
            return httpx.Response(
                200,
                headers={"content-type": "text/html; charset=utf-8"},
                content=html.encode("utf-8"),
            )
        if url.endswith("/c"):
            html = '<html><head><title>C</title></head><body><p>Page C</p><a href="https://external.example/x">Ext</a></body></html>'
            return httpx.Response(
                200,
                headers={"content-type": "text/html; charset=utf-8"},
                content=html.encode("utf-8"),
            )
        if url.endswith("/b"):
            # return a PDF response
            pdf_bytes = b"%PDF-1.4 fake"
            return httpx.Response(
                200, headers={"content-type": "application/pdf"}, content=pdf_bytes
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda *args, **kwargs: original_client(transport=transport, **kwargs),
    )

    # Fake pdfplumber for PDF extraction
    import sys
    import types

    class DummyPage:
        def extract_text(self):
            return "PDF content"

    class DummyPDF:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        @property
        def pages(self):
            return [DummyPage()]

    fake_pdfplumber = types.SimpleNamespace(open=lambda f: DummyPDF())
    monkeypatch.setitem(sys.modules, "pdfplumber", fake_pdfplumber)

    # Run pipeline using Fetcher class
    loader = SeedLoader()
    urls = loader.load_file(str(seeds_file))

    m = Map(db_path=str(tmp_path / "probe.db"))
    ing = Ingestor(m)

    fetcher = Fetcher()

    for u in urls:
        res = fetcher.fetch(u)
        # For HTML, verify cleaning works
        if res.get("content_type", "").startswith("text/html"):
            cleaned = clean_html(res.get("raw_bytes").decode("utf-8"), u)
            res["title"] = cleaned.get("title")
            res["links"] = cleaned.get("links")
        ing.ingest_fetch_result(res)

    # Assertions: pages and documents persisted
    summary = m.get_map_summary()
    assert summary["pages"] >= 3  # main pages + linked pages
    assert summary["documents"] >= 1  # site2.pdf should be a document

    # Check edges exist for links from site1/a
    cursor = m.conn.execute(
        "SELECT id FROM pages WHERE url = ?", ("https://site1.example/a",)
    )
    row = cursor.fetchone()
    assert row is not None
    page_id = row["id"]
    edges = m.get_edges_from("page", page_id, relation="links_to")
    assert len(edges) >= 1

    m.close()
