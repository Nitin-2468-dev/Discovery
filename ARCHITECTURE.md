# Architecture

## System Overview
```
Query → Map Query → Gap Detection → Seed Generation → Crawler → Map Update
   ↓                                                                ↓
Answer ←────────────────── Synthesize ←──────────────────────────┘
```

**Policy Engine (new):** a global gatekeeper that evaluates queries and seeds
before they reach the Orchestrator. It enforces the active mode (`public_guarded`
or `educational_open`) and annotates or restricts actions when necessary.

**High-level flow with Policy:**
```
User / Chat / MCP
        ↓
   Policy Engine
        ↓
Orchestrator / Investigator
```

## Components

### 1. The Map (Knowledge Graph)

**Persistent storage of everything discovered.**

**Node Types:**
- **Entity**: Things being investigated (engines, regulations, companies)
- **Document**: Terminal evidence nodes (PDFs, manuals, bulletins)
- **Page**: Navigational nodes (HTML pages)
- **Domain**: Source tracking (yield and trust scores)

**Edge Types:**
- Entity → Document (mentions, specifies)
- Page → Document (links_to)
- Document → Document (cites, supersedes)
- Page → Page (navigates_to)
- Entity → Entity (variant_of, related_to)

**Storage:** SQLite with JSON fields for flexibility

**Key Methods:**
- `get_entity(name)` → retrieve known entity
- `get_entity_documents(name)` → find linked evidence
- `get_high_yield_domains()` → identify good sources
- `has_documents_for_entity(name, type)` → detect gaps

---

### 2. The Orchestrator (Decision Engine)

**Decides what to investigate and when to stop.**

**Flow:**
1. Parse query into entity + intent
2. Query map for existing knowledge
3. Detect gaps (missing document types, weak confidence, old dates)
4. Generate seeds from:
   - High-yield domains
   - Known entity neighborhoods
   - External sources (search APIs)
5. Hand seeds to crawler with stop conditions

**Stop Conditions:**
- Gap filled (found target document type)
- N consecutive low-relevance pages
- Seed budget exhausted

---

### 3. The Crawler (Exploration Engine)

**Fetches and scores pages, following relevant links.**

**Key Behavior:**
- Breadth-first with relevance pruning
- Domain-aware (respects robots.txt, rate limits)
- PDF-aware (downloads and extracts)
- Stops branches early if relevance drops

**Not Implemented:**
- Full-site crawling
- Infinite depth
- Authentication/login

---

### 4. The Scorer (Relevance Engine)

**Determines if a page is worth exploring further.**

**Formula (v1):**
```
score =
  0.4 * embedding_similarity +
  0.3 * keyword_density +
  0.2 * entity_regex_hits -
  0.1 * link_density -
  0.15 * boilerplate_ratio
```

**Branch Stop Rule:**
If 3 consecutive pages score < 0.3 → stop branch

**Global Stop Rule:**
If no new entities/docs found in last N pages → stop crawl

---

### 5. The Analyzer (Synthesis Engine)

**Combines map knowledge + new findings into answers.**

*(Phase 2)*

---

## Data Flow Example

**Query:** "PT6A-52 maintenance manual"

1. **Map Query:**
   - Found entity: PT6A-52 (engine)
   - Found 2 documents: service bulletin, spec sheet
   - Missing: maintenance manual
   - High-yield domains: pwc.ca, aviation-forums.com

2. **Gap Detection:**
   - Need: document type = "manual"
   - Priority: high

3. **Seed Generation:**
   - pwc.ca/support/manuals
   - aviation-forums.com/search?q=PT6A-52+manual
   - Google: "PT6A-52 maintenance manual filetype:pdf"

4. **Crawl:**
   - Fetch seeds → extract links → score → follow relevant → repeat
   - Stop when: manual found OR 3 consecutive low-score pages

5. **Map Update:**
   - Add document node (manual)
   - Add entity → document edge
   - Update domain yield scores
   - Store page → document links

6. **Result:**
   - Return: new manual + existing documents
   - Map is now smarter for related queries (PT6A-60, PT6A-65)

---

## Design Decisions

### Why SQLite?
- Single file, portable
- Good enough for 10K-100K nodes
- Migrate to Neo4j only if needed

### Why Not Scrapy?
- Too heavy for small-scale investigation
- Built for full-site crawling, not targeted exploration
- We need custom stopping logic

### Why httpx?
- Simple, async-capable
- We control every request
- Playwright only when JavaScript is required

### Why "Investigation, Not Indexing"?
- Justifies aggressive stopping
- Justifies imperfect data
- Justifies local-only scale
- Clarifies success criteria (find evidence, not index web)

---

## Non-Goals

- Indexing the entire web
- Real-time updates
- Multi-user collaboration (v1)
- Web UI (v1)
- Cloud deployment (v1)
