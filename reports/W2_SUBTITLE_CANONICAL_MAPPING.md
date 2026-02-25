# W2 Subtitle canonical mapping (7.1)

## Rule

- **UI “Subtitle” input:** Display `post.subtitle` first, fallback to `post.summary`, else empty.
- **Theme description (Ideas page body):** Display `post.summary` (fallback `post.subtitle` if you standardise on one; we use summary-first, then subtitle).

Standardisation: **Theme description** = `post.summary || post.subtitle || ''` (one source of truth from post; summary preferred for “description” semantics).

## Where implemented

| Location | What |
|----------|------|
| **Backend** `blueprints/planning_calendar_clean.py` | `planning_calendar_ideas`: SELECT includes `p.subtitle`. `post_context` = `{ post_id, title, summary, subtitle }` from post. `post_derived_theme.theme_description` = `post.summary or post.subtitle or ''`. |
| **Template/JS** `templates/planning/calendar/ideas.html` | **Subtitle input:** On DOMContentLoaded (post page): `subtitleInput.value = (postContext.subtitle \|\| postContext.summary \|\| '').trim()`. In `loadPostMetadata()`: when `postContext`: `(postContext.subtitle \|\| postContext.summary \|\| '').trim()`; else `(data.post.subtitle \|\| data.post.summary \|\| '').trim()`. **Theme description:** `selectedTheme.theme_description` set from `postContext.summary || postContext.subtitle` when building from postContext. |

## Functions

- **planning_calendar_ideas** (planning_calendar_clean.py): Builds `post_context` and `post_derived_theme` with subtitle/summary and theme_description per rule.
- **loadPostMetadata** (ideas.html inline JS): Sets subtitle input per rule; no implicit generate-from-theme on load (7.4).
- **DOMContentLoaded** (ideas.html): When `postContext.post_id`, sets subtitle input and `selectedTheme.theme_description` per rule.
