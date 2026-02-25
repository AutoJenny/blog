# W2 No silent auto-generation audit (8.4)

## Prohibited behaviours

- No automatic subtitle generation on page load.
- No automatic section creation without user click.
- No theme-based overrides.
- No auto-stage advancement.

All generation must be triggered by **button click** or **explicit API call**.

---

## Guard rule

Any function named `generate*`, `auto*`, `checkThemeSelection`, or `loadThemesForWeek` must **early-return** if `post_id` context exists and the user did not explicitly trigger generation.

**Guard condition:** `if (window.postContext && window.postContext.post_id) return;` (or equivalent: do not run week/theme resolution or theme-based generation when on a post page).

---

## Guarded functions (ideas.html)

| Function | Guard | File |
|----------|-------|------|
| (DOMContentLoaded) | When `postContext.post_id` set theme + subtitle from postContext and return; do not run checkThemeSelection / loadThemesForWeek | templates/planning/calendar/ideas.html |
| checkThemeSelection | First line: `if (window.postContext && window.postContext.post_id) return;` | templates/planning/calendar/ideas.html |
| loadThemesForWeek | First line: `if (window.postContext && window.postContext.post_id) return;` | templates/planning/calendar/ideas.html |
| generateSubtitleFromTheme | First line: `if (window.postContext && window.postContext.post_id) return;` | templates/planning/calendar/ideas.html |
| loadPostMetadata | When postContext exists, set subtitle from post only; do not call generateSubtitleFromTheme on load | templates/planning/calendar/ideas.html |

---

## autoSaveSubtitle

`autoSaveSubtitle` is triggered by **user input** (input event on subtitle field), not on load; no change required.

---

## Files touched

- `templates/planning/calendar/ideas.html` — guards as above (already in place from 7.4).
