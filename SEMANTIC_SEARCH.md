# Semantic Search Integration (Probe)

**Status:** Stable
**Scope:** V1 (Design Locked)
**Audience:** Core developers / contributors
**Last Updated:** 2026-01-17

---

## Purpose

This document defines **how semantic search is integrated into Probe** and the **rules that govern its use**.

It is not an overview of embeddings or AI.
It is a **contract** that ensures:

- No hallucinated relationships
- No cross-domain collisions
- No trust leaks
- No “AI decides truth” failures

If you change this file, you are changing Probe’s epistemology.

---

## Core Invariant (Read This First)

> **Embeddings are navigation aids, not sources of truth.**

Probe enforces this invariant structurally:

```

Hard boundaries (buckets)
→ Soft navigation (embeddings inside bucket)
→ Hard facts (explicit edges + evidence)

```

Any code that violates this invariant is incorrect by definition.

---

## What Semantic Search Is Allowed To Do

Semantic search (embeddings) may be used ONLY for:

- Fuzzy matching of natural language queries
- Improving recall inside a bucket
- Clustering similar descriptions
- Deduplication of near-identical content
- Ranking candidates before verification

Semantic search may NEVER:

- Create relationships
- Imply compatibility
- Establish authority or trust
- Replace explicit graph edges
- Feed unverified facts to AI

---

## Bucket Model (Hard Boundaries)

All semantic search is **bucket-scoped**.

### V1 Buckets

| Bucket | Description | Embedding Table |
|------|------------|----------------|
| Documents | Datasheets, manuals, specs | `document_embeddings` |
| Drivers | Kernel modules, firmware | `driver_embeddings` |
| Community | Forums, Q&A | `community_embeddings` |

Rules:

- Each bucket has its **own vector table**
- No cross-bucket similarity queries
- No shared embedding space

This prevents semantic collisions (e.g. fish ≠ diamond).

---

## Examples

**Allowed (pseudocode):**

```python
# Search embeddings inside the single 'drivers' bucket (OK)
results = embedding_search(bucket='drivers', query='rtl8111 driver', top_k=50)
```

**Disallowed (pseudocode):**

```python
# Cross-bucket similarity is PROHIBITED
results = embedding_search(buckets=['drivers', 'documents'], query='rtl8111')  # ❌ do not do this
```

---

## Enforcement & CI checks

To keep the contract enforceable, the repo requires automated checks and tests for any semantic-search code changes:

- Unit tests: any new code that uses embeddings must include unit tests that assert the code operates with an explicit single `bucket` and rejects cross-bucket queries.
- Integration tests: add a test that attempts a cross-bucket query and expects a raised exception or validation error.
- CI gate: require that `tests/test_semantic_search_contract.py` exists/updates for any changes adding embeddings or new buckets.
- PR checklist: all PRs touching search or embedding code must include:
  - A unit test demonstrating bucket-isolation, and
  - Documentation for the new bucket and its allowed scopes.

Violations discovered by tests are **treated as critical** and must be reverted or fixed before merge.

---

## Embedding Containment Rule

**Rule:**
Embeddings may operate *only* inside their bucket and may never generate edges.

**Enforced By:**
- Separate vector tables
- No JOINs between embedding tables
- Search APIs require explicit `bucket` selection

Violations are considered **critical bugs**.

---

## Relationship Truth Model

All relationships must be:

1. **Explicit** – stored in the `edges` table
2. **Evidenced** – backed by `relationship_evidence`
3. **Auditable** – source URL + confidence required

### Truth Comes From

- Explicit edges
- Evidence records
- Trust metadata

### Truth Never Comes From

- Vector similarity
- LLM output
- Keyword proximity

---

## Verified Search Pipeline

All user-facing search flows must follow this order:

```

Query
↓
Bucket Selection (rules / CLI flag)
↓
Hybrid Retrieval

* FTS5 (precision)
* Embeddings (recall)
  ↓
  Candidate Merge & Ranking
  ↓
  Relationship Verification
* Evidence required (optional override)
* Confidence threshold enforced
  ↓
  (Optional) AI Summary
* Verified facts only
* Citations included

```

AI is **never** allowed upstream of verification.

---

## Hybrid Search Rules

### Weighting (Default)

```python
keyword_weight = 0.6
vector_weight  = 0.4
```

* Keyword search anchors precision
* Embeddings improve recall
* Final ranking is deterministic

### Vector Thresholds

* Similarity thresholds are **filters**, not decisions
* Distance ≠ truth
* Thresholds may evolve, invariants may not

---

## Evidence Requirements

### relationship_evidence Is Mandatory When:

* `require_evidence=True`
* Results are shown as “verified”
* Results are passed to AI

### Evidence Must Include:

* `source_type`
* `source_url`
* `confidence`
* timestamp

No evidence → no verified relationship.

---

## Trust Metadata Rules

Trust is **metadata**, not semantics.

Allowed trust signals:

* Domain classification (`OEM`, `community`, `archive`)
* Verification level (`manual`, `community`, `automated`)
* Timestamps

Embeddings and AI **must never infer trust**.

---

## AI Integration Contract

AI components:

* Receive **verified facts only**
* Receive **citations + confidence**
* Never see raw vector results
* Never create edges or claims

AI output is:

* Explanatory
* Summarizing
* Non-authoritative

AI is not a source of truth.

---

## What NOT to Add (Without Design Review)

The following are **explicitly out of scope for V1**:

* Cross-bucket semantic similarity
* Auto-generated relationships
* Ontology inference
* Trust scoring via AI
* Graph construction via embeddings
* “Let the LLM decide” logic

Adding any of these breaks Probe’s guarantees.

---

## Extension Rules (Future)

You MAY extend Probe by:

* Adding new buckets (with isolation)
* Adding new evidence types
* Adding new relationship types
* Adding new embedding scopes

You MAY NOT extend Probe by:

* Removing evidence requirements
* Allowing embeddings to create edges
* Letting AI bypass verification

---

## Developer Checklist

Before merging semantic-search-related code, ensure the following **mandatory** items are satisfied:

* [ ] Does this operate inside a single bucket only? (no cross-bucket queries)
* [ ] Does it avoid creating relationships or mutating `edges` directly?
* [ ] Are all claims backed by explicit edges and evidence where required?
* [ ] Is evidence required and collected for verified flows?
* [ ] Does AI only receive verified data (citations + confidence)?
* [ ] Is there a unit test that asserts bucket isolation or raises on cross-bucket use?
* [ ] Is there an integration test covering the verification step for the new flow?
* [ ] Documentation updated: `SEMANTIC_SEARCH.md` and any bucket docs or schema changes
* [ ] CI tests updated: add entries to `tests/test_semantic_search_contract.py` demonstrating isolation and evidence requirements

If any answer is “no”, the PR must be blocked and the author should address the failure before merging.

---

## Summary (Non-Negotiable)

Probe is **not** an AI-first system.
Probe is a **truth-first system with semantic navigation**.

Embeddings help humans find the right area.
Structured data and evidence decide what is true.

This file defines that boundary.

---

**Design Locked. Do not loosen without consensus.**
