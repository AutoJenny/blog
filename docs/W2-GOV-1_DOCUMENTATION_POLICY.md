# W2-GOV-1 — Mandatory Documentation & Knowledge Base Updates

**Date:** 2026-02-23  
**Status:** Active policy

---

## Objective

Ensure technical documentation and user-facing Knowledge Base remain aligned with system changes after each major phase (e.g., W2-FIX-5, W2-FIX-6, W2-DESIGN-*, etc.).

---

## Policy

After completion of any major phase (W2-FIX-* or W2-DESIGN-* implementation), you **must**:

### A. Update technical documentation under `/docs/`

- Architecture docs (lifecycle, workflow, status model)
- API contracts
- Publishing contract
- Section model
- Workflow stage model
- Status transition rules

### B. Update user-facing Knowledge Base (if relevant to feature changes)

- `docs/kb/` — Authoring workflow guides
- "How to publish a post"
- Status meanings
- Stage meanings
- Override behaviour (admin only)

---

## Documentation updates must include

- Clear description of new behaviour
- Updated diagrams (text diagrams acceptable)
- Route and endpoint changes
- Field contract changes
- Any removed/deprecated behaviour

---

## Implementation report requirement

Provide a short **"Documentation Update Summary"** in the implementation report:

- Files updated
- What changed
- Any deprecated docs moved or archived

---

## Deferred documentation

If documentation is **intentionally deferred**, explicitly state:

> **Docs deferred — reason:** *[reason]*

Silence is not acceptable.

---

## Applies to

- All future major structural phases (W2-FIX-*, W2-DESIGN-*, etc.)
- Implemented retroactively for W2-FIX-5 and W2-FIX-6 (2026-02-23)
