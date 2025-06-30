# Blog Post Views Refactor Plan (Canonical by ID)

## Objective
Unify all blog post views (develop, preview, json, etc.) under a consistent, ID-based URL schema and shared subheading/tab layout, ensuring reliability and maintainability for a private/internal site.

---

## 1. Canonical URL Schema

All post views will use the post's numeric ID as the canonical identifier:

```
/blog/<int:post_id>/<view>
```
Where:
- `<post_id>` is the unique integer ID of the post
- `<view>` is one of: `develop`, `preview`, `json`, etc.

**Examples:**
- `/blog/1/develop`   → Develop (edit/workflow) view
- `/blog/1/preview`   → Preview (public or styled preview)
- `/blog/1/json`      → JSON API view
- `/blog/1`           → Default view (could be preview or redirect to preview)

**Redirects:**
- `/blog/develop/<id>` and `/blog/<slug>` should redirect to `/blog/<id>/<view>` as appropriate.

---

## 2. Consistent Subheading (Tab/Secondary Nav) Layout

- Every post view renders a shared subheading (tabs/nav) below the main site header.
- This subheading:
  - Shows links to all available views (Develop, Preview, JSON, etc.)
  - Highlights the active view
  - Uses the same layout and styling everywhere

---

## 3. Refactoring Steps

### A. Routing
- Refactor all post-related routes to use `/blog/<int:post_id>/<view>` as the canonical pattern.
- Add helper functions to resolve a post by ID (and redirect from slug if needed).
- Update all links and redirects in templates and scripts.

### B. Shared Subheading Component
- Create a Jinja macro or include template for the post subheading nav.
- Pass the current view and post object to this component.
- Use consistent classes and highlight the active tab.

### C. View Functions
- Each view (`develop`, `preview`, `json`, etc.) gets its own route and template, but all use the same subheading.
- The default `/blog/<id>` can redirect to `/blog/<id>/preview` or render the preview directly.

### D. Backward Compatibility
- Keep `/blog/develop/<id>` and `/blog/<slug>` as redirects to the new canonical URLs.

### E. Testing
- After each step, test all views for consistency and correct highlighting of the active tab.

---

## 4. Example: Unified Routing and Template Usage

**Flask routes:**
```python
@bp.route('/<int:post_id>/', defaults={'view': 'preview'})
@bp.route('/<int:post_id>/<view>')
def post_view(post_id, view):
    post = Post.query.get_or_404(post_id)
    if view == 'develop':
        # render develop template
    elif view == 'json':
        # return JSON
    elif view == 'preview':
        # render preview template
    else:
        abort(404)
```

**Jinja subheading macro:**
```jinja
{% macro post_subnav(post, active) %}
<div class="post-subnav">
  <a href="{{ url_for('blog.post_view', post_id=post.id, view='develop') }}" class="{{ 'active' if active == 'develop' else '' }}">Develop</a>
  <a href="{{ url_for('blog.post_view', post_id=post.id, view='preview') }}" class="{{ 'active' if active == 'preview' else '' }}">Preview</a>
  <a href="{{ url_for('blog.post_view', post_id=post.id, view='json') }}" class="{{ 'active' if active == 'json' else '' }}">JSON</a>
</div>
{% endmacro %}
```

**Usage in templates:**
```jinja
{% from 'blog/_post_subnav.html' import post_subnav %}
{{ post_subnav(post, 'develop') }}
```

---

## 5. Next Steps

1. Refactor Flask routes to use the new schema.
2. Create the shared subheading macro/template.
3. Update all templates to use the new subheading and canonical URLs.
4. Add redirects for legacy URLs.
5. Test all views for consistency. 