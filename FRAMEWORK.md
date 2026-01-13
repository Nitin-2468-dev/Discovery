# Development Framework

This project follows the BMad Method for project control:

## 1. Vision-First Design

- README.md defines what and why
- Prevents building without purpose

## 2. Architecture-First Implementation

- ARCHITECTURE.md locks system design
- Code implements the design, not the other way around

## 3. Scope Enforcement

- SCOPE.md defines milestones and boundaries
- Prevents feature creep and bikeshedding

## 4. Decision Logging

- DECISIONS.md records architectural choices
- Prevents circular debates and context loss

## 5. Foundation-First Building

- Map layer before everything else
- Each layer depends on the previous
- No skipping ahead to "cool features"

## Seed runner & politeness

The `seeds run` CLI performs polite fetching and writes CSV summaries. Key points:

- `--per-domain-delay` controls the minimum delay between requests to the same domain.
- `--persistent-politeness` stores domain last-crawl timestamps in `.probe_state.json` (per-domain ISO timestamps) to avoid hitting domains too quickly across runs.
- Use `--summary-dir` to control the output directory for timestamped CSV runs, or `--summary-csv <path>` to produce a file with an explicit path (useful for automation/CI).

## Why This Matters

- Projects survive breaks (weeks, months)
- New contributors onboard cleanly
- Refactors have context
- Success criteria are explicit
