"""Orchestrator and simple breadth-first crawler for v0.5.

This module provides a minimal, synchronous BreadthFirstCrawler and an
Orchestrator facade. The focus is on small, testable behavior: crawl
from seeds breadth-first, score pages using RelevanceScorer, and
respect PolicyEngine decisions and per-domain denylists.

The implementation is intentionally small — follow-up PRs will add
concurrency, better politeness, and richer stop conditions.
"""

from collections import deque
from typing import Callable, Dict, Iterable, List, Optional, Set

from probe.core.map import Map
from probe.policy import PolicyEngine


class BreadthFirstCrawler:
    """Simple synchronous breadth-first crawler.

    Args:
        map_obj: Map instance to record findings
        fetch_fn: callable(url) -> fetch result dict (status_code, links)
        scorer_fn: callable(page) -> float (0.0-1.0 relevance)
        policy_engine: PolicyEngine to consult about domains
    """

    def __init__(
        self,
        map_obj: Optional[Map] = None,
        fetch_fn: Optional[Callable] = None,
        scorer_fn: Optional[Callable] = None,
        policy_engine: Optional[PolicyEngine] = None,
    ) -> None:
        # Allow zero-arg construction for compatibility with different
        # packaging/import scenarios (CI historically ran stale imports).
        self.map = map_obj
        self.fetch = fetch_fn or (
            lambda url: {"status_code": 404, "links": [], "content_type": ""}
        )
        self.score = scorer_fn or (lambda page: 0.0)
        self.policy = policy_engine

    def _domain_from_url(self, url: str) -> Optional[str]:
        try:
            from urllib.parse import urlparse

            return urlparse(url).netloc
        except Exception:
            return None

    def _policy_allows(self, url: str) -> bool:
        if not self.policy:
            return True
        domain = self._domain_from_url(url)
        if not domain:
            return True
        decision = self.policy.evaluate_query("fetch", context={"domain": domain})
        return bool(decision.get("allowed", True))

    def _enqueue_links(
        self, q: deque, res: Dict, depth: int, max_depth: int, visited: Set[str]
    ):
        if depth >= max_depth:
            return
        for link in res.get("links", []) or []:
            href = link if isinstance(link, str) else link.get("url")
            if href and href not in visited:
                q.append((href, depth + 1))

    def _is_document(self, url: str, res: Dict) -> bool:
        ct = res.get("content_type") or ""
        return "pdf" in ct or (isinstance(url, str) and url.lower().endswith(".pdf"))

    def crawl(
        self, seeds: Iterable[str], max_depth: int = 2, max_pages: int = 50
    ) -> Dict[str, int]:
        visited: Set[str] = set()
        q = deque([(s, 0) for s in seeds])
        pages_fetched = 0
        docs_found = 0

        while q and pages_fetched < max_pages:
            url, depth = q.popleft()
            if url in visited or depth > max_depth:
                continue

            if not self._policy_allows(url):
                visited.add(url)
                continue

            try:
                res = self.fetch(url)
            except Exception:
                visited.add(url)
                continue

            pages_fetched += 1
            visited.add(url)

            # Score page and decide whether to follow links
            score = float(self.score(res))
            if score >= 0.1:
                self._enqueue_links(q, res, depth, max_depth, visited)

            if self._is_document(url, res):
                docs_found += 1

        return {"pages_fetched": pages_fetched, "documents_found": docs_found}


class Orchestrator:
    """Facade that composes GapDetector/SeedGenerator/Fetcher/Scorer into a run.

    This is a minimal orchestrator that runs a breadth-first crawl and
    persists scoring/reporting to the Map.
    """

    def __init__(
        self,
        map_obj: Map,
        fetch_fn: Callable,
        scorer_fn: Callable,
        policy_engine: Optional[PolicyEngine] = None,
    ):
        self.map = map_obj
        self.crawler = BreadthFirstCrawler(map_obj, fetch_fn, scorer_fn, policy_engine)

    def run(
        self, seeds: List[str], max_depth: int = 2, max_pages: int = 50
    ) -> Dict[str, int]:
        return self.crawler.crawl(seeds, max_depth=max_depth, max_pages=max_pages)
