import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

TELEMETRY_FILE = Path("policy_denials.jsonl")


def record_denial(decision: Dict[str, Any]) -> None:
    """Append a policy denial decision to the telemetry JSONL file.

    The record includes an ISO timestamp and a sanitized copy of the decision.
    """
    try:
        rec = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "mode": decision.get("mode"),
            "reason": decision.get("reason"),
            "tags": decision.get("tags", []),
            "context": decision.get("context", {}),
        }
        with open(TELEMETRY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, separators=(",", ":")) + "\n")
    except Exception:
        # Telemetry should not raise in production paths
        pass
