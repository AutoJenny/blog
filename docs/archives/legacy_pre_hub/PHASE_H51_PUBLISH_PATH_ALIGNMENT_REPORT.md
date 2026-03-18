# Phase H-5.1 — Publish Path Alignment (Report)

**Phase:** H-5.1  
**Title:** Publish Path Alignment (Backend wiring only)  
**Date:** 2026-03-01  
**Preconditions:** Phase H-0 through H-5 complete and merged.

---

## 1. Problem resolved

After H-5, the system could determine which run is current for `(content_ref, platform, channel_type, slot)`, but publish-time consumers could still assume “latest generated”, “most recent posting_queue row”, or “whatever the queue view shows”. This phase removes that ambiguity.

After H-5.1:

- Posting, scheduling, and queue execution **must** publish the run referenced by `workbench_current_outputs`, or **fail explicitly** if none is set.
- No silent fallback.

---

## 2. Authoritative source of publishable output

Canonical resolution path (fixed, not reinterpreted):

```
(content_ref, platform, channel_type, slot_identifier)
        ↓
workbench_current_outputs.run_id
        ↓
generation_runs.output_refs.posting_queue_id
        ↓
posting_queue row used for publish
```

If any link is missing, the action must not publish.

---

## 3. Backend changes implemented

### 3.1 Central resolver (mandatory)

**Location:** `blueprints/launchpad_utils.py`

**Function:** `resolve_current_posting_queue_id(content_ref, platform, channel_type, slot_identifier='primary') -> posting_queue_id | None`

**Behaviour:**

1. Query `workbench_current_outputs` for the row.
2. If no row → return `None`.
3. Fetch `generation_runs` by `run_id`.
4. Extract `output_refs.posting_queue_id` (JSONB).
5. Validate that the `posting_queue` row exists and matches `platform` / `channel_type`.
6. Return `posting_queue_id`.

No fallback logic. No guessing.

---

### 3.2 post_now alignment

**Updated:** `blueprints/launchpad_old.py`, `blueprints/launchpad_scheduling.py`, `blueprints/launchpad/blog_post_syndication.py`.

**Behaviour:**

1. **Workbench path:** Request body may include `content_ref`, `platform`, `channel_type`. Resolver is called; if it returns `None`, respond with **400** and error code `NO_CURRENT_OUTPUT`; otherwise publish the resolved `posting_queue_id`.
2. **Item path:** Request body includes `item_id`. Load the queue row; if `content_type == 'blog_post'` and `post_id` is set, call resolver for `(post_id, platform, channel_type)`. If resolver returns `None`, respond **400** with `NO_CURRENT_OUTPUT`. If resolver returns a different id than `item_id`, respond **400** (“Selected item is not the current output”). Otherwise publish `item_id`.
3. Non–blog_post items (e.g. product) are unchanged: no resolver, publish the given `item_id`.

No auto-selection. No “latest”.

**Error shape (recommended):**

```json
{
  "success": false,
  "error": "NO_CURRENT_OUTPUT",
  "message": "No current output selected for this item. Select an output in the workbench before publishing."
}
```

---

### 3.3 Schedule execution alignment

**Updated:** `scripts/scheduled_posting_executor.py`.

- **get_due_posts:** `post_id` added to the SELECT so blog_post rows have a content reference.
- **Validation loop (Phase H-5.1):** For each candidate post, if `content_type == 'blog_post'` and `post_id` is not None:
  1. Call `resolve_current_posting_queue_id(post_id, platform, channel_type, 'primary')`.
  2. If `None`: log “no current output set”, **skip** (do not publish).
  3. If resolved id ≠ post `id`: log “queue row is not the current output”, **skip**.
  4. Otherwise proceed to publish.

Scheduling therefore respects explicit workbench current output; engine comparisons cannot accidentally publish the wrong output.

---

### 3.4 schedule_tomorrow alignment

**Updated:** `blueprints/launchpad_scheduling.py` — `schedule_tomorrow()`.

Same resolver rules as post_now: for blog_post, only the resolved current output is allowed; otherwise **400** with `NO_CURRENT_OUTPUT` or “Selected item is not the current output”.

---

### 3.5 Queue display (backend)

**No change.** The queue API (e.g. GET `/launchpad/api/queue`) continues to return queue rows as before. “Current” is not inferred from ordering; it is a property of workbench state. The queue may contain multiple rows for the same `content_ref`; only the one resolved via `workbench_current_outputs` is publishable for blog_post.

---

## 4. Error semantics

Publishing without a current output is a **hard error**, not a silent fallback.

- **400** with `error: "NO_CURRENT_OUTPUT"` and the specified message when no current output is set.
- **400** with the same code when the client sends an `item_id` that is not the current output for that blog_post.

This prevents accidental publication of the wrong engine output.

---

## 5. What was not done

- No UI warnings added.
- No auto-selection of the newest run.
- No mutation of `generation_runs`.
- No slot complexity beyond `"primary"`.
- No carousel logic changes.
- No “helpful” fallback to old behaviour.

---

## 6. Acceptance criteria (sign-off checklist)

| Criterion | Status |
|-----------|--------|
| post_now publishes only the run marked current (blog_post) | ✓ Resolver used in launchpad_old, launchpad_scheduling, blog_post_syndication |
| Scheduling publishes only the run marked current (blog_post) | ✓ Executor skips when no current output or when row ≠ resolved id |
| If no current output exists, publishing fails explicitly | ✓ 400 NO_CURRENT_OUTPUT |
| No generator code modified | ✓ |
| No UI code modified | ✓ |
| FB and IG both route through the same resolver | ✓ Single resolver; platform/channel_type from request or queue row |
| Behaviour is deterministic and auditable | ✓ Single function, no fallback |

---

## 7. Stop statement (verbatim)

**Phase H-5.1 aligned publishing and scheduling paths with explicit workbench current-output selection. All publish actions now resolve deterministically through workbench_current_outputs. No UI, generator, carousel, or prompt logic was modified.**
