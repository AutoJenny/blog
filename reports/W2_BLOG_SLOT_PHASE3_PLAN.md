# W2 Blog Slot Phase 3 — Make Blog a First-Class Weekly Slot

## Current behaviour summary

- **Synthetic blog row:** The governance summary does not read a `calendar_week_items` row with `item_type = 'blog'`. Instead it derives a "Blog" row from the idea candidates: if there is a candidate with `is_selected = true` and `metadata.post_id` set, that candidate is appended to `scheduled_slots` as a synthetic row with `role: "blog"`, `item_type: "idea"`, and `scheduled_date: null`.
- **Location:** `blueprints/core.py` — block that builds `active_blog` from `blog_candidates` and appends it to `scheduled_slots`.
- **Convert flow:** "Start Blog Post" calls `create_post_from_item` (idea); the backend creates or reuses a post and the client PATCHes the **idea** week item with `metadata.converted`, `metadata.post_id`, and `is_selected`. The idea row is sometimes deactivated. No dedicated blog slot row exists.

## Target behaviour summary

- **Real blog slot:** One row per week in `calendar_week_items` with `item_type = 'blog'`, `item_id = 0`, and `scheduled_date` = Thursday of that ISO week. Seeded/backfilled in the same place as `weekly_word` / `weekly_phrase` (e.g. `_ensure_weekly_content_seeded_for_week` and equivalent backfill).
- **Governance summary:** No injection of a row from candidates. `scheduled_slots` includes the real blog slot when its `scheduled_date` falls in the next-7-days window. Summary text: from `metadata.post_id` (post title) if set, else from `metadata.idea_item_id` (idea title), else "—".
- **Convert flow:** On "Start Blog Post", after creating/reusing the post, update the **blog slot** row for that week: `metadata.converted = true`, `metadata.post_id = <post_id>`, `metadata.idea_item_id = <idea item_id>`. The idea candidate row is unchanged for `is_active` (no reliance on deactivation for correctness).

---

## A2. Snapshot current state

### git status

```
On branch main
Your branch is ahead of 'origin/refactor/authoring-modularization' by 4 commits.
Changes not staged for commit:
	modified:   logs/launchd_monitor.err
	modified:   logs/launchd_posting.err
Untracked files:
	package-lock.json
	package.json
	utils/publishing/
```

### git log -5 --oneline

```
f897641f W2: ensure seeded weekly items get scheduled_date; homepage next-7-days shows week content
95545d56 W2: fix governance modal backdrop and ensure modal readability
ccf9ba97 W2: homepage governance fully date-driven; remove week references; blog independent of date window
ccd3fcc0 W2: homepage governance shows next 7 days; hide blog candidates in accordion; add calendar link
b42da168 Docs & KB: Governance panel, blog candidates, convert flow; sync tech and user docs
```

### curl governance-summary (scheduled_slots + blog_candidates)

```json
{
  "window_start": "2026-02-25",
  "window_end": "2026-03-04",
  "scheduled_slots": [
    {
      "role": "weekly_word",
      "item_type": "weekly_word",
      "slot_id": 423,
      "scheduled_date": "2026-03-02",
      "post_id": null,
      "summary": "wheesht"
    },
    {
      "role": "weekly_phrase",
      "item_type": "weekly_phrase",
      "slot_id": 490,
      "scheduled_date": "2026-03-03",
      "post_id": null,
      "summary": "Pure dead brilliant"
    },
    {
      "role": "blog",
      "item_type": "idea",
      "slot_id": 499,
      "scheduled_date": null,
      "post_id": 728,
      "summary": "Irish tartans"
    }
  ],
  "blog_candidates": [
    {
      "week_item_id": 315,
      "item_id": 61,
      "title": "Celtic Jewellery Guide",
      "is_selected": false,
      "is_primary": false,
      "is_active": true,
      "metadata": {},
      "post_id": null
    },
    ...
    {
      "week_item_id": 499,
      "item_id": 1398,
      "title": "Irish tartans",
      "is_selected": true,
      "is_primary": false,
      "is_active": true,
      "metadata": { "converted": true, "post_id": 728 },
      "post_id": 728
    }
  ]
}
```

### psql calendar_week_items (year 2026, weeks 9 and 10)

```
 id  |   item_type   | item_id | year | week_number | scheduled_date | is_active | is_selected | is_primary | metadata
-----+---------------+---------+------+-------------+----------------+-----------+-------------+------------+-------------------------------------
 315 | idea          |      61 | 2026 |           9 |                | t         | f           | f          | {"test_key": "test_value"}
 335 | idea          |      63 | 2026 |           9 |                | t         | f           | f          | {}
 ...
 499 | idea          |    1398 | 2026 |           9 | 2026-02-26     | t         | t           | f          | {"post_id": 728, "converted": true}
 ...
 423 | weekly_word   |    1097 | 2026 |          10 | 2026-03-02     | t         | f           | f          | {}
 490 | weekly_phrase |    1195 | 2026 |          10 | 2026-03-03     | t         | f           | f          | {}
(13 rows total; no item_type = 'blog')
```
