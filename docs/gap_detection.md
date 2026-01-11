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

## Tuning weights

`GapDetector` supports tunable weights to control how suggested domains are ranked. You can pass weights when instantiating `GapDetector`:

```python
from probe.analysis.gaps import GapDetector

# example: increase importance of domains known to contain missing types
gd = GapDetector(map_obj, weights={"count": 3.0, "yield": 1.0, "trust": 0.5, "recent": 0.5})
```

Supported weight keys:
- `count` — weight for frequency of domain appearances across missing types (default 2.0)
- `yield` — weight for domain `yield_score` (default 1.0)
- `trust` — weight for domain `trust_score` (default 0.5)
- `recent` — weight for recency boost (default 0.5)

Tweak weights to bias suggestions for your use case (e.g., favor yield over trust for exploratory crawls).

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
