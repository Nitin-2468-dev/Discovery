from probe.core.map import Map
from probe.core.map_adapter import MapAdapter
from probe.orchestrator import Orchestrator


class DummyGapDetector:
    def __init__(self, domain):
        self.domain = domain

    def analyze_entity_gaps(self, entity_name, desired_doc_types, include_scores=False):
        return {"suggested_domains": [self.domain]}


class DummySeedGenerator:
    def __init__(self, base_url):
        self.base_url = base_url

    def generate_seeds(
        self, suggested_domains, desired_doc_types, per_domain=3, max_seeds=20
    ):
        return [self.base_url + "/index.html"]


def test_orchestrator_accepts_map_adapter(tmp_path):
    # Create a small local site and HTTP server (minimal inline fixture)
    site_dir = tmp_path / "demo_site_local"
    site_dir.mkdir()
    (site_dir / "index.html").write_text(
        '<html><body><h1>Hi</h1><a href="/doc.pdf">PDF</a></body></html>'
    )
    (site_dir / "doc.pdf").write_bytes(b"%PDF-1.4\n%demo\ncontent")

    import threading
    import time
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(site_dir), **kwargs)

        def log_message(self, format, *args):
            pass

    server = ThreadingHTTPServer(("", 0), Handler)
    port = server.server_address[1]
    base_url = f"http://127.0.0.1:{port}"
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.05)

    db = tmp_path / "map_adapter_orch.db"
    m = Map(str(db))
    adapter = MapAdapter(m)

    orch = Orchestrator(
        adapter,
        lambda u: {
            "status_code": 200,
            "links": [],
            "content_type": "text/html",
            "text": "",
            "url": u,
        },
        lambda res: 1.0,
    )

    gd = DummyGapDetector(base_url.replace("http://", ""))
    sg = DummySeedGenerator(base_url)

    out = orch.orchestrate_gap_seed(
        "E", ["pdf"], gap_detector=gd, seed_generator=sg, max_depth=1, max_pages=5
    )

    # shutdown
    server.shutdown()
    t.join(timeout=1)

    assert "crawl_result" in out
    # map_summary should reflect at least one page crawled
    summary = adapter.get_map_summary()
    assert summary["pages"] >= 1
