# Unified Queue API Reference

## Overview

The Unified Queue API provides a single, centralized interface for managing all social media posting queues. This API replaces the previous fragmented approach with separate endpoints for each content type.

**Base URL**: `/api/queue`  
**Version**: 1.0  
**Last Updated**: 2025-01-27

---

## Authentication

All endpoints require authentication. Include the session cookie in your requests.

---

## Endpoints

### GET /api/queue

Retrieve queue items with optional filtering.

**Query Parameters**:

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `content_type` | string | No | Filter by content type | `product`, `blog_post`, `event` |
| `platform` | string | No | Filter by platform | `facebook`, `instagram`, `twitter` |
| `channel_type` | string | No | Filter by channel | `feed_post`, `story`, `reel` |
| `status` | string | No | Filter by status | `pending`, `ready`, `published`, `failed` |
| `date_from` | date | No | Filter by scheduled date (from) | `2025-01-27` |
| `date_to` | date | No | Filter by scheduled date (to) | `2025-01-28` |
| `limit` | integer | No | Number of items to return (default: 50) | `20` |
| `offset` | integer | No | Number of items to skip (default: 0) | `40` |

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

**Error Responses**:

```json
{
  "success": false,
  "error": "Invalid content_type. Must be one of: product, blog_post, event",
  "code": "INVALID_CONTENT_TYPE"
}
```

---

### POST /api/queue

Add a new item to the queue.

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

**Required Fields**:
- `platform`: Platform name (facebook, instagram, etc.)
- `channel_type`: Channel type (feed_post, story, etc.)
- `content_type`: Content type (product, blog_post, etc.)
- `generated_content`: The content to post

**Optional Fields**:
- `product_id`: ID of the product (for product content)
- `section_id`: ID of the blog section (for blog content)
- `scheduled_date`: Date to schedule the post
- `scheduled_time`: Time to schedule the post
- `schedule_name`: Name of the schedule
- `timezone`: Timezone for scheduling
- `status`: Initial status (default: ready)

**Response**:

```json
{
  "success": true,
  "item_id": 456,
  "message": "Item added to queue successfully"
}
```

**Error Responses**:

```json
{
  "success": false,
  "error": "Missing required field: generated_content",
  "code": "VALIDATION_ERROR"
}
```

---

### PUT /api/queue/{item_id}

Update an existing queue item.

**Path Parameters**:
- `item_id` (integer): ID of the queue item to update

**Request Body**:

```json
{
  "generated_content": "Updated content",
  "scheduled_date": "2025-01-29",
  "scheduled_time": "18:00",
  "status": "ready"
}
```

**Updatable Fields**:
- `generated_content`: The content to post
- `scheduled_date`: Date to schedule the post
- `scheduled_time`: Time to schedule the post
- `schedule_name`: Name of the schedule
- `timezone`: Timezone for scheduling
- `status`: Current status
- `platform_post_id`: ID from social platform after posting
- `error_message`: Error message if posting failed

**Response**:

```json
{
  "success": true,
  "message": "Queue item updated successfully"
}
```

**Error Responses**:

```json
{
  "success": false,
  "error": "Queue item not found",
  "code": "ITEM_NOT_FOUND"
}
```

---

### DELETE /api/queue/{item_id}

Remove an item from the queue.

**Path Parameters**:
- `item_id` (integer): ID of the queue item to delete

**Response**:

```json
{
  "success": true,
  "message": "Queue item deleted successfully"
}
```

**Error Responses**:

```json
{
  "success": false,
  "error": "Queue item not found",
  "code": "ITEM_NOT_FOUND"
}
```

---

### DELETE /api/queue/clear

Clear all items from the queue with optional filtering.

**Query Parameters**:

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `content_type` | string | No | Only clear items of this type | `product` |
| `platform` | string | No | Only clear items for this platform | `facebook` |
| `status` | string | No | Only clear items with this status | `failed` |

**Example Requests**:

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

## Data Models

### Queue Item

```json
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
```

### Product Content Item

