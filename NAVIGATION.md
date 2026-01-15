# NAVIGATION.md

This document defines the **Groups → Tabs → Categories** information architecture used across Chat, CLI, MCP, and future UI layers.

## Groups (Top-Level Domains)

Groups answer **why** the user is researching something.

1. **OSINT** – Open-source intelligence & public information
2. **News & Media** – Journalism, events, narratives
3. **Cybersecurity & Threat Research** – Defensive security research
4. **Markets & Companies** – Qualitative market & company intelligence
5. **Technology & Development** – Software, standards, documentation
6. **Meta / System** – Probe internals, policy, diagnostics

## Tabs (Intent Layer)

Tabs answer **what the user wants to do**.

The same tabs exist across all groups:

- **Discover** – Find new sources, documents, entities
- **Investigate** – Deep dives, gap detection, evidence gathering
- **Analyze** – Patterns, trends, correlations
- **Monitor** – Ongoing tracking and alerts
- **Visualize** – Graphs, timelines, relationships
- **Explain** – Educational and conceptual explanations

## Categories (Data Types)

Categories answer **what kind of information** is involved.

### OSINT
- Reports & whitepapers
- Archived pages
- Forums & discussions
- Entity mentions
- Source credibility
- Timelines

### News & Media
- Breaking news
- Regional coverage
- Opinion & analysis
- Fact-checking sources
- Media bias indicators

### Cybersecurity & Threat Research
- CVEs & advisories
- Incident reports
- Threat actor profiles
- Attack-chain analysis (theoretical)
- Mitigations & defenses

### Markets & Companies
- Filings & disclosures
- Earnings reports
- Corporate structure
- Product mentions
- Qualitative risk signals

### Technology & Development
- Documentation & manuals
- RFCs & standards
- Open-source repositories
- Design discussions
- Deprecations & changelogs

### Meta / System
- Policies & modes
- Scoring weights
- Crawl diagnostics
- Visualization settings

## Modes & Visibility

Modes **filter categories**, not groups or tabs.

| Mode | Behavior |
|-----|---------|
| `public_guarded` | High-risk categories hidden or summarized |
| `educational_open` | Full category visibility with warnings (requires explicit admin opt-in to be permissive) |

Note: `educational_open` is *opt-in* — operators must enable `admin_enabled` (via `probe.config.json` or `probe config set-admin enable`) to unlock relaxed behaviors. If not enabled, `educational_open` is treated as `public_guarded` for enforcement and visibility rules.
## CLI Mapping (Example)

```bash
probe osint discover "entity name"
probe cyber investigate "CVE-2024-XXXX"
probe markets analyze "company name"
probe tech explain "protocol name"
```

## MCP Mapping (Example Context)

```json
{
  "group": "cybersecurity",
  "tab": "investigate",
  "category": "attack_chain",
  "mode": "educational_open"
}
```

## Design Rules
- Groups do not encode policy
- Tabs do not encode risk
- Categories may be restricted by mode
- Policy decisions are centralized
