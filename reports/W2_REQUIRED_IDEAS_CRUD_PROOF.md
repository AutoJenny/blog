# W2 Required ideas CRUD proof (3.3)

## API

- **GET** `/planning/api/posts/<id>/required-ideas` — list (from `post_required_idea`).
- **POST** `/planning/api/posts/<id>/required-ideas` — replace all (body: `{ "required_ideas": [ { "text", "sort_order" } ] }`).
- **POST** `/planning/api/posts/<id>/required-ideas/items` — add one (body: `{ "text", "sort_order"? }`).
- **PATCH** `/planning/api/posts/<id>/required-ideas/items/<item_id>` — update text/sort_order.
- **DELETE** `/planning/api/posts/<id>/required-ideas/items/<item_id>` — delete one.

Main post fetch (`GET /planning/api/posts/<id>`) now injects `embedding_overrides.required_ideas` from `post_required_idea` so the ideas page sees the table data.

## Proof (post 729)

**1. List required ideas in DB**

```bash
psql -d blog -c "SELECT id, post_id, sort_order, text FROM post_required_idea WHERE post_id=729 ORDER BY sort_order, id;"
```

```
 id | post_id | sort_order |           text            
----+---------+------------+---------------------------
  1 |     729 |          1 | Irish tartan history
  2 |     729 |          2 | Scottish vs Irish tartans
  3 |     729 |          3 | How to wear Irish tartans
(3 rows)
```

**2. Early-stage shows count 3**

```bash
curl -s http://localhost:5000/api/posts/729/early-stage | jq
```

```json
{
  "required_ideas_count": 3,
  "sections_count": 5,
  "success": true,
  "workflow_stage": "ideas"
}
```

**3. Advance ideas → structure succeeds**

```bash
curl -s -X POST http://localhost:5000/api/posts/729/advance-stage | jq
```

```json
{
  "new_stage": "structure",
  "success": true
}
```

**4. Stage persisted**

```bash
curl -s http://localhost:5000/api/posts/729/early-stage | jq
```

```json
{
  "required_ideas_count": 3,
  "sections_count": 5,
  "success": true,
  "workflow_stage": "structure"
}
```

---

## Proof block

```
git rev-parse HEAD
git status
git log -1 --oneline
```
