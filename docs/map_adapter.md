# Map Adapter (probe/core/map_adapter.py)

🔧 **Purpose**

The MapAdapter is a thin compatibility layer around `probe.core.map.Map` that:

- Provides a stable, small surface for callers (Orchestrator and tests) to interact with the Map.
- Exposes convenience helpers such as `extract_metadata` that safely deserialize stored JSON metadata.
- Makes it easier to add tests and handle backward-compatible adapter behavior when the Map storage shape changes.

💡 **Key behaviors**

- Delegates `add_page`, `add_document`, `get_map_summary`, and other simple methods to the underlying `Map` instance.
- Exposes `conn` (the underlying sqlite3.Connection) for test helpers and direct queries when necessary.
- `extract_metadata(row)` defensively handles `NULL` or malformed JSON values and returns an empty dict on error.

🚀 **Usage / Migration tips**

- To accept Map-like objects in higher-level modules, prefer accepting a `MapAdapter` or wrapping a `Map` via `MapAdapter(map)`.
- When adding new adapter helpers, add unit tests that cover both normal behavior and error cases (e.g., malformed metadata or DB errors).

---

**Where to add tests:**
- Unit tests for adapter behavior live under `tests/test_map_adapter.py` and `tests/test_map_adapter_errors.py`.

**Next steps:**
- Expand adapter tests to include failure modes, edge cases for metadata, and more delegated method behaviors as needed.
