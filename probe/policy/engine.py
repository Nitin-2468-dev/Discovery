from enum import Enum
from typing import Any, Dict, Optional


class Mode(str, Enum):
    PUBLIC_GUARDED = "public_guarded"
    EDUCATIONAL_OPEN = "educational_open"


# Backwards- and docs-friendly alias: allow `Mode.educational_open` (lowercase) in code/docs/tests
# This does not create a new enum member; it points the attribute to the existing member.
Mode.educational_open = Mode.EDUCATIONAL_OPEN


class PolicyEngine:
    """Minimal PolicyEngine stub.

    Responsibilities (stubbed):
    - interpret active mode
    - evaluate query intent
    - allow, limit, or annotate actions

    Methods are intentionally minimal; follow-up PRs will implement enforcement
    and tests.
    """

    def __init__(self, mode: Mode = Mode.PUBLIC_GUARDED):
        self.mode = mode

    def evaluate_query(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Return a small decision payload describing allowed activity.

        Currently a conservative default: returns `allowed: False` for high-risk
        categories only in implementation PRs. This stub returns a permissive
        placeholder that downstream code may annotate.
        """
        return {
            "mode": self.mode.value,
            "allowed": True,
            "reason": "stub - no enforcement implemented",
            "tags": [],
        }

    def domain_allowed(self, domain: str) -> bool:
        """Domain allowlist check (placeholder).

        Real implementation will consult configured denylists/allowlists and
        per-mode rules.
        """
        return True
