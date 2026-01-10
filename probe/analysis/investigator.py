from typing import List, Dict, Any
from probe.core.map import Map
from probe.analysis.gaps import GapDetector
from probe.analysis.seed_generator import SeedGenerator


class Investigator:
    """Orchestrates a short investigation loop.

    It is intentionally minimal for v0.4: detect gaps, generate seeds, and
    optionally perform a limited fetch pass for the generated seeds.
    """

    def __init__(self, map_obj: Map):
        self.map = map_obj

    def investigate(self, entity_name: str, desired_doc_types: List[str], *, max_seeds: int = 10, dry_run: bool = True, fetch_timeout: float = 5.0) -> Dict[str, Any]:
        detector = GapDetector(self.map)
        gap = detector.analyze_entity_gaps(entity_name, desired_doc_types)

        sg = SeedGenerator(self.map)
        seeds: List[str] = []
        for t in gap.get("missing_types", []):
            seeds.extend(sg.generate_seeds(entity_name, t, max_seeds=max_seeds))

        # enforce overall max
        seeds = seeds[:max_seeds]

        result: Dict[str, Any] = {
            "entity": entity_name,
            "gap": gap,
            "seeds": seeds,
        }

        if not dry_run:
            # perform limited fetch on seeds (best-effort). Import here to keep dependency local.
            from probe.crawl.fetcher import fetch

            seed_results = []
            for s in seeds:
                try:
                    r = fetch(s, timeout=fetch_timeout, max_retries=1, backoff_factor=0.0)
                except Exception as e:
                    seed_results.append({"seed": s, "status_code": None, "error": str(e)})
                    continue
                seed_results.append({"seed": s, "status_code": r.get("status_code"), "error": r.get("error")})

            result["results"] = seed_results

        return result
