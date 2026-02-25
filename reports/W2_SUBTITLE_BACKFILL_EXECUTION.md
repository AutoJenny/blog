# W2 Subtitle backfill execution (7.2)

**Note:** Table name is `post` (not `posts`). All commands below use `post`.

## Before

```text
SELECT id, title, summary, subtitle FROM post WHERE id IN (729);
```

| id  | title          | summary | subtitle |
|-----|----------------|---------|----------|
| 729 | Irish tartans  | NULL    | (Unicorn leak text) |

(Subtitle had been overwritten by week-theme; summary was NULL.)

## Backfill run

```bash
# From project root, using psql:
psql -d blog -f migrations/20260225_backfill_post_subtitle_summary_from_ideas.sql
```

Or via Python (as executed):

```python
from config.database import db_manager
with open('migrations/20260225_backfill_post_subtitle_summary_from_ideas.sql') as f:
    sql = f.read()
with db_manager.get_cursor() as c:
    c.execute(sql)
```

Migration: `migrations/20260225_backfill_post_subtitle_summary_from_ideas.sql` — backfills `post.subtitle` and `post.summary` from the linked idea (blog slot `metadata.post_id` → `metadata.idea_item_id` → `calendar_ideas.idea_description` / `idea_title`), truncated to 300 chars.

## After

```text
SELECT id, title, summary, subtitle FROM post WHERE id IN (729);
```

| id  | title          | summary | subtitle |
|-----|----------------|---------|----------|
| 729 | Irish tartans  | The tradition of Irish tartans, and how they differ from the traditions of Scottish tartans | The tradition of Irish tartans, and how they differ from the traditions of Scottish tartans |

Both `summary` and `subtitle` are now populated from the linked idea (calendar_ideas id 1398).
