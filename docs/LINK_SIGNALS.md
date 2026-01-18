# Link Signals (v0.5)

**Status:** v0.5 (Design Locked)
**Purpose:** Define the exact, conservative behavior for extracting and using *local context around links* for crawl prioritization and explainability. This is a signal-only feature: it must not create entities, edges, or feed AI upstream of verification.

---

## Overview

When the crawler encounters a link, it extracts local textual context and converts it into deterministic tokens and a simple relevance score. These link-context records are stored in a non-authoritative table `link_context` and used ONLY for crawl prioritization and explanation.

No knowledge is inferred or written into the graph at v0.5.

---

## Exact v0.5 contract (short)

- Extract local context (±5 lines, or parent DOM node + siblings, or nearest heading) — pick one mode per page/config.
- Deterministic token extraction (lowercase tokens, noun phrases, known keywords); no ML or embeddings.
- Simple heuristic scoring (keyword matches, entity token boost, section hint, file hint) — score normalized 0.0–1.0.
- Persist to `link_context` table (ephemeral, replaceable, non-authoritative).
- Use only for crawl queue priority, branch stopping heuristics, and explainability.

---

## SQL (v0.5)

Create table (example):

```sql
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
```

Note: this table is intentionally non-authoritative and may be truncated or dropped as needed.

---

## Privacy & Safety

- Link context is stored only to improve crawling and explainability; it is not treated as evidence.
- All privacy-sensitive harvesting must obey `probe.policy` and local robots/consent rules.

---

## Exit Criteria

- Crawler prioritizes better (links leading to higher-yield pages are explored earlier).
- Fewer irrelevant branches are visited.
- Link-follow decisions are explainable from recorded signals.
- No edges or entities were created from context alone. Any such case is a bug.

---

**Design locked v0.5.** Changes require consensus and a documented migration path.
