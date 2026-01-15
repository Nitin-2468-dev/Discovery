# Probe: A Deep Research Engine

[![CI](https://github.com/Nitin-2468-dev/Discovery/actions/workflows/ci.yml/badge.svg)](https://github.com/Nitin-2468-dev/Discovery/actions) [![OCR Scheduled CI](https://github.com/Nitin-2468-dev/Discovery/actions/workflows/ci.yml/badge.svg?event=schedule)](https://github.com/Nitin-2468-dev/Discovery/actions) [![Release](https://img.shields.io/github/v/release/Nitin-2468-dev/Discovery?label=release)](https://github.com/Nitin-2468-dev/Discovery/releases) [![License](https://img.shields.io/github/license/Nitin-2468-dev/Discovery?label=license)](https://github.com/Nitin-2468-dev/Discovery/blob/master/LICENSE)

> CI: Packaging preflight test trigger (non-functional README touch)

## What This Is

Probe is a personal discovery engine for finding information that search engines surface poorly:

- Maintenance manuals buried in PDFs
- Forum posts deep in pagination
- Archived technical documents
- Broker listings and spec sheets

It doesn't scrape everything—it investigates intelligently, like a human researcher, but faster and with memory.

## The Core Problem

Search engines favor SEO pages and stop at surface-level results. Real information lives:

- Deep in pagination
- In PDFs
- In old forum replies
- Behind indirect links

## How Probe Works

1. **Query the Knowledge Map**: Check what we already know
2. **Detect Gaps**: Identify missing information
3. **Generate Smart Seeds**: Use high-yield sources and entity relationships
4. **Crawl Intelligently**: Follow relevant links, stop when relevance drops
5. **Remember Everything**: Build a persistent semantic map

### The Key Innovation

> Most crawlers forget. Probe remembers.

Every query makes the system smarter. The map compounds over time.

## Design Philosophy

- **Investigation, not indexing**: This is a research instrument, not infrastructure
- **Stop early, not exhaustive**: Human-like exploration, not web-scale crawling
- **Memory over repetition**: Query the map before crawling the web
- **Evidence over structure**: PDFs are first-class citizens

## Current Status

**Phase:** Foundation (v0.1)

- [x] Schema design
- [x] Map interface
- [x] CLI basics
- [x] Fetcher (v0.2 - basic)
- [ ] Relevance scorer
- [ ] Investigation loop

**Release:** v0.1.1 (2026-01-11) — Adds an opt-in real-network integration workflow and a small `FetcherAdapter` to make validating real-network crawling behavior easier. See `CHANGELOG.md` for details and release notes.

### Fetcher (v0.2) — implemented ✅

The fetcher is a synchronous, test-first implementation that:

- Uses `httpx` for HTTP requests with configurable timeouts and retries
- Cleans HTML with `BeautifulSoup` and extracts normalized absolute links
- Detects and extracts text from PDFs using `pdfplumber` (best-effort) with an optional OCR fallback when `pdfplumber` extracts no text
- Returns structured results: `status_code`, `content_type`, `text`, `title`, `links`, `raw_bytes`, `metadata`, and `error` hints
- The HTML cleaner now returns richer metadata (including `description`, `link_count`, `pdf_link_count`, and `boilerplate_ratio`) and marks PDF links with `is_pdf` for easier downstream decisions
- The ingest helper `probe.crawl.ingest.ingest_fetch_result(map, result)` now computes page `content_hash` from cleaned text (falling back to raw bytes), differentiates internal vs external links, creates edges only for internal links, and stores `outgoing_links`/`external_links` in page metadata for follow-up

Tests: full test suite currently passes locally (52 tests).

### Seed runner & politeness

The CLI `seeds run <file>` command runs a list of seed URLs and writes a CSV summary and optional failure log. Important flags:

- `--summary-dir <dir>`: directory where timestamped CSV run summaries are written (default: `run_reports`).
- `--summary-csv <path>`: write the summary CSV to an explicit path (overrides `--summary-dir`). Useful in CI or automation where a specific filename is required.
- `--ignore-retry-after`: ignore server `Retry-After` headers and use exponential backoff instead (useful for controlled environments where servers return overly long waits).
- `--persistent-politeness`: enable persistent per-domain politeness — stores the last-crawl timestamp per domain in `.probe_state.json` and uses it to delay subsequent runs according to `--per-domain-delay`.
- `--score`: compute a relevance score for each fetched page during seed runs (requires `--score`)
- `--score-keywords`: comma-separated keywords to pass to the KeywordDensity and EntityRegex scorers.
- `--persist-scores`: write per-page scoring reports to the DB (`scoring_reports` table) when scoring is enabled.

Persistent politeness stores timestamps in a small JSON file `.probe_state.json` in the current working directory as `{ "domain": "YYYY-MM-DDTHH:MM:SS.ssssss" }`. When enabled, the seed-runner consults this file to avoid hitting domains too quickly across separate runs.

(Other useful flags: `--concurrency`, `--per-domain-delay`, `--ignore-robots`, and `--no-log-failures`.)

### Analyze & export scoring reports

Use `probe analyze-crawl` to export scoring reports for inspection and sharing.

Examples:

```bash
# Export reports for a specific URL to CSV
probe analyze-crawl --url https://example.com/page --format csv --out report.csv

# Export reports in Markdown for a date range (ISO datetime)
probe analyze-crawl --since 2026-01-01T00:00:00 --until 2026-01-09T23:59:59 --format md --out report.md
```

For automation or reporting, the CSV contains fields: `created_at, url, page_id, score, top_component, component_scores, metadata`.

Usage example (Python):

```python
from probe.crawl.fetcher import fetch
from probe.crawl.ingest import ingest_fetch_result
from probe.core.map import Map

res = fetch("https://example.com")
print(res["title"], len(res.get("text", "")))

m = Map()
ingest_fetch_result(m, res)
```

Fetcher class example (advanced):

```python
from probe.crawl.fetcher import Fetcher
from probe.observability import Metrics

# Create a Fetcher with UA rotation and custom metrics
metrics = Metrics()
fetcher = Fetcher(user_agents=["MyBot/1.0", "MyBot/1.1"], metrics_obj=metrics)

# Fetch and inspect result
res = fetcher.fetch("https://example.com")
print(res["status_code"], res.get("title"))

# Metrics recorded in `metrics` (dummy or Prometheus-backed)
print("fetch_total:", metrics.fetch_total.get() if hasattr(metrics.fetch_total, 'get') else 'prom')
```

Optional OCR dependencies (install if you want PDF OCR fallback):

- `pdf2image` and `pytesseract` are optional and required only for OCR fallback when `pdfplumber` returns no text.
- Install via pip using the requirements file:

```bash
pip install -r requirements-ocr.txt
```

- Or install as an optional extra (if you install the package):

```bash
pip install -e .[ocr]
```

CI note: the repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs tests across Python versions and includes an `ocr` matrix (installs OCR extras when `ocr=true`). The CI now installs the package in editable mode (`pip install -e .`) so optional extras are available while running tests.

Contributing & formatting

- We use `pre-commit` (Black, isort, ruff) to keep formatting consistent across contributors and CI. Run locally before committing:

```bash
pip install pre-commit mypy
pre-commit run --all-files
mypy --config-file mypy.ini
```

- The repository includes an Autofix workflow (`.github/workflows/autofix.yml`) that runs on pull requests and attempts to apply formatting fixes on the runner and push them back to the PR branch. Note:
  - The runner will attempt to push commits using the repository token (`GITHUB_TOKEN`) when allowed. The workflow is now tolerant of push failures (common for forked PRs where the token is read-only), so a failed push will no longer fail the job.
  - If CI reports a submodule-related post-checkout error (e.g., "No url found for submodule path 'tmp_ci_check' in .gitmodules"), follow the steps in `docs/CI.md` to remove the lingering gitlink and add it to `.gitignore`.

- To avoid autofix churn: run `pre-commit run --all-files` and `mypy --config-file mypy.ini` locally; address any failures before opening the PR.

Unit and integration tests cover HTML cleaning, PDF extraction (mocked), max-size aborts, and retry/429 behavior.

## Running tests

- Basic test run:

```bash
python -m pip install -U pip
pip install -r requirements.txt
pytest -q
```

- Parallel / fast tests (recommended):

```bash
# Install xdist (already included in dev requirements)
pip install -r requirements.txt
# Run all fast tests in parallel (-m "not slow")
pytest -q -n auto -m "not slow"
```

- Slow / integration tests (opt-in):

```bash
# Slow tests are marked with @pytest.mark.slow. Run them manually or in CI dispatch.
pytest -q -m slow -n 2
```

- Opt-in real-network integration test (local):

```bash
# By default this test is skipped; set env to opt-in and run the specific test
RUN_REAL_NET_TESTS=true pytest -q tests/test_crawler_integration.py::test_end_to_end_crawl_index_and_search_real
```

- Run tests with OCR extras (optional):

```bash
# Install OCR extras via requirements
pip install -r requirements-ocr.txt
pytest -q

# Or install optional extra when installing the package
pip install -e .[ocr]
pytest -q
```
- Reproduce packaging & editable install checks:

```bash
python -m pip install -U pip
pip install build
python -m build --sdist --wheel
pip install -e .
pip install -e .[ocr]
```

## Quick Start

```bash
# Initialize or upgrade the database schema (creates missing tables safely)
python cli.py init --db probe.db

# Add an entity
python cli.py add-entity "PT6A-52" --type engine

# Run seeds and write an explicit summary CSV (example)
python cli.py seeds run seeds.txt --limit 10 --summary-csv out/report.csv

# Score a URL manually
python cli.py score https://example.com --keywords manual,maintenance

# Export scoring reports for a URL
python cli.py analyze-crawl --url https://example.com/page --format csv --out report.csv

# Export documents for an entity
python cli.py export "PT6A-52" --format md --out pt6a52.md
```

See the full changelog in `CHANGELOG.md` for details on the v0.3 release and migration instructions.

## Tech Stack

- Python 3.10+
- SQLite (persistent map)
- httpx (HTTP client)
- BeautifulSoup (HTML parsing)
- sentence-transformers (embeddings, later)

No Scrapy, no Elasticsearch, no heavy frameworks.

## License

MIT
