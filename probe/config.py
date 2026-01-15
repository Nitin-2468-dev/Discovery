"""Configuration loader for Probe.

Supports JSON (`probe.config.json`) or YAML (`probe.config.yaml`) files in the current working directory
or an explicitly provided path. If PyYAML is not installed, only JSON is supported.

Behavior:
- Loads file if present and returns a dict with values.
- Provides sensible defaults when keys are missing.
"""

import json
from pathlib import Path
from typing import Any, Dict

DEFAULTS: Dict[str, Any] = {
    "concurrency": 1,
    "per_domain_delay": 0.25,
    "min_delay": 0.0,
    "blocked_domains": "blocked_domains.txt",
    "tqdm": True,
    # Admin opt-in flag for relaxed modes (e.g., EDUCATIONAL_OPEN). Default: False
    "admin_enabled": False,
    "scorer_weights": {
        "keyword_density": 1.0,
        "boilerplate": 1.0,
        "link_density": 1.0,
        "entity_regex": 1.0,
    },
}


def _load_yaml(path: Path) -> Dict[str, Any]:
    try:
        import yaml
    except Exception:
        raise RuntimeError("PyYAML not available to load YAML config")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f) or {}


def load_config(path: str | None = None) -> Dict[str, Any]:
    """Load configuration from a file (YAML or JSON) or return defaults if no file.

    Args:
        path: optional explicit path to config file. If omitted, tries `probe.config.yaml` then `probe.config.json`.

    Returns:
        dict with configuration merged with DEFAULTS (only keys present in file override defaults).
    """
    cfg: Dict[str, Any] = {}
    try:
        if path:
            p = Path(path)
            if not p.exists():
                return dict(DEFAULTS)
            if p.suffix in (".yml", ".yaml"):
                cfg = _load_yaml(p)
            else:
                cfg = _load_json(p)
        else:
            # try yaml then json
            y = Path("probe.config.yaml")
            j = Path("probe.config.json")
            if y.exists():
                cfg = _load_yaml(y)
            elif j.exists():
                cfg = _load_json(j)
            else:
                cfg = {}
    except Exception:
        # if parsing or loader fails, fall back to defaults
        cfg = {}

    # Merge defaults shallowly
    out = dict(DEFAULTS)
    for k, v in (cfg or {}).items():
        if k == "scorer_weights" and isinstance(v, dict):
            # merge sub-keys
            sw = dict(out.get("scorer_weights", {}))
            sw.update(v)
            out["scorer_weights"] = sw
        else:
            out[k] = v

    return out
