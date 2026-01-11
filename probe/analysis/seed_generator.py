from typing import List
from urllib.parse import quote_plus
from probe.core.map import Map


class SeedGenerator:
    """Generate smart seeds based on gaps and high-yield sources."""

    def __init__(self, map_obj: Map):
        self.map = map_obj

    def generate_seeds(self, entity_name: str, doc_type: str, max_seeds: int = 10) -> List[str]:
        """
        Generate seed URLs for finding specific document types.

        Strategy:
        1. Use high-yield domains
        2. Use related-entity neighborhoods (if any)
        3. Construct search URLs with sensible query patterns
        4. Add Google search fallback using filetype:pdf
        """
        seeds: List[str] = []

        # Get high-yield domains
        domains = self.map.get_high_yield_domains(limit=5)

        q = quote_plus(f"{entity_name} {doc_type}")
        for d in domains:
            # Construct a few plausible query endpoints on the domain
            seeds.append(f"https://{d.domain_name}/search?q={q}")
            seeds.append(f"https://{d.domain_name}/?s={q}")

        # Use related entities to diversify queries
        related = self.map.get_related_entities(entity_name)
        for r in related:
            seeds.append(f"https://www.google.com/search?q={quote_plus(r.name + ' ' + doc_type)}")

        # Add Google PDF filetype fallback
        seeds.append(f"https://www.google.com/search?q={q}+filetype:pdf")

        # Deduplicate while preserving order
        seen = set()
        unique_seeds = []
        for s in seeds:
            if s not in seen:
                unique_seeds.append(s)
                seen.add(s)
            if len(unique_seeds) >= max_seeds:
                break

        return unique_seeds
