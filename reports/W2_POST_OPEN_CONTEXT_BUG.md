# W2 — Open Post landing context bug (post 729)

**Created:** 2026-02-25  
**Purpose:** Fix "Open Post" landing so the ideas page shows post context (title, status) instead of "Theme | Unselected theme".

---

## 5.1 DB truth for post 729

### Post record

```text
psql -d blog -c "
SELECT id, title, status, category, workflow_stage, created_at, updated_at
FROM post
WHERE id = 729;"
```

**Actual output (category/workflow_stage not in schema; run without them):**

```text
POST 729: {'id': 729, 'title': 'Irish tartans', 'status': 'draft', 'created_at': datetime.datetime(2026, 2, 25, 14, 45, 45, 3476), 'updated_at': datetime.datetime(2026, 2, 25, 17, 12, 17, 343054)}
```

Post 729 is a normal blog post: title "Irish tartans", status "draft". (No `category` or `workflow_stage` column in `post`; workflow_stage lives in `extra_settings`.)

### Blog slot linking to post 729

```text
psql -d blog -c "
SELECT id, item_type, item_id, year, week_number, scheduled_date, is_active, metadata
FROM calendar_week_items
WHERE item_type='blog' AND (metadata->>'post_id')::int = 729
ORDER BY year DESC, week_number DESC
LIMIT 5;"
```

**Output:**

```text
BLOG SLOT rows: [{'id': 503, 'item_type': 'blog', 'item_id': 0, 'year': 2026, 'week_number': 9, 'scheduled_date': datetime.date(2026, 2, 26), 'is_active': True, 'metadata': {'post_id': 729, 'converted': True, 'idea_item_id': 1398, 'idea_week_item_id': 499}}]
```

Blog slot metadata correctly links to post 729.

### Idea rows with metadata.post_id = 729

```text
psql -d blog -c "
SELECT id, item_type, item_id, year, week_number, is_selected, metadata
FROM calendar_week_items
WHERE item_type='idea' AND (metadata->>'post_id')::int = 729
ORDER BY id DESC
LIMIT 5;"
```

**Output:**

```text
IDEA rows (metadata.post_id=729): []
```

No idea rows have metadata.post_id=729 (conversion links the blog slot to the post, not the idea row).

---

## 5.2 Route + template that render "Theme | Unselected theme"

**Route (single best match):**

- **File:** `blueprints/planning.py`
- **Function:** `planning_calendar_ideas(post_id)`
- **Decorator:** `@bp.route('/posts/<int:post_id>/calendar/ideas')` (line 174)
- **Handler:** `ideas_func(post_id)` → `planning_calendar_ideas` in `blueprints/planning_calendar_clean.py`

**Template:** `planning/calendar/ideas.html` (rendered by `planning_calendar_ideas` in `planning_calendar_clean.py`).

**Code that sets "Unselected theme":**

- **Template:** `templates/shared/blog_pipeline_header.html` line 32:  
  `<span class="pipeline-title-theme" id="pipeline-title-theme">Unselected theme</span>`  
  (initial placeholder; shown when `post_type` is not recipe/profile/generated.)
- **JS:** `static/js/shared/blog-pipeline-header.js` line 794:  
  `themeEl.textContent = 'Unselected theme';`  
  (in `updateWeekAndTheme()` when no theme is found and no post-type override applied.)

**Snippet (blog-pipeline-header.js, ~lines 748–796):**

The header fetches `/api/post-type-pipeline/posts/${postId}/pipeline` and only overrides the theme element for `post_type === 'recipe'`, `'profile'`, or `'generated'` (with products-producers). For `post_type === 'themed'` (blog/article) it does not override; it falls through to week/theme lookup, and when no theme is selected for the week it sets "Unselected theme". Post 729 is `themed` (no recipe_id, profile_category_id, or generated_source_type), so it never gets the post title in the theme slot.

---

## 5.3 What "Open Post" links to (source of truth)

**From static/js/home_governance.js:**

- Line 467:  
  `actions.push('<a href="/planning/posts/' + slot.post_id + '/calendar" class="text-blue-400 hover:text-blue-300">Open Post</a>');`  
  So the blog row "Open Post" href is: **`/planning/posts/729/calendar`**.

**Redirect:** In `blueprints/planning.py`, the route `/posts/<int:post_id>/calendar` (line 95, `planning_calendar`) redirects to `url_for('planning.planning_calendar_ideas', post_id=post_id, year=year, week=week)`, so the user lands on **`/planning/posts/729/calendar/ideas`** (with optional year/week query params). So "Open Post" correctly lands on the ideas page; the bug is that the ideas page header shows "Unselected theme" instead of the post title/status for themed (blog) posts.

---

## 5.4 Fix rule (implemented)

- **Chosen approach:** Option 1 — Keep "Open Post" pointing at `/planning/posts/<id>/calendar/ideas` and fix the page so the header uses post context for blog/article posts.
- **Implementation:** In `static/js/shared/blog-pipeline-header.js`, in `updateWeekAndTheme()`, after fetching `/api/post-type-pipeline/posts/${postId}/pipeline`, add a branch for `post_type === 'themed'`: set the theme element to `post_title` (or "Blog post") so the header shows the post title and no longer shows "Unselected theme" for a valid post like 729.

---

## 5.5 Reporting proof (after fix)

**1. curl:**

```bash
curl -s http://localhost:5000/api/home/governance-summary | jq '.scheduled_slots | map({role,item_type,post_id,summary,scheduled_date})'
```

**Output:**

```json
[
  {
    "role": "blog",
    "item_type": "blog",
    "post_id": 729,
    "summary": "Irish tartans",
    "scheduled_date": "2026-02-26"
  },
  {
    "role": "weekly_word",
    "item_type": "weekly_word",
    "post_id": null,
    "summary": "wheesht",
    "scheduled_date": "2026-03-02"
  },
  {
    "role": "weekly_phrase",
    "item_type": "weekly_phrase",
    "post_id": null,
    "summary": "Pure dead brilliant",
    "scheduled_date": "2026-03-03"
  }
]
```

**2. Screenshot path:** `reports/screenshots/W2_POST_OPEN_CONTEXT_FIXED.png`

Shows the destination page after clicking Open Post (or navigating to `/planning/posts/729/calendar/ideas`): header shows post title "Irish tartans" (not "Unselected theme") and status from post context.

---

## 5.6 Commit

**Done:**

- `git add static/js/shared/blog-pipeline-header.js reports/W2_POST_OPEN_CONTEXT_BUG.md reports/screenshots/W2_POST_OPEN_CONTEXT_FIXED.png`
- `git commit -m "W2: fix Open Post landing to use post context (no unselected theme mismatch)"`

**git log -1 --oneline:** `b3c91e4f W2: fix Open Post landing to use post context (no unselected theme mismatch)`

**git status:** 3 files changed (report, screenshot, blog-pipeline-header.js); other local changes remain unstaged.
