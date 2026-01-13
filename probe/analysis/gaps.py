"""Gap detection utilities (GapDetector).

This module must be non-empty so packaging and CI checks include it.
"""

from typing import List, Dict, Any
import types
from probe.core.map import Map


class GapDetector:
    """Detect gaps in entity knowledge coverage.

    Parameters:
    - map_obj: Map instance
    - weights: optional dict to tune heuristic scoring. Supported keys:
      - count: weight for domain frequency across missing types (default 2.0)
      - yield: weight for domain yield_score (default 1.0)
      - trust: weight for domain trust_score (default 0.5)
      - recent: weight for recency boost (default 0.5)
    """

    def __init__(self, map_obj: Map, *, weights: Dict[str, float] | None = None, normalize: str = "none"):
        """Create a GapDetector.

        normalize: how to normalize per-domain document counts. Options:
          - 'none' (default): use raw counts
          - 'per_page': divide counts by domain.pages_crawled (use max(1, pages_crawled) to avoid div-by-zero)
          - 'log': use log1p(count)
          - 'per_page_log': apply per-page then log1p
        """
        self.map = map_obj
        # default weights
        defaults = {"count": 2.0, "yield": 1.0, "trust": 0.5, "recent": 0.5}
        w = defaults if weights is None else {**defaults, **weights}
        self.w_count = float(w.get("count", defaults["count"]))
        self.w_yield = float(w.get("yield", defaults["yield"]))
        self.w_trust = float(w.get("trust", defaults["trust"]))
        self.w_recent = float(w.get("recent", defaults["recent"]))
        # normalization mode for counts
        if normalize not in ("none", "per_page", "log", "per_page_log"):
            raise ValueError(f"invalid normalize option: {normalize!r}")
        self.normalize = normalize

    def analyze_entity_gaps(self, entity_name: str, desired_doc_types: List[str], include_scores: bool = False) -> Dict[str, Any]:
        """
        Analyze what's missing for an entity.

        Returns a dictionary containing existence, missing types, confidence and suggested domains.

        If `include_scores` is True, also returns `domain_scores` detailing component scores for each candidate domain.
        """
        entity = self.map.get_entity(entity_name)
        if not entity:
            return {
                "entity": entity_name,
                "exists": False,
                "confidence": 0.0,
                "missing_types": desired_doc_types,
                "has_documents": 0,
                "weak_confidence": True,
                "suggested_domains": [],
            }

        # Use a lightweight query to fetch only document types for efficiency if available.
        # If the lighter-weight method exists but raises, fall back to the full-document query.
        if hasattr(self.map, 'get_entity_document_types'):
            try:
                existing_types = set(self.map.get_entity_document_types(entity_name))
            except Exception:
                existing_docs = self.map.get_entity_documents(entity_name)
                existing_types = {d.doc_type for d in existing_docs}
        else:
            # fallback to loading full documents (older Map versions)
            existing_docs = self.map.get_entity_documents(entity_name)
            existing_types = {d.doc_type for d in existing_docs}

        missing = [t for t in desired_doc_types if t not in existing_types]

        # Heuristic: if specific types are missing, prefer domains that contain those types
        # Extended scoring: weight by count matches, domain yield_score, trust_score, and recency
        candidates = {}
        if missing:
            if hasattr(self.map, 'get_domains_with_doc_type'):
                for t in missing:
                    try:
                        # Count the number of documents per domain for this doc_type so 'count' reflects
                        # document frequency (not just presence of the type on a domain).
                        # Include pages_crawled in the query so normalizations (per_page) can use it
                        cur = self.map.conn.execute(
                            """
                            SELECT d.domain AS domain, COUNT(*) AS cnt, COALESCE(dom.pages_crawled, 0) AS pages
                            FROM documents d
                            LEFT JOIN domains dom ON dom.domain_name = d.domain
                            WHERE d.doc_type = ?
                            GROUP BY d.domain
                            """,
                            (t,)
                        )
                        for row in cur.fetchall():
                            domain_name = row["domain"]
                            cnt = int(row["cnt"])
                            pages = int(row["pages"] or 0)
                            candidates.setdefault(domain_name, {"count": 0, "pages": pages})
                            # accumulate both document counts and ensure pages is recorded (max existing)
                            candidates[domain_name]["count"] += cnt
                            candidates[domain_name]["pages"] = max(candidates[domain_name].get("pages", 0), pages)
                    except Exception:
                        # If DB access fails for some reason, fall back to presence-based counting
                        try:
                            for d in self.map.get_domains_with_doc_type(t, limit=8):
                                candidates.setdefault(d.domain_name, {"count": 0})
                                candidates[d.domain_name]["count"] += 1
                        except Exception:
                            continue

            else:
                # Some Map mocks may not accept min_pages kwarg; fall back if needed
                try:
                    domains = self.map.get_high_yield_domains(limit=20, min_pages=1)
                except TypeError:
                    domains = self.map.get_high_yield_domains(limit=20)
                for d in domains:
                    candidates.setdefault(d.domain_name, {'count': 0, 'pages': getattr(d, 'pages_crawled', 0)})
            # If candidates are still empty (e.g., domain helper exists but returned no results),
            # fall back to high-yield domains as a graceful default so we always have suggestions.
            if not candidates:
                try:
                    domains = self.map.get_high_yield_domains(limit=20, min_pages=1)
                except TypeError:
                    domains = self.map.get_high_yield_domains(limit=20)
                for d in domains:
                    candidates.setdefault(d.domain_name, {'count': 0})

        # Scoring weights (tunable) - use instance configuration
        w_count = self.w_count
        w_yield = self.w_yield
        w_trust = self.w_trust
        w_recent = self.w_recent

        now = types.SimpleNamespace()
        from datetime import datetime, timezone
        now.dt = datetime.now(timezone.utc)

        # Compute scores for candidate domains
        scored, domain_scores = self._compute_domain_scores(candidates, now, include_scores)
        # Create suggested domain objects from sorted scored list
        suggested_domains_objs = [types.SimpleNamespace(domain_name=name) for name, _ in scored[:5]]

        # support older Map versions without get_entity_document_count or get_entity_documents
        if hasattr(self.map, 'get_entity_document_count'):
            doc_count = self.map.get_entity_document_count(entity_name)
        elif hasattr(self.map, 'get_entity_documents'):
            doc_count = len(self.map.get_entity_documents(entity_name))
        else:
            doc_count = 0

        result = {
            "entity": entity_name,
            "exists": True,
            "confidence": getattr(entity, "confidence_score", 0.0),
            "missing_types": missing,
            "has_documents": doc_count,
            "weak_confidence": getattr(entity, "confidence_score", 0.0) < 0.7,
            "suggested_domains": [d.domain_name for d in suggested_domains_objs],
        }

        if include_scores:
            result["domain_scores"] = domain_scores

        return result

    def _compute_domain_scores(self, candidates: dict, now: types.SimpleNamespace, include_scores: bool):
        """Compute composite scores and return a sorted scored list and domain_scores list."""
        w_count = self.w_count
        w_yield = self.w_yield
        w_trust = self.w_trust
        w_recent = self.w_recent

        scored = []
        domain_scores = []
        from datetime import datetime
        import math

        for domain_name, meta in candidates.items():
            count = meta.get('count', 0)
            pages = meta.get('pages', 0)

            # Apply normalization to counts as configured
            base = float(count)
            if self.normalize in ('per_page', 'per_page_log'):
                base = float(count) / max(1.0, float(pages or 0))
            if self.normalize in ('log', 'per_page_log'):
                base = math.log1p(base)

            yield_score = 0.0
            trust_score = 0.5
            recent_score = 0.0

            if hasattr(self.map, 'get_domain'):
                try:
                    d_obj = self.map.get_domain(domain_name)
                    if d_obj:
                        yield_score = getattr(d_obj, 'yield_score', 0.0)
                        trust_score = getattr(d_obj, 'trust_score', 0.5)
                        last = getattr(d_obj, 'last_crawled_at', None)
                        if last:
                            try:
                                last_dt = datetime.fromisoformat(last)
                                # Ensure timezone-aware comparison: assume UTC if naive
                                from datetime import timezone
                                if last_dt.tzinfo is None:
                                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                                days = (now.dt - last_dt).days
                                recent_score = max(0.0, (30.0 - float(days)) / 30.0)
                            except Exception:
                                recent_score = 0.0
                except Exception:
                    pass

            # Use normalized base value for count contribution
            score = w_count * float(base) + w_yield * float(yield_score) + w_trust * float(trust_score) + w_recent * float(recent_score)
            scored.append((domain_name, score))
            domain_scores.append({
                "domain": domain_name,
                "count": int(count),
                "pages": int(pages),
                "normalized_count": float(base),
                "yield_score": float(yield_score),
                "trust_score": float(trust_score),
                "recent_score": float(recent_score),
                "composite_score": float(score),
            })

        scored.sort(key=lambda kv: kv[1], reverse=True)
        if include_scores:
            domain_scores.sort(key=lambda d: d["composite_score"], reverse=True)
        else:
            domain_scores = None
        return scored, domain_scores
