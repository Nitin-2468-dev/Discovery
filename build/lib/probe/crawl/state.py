"""Persistent state helpers for crawl-run persistence.

Stores `domain -> last_crawled_iso` in a small JSON file (`.probe_state.json`).
Provides get_last_crawled(domain) and set_last_crawled(domain, datetime).
"""
from pathlib import Path
from datetime import datetime
import json
from typing import Optional

STATE_FILE = Path('.probe_state.json')


def _load():
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _save(d):
    STATE_FILE.write_text(json.dumps(d), encoding='utf-8')


def get_last_crawled(domain: str) -> Optional[datetime]:
    d = _load()
    v = d.get(domain)
    if not v:
        return None
    try:
        return datetime.fromisoformat(v)
    except Exception:
        return None


def set_last_crawled(domain: str, when: datetime):
    d = _load()
    d[domain] = when.isoformat()
    _save(d)


def clear_state():
    if STATE_FILE.exists():
        STATE_FILE.unlink()