```json
{
  "id": 1,
  "platform": "facebook",
  "channel_type": "feed_post",
  "content_type": "product",
  "product_id": 123,
  "product_name": "Tartan Scarf",
  "product_image": "https://example.com/scarf.jpg",
  "sku": "SCARF-001",
  "price": "£29.99",
  "generated_content": "Check out this amazing product!",
  "status": "ready",
  "scheduled_timestamp": "2025-01-28T17:00:00Z"
}
```

### Blog Post Content Item

```json
{
  "id": 2,
  "platform": "facebook",
  "channel_type": "feed_post",
  "content_type": "blog_post",
  "post_id": 456,
  "post_title": "The Art of Scottish Storytelling",
  "section_id": 789,
  "section_title": "Introduction",
  "generated_content": "Discover the rich tradition of Scottish storytelling...",
  "status": "ready",
  "scheduled_timestamp": "2025-01-28T18:00:00Z"
}
```

---

## Status Values

| Status | Description |
|--------|-------------|
| `pending` | Item is waiting to be processed |
| `ready` | Item is ready to be posted |
| `published` | Item has been successfully posted |
| `failed` | Item failed to post |
| `cancelled` | Item was cancelled |

---

## Content Types

| Content Type | Description | Required Fields |
|--------------|-------------|-----------------|
| `product` | Product-focused content | `product_id` |
| `blog_post` | Blog post content | `post_id`, `section_id` |
| `event` | Event announcements | `event_id` |
| `announcement` | General announcements | None |

---

## Platform Values

| Platform | Description |
|----------|-------------|
| `facebook` | Facebook platform |
| `instagram` | Instagram platform |
| `twitter` | Twitter platform |
| `linkedin` | LinkedIn platform |

---

## Channel Types

| Channel Type | Description |
|--------------|-------------|
| `feed_post` | Regular feed post |
| `story` | Story post |
| `reel` | Reel post |
| `carousel` | Carousel post |

---

## Error Codes

| Code | Description |
|------|-------------|
| `INVALID_FILTER` | Invalid query parameter value |
| `ITEM_NOT_FOUND` | Queue item doesn't exist |
| `VALIDATION_ERROR` | Request body validation failed |
| `DATABASE_ERROR` | Database operation failed |
| `PERMISSION_DENIED` | User doesn't have permission |
| `INVALID_CONTENT_TYPE` | Invalid content type specified |
| `INVALID_PLATFORM` | Invalid platform specified |
| `INVALID_STATUS` | Invalid status specified |

---

## Rate Limiting

The API has the following rate limits:
- **Read Operations**: 100 requests per minute
- **Write Operations**: 50 requests per minute
- **Bulk Operations**: 10 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

---

## Examples

### Frontend Integration

#### JavaScript Fetch Example

```javascript
// Get all product items
async function getProductItems() {
  const response = await fetch('/api/queue?content_type=product');
  const data = await response.json();
  
  if (data.success) {
    console.log('Product items:', data.items);
  } else {
    console.error('Error:', data.error);
  }
}

// Add new item to queue
async function addToQueue(itemData) {
  const response = await fetch('/api/queue', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(itemData)
  });
  
  const data = await response.json();
  return data;
}

// Update queue item
async function updateQueueItem(itemId, updates) {
  const response = await fetch(`/api/queue/${itemId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updates)
  });
  
  const data = await response.json();
  return data;
}
```

#### jQuery Example

```javascript
// Get filtered items
$.get('/api/queue', {
  content_type: 'product',
  status: 'ready'
}, function(data) {
  if (data.success) {
    console.log('Items:', data.items);
  }
});

// Add item to queue
$.ajax({
  url: '/api/queue',
  method: 'POST',
  contentType: 'application/json',
  data: JSON.stringify({
    platform: 'facebook',
    channel_type: 'feed_post',
    content_type: 'product',
    product_id: 123,
    generated_content: 'Amazing product!'
  }),
  success: function(data) {
    console.log('Item added:', data.item_id);
  }
});
```

---

## Changelog

### Version 1.0 (2025-01-27)
- Initial release
- Unified API endpoints
- Comprehensive filtering
- Error handling
- Documentation

---

*This API reference is maintained by the Blog Launchpad development team. Last updated: 2025-01-27*
