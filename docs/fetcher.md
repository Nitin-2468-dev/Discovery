# Fetcher (v0.2)

Overview
--------
The fetcher provides a synchronous, test-first API to retrieve web resources and return cleaned, structured content suitable for ingestion into the Map.

Key features
------------
- HTTP fetching via `httpx` with configurable timeouts and retry/backoff behavior
- HTML cleaning and link extraction using `BeautifulSoup` (text, title, absolute links)
- PDF download and text extraction using `pdfplumber` (best-effort)
- Structured return value with `raw_bytes`, `text`, `title`, `links`, and `metadata`
- Simple ingest helper: `probe.crawl.ingest.ingest_fetch_result`

API
---
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

Testing notes
-------------
- Tests use `httpx.MockTransport` to simulate network responses; PDF extraction is mocked in tests where a full binary fixture isn't required.
- Consider adding a real PDF fixture under `tests/fixtures/` for an integration test with real `pdfplumber` behavior.

Integration
-----------
Use `ingest_fetch_result(map, result)` to write results to the Map. Document objects and pages are created with content hashes and metadata.

Future work
-----------
- Politeness: robots.txt and crawl-delay handling
- Async variant or coroutine-based client for higher throughput
- Add OCR fallback for image-only PDFs (out-of-scope for v0.2)
