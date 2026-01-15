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

---

## Disclaimers

Educational mode displays:
> "This environment is provided for educational and research purposes only. Use knowledge responsibly and ethically."

---

## Rationale & Implementation Notes

This doc captures intended behaviors, but the canonical enforcement is the code in `probe.policy.*`. We follow a structure-first approach: add stubs, update architecture, then implement enforcement.

---

## FAQ
- Q: Can `educational_open` perform automated fetches against any domain?
  - A: No. Even in educational mode, non-consensual or high-risk actions are restricted and require explicit operator approval.
