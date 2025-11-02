# ARCHIVED: Old Workflow/Blog Development System

## ⚠️ DEPRECATED - DO NOT USE

This directory contains archived code from the old multi-server blog development system that has been **fully deprecated**.

## What Was Archived

- Old `/workflow/posts/*` routes (from `blueprints/core.py`)
- `planning_old_interface` route and template
- All navigation links to "Old Interface"
- Old workflow system templates (`workflow.html`, `old_interface.html`)

## Current System

The modern unified system uses:
- **Single Flask app** (`unified_app.py`) on port 5000
- **Unified routes**: `/planning/`, `/authoring/`, `/imaging/`, `/header/`, `/launchpad/`
- **No separate microservices** - everything is in one application

## Migration Map

| Old Route | New Route |
|-----------|-----------|
| `/workflow/posts/{id}/planning/idea/initial_concept` | `/planning/posts/{id}/calendar/week-view` |
| `/workflow/posts/{id}/writing/content` | `/authoring/posts/{id}/sections/drafting` |
| `/planning/posts/{id}/old-interface` | (removed - use unified system) |
| `http://localhost:5005` (blog-images) | `/imaging/posts/{id}/sections/image-generation` |

## Archive Contents

- `routes/workflow_routes.py` - All old workflow routes extracted from `blueprints/core.py`
- `templates/old_interface.html` - Old interface redirect page
- `templates/workflow.html` - Old workflow template

## Why Archived

The old system used multiple Flask apps running on different ports, which was confusing and hard to maintain. The new system consolidates everything into a single application for better maintainability and clarity.

## Restoration

If you need to restore this code for reference:
1. All code is preserved in this directory
2. The routes can be re-registered by importing from `ARCHIVED_OLD_WORKFLOW/routes/workflow_routes.py`
3. Templates are preserved in `ARCHIVED_OLD_WORKFLOW/templates/`

**However, these should NEVER be activated in production. This is for reference only.**

## For LLMs

**NEVER reference or activate code in this archive.** Always use the modern unified system routes and structure.
