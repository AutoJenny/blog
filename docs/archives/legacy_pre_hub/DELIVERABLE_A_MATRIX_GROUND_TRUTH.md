# Deliverable A — Step 1 Ground Truth (Facebook Matrix v1)

**Purpose:** Establish DB-first ground truth for week 2026-W5 (and sources) as required by the “Fix Facebook Matrix v1 drift” briefing.

---

## 1. posting_queue (Facebook, date range 2026-01-26 .. 2026-02-01)

**Exact SQL (briefing columns; `channel_type` not in schema, omitted):**

```sql
SELECT id, platform, role, content_type, status,
       scheduled_date, scheduled_time, rota_year, rota_week,
       topic_id, angle_id
FROM posting_queue
WHERE platform = 'facebook'
  AND scheduled_date BETWEEN '2026-01-26' AND '2026-02-01'
ORDER BY scheduled_date, scheduled_time, id;
```

**Observed (2026-W5):** 21 rows. Summary by day (ISO weekday from date):

| Date       | ISO DOW | Content types present | Role |
|------------|---------|------------------------|------|
| 2026-01-26 (Mon) | 1 | weekly_phrase, weekly_insult, weekly_word | all NULL |
| 2026-01-27 (Tue) | 2 | weekly_phrase, weekly_insult, weekly_word, **product** | all NULL |
| 2026-01-28 (Wed) | 3 | weekly_phrase | NULL |
| 2026-01-29 (Thu) | 4 | weekly_insult, **product** | NULL |
| 2026-01-30 (Fri) | 5 | weekly_insult | NULL |
| 2026-01-31 (Sat) | 6 | **message**, **product** (×2) | NULL |
| 2026-02-01 (Sun) | 7 | depth_long | DEPTH_LONG |

**Drift vs Matrix v1:** Products on Tue/Thu/Sat; message on Sat; no authority on Fri; many duplicate language items on Mon/Tue. Matrix wants: Mon=Word, Tue=Phrase, Wed=Message, Thu=Insult, Fri=Authority, Sat=Product, Sun=Deep Dive.

---

## 2. Weekly language streams (word/phrase/insult)

**Tables:** `calendar_ideas` (item_classification, position), `calendar_category_cycles` (category, cycle_start_week).

**SQL used:**

```sql
SELECT category, cycle_start_week
FROM calendar_category_cycles
WHERE category IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
ORDER BY category;
```

```sql
SELECT id, item_classification, idea_title, position, created_at
FROM calendar_ideas
WHERE item_classification IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
ORDER BY item_classification, position
LIMIT 50;
```

**Observed:** `calendar_category_cycles` has `weekly_word`, `weekly_phrase` (no `weekly_insult` in output). `calendar_ideas` holds the pools; resolution for a given week is via `utils.calendar_resolver.resolve_item_for_week("weekly_word"|"weekly_phrase"|"weekly_insult", year, week_number, classification=...)`.

---

## 3. Product scheduling source

**Config:** `post_type_channel_config` (product) returned no rows in this run. **Recurring weekdays** come from `daily_posts_schedule`:

**SQL:**

```sql
SELECT id, name, platform, content_type, days, time, is_active
FROM daily_posts_schedule
WHERE is_active = TRUE AND platform = 'facebook' AND content_type = 'product';
```

**Observed:**

| id | name         | days   | time   |
|----|--------------|--------|--------|
| 31 | TuesThurs5pm | [2, 4] | 17:00  |
| 9  | Weekends     | [7]    | 15:00  |

So product weekdays are **Tue, Thu, Sun** (ISO 2, 4, 7). Matrix v1 requires **Saturday (6) only** for COMMERCE/product.

---

## 4. Message/reassurance scheduling source

**SQL:**

```sql
SELECT post_type, channel, publication_day, publication_time, is_active
FROM post_type_channel_config
WHERE channel = 'facebook' AND post_type = 'message' AND is_active = TRUE;
```

**Observed:** `publication_day = 6` (Saturday), `publication_time = 14:30`.

**Code:** `scripts/automated_message_post_creator.py` line 41: `self.publication_day = 6` (Saturday). Matrix v1 requires **Wednesday (3)** for REASSURANCE/message.

---

## 5. Script and how to re-run

- **Script:** `scripts/step1_matrix_ground_truth.py`
- **Command for 2026-W5:**  
  `python3 scripts/step1_matrix_ground_truth.py --week 2026-W5`
- **Write to file:**  
  `python3 scripts/step1_matrix_ground_truth.py --week 2026-W5 --out docs/DELIVERABLE_A_MATRIX_GROUND_TRUTH_output.txt`
