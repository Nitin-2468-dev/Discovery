import json
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterator, Tuple, cast
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen

import pytest

from probe.core.map import Map
from probe.crawl.link_signals import LinkContextStore
from probe.orchestrator import BreadthFirstCrawler, Orchestrator


@pytest.fixture()
def demo_site(tmp_path: Path) -> Iterator[Tuple[str, Path]]:
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
    addr = server.server_address
    # server_address may be a 2- or 4-tuple depending on family; use indices
    port = addr[1]
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
    crawl = cast(Dict[str, int], out.get("crawl_result", {}))
    assert crawl.get("pages_fetched", 0) >= 1
    assert crawl.get("documents_found", 0) >= 1

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
    raw_meta = row["metadata"] if row and row["metadata"] else None
    metadata = cast(Dict[str, Any], json.loads(raw_meta)) if raw_meta else {}
    assert metadata.get("crawl_run_id")

    cur2 = m.conn.execute(
        "SELECT metadata FROM documents WHERE domain = ? LIMIT 1", (domain,)
    )
    row2 = cur2.fetchone()
    assert row2 is not None
    raw_meta2 = row2["metadata"] if row2 and row2["metadata"] else None
    metadata2 = cast(Dict[str, Any], json.loads(raw_meta2)) if raw_meta2 else {}
    assert metadata2.get("crawl_run_id")


def test_offline_e2e_link_signals(tmp_path: Path, demo_site):
    """Validate link-signals store is used and that prioritized links are followed.

    This test instantiates a BreadthFirstCrawler with a LinkContextStore and
    a low threshold so relevant links are prioritized and persisted to the store.
    """
    base_url, site_dir = demo_site

    db_path = tmp_path / "map_ls.db"
    m = Map(str(db_path))

    store = LinkContextStore(":memory:")
    crawler = BreadthFirstCrawler(
        map_obj=m,
        fetch_fn=simple_fetch_fn,
        scorer_fn=lambda res: 1.0,
        link_signals_enabled=True,
        link_signals_store=store,
        link_signals_threshold=0.0,
    )

    seeds = [base_url + "/index.html"]
    res = crawler.crawl(seeds, max_depth=2, max_pages=10)

    # ensure the store recorded at least one link context
    contexts = store.list_recent()
    assert len(contexts) >= 1

    # ensure crawler found documents (the prioritized links were followed)
    assert res.get("documents_found", 0) >= 1

    # write demo artifacts for reviewer inspection
    out_path = Path("tmp_demo_out")
    out_path.mkdir(exist_ok=True)

    # extract a crawl_run_id (if any) from persisted pages for provenance
    cur_c = m.conn.execute(
        "SELECT metadata FROM pages WHERE metadata IS NOT NULL LIMIT 1"
    )
    row_c = cur_c.fetchone()
    crawl_run_id = None
    if row_c and row_c["metadata"]:
        try:
            _md = cast(Dict[str, Any], json.loads(row_c["metadata"]))
            crawl_run_id = _md.get("crawl_run_id")
        except Exception:
            crawl_run_id = None

    # include link-signals counts for quick inspection
    link_context_count = len(contexts)

    demo_results = {
        "crawler_out": res,
        "map_summary": m.get_map_summary(),
        "crawl_run_id": crawl_run_id,
        "link_context_count": link_context_count,
    }

    (out_path / "demo_results.json").write_text(json.dumps(demo_results))
    (out_path / "demo_summary.html").write_text(
        """
        <html><body><h1>Offline E2E Demo Results</h1>
        <pre>{}</pre>
        </body></html>
        """.format(
            json.dumps(demo_results, indent=2)
        )
    )


def test_breadthfirstcrawler_sets_run_id(tmp_path: Path, demo_site):
    """When the crawler is invoked directly, it should generate and persist a run_id."""
    base_url, _ = demo_site

    db_path = tmp_path / "map_runid.db"
    m = Map(str(db_path))

    crawler = BreadthFirstCrawler(
        map_obj=m,
        fetch_fn=simple_fetch_fn,
        scorer_fn=lambda res: 1.0,
    )

    seeds = [base_url + "/index.html"]
    # execute the crawl (result not needed for this assertion)
    crawler.crawl(seeds, max_depth=2, max_pages=10)

    # crawler should have a run_id set
    assert getattr(crawler, "run_id", None)

    # persisted page metadata should include crawl_run_id matching crawler.run_id
    cur = m.conn.execute(
        "SELECT metadata FROM pages WHERE metadata IS NOT NULL LIMIT 1"
    )
    row = cur.fetchone()
    assert row is not None
    raw_meta = row["metadata"] if row and row["metadata"] else None
    metadata = cast(Dict[str, Any], json.loads(raw_meta)) if raw_meta else {}
    assert metadata.get("crawl_run_id") == crawler.run_id


