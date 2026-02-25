# W2 Conversion sets subtitle/summary (7.3)

## Rule

- **New draft post:** Set `post.subtitle` and `post.summary` from source item description (theme/idea); truncate to 300 chars. If source has only a title (no description), leave subtitle/summary NULL.
- **Reuse existing post:** When returning an existing post for the same idea/theme, if that post has NULL or empty subtitle/summary and the source has a description, UPDATE the post to set `subtitle` and `summary` from the source (same truncation). Do not invent from week theme.

## Source fields and truncation

| Category | Source fields (in order) | Truncation |
|----------|-------------------------|------------|
| theme    | `theme_description`, `description` | 300 chars |
| idea     | `idea_description`, `description` | 300 chars |

Python: `(item_dict.get('theme_description') or item_dict.get('idea_description') or item_dict.get('description') or '')[:300]`. Empty string becomes NULL in INSERT.

## Where implemented

- **New post:** `blueprints/automation_core.py` — `create_post_from_item`: `post_summary = (...)[:300] if category in ('theme', 'idea') else None`; INSERT uses `(title, slug, 'draft', post_summary, post_summary, ...)`.
- **Reuse:** Same file, immediately after `if existing_post_id:`: if `category in ('theme','idea')`, compute `_desc` from same source and truncate 300; run `UPDATE post SET subtitle = %s, summary = %s, updated_at = NOW() WHERE id = %s AND (subtitle IS NULL OR subtitle = '') AND (summary IS NULL OR summary = '')`.

## Curl proof (convert then verify)

Create a test idea with description, convert to post, then show the post has subtitle/summary:

```bash
# 1) Create an idea with a known description (e.g. via API or DB). Assume idea_id=ID and year/week known.

# 2) Convert idea to post
curl -s -X POST http://localhost:5000/planning/create-post-from-item \
  -H "Content-Type: application/json" \
  -d '{"category":"idea","item_id":"<idea_id>","year":2026,"week":9}' | jq .

# 3) From response take post_id, then fetch post and check subtitle/summary
curl -s "http://localhost:5000/planning/api/posts/<post_id>" | jq '.post | {title, subtitle, summary}'
```

Example (after running convert for an idea that has `idea_description` set):

```json
{
  "title": "Irish tartans",
  "subtitle": "The tradition of Irish tartans, and how they differ from the traditions of Scottish tartans",
  "summary": "The tradition of Irish tartans, and how they differ from the traditions of Scottish tartans"
}
```

(Planning API returns `post` with `subtitle`; if your GET endpoint exposes `summary` too, both will be populated for new and updated conversions.)
