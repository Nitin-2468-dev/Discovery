"""Link Signals (v0.5) - lightweight deterministic context extraction and scoring.

This module provides a small, dependency-free implementation suitable for v0.5:
- context extraction (text lines / heading / parent-siblings)
- token extraction (simple deterministic tokenizer)
- scoring via configurable heuristics
- small sqlite-backed LinkContextStore for v0.5 testing

Design notes: v0.5 is signal-only. This code deliberately avoids ML/embeddings and
is deterministic for reproducible tests.
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

TOKEN_RE = re.compile(r"[a-z0-9\-]+")


@dataclass
class LinkContext:
    from_page: str
    to_url: str
    context_text: str
    matched_tokens: List[str]
    section_heading: Optional[str]
    relevance_score: float


def extract_context_text(
    lines: Sequence[str], anchor_index: int, mode: str = "lines", radius: int = 5
) -> Tuple[str, Optional[str]]:
    """Extract local text context around an anchor presented as a list of text lines.

    Modes:
    - "lines" (default): ±radius lines around anchor_index
    - "heading": take nearest heading line above (if present) + its following lines

    Returns (context_text, section_heading)
    """
    n = len(lines)
    if mode == "heading":
        # scan backwards for a markdown-style heading line (starts with '# ')
        for i in range(anchor_index, -1, -1):
            if re.match(r"^#{1,4}\s+", lines[i]):
                start = i
                # include up to `radius` lines after the heading (inclusive)
                end = min(n, i + radius + 1)
                chunk = "\n".join(lines[start:end])
                heading = lines[i].strip()
                return chunk, heading
        # fallback to lines
    # default: lines mode
    start = max(0, anchor_index - radius)
    end = min(n, anchor_index + radius + 1)
    chunk = "\n".join(lines[start:end])
    return chunk, None


def extract_tokens(text: str) -> List[str]:
    """Deterministic token extraction: lowercase, find alnum/hyphen tokens, dedupe preserving order."""
    txt = text.lower()
    raw = TOKEN_RE.findall(txt)
    seen = set()
    out = []
    for t in raw:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def score_tokens(tokens: Iterable[str], heuristics: Optional[dict] = None) -> float:
    """Score based on simple heuristics. heuristics is a mapping of token->weight or
    preconfigured keywords. Returns normalized score 0.0-1.0.
    """
    if heuristics is None:
        heuristics = {
            "keyword_weight": 0.3,
            "entity_weight": 0.4,
            "section_weight": 0.2,
            "file_hint_weight": 0.1,
            "keywords": {"driver": 0.3, "manual": 0.2, "download": 0.2},
            "entities": set(),
            "file_hints": {"pdf": 0.1, "zip": 0.1},
        }

    score = 0.0

    # keyword matches
    for k, w in heuristics.get("keywords", {}).items():
        if k in tokens:
            score += w * heuristics["keyword_weight"]

    # entity mention boost
    for e in heuristics.get("entities", set()):
        if e in tokens:
            score += heuristics["entity_weight"]

    # file hints
    for fh, w in heuristics.get("file_hints", {}).items():
        if fh in tokens:
            score += w * heuristics["file_hint_weight"]

    # cap to 1.0
    return max(0.0, min(1.0, score))


class LinkContextStore:
    """Simple SQLite store for LinkContext in v0.5. Used for tests and smoke runs."""

    def __init__(self, path: str = ":memory:"):
        self.path = path
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_table()

    def _ensure_table(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS link_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_page TEXT NOT NULL,
                to_url TEXT NOT NULL,
                context_text TEXT,
                matched_tokens TEXT,
                section_heading TEXT,
                relevance_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        self._conn.commit()

    def insert(self, ctx: LinkContext) -> int:
        cur = self._conn.execute(
            "INSERT INTO link_context(from_page,to_url,context_text,matched_tokens,section_heading,relevance_score) VALUES (?,?,?,?,?,?)",
            (
                ctx.from_page,
                ctx.to_url,
                ctx.context_text,
                json.dumps(ctx.matched_tokens),
                ctx.section_heading,
                float(ctx.relevance_score),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def list_recent(self, limit: int = 100) -> List[LinkContext]:
        cur = self._conn.execute(
            "SELECT * FROM link_context ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = cur.fetchall()
        out = []
        for r in rows:
            out.append(
                LinkContext(
                    from_page=r["from_page"],
                    to_url=r["to_url"],
                    context_text=r["context_text"],
                    matched_tokens=json.loads(r["matched_tokens"] or "[]"),
                    section_heading=r["section_heading"],
                    relevance_score=r["relevance_score"],
                )
            )
        return out


# lightweight helper for typical flow
def analyze_link_from_lines(
    from_page: str, to_url: str, lines: Sequence[str], anchor_idx: int, **kwargs
) -> LinkContext:
    ctx_text, heading = extract_context_text(
        lines,
        anchor_idx,
        mode=kwargs.get("mode", "lines"),
        radius=kwargs.get("radius", 5),
    )
    tokens = extract_tokens(ctx_text)
    score = score_tokens(tokens, heuristics=kwargs.get("heuristics"))
    matched = tokens[:10]
    return LinkContext(
        from_page=from_page,
        to_url=to_url,
        context_text=ctx_text,
        matched_tokens=matched,
        section_heading=heading,
        relevance_score=score,
    )
