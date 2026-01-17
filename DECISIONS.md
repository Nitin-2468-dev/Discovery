# Design Decisions

## Decision Log

### [2025-01-06] Storage: SQLite vs Graph Database

**Decision:** Start with SQLite

**Rationale:**
- Single file, no server setup
- Good enough for 10K-100K nodes
- Easier to inspect and debug
- Can migrate to Neo4j later if needed

**Trade-offs:**
- Graph queries will be less elegant (JOINs vs Cypher)
- May hit performance limits at 100K+ nodes

---

### [2025-01-06] Crawling: Scrapy vs Custom

**Decision:** Custom crawler with httpx

**Rationale:**
- Scrapy is built for full-site crawling
- We need fine-grained stopping logic
- Custom scorer needs tight integration
- Simpler to understand and modify

**Trade-offs:**
- Reinventing some wheels (rate limiting, retries)
- Less battle-tested at scale

---

### [2025-01-06] Relevance: Embeddings Now vs Later

**Decision:** Start with keyword/regex, add embeddings in v0.6

**Rationale:**
- Get investigation loop working first
- Embeddings add complexity and latency
- Keyword scoring is debuggable and fast

**Trade-offs:**
- Will miss semantic relationships early on
- May require re-scoring later

---

### [2025-01-06] Scope: Investigation vs Indexing

**Decision:** Build for targeted investigation, not web-scale indexing

**Rationale:**
- Different success criteria (find evidence vs comprehensive coverage)
- Justifies aggressive stopping
- Justifies local-only operation
- Clarifies what "good enough" means

**Trade-offs:**
- Won't be useful for broad research queries
- Not a Google replacement

---

### [2025-01-06] PDFs: First-Class vs Secondary

**Decision:** PDFs are terminal evidence nodes, prioritized over HTML

**Rationale:**
- Target use case (manuals, bulletins) lives in PDFs
- PDFs signal authoritative content
- HTML pages are often navigation to PDFs

**Trade-offs:**
- PDF extraction is slower and more error-prone
- Scanned PDFs require OCR (deferred)

---

### [2025-01-06] Map: Query Before Crawl

**Decision:** Always check map before generating seeds

**Rationale:**
- This is the core compounding mechanism
- Prevents redundant work
- Enables semantic expansion (find related entities)

**Trade-offs:**
- Requires good map query design upfront
- Slower cold start (no knowledge yet)
