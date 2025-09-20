# Blog Launchpad Documentation

## Overview

Blog Launchpad is a comprehensive content management and social media automation platform with a unified queue system for managing all social media content.

**Version**: 2.0  
**Last Updated**: 2025-01-27

---

## Documentation Structure

### 📚 Core Documentation
- **[Unified Queue System](unified_queue_system.md)** - Central queue management system
- **[API Reference](api/unified_queue_api.md)** - Complete API documentation
- **[Database Schema](database/posting_queue_schema.md)** - Queue table structure
- **[Frontend Integration](frontend/integration_guide.md)** - Frontend development guides

---

## Quick Start

### For Developers
1. **Read the [Unified Queue System](unified_queue_system.md)** to understand the architecture
2. **Check the [API Reference](api/unified_queue_api.md)** for endpoint details
3. **Review the [Frontend Integration Guide](frontend/integration_guide.md)** for implementation

### For Frontend Developers
1. **Start with [Frontend Integration Guide](frontend/integration_guide.md)**
2. **Use [API Reference](api/unified_queue_api.md)** for data integration
3. **Check [Database Schema](database/posting_queue_schema.md)** for data structure

---

## System Architecture

### Core Principles
- **Unified Database**: Single table for all queue items
- **Filtered APIs**: One API with filtering capabilities
- **Centralized Management**: Command center for all content

### Key Components
1. **Posting Queue**: Central storage for all social media content
2. **Unified API**: Single endpoint system with filtering
3. **Frontend Pages**: Filtered views for different content types
4. **Command Center**: Centralized management interface

---

## API Endpoints

### Unified Queue System
- `GET /api/queue` - Get queue items with filtering
- `POST /api/queue` - Add new item to queue
- `PUT /api/queue/{id}` - Update queue item
- `DELETE /api/queue/{id}` - Delete queue item
- `DELETE /api/queue/clear` - Clear queue with filtering

---

## Database Schema

### Core Tables
- **`posting_queue`** - Central queue storage
- **`clan_products`** - Product data
- **`post`** - Blog post content
- **`post_section`** - Blog post sections
- **`daily_posts_schedule`** - Scheduling configuration

---

## Frontend Integration

### Page-Specific Filtering
- **Daily Product Posts**: `content_type=product`
- **Facebook Feed Post**: `content_type=blog_post`
- **Command Center**: All content types with advanced filtering

---

*This documentation is maintained by the Blog Launchpad development team.*