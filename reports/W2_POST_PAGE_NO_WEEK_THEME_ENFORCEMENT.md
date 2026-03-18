# W2 Post page: no week/theme leaks (5.1 + 5.2)

## Canonical rule

On `/planning/posts/<id>/calendar/*` pages:

- **Theme title/description and subtitle** come from **post context only**.
- **Subtitle field:** `post.subtitle` else `post.summary` else empty.
- **Theme description:** `post.summary` else `post.subtitle` else empty.
- Any **week schedule** theme selection logic **must no-op** when `post_id` context exists.

## Guarded functions (names + files)

| Function / behaviour | File |
|----------------------|------|
| DOMContentLoaded: when `postContext.post_id` set theme + subtitle from postContext and return (no schedule fetch) | `templates/planning/calendar/ideas.html` |
| `checkThemeSelection` — first line: `if (window.postContext && window.postContext.post_id) return;` | `templates/planning/calendar/ideas.html` |
| `loadThemesForWeek` — first line: `if (window.postContext && window.postContext.post_id) return;` | `templates/planning/calendar/ideas.html` |
| `generateSubtitleFromTheme` — first line: `if (window.postContext && window.postContext.post_id) return;` | `templates/planning/calendar/ideas.html` |
| `loadPostMetadata` — when postContext exists, set subtitle from post only; do not call generateSubtitleFromTheme on load | `templates/planning/calendar/ideas.html` |
| Backend passes `post_context` and `post_derived_theme` from post row | `blueprints/planning_calendar_clean.py` |
| Header: themed post uses `postTypeData.post_title`, returns before schedule fetch | `static/js/shared/blog-pipeline-header.js` |

## Screenshot

Path: `reports/screenshots/W2_POST_729_THEME_SUBTITLE_CORRECT.png` — post 729 ideas page showing correct post theme (Irish tartans) and subtitle from post, no week theme.

---

## Proof block

```
9bfc29c4
...
9bfc29c4 W2: Leak enforcement + audit report and screenshot
```
