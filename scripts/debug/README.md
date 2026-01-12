# Debug scripts

This folder contains small development-only scripts used to introspect code or run local reproductions while debugging.

These scripts are not part of the public API and are intended for local developer use only. They are not executed as part of the test suite or CI.

Examples:
- `attach_fresh.py` — load a fresh copy of `probe.core.map` and attach helpers into the loaded runtime (useful for diagnosing import-order issues).
- `debug_gap_run.py` — run a small scenario exercising `GapDetector` and domain helpers.
