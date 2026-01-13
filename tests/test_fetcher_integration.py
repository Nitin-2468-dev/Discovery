import httpx

from probe.core.map import Map
from probe.crawl.cleaner import clean_html
from probe.crawl.fetcher import fetch
from probe.crawl.ingest import Ingestor
from probe.crawl.seed_loader import SeedLoader




def _make_transport_and_patch(monkeypatch):
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
        httpx, "Client", lambda *args, **kwargs: original_client(transport=transport)
    )


def _patch_pdfplumber(monkeypatch):
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


def _setup_env(monkeypatch, tmp_path):
    seeds_file = tmp_path / "s.txt"
    seeds_file.write_text(
        "https://site1.example/a\nhttps://site2.example/b\nhttps://site1.example/c\n"
    )

    _make_transport_and_patch(monkeypatch)
    _patch_pdfplumber(monkeypatch)

    loader = SeedLoader()
    urls = loader.load_file(str(seeds_file))

    m = Map(db_path=str(tmp_path / "probe.db"))
    ing = Ingestor(m)

    return urls, m, ing


def _run_pipeline_and_ingest(fetch_fn, urls, ing):
    for u in urls:
        res = fetch_fn(u)
        # For HTML, verify cleaning works
        if res.get("content_type", "").startswith("text/html"):
            cleaned = clean_html(res.get("raw_bytes").decode("utf-8"), u)
            res["title"] = cleaned.get("title")
            res["links"] = cleaned.get("links")
        ing.ingest_fetch_result(res)


def test_fetcher_ingest_html_pages(monkeypatch, tmp_path):
    urls, m, ing = _setup_env(monkeypatch, tmp_path)
    _run_pipeline_and_ingest(fetch, urls, ing)

    summary = m.get_map_summary()
    assert summary["pages"] >= 2  # site1 a and c

    m.close()


def test_fetcher_ingest_pdf_document(monkeypatch, tmp_path):
    urls, m, ing = _setup_env(monkeypatch, tmp_path)
    _run_pipeline_and_ingest(fetch, urls, ing)

    summary = m.get_map_summary()
    assert summary["documents"] >= 1  # site2.pdf

    m.close()


def test_fetcher_links_edges(monkeypatch, tmp_path):
    urls, m, ing = _setup_env(monkeypatch, tmp_path)
    _run_pipeline_and_ingest(fetch, urls, ing)

    cursor = m.conn.execute(
        "SELECT id FROM pages WHERE url = ?", ("https://site1.example/a",)
    )
    row = cursor.fetchone()
    assert row is not None
    page_id = row["id"]
    edges = m.get_edges_from("page", page_id, relation="links_to")
    assert len(edges) >= 1

    m.close()
