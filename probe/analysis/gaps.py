"""Gap detection utilities (GapDetector).

This module must be non-empty so packaging and CI checks include it.
"""

from typing import List, Dict, Any
import types
from probe.core.map import Map


class GapDetector:
    """Detect gaps in entity knowledge coverage."""

    def __init__(self, map_obj: Map):
        self.map = map_obj

    def analyze_entity_gaps(self, entity_name: str, desired_doc_types: List[str]) -> Dict[str, Any]:
        """
        Analyze what's missing for an entity.

        Returns a dictionary containing existence, missing types, confidence and suggested domains.
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

        # Use a lightweight query to fetch only document types for efficiency if available
        if hasattr(self.map, 'get_entity_document_types'):
            existing_types = set(self.map.get_entity_document_types(entity_name))
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
                        for d in self.map.get_domains_with_doc_type(t, limit=8):
                            candidates.setdefault(d.domain_name, {'count': 0})
                            candidates[d.domain_name]['count'] += 1
                    except Exception:
                        continue
            else:
                for d in self.map.get_high_yield_domains(limit=20):
                    candidates.setdefault(d.domain_name, {'count': 0})
        else:
            for d in self.map.get_high_yield_domains(limit=20):
                candidates.setdefault(d.domain_name, {'count': 0})

        # Scoring weights (tunable)
        w_count = 2.0
        w_yield = 1.0
        w_trust = 0.5
        w_recent = 0.5

        now = types.SimpleNamespace()
        from datetime import datetime
        now.dt = datetime.utcnow()

        scored = []
        for domain_name, meta in candidates.items():
            count = meta.get('count', 0)
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
                                days = (now.dt - last_dt).days
                                recent_score = max(0.0, (30.0 - float(days)) / 30.0)
                            except Exception:
                                recent_score = 0.0
                except Exception:
                    pass

            score = w_count * float(count) + w_yield * float(yield_score) + w_trust * float(trust_score) + w_recent * float(recent_score)
            scored.append((domain_name, score))

        scored.sort(key=lambda kv: kv[1], reverse=True)
        suggested_domains_objs = [types.SimpleNamespace(domain_name=name) for name, _ in scored[:5]]

        # support older Map versions without get_entity_document_count
        if hasattr(self.map, 'get_entity_document_count'):
            doc_count = self.map.get_entity_document_count(entity_name)
        else:
            doc_count = len(self.map.get_entity_documents(entity_name))

        return {
            "entity": entity_name,
            "exists": True,
            "confidence": getattr(entity, "confidence_score", 0.0),
            "missing_types": missing,
            "has_documents": doc_count,
            "weak_confidence": getattr(entity, "confidence_score", 0.0) < 0.7,
            "suggested_domains": [d.domain_name for d in suggested_domains_objs],
        }
