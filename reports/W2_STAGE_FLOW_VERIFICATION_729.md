# W2 Stage flow verification for post 729 (8.7)

## 1. Initial stage

Post 729 after migration: `workflow_stage` = **metadata** (or **ideas** after first advance).

```sql
SELECT id, workflow_stage FROM post WHERE id = 729;
-- id | workflow_stage
-- 729 | metadata
```

## 2. Add 3 required ideas

```sql
INSERT INTO post_required_idea (post_id, text, sort_order)
VALUES (729, 'Irish tartan history', 1), (729, 'Scottish vs Irish tartans', 2), (729, 'How to wear Irish tartans', 3);
```

## 3. Advance stage → structure

```bash
curl -s -X POST http://localhost:5000/api/posts/729/advance-stage
```

Expected (after metadata→ideas and ideas→structure): `{"success":true,"new_stage":"structure"}` (or first advance returns `"new_stage":"ideas"`).

## 4. Generate sections

Ensure `post_section` has ≥3 rows for post_id=729 (existing factory or manual INSERT). Then advance to titling.

## 5. Advance stage → titling

```bash
curl -s -X POST http://localhost:5000/api/posts/729/advance-stage
```

Expected (when current=structure and ≥3 sections, all with titles): `{"success":true,"new_stage":"titling"}`.

## 6. Persist after reload

```sql
SELECT id, workflow_stage FROM post WHERE id = 729;
-- id | workflow_stage
-- 729 | titling
```

Reload ideas page: stage indicator should show **Stage: TITLING** (from GET /api/posts/729/early-stage).

## Screenshot

**Path:** `reports/screenshots/W2_STAGE_FLOW_729.png` — ideas page for 729 showing Stage: IDEAS (3/3 min) or STRUCTURE (N sections) or TITLING after advances.

## SQL before/after (summary)

| Step        | workflow_stage |
|------------|----------------|
| Before     | metadata       |
| After +3 ideas, advance | ideas → structure |
| After sections, advance | structure → titling |
| After reload | titling (persisted) |
