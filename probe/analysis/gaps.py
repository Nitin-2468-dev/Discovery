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
        suggested_domains_objs = []
        if missing:
            # If Map supports domain lookups by doc_type, use it
            if hasattr(self.map, 'get_domains_with_doc_type'):
                seen = {}
                for t in missing:
                    try:
                        for d in self.map.get_domains_with_doc_type(t, limit=5):
                            # score domains by frequency across missing types
                            seen.setdefault(d.domain_name, 0)
                            seen[d.domain_name] += 1
                    except Exception:
                        continue
                # Sort by score (descending) then yield_score if available
                dd = sorted(seen.items(), key=lambda kv: kv[1], reverse=True)
                suggested_domains_objs = [types.SimpleNamespace(domain_name=k) for k, _ in dd[:5]]
            else:
                # Fallback: choose high-yield domains
                suggested_domains_objs = self.map.get_high_yield_domains(limit=5)
        else:
            suggested_domains_objs = self.map.get_high_yield_domains(limit=5)

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
