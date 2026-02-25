# W2 7.5 UI verification

## Screenshot

- **Path:** `reports/screenshots/W2_POST_729_SUBTITLE_FIXED.png`
- **Shows:** `/planning/posts/729/calendar/ideas` with body theme = Irish tartans, Subtitle field populated from post, no Unicorn.

## Curl proof (postContext in page)

```bash
curl -s http://localhost:5000/planning/posts/729/calendar/ideas | grep -n "postContext"
```

Sample output (line 501 shows injected context):

```
501:    window.postContext = {"post_id": 729, "subtitle": "The tradition of Irish tartans, and how they differ from the traditions of Scottish tartans", "summary": "The tradition of Irish tartans, and how they differ from the traditions of Scottish tartans", "title": "Irish tartans"};
...
```

## DB proof (post 729 subtitle/summary non-null)

```sql
SELECT id, title, LEFT(subtitle,80) AS subtitle_preview, LEFT(summary,80) AS summary_preview
FROM post WHERE id = 729;
```

Result after backfill:

| id  | title         | subtitle_preview | summary_preview |
|-----|---------------|------------------|-----------------|
| 729 | Irish tartans | The tradition of Irish tartans, and how they differ from the traditions of Scott... | The tradition of Irish tartans, and how they differ from the traditions of Scott... |
