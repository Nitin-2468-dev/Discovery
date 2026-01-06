# Scope & Milestones

## v0.1 — Foundation (Current)
**Goal:** Persistent map + basic CLI

- [x] Schema design
- [x] Map interface (CRUD operations)
- [x] CLI (init, show, add-entity, domains)
- [ ] Basic test coverage

**Success Criteria:** Can manually add entities and documents, query relationships

---

## v0.2 — Fetching
**Goal:** Retrieve and clean web content

- [ ] HTTP fetcher (httpx-based)
- [ ] HTML cleaning (BeautifulSoup)
- [ ] PDF download + text extraction
- [ ] Link extraction
- [ ] Error handling (timeouts, 404s, rate limits)

**Success Criteria:** `fetcher.fetch(url)` returns cleaned content and links

---

## v0.3 — Scoring
**Goal:** Determine page relevance

- [ ] Keyword density scorer
- [ ] Entity regex matcher
- [ ] Link density calculator
- [ ] Boilerplate detector
- [ ] Combined scoring formula
- [ ] Branch stop logic

**Success Criteria:** `scorer.score(page, context)` returns 0.0-1.0, suggests stop/continue

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