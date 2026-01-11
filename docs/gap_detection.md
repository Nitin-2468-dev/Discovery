# Gap Detection (v0.4)

Gap detection identifies missing documents and weak confidence areas for tracked entities. This document describes the algorithm, CLI usage, and examples.

## Concepts

- Desired document types: a small taxonomy of high-value document types (e.g., `manual`, `spec`, `bulletin`).
- Missing types: the set difference between desired types and types already present in the Map.
- Weak confidence: when an entity's `confidence_score` falls below a configurable threshold (default 0.7).
- Suggested domains: the highest-yield domains in the Map (requires domains with sufficient pages crawled).

## Algorithm

- Load the entity and its document types (lightweight SQL query for distinct types).
- Compute missing types and weak-confidence flag.
- Return a small analysis payload suitable for CLI and programmatic consumption.

## CLI

`probe gaps <entity_name> [--types manual,bulletin,spec] [--db probe.db] [--json]`

- `--json` emits JSON suitable for automation.

Example:

```bash
probe gaps "PT6A-52" --types manual,bulletin,spec
```

## Seed Generation

You can generate seed URLs for a given entity and document type using the CLI:

```bash
probe seeds gen "PT6A-52" --type manual --max 10
```

Use `--json` to emit machine-readable seed payloads for automation.
