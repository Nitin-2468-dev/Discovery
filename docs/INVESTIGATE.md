# `probe investigate` CLI

Usage: probe investigate <query> [options]

This command integrates GapDetector → SeedGenerator → Orchestrator to perform an investigation for a given query (typically an entity name).

Options:
- `--types` comma-separated desired document types (default: `driver`)
- `--max-seeds` maximum number of seeds to generate (default: 20)
- `--max-depth` crawl depth (default: 2)
- `--max-pages` maximum pages to fetch (default: 50)
- `--fetch-remote` enable SeedGenerator remote discovery (sitemap/robots)
- `--dry-run` do not perform the crawl; show suggested domains and seeds
- `--json` output machine-readable JSON
- `--resolve/--no-resolve` try to resolve the query to an existing entity using a substring match

Examples:

- Dry-run with JSON output (dry-run is the default):

  probe investigate "rtl8111" --types driver --json

- Run an investigation and perform the crawl:

  probe investigate "rtl8111" --types driver --max-pages 50

Notes:
- When a matching entity record is not present, the GapDetector will still suggest domains based on document-type heuristics (v0.5 conservative behavior).
- Use `--fetch-remote` to allow `SeedGenerator` to consult sitemaps and robots.txt (this may perform network requests).