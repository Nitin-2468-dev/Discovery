#!/usr/bin/env python3
"""Follow internal links for a domain found in a DB and ingest pages up to a given depth."""
from __future__ import annotations

import argparse
import json
import time
from typing import List, Set

from probe.core.map import Map
from probe.crawl.ingest import ingest_fetch_result


def parse_args(argv: List[str] | None = None):
    p = argparse.ArgumentParser(description="Deep crawl domain and ingest pages")
    p.add_argument("--db", required=True, help="Path to DB file")
    p.add_argument("--domain", required=True, help="Domain to crawl (netloc)")
    p.add_argument(
        "--depth", type=int, default=1, help="Depth to follow outgoing internal links"
    )
    p.add_argument("--limit", type=int, default=100, help="Maximum pages to fetch")
    return p.parse_args(argv)


def get_pages_for_domain(m: Map, domain: str) -> List[dict]:
    # direct SQL access for simplicity
    cur = m.conn.execute(
        "SELECT id, url, metadata FROM pages WHERE domain = ?", (domain,)
    )
    out = []
    for r in cur.fetchall():
        md = json.loads(r[2]) if r[2] else {}
        out.append({"id": r[0], "url": r[1], "metadata": md})
    return out


def run_deep_crawl(
    db_path: str, domain: str, depth: int = 1, limit: int = 100
):  # noqa: C901 - script helper; scheduled for refactor
    fetcher = __import__("probe.crawl.fetcher", fromlist=["fetch"])  # module
    m = Map(db_path)

    seen: Set[str] = set()
    queue: List[str] = []

    # seed from existing pages for the domain
    pages = get_pages_for_domain(m, domain)
    for p in pages:
        if p["url"] not in seen:
            queue.append(p["url"])
            seen.add(p["url"])

    # If no pages present, try to add a root domain URL
    if not queue:
        root = f"https://{domain}/"
        queue.append(root)
        seen.add(root)

    depth_level = 0
    fetched = 0

    while queue and depth_level <= depth and fetched < limit:
        next_queue: List[str] = []
        for url in queue:
            if fetched >= limit:
                break
            try:
                res = fetcher.fetch(url, timeout=10, max_retries=2, max_size=2000000)
            except Exception:
                continue
            if res.get("error"):
                continue

            ingest_fetch_result(m, res)
            fetched += 1

            # extract outgoing_links from result or metadata
            links = res.get("links") or []
            for link in links:
                lurl = link.get("url")
                if not lurl:
                    continue
                # keep only same domain
                if lurl.startswith("//"):
                    continue
                from urllib.parse import urlparse

                parsed = urlparse(lurl)
                if parsed.netloc != domain:
                    continue
                if lurl not in seen:
                    seen.add(lurl)
                    next_queue.append(lurl)

            # polite sleep
            time.sleep(0.5)

        queue = next_queue
        depth_level += 1

    m.close()
    return fetched


if __name__ == "__main__":
    args = parse_args()
    n = run_deep_crawl(args.db, args.domain, depth=args.depth, limit=args.limit)
    print(f"Fetched {n} pages for domain {args.domain}")
