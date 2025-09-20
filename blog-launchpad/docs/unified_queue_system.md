# Unified Queue System Documentation

## Overview

The Unified Queue System provides a single, centralized API for managing all social media posting queues across different platforms, channels, and content types. This system replaces the previous fragmented approach with separate APIs for each content type.

**Status**: ✅ **DESIGNED** - Ready for implementation  
**Last Updated**: 2025-01-27  
**Version**: 1.0

---

## Architecture

### Core Principle
**Single Database Table + Filtered API Endpoints = Unified System**

All social media content (products, blog posts, etc.) is stored in a single `posting_queue` table and accessed through a unified API with filtering capabilities.

### Database Schema

#### `posting_queue` Table
```sql
CREATE TABLE posting_queue (
    id SERIAL PRIMARY KEY,
    product_id INTEGER,                    -- References clan_products(id) for products
    section_id INTEGER,                    -- References post_section(id) for blog posts
    platform VARCHAR(50) DEFAULT 'facebook',
    channel_type VARCHAR(50) DEFAULT 'feed_post',
    content_type VARCHAR(50) DEFAULT 'product',
    scheduled_date DATE,
    scheduled_time TIME,
    scheduled_timestamp TIMESTAMP,
    schedule_name VARCHAR(100),
    timezone VARCHAR(50),
    generated_content TEXT,
    queue_order INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'ready',
    platform_post_id VARCHAR(100),        -- ID from social platform after posting
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Filtering Fields
- **`platform`**: facebook, instagram, twitter, linkedin
- **`channel_type`**: feed_post, story, reel, carousel
- **`content_type`**: product, blog_post, event, announcement
- **`status`**: pending, ready, published, failed, cancelled
- **`scheduled_timestamp`**: For date range filtering

---

## API Endpoints

### Base URL
All queue operations use the unified endpoint: `/api/queue`

### 1. Get Queue Items
**Endpoint**: `GET /api/queue`  
**Purpose**: Retrieve queue items with optional filtering  
**Query Parameters**:
- `content_type` (optional): Filter by content type (product, blog_post, etc.)
- `platform` (optional): Filter by platform (facebook, instagram, etc.)
- `channel_type` (optional): Filter by channel (feed_post, story, etc.)
- `status` (optional): Filter by status (ready, published, failed, etc.)
- `date_from` (optional): Filter by scheduled date (YYYY-MM-DD)
- `date_to` (optional): Filter by scheduled date (YYYY-MM-DD)
- `limit` (optional): Number of items to return (default: 50)
- `offset` (optional): Number of items to skip (default: 0)

**Example Requests**:
```bash
# Get all items
GET /api/queue

# Get only product items
GET /api/queue?content_type=product

# Get ready blog posts
GET /api/queue?content_type=blog_post&status=ready

# Get items scheduled for today
GET /api/queue?date_from=2025-01-27&date_to=2025-01-27

# Get published items with pagination
GET /api/queue?status=published&limit=20&offset=40
```

**Response**:
```json
{
  "success": true,
  "items": [
    {
      "id": 1,
      "platform": "facebook",
      "channel_type": "feed_post",
      "content_type": "product",
      "status": "ready",
      "scheduled_timestamp": "2025-01-28T17:00:00Z",
      "generated_content": "Check out this amazing product!",
      "product_name": "Tartan Scarf",
      "product_image": "https://example.com/scarf.jpg",
      "sku": "SCARF-001",
      "price": "£29.99",
      "created_at": "2025-01-27T10:30:00Z",
      "updated_at": "2025-01-27T10:30:00Z"
    }
  ],
  "count": 1,
  "total": 150,
  "filters_applied": {
    "content_type": "product",
    "status": "ready"
  }
}
```

### 2. Add Queue Item
**Endpoint**: `POST /api/queue`  
**Purpose**: Add new item to the queue  
**Request Body**:
```json
{
  "platform": "facebook",
  "channel_type": "feed_post",
  "content_type": "product",
  "product_id": 123,
  "generated_content": "Amazing product content!",
  "scheduled_date": "2025-01-28",
  "scheduled_time": "17:00",
  "schedule_name": "Daily Posts",
  "timezone": "GMT",
  "status": "ready"
}
```

**Response**:
```json
{
  "success": true,
  "item_id": 456,
  "message": "Item added to queue successfully"
}
```

### 3. Update Queue Item
**Endpoint**: `PUT /api/queue/<int:item_id>`  
**Purpose**: Update existing queue item  
**Request Body**:
```json
{
  "generated_content": "Updated content",
  "scheduled_date": "2025-01-29",
  "scheduled_time": "18:00",
  "status": "ready"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Queue item updated successfully"
}
```

### 4. Delete Queue Item
**Endpoint**: `DELETE /api/queue/<int:item_id>`  
**Purpose**: Remove item from queue  
**Response**:
```json
{
  "success": true,
  "message": "Queue item deleted successfully"
}
```

### 5. Clear Queue
**Endpoint**: `DELETE /api/queue/clear`  
**Purpose**: Clear all items from queue (with optional filtering)  
**Query Parameters**:
- `content_type` (optional): Only clear items of this type
- `platform` (optional): Only clear items for this platform
- `status` (optional): Only clear items with this status

**Example**:
```bash
# Clear all items
DELETE /api/queue/clear

