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

from probe.core.map import Document, Map, Page
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
        link_signals_enabled: bool = False,
        link_signals_store: Optional[object] = None,
        link_signals_threshold: float = 0.5,
    ) -> None:
        # Allow zero-arg construction for compatibility with different
        # packaging/import scenarios (CI historically ran stale imports).
        self.map = map_obj
        self.fetch = fetch_fn or (
            lambda url: {"status_code": 404, "links": [], "content_type": ""}
        )
        self.score = scorer_fn or (lambda page: 0.0)
        self.policy = policy_engine
        # Link signals (v0.5) - opt-in feature
        self.link_signals_enabled = bool(link_signals_enabled)
        self.link_signals_store = link_signals_store
        self.link_signals_threshold = float(link_signals_threshold)

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
        # optional link-signals integration (v0.5)
        use_link_signals = (
            self.link_signals_enabled and self.link_signals_store is not None
        )
        for link in res.get("links", []) or []:
            href = link if isinstance(link, str) else link.get("url")
            anchor_text = None if isinstance(link, str) else link.get("text")
            if not href or href in visited:
                continue

            if use_link_signals:
                # Try to handle the link using link-signals; if it returns True the link
                # was prioritized and enqueued to the left.
                if self._process_link_with_signals(href, anchor_text, res, q, depth):
                    continue

            q.append((href, depth + 1))

    def _process_link_with_signals(
        self, href: str, anchor_text: Optional[str], res: Dict, q: deque, depth: int
    ) -> bool:
        """Attempt to analyze the link using link-signals and prioritize it.

        Returns True if the link was prioritized and enqueued to the left.
        Any exception is swallowed to preserve crawl robustness.
        """
        try:
            # build a simple lines context from page text and find anchor index
            text = res.get("text") or ""
            lines = text.splitlines() or [text]
            anchor_idx = 0
            if anchor_text:
                for i, ln in enumerate(lines):
                    if anchor_text in ln:
                        anchor_idx = i
                        break

            # import lazily to avoid circular imports at module load
            from probe.crawl.link_signals import analyze_link_from_lines

            ctx = analyze_link_from_lines(
                res.get("url") or "", href, lines, anchor_idx, mode="lines", radius=5
            )
            # persist to store (best-effort)
            try:
                # link_signals_store may be e.g. LinkContextStore or a wrapper with insert(ctx)
                if hasattr(self.link_signals_store, "insert"):
                    self.link_signals_store.insert(ctx)
            except Exception:
                pass

            # prioritize if score >= threshold
            if float(ctx.relevance_score) >= float(self.link_signals_threshold):
                q.appendleft((href, depth + 1))
                return True
        except Exception:
            # on any failure in link-signals, fall back to normal enqueue
            pass
        return False

    def _is_document(self, url: str, res: Dict) -> bool:
        ct = res.get("content_type") or ""
        return "pdf" in ct or (isinstance(url, str) and url.lower().endswith(".pdf"))

    def _persist_findings(self, url: str, res: Dict) -> int:
        """Persist page and document (when applicable) to the Map.

        Returns 1 if a document was recorded, 0 otherwise.
        """
        if not self.map:
            return 0
        try:
            from datetime import datetime

            domain = self._domain_from_url(url) or ""
            page = Page(
                id=None,
                url=url,
                domain=domain,
                title=None,
                content_hash=None,
                relevance_score=float(self.score(res)),
                metadata=None,
                last_crawled_at=datetime.utcnow().isoformat() + "Z",
            )
            try:
                self.map.add_page(page)
            except Exception:
                pass

            if self._is_document(url, res):
                doc_type = (
                    "pdf"
                    if "pdf" in (res.get("content_type") or "")
                    or (isinstance(url, str) and url.lower().endswith(".pdf"))
                    else "other"
                )
                document = Document(
                    id=None,
                    title=page.title or "",
                    doc_type=doc_type,
                    hash="",
                    url=url,
                    domain=domain,
                )
                try:
                    self.map.add_document(document)
                    try:
                        self.map.update_domain_stats(domain, True)
                    except Exception:
                        pass
                except Exception:
                    pass
                return 1
        except Exception:
            pass
        return 0

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

            # Persist findings (page + optional document) and update counts
            docs_found += self._persist_findings(url, res)

            # Score page and decide whether to follow links
            score = float(self.score(res))
            if score >= 0.1:
                self._enqueue_links(q, res, depth, max_depth, visited)

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
        """Run a crawl and persist findings to the Map when available.

        The BreadthFirstCrawler returns counts; when a `Map` instance is
        provided to the crawler, the Orchestrator ensures pages and
        discovered documents are persisted using `Map.add_page` and
        `Map.add_document`, and updates domain statistics.
        """
        out = self.crawler.crawl(seeds, max_depth=max_depth, max_pages=max_pages)

        # Persist to map if crawler produced page-level results on `self.map`.
        # For the lightweight BreadthFirstCrawler, we don't have per-page
        # structured results available. If future crawlers provide them,
        # this is where we would turn the per-page findings into Map entries.
        # Instead, as a minimal first step, we will update domain-level stats
        # for the run based on reported counts when possible.
        try:
            # Example: update domain summary by reading domains found in the map
            # or by applying a simple rule: documents_found increments to domain stats
            # are a useful first-order approximation.
            # TODO: extend to per-page persistence when crawler yields page details.
            pass
        except Exception:
            pass

        return out
