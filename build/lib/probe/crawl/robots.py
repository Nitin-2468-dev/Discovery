"""Robots.txt helper with caching.

Provides:
- can_fetch(user_agent, url) -> bool
- crawl_delay(user_agent, url) -> Optional[float]
- clear_cache() for tests

Behavior:
- Fetches robots.txt via httpx and parses with urllib.robotparser.RobotFileParser
- Caches parser per domain for TTL (default 24h)
- On errors fetching/parsing, treats as permissive (returns True) and logs nothing
"""
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from datetime import datetime, timedelta, timezone
from typing import Optional
import threading

import httpx


CACHE_TTL = timedelta(hours=24)

_lock = threading.Lock()
_cache = {}  # domain -> (parser, fetched_at)


def _robots_url_for(domain: str, scheme: str = "https") -> str:
    return f"{scheme}://{domain}/robots.txt"


def clear_cache():
    with _lock:
        _cache.clear()


def _fetch_and_parse(domain: str) -> Optional[RobotFileParser]:
    url_https = _robots_url_for(domain, scheme="https")
    url_http = _robots_url_for(domain, scheme="http")

    # Try HTTPS then HTTP
    for url in (url_https, url_http):
        try:
            with httpx.Client(timeout=5.0, headers={"User-Agent": "probe/0.1"}) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    text = resp.text
                    rp = RobotFileParser()
                    rp.parse(text.splitlines())
                    rp.set_url(url)
                    return rp
        except Exception:
            continue
    return None


def _get_parser(domain: str) -> Optional[RobotFileParser]:
    now = datetime.now(timezone.utc)
    with _lock:
        entry = _cache.get(domain)
        if entry:
            rp, fetched = entry
            if now - fetched < CACHE_TTL:
                return rp
        # fetch anew
    rp = _fetch_and_parse(domain)
    with _lock:
        _cache[domain] = (rp, now)
    return rp


def can_fetch(user_agent: str, url: str) -> bool:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        rp = _get_parser(domain)
        if rp is None:
            # treat permissive on failure
            return True
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True


def crawl_delay(user_agent: str, url: str) -> Optional[float]:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        rp = _get_parser(domain)
        if rp is None:
            return None
        return rp.crawl_delay(user_agent)
    except Exception:
        return None
