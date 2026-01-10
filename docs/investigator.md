# Investigator (v0.4)

The Investigator orchestrates a short investigation loop for an entity:

1. Detect gaps using `GapDetector`.
2. Generate seeds for missing document types using `SeedGenerator`.
3. Optionally perform a limited fetch pass over generated seeds (dry-run by default).

Usage:

```bash
# Dry-run: generate seeds without fetching
probe investigate "PT6A-52" --types manual,spec --max-seeds 10 --db probe.db

# Run fetches for generated seeds (best-effort)
probe investigate "PT6A-52" --types manual,spec --max-seeds 10 --no-dry-run --db probe.db
```

The Investigator is intentionally conservative in v0.4 — it focuses on producing actionable seeds and a small, opt-in runtime for fetching.
