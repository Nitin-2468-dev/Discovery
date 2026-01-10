from typing import List, Dict, Any
from probe.core.map import Map
from probe.analysis.gaps import GapDetector
from probe.analysis.seed_generator import SeedGenerator


class Investigator:
    """Orchestrates a short investigation loop.

    It is intentionally minimal for v0.4: detect gaps, generate seeds, and
    optionally perform a limited fetch pass for the generated seeds.
    """

    def __init__(self, map_obj: Map, *, ingest_on_fetch: bool = False):
        self.map = map_obj
        # When True, fetched seed pages will be ingested into the provided Map
        self.ingest_on_fetch = bool(ingest_on_fetch)

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

            # Prioritize seeds by domain yield score (higher first)
            def domain_yield(seed_url: str) -> float:
                try:
                    from urllib.parse import urlparse
                    d = urlparse(seed_url).netloc
                    dom = self.map.get_domain(d)
                    return dom.yield_score if dom else 0.0
                except Exception:
                    return 0.0

            seeds_sorted = sorted(seeds, key=lambda s: domain_yield(s), reverse=True)

            seed_results = []
            for s in seeds_sorted:
                try:
                    r = fetch(s, timeout=fetch_timeout, max_retries=1, backoff_factor=0.0)
                except Exception as e:
                    seed_results.append({"seed": s, "status_code": None, "error": str(e)})
                    continue

                entry = {"seed": s, "status_code": r.get("status_code"), "error": r.get("error")}

                # Optional ingest: if Investigator constructed with a Map instance, ingest results
                try:
                    if getattr(self, 'ingest_on_fetch', False):
                        from probe.crawl.ingest import ingest_fetch_result
                        ing = ingest_fetch_result(self.map, r)
                        entry['ingested'] = ing

                        # Feedback loop: if a document was discovered during ingestion, increment domain documents
                        try:
                            domain = __import__('urllib.parse', fromlist=['urlparse']).urlparse(s).netloc
                            found_doc = bool(ing.get('document_id')) or (ing.get('edges_created', 0) > 0)
                            # also check outgoing links for pdfs
                            for out in ing.get('outgoing_links', []):
                                if out.lower().endswith('.pdf'):
                                    found_doc = True
                                    break
                            if found_doc:
                                self.map.increment_domain_documents(domain, delta=1)
                        except Exception:
                            pass
                except Exception as ing_exc:
                    entry['ingest_error'] = str(ing_exc)

                seed_results.append(entry)

            result["results"] = seed_results

        return result
