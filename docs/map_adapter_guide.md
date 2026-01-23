# MapAdapter Guide

This short guide shows practical usage examples and a migration checklist for `MapAdapter`.

## Usage Examples 🔧

- Wrap an existing `Map` instance:

```python
from probe.core.map import Map
from probe.core.map_adapter import MapAdapter

m = Map("/path/to/db.sqlite")
adapter = MapAdapter(m)

# Add page/document
page_id = adapter.add_page(Page(id=None, url="https://example.com", domain="example.com"))
doc_id = adapter.add_document(Document(id=None, title="My PDF", doc_type="pdf", hash="h", url="https://example.com/a.pdf", domain="example.com"))

# Read map summary
summary = adapter.get_map_summary()
```

- Defensive metadata read in tests:

```python
cur = adapter.conn.execute("SELECT metadata FROM pages WHERE url = ?", (url,))
row = cur.fetchone()
md = adapter.extract_metadata(row)  # returns {} for NULL/malformed
```

## Migration checklist ✅

1. Accept `MapAdapter` in high-level modules (Orchestrator tests, integration runners) instead of `Map` where compatibility helper methods are useful.
2. When adding helpers that read raw DB rows, add unit tests for malformed/null metadata cases.
3. Prefer using `adapter.add_page`/`add_document` where possible to keep callsites stable; if direct SQL use is needed, expose `adapter.conn` and add tests.
4. Add adapter unit tests for delegation behavior when Map implementations change (e.g., return types or errors).

### Migration example: Orchestrator (before → after)

**Before** (accepts `Map` directly):

```python
class Orchestrator:
    def __init__(self, map: Map):
        self.map = map
```

**After** (accept either `Map` or `MapAdapter`, normalizes to an adapter):

```python
from probe.core.map_adapter import MapAdapter
from probe.core.map import Map

class Orchestrator:
    def __init__(self, map_obj: Map | MapAdapter):
        # Wrap raw Map instances with the adapter for a stable contract
        self.map = MapAdapter(map_obj) if isinstance(map_obj, Map) else map_obj
```

This pattern lets existing call sites pass a `Map` unchanged while new code can pass a `MapAdapter` directly. Add a small unit test that constructs the `Orchestrator` with both types to confirm behavior.

## Notes & Rationale 💡

- The adapter keeps the surface small and testable while allowing the Map implementation to evolve under it.
- Keep tests that depend on DB shape local to adapter tests so higher-level modules can rely on the adapter contract.