# Clear only product items
DELETE /api/queue/clear?content_type=product

# Clear only failed items
DELETE /api/queue/clear?status=failed
```

**Response**:
```json
{
  "success": true,
  "deleted_count": 25,
  "message": "Queue cleared successfully"
}
```

---

## Frontend Integration

### Page-Specific Filtering

#### Daily Product Posts Page
```javascript
// Load only product items
const response = await fetch('/api/queue?content_type=product&platform=facebook&channel_type=feed_post');
```

#### Facebook Feed Post Page
```javascript
// Load only blog post items
const response = await fetch('/api/queue?content_type=blog_post&platform=facebook&channel_type=feed_post');
```

#### Social Media Command Center
```javascript
// Load all items with advanced filtering
const response = await fetch('/api/queue?status=ready&date_from=2025-01-27&limit=50');
```

### Filtering UI Components

#### Status Filter
```html
<select id="status-filter">
  <option value="">All Statuses</option>
  <option value="pending">Pending</option>
  <option value="ready">Ready</option>
  <option value="published">Published</option>
  <option value="failed">Failed</option>
</select>
```

#### Content Type Filter
```html
<select id="content-type-filter">
  <option value="">All Content Types</option>
  <option value="product">Products</option>
  <option value="blog_post">Blog Posts</option>
  <option value="event">Events</option>
</select>
```

#### Date Range Filter
```html
<input type="date" id="date-from" placeholder="From Date">
<input type="date" id="date-to" placeholder="To Date">
```

---

## Migration Strategy

### Phase 1: Create Unified API
1. Create new unified endpoints (`/api/queue`)
2. Implement filtering logic
3. Add comprehensive error handling
4. Create API documentation

### Phase 2: Update Frontend Pages
1. Update Daily Product Posts page to use unified API
2. Update Facebook Feed Post page to use unified API
3. Update Social Media Command Center to use unified API
4. Add filtering UI components

### Phase 3: Deprecate Old APIs
1. Mark old endpoints as deprecated
2. Add deprecation warnings
3. Remove old endpoints after migration period

### Phase 4: Advanced Features
1. Add bulk operations
2. Implement advanced filtering
3. Add export functionality
4. Create analytics dashboard

---

## Benefits

### For Developers
- **Single API**: One set of endpoints to maintain
- **Consistent Interface**: Same patterns across all content types
- **Easy Filtering**: Powerful query parameter system
- **Unified Documentation**: One place for all API docs

### For Users
- **Centralized View**: See all content in one place
- **Advanced Filtering**: Find exactly what you need
- **Consistent Experience**: Same UI patterns everywhere
- **Real-time Updates**: Live status updates across all pages

### For System
- **Unified Database**: Single source of truth
- **Better Performance**: Optimized queries with proper indexing
- **Easier Maintenance**: One system to monitor and debug
- **Scalable Architecture**: Easy to add new platforms/content types

---

## Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "success": false,
  "error": "Invalid content_type. Must be one of: product, blog_post, event",
  "code": "INVALID_CONTENT_TYPE"
}
```

#### 404 Not Found
```json
{
  "success": false,
  "error": "Queue item not found",
  "code": "ITEM_NOT_FOUND"
}
```

#### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Database connection failed",
  "code": "DATABASE_ERROR"
}
```

### Error Codes
- `INVALID_FILTER`: Invalid query parameter value
- `ITEM_NOT_FOUND`: Queue item doesn't exist
- `VALIDATION_ERROR`: Request body validation failed
- `DATABASE_ERROR`: Database operation failed
- `PERMISSION_DENIED`: User doesn't have permission

---

## Testing

### Unit Tests
- Test all API endpoints
- Test filtering logic
- Test error handling
- Test data validation

### Integration Tests
- Test frontend integration
- Test database operations
- Test cross-platform compatibility
- Test performance with large datasets

### Manual Testing
- Test all filtering combinations
- Test UI responsiveness
- Test error scenarios
- Test real-world usage patterns

---

## Future Enhancements

### Planned Features
1. **Bulk Operations**: Select multiple items for batch actions
2. **Advanced Analytics**: Detailed reporting and insights
3. **Export Functionality**: Export queue data to CSV/Excel
4. **Real-time Updates**: WebSocket integration for live updates
5. **Mobile App**: Native mobile interface
6. **API Versioning**: Support for multiple API versions

### Potential Integrations
1. **Calendar Integration**: Sync with Google Calendar
2. **Slack Notifications**: Alert on posting status
3. **Analytics Platforms**: Integration with Google Analytics
4. **Content Management**: Advanced content editing tools
5. **Workflow Automation**: Automated approval processes

---

## Support

### Documentation
- API Reference: `/docs/api/queue-system.md`
- Frontend Guide: `/docs/frontend/integration.md`
- Database Schema: `/docs/database/posting_queue.md`

### Contact
- Technical Issues: Create GitHub issue
- Feature Requests: Submit enhancement proposal
- General Questions: Contact development team

---

*This documentation is maintained by the Blog Launchpad development team. Last updated: 2025-01-27*
