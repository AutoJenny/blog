# Blog Launchpad

A microservice for previewing and managing blog posts, designed to be the central hub for post publication and syndication.

## Overview

Blog Launchpad serves as the central control center for blog post management, providing:
- Post preview functionality
- Post listing and management
- Future: Social media syndication
- Future: Publishing readiness checks
- Future: Analytics and performance tracking

## Port Configuration

- **Port**: 5001
- **URL**: http://localhost:5001

## Features

### Current
- ✅ Post preview with content priority (polished > draft)
- ✅ Post listing with metadata
- ✅ Direct links to workflow editing
- ✅ Responsive design

### Planned
- 🔄 Social media syndication
- 🔄 Publishing readiness validation
- 🔄 Analytics dashboard
- 🔄 Multi-platform publishing

## API Endpoints

- `GET /` - Main launchpad page
- `GET /health` - Health check
- `GET /preview/<post_id>` - Preview specific post
- `GET /api/posts` - Get all posts

## Database

Shares the same PostgreSQL database as other blog microservices:
- `post` - Post metadata
- `post_development` - Development data
- `post_section` - Section content
- `image` - Image metadata

## Development

### Setup
```bash
cd blog-launchpad
pip install -r requirements.txt
python app.py
```

### Dependencies
- Flask
- psycopg2-binary
- requests
- python-dotenv
- humanize
- pytz

## Architecture

Blog Launchpad is designed as a standalone microservice that:
1. Reads from the shared database
2. Provides preview and management interfaces
3. Will integrate with external services for syndication
4. Maintains clean separation from the main workflow system

## Future Integration

This service is positioned to become the central hub for:
- Social media platforms (Twitter, Facebook, LinkedIn)
- Content syndication networks
- Analytics and performance tracking
- Publishing workflow management 