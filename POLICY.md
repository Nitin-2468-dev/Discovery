# POLICY.md

## Purpose
This document defines **global policy enforcement** for Probe / Discovery. Policies apply uniformly across **CLI, chat, MCP, agents, and automation**.

The system supports **two public modes**:

- `public_guarded` — safe-by-default, suitable for general users
- `educational_open` — reduced restrictions for learning & research

Policies are enforced **centrally** and are not re-implemented per feature.

---

## Core Principles

1. **Single Source of Truth**
   - Policy decisions are derived from the active `mode`
   - No component may bypass policy checks

2. **Context Over Censorship**
   - Prefer warnings, annotations, and scope-limiting over hard blocks

3. **Education ≠ Automation**
   - Even in `educational_open`, the system explains concepts
   - It does not autonomously execute harmful actions

---

## Modes

### public_guarded

Allowed:
- OSINT (news, public reports, archives)
- Cybersecurity *defensive* explanations
- Stock-related qualitative research
- Documentation discovery

Restricted:
- Exploit code
- Step-by-step intrusion guides
- Mass surveillance instructions
- Autonomous deep crawling of risky domains

---

### educational_open

Allowed:
- Deep technical explanations
- Vulnerability analysis (theoretical)
- Threat research and postmortems
- Historical exploit discussions

Still restricted:
- Live attack execution
- Malware deployment
- Non-public data access
- Irreversible destructive actions

---

## Enforcement Points

Policy is checked at:
- Query intake
- Seed generation
- Fetch execution
- Result synthesis
- Visualization output

### Semantic Search & Embeddings Policy

Semantic search and embedding usage are governed by the separate integration contract in `SEMANTIC_SEARCH.md` (Design locked v1). Key enforcement points:

- **Embeddings are navigation aids only**: they may never create relationships or imply trust.
- **Embedding containment**: vector data must be stored in bucket-scoped tables (e.g., `document_embeddings`) with no cross-table JOINs allowed.
- **AI usage**: AI components receive verified facts only, with citations and confidence; AI must not be fed raw vector results.
- **Verification**: any candidate surfaced by embeddings must be verified (evidence + explicit edge) before it can be treated as a relationship.

Violations of these rules are considered critical and should be treated as policy breaches; they are logged to `policy_denials.jsonl` with a distinct tag `semantic_search` for auditing.

---

## Disclaimers

Educational mode displays:
> "This environment is provided for educational and research purposes only. Use knowledge responsibly and ethically."

---

## Rationale & Implementation Notes

This document captures intended behaviors, but the canonical enforcement is the code in `probe.policy.*`. We follow a structure-first approach: add stubs, update architecture, then implement enforcement.

Operational notes:

- **Admin opt-in for additional behaviors:** `educational_open` is permissive by default for domain allow checks (selecting this mode allows broader fetching by default). The `admin_enabled` flag remains relevant for gating additional operational relaxations (for example, showing hidden edges in visualizations or enabling admin-only features). Toggle via CLI (`probe config set-admin enable`) or via `probe.config.json` (`"admin_enabled": true`).

- **Decision payload & logging:** Policy decisions are returned as lightweight decision payloads, e.g. `{ "mode": "educational_open", "allowed": false, "reason": "domain 'x' disallowed", "tags": ["domain"] }`. Denied decisions are logged at WARNING level with context (mode, domain, reason) to facilitate operational review and auditing.

- **Follow-up work:** Add configurable deny/allow lists, persistent telemetry for denied decisions, and per-mode tuning rules. Follow-up PRs will implement configuration plumbing and richer enforcement semantics.

---

## Policy roadmap (short-term)

- v0.4 — Gap Detection (status: done)
  - [x] GapDetector: identify missing document types and candidate domains
  - [x] SeedGenerator: produce candidate seeds from gap signals
  - [x] Investigator: consult `PolicyEngine` and enforce domain denylist during seed fetch
  - [x] Tests & docs: unit tests for policy enforcement and CLI docs

- v0.5 — Investigation Loop (status: in progress)
  - [ ] Orchestrator → Map ingest: persist pages/documents found during investigation
  - [ ] CLI `probe investigate` end-to-end: run, score, ingest, and report
  - [ ] Automatic telemetry uploader: rotate denial logs and optionally upload to S3 (tests + mock S3)
  - [ ] Operational docs: admin opt-in flow, telemetry retention, and auditing guidance

- v0.6 — Embeddings (status: planned)
  - [ ] Add optional embeddings pipeline for semantic search and seed augmentation
  - [ ] Tests and docs for embedding-based seed generation

- v1.0 — Production readiness
  - [ ] Full test coverage, resilient crawl resume, performance benchmarks, packaging and release notes

### Notes & operational guidance

- Admin opt-in (`admin_enabled`): selecting `Mode.educational_open` is permissive by default for domain checks, but `admin_enabled` remains relevant for enabling other administrative relaxations (e.g., visualizations that reveal hidden edges, or operational features that should only be used with explicit operator consent).

- Telemetry & auditing: policy denials are recorded to a JSONL telemetry file (e.g., `policy_denials.jsonl`) with timestamps, mode, reason, and context. We plan to add a rotating-file uploader that can optionally push telemetry to S3; the uploader should be configurable and support dry-run/test modes. Ensure telemetry is auditable and redact sensitive fields before uploading.

---

## FAQ
- Q: Can `educational_open` perform automated fetches against any domain?
  - A: No. Even in educational mode, non-consensual or high-risk actions are restricted and require explicit operator approval.
