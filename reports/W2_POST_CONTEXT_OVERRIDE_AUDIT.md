# W2 Post context override audit (7.4)

## Rule

On any `/planning/posts/<post_id>/...` page: post context wins; week schedule must not overwrite theme/subtitle/summary. Any “auto-generate from theme” must be explicit (button-driven), not implicit on load, and must not run if post already has subtitle unless user requests.

## Files touched and guards

| File | Guard added? | Guard condition / behaviour |
|------|--------------|----------------------------|
| `templates/planning/calendar/ideas.html` | Yes | **DOMContentLoaded:** If `window.postContext?.post_id` → set theme + subtitle from postContext, `updateUIState()`, return; no `checkThemeSelection` / `loadThemesForWeek`. |
| `templates/planning/calendar/ideas.html` | Yes | **checkThemeSelection:** First line: `if (window.postContext && window.postContext.post_id) return;` |
| `templates/planning/calendar/ideas.html` | Yes | **loadThemesForWeek:** First line: `if (window.postContext && window.postContext.post_id) return;` |
| `templates/planning/calendar/ideas.html` | Yes | **generateSubtitleFromTheme:** First line: `if (window.postContext && window.postContext.post_id) return;` |
| `templates/planning/calendar/ideas.html` | Yes | **loadPostMetadata:** When `postContext.post_id`, subtitle = `postContext.subtitle \|\| postContext.summary`; no call to `generateSubtitleFromTheme` on load (implicit generate removed). |
| `blueprints/planning_calendar_clean.py` | Yes (context) | Passes `post_context` and `post_derived_theme` from post row so post page never relies on schedule for theme/subtitle. |
| `static/js/shared/blog-pipeline-header.js` | No new guard | Already uses post: when `postId` present and post type is `themed`, sets theme from `postTypeData.post_title` and returns before any schedule fetch (Instruction Set 5). |
| `templates/planning/calendar/ideas_week.html` | N/A | Week-based page (no post_id in URL); not a post page. |
| `static/js/planning/taxonomy-assignment.js` | N/A | Fetches schedule for week context; does not set theme/subtitle on ideas body. |
| `static/js/planning/calendar-week-view.js` | N/A | Week view; not a post page. |

## Summary

Only the **post-based ideas page** (`ideas.html` under `/planning/posts/<id>/calendar/ideas`) needed guards. All theme/subtitle resolution there is gated on `window.postContext.post_id`; when set, week/theme APIs are not used and generate-from-theme does not run on load.
