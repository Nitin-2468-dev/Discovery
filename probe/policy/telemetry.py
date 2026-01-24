import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

TELEMETRY_FILE = Path("policy_denials.jsonl")

logger = logging.getLogger("probe.policy.telemetry")


def init_logger(
    path: Optional[Path] = None, max_bytes: int = 10_000_000, backup_count: int = 5
) -> None:
    """Initialize a rotating file handler for policy telemetry.

    If `path` is provided, use that path; otherwise use `TELEMETRY_FILE`.
    The handler writes raw JSON lines (message-only) so downstream systems can
    ingest the file directly.
    """
    p = Path(path) if path else TELEMETRY_FILE
    try:
        from logging.handlers import RotatingFileHandler

        # ensure parent exists
        if p.parent and not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)

        handler = RotatingFileHandler(
            str(p), maxBytes=max_bytes, backupCount=backup_count
        )
        # message will be the JSON line
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    except Exception:
        # Do not fail if logging cannot be configured
        logger.debug("Failed to initialize telemetry logger", exc_info=True)


def record_denial(decision: Dict[str, Any]) -> None:
    """Append a policy denial decision to the telemetry JSONL file.

    The record includes an ISO timestamp and a sanitized copy of the decision.
    """
    try:
        from datetime import timezone

        rec = {
            # Use timezone-aware UTC and normalize to a trailing Z like before
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "mode": decision.get("mode"),
            "reason": decision.get("reason"),
            "tags": decision.get("tags", []),
            "context": decision.get("context", {}),
        }
        msg = json.dumps(rec, separators=(",", ":"))
        # If a rotating logger is configured, emit via logger so rotation applies
        if logger.handlers:
            logger.info(msg)
            return

        # Fallback: append directly to file
        with open(TELEMETRY_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        # Telemetry should not raise in production paths
        logger.debug("Failed to record telemetry", exc_info=True)


def upload_to_s3(
    bucket: str, key: Optional[str] = None, aws_profile: Optional[str] = None
) -> bool:
    """Upload the current telemetry file to S3.

    Returns True on success, False otherwise. Requires `boto3` to be available.
    """
    p = TELEMETRY_FILE
    if not p.exists():
        logger.debug("Telemetry file %s does not exist", p)
        return False

    try:
        import importlib

        boto3 = importlib.import_module("boto3")
        session = (
            boto3.Session(profile_name=aws_profile) if aws_profile else boto3.Session()
        )
        s3 = session.client("s3")
        upload_key = key if key else p.name
        s3.upload_file(str(p), bucket, upload_key)
        logger.info("Uploaded telemetry to s3://%s/%s", bucket, upload_key)
        return True
    except Exception:
        logger.exception("Failed to upload telemetry to S3")
        return False
