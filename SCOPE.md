# Scope & Milestones

## v0.1 — Foundation (Current)

**Goal:** Persistent map + basic CLI

- [x] Schema design
- [x] Map interface (CRUD operations)
- [x] CLI (init, show, add-entity, domains)
- [x] Basic test coverage

**Success Criteria:** Can manually add entities and documents, query relationships

---

## v0.2 — Fetching

**Goal:** Retrieve and clean web content

- [x] HTTP fetcher (httpx-based)
- [x] HTML cleaning (BeautifulSoup)
- [x] PDF download + text extraction
- [x] Link extraction
- [x] Error handling (timeouts, 404s, rate limits, retries)

**Success Criteria:** `fetcher.fetch(url)` returns cleaned content, links, `title`, `raw_bytes`, and structured `metadata`. Tests cover HTML cleaning, PDF extraction, max-size aborts, and retry/429 behavior. An integration helper `probe.crawl.ingest.ingest_fetch_result` persists pages/documents into the Map.

> Notes: Implemented a sync `fetch` with configurable `max_retries` and `backoff_factor`. PDF extraction uses `pdfplumber` (fallbacks/edge-case hints are recorded in `error` field). Further work: scorer (v0.3) and politeness (robots.txt) enforcement in v0.3.

---

## v0.3 — Scoring (IMPLEMENTED)

**Goal:** Determine page relevance

- [x] Keyword density scorer
- [x] Entity regex matcher
- [x] Link density calculator
- [x] Boilerplate detector
- [x] Combined scoring formula
- [x] Branch stop logic

**Guidance:** Implement a pluggable composite scorer (e.g., `RelevanceScorer`) that composes multiple small scorers (keyword density, entity regex, link density, boilerplate detector) with tunable weights. Add debug logging explaining component scores, and a CLI command `probe score <url>` for local scoring inspection.

**Success Criteria:** `scorer.score(page, context)` returns 0.0-1.0, suggests stop/continue

**Notes:** v0.3 is implemented (see `CHANGELOG.md`). Schema bump: `v0.1.1` (adds `scoring_reports`) — run `python cli.py init --db <your_db>` to ensure schema is up-to-date before using scoring export features.

---

## v0.4 — Gap Detection

**Goal:** Identify what's missing

- [ ] Query map for entity knowledge
- [ ] Detect missing document types
- [ ] Identify weak confidence areas
- [ ] Suggest seed sources

**Success Criteria:** Given entity + desired doc type, returns gap analysis

---

## v0.5 — Investigation Loop

**Goal:** End-to-end query → answer

- [ ] Orchestrator (ties components together)
- [ ] Seed generator
- [ ] Breadth-first crawler with scoring
- [ ] Map ingest (add findings to graph)
- [ ] CLI: `probe investigate <query>`

**Success Criteria:** Can run full investigation, map accumulates knowledge

---

## v0.6 — Embeddings (Optional for v1)

**Goal:** Semantic similarity

- [ ] Generate embeddings for entities/documents
- [ ] Semantic search in map
- [ ] Similarity-based seed generation

**Success Criteria:** Queries like "engines similar to PT6A-52" work

---

## v1.0 — Production-Ready CLI

**Goal:** Stable, documented, tested

- [ ] Comprehensive test suite
- [ ] Error recovery (resume failed crawls)
- [ ] Logging and diagnostics
- [ ] Performance optimization
- [ ] Documentation

---

## Future (v2+)

- Web UI for map visualization
- Multi-entity queries ("compare X vs Y")
- Scheduled recrawling
- Export to markdown/PDF reports
- Cloud sync (optional)
- Collaborative maps (shared knowledge)

---

## Out of Scope (Forever)

- Full-site indexing
- Real-time web monitoring
- Authentication/login handling
- JavaScript-heavy SPA crawling (use sparingly)
- Competing with Google/Bing
