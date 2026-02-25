# W2 Blog Slot Phase 3 — Verification

## F) Verification outputs

### SQL: weekly_word, weekly_phrase, blog for week 10

```bash
psql -d blog -c "
SELECT item_type, scheduled_date, id, item_id, metadata
FROM calendar_week_items
WHERE year=2026 AND week_number=10 AND item_type IN ('weekly_word','weekly_phrase','blog')
ORDER BY item_type;"
```

**Result:**

| item_type   | scheduled_date | id  | item_id | metadata |
|-------------|----------------|-----|---------|----------|
| weekly_word | 2026-03-02     | 423 | 1097    | {}       |
| weekly_phrase | 2026-03-03   | 490 | 1195    | {}       |
| blog        | 2026-03-05     | 504 | 0       | {}       |

- weekly_word date = 2026-03-02 (Monday)
- weekly_phrase date = 2026-03-03 (Tuesday)
- blog date = 2026-03-05 (Thursday)

### curl governance-summary

```bash
curl -s http://localhost:5000/api/home/governance-summary | jq '{
  window_start, window_end,
  scheduled_slots: (.scheduled_slots|map({role,item_type,slot_id,scheduled_date,post_id,summary})),
  blog_candidates: (.blog_candidates|map({week_item_id,title,is_selected,is_active,metadata,post_id}))
}'
```

**Result (representative):**

- `scheduled_slots` contains `weekly_word`, `weekly_phrase`, and `blog`.
- Blog slot has `item_type: "blog"`, a non-null `scheduled_date` (e.g. 2026-02-26 for week 9 when in window), and `slot_id` from the real `calendar_week_items` row.
- No synthetic blog injection: the blog row comes from the DB (`item_type = 'blog'`), not from a selected idea candidate.

**Confirmations:**

- scheduled_slots includes weekly_word, weekly_phrase, blog (blog has non-null scheduled_date).
- No synthetic blog injection code path remains (block removed from `api_home_governance_summary`).

### F2. Screenshot evidence

Save locally and reference in this report:

1. Governance panel showing the Blog row with a real scheduled date in the “Next 7 days” table.
2. Blog ideas accordion showing the candidates list.

Paths: (user to add after capturing, e.g. `screenshots/w2_phase3_governance_blog.png`, `screenshots/w2_phase3_candidates.png`)
