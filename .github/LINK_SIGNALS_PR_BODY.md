Add v0.5 Link Signals (context-aware link signals) feature.

This includes:

- docs/LINK_SIGNALS.md (design-locked v0.5 contract)
- probe/crawl/link_signals.py (small deterministic implementation for context extraction, tokenization, scoring, and a sqlite-backed store)
- tests/test_link_signals.py (unit tests for extraction/scoring/store)
- sql/migrations/0001_create_link_context.sql (SQL migration for the link_context table)

Design goals: v0.5 is signal-only: no entities, no edges, no AI upstream. This PR introduces the contract and a conservative implementation for early integration and testing. Follow-ups: wire into crawl scorer and add telemetry / policy tags.
