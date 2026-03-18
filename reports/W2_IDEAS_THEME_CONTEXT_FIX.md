# W2 — Ideas page theme context fix (kill theme leakage)

**Created:** 2026-02-25  
**Purpose:** Make the ideas page body use post-derived theme only; no week-based theme resolver so "Theme: Unicorn" cannot override the current post (e.g. 729 "Irish tartans").

---

## 6.1 Where the Unicorn data came from

- **Source of "Unicorn":** Theme title from calendar data (e.g. `data/themes_w_descriptions.csv`: id 10, "Unicorn", "Why the unicorn became Scotland's national beast."). The week’s schedule API returns the selected theme for that week (Unicorn).
- **Backend:** `ideas_func(post_id)` in `planning_calendar_clean.py` did **not** pass any theme to the template; it only passed `post`, `post_title`, `post_status`, `year`, `week_number`.
- **Body "Theme: …" section:** In `templates/planning/calendar/ideas.html`, the block around lines 77–84 renders the theme display; the JS around 698–711 sets `theme-title-display` and `theme-description-display` from `selectedTheme.theme_title` and `selectedTheme.theme_description`. `selectedTheme` was set only by week-based logic: `checkThemeSelection()` fetches `/planning/api/calendar/schedule/${year}/${week}` and sets `selectedTheme` from the schedule (hence Unicorn).

---

## Old code (before)

**Backend (planning_calendar_clean.py):** No theme passed; template received only post + year/week.

```python
# Get post data with all required fields for header
with db_manager.get_cursor() as cursor:
    cursor.execute("""
        SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
               p.content_type_id
        FROM post p
        WHERE p.id = %s
    """, (target_post_id,))
    post = cursor.fetchone()
# ...
return render_template('planning/calendar/ideas.html', 
                       post_id=post_id,
                       post=post,
                       post_type=post_type,
                       post_title=post.get('title'),
                       post_status=post.get('status'),
                       # ... no post_derived_theme
                       year=year,
                       week_number=week_number,
                       ...)
```

**Template/JS:** No `postDerivedTheme`; DOMContentLoaded always ran week-based theme load.

```javascript
document.addEventListener('DOMContentLoaded', async function() {
    await checkThemeSelection();
    await loadThemesForWeek();
    updateUIState();
});
```

`checkThemeSelection()` fetched `/planning/api/calendar/schedule/${year}/${week}` and set `selectedTheme` from the week’s theme (Unicorn), which was then shown in the body.

---

## New code (after)

**Backend:** Post query includes `p.summary`; for `post_type == 'themed'`, build theme from post only and pass it.

```python
# Get post data with all required fields for header and body
with db_manager.get_cursor() as cursor:
    cursor.execute("""
        SELECT p.id, p.title, p.status, p.summary, p.created_at, p.updated_at,
               p.content_type_id
        FROM post p
        WHERE p.id = %s
    """, (target_post_id,))
    post = cursor.fetchone()
# ...
# Post-authoritative theme for body: no week/theme resolver; theme from post only
post_derived_theme = None
if post_type == 'themed' and post.get('title'):
    post_derived_theme = {
        'post_id': post_id,
        'theme_title': post.get('title'),
        'theme_description': post.get('summary') or '',
        'priority': 'normal',
    }
return render_template('planning/calendar/ideas.html', 
                       ...
                       post_derived_theme=post_derived_theme,
                       ...)
```

**Template:** Inject `postDerivedTheme` when present.

```html
{% if post_derived_theme %}window.postDerivedTheme = {{ post_derived_theme | tojson }};{% else %}window.postDerivedTheme = null;{% endif %}
```

**JS:** Prefer post-derived theme; skip week theme when present; guard against cross-post theme.

```javascript
document.addEventListener('DOMContentLoaded', async function() {
    if (window.postDerivedTheme && window.postDerivedTheme.theme_title) {
        selectedTheme = window.postDerivedTheme;
        themeSelectedForWeek = true;
    } else {
        await checkThemeSelection();
        await loadThemesForWeek();
        if (selectedTheme && window.postId && selectedTheme.post_id != null && selectedTheme.post_id !== window.postId) {
            selectedTheme = null;
            themeSelectedForWeek = false;
        }
    }
    updateUIState();
});
```

In `checkThemeSelection()`, after setting `selectedTheme` from the schedule/API, the same guard is applied: if `selectedTheme.post_id != window.postId`, clear `selectedTheme`.

---

## Screenshot

**Path:** `reports/screenshots/W2_IDEAS_THEME_CONTEXT_FIXED.png`

Shows `/planning/posts/729/calendar/ideas` with body displaying **Theme: Irish tartans** (or equivalent from post title/summary), not Unicorn.

---

## Verification

**Confirmed:** Theme in the body is derived from post 729 (title/summary) only, not from the week/theme resolver.
