-- Migration: create link_context table (v0.5 signal-only table)
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
