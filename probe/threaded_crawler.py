"""Threaded crawler with per-domain politeness and PolicyEngine checks.

This is a small, testable threaded crawler built on a thread pool. It accepts
injected `time_func` and `sleep_func` to make per-domain delays testable without
real sleeping.
"""

import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Iterable, Optional, Set

from probe.policy import PolicyEngine


class ThreadedCrawler:
    def __init__(
        self,
        fetch_fn: Callable,
        scorer_fn: Callable,
        policy_engine: Optional[PolicyEngine] = None,
        concurrency: int = 4,
        per_domain_delay: float = 0.25,
        time_func: Callable = None,
        sleep_func: Callable = None,
        persistent_politeness: bool = False,
    ):
        self.fetch = fetch_fn
        self.score = scorer_fn
        self.policy = policy_engine
        self.concurrency = max(1, int(concurrency))
        self.per_domain_delay = float(per_domain_delay)
        self.time = time_func or __import__("time").monotonic
        self.sleep = sleep_func or __import__("time").sleep
        self.persistent_politeness = bool(persistent_politeness)

        # domain -> last fetch monotonic time
        self._domain_last: Dict[str, float] = {}
        self._domain_lock = threading.Lock()

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

    def _wait_for_domain(self, domain: str) -> None:
        if not domain:
            return
        with self._domain_lock:
            last = self._domain_last.get(domain, 0.0)
            now = self.time()

            # If persistent politeness is enabled and we don't have an in-memory
            # last-crawled time for the domain, attempt to load it from state file
            if last == 0.0 and self.persistent_politeness:
                try:
                    from probe.crawl.state import get_last_crawled

                    last_dt = get_last_crawled(domain)
                    if last_dt:
                        # Convert wall-clock last_dt to a monotonic baseline comparable with self.time()
                        now_mon = self.time()
                        now_epoch = __import__("time").time()
                        last_epoch = last_dt.timestamp()
                        last_mon = now_mon - (now_epoch - last_epoch)
                        last = last_mon
                except Exception:
                    pass

            wait = max(0.0, self.per_domain_delay - (now - last))
            if wait > 0:
                self.sleep(wait)
                now = self.time()
            self._domain_last[domain] = now

    def _make_task(self, url: str, domain: Optional[str]):
        def task():
            self._wait_for_domain(domain)
            try:
                res = self.fetch(url)
            except Exception:
                return {"url": url, "error": "fetch_error"}

            if self.persistent_politeness and domain:
                try:
                    from datetime import datetime

                    from probe.crawl.state import set_last_crawled

                    set_last_crawled(domain, datetime.utcnow())
                except Exception:
                    pass

            return {"url": url, "res": res}

        return task

    def _enqueue_links(self, res: Dict, visited: Set[str], q: deque):
        links = res.get("links", []) or []
        for link in links:
            href = link if isinstance(link, str) else link.get("url")
            if href and href not in visited:
                q.append((href, 0))

    def _is_document(self, url: str, res: Dict) -> bool:
        ct = res.get("content_type") or ""
        return "pdf" in ct or (isinstance(url, str) and url.lower().endswith(".pdf"))

    def _process_result(
        self, r: Dict, visited: Set[str], q: deque, max_depth: int
    ) -> tuple[int, int]:
        # returns (pages_increment, docs_increment)
        if r.get("error"):
            return 0, 0
        res = r.get("res") or {}
        url = r.get("url")

        # scoring & enqueue children
        try:
            score = float(self.score(res))
        except Exception:
            score = 0.0

        if score >= 0.1:
            self._enqueue_links(res, visited, q)

        docs_inc = 1 if self._is_document(url, res) else 0
        return 1, docs_inc

    def _process_futures_loop(
        self,
        futures: Set,
        q: deque,
        visited: Set[str],
        pages_fetched: int,
        docs_found: int,
        ex: ThreadPoolExecutor,
        max_depth: int,
        max_pages: int,
    ) -> tuple[int, int]:
        while futures and pages_fetched < max_pages:
            for fut in as_completed(list(futures)):
                if pages_fetched >= max_pages:
                    break
                try:
                    r = fut.result()
                except Exception:
                    r = {"url": None, "error": "task_error"}

                futures.discard(fut)

                inc_pages, inc_docs = self._process_result(r, visited, q, max_depth)
                if inc_pages == 0:
                    continue

                pages_fetched += inc_pages
                docs_found += inc_docs

                # schedule next items from the queue
                while (
                    q and len(futures) < self.concurrency and pages_fetched < max_pages
                ):
                    nu, nd = q.popleft()
                    if nu in visited or nd > max_depth:
                        continue
                    visited.add(nu)
                    if not self._policy_allows(nu):
                        continue
                    domain = self._domain_from_url(nu)
                    futures.add(ex.submit(self._make_task(nu, domain)))

        return pages_fetched, docs_found

    def crawl(
        self, seeds: Iterable[str], max_depth: int = 1, max_pages: int = 50
    ) -> Dict[str, int]:
        visited: Set[str] = set()
        q = deque([(s, 0) for s in seeds])
        pages_fetched = 0
        docs_found = 0

        with ThreadPoolExecutor(max_workers=self.concurrency) as ex:
            futures = set()

            def schedule(url, depth):
                if not self._policy_allows(url):
                    return
                domain = self._domain_from_url(url)
                futures.add(ex.submit(self._make_task(url, domain)))

            # seed initial scheduling
            while q and len(futures) < self.concurrency and pages_fetched < max_pages:
                url, depth = q.popleft()
                if url in visited or depth > max_depth:
                    continue
                visited.add(url)
                schedule(url, depth)

            # process completed fetches, schedule more as capacity becomes available
            pages_fetched, docs_found = self._process_futures_loop(
                futures, q, visited, pages_fetched, docs_found, ex, max_depth, max_pages
            )

        return {"pages_fetched": pages_fetched, "documents_found": docs_found}
