# W2 Post Context Leak Audit — Instruction Set 7

## A) DB truth for post 729

```text
id: 729
title: 'Irish tartans'
summary: None
status: draft
created_at: 2026-02-25 14:45:45.003476
updated_at: 2026-02-25 17:12:17.343054
```

**Interpretation:** `title` is correct (Irish tartans). `summary` is NULL, so the Subtitle field had been filled by week-theme logic (e.g. generateSubtitleFromTheme using Unicorn) and/or by a previously saved `subtitle` value from that flow. The fix: (1) Ideas page uses `postContext.summary` for theme description and subtitle when `post_id` is present, so no week/theme overwrite; (2) New conversions set `post.summary` and `post.subtitle` from the idea/theme source (conversion mapping in section D).

---

## B) Ideas page — before/after

**Before:** Theme title was fixed to post (Irish tartans), but Subtitle was still set from `data.post.subtitle` then, if empty, from `generateSubtitleFromTheme()` using week theme (Unicorn). So week-theme could overwrite the subtitle.

**After:**
- Backend (`planning_calendar_clean.py`): For themed posts, pass `post_context = { post_id, title, summary }` (and keep `post_derived_theme`).
- Template: Inject `window.postContext` when `post_context` is present.
- JS:
  - On DOMContentLoaded, if `window.postContext?.post_id`: set `selectedTheme` from postContext (title/summary), set subtitle input to `postContext.summary || ''`, then `updateUIState()` and **return** (no `checkThemeSelection` / `loadThemesForWeek`).
  - In `loadPostMetadata()`: if `postContext.post_id`, set subtitle from `postContext.summary` only; do not call `generateSubtitleFromTheme()`.
  - `generateSubtitleFromTheme()`: no-op if `window.postContext?.post_id`.
  - `checkThemeSelection()` and `loadThemesForWeek()`: no-op if `window.postContext?.post_id`.

Result: Theme title, theme description, and Subtitle all come from post (title/summary). No schedule/week theme overwrites.

---

## C) Other calendar subpages

Search for `checkThemeSelection`, `loadThemesForWeek`, `selectedTheme`, `theme-title-display`, `subtitle`, `postDerivedTheme` / `postContext` was done. Only **ideas.html** (post-based ideas page under `/planning/posts/<id>/calendar/ideas`) uses theme resolution and subtitle; **ideas_week.html** is week-based (no post_id in context for the main flow). No other post calendar subpages required patching for this leak.

---

## D) Conversion mapping

Post 729 had `summary: None`; the idea’s description was not copied into `post.summary` at creation. Conversion was updated so that when a post is created from an idea or theme:

- `post.title` = idea/theme title (unchanged).
- `post.summary` = idea/theme description (from `idea_description` / `theme_description` / `description`), truncated to 300 chars for storage.
- `post.subtitle` = same value as `post.summary` so the Ideas page and APIs have a consistent subtitle from the source.

**Code:** `blueprints/automation_core.py` — in `create_post_from_item`, for `category in ('theme', 'idea')` we set `post_summary` from the item and pass it into the INSERT: `INSERT INTO post (title, slug, status, summary, subtitle, created_at, updated_at) VALUES (..., post_summary, post_summary, ...)`.

---

## E) Verification

### Curl (page renders)

```bash
curl -s http://localhost:5000/planning/posts/729/calendar/ideas | head -n 40
```

Output (confirming page renders):

```html
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    ...
    <link rel="stylesheet" href="/static/css/shared/dark-theme.css">
    ...
```

(Screenshot is the real proof; see below.)

### Screenshots

- **reports/screenshots/W2_POST_729_IDEAS_FIXED.png** — Ideas page for post 729: Theme title “Irish tartans”, Subtitle empty or from post (no Unicorn text).

No other tabs were patched; no additional screenshots.

---

## Summary

- **A:** Post 729 DB: title correct, summary NULL (subtitle was being filled by week-theme).
- **B:** Ideas page now uses `postContext` only when `post_id` is present; theme and subtitle from post; week/theme fetches cannot overwrite.
- **C:** Only ideas.html needed changes; ideas_week.html is week-based.
- **D:** New posts from idea/theme get `post.summary` and `post.subtitle` from the source item.
- **E:** Report and screenshot paths as above.
