import json
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Tuple
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen

import pytest

from probe.core.map import Map
from probe.orchestrator import Orchestrator


@pytest.fixture()
def demo_site(tmp_path: Path) -> Tuple[str, Path]:
    """Create a small demo site and run a simple HTTP server to serve it."""
    site_dir = tmp_path / "demo_site"
    site_dir.mkdir()

    # index page linking to a PDF and another page
    (site_dir / "index.html").write_text(
        """
        <html><body>
        <h1>Demo Index</h1>
        <p>This is a demo page mentioning driver and manual.</p>
        <a href="/doc.pdf">Download PDF</a>
        <a href="/page2.html">Page 2</a>
        </body></html>
        """
    )

    (site_dir / "page2.html").write_text(
        """
        <html><body>
        <h1>Page Two</h1>
        <p>Another page with useful content.</p>
        <a href="/doc2.pdf">PDF 2</a>
        </body></html>
        """
    )

    # simple PDF bytes (not a real PDF, but content-type will be application/pdf)
    (site_dir / "doc.pdf").write_bytes(b"%PDF-1.4\n%demo\nThis is a fake pdf file")
    (site_dir / "doc2.pdf").write_bytes(b"%PDF-1.4\n%demo2\nAnother fake pdf file")

    # start HTTP server in background thread
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(site_dir), **kwargs)

        def log_message(self, format, *args):
            # suppress logs during tests
            pass

    server = ThreadingHTTPServer(("", 0), Handler)
    host, port = server.server_address
    # server binds to 0.0.0.0; use localhost for client connections
    base_url = f"http://127.0.0.1:{port}"

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    # wait briefly for server to be ready
    time.sleep(0.1)

    yield base_url, site_dir

    # teardown
    server.shutdown()
    t.join(timeout=1)


def simple_fetch_fn(url: str):
    """Fetch the URL using urllib and return the lightweight dict used by the crawler."""
    try:
        with urlopen(url, timeout=5) as resp:
            status = resp.getcode()
            content_type = resp.headers.get_content_type()
            raw = resp.read()
            text = None
            if content_type == "text/html":
                try:
                    text = raw.decode("utf-8")
                except Exception:
                    text = ""
            else:
                text = ""

            # naive link extraction for demo purposes
            links = []
            if text:
                import re

                for m in re.findall(r"href=\"([^\"]+)\"", text):
                    # make absolute
                    if urlparse(m).netloc:
                        links.append(m)
                    else:
                        links.append(urljoin(url, m))

            return {
                "status_code": status,
                "links": links,
                "content_type": content_type,
                "text": text,
                "url": url,
            }
    except Exception:
        return {
            "status_code": 500,
            "links": [],
            "content_type": "",
            "text": "",
            "url": url,
        }


class FakeGapDetector:
    def __init__(self, domain: str):
        self.domain = domain

    def analyze_entity_gaps(
        self, entity_name: str, desired_doc_types, include_scores=False
    ):
        return {"suggested_domains": [self.domain]}


class FakeSeedGenerator:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def generate_seeds(
        self, suggested_domains, desired_doc_types, per_domain=3, max_seeds=20
    ):
        # just return the base URL for each domain
        seeds = []
        for d in suggested_domains:
            seeds.append(self.base_url + "/index.html")
        return seeds


def test_offline_e2e_smoke(tmp_path: Path, demo_site):
    base_url, site_dir = demo_site
    # domain is host:port
    domain = urlparse(base_url).netloc

    db_path = tmp_path / "map.db"
    m = Map(str(db_path))

    orchestrator = Orchestrator(m, simple_fetch_fn, lambda res: 1.0)

    # ensure previously empty
    summary_before = m.get_map_summary()
    assert summary_before["documents"] == 0

    gd = FakeGapDetector(domain)
    sg = FakeSeedGenerator(base_url)

    out = orchestrator.orchestrate_gap_seed(
        "Test Entity",
        ["pdf"],
        gap_detector=gd,
        seed_generator=sg,
        max_depth=2,
        max_pages=10,
    )

    # validate crawl result
    assert out["crawl_result"]["pages_fetched"] >= 1
    assert out["crawl_result"]["documents_found"] >= 1

    # validate map now has documents and domain stats updated
    summary_after = m.get_map_summary()
    assert summary_after["documents"] >= 1
    dom = m.get_domain(domain)
    assert dom is not None
    assert dom.documents_found >= 1

    # check provenance attached to at least one page/document
    cur = m.conn.execute(
        "SELECT metadata FROM pages WHERE domain = ? LIMIT 1", (domain,)
    )
    row = cur.fetchone()
    assert row is not None
    metadata = json.loads(row[0]) if row and row[0] else {}
    assert "crawl_run_id" in metadata and metadata["crawl_run_id"]

    cur2 = m.conn.execute(
        "SELECT metadata FROM documents WHERE domain = ? LIMIT 1", (domain,)
    )
    row2 = cur2.fetchone()
    assert row2 is not None
    metadata2 = json.loads(row2[0]) if row2 and row2[0] else {}
    assert "crawl_run_id" in metadata2 and metadata2["crawl_run_id"]
