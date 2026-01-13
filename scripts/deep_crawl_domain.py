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


def _get_seed_urls(m: Map, domain: str) -> List[str]:
    """Return seed URLs for a domain from DB or the domain root if none found."""
    pages = get_pages_for_domain(m, domain)
    out: List[str] = []
    for p in pages:
        url = p.get("url") if isinstance(p, dict) else p[1]
        if url and url not in out:
            out.append(url)

    if not out:
        out.append(f"https://{domain}/")

    return out


def _fetch_and_ingest(fetcher_module, m: Map, url: str, *, timeout: int = 10) -> dict | None:
    """Fetch a URL via the fetcher module and ingest it into the Map on success.

    Returns the fetch result dict on success, or None on error.
    """
    try:
        res = fetcher_module.fetch(url, timeout=timeout, max_retries=2, max_size=2000000)
    except Exception:
        return None

    if res.get("error"):
        return None

    ingest_fetch_result(m, res)
    return res


def _extract_same_domain_links(result: dict, domain: str) -> List[str]:
    """Return a list of same-domain links extracted from a fetch result."""
    out: List[str] = []
    links = result.get("links") or []
    from urllib.parse import urlparse

    for link in links:
        lurl = link.get("url")
        if not lurl:
            continue
        if lurl.startswith("//"):
            continue
        parsed = urlparse(lurl)
        if parsed.netloc != domain:
            continue
        out.append(lurl)
    return out


def run_deep_crawl(db_path: str, domain: str, depth: int = 1, limit: int = 100):
    """Traverse and ingest pages for a domain up to a specified depth and limit.

    This version decomposes behavior into smaller units for testability and
    to reduce complexity (Ruff C901).
    """
    fetcher = __import__("probe.crawl.fetcher", fromlist=["fetch"])  # module
    m = Map(db_path)

    seen: Set[str] = set()
    queue = _get_seed_urls(m, domain)
    for u in queue:
        seen.add(u)

    depth_level = 0
    fetched = 0

    while queue and depth_level <= depth and fetched < limit:
        next_queue: List[str] = []
        for url in queue:
            if fetched >= limit:
                break

            res = _fetch_and_ingest(fetcher, m, url)
            if not res:
                continue

            fetched += 1

            links = _extract_same_domain_links(res, domain)
            for lurl in links:
                if lurl not in seen:
                    seen.add(lurl)
                    next_queue.append(lurl)

            # politeness
            time.sleep(0.5)

        queue = next_queue
        depth_level += 1

    m.close()
    return fetched


if __name__ == "__main__":
    args = parse_args()
    n = run_deep_crawl(args.db, args.domain, depth=args.depth, limit=args.limit)
    print(f"Fetched {n} pages for domain {args.domain}")
