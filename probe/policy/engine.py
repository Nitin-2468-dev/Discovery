import logging
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


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

    def __init__(self, mode: Mode = Mode.PUBLIC_GUARDED, admin_enabled: bool = False):
        self.mode = mode
        # Administrative opt-in required for relaxed modes (like EDUCATIONAL_OPEN)
        self.admin_enabled = admin_enabled

    DEFAULT_DENYLIST = {"malicious.example", "do-not-fetch.example"}

    def evaluate_query(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Return a small decision payload describing allowed activity.

        Current minimal enforcement:
        - If `context["domain"]` is provided and `domain_allowed` rejects it,
          return `allowed: False` with a reason and `tags: ["domain"]`.
        - Otherwise, return a permissive decision (placeholder for future rules).
        """
        context = context or {}
        domain = context.get("domain")

        if domain is not None and not self.domain_allowed(domain):
            reason = f"domain '{domain}' disallowed in mode '{self.mode.value}'"
            logger.warning(
                "Policy decision denied: mode=%s domain=%s reason=%s",
                self.mode.value,
                domain,
                reason,
            )
            decision = {
                "mode": self.mode.value,
                "allowed": False,
                "reason": reason,
                "tags": ["domain"],
                "context": {"domain": domain},
            }
            try:
                from .telemetry import record_denial

                record_denial(decision)
            except Exception:
                logger.debug("Failed to record policy telemetry", exc_info=True)

            return decision

        return {
            "mode": self.mode.value,
            "allowed": True,
            "reason": "permissive placeholder",
            "tags": [],
        }

    def domain_allowed(self, domain: str) -> bool:
        """Domain allowlist/denylist check (minimal implementation).

        - In `PUBLIC_GUARDED` mode: deny domains in `DEFAULT_DENYLIST`.
        - In `EDUCATIONAL_OPEN` mode: be permissive (allow all domains).

        This is intentionally small — follow-up PRs will add configuration
        and richer policies.
        """
        domain = domain.lower().strip()

        if self.mode is Mode.EDUCATIONAL_OPEN and not getattr(
            self, "admin_enabled", False
        ):
            logger.warning(
                "Educational mode requested but `admin_enabled` is False; treating as PUBLIC_GUARDED for domain checks"
            )
            # Fall through to denylist behavior (i.e., treat like PUBLIC_GUARDED)

        if self.mode is Mode.EDUCATIONAL_OPEN and getattr(self, "admin_enabled", False):
            return True

        # PUBLIC_GUARDED (and other future modes) deny known bad domains
        return domain not in self.DEFAULT_DENYLIST
