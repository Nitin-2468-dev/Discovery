# Probe: A Deep Research Engine

[![CI](https://github.com/Nitin-2468-dev/Discovery/actions/workflows/ci.yml/badge.svg)](https://github.com/Nitin-2468-dev/Discovery/actions)
[![OCR Scheduled CI](https://github.com/Nitin-2468-dev/Discovery/actions/workflows/ci.yml/badge.svg?event=schedule)](https://github.com/Nitin-2468-dev/Discovery/actions)

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

### Fetcher (v0.2) — implemented ✅
The fetcher is a synchronous, test-first implementation that:

- Uses `httpx` for HTTP requests with configurable timeouts and retries
- Cleans HTML with `BeautifulSoup` and extracts normalized absolute links
- Detects and extracts text from PDFs using `pdfplumber` (best-effort)
- Returns structured results: `status_code`, `content_type`, `text`, `title`, `links`, `raw_bytes`, `metadata`, and `error` hints
- Includes an ingestion helper `probe.crawl.ingest.ingest_fetch_result(map, result)` that persists pages and documents into the Map

### Seed runner & politeness
The CLI `seeds run <file>` command runs a list of seed URLs and writes a CSV summary and optional failure log. Important flags:

- `--summary-dir <dir>`: directory where timestamped CSV run summaries are written (default: `run_reports`).
- `--summary-csv <path>`: write the summary CSV to an explicit path (overrides `--summary-dir`). Useful in CI or automation where a specific filename is required.
- `--ignore-retry-after`: ignore server `Retry-After` headers and use exponential backoff instead (useful for controlled environments where servers return overly long waits).
- `--persistent-politeness`: enable persistent per-domain politeness — stores the last-crawl timestamp per domain in `.probe_state.json` and uses it to delay subsequent runs according to `--per-domain-delay`.

Persistent politeness stores timestamps in a small JSON file `.probe_state.json` in the current working directory as `{ "domain": "YYYY-MM-DDTHH:MM:SS.ssssss" }`. When enabled, the seed-runner consults this file to avoid hitting domains too quickly across separate runs.

(Other useful flags: `--concurrency`, `--per-domain-delay`, `--ignore-robots`, and `--no-log-failures`.)

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

CI note: the repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs tests across Python versions and optionally installs OCR dependencies when matrix `ocr` is set to `true`.

Unit and integration tests cover HTML cleaning, PDF extraction (mocked), max-size aborts, and retry/429 behavior.

## Quick Start
```bash
# Initialize
python cli.py init

# Add an entity
python cli.py add-entity "PT6A-52" --type engine

# Run seeds and write an explicit summary CSV (example)
python cli.py seeds run seeds.txt --limit 10 --summary-csv out/report.csv

# Investigate (coming soon)
python cli.py investigate "PT6A-52 maintenance manual"
```

## Tech Stack

- Python 3.10+
- SQLite (persistent map)
- httpx (HTTP client)
- BeautifulSoup (HTML parsing)
- sentence-transformers (embeddings, later)

No Scrapy, no Elasticsearch, no heavy frameworks.

## License

MIT