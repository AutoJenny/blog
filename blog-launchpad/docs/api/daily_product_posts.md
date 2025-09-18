# Daily Product Posts API Documentation

## Overview

The Daily Product Posts system is a comprehensive Facebook automation tool that generates, schedules, and manages product-focused social media content. It integrates AI-powered content generation with automated scheduling to create a streamlined posting workflow.

**Status**: ✅ **PRODUCTION READY** - Fully functional with AI integration  
**Last Updated**: 2025-01-27  
**Version**: 2.0

---

## System Architecture

### Core Components
1. **Product Selection** - Choose products from Clan.com inventory
2. **AI Content Generation** - Generate engaging post content using Ollama
3. **Posting Queue** - Manage scheduled posts with drag-and-drop interface
4. **Schedule Management** - Configure posting patterns and times
5. **Ollama Integration** - Automatic AI service management

### Database Schema
- **`posting_queue`** - Stores scheduled posts with content and metadata
- **`product_content_templates`** - AI prompt templates for different content types
- **`posting_schedules`** - Recurring schedule patterns
- **`products`** - Clan.com product data cache

---

## API Endpoints

### 1. Main Interface

#### Get Daily Product Posts Page
**Endpoint**: `GET /daily-product-posts`  
**Purpose**: Main interface for managing daily product posts  
**Response**: HTML page with accordion-based UI

#### Get Product Selection Page
**Endpoint**: `GET /daily-product-posts/select`  
**Purpose**: Product selection interface  
**Response**: HTML page for product selection

### 2. Product Management

#### Test Categories
**Endpoint**: `GET /api/daily-product-posts/test-categories`  
**Purpose**: Test category loading functionality  
**Response**: JSON with category data

#### Test Simple
**Endpoint**: `GET /api/daily-product-posts/test-simple`  
**Purpose**: Simple test endpoint  
**Response**: JSON with test data

#### Select Product
**Endpoint**: `POST /api/daily-product-posts/select-product`  
**Purpose**: Select a product for content generation  
**Request Body**:
```json
{
  "product_id": 123,
  "sku": "PROD-001"
}
```
**Response**:
```json
{
  "success": true,
  "product": {
    "id": 123,
    "name": "Product Name",
    "sku": "PROD-001",
    "price": "£29.99",
    "description": "Product description",
    "image_url": "https://example.com/image.jpg"
  }
}
```

#### Update Products
**Endpoint**: `POST /api/daily-product-posts/update-products`  
**Purpose**: Refresh product data from Clan.com  
**Request Body**:
```json
{
  "force_refresh": false
}
```
**Response**:
```json
{
  "success": true,
  "message": "Products updated successfully",
  "count": 150
}
```

### 3. Content Generation

#### Generate Content
**Endpoint**: `POST /api/daily-product-posts/generate-content`  
**Purpose**: Generate AI-powered content for selected product  
**Request Body**:
```json
{
  "product_id": 123,
  "content_type": "feature",
  "product_name": "Product Name",
  "product_description": "Product description",
  "product_price": "£29.99"
}
```
**Response**:
```json
{
  "success": true,
  "content": "Generated post content...",
  "content_type": "feature",
  "generation_time": "2025-01-27T10:30:00Z"
}
```

#### Start Ollama
**Endpoint**: `POST /api/daily-product-posts/start-ollama`  
**Purpose**: Start Ollama AI service  
**Response**:
```json
{
  "success": true,
  "message": "Ollama started successfully"
}
```

### 4. Queue Management

#### Get Queue
**Endpoint**: `GET /api/daily-product-posts/queue`  
**Purpose**: Get all items in the posting queue  
**Response**:
```json
{
  "success": true,
  "queue": [
    {
      "id": 1,
      "product_name": "Product Name",
      "sku": "PROD-001",
      "generated_content": "Post content...",
      "scheduled_time": "2025-01-28T17:00:00Z",
      "status": "pending"
    }
  ],
  "count": 1
}
```

#### Add to Queue
**Endpoint**: `POST /api/daily-product-posts/queue`  
**Purpose**: Add item to posting queue  
**Request Body**:
```json
{
  "product_id": 123,
  "content": "Post content...",
  "content_type": "feature"
}
```
**Response**:
```json
{
  "success": true,
  "item_id": 1,
  "message": "Item added to queue"
}
```

#### Update Queue Item
**Endpoint**: `PUT /api/daily-product-posts/queue/<int:item_id>`  
**Purpose**: Update existing queue item  
**Request Body**:
```json
{
  "content": "Updated post content...",
  "scheduled_time": "2025-01-28T18:00:00Z"
}
```
**Response**:
```json
{
  "success": true,
  "message": "Queue item updated"
}
```

