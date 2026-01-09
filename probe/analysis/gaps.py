from typing import List, Dict, Any
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
                "missing_types": desired_doc_types,
                "suggested_domains": [],
            }

        # Use a lightweight query to fetch only document types for efficiency
        existing_types = set(self.map.get_entity_document_types(entity_name))

        missing = [t for t in desired_doc_types if t not in existing_types]

        suggested_domains = self.map.get_high_yield_domains(limit=5)

        return {
            "entity": entity_name,
            "exists": True,
            "confidence": getattr(entity, "confidence_score", 0.0),
            "missing_types": missing,
            "has_documents": self.map.get_entity_document_count(entity_name),
            "weak_confidence": getattr(entity, "confidence_score", 0.0) < 0.7,
            "suggested_domains": [d.domain_name for d in suggested_domains],
        }