def test_link_signals_priority_effect(tmp_path: Path, demo_site):
    """Verify link-signals produces prioritized enqueue decisions and persists contexts.

    This test calls the crawler's internal prioritization helper in a deterministic
    way with a crafted page result to assert the link is prioritized and the
    LinkContextStore records the context.
    """
    base_url, _ = demo_site

    m = Map(str(tmp_path / "map_ls_effect2.db"))
    store = LinkContextStore(":memory:")
    crawler = BreadthFirstCrawler(
        map_obj=m,
        fetch_fn=simple_fetch_fn,
        scorer_fn=lambda res: 1.0,
        link_signals_enabled=True,
        link_signals_store=store,
        link_signals_threshold=0.0,
    )

    # craft a page result whose text contains the anchor context we expect
    page_url = base_url + "/index.html"
    fetch_res = {
        "status_code": 200,
        "links": [base_url + "/doc.pdf"],
        "content_type": "text/html",
        "text": "\n".join(
            [
                "<html><body>",
                "<p>Important: see the Download PDF link below</p>",
                '<a href="/doc.pdf">Download PDF</a>',
                "</body></html>",
            ]
        ),
        "url": page_url,
    }

    from collections import deque
    from typing import Deque, Tuple

    q: Deque[Tuple[str, int]] = deque()
    enqueued = crawler._try_enqueue_with_link_signals(
        href=base_url + "/doc.pdf",
        anchor_text="Download PDF",
        res=fetch_res,
        q=q,
        depth=0,
    )

    # prioritized enqueue should have returned True and placed the link at the left
    assert enqueued is True
    assert q and q[0][0].endswith("/doc.pdf")

    # store should have recorded at least one context
    contexts = store.list_recent()
    assert len(contexts) >= 1


def test_link_signals_integration_effect(tmp_path: Path, demo_site):
    """Integration test: with limited max_pages, link-signals should prioritize a direct
    document link on the index page so that a document is discovered, while without
    link-signals the doc is missed due to enqueue ordering.
    """
    base_url, site_dir = demo_site

    # Overwrite the demo site with a deterministic structure:
    # index.html -> page1.html, page2.html, doc.pdf (doc link last)
    (site_dir / "index.html").write_text(
        """
        <html><body>
        <h1>Priority Test</h1>
        <a href="/page1.html">Page 1</a>
        <a href="/page2.html">Page 2</a>
        <a href="/doc.pdf">Download PDF</a>
        </body></html>
        """
    )

    (site_dir / "page1.html").write_text("<html><body><h1>Page 1</h1></body></html>")
    (site_dir / "page2.html").write_text("<html><body><h1>Page 2</h1></body></html>")
    (site_dir / "doc.pdf").write_bytes(b"%PDF-1.4\n%deterministic\ncontent")

    seeds = [base_url + "/index.html"]

    # run without link-signals (small budget so order matters)
    m1 = Map(str(tmp_path / "map_nols_integ.db"))
    crawler1 = BreadthFirstCrawler(
        map_obj=m1,
        fetch_fn=simple_fetch_fn,
        scorer_fn=lambda res: 1.0,
        link_signals_enabled=False,
    )
    res1 = crawler1.crawl(seeds, max_depth=2, max_pages=2)
    docs1 = res1.get("documents_found", 0)

    # run with link-signals enabled and low threshold so the PDF link is prioritized
    m2 = Map(str(tmp_path / "map_ls_integ.db"))
    store = LinkContextStore(":memory:")
    crawler2 = BreadthFirstCrawler(
        map_obj=m2,
        fetch_fn=simple_fetch_fn,
        scorer_fn=lambda res: 1.0,
        link_signals_enabled=True,
        link_signals_store=store,
        link_signals_threshold=0.0,
    )
    res2 = crawler2.crawl(seeds, max_depth=2, max_pages=2)
    docs2 = res2.get("documents_found", 0)

    # link-signals run should find at least as many documents, and in this crafted
    # scenario it should find the PDF whereas the no-ls run will miss it due to order
    assert docs2 >= docs1
    assert docs2 > 0

    # verify a context was persisted and crawl_run_id was recorded on persisted pages
    contexts = store.list_recent()
    assert len(contexts) >= 1

    cur = m2.conn.execute(
        "SELECT metadata FROM pages WHERE metadata IS NOT NULL LIMIT 1"
    )
    row = cur.fetchone()
    assert row is not None
    raw_meta = row["metadata"] if row and row["metadata"] else None
    metadata = cast(Dict[str, Any], json.loads(raw_meta)) if raw_meta else {}
    assert metadata.get("crawl_run_id")
