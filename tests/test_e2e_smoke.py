import os
import re
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import pytest

from probe.core.map import Map
from probe.core.schema import initialize_schema
from probe.orchestrator import Orchestrator


@pytest.mark.skipif(
    os.getenv("RUN_REAL_NET_TESTS") != "true",
    reason="Real-network/integration tests disabled; set RUN_REAL_NET_TESTS=true to enable",
)
def test_orchestrator_e2e_smoke(tmp_path):
    """Deterministic e2e smoke test using a local HTTP server.

    Steps:
      - Start a local static server serving two simple pages (page1 -> page2)
      - Use a small Orchestrator with a simple fetch and scorer
      - Provide stub GapDetector and SeedGenerator that point to the server
      - Run orchestrate_gap_seed and assert Map was updated with domain stats
    """
    # Create simple website
    site_dir = tmp_path / "site"
    site_dir.mkdir()

    page1 = site_dir / "page1.html"
    page2 = site_dir / "page2.html"
    page1.write_text(
        '<html><body><h1>Page 1</h1><a href="page2.html">link</a></body></html>',
        encoding="utf-8",
    )
    # page2 contains a keyword "driver" so our simple scorer can treat it as relevant
    page2.write_text(
        "<html><body><h1>Manual</h1><p>driver manual content</p></body></html>",
        encoding="utf-8",
    )

    # Start HTTP server on an ephemeral port
    handler = partial(SimpleHTTPRequestHandler, directory=str(site_dir))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    try:
        # small helper fetch_fn that returns the shape expected by the crawler
        def fetch_fn(url: str):
            req = Request(url, headers={"User-Agent": "pytest"})
            with urlopen(req, timeout=5) as r:
                raw = r.read()
                text = raw.decode("utf-8", errors="ignore")
                links = [urljoin(url, m) for m in re.findall(r'href="([^"]+)"', text)]
                content_type = r.headers.get("Content-Type", "text/html")
                return {
                    "url": url,
                    "status_code": r.getcode(),
                    "text": text,
                    "raw_bytes": raw,
                    "links": links,
                    "content_type": content_type,
                }

        # trivial scorer: returns 1.0 if keyword 'driver' in text else 0.0
        def scorer_fn(page: dict) -> float:
            return 1.0 if "driver" in page.get("text", "") else 0.0

        # Setup Map + DB
        db_path = str(tmp_path / "test_map.db")
        initialize_schema(db_path)
        m = Map(db_path)

        # stub GapDetector returning the test domain
        class StubGD:
            def analyze_entity_gaps(self, entity_name, types, include_scores=False):
                return {"suggested_domains": [f"127.0.0.1:{port}"]}

        # stub SeedGenerator returning a seed for the domain
        class StubSG:
            def generate_seeds(self, suggested_domains, desired_types, **kwargs):
                # produce page1 as a starting seed for the domain
                return [f"http://127.0.0.1:{port}/page1.html"]

        # Build orchestrator with real fetcher/scorer
        orc = Orchestrator(map_obj=m, fetch_fn=fetch_fn, scorer_fn=scorer_fn)

        res = orc.orchestrate_gap_seed(
            "TestEntity",
            ["manual"],
            gap_detector=StubGD(),
            seed_generator=StubSG(),
            max_seeds=5,
            max_depth=2,
            max_pages=10,
        )

        # Assertions: seeds generated and crawl result fetched pages
        assert isinstance(res, dict)
        assert res.get("seeds")
        assert (
            res.get("crawl_result") and res["crawl_result"].get("pages_fetched", 0) > 0
        )

        # Map should have updated domain stats for the test domain
        domains = m.get_high_yield_domains(limit=10, min_pages=1)
        found = False
        for d in domains:
            if d.domain_name == f"127.0.0.1:{port}" or d.domain_name == "127.0.0.1":
                found = True
                assert d.pages_crawled >= 1
        assert found, "Expected to find the test domain in high-yield domains"

    finally:
        # Shutdown server
        httpd.shutdown()
        thread.join(timeout=2)
        m.close()
