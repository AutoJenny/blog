# W2 — Strict 7-Day Operational Model Lock

**Created:** 2026-02-25  
**Purpose:** Lock the governance panel to a strict rolling 7-day operational dashboard. No ISO week, no current_week/year in API, no seeding from governance-summary, no synthetic rows.

---

## 1. curl proof

```bash
curl -s http://localhost:5000/api/home/governance-summary | jq
```

**Required:**
- No `current_week`
- No `year`
- `scheduled_slots` only containing rows with `scheduled_date` in `[window_start, window_end]`
- Blog only if its `scheduled_date` is in window

**Sample output (2026-02-25):**

```json
{
  "automation_summary": {
    "blocked_count": 1,
    "no_post_count": 2,
    "ready_count": 0,
    "total_slots": 3
  },
  "blog_candidates": [ ... ],
  "scheduled_slots": [
    {
      "item_type": "blog",
      "scheduled_date": "2026-02-26",
      ...
    },
    {
      "item_type": "weekly_word",
      "scheduled_date": "2026-03-02",
      ...
    },
    {
      "item_type": "weekly_phrase",
      "scheduled_date": "2026-03-03",
      ...
    }
  ],
  "window_end": "2026-03-04",
  "window_start": "2026-02-25"
}
```

- `current_week` and `year` are **absent**.
- `window_start` = today, `window_end` = today + 7 days.
- All `scheduled_slots[].scheduled_date` are between `2026-02-25` and `2026-03-04`.
- Blog appears only because it has `scheduled_date` in that window.

---

## 2. SQL proof

The API uses exactly:

```sql
SELECT ...
FROM calendar_week_items cwi
...
WHERE cwi.is_active = TRUE
  AND cwi.scheduled_date IS NOT NULL
  AND cwi.scheduled_date BETWEEN %s AND %s
ORDER BY cwi.scheduled_date ASC;
```

**Equivalent direct query (replace dates with your window_start/window_end):**

```sql
SELECT item_type, scheduled_date
FROM calendar_week_items
WHERE is_active = TRUE
  AND scheduled_date IS NOT NULL
  AND scheduled_date BETWEEN '2026-02-25' AND '2026-03-04'
ORDER BY scheduled_date ASC;
```

**Expected result** must match the `scheduled_slots` from the curl response (same item_type and scheduled_date, in order). Example:

| item_type   | scheduled_date |
|------------|----------------|
| blog       | 2026-02-26     |
| weekly_word | 2026-03-02    |
| weekly_phrase | 2026-03-03  |

Run this query in your PostgreSQL client; the rows must match the API’s `scheduled_slots`.

---

## 3. Screenshot path

**Path:** `reports/screenshots/W2_STRICT_7_DAY_MODEL_LOCK.png`

Governance panel showing:
- Window header: “Next 7 days (25 Feb – 4 Mar)” (no week numbers)
- Table rows strictly matching the date window
- No synthetic rows
- Empty state row when there are no slots: “No scheduled content in the next 7 days.”

---

## Implementation summary

| Item | Done |
|------|------|
| **C1** Backend: window_start = today, window_end = today+7; single query with `scheduled_date BETWEEN`; no `current_week`/`year`; no `_ensure_weekly_content_seeded_for_week` | ✓ |
| **C2** Removed theme fallback that set `scheduled_date` from ISO week; blog only if in window | ✓ |
| **C3** Window header from server `window_start`/`window_end` only; no week numbers | ✓ |
| **C4** Empty state: one table row “No scheduled content in the next 7 days.” when `scheduled_slots` is empty | ✓ |
| Diagnostics removed from UI (strip, debug row, console logs, force refresh) | ✓ |

No seeding changes, no idea/selection logic changes, no candidate accordion changes. Strict rolling 7-day operational model only.
