from typing import List, Optional
from urllib.parse import quote_plus
try:
    import httpx
except Exception:
    httpx = None
import xml.etree.ElementTree as ET
from probe.core.map import Map


class SeedGenerator:
    """Generate smart seeds based on gaps and high-yield sources.

    Heuristics include sitemap discovery and robots.txt parsing (best-effort). These network
    operations are optional and controlled with `fetch_remote` to avoid unexpected network I/O
    during unit tests; tests should mock `httpx.get` when exercising remote discovery.
    """

    def __init__(self, map_obj: Map, *, fetch_remote: bool = False, http_timeout: float = 3.0):
        self.map = map_obj
        self.fetch_remote = bool(fetch_remote)
        self.http_timeout = float(http_timeout)

    def _fetch_text(self, url: str) -> Optional[str]:
        if httpx is None:
            return None
        try:
            r = httpx.get(url, timeout=self.http_timeout)
            r.raise_for_status()
            return r.text
        except Exception:
            return None

    def discover_sitemap(self, domain: str) -> List[str]:
        """Attempt to discover sitemap URLs and return a list of sitemap-located URLs.

        This is a lightweight parser that looks for <loc> tags.
        """
        if not self.fetch_remote:
            return []
        url = f"https://{domain.rstrip('/')}/sitemap.xml"
        text = self._fetch_text(url)
        if not text:
            return []
        try:
            root = ET.fromstring(text)
            urls = [elem.text.strip() for elem in root.findall('.//{*}loc') if elem.text]
            return urls
        except Exception:
            return []

    def discover_robots_disallows(self, domain: str) -> List[str]:
        """Return a list of disallowed path prefixes from robots.txt (basic parse)."""
        if not self.fetch_remote:
            return []
        url = f"https://{domain.rstrip('/')}/robots.txt"
        txt = self._fetch_text(url)
        if not txt:
            return []
        disallows = []
        for line in txt.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.lower().startswith('disallow:'):
                path = line.split(':', 1)[1].strip()
                if path:
                    disallows.append(path)
        return disallows

    def generate_seeds_for_domain(self, domain: str, doc_type: str, limit: int = 5, fetch_remote: Optional[bool] = None) -> List[str]:
        """Generate up to `limit` seed URLs for a domain and desired doc_type.

        If fetch_remote is True, attempt to consult sitemap/robots for additional URLs and to avoid disallowed paths.
        """
        out = []
        base = f"https://{domain.rstrip('/')}"
        # always add root
        out.append(base + "/")

        # common heuristic paths
        common_paths = ["/datasheets", "/downloads", "/search?q={q}", "/{q}", "/{q}s", "/products", "/resources"]

        for path in common_paths:
            if len(out) >= limit:
                break
            p = path.format(q=doc_type)
            url = base + p
            if url not in out:
                out.append(url)

        # remote discovery
        fr = self.fetch_remote if fetch_remote is None else bool(fetch_remote)
        if fr:
            s_urls = self.discover_sitemap(domain)
            for u in s_urls:
                if len(out) >= limit:
                    break
                if u not in out:
                    out.append(u)
            disallowed = self.discover_robots_disallows(domain)
            # filter out any entries that match disallowed prefixes
            if disallowed:
                out = [u for u in out if not any(u.startswith(base + p) for p in disallowed)]

        return out[:limit]

    def generate_seeds(self, domains_or_entity, doc_types_or_type, per_domain: int = 3, fetch_remote: Optional[bool] = None, max_seeds: Optional[int] = None) -> List[str]:
        """Generate seed URLs.

        Backwards-compatible behavior:
        - If called as generate_seeds(domains: List[str], doc_types: List[str], ...), it generates
          per-domain seeds for each domain/doc_type pair.
        - If called as generate_seeds(entity_name: str, doc_type: str, max_seeds=int), it uses
          high-yield domains and related entities to produce up to `max_seeds` seeds (legacy API).
        """
        # Legacy call signature: (entity_name: str, doc_type: str, max_seeds=int)
        if isinstance(domains_or_entity, str) and isinstance(doc_types_or_type, str):
            return self._generate_seeds_for_entity(domains_or_entity, doc_types_or_type, per_domain, fetch_remote, max_seeds)

        # New-style call: domains list + doc_types list
        domains = domains_or_entity
        doc_types = doc_types_or_type
        seeds = []
        seen = set()
        for domain in domains:
            for dt in doc_types:
                for url in self.generate_seeds_for_domain(domain, dt, limit=per_domain, fetch_remote=fetch_remote):
                    if url not in seen:
                        seeds.append(url)
                        seen.add(url)
        return seeds


    def _generate_seeds_for_entity(self, entity_name: str, doc_type: str, per_domain: int, fetch_remote: Optional[bool], max_seeds: Optional[int]) -> List[str]:
        """Legacy helper: generate seeds for an entity name and a single doc_type."""
        max_s = int(max_seeds) if max_seeds else int(per_domain)

        # prefer high-yield domains
        try:
            domains = [d.domain_name for d in self.map.get_high_yield_domains(limit=max_s)]
        except Exception:
            domains = []

        seeds = []
        # distribute per-domain budget across domains to prefer breadth
        per_domain_budget = max(1, int(max_s // max(1, len(domains)))) if domains else max_s
        seeds.extend(self.generate_seeds(domains, [doc_type], per_domain=per_domain_budget, fetch_remote=fetch_remote))

        # add google search for the entity and related entities
        gq = quote_plus(f"{entity_name} {doc_type}")
        seeds.append(f"https://www.google.com/search?q={gq}")
        try:
            rels = self.map.get_related_entities(entity_name)
            for r in rels:
                rq = quote_plus(f"{r.name} {doc_type}")
                seeds.append(f"https://www.google.com/search?q={rq}")
        except Exception:
            pass

        return self._dedupe_and_limit(seeds, max_s)

    def _dedupe_and_limit(self, seeds: List[str], max_s: int) -> List[str]:
        """Deduplicate preserving order and enforce a maximum length."""
        out: List[str] = []
        seen = set()
        for s in seeds:
            if s not in seen:
                out.append(s)
                seen.add(s)
            if len(out) >= max_s:
                break
        return out
