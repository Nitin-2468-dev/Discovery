# Changelog

All notable changes to this project are documented in this file.

## [Unreleased] - TBD

### Added (unreleased)

- Gap detection: `probe.analysis.gaps.GapDetector` with `analyze_entity_gaps(entity_name, desired_doc_types)` that returns missing document types, weak confidence indicator, and suggested domains.
- CLI: `probe gaps <entity> --types <types>` with a `--json` flag for machine-readable output. ✅
- Tests: unit tests for `GapDetector` and CLI tests for `probe gaps` (added under `tests/test_gap_detector.py` and `tests/test_cli_gaps.py`).
- Integration: Added an integration test exercising domain stats and suggestion behavior (`tests/test_gap_integration.py`).
- Heuristics & tuning: exposed configurable weights for `GapDetector` and extended domain scoring to weight by missing-type frequency, domain `yield_score`, `trust_score`, and recency; added tests and documentation for weights.

## [v0.4.1] - 2026-01-11

### Added (v0.4.1)

- Research/CI: added and validated an opt-in scheduled/manual real-network integration workflow (`.github/workflows/research-integration.yml`) that safely skips when the test file or token is not present; run with `RUN_REAL_NET_TESTS=true` to exercise the test.
- Added `probe/crawl/fetcher_adapter.py` and `tests/test_crawler_integration.py` (opt-in) to validate real-network crawling behavior.

## [v0.4] - 2026-01-09

### Added (v0.4)

- Gap detection: `probe.analysis.gaps.GapDetector` with `probe gaps` CLI for analyzing missing document types, weak confidence, and suggested sources.
- Seed generator: `probe.analysis.seed_generator.SeedGenerator` with CLI `probe seeds gen` for creating smart seed URLs.
- Investigator skeleton: `probe.analysis.investigator.Investigator` with `probe investigate` CLI for gap→seed investigation (dry-run by default).
- Lightweight Map helpers: `Map.get_entity_document_types()` and `Map.get_entity_document_count()` for efficient gap detection.
- CLI `gaps` supports JSON output (`--json`) for automation.
- Research/CI: added an opt-in scheduled/manual real-network integration workflow (`.github/workflows/research-integration.yml`) that is guarded and skips when the real-network test or token is missing; enable with `RUN_REAL_NET_TESTS=true` to run the test.
- Added a small `FetcherAdapter` (`probe/crawl/fetcher_adapter.py`) and an opt-in real-network integration test (`tests/test_crawler_integration.py`) to validate real-network crawling behavior (skipped by default).

## [v0.3] - 2026-01-09

### Added (v0.3)

- Pluggable scoring framework (`probe.crawl.scorer`) with components:
  - `KeywordDensityScorer`, `BoilerplateDetector`, `LinkDensityScorer`, `EntityRegexScorer`
- `probe score <url>` CLI for local scoring and `--from-db` mode for scoring stored pages
- Seed-runner scoring integration with `--score`, `--score-keywords`, and `--persist-scores` flags
- Scoring persistence: `scoring_reports` table and `Map.add_scoring_report()` API
- Scoring export and analysis CLI: `probe analyze-crawl` (CSV/Markdown output)
- `probe export <entity>` to export entity documents and scores (CSV/Markdown)
- Optional tqdm progress bars in `seeds run` with `--no-progress` flag
- Domain blocklist support (`--blocked-domains`) and config-driven defaults
- Centralized configuration loader: `probe.config` (supports YAML/JSON)

### Changed

- Ingest changes: compute `content_hash` from cleaned text, separate internal/external links and store `outgoing_links`/`external_links` in page metadata
- `clean_html` now returns richer metadata (description, link counts, pdf_link_count, boilerplate_ratio)

### Fixed

- Multiple small bug fixes and test improvements. Full test suite passes locally (73+ tests at time of release).

### Migration

- Schema version bumped to **v0.1.1** (adds `scoring_reports` table).
- To migrate an existing database, run:

```bash
# Initialize or upgrade schema for a given DB
python cli.py init --db probe.db
```

This will create any missing tables without destroying existing data.

## [v0.2] - (previous entries)

- See prior notes in repository history.
