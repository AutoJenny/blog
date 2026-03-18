# W2 UI — Branch B: Null guards + deterministic render proof

**Created:** 2026-02-25  
**Purpose:** Prove whether the UI renders 0 slots (exception), filters/sorts incorrectly, or has DOM overwrite/double render. No backend or seeding changes.

---

## 1. Screenshot

**Path (actual file saved):**

```
/Users/autojenny/Documents/projects/blog/reports/screenshots/W2_UI_RENDER_BRANCH_B_RESULTS.png
```

Shows the Governance panel with:
- **Diagnostics strip** (Build, Fetched, Payload hash, Rendered slots, Render error, Force refresh)
- **Table rows** (all slots from API in raw order)
- **DEBUG ROW COUNT** row at bottom of table (orange text)

*(PNG, 1280×720, captured via Playwright on same page load as payload below.)*

---

## 2. Console output

**Same page-load / same “Fetched” timestamp — runtime payload from backend:**

### [GOV][PAYLOAD RAW]

```
{"automation_summary": {"blocked_count": 1, "no_post_count": 2, "ready_count": 0, "total_slots": 3}, "blog_candidates": [{"is_active": true, "is_primary": false, "is_selected": false, "item_id": 61, "metadata": {"test_key": "test_value"}, "post_id": null, "summary": "Traditional Celtic jewellery and its meanings", "title": "Celtic Jewellery Guide", "week_item_id": 315}, {"is_active": true, "is_primary": false, "is_selected": false, "item_id": 63, "metadata": {}, "post_id": null, "summary": "Welsh traditions, daffodils, and St David's Day celebrations", "title": "St David's Day (Wales)", "week_item_id": 335}, {"is_active": true, "is_primary": false, "is_selected": true, "item_id": 1398, "metadata": {"converted": true, "post_id": 728}, "post_id": 728, "summary": "The tradition of Irish tartans, and how they differ from the traditions of Scottish tartans", "title": "Irish tartans", "week_item_id": 499}], "current_week": 9, "scheduled_slots": [{"automation_blocked_reason": "stage_blocked", "automation_enabled": true, "channels": [{"channel": "blog", "content_format": "article", "is_primary": true, "is_required": true}], "created_at": "2026-02-25T13:54:10.633463Z", "is_provisional": false, "item_id": 0, "item_type": "blog", "metadata": {"converted": true, "idea_item_id": 1398, "idea_week_item_id": 499, "post_id": 729}, "output_ready": null, "post_id": 729, "post_status": null, "preflight_ok": null, "role": "blog", "scheduled_date": "2026-02-26", "slot_id": 503, "summary": "Irish tartans", "updated_at": "2026-02-25T16:57:07.099085Z", "weekday": null, "workflow_stage": "idea"}, {"automation_blocked_reason": null, "automation_enabled": null, "channels": [{"channel": "facebook", "content_format": "word_of_day", "is_primary": true, "is_required": true}, {"channel": "instagram", "content_format": "word_of_day", "is_primary": false, "is_required": true}], "created_at": "2026-02-24T14:25:28.135969Z", "is_provisional": true, "item_id": 1097, "item_type": "weekly_word", "metadata": {}, "output_ready": null, "post_id": null, "post_status": null, "preflight_ok": null, "role": "weekly_word", "scheduled_date": "2026-03-02", "slot_id": 423, "summary": "wheesht", "updated_at": "2026-02-25T13:17:09.242278Z", "weekday": null, "workflow_stage": null}, {"automation_blocked_reason": null, "automation_enabled": null, "channels": [{"channel": "facebook", "content_format": "phrase_of_day", "is_primary": true, "is_required": true}], "created_at": "2026-02-24T14:25:28.135969Z", "is_provisional": true, "item_id": 1195, "item_type": "weekly_phrase", "metadata": {}, "output_ready": null, "post_id": null, "post_status": null, "preflight_ok": null, "role": "weekly_phrase", "scheduled_date": "2026-03-03", "slot_id": 490, "summary": "Pure dead brilliant", "updated_at": "2026-02-25T13:17:09.242278Z", "weekday": null, "workflow_stage": null}], "window_end": "2026-03-04", "window_start": "2026-02-25", "year": 2026}
```

### [GOV][SLOTS]

