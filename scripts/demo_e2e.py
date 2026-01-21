#!/usr/bin/env python3
"""Demo: deterministic e2e scenario

Starts a small local HTTP server, runs the orchestrator with stub GapDetector
and SeedGenerator, and writes out a JSON and a simple HTML summary to an
output directory for reviewers.

Usage:
  python scripts/demo_e2e.py --output-dir ./demo-out

Note: This is intentionally dependency-free (uses Python stdlib + project code).
"""

import argparse
import json
import re
import tempfile
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from probe.core.map import Map
from probe.core.schema import initialize_schema
from probe.orchestrator import Orchestrator


def make_site(site_dir: Path):
    site_dir.mkdir(parents=True, exist_ok=True)
    p1 = site_dir / "page1.html"
    p2 = site_dir / "page2.html"
    p1.write_text(
        '<html><body><h1>Page 1</h1><a href="page2.html">link</a></body></html>',
        encoding="utf-8",
    )
    p2.write_text(
        "<html><body><h1>Manual</h1><p>driver manual content</p></body></html>",
        encoding="utf-8",
    )


def fetch_fn(url: str):
    req = Request(url, headers={"User-Agent": "demo"})
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


def scorer_fn(page: dict) -> float:
    return 1.0 if "driver" in page.get("text", "") else 0.0


class StubGD:
    def __init__(self, domain):
        self.domain = domain

    def analyze_entity_gaps(self, entity_name, types, include_scores=False):
        return {"suggested_domains": [self.domain]}


class StubSG:
    def __init__(self, seed_url):
        self.seed_url = seed_url

    def generate_seeds(self, suggested_domains, desired_types, **kwargs):
        return [self.seed_url]


def run_demo(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    site_dir = Path(tempfile.mkdtemp(prefix="demo_site_"))
    make_site(site_dir)

    handler = partial(SimpleHTTPRequestHandler, directory=str(site_dir))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    time.sleep(0.1)  # give server a moment to start

    db_path = str(output_dir / "demo_map.db")
    initialize_schema(db_path)
    m = Map(db_path)

    try:
        domain = f"127.0.0.1:{port}"
        seed = f"http://{domain}/page1.html"

        orc = Orchestrator(map_obj=m, fetch_fn=fetch_fn, scorer_fn=scorer_fn)
        res = orc.orchestrate_gap_seed(
            "DemoEntity",
            ["manual"],
            gap_detector=StubGD(domain),
            seed_generator=StubSG(seed),
            max_seeds=5,
            max_depth=2,
            max_pages=10,
        )

        # Build artifact
        artifact = {
            "seeds": res.get("seeds"),
            "crawl_result": res.get("crawl_result"),
            "suggested_domains": res.get("suggested_domains"),
            "domains": [],
            "pages": [],
            "documents": [],
        }

        # domains
        for d in m.get_high_yield_domains(limit=50, min_pages=1):
            artifact["domains"].append(
                {
                    "domain_name": d.domain_name,
                    "pages_crawled": d.pages_crawled,
                    "documents_found": d.documents_found,
                    "yield_score": d.yield_score,
                }
            )

        # pages and documents via direct SQL
        cur = m.conn.execute("SELECT * FROM pages ORDER BY id DESC")
        for r in cur.fetchall():
            artifact["pages"].append(
                {
                    "url": r["url"],
                    "domain": r["domain"],
                    "relevance_score": r["relevance_score"],
                    "last_crawled_at": r["last_crawled_at"],
                }
            )

        cur = m.conn.execute("SELECT * FROM documents ORDER BY id DESC")
        for r in cur.fetchall():
            artifact["documents"].append(
                {
                    "url": r["url"],
                    "doc_type": r["doc_type"],
                    "domain": r["domain"],
                }
            )

        # Write JSON artifact
        out_json = output_dir / "demo_results.json"
        with out_json.open("w", encoding="utf-8") as f:
            json.dump(artifact, f, indent=2)

        # Write simple HTML summary
        out_html = output_dir / "demo_summary.html"
        with out_html.open("w", encoding="utf-8") as f:
            f.write("<html><body><h1>Probe Demo Results</h1>\n")
            f.write(
                f"<h2>Seeds</h2><pre>{json.dumps(artifact['seeds'], indent=2)}</pre>\n"
            )
            f.write(
                f"<h2>Crawl Result</h2><pre>{json.dumps(artifact['crawl_result'], indent=2)}</pre>\n"
            )
            f.write("<h2>Domains</h2><ul>\n")
            for d in artifact["domains"]:
                f.write(
                    f"<li>{d['domain_name']}: pages={d['pages_crawled']} docs={d['documents_found']} yield={d['yield_score']}</li>\n"
                )
            f.write("</ul>\n")
            f.write("<h2>Pages</h2><ul>\n")
            for p in artifact["pages"]:
                f.write(f"<li>{p['url']} (score={p['relevance_score']})</li>\n")
            f.write("</ul>\n")
            f.write("</body></html>")

        print("Demo artifacts written:")
        print(" -", out_json)
        print(" -", out_html)

    finally:
        httpd.shutdown()
        thread.join(timeout=2)
        m.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir", default="./demo-out", help="Directory to write artifacts"
    )
    args = parser.parse_args()
    run_demo(Path(args.output_dir))
