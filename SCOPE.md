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

**Research / CI (new):**

- Added a small `FetcherAdapter` (`probe/crawl/fetcher_adapter.py`) to provide a stable shim for higher-level tests.
- Added an opt-in scheduled/manual real-network integration workflow (`.github/workflows/research-integration.yml`) that runs a single real-network test on master when enabled (`RUN_REAL_NET_TESTS=true`). This helps validate end-to-end crawling behavior without introducing flaky tests into the main PR matrix.
- Local dev: run `RUN_REAL_NET_TESTS=true pytest -q tests/test_crawler_integration.py::test_end_to_end_crawl_index_and_search_real` to exercise the same test locally.

- CI maintenance (2026-01-15): removed a lingering `tmp_ci_check` gitlink that caused a post-checkout submodule error in Actions; made the Autofix workflow tolerant of push failures (so forked PRs won't fail the job when the runner cannot push); updated docs (CHANGELOG, `docs/CI.md`, `README.md`) and recorded the change in `constraints.log`.

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

## v0.4 — Gap Detection (in progress)
**Goal:** Identify what's missing

- [x] Query map for entity knowledge
- [x] Detect missing document types
- [x] Identify weak confidence areas
- [x] Suggest seed sources (implemented — `GapDetector` suggests candidate domains and `SeedGenerator` produces seeds; Investigator supports limited fetch passes and enforces policy; orchestrator and breadth-first crawler remain)

**Progress:** Implemented `GapDetector` (missing-type detection and candidate domain scoring with configurable weights), added Map compatibility helpers (`Map.get_domains_with_doc_type` attached at import time), and introduced normalization modes (`none`, `per_page`, `log`, `per_page_log`). Also added a weight-sweep utility (`scripts/weight_sweep.py`) and plotting helpers (`scripts/plot_sweep.py`), plus unit tests covering fallback behavior, heuristics, normalization, and plotting. See PR #27 for details and the full test results.

**Policy summary:** We introduced `Mode.educational_open` for broader exploration; it is permissive by default for domain allow checks but some operational relaxations (e.g., visualization details, auto-telemetry uploader) are gated by `admin_enabled`. Policy denials are recorded to `policy_denials.jsonl` and a CLI command `probe policy upload-telemetry` exists to upload telemetry to S3. The automatic telemetry uploader (rotate-and-upload) is planned for v0.5.

**Success Criteria:** Given entity + desired doc type, returns gap analysis including missing types, suggested domains, and optional per-domain component scores; supports weight tuning and normalization for seed-suggestion heuristics.

---

## v0.5 — Investigation Loop (Baseline tagged v0.5)

**Baseline:** Tag `v0.5` created on 2026-01-18; branch `work/from-v0.5` seeded from this tag for follow-up work.

**Goal:** End-to-end query → answer

- [ ] Orchestrator (ties components together)
- [ ] Seed generator
- [ ] Breadth-first crawler with scoring
- [ ] Map ingest (add findings to graph)
- [ ] CLI: `probe investigate <query>`

**v0.5 Add-on — Link Signals (Context-Aware Crawling):** See `docs/LINK_SIGNALS.md` for the conservative v0.5 contract for local context extraction and link-context signals (signal-only, no edges, no entities, no embeddings).

**Success Criteria:** Can run full investigation, map accumulates knowledge

> **Note — Educational Openness:** Add support for an **"Educational Openness"** mode (e.g., `Mode.educational_open`) that relaxes some gating for research and educational use-cases to enable broader exploration and transparency. This mode must include clear disclaimers, logging, and opt-in administrative enablement, and **is not intended** as the default for production deployments.

---

## v0.6 — Embeddings (Optional for v1)

**Goal:** Semantic similarity (see `SEMANTIC_SEARCH.md` for the integration contract)

- [ ] Generate embeddings for entities/documents (bucketed, isolated)
- [ ] Semantic search in map (hybrid retrieval: FTS + embeddings)
- [ ] Similarity-based seed generation (verification required)

**Success Criteria:** Queries like "engines similar to PT6A-52" work; embeddings are navigation aids only and must follow rules in `SEMANTIC_SEARCH.md` (Design locked v1).

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
