# Base-Framework Branch: File Manifest & Deletion Plan

## Purpose
This document defines the minimal set of files and directories required for the firewalled base-framework branch, and lists all files/directories that are safe for deletion to maintain module purity. This ensures the framework can be merged into other branches without legacy or workflow contamination.

---

## 1. Files/Directories REQUIRED for Main Framework

### Python Modules
- `app/__init__.py`
- `app/main/` (context processors, routes, homepage, navigation)
- `app/database/` (database explorer)
- `app/api/llm/` (LLM settings)
- `app/routes/settings.py` (settings navigator)
- `app/errors/` (error handling)
- `app/blog/` (for header/footer, posts list, but NOT workflow)
- `app/models.py`, `app/db.py`, `app/utils.py`, `app/tasks.py` (core utilities, if used by above)
- `app/logs/` (if logging is required for framework)

### Templates
- `app/templates/base.html`, `base_minimal.html`
- `app/templates/main/` (homepage, navigation, docs browser, LLM dashboard, etc.)
- `app/templates/db/` (database explorer)
- `app/templates/docs/` (docs module)
- `app/templates/settings/` (settings navigator)
- `app/templates/errors/` (error pages)
- `app/templates/blog/` (header, posts_list, etc. — but NOT workflow/planning)

### Static Assets
- `app/static/css/dist/main.css` (Tailwind build)
- `app/static/css/src/main.css` (Tailwind source)
- `app/static/css/admin.css`, `blog.css`, `style.css` (if referenced in templates)
- `app/static/images/site/` (brand logo, header, footer images)
- `app/static/images/logo/` (site logo)
- `app/static/images/posts/` (if posts list uses them)
- `app/static/uploads/`, `app/static/cache/` (if used by main modules)

---

## 2. Files/Directories SAFE FOR DELETION (Workflow/Legacy/Not Needed)

- `app/archive/` (entire directory: only workflow/planning templates)
- `app/data/prompts/` (all files are workflow/planning related)
- `app/posts/` (not needed)
- `app/preview/` (not needed)
- `app/services/structure.py` (not used by main framework)
- `app/templates/settings/planning_steps.html`, `workflow_field_mapping.html`, `workflow_prompts.html` (all workflow-related)
- `app/templates/main/llm_prompts.html` (if only used for workflow)
- `app/static/comfyui_output/` (if only used for workflow/LLM image generation)
- `app/static/images/posts/quaich-traditions/`, `app/static/images/posts/kilt-evolution/` (if only used for workflow/legacy posts)
- Any unused/legacy CSS files in `app/static/css/` except those referenced in templates

---

## 3. Notes
- `app/services/structure.py` is NOT used by any main framework code and is safe to delete.
- If any images or CSS are referenced by the homepage, header, or posts list, retain them.
- This manifest should be updated if new modules are added or requirements change.

---

## 4. Next Steps
- Delete all files/directories listed in section 2.
- Retain only those in section 1 for a pure, firewalled base-framework.
- Commit this manifest and all changes to git as a record of the branch state. 