#### Delete Queue Item
**Endpoint**: `DELETE /api/daily-product-posts/queue/<int:item_id>`  
**Purpose**: Remove item from queue  
**Response**:
```json
{
  "success": true,
  "message": "Queue item deleted"
}
```

#### Clear Queue
**Endpoint**: `DELETE /api/daily-product-posts/queue/clear`  
**Purpose**: Clear all items from queue  
**Response**:
```json
{
  "success": true,
  "message": "Queue cleared",
  "deleted_count": 5
}
```

#### Generate Batch
**Endpoint**: `POST /api/daily-product-posts/generate-batch`  
**Purpose**: Generate multiple queue items automatically  
**Request Body**:
```json
{
  "count": 10
}
```
**Response**:
```json
{
  "success": true,
  "generated_count": 10,
  "errors": [],
  "message": "Batch generation completed"
}
```

### 5. Schedule Management

#### Add Schedule
**Endpoint**: `POST /api/daily-product-posts/add-schedule`  
**Purpose**: Add new posting schedule  
**Request Body**:
```json
{
  "name": "Weekdays",
  "time": "17:00",
  "timezone": "GMT",
  "days": [1, 2, 3, 4, 5]
}
```
**Response**:
```json
{
  "success": true,
  "schedule_id": 1,
  "message": "Schedule added successfully"
}
```

#### Set Schedule
**Endpoint**: `POST /api/daily-product-posts/set-schedule`  
**Purpose**: Update existing schedule  
**Request Body**:
```json
{
  "schedule_id": 1,
  "time": "18:00",
  "days": [1, 2, 3, 4, 5, 6]
}
```
**Response**:
```json
{
  "success": true,
  "message": "Schedule updated successfully"
}
```

#### Clear Schedule
**Endpoint**: `POST /api/daily-product-posts/clear-schedule`  
**Purpose**: Clear all schedules  
**Response**:
```json
{
  "success": true,
  "message": "All schedules cleared"
}
```

#### Get Schedule Status
**Endpoint**: `GET /api/daily-product-posts/schedule-status`  
**Purpose**: Get current schedule status  
**Response**:
```json
{
  "success": true,
  "schedules": [
    {
      "id": 1,
      "name": "Weekdays",
      "time": "17:00",
      "timezone": "GMT",
      "days": [1, 2, 3, 4, 5],
      "is_active": true
    }
  ],
  "next_posts": [
    {
      "date": "2025-01-28",
      "time": "17:00",
      "schedule_name": "Weekdays"
    }
  ]
}
```

#### Get Schedules
**Endpoint**: `GET /api/daily-product-posts/schedules`  
**Purpose**: Get all schedules  
**Response**:
```json
{
  "success": true,
  "schedules": [
    {
      "id": 1,
      "name": "Weekdays",
      "time": "17:00",
      "timezone": "GMT",
      "days": [1, 2, 3, 4, 5],
      "is_active": true,
      "created_at": "2025-01-27T10:00:00Z"
    }
  ]
}
```

#### Delete Schedule
**Endpoint**: `DELETE /api/daily-product-posts/delete-schedule/<int:schedule_id>`  
**Purpose**: Delete specific schedule  
**Response**:
```json
{
  "success": true,
  "message": "Schedule deleted successfully"
}
```

#### Test Schedules
**Endpoint**: `GET /api/daily-product-posts/test-schedules`  
**Purpose**: Test schedule functionality  
**Response**: JSON with test schedule data

### 6. Status and Information

#### Get Categories
**Endpoint**: `GET /api/daily-product-posts/categories`  
**Purpose**: Get available product categories  
**Response**:
```json
{
  "success": true,
  "categories": [
    {
      "id": 1,
      "name": "Tartan",
      "count": 25
    },
    {
      "id": 2,
      "name": "Accessories",
      "count": 15
    }
  ]
}
```

#### Get Today Status
**Endpoint**: `GET /api/daily-product-posts/today-status`  
**Purpose**: Get today's posting status  
**Response**:
```json
{
  "success": true,
  "status": "draft",
  "last_post": null,
  "next_post": "2025-01-28T17:00:00Z",
  "queue_count": 5
}
```

#### Post Now
**Endpoint**: `POST /api/daily-product-posts/post-now`  
**Purpose**: Publish post immediately  
**Request Body**:
```json
{
  "content": "Post content...",
  "product_id": 123
}
```
**Response**:
```json
{
  "success": true,
  "post_id": "facebook_post_123",
  "message": "Post published successfully"
}
```

