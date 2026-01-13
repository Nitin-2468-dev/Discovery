"""FetcherAdapter: small wrapper to expose a compatible fetch interface for the crawler/tests.

This adapter delegates to `probe.crawl.fetcher.Fetcher` but provides a tiny stable shim
that higher-level code (and tests) can import without depending on Fetcher internals.
"""

from typing import Any, Dict

from probe.crawl.fetcher import Fetcher


class FetcherAdapter:
    def __init__(self, **kwargs: Any) -> None:
        self._fetcher = Fetcher(**kwargs)

    def fetch_url(self, url: str, **kwargs: Any) -> Dict[str, Any]:
        """Fetch a URL and return the dict-shaped result from Fetcher.fetch."""
        return self._fetcher.fetch(url, **kwargs)