```json
[
  {"automation_blocked_reason": "stage_blocked", "automation_enabled": true, "channels": [{"channel": "blog", "content_format": "article", "is_primary": true, "is_required": true}], "created_at": "2026-02-25T13:54:10.633463Z", "is_provisional": false, "item_id": 0, "item_type": "blog", "metadata": {"converted": true, "idea_item_id": 1398, "idea_week_item_id": 499, "post_id": 729}, "output_ready": null, "post_id": 729, "post_status": null, "preflight_ok": null, "role": "blog", "scheduled_date": "2026-02-26", "slot_id": 503, "summary": "Irish tartans", "updated_at": "2026-02-25T16:57:07.099085Z", "weekday": null, "workflow_stage": "idea"},
  {"automation_blocked_reason": null, "automation_enabled": null, "channels": [{"channel": "facebook", "content_format": "word_of_day", "is_primary": true, "is_required": true}, {"channel": "instagram", "content_format": "word_of_day", "is_primary": false, "is_required": true}], "created_at": "2026-02-24T14:25:28.135969Z", "is_provisional": true, "item_id": 1097, "item_type": "weekly_word", "metadata": {}, "output_ready": null, "post_id": null, "post_status": null, "preflight_ok": null, "role": "weekly_word", "scheduled_date": "2026-03-02", "slot_id": 423, "summary": "wheesht", "updated_at": "2026-02-25T13:17:09.242278Z", "weekday": null, "workflow_stage": null},
  {"automation_blocked_reason": null, "automation_enabled": null, "channels": [{"channel": "facebook", "content_format": "phrase_of_day", "is_primary": true, "is_required": true}], "created_at": "2026-02-24T14:25:28.135969Z", "is_provisional": true, "item_id": 1195, "item_type": "weekly_phrase", "metadata": {}, "output_ready": null, "post_id": null, "post_status": null, "preflight_ok": null, "role": "weekly_phrase", "scheduled_date": "2026-03-03", "slot_id": 490, "summary": "Pure dead brilliant", "updated_at": "2026-02-25T13:17:09.242278Z", "weekday": null, "workflow_stage": null}
]
```

### [GOV][RENDERING SLOT] (every one)

```
[GOV][RENDERING SLOT] {"automation_blocked_reason": "stage_blocked", "automation_enabled": true, "channels": [{"channel": "blog", "content_format": "article", "is_primary": true, "is_required": true}], "created_at": "2026-02-25T13:54:10.633463Z", "is_provisional": false, "item_id": 0, "item_type": "blog", "metadata": {"converted": true, "idea_item_id": 1398, "idea_week_item_id": 499, "post_id": 729}, "output_ready": null, "post_id": 729, "post_status": null, "preflight_ok": null, "role": "blog", "scheduled_date": "2026-02-26", "slot_id": 503, "summary": "Irish tartans", "updated_at": "2026-02-25T16:57:07.099085Z", "weekday": null, "workflow_stage": "idea"}
[GOV][RENDERING SLOT] {"automation_blocked_reason": null, "automation_enabled": null, "channels": [{"channel": "facebook", "content_format": "word_of_day", "is_primary": true, "is_required": true}, {"channel": "instagram", "content_format": "word_of_day", "is_primary": false, "is_required": true}], "created_at": "2026-02-24T14:25:28.135969Z", "is_provisional": true, "item_id": 1097, "item_type": "weekly_word", "metadata": {}, "output_ready": null, "post_id": null, "post_status": null, "preflight_ok": null, "role": "weekly_word", "scheduled_date": "2026-03-02", "slot_id": 423, "summary": "wheesht", "updated_at": "2026-02-25T13:17:09.242278Z", "weekday": null, "workflow_stage": null}
[GOV][RENDERING SLOT] {"automation_blocked_reason": null, "automation_enabled": null, "channels": [{"channel": "facebook", "content_format": "phrase_of_day", "is_primary": true, "is_required": true}], "created_at": "2026-02-24T14:25:28.135969Z", "is_provisional": true, "item_id": 1195, "item_type": "weekly_phrase", "metadata": {}, "output_ready": null, "post_id": null, "post_status": null, "preflight_ok": null, "role": "weekly_phrase", "scheduled_date": "2026-03-03", "slot_id": 490, "summary": "Pure dead brilliant", "updated_at": "2026-02-25T13:17:09.242278Z", "weekday": null, "workflow_stage": null}
```

---

## 3. Rendered slots vs DEBUG ROW COUNT

**Does the diagnostics strip “Rendered slots” equal the orange “DEBUG ROW COUNT” value?**

Yes — both show 3. The payload has 3 `scheduled_slots` (blog, weekly_word, weekly_phrase); the strip’s Rendered slots and the table’s DEBUG ROW COUNT both reflect 3.

---

## Branch B implementation summary

| Item | Done |
|------|------|
| **B1** `console.log('[GOV][PAYLOAD RAW]', …)`, `[GOV][SLOTS]`, `[GOV][RENDERING SLOT]` per slot | ✓ |
| **B2** No client-side filtering — render every `data.scheduled_slots` in order; null `scheduled_date`/`summary`/channels display as — or ignored | ✓ |
| **B3** No `.sort()` on slots (none present; raw API order) | ✓ |
| **B5** Debug row appended to table: `DEBUG ROW COUNT: ${slots.length}` (colspan=9, orange) | ✓ |

Diagnostics strip unchanged. Backend and endpoints unchanged.
