# Fetcher (v0.2)

## Overview

The fetcher provides a synchronous, test-first API to retrieve web resources and return cleaned, structured content suitable for ingestion into the Map.

## Key features

- HTTP fetching via `httpx` with configurable timeouts and retry/backoff behavior
- HTML cleaning and link extraction using `BeautifulSoup` (text, title, absolute links)
- PDF download and text extraction using `pdfplumber` (best-effort)
- Structured return value with `raw_bytes`, `text`, `title`, `links`, and `metadata`
- Simple ingest helper: `probe.crawl.ingest.ingest_fetch_result`

### API

fetch(url, timeout=10, max_size=10_000_000, max_retries=3, backoff_factor=0.5, sleep_func=None) -> dict

Return keys (not exhaustive):

- `url`, `status_code`, `headers`, `content_type`
- `is_pdf` (bool)
- `raw_bytes` (bytes) — raw response body
- `text` (str) — cleaned HTML text or extracted PDF text
- `title` (str) — HTML `<title>` when available
- `links` (list) — list of `{"url": ..., "text": ...}`
- `metadata` (dict) — e.g. `{"pages": N}` for PDFs
- `error` (str|None) — surface hints like `timeout`, `max_size_exceeded`, `pdf_extraction_failed`, `http_404`, etc.

### Testing notes

- Tests use `httpx.MockTransport` to simulate network responses; PDF extraction is mocked in tests where a full binary fixture isn't required.
- Consider adding a real PDF fixture under `tests/fixtures/` for an integration test with real `pdfplumber` behavior (we committed `tests/fixtures/sample.pdf`).

### Fetch options

- `max_size` (default 10_000_000): maximum response size in bytes; responses larger than this will be aborted and marked `max_size_exceeded` in the result and in run CSVs.
- `sleep_func`: test hook passed to `fetch` to override sleeping behavior during retries (useful for unit tests to avoid actual delays).
- `retry_count` is returned in the fetch result and recorded in run CSVs; `user_agent` is also exposed in fetch results.

### Integration

Use `ingest_fetch_result(map, result)` to write results to the Map. Document objects and pages are created with content hashes and metadata.

### CLI: `probe fetch`

A convenience CLI command is available to fetch a URL and optionally ingest the result into the Map:

```bash
# Fetch a URL and print summary
python cli.py fetch https://example.com

# Fetch and ingest into a specific DB
python cli.py fetch https://example.com --ingest --db /path/to/probe.db
```

### Testing & Fixtures

For a full end-to-end PDF extraction test, an example test uses `reportlab` to generate a small PDF and verifies `pdfplumber` extracts the expected text. The test is skipped when `reportlab` is not available; to generate a permanent fixture, run `tests/helpers/create_pdf_fixture.py` (requires `reportlab`).

### Future work

- Politeness: robots.txt and crawl-delay handling
- Async variant or coroutine-based client for higher throughput
- Add OCR fallback for image-only PDFs (out-of-scope for v0.2)

### Mode-aware defaults (policy integration)

The fetcher will expose conservative, mode-aware defaults when the Policy Engine is active:

| Setting | Guarded | Educational |
|------|--------:|------------:|
| Max size | 5 MB | 20 MB |
| Retries | Low | Moderate |
| OCR | Off | Optional |

Policy-driven defaults will be applied at runtime; follow-up PRs will implement enforcement and configuration plumbing.
