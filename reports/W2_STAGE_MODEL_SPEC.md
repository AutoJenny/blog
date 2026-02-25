# W2 Early development round — stage model spec (8.1)

## Objective

Minimal, deterministic pipeline: **Post Metadata → Required Ideas → Section Structure → Section Titling → Authoring**. No silent auto-generation; no implicit week/theme injection. Stage advances only when user explicitly clicks "Advance Stage".

---

## Table of stages

| Stage      | Condition to advance from previous | Notes |
|-----------|-------------------------------------|-------|
| metadata  | (initial)                           | Default for new posts. |
| ideas     | title + subtitle present             | User has set post metadata. |
| structure | ≥3 required ideas                   | Min 3 in `post_required_idea`. |
| titling   | ≥3 sections generated               | Min 3 rows in `post_section`. |
| authoring | all sections have titles            | `section_heading` set on all sections. |
| imaging   | ≥1 section has body text             | At least one `post_section.draft` non-empty. |
| review    | (optional)                          | Can relax; advance from imaging allowed. |

Progression is **no skipping**: advance one step at a time. Backend enforces conditions on advance.

---

## SQL (column + constraint)

```sql
ALTER TABLE post
ADD COLUMN IF NOT EXISTS workflow_stage TEXT NOT NULL DEFAULT 'metadata';

UPDATE post SET workflow_stage = 'metadata' WHERE workflow_stage IS NULL OR workflow_stage = '';

ALTER TABLE post DROP CONSTRAINT IF EXISTS post_workflow_stage_valid;

ALTER TABLE post
ADD CONSTRAINT post_workflow_stage_valid
CHECK (workflow_stage IN (
  'metadata',
  'ideas',
  'structure',
  'titling',
  'authoring',
  'imaging',
  'review'
));
```

**Migration file:** `migrations/20260226_add_workflow_stage_column.sql`

---

## Progression logic

- **Backend function:** `advance_post_stage(post_id)` in `utils/posts/early_stage.py`.
- **Behaviour:** Reads current stage from `post.workflow_stage`; computes next stage; checks condition for current → next; if met, updates `post.workflow_stage` and returns `(True, None, new_stage)`; otherwise returns `(False, error_message, None)`.
- **Do NOT auto-advance:** Stage only changes when this function is called (e.g. from `POST /api/posts/<id>/advance-stage` triggered by "Advance Stage" button).

Conditions (from → to):

| From       | To         | Condition |
|-----------|------------|-----------|
| metadata  | ideas      | `post.title` and `post.subtitle` present (non-empty). |
| ideas     | structure  | `COUNT(post_required_idea WHERE post_id=?) >= 3`. |
| structure | titling    | `COUNT(post_section WHERE post_id=?) >= 3`. |
| titling   | authoring  | All `post_section` rows have non-empty `section_heading`. |
| authoring | imaging    | At least one `post_section` has non-empty `draft`. |
| imaging   | review     | Allowed (relaxed). |
