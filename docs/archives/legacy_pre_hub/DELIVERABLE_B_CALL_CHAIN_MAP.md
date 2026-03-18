# Deliverable B — Call-chain map (week-view schedule)

**Route:** `/planning/calendar?year=2026&week=5&tab=week-view`

---

## 1. Backend endpoint(s) the week-view calls

| Endpoint | File | Function | Returns |
|----------|------|----------|---------|
| `GET /planning/api/calendar/schedule/<year>/<week_number>` | `blueprints/planning.py` | `api_calendar_schedule(year, week_number)` → delegates to `schedule_api_func` | `{ success, year, week_number, schedule[], selected_theme_id }` |
| (implementation) | `blueprints/planning_api_calendar_schedule.py` | `api_calendar_schedule(year, week_number)` | Builds `schedule` array from theme, recipe, profiles, weekly_word/phrase/insult, **products**, **messages**, **role_posts** |

---

## 2. Per-endpoint: where products, messages, language, depth_long come from

**File:** `blueprints/planning_api_calendar_schedule.py`

| Data | Query / function | Where filtering/grouping into days happens |
|------|------------------|--------------------------------------------|
| **Products** | Direct SQL on `posting_queue`: `content_type = 'product'`, `platform = 'facebook'`, date range, **and `EXTRACT(ISODOW FROM scheduled_date) != 6`** (exclude Saturday). | Backend: SQL excludes Sat. Frontend: groups by `scheduled_date`, maps to `social-posts-row-day-${dayIndex}`. |
| **Messages** | Direct SQL on `posting_queue`: `content_type = 'message'`, `platform = 'facebook'`, date range, **and `EXTRACT(ISODOW FROM scheduled_date) = 6`** (Saturday only). | Backend: SQL restricts to Sat. Frontend: only renders if `dayIndex === 6` into `social-posts-row-day-6`. |
| **Language** (word/phrase/insult) | `resolve_item_for_week("weekly_word"|"weekly_phrase"|"weekly_insult", year, week_number, classification=...)` from `utils.calendar_resolver`. Backed by `calendar_ideas` + `calendar_category_cycles`. | Backend: one item per type per week. Frontend: **fixed slots** — Word→day 1, Phrase→day 2, Insult→day 4. |
| **depth_long** | SQL on `posting_queue`: `role IS NOT NULL`, `platform = 'facebook'`, date range. Items with `role` (e.g. `DEPTH_LONG`) included. | Backend: no day filter. Frontend: `schedule.filter(s => s.role && s.posting_queue_id)`, then `dayIndex = getISOWeekday(scheduled_date)` → `social-posts-row-day-${dayIndex}`. |

---

## 3. Frontend: day buckets and “social post row” mapping

**File:** `static/js/planning/calendar-week-view.js`

| Concern | Location | Behaviour |
|--------|----------|-----------|
| **Schedule fetch** | `loadWeek()` ~L572 | `fetchJSON(\`/planning/api/calendar/schedule/${year}/${weekNumber}\`)` → `schedule = scheduleData.schedule` |
| **Day buckets** | `ensureRowCells('social-posts-row')` ~L716 | Creates `social-posts-row-day-1` … `social-posts-row-day-7`. |
| **Word/Phrase/Insult → days** | ~L979–989 | `selectedWord` → `social-posts-row-day-1`; `selectedPhrase` → day 2; `selectedInsult` → day 4. |
| **Product → day** | ~L992–1031 | `productPosts = schedule.filter(s => s.type === 'product')`; group by `scheduled_date`; for each day, `dayIndex = getISOWeekday(dateObj)` → `social-posts-row-day-${dayIndex}`. |
| **Message → day** | ~L1034–1055 | `messagePosts = schedule.filter(s => s.type === 'message')`; only if `dayIndex === 6` → `social-posts-row-day-6`. |
| **Role posts (e.g. depth_long)** | ~L1058–1079 | `rolePosts = schedule.filter(s => s.role && s.posting_queue_id)`; `dayIndex = getISOWeekday(scheduled_date)` → `social-posts-row-day-${dayIndex}`. |
| **Item type → “social post row”** | Implicit | Anything rendered into `socialPostsCells` / `social-posts-row-day-*` is part of the Social Posts row. Type comes from the second argument to `renderItems(..., 'weekly-word'|'product'|'message'|…)`. |
| **Client-side “force role”** | `renderItems()` ~L186–231 | `primaryRole = item.role || null`; then for `weekly-word`/`phrase`/`insult`: `primaryRole = primaryRole || 'CULTURE'`; for `product`: `primaryRole = primaryRole || 'COMMERCE'`; for `message`: `primaryRole = primaryRole || 'REASSURANCE'`; for `depth_long`: `primaryRole = primaryRole || 'DEPTH_LONG'`. So **role is overwritten when item.role is null** — UI-only masking. |

---

## 4. Summary: where “force role” lives

- **File:** `static/js/planning/calendar-week-view.js`
- **Function:** logic inside `renderItems()` that builds `primaryRole` and `typeName` for the card.
- **Lines (approx):** 186–231. For types `weekly-word`/`weekly-phrase`/`weekly-insult`, `product`, `message`, `depth_long`, the code sets `primaryRole = primaryRole || 'CULTURE'|'COMMERCE'|'REASSURANCE'|'DEPTH_LONG'`, so a null `item.role` is replaced by the Matrix-implied role. That masks items that are **not** actually scheduled with that role in the DB.
