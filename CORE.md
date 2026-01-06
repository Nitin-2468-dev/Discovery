# System Core Components

Every investigation system needs five components:

## 1. Memory (The Map)
**Purpose:** Persistent knowledge accumulation

**In Probe:**
- SQLite knowledge graph
- Entities, documents, pages, domains
- Relationships and confidence scores

**Key Property:** Queries get smarter over time

---

## 2. Coordinator (The Orchestrator)
**Purpose:** Decision-making and flow control

**In Probe:**
- Query parsing
- Gap detection
- Seed generation
- Stop condition enforcement

**Key Property:** Prevents infinite loops and wasted work

---

## 3. Executor (The Worker)
**Purpose:** Doing the actual work

**In Probe:**
- HTTP fetching (httpx)
- HTML cleaning (BeautifulSoup)
- PDF extraction
- Link following

**Key Property:** Replaceable without breaking system

---

## 4. Evaluator (The Scorer)
**Purpose:** Quality and relevance assessment

**In Probe:**
- Relevance scoring formula
- Branch stopping logic
- Domain yield tracking

**Key Property:** Tunable without rewriting crawler

---

## 5. Interface (Human Control)
**Purpose:** Inspection and control

**In Probe:**
- CLI commands (probe init, investigate, show)
- Map inspection tools
- Debug visibility

**Key Property:** System is never a black box