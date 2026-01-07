# Probe: A Deep Research Engine

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

Unit and integration tests cover HTML cleaning, PDF extraction (mocked), max-size aborts, and retry/429 behavior.

## Quick Start
```bash
# Initialize
python cli.py init

# Add an entity
python cli.py add-entity "PT6A-52" --type engine

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