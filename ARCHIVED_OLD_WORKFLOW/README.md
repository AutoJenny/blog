# ARCHIVED: Old Workflow/Blog Development System

## ⚠️ DEPRECATED - DO NOT USE

This directory contains archived code from the old multi-server blog development system that has been **fully deprecated**.

## What Was Archived

- Old `/workflow/posts/*` routes
- Multi-server architecture (blog-images on port 5005, blog-core, etc.)
- Old planning system routes
- Legacy workflow navigation

## Current System

The modern unified system uses:
- **Single Flask app** (`unified_app.py`) on port 5000
- **Unified routes**: `/planning/`, `/imaging/`, `/launchpad/`
- **No separate microservices** - everything is in one application

## Migration Map

| Old Route | New Route |
|-----------|-----------|
| `/workflow/posts/{id}/planning/idea/initial_concept` | `/planning/posts/{id}/calendar/week-view` |
| `http://localhost:5005` (blog-images) | `/imaging/posts/{id}/sections/image-generation` |
| Multiple microservices | Single unified app |

## Why Archived

The old system used multiple Flask apps running on different ports, which was confusing and hard to maintain. The new system consolidates everything into a single application for better maintainability and clarity.

## For LLMs

**NEVER reference or activate code in this archive.** Always use the modern unified system routes and structure.

