# Governance Panel — Technical Reference

**Date:** 2026-02-23  
**Scope:** Homepage Governance modal, blog candidates, convert flow, week-item APIs

---

## Overview

The **Governance Panel** is a modal on the homepage that shows the current week’s scheduled content and **Blog Candidates** (ideas that can become the week’s blog post). It is the main place to choose which idea is “this week’s blog” and to convert an idea into a draft post.

---

## Data Source

- **Endpoint:** `GET /api/home/governance-summary`
- **Returns:** `current_year`, `current_week`, `scheduled_slots[]`, `blog_candidates[]`, and metrics (e.g. `total_slots`, `ready_count`, `no_post_count`).

### scheduled_slots

Non-idea items for the current week: `weekly_word`, `weekly_phrase`, `recipe`, `profile`, `theme`, and a synthetic **blog** row when a candidate has been converted.

- Each slot has: `role`, `item_type`, `slot_id` (week_item_id), `item_id`, `post_id` (if linked), `summary`, `scheduled_date`, `channels[]`, `stage_blocked`, etc.
- The **blog** role row is derived from the **selected** blog candidate that has `metadata.post_id` (i.e. has been converted). It does not create a separate `calendar_week_items` theme row; the same idea week-item is shown in both the candidates list and as the blog slot.

### blog_candidates

Active, non-system **idea** week items for the current week.

- **Source:** `calendar_week_items` where `item_type = 'idea'`, `year`/`week_number` = current, `is_active = TRUE`, and `(metadata->>'system') IS DISTINCT FROM 'true'`.
- Each candidate has: `week_item_id`, `item_id`, `title`, `summary`, `is_primary`, `is_selected`, `metadata` (e.g. `converted`, `post_id`), `is_active`.
- **Single selection:** Only one candidate per week should have `is_selected = TRUE`; the UI uses this for “active” blog candidate and for surfacing the blog row in `scheduled_slots` when converted.

---

## APIs Used by the Panel

| Action | Method / Endpoint | Payload / behaviour |
|--------|-------------------|----------------------|
| Load panel | `GET /api/home/governance-summary` | — |
| Set selected candidate | `PATCH /planning/api/calendar/week-items/<week_item_id>` | `{ "is_selected": true }` — backend clears `is_selected` on other ideas for that week, then sets it on this row. |
| Convert idea to post | `POST /launchpad/one-click-publication/api/create-post-from-item` | `{ "category": "idea", "item_id": <idea_id>, "week_item_id": <week_item_id>, "year", "week" }` |
| Persist conversion linkage | `PATCH /planning/api/calendar/week-items/<week_item_id>` | `{ "metadata": { "converted": true, "post_id": <post_id> }, "is_selected": true, "is_active": true }` |
| Delete (deactivate) candidate | `PATCH /planning/api/calendar/week-items/<week_item_id>` | `{ "is_active": false }` |
| New idea | `POST /planning/api/calendar/ideas` | `{ "title", "summary", "year", "week_number" }` — creates `calendar_ideas` + `calendar_week_items` (idea). |
| Edit / Move | `PATCH /planning/api/calendar/week-items/<week_item_id>` or ideas API | Edit: idea title/summary; Move: `year`, `week_number`, `scheduled_date`. |

---

## Convert Flow (Idea → Blog Post)

1. User selects a candidate (radio) → frontend calls `PATCH .../week-items/<id>` with `is_selected: true`.
2. User clicks **Start Blog Post** → frontend calls `POST .../create-post-from-item` with `category: "idea"`, `item_id`, `week_item_id`, `year`, `week`.
3. Backend creates a draft post (or reuses an existing calendar-seeded post), sets `calendar_seed` on the post, and **does not** insert a new `calendar_week_items` theme row; the idea row remains and is updated by the client.
4. On success, frontend calls `PATCH .../week-items/<week_item_id>` with `metadata: { converted: true, post_id }`, `is_selected: true`, `is_active: true`.
5. Governance summary then shows that candidate as converted and surfaces the **blog** row in `scheduled_slots` with the same post.

---

## UI Behaviour (Frontend)

- **Scheduled table:** Renders all `scheduled_slots` (including role **blog**). Blog row links to `/planning/posts/<post_id>/calendar`.
- **Blog Candidates:** Radio list; `checked` state from `candidate.is_selected`. Active tag when `is_selected`. For converted candidates (`metadata.converted` and `post_id`): show **Open Post**, Edit, Move, Delete (disabled). For unconverted: **Start Blog Post**, Edit, Move, Delete.
- **+ New Idea:** Opens modal; on submit, `POST /planning/api/calendar/ideas` then refresh.

---

## Related

- **Backend:** `blueprints/core.py` (`api_home_governance_summary`), `blueprints/automation_core.py` (`create_post_from_item`), `blueprints/planning_api_calendar_schedule.py` (PATCH week-items, POST ideas).
- **Frontend:** `static/js/home_governance.js`.
- **Calendar seed:** `docs/workflow/calendar_seed_model.md`. Idea conversion sets `calendar_seed` on the post; linkage to the week is kept in the idea `calendar_week_items` row via `metadata.post_id`.
