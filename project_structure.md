# Probe: Project Setup Guide

## 📁 Complete Directory Structure

```
probe/
├── README.md               # Project vision and philosophy
├── ARCHITECTURE.md         # System design and components
├── SCOPE.md               # Milestones and boundaries
├── DECISIONS.md           # Architectural choices log
├── FRAMEWORK.md           # BMad Method documentation
├── CORE.md               # BMad Core components
├── constraints.log       # Violation and decision tracking
├── requirements.txt      # Python dependencies
├── cli.py               # Command-line interface
├── probe/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── schema.py    # Database schema (DONE)
│   │   └── map.py       # Knowledge graph interface (DONE)
│   ├── crawl/           # v0.2+
│   │   ├── __init__.py
│   │   ├── fetcher.py   # HTTP/PDF fetching
│   │   ├── reporting.py # CSV run summaries and failure logs
│   │   ├── robots.py    # robots.txt helper with caching and crawl_delay
│   │   └── scorer.py    # Relevance scoring

# Notes on Seed Runner & Politeness
- `seeds run` writes CSV summaries and optional constraints logs.
- `--summary-dir` writes timestamped CSV files into a directory; `--summary-csv <path>` writes to an explicit filename.
- `--persistent-politeness` stores `.probe_state.json` (domain -> ISO timestamp) to enforce per-domain delays across separate runs.
│   └── analysis/        # v0.4+
│       ├── __init__.py
│       └── gaps.py      # Gap detection logic
└── tests/
    ├── __init__.py
    ├── test_schema.py
    ├── test_map.py
    └── test_cli.py
```

---

## 🚀 Setup Instructions

### 1. Create Project Structure

```bash
# Create main directory
mkdir probe
cd probe

# Create subdirectories
mkdir -p probe/core
mkdir -p probe/crawl
mkdir -p probe/analysis
mkdir -p tests

# Create __init__.py files
touch probe/__init__.py
touch probe/core/__init__.py
touch probe/crawl/__init__.py
touch probe/analysis/__init__.py
touch tests/__init__.py
```

### 2. Copy Artifacts

Copy the following files from the artifacts above:

1. **constraints.log** → Root directory
2. **probe/core/schema.py** → `probe/core/`
3. **probe/core/map.py** → `probe/core/`
4. **cli.py** → Root directory
5. **requirements.txt** → Root directory

Also copy your spec-kit files:
- README.md
- ARCHITECTURE.md
- SCOPE.md
- DECISIONS.md
- FRAMEWORK.md
- CORE.md

### 3. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Initialize the Database

```bash
# Test schema initialization directly
python probe/core/schema.py

# Or use the CLI
python cli.py init
```

**Expected output:**
```
Initializing Probe database...
✓ Schema initialized successfully
✓ Created 5 tables: documents, domains, edges, entities, pages
```

---

## ✅ Verify Installation

### Test 1: Add an Entity
```bash
python cli.py add-entity "PT6A-52" --type engine
```

**Expected:**
```
✓ Added entity 'PT6A-52' (ID: 1, Type: engine)
```

### Test 2: Show Entity
```bash
python cli.py show "PT6A-52"
```

**Expected:**
```
📍 Entity: PT6A-52
   Type: engine
   Confidence: 0.50
   First seen: 2025-01-06 ...
   Last seen: 2025-01-06 ...

📄 No documents found yet.
```

### Test 3: View Summary
```bash
python cli.py summary
```

**Expected:**
```
📊 Probe Map Summary:

  Entities:       1
  Documents:      0
  Pages:          0
  Domains:        0
  Edges:          0
```

### Test 4: Link Entity to Document
```bash
python cli.py link "PT6A-52" \
  "PT6A-52 Maintenance Manual" \
  "https://pwc.ca/manuals/pt6a-52.pdf" \
  --type manual \
  --hash "abc123def456..."
```

**Expected:**
```
✓ Linked 'PT6A-52' → 'PT6A-52 Maintenance Manual'
  Relation: mentions
  Document ID: 1
  Edge ID: 1
```

---

## 🧪 Testing the Map Interface

Create a test script `test_manual.py`:

```python
from probe.core.schema import initialize_schema
from probe.core.map import Map, Entity, Document, Edge

# Initialize
conn = initialize_schema("test.db")
conn.close()

# Create map
m = Map("test.db")

# Add entity
entity = Entity(id=None, name="PT6A-52", type="engine")
entity_id = m.add_entity(entity)
print(f"Created entity: {entity_id}")

# Add document
doc = Document(
    id=None,
    title="PT6A-52 Manual",
    doc_type="manual",
    hash="abc123",
    url="https://example.com/manual.pdf",
    domain="example.com"
)
doc_id = m.add_document(doc)
print(f"Created document: {doc_id}")

# Link them
edge = Edge(
    id=None,
    from_type="entity",
    from_id=entity_id,
    to_type="document",
    to_id=doc_id,
    relation="specifies"
)
edge_id = m.add_edge(edge)
print(f"Created edge: {edge_id}")

# Query
docs = m.get_entity_documents("PT6A-52")
print(f"Found {len(docs)} documents for PT6A-52")
print(f"  - {docs[0].title}")

# Summary
summary = m.get_map_summary()
print(f"\nMap summary: {summary}")

m.close()
```

Run it:
```bash
python test_manual.py
```

---

## 📝 Next Steps (After Setup)

### Immediate (v0.1 Foundation)
1. ✅ Schema complete
2. ✅ Map interface complete
3. ✅ CLI complete
4. ⏭️ Write tests for Map layer
5. ⏭️ Start logging violations in `constraints.log`

### Coming Next (v0.2 Fetching)
1. Implement `probe/crawl/fetcher.py`
2. Add HTTP fetching with httpx
3. Add PDF download/extraction
4. Add HTML cleaning

### Remember
- Log every temptation in `constraints.log`
- Don't skip ahead to v0.2+ features
- Keep architecture aligned with ARCHITECTURE.md
- Update DECISIONS.md when making choices

---

## 🎯 Success Criteria for v0.1

You've completed v0.1 when:

- [x] Database schema is stable
- [x] Map interface works for all node types
- [x] CLI commands work (init, add-entity, show, domains, summary, link)
- [ ] Basic tests pass
- [ ] Can manually build a small knowledge graph (10+ entities, 5+ documents)
- [ ] `constraints.log` has 5+ entries

**Current Status: Foundation layer complete, ready for testing phase.**
