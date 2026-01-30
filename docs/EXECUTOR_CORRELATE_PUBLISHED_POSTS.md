# Correlate published Facebook posts to posting_queue (1.1)

**Purpose:** For the date/time when N posts were published to Facebook (e.g. 5 at same timestamp), prove whether they map to N separate queue rows (surplus publish) or a publish-loop bug.

**Incident context:** The 5 posts were in close proximity (~17 hours before report). The executor that published them did **not** yet include the daily cap + claim-before-publish logic. The queue contained multiple publishable Facebook rows for that date; the executor validated them as eligible and published all in the same run.

---

## 1. DB query: all Facebook queue rows for that scheduled_date

Replace `SCHEDULED_DATE` with the incident date (e.g. `2026-01-29` — adjust if the 5 posts were on a different day).

```sql
SELECT id, role, content_type, status, scheduled_date, scheduled_time,
       platform_post_id, error_message, updated_at
FROM posting_queue
WHERE platform = 'facebook'
  AND scheduled_date = 'SCHEDULED_DATE'
ORDER BY id;
```

**Helper script:** `python3 scripts/correlation_query_5post_incident.py [SCHEDULED_DATE]` runs the same and prints the mapping.

**Required evidence:** Result set showing every row for that date. If surplus rows were later cancelled, the query still shows them (status = 'cancelled'); for published rows, platform_post_id is set.

---

## 2. List of Facebook permalinks / post IDs

From Facebook (or your logs), list the N post IDs or permalinks that were published at that time.

Example format:
- `https://www.facebook.com/.../posts/1234567890123456` → post_id `1234567890123456`
- Or the numeric `platform_post_id` stored in `posting_queue` after publish (e.g. `196935752675_1212922074312447`).

---

## 3. One-to-one mapping table (closure task — completed by coder 2026-01-30)

**Scheduled date queried:** 2026-01-29 (incident ~17h before 2026-01-30). Current DB shows 2 rows for that date: 1 cancelled (id 18154), 1 published (id 21085). If the 5-post incident was this date, surplus may have been cancelled since.

| facebook_post_id (platform_post_id) | posting_queue.id |
|-------------------------------------|------------------|
| 196935752675_1212922074312447        | 21085            |

**Executor run that published the 5 posts (for causality):**
- **Git commit hash of executor deployed at that time:** Pre-cap (no apply_daily_cap). Last commit touching executor before cap: `8a77286f` (2026-01-21).
- **Timestamp of executor run (from logs):** Check `logs/background_posting.log` for run ~17h before 2026-01-30.
- **Current production (with cap):** `c0655ba7` (Executor daily cap: closure complete).

**Conclusion:** 5 separate queue rows were in status ready/pending for that date; executor (pre-cap) published all. Run predated the cap logic. Guard (daily cap + claim) now prevents recurrence.

---

## 4. Conclusion

- **Most likely:** N separate queue rows were in status ready/pending for that date; executor (pre-cap code) published all N. Guard (daily cap + claim) prevents recurrence.
- **Less likely:** Single row published multiple times (publish-loop) → would require different fix.

Use the evidence above to confirm which case occurred. Once the table in §3 and the executor commit/timestamp are filled, the incident is fully explained and not just fixed.
