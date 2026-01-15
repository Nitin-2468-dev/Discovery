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
                # policy check
                if not self._policy_allows(url):
                    return

                domain = self._domain_from_url(url)

                def task(u=url, d=depth, dom=domain):
                    # politeness
                    self._wait_for_domain(dom)
                    try:
                        res = self.fetch(u)
                    except Exception:
                        return {"url": u, "error": "fetch_error"}

                    # persist last-crawled time if enabled
                    try:
                        from probe.crawl.state import set_last_crawled

                        if dom:
                            from datetime import datetime

                            set_last_crawled(dom, datetime.utcnow())
                    except Exception:
                        pass

                    return {"url": u, "res": res}

                futures.add(ex.submit(task))

            # seed initial scheduling
            while q and len(futures) < self.concurrency and pages_fetched < max_pages:
                url, depth = q.popleft()
                if url in visited or depth > max_depth:
                    continue
                visited.add(url)
                schedule(url, depth)

            while futures and pages_fetched < max_pages:
                done, _ = as_completed(futures, timeout=None), None
                for fut in done:
                    try:
                        r = fut.result()
                    except Exception:
                        r = {"url": None, "error": "task_error"}

                    futures.discard(fut)

                    if r.get("error"):
                        continue

                    pages_fetched += 1
                    res = r.get("res") or {}
                    url = r.get("url")

                    # scoring & enqueue
                    score = float(self.score(res))
                    if score >= 0.1:
                        # enqueue children if within depth
                        # We assume links are list of urls or dicts with 'url'
                        links = res.get("links", []) or []
                        for link in links:
                            href = link if isinstance(link, str) else link.get("url")
                            if href and href not in visited:
                                q.append((href, 0))

                    # detect docs
                    ct = res.get("content_type") or ""
                    if "pdf" in ct or (
                        isinstance(url, str) and url.lower().endswith(".pdf")
                    ):
                        docs_found += 1

                    # schedule next from queue if available
                    while (
                        q
                        and len(futures) < self.concurrency
                        and pages_fetched < max_pages
                    ):
                        nu, nd = q.popleft()
                        if nu in visited or nd > max_depth:
                            continue
                        visited.add(nu)
                        schedule(nu, nd)

        return {"pages_fetched": pages_fetched, "documents_found": docs_found}
