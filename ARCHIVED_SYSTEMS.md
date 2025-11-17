# Archived Systems - DO NOT USE

This document lists deprecated and archived systems that should NOT be used by LLMs or developers.

## 🚨 Critical: Old Blog Development System (DEPRECATED)

### Status: ARCHIVED - DO NOT USE

The old multi-server blog development system has been **fully deprecated and archived**. 

**NEVER reference or use:**
- `/workflow/posts/*` routes
- `blog-images` service on port 5005
- Old workflow system with multiple microservices
- `/planning/posts/0/calendar/week-view` (old planning system)

### Current System

The current unified system uses:
- **Single Flask app** on port 5000
- **Unified image processing** at `/imaging/posts/{id}/sections/image-generation`
- **Modern planning** at `/planning/posts/{id}/calendar/week-view`
- **Launchpad** at `/launchpad/`

### Archive Location

Old system code has been moved to:
- `ARCHIVED_OLD_WORKFLOW/` - Old workflow routes and templates
- `blog-images/` - Deprecated microservice (kept for reference only, NOT active)
- `blog-core/` - Old core system components
- `blog-launchpad/` - Old launchpad components (some still active)

### Migration Guide

- **Old**: `/workflow/posts/0/planning/idea/initial_concept`
- **New**: `/planning/posts/0/calendar/week-view` or `/imaging/posts/{id}/sections/image-generation`

- **Old**: `http://localhost:5005` (blog-images service)
- **New**: `http://localhost:5000/imaging/posts/{id}/sections/image-generation`

- **Old**: Multiple microservices
- **New**: Single unified Flask application

## For LLMs

⚠️ **If you see any reference to:**
- Port 5005
- `blog-images` service
- `/workflow/posts/` routes (unless clearly in ARCHIVED directory)
- Multiple server setup

**STOP** and use the modern unified system instead. The old system is archived for reference only and should never be activated or referenced in new code.







