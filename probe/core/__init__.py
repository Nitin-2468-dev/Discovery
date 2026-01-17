# probe.core package

# Import map_helpers to attach optional helper methods on Map at import time.
# This keeps compatibility with older Map implementations used in tests and
# allows lightweight queries like `get_entity_document_types` to exist when
# the underlying Map implementation is older.
try:
    from . import map_helpers  # type: ignore
except Exception:
    # Best-effort import; if map_helpers is not present or errors, continue silently
    pass
