# Orchestrator

The Orchestrator ties together `GapDetector`, `SeedGenerator`, and a crawler to provide a simple gap→seed→crawl flow.

Usage (CLI):

```
# Run an orchestration for entity 'rtl8111' and 'driver' doc type
probe orchestrate run "rtl8111" --types driver --max-seeds 10 --max-depth 1 --max-pages 20
```

Behavior:
- GapDetector analyzes missing document types and suggests high-yield domains.
- SeedGenerator produces seeds for suggested domains (honors robots/sitemap when enabled).
- BreadthFirstCrawler fetches seeds and persists page records into the Map.
- Orchestrator updates domain-level stats based on pages and documents discovered during the run.

Notes:
- This is intentionally conservative: the orchestrator does not auto-create relationships or mark documents as verified. It is a discovery pipeline only.