---

## Key Features

### 1. AI-Powered Content Generation
- **Ollama Integration**: Automatic AI service management
- **Content Types**: Feature, Benefit, and Story-focused posts
- **Template System**: Configurable prompt templates
- **Auto-Start**: Automatically starts Ollama if not running

### 2. Queue Management
- **Drag-and-Drop Interface**: Reorder posts visually
- **Batch Operations**: Generate multiple posts at once
- **Status Tracking**: Pending, Ready, Published, Failed
- **Time Slot Generation**: Automatic scheduling based on patterns

### 3. Schedule Management
- **Recurring Patterns**: Weekly, daily, custom schedules
- **Timezone Support**: Multiple timezone handling
- **Visual Calendar**: See upcoming posts at a glance
- **Bulk Scheduling**: Schedule multiple posts efficiently

### 4. Product Integration
- **Clan.com Sync**: Automatic product data updates
- **Category Filtering**: Filter products by category
- **Image Management**: Automatic product image handling
- **Price Display**: Current pricing information

### 5. User Interface
- **Accordion Layout**: Organized, collapsible sections
- **Real-Time Updates**: Live data without page refreshes
- **Responsive Design**: Works on all device sizes
- **Error Handling**: Clear feedback for all operations

---

## Error Handling

### Common Error Responses
```json
{
  "success": false,
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

### Error Codes
- `OLLAMA_NOT_RUNNING` - Ollama service not available
- `PRODUCT_NOT_FOUND` - Product not found in database
- `INVALID_SCHEDULE` - Invalid schedule configuration
- `QUEUE_FULL` - Queue has reached maximum capacity
- `GENERATION_FAILED` - AI content generation failed

---

## Integration Points

### Clan.com API
- **Product Data**: Fetches product information and images
- **Category Data**: Gets product categories and counts
- **Price Updates**: Syncs current pricing information

### Ollama AI Service
- **Content Generation**: Creates engaging post content
- **Template Processing**: Uses configured prompt templates
- **Auto-Management**: Starts/stops service as needed

### Facebook API (Future)
- **Post Publishing**: Will publish to Facebook when implemented
- **Scheduling**: Will use Facebook's scheduling API
- **Analytics**: Will track post performance

---

## Development Notes

### Recent Updates (2025-01-27)
- ✅ **Accordion UI**: Converted main panels to collapsible accordions
- ✅ **Ollama Integration**: Added automatic AI service management
- ✅ **Queue Display Fix**: Fixed timeline display issues
- ✅ **Include Templates**: Extracted reusable components
- ✅ **Error Handling**: Improved error messages and fallbacks

### Performance Optimizations
- **Timeout Management**: 10-second timeout for AI calls
- **Batch Processing**: 2-minute maximum for batch operations
- **Caching**: Product data caching for faster loading
- **Async Operations**: Non-blocking UI updates

### Security Considerations
- **Input Validation**: All inputs are validated and sanitized
- **SQL Injection Prevention**: Parameterized queries used
- **Error Information**: Sensitive data not exposed in errors
- **Rate Limiting**: Built-in protection against abuse

---

## Testing

### Manual Testing
```bash
# Test queue functionality
curl -X GET http://localhost:5001/api/daily-product-posts/queue

# Test content generation
curl -X POST http://localhost:5001/api/daily-product-posts/generate-content \
  -H "Content-Type: application/json" \
  -d '{"product_id": 123, "content_type": "feature"}'

# Test batch generation
curl -X POST http://localhost:5001/api/daily-product-posts/generate-batch \
  -H "Content-Type: application/json" \
  -d '{"count": 5}'
```

### Automated Testing
- Unit tests for all API endpoints
- Integration tests for Ollama connectivity
- UI tests for accordion functionality
- Performance tests for batch operations

---

## Future Enhancements

### Planned Features
- **Multi-Platform Support**: Instagram, Twitter, LinkedIn
- **Advanced Analytics**: Post performance tracking
- **A/B Testing**: Test different content variations
- **Team Collaboration**: Multi-user support
- **Content Calendar**: Visual calendar interface
- **Event Integration**: Holiday and event-based posting

### Technical Improvements
- **Database Optimization**: Improved query performance
- **Caching Layer**: Redis integration for faster responses
- **API Rate Limiting**: Protection against abuse
- **Monitoring**: Health checks and alerting
- **Documentation**: API documentation generation

---

**Document Status**: Production Ready  
**Last Updated**: 2025-01-27  
**Next Review**: After Social Media Command Center implementation
