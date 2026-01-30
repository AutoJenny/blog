# Phase P1: Confirmation and Final Creator List

**Date:** 2026-01-29  
**Purpose:** Reply to locked decisions and immediate questions before the formal Phase P1 brief.

---

## 1. Confirmation of the two locked decisions

**Decision 1 — Automate Sunday like Friday**  
Confirmed. Sunday DEPTH_LONG will be batch-generated in advance (new creator script), same pattern as Friday AUTHORITY_SHORT. Editorial approval can stay manual; generation is automatic. The system will be able to pre-generate 8–12 weeks ahead with no human intervention for generation.

**Decision 2 — Adopt the AUTHORITY_SHORT model everywhere**  
Confirmed. We will standardise on:

- **Exactly one posting_queue row per (platform, role/slot, scheduled_date)** [see slot definition per day below].
- Creators **reuse and regenerate the same row** when content is failed, empty, or placeholder.
- **No creator creates a second row** for the same slot because a failed row exists.
- AUTHORITY_SHORT is the reference implementation for idempotency, failure recovery, and “one slot = one row.”

No objections; ready to implement once the formal brief and acceptance criteria are issued.

---

## 2. Blockers and concerns (refactor to authority_short pattern)

No hard blockers. A few design choices and one recommendation:

### 2.1 Design choices to fix in the brief

- **Wednesday (message)**  
  “Regenerate in place” can mean: (a) **retry same message** (same CSV row), or (b) **advance to next message** in rotation and overwrite the slot. Current behaviour is “next message by index.” Recommend defining in the brief: e.g. “regenerate = fill with next message in rotation (overwrite failed row content).”

- **Saturday (product)**  
  “Regenerate in place” can mean: (a) **re-run workflow for same product_id** (caption/image generation again), or (b) **pick a new product** for the slot and UPDATE the row (new product_id, regenerate content). Recommend defining in the brief: e.g. “regenerate = same slot, re-pick product from pool and UPDATE row (product_id + content).”

### 2.2 Tuesday (weekly_word / weekly_phrase / weekly_insult)

- Current DB: unique index on `(platform, content_type, idea_id, scheduled_date)` for language types — prevents duplicate (platform, content_type, idea_id, date) but **not** “one row per Tuesday” (different content_type/idea_id could theoretically exist for same date).
- Refactor: for each Tuesday, **SELECT** the single row for that (platform, scheduled_date) with content_type IN (weekly_word, weekly_phrase, weekly_insult). If none → INSERT; if exists and valid → skip; if exists and failed/empty → **UPDATE** in place (same or new idea_id within the week’s content_type; content_type for the week is fixed by (week_number - 1) % 3). No need to change content_type when regenerating; only idea_id and generated_content can change.
- Optional: add a partial unique on `(platform, scheduled_date)` WHERE content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult') so the DB enforces “one row per Tuesday” regardless of code paths.

### 2.3 DB enforcement of “one row per slot”

- Today only **Tuesday** has a partial unique on posting_queue for Matrix slots (and it’s per (platform, content_type, idea_id, scheduled_date), not per (platform, scheduled_date)).
- **Recommendation:** In P1 (or a follow-on migration), add partial unique indexes so “one row per slot” is enforced at DB level for all Matrix slots. That makes duplicate inserts impossible and keeps behaviour consistent even if multiple scripts or runs touch the same slot. Suggested slot keys (to be confirmed in brief):
  - Monday: `(platform, content_type, scheduled_date)` WHERE content_type = 'culture_fact'
  - Tuesday: `(platform, scheduled_date)` WHERE content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
  - Wednesday: `(platform, content_type, scheduled_date)` WHERE content_type = 'message'
  - Thursday: `(platform, role, scheduled_date)` WHERE role = 'HERITAGE'
  - Friday: `(platform, role, scheduled_date)` WHERE role = 'AUTHORITY_SHORT'
  - Saturday: `(platform, content_type, scheduled_date, scheduled_time)` WHERE content_type = 'product'
  - Sunday: `(platform, content_type, scheduled_date)` WHERE content_type = 'depth_long'

### 2.4 Sunday (new depth_long creator)

- No technical blocker. Pattern: same as authority_short — for each Sunday in horizon, SELECT existing row for (platform, content_type='depth_long', scheduled_date); if none → INSERT skeleton; if valid → skip; if failed/empty/placeholder → call existing DepthLongGenerator (rota for that week via kb_topic_rota), then UPDATE row. Reuse `utils/content_roles/depth_long_generator.py` and rota resolution; no new generation logic.

---

## 3. Final list of creator scripts (after refactor)

After Phase P1.1 (normalise all creators) and P1.2 (orchestration), the **surface area** of Matrix pre-generation will be:

| # | Script | Day | Slot / role | Content type | Source |
|---|--------|-----|-------------|--------------|--------|
| 1 | `scripts/automated_culture_creator.py` | Monday | CULTURE | culture_fact | culture_library |
| 2 | `scripts/automated_weekly_content_creator.py` | Tuesday | CULTURE (language) | weekly_word / weekly_phrase / weekly_insult | calendar_ideas (rotating) |
| 3 | `scripts/automated_message_post_creator.py` | Wednesday | REASSURANCE | message | data/facebook_messages.csv |
| 4 | `scripts/automated_heritage_creator.py` | Thursday | HERITAGE | heritage_fact | heritage_library |
| 5 | `scripts/automated_authority_short_creator.py` | Friday | AUTHORITY_SHORT | authority_short | KB rota / fallback |
| 6 | `scripts/automated_product_post_creator.py` | Saturday | COMMERCE | product | daily_posts_schedule + clan_products |
| 7 | `scripts/automated_depth_long_creator.py` | Sunday | DEPTH_LONG | depth_long | KB rota + DepthLongGenerator *(new)* |

**Orchestrator (no generation logic):**

| # | Script | Responsibility |
|---|--------|----------------|
| 8 | `scripts/pregenerate_matrix.py` | Iterate weeks ahead; invoke creators 1–7 in order; collect outcomes; emit coverage report; exit non-zero if required slots unfilled |

**Total: 7 creators + 1 orchestrator.**  

No other scripts should create or update Matrix slots for the pre-generation pass; the Content Roles API will remain for on-demand Sunday generation (e.g. editorial override) but the **batch** path is the new Sunday creator plus the orchestrator.

---

## 4. Summary

- **Decisions:** Both confirmed (automate Sunday; one row per slot, reuse/regenerate in place).
- **Blockers:** None. Clarify in brief: message “regenerate” = same slot, next message in rotation; product “regenerate” = same slot, re-pick product and UPDATE. Optional: partial unique indexes per slot for DB enforcement.
- **Creator list:** 7 scripts (Mon–Sun), plus `pregenerate_matrix.py` as the only orchestrator. This is the locked surface area for Phase P1.

Ready for the formal Phase P1 brief with acceptance criteria and non-regression rules.
