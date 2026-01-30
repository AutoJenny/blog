# Phase P1 — Locked Plan (Final)

**Date:** 2026-01-29  
**Status:** Locked. Formal Phase P1 brief to follow (acceptance criteria, non-regression rules, regeneration behaviour, DB constraints).

---

## Decisions (final)

1. **Automate all days (Sunday included)**  
   Sunday DEPTH_LONG is automated like Friday AUTHORITY_SHORT. Generation is automatic and batch-driven; editorial approval can remain manual. System must reliably pre-generate at least 8–12 weeks ahead with no human intervention for generation. No manual gaps in the Matrix.

2. **Authority-short model is the global standard**  
   Exactly one posting_queue row per (platform, slot/role, scheduled_date). Creators reuse and regenerate the same row when content is failed, empty, or placeholder. No creator inserts a second row for a slot because a failed row exists. AUTHORITY_SHORT is the reference for idempotency, failure recovery, and “one slot = one row.” Applies to every day and every role.

---

## What we are building

### Phase P1.1 — Normalise all creators

For every creator (Mon–Sun):

1. If no row exists for the slot → insert skeleton row.
2. If row exists and is valid → skip.
3. If row exists but is failed / empty / placeholder → regenerate in place (UPDATE the same row).
4. No duplicate rows per slot under any circumstance.

Sunday: new batch creator following this pattern, using existing DepthLong generator and rota.

### Phase P1.2 — Single orchestration pass

**scripts/pregenerate_matrix.py** (thin orchestrator only):

- Iterate weeks ahead (configurable horizon).
- Invoke each day’s creator in order (Mon → Sun).
- Collect outcomes (created / regenerated / skipped / failed).
- Emit coverage report.
- Exit non-zero if required slots are unfilled.

No generation logic in the orchestrator — coordinate and report only.

---

## Agreed direction (raised points)

| Slot | Regenerate-in-place behaviour |
|------|------------------------------|
| **Wednesday (message)** | Advance to **next message in rotation** and overwrite the failed row (not retry same CSV row). |
| **Saturday (product)** | **Re-pick product** from pool and UPDATE the same row (new product_id + regenerated content). |
| **Tuesday (language)** | SELECT the single Tuesday slot row; if failed/empty → UPDATE in place. Optional: partial unique index enforcing one row per Tuesday. |
| **DB enforcement** | Add partial unique indexes per slot so “one row per slot” is enforced at database level. |

---

## Locked creator surface area

| # | Script | Day | Content type |
|---|--------|-----|--------------|
| 1 | automated_culture_creator.py | Monday | culture_fact |
| 2 | automated_weekly_content_creator.py | Tuesday | weekly_word / phrase / insult |
| 3 | automated_message_post_creator.py | Wednesday | message |
| 4 | automated_heritage_creator.py | Thursday | heritage_fact |
| 5 | automated_authority_short_creator.py | Friday | authority_short |
| 6 | automated_product_post_creator.py | Saturday | product |
| 7 | automated_depth_long_creator.py | Sunday | depth_long *(new)* |
| — | pregenerate_matrix.py | — | Orchestrator only |

No other scripts should create or update Matrix slots as part of the pre-generation pass.

---

## Next step

Formal Phase P1 brief to be issued with: acceptance criteria, non-regression rules, explicit definitions for regeneration behaviour and DB constraints.
