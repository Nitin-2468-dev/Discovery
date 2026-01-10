# Changelog

All notable changes to this project are documented in this file.

## [v0.4] - 2026-01-10
### Added
- Investigator: prioritization, ingest feedback loop, and improved CLI controls to run investigations and dry-runs.
- Seed generator: `probe.analysis.seed_generator.SeedGenerator` for generating high-quality seeds from domains and entities.
- Gap detection: `probe.analysis.gaps.GapDetector` enhancements and lightweight Map helpers for efficient queries.

### Fixed
- Defensive imports: made imports in `probe.analysis.investigator` lazy and added diagnostics to surface missing exports during import-time errors.
- Tests: added smoke tests to assert `probe.analysis.gaps` exports `GapDetector` and that `probe.analysis.investigator` imports successfully.
- CI: added a pre-test check that fails on empty Python files (excluding `__init__.py`) and fixed a YAML parsing edge case (quoted step name).

### Notes
- These changes address import-time failures observed in CI and add defensive checks to catch regressions early.

## [v0.3] - 2026-01-09
### Added
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
