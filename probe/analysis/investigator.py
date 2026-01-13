from typing import Any, Dict, List

from probe.analysis.seed_generator import SeedGenerator
from probe.core.map import Map


def _load_gap_detector_cls():
    """Dynamically import and return the GapDetector class with diagnostics on failure."""
    try:
        import importlib

        mod = importlib.import_module("probe.analysis.gaps")
        if not hasattr(mod, "GapDetector"):
            raise ImportError(
                f"'GapDetector' not in module; members: {[n for n in dir(mod) if not n.startswith('_')]}"
            )
        return mod.GapDetector
    except Exception as e:
        raise ImportError(
            f"Could not import GapDetector from probe.analysis.gaps: {e}"
        ) from e


def _domain_yield_score(map_obj: Map, seed_url: str) -> float:
    try:
        from urllib.parse import urlparse

        d = urlparse(seed_url).netloc
        dom = map_obj.get_domain(d)
        return dom.yield_score if dom else 0.0
    except Exception:
        return 0.0


class Investigator:
    """Orchestrates a short investigation loop.

    It is intentionally minimal for v0.4: detect gaps, generate seeds, and
    optionally perform a limited fetch pass for the generated seeds.
    """

    def __init__(self, map_obj: Map, *, ingest_on_fetch: bool = False):
        self.map = map_obj
        # When True, fetched seed pages will be ingested into the provided Map
        self.ingest_on_fetch = bool(ingest_on_fetch)

    def _maybe_apply_ingest_feedback(
        self, seed_url: str, ingested: Dict[str, Any]
    ) -> None:
        """If ingest produced a document, increment the domain document count."""
        try:
            domain = (
                __import__("urllib.parse", fromlist=["urlparse"])
                .urlparse(seed_url)
                .netloc
            )
            found_doc = bool(ingested.get("document_id")) or (
                ingested.get("edges_created", 0) > 0
            )
            for out in ingested.get("outgoing_links", []):
                if out.lower().endswith(".pdf"):
                    found_doc = True
                    break
            if found_doc:
                self.map.increment_domain_documents(domain, delta=1)
        except Exception:
            # best-effort: swallow errors and continue
            pass

    def _fetch_seeds(
        self, seeds: List[str], fetch_timeout: float
    ) -> List[Dict[str, Any]]:
        """Perform best-effort fetches for seeds, ingesting if configured."""
        from probe.crawl.fetcher import fetch

        seeds_sorted = sorted(
            seeds, key=lambda s: _domain_yield_score(self.map, s), reverse=True
        )
        seed_results: List[Dict[str, Any]] = []
        for s in seeds_sorted:
            try:
                r = fetch(s, timeout=fetch_timeout, max_retries=1, backoff_factor=0.0)
            except Exception as e:
                seed_results.append({"seed": s, "status_code": None, "error": str(e)})
                continue

            entry = {
                "seed": s,
                "status_code": r.get("status_code"),
                "error": r.get("error"),
            }

            if getattr(self, "ingest_on_fetch", False):
                try:
                    from probe.crawl.ingest import ingest_fetch_result

                    ing = ingest_fetch_result(self.map, r)
                    entry["ingested"] = ing
                    self._maybe_apply_ingest_feedback(s, ing)
                except Exception as ing_exc:
                    # record ingest error but continue
                    entry["ingest_error"] = str(ing_exc)

            seed_results.append(entry)

        return seed_results

    def investigate(
        self,
        entity_name: str,
        desired_doc_types: List[str],
        *,
        max_seeds: int = 10,
        dry_run: bool = True,
        fetch_timeout: float = 5.0,
    ) -> Dict[str, Any]:
        gap_detector_cls = _load_gap_detector_cls()

        detector = gap_detector_cls(self.map)
        gap = detector.analyze_entity_gaps(entity_name, desired_doc_types)

        sg = SeedGenerator(self.map)
        seeds: List[str] = []
        # For each missing type, generate seeds using suggested domains from the gap detector
        for t in gap.get("missing_types", []):
            domains = gap.get("suggested_domains", [])
            seeds.extend(sg.generate_seeds(domains, [t], per_domain=max_seeds))

        # enforce overall max
        seeds = seeds[:max_seeds]

        result: Dict[str, Any] = {"entity": entity_name, "gap": gap, "seeds": seeds}

        if not dry_run:
            result["results"] = self._fetch_seeds(seeds, fetch_timeout)

        return result
