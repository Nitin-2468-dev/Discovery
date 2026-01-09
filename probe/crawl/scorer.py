from typing import Dict, Any, List
import math
import logging

logger = logging.getLogger(__name__)


class Scorer:
    """Base scorer interface."""

    def score(self, page: Dict[str, Any]) -> float:
        raise NotImplementedError


class KeywordDensityScorer(Scorer):
    """Simple keyword density scorer.

    Expects `page['text']` and optional `page['metadata']['keywords']` (list of keywords).
    Returns a score in 0.0-1.0 proportional to normalized keyword density.
    """

    def __init__(self, keywords: List[str] = None, weight: float = 1.0):
        self.keywords = [k.lower() for k in (keywords or [])]
        self.weight = weight

    def score(self, page: Dict[str, Any]) -> float:
        text = (page.get("text") or "").lower()
        if not text or not self.keywords:
            return 0.0
        words = text.split()
        if not words:
            return 0.0
        total = len(words)
        hits = sum(sum(1 for _ in range(1) if kw in w) for w in words for kw in self.keywords)
        density = hits / total
        # Normalize: a density of 0.05 -> 1.0, scale log for diminishing returns
        score = min(1.0, math.log1p(density * 100) / math.log1p(5))
        return float(score * self.weight)


class BoilerplateDetector(Scorer):
    """Penalizes pages with high boilerplate_ratio available in page['boilerplate_ratio'].

    Returns a score in 0.0-1.0 where lower is worse (so this scorer will contribute negatively in composition).
    """

    def __init__(self, weight: float = 1.0):
        self.weight = weight

    def score(self, page: Dict[str, Any]) -> float:
        br = page.get("boilerplate_ratio")
        if br is None:
            return 1.0 * self.weight
        # If boilerplate_ratio is high (>=0.5), heavy penalty
        s = max(0.0, 1.0 - br * 2)
        return float(s * self.weight)


class LinkDensityScorer(Scorer):
    """Scores pages based on the fraction of internal links vs total links.

    Expects `page['links']` as list of dicts with `url` keys and `page['domain']` present.
    Returns a score in 0.0-1.0 where values closer to 1.0 indicate a high proportion of internal links.
    """

    def __init__(self, weight: float = 1.0):
        self.weight = weight

    def _get_domain(self, url: str) -> str:
        from urllib.parse import urlparse
        try:
            return urlparse(url).netloc
        except Exception:
            return ""

    def score(self, page: Dict[str, Any]) -> float:
        links = page.get("links") or []
        if not links:
            return 0.0
        domain = page.get("domain") or ""
        total = len(links)
        internal = 0
        for l in links:
            u = l.get("url")
            if not u:
                continue
            if self._get_domain(u) == domain:
                internal += 1
        ratio = internal / total if total > 0 else 0.0
        # Return ratio scaled by weight
        return float(max(0.0, min(1.0, ratio * self.weight)))

class RelevanceScorer:
    """Composite scorer that combines multiple components with weights.

    Usage:
        scorer = RelevanceScorer(components=[KeywordDensityScorer(['manual']), BoilerplateDetector()])
        total = scorer.score(page)
        comps = scorer.score_components(page)
    """

    def __init__(self, components: List[Scorer] = None):
        self.components = components or []

    def score_components(self, page: Dict[str, Any]) -> Dict[str, float]:
        out = {}
        for c in self.components:
            name = c.__class__.__name__
            try:
                s = c.score(page)
            except Exception:
                logger.exception("Scorer component %s failed", name)
                s = 0.0
            out[name] = float(max(0.0, min(1.0, s)))
        return out

    def score(self, page: Dict[str, Any]) -> float:
        comps = self.score_components(page)
        if not comps:
            return 0.0
        # Simple average for now
        total = sum(comps.values()) / len(comps)
        return float(max(0.0, min(1.0, total)))


# Backwards-compatible placeholder
def score_placeholder():
    return 0.5
