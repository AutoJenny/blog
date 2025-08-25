# Project Overview

The Blog Content Management System (CMS) is a Flask-based platform for creating, previewing, and managing blog content with AI assistance. It is designed for use with clan.com/blog, enabling local content creation, preview, and seamless export to the main platform.

## Main Features
- AI-assisted writing and editing (LLM integration)
- Local preview matching clan.com styling
- Media management (images, uploads)
- Direct export to clan.com/blog
- Redis caching for fast previews
- PostgreSQL database backend
- Tailwind CSS for modern UI

## High-Level Architecture
- **Backend:** Flask (Python), SQLAlchemy ORM, PostgreSQL
- **Frontend:** Jinja2 templates, Tailwind CSS, custom JS
- **AI Integration:** LLM service for content suggestions and automation
- **APIs:** RESTful endpoints for blog, LLM, and media
- **Utilities:** Scripts for migration, backup, and workflow automation

See the [System Architecture](architecture.md) for a detailed diagram and component breakdown. 