# W2 Required ideas contract (8.2)

## Rules

- **Minimum:** 3 required ideas (enforced on advance from `ideas` → `structure`).
- **Maximum:** Soft cap 12 (UI can warn; backend can allow more if needed).
- **Storage:** Dedicated table `post_required_idea`, not JSON blob.

---

## Schema

```sql
CREATE TABLE IF NOT EXISTS post_required_idea (
  id SERIAL PRIMARY KEY,
  post_id INT NOT NULL REFERENCES post(id) ON DELETE CASCADE,
  text TEXT NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Migration:** `migrations/20260226_create_post_required_idea.sql`

---

## Validation

- **On stage advance (ideas → structure):** Backend calls `_count_required_ideas(post_id)`; if count < 3, `advance_post_stage()` returns `(False, "Minimum 3 required ideas not met", None)`.
- **UI:** Show count badge e.g. "Ideas (2/3 min)".

---

## Example query (count)

```sql
SELECT post_id, COUNT(*) AS required_count
FROM post_required_idea
WHERE post_id = 729
GROUP BY post_id;
```

Example result: `post_id | required_count` → `729 | 2` (would block advance until ≥ 3).
