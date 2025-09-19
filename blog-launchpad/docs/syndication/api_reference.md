# Syndication API Reference

**Document Version**: 1.0  
**Created**: 2025-01-19  
**Status**: **IMPLEMENTED AND WORKING**  
**Author**: AI Assistant  
**Reviewer**: User  

---

## 🎯 **OVERVIEW**

This document provides a comprehensive reference for all syndication-related API endpoints, including the new automated selection system and progress tracking functionality.

---

## 📡 **AUTOMATED SELECTION API**

### **Get Next Section**
```http
GET /api/syndication/next-section
```

**Description**: Retrieves the next unprocessed section for syndication based on the automated selection algorithm.

**Query Parameters**:
- `platform_id` (integer, optional): Platform ID (default: 1 for Facebook)
- `channel_type_id` (integer, optional): Channel type ID (default: 1 for feed_post)
- `process_id` (integer, optional): Process ID (default: 1)

**Example Request**:
```http
GET /api/syndication/next-section?platform_id=1&channel_type_id=1&process_id=1
```

**Success Response** (200):
```json
{
  "status": "success",
  "next_section": {
    "post_id": 123,
    "post_title": "Celtic Storytelling Traditions",
    "post_created_at": "2025-01-19T10:30:00Z",
    "section_id": 456,
    "section_order": 2,
    "section_heading": "The Origins of Celtic Myths",
    "section_description": "Exploring the ancient roots of Celtic storytelling...",
    "platform_id": 1,
    "channel_type_id": 1,
    "process_id": 1,
    "status": "pending"
  }
}
```

**No Sections Response** (200):
```json
{
  "status": "success",
  "next_section": null,
  "message": "No unprocessed sections found"
}
```

**Error Response** (500):
```json
{
  "error": "Database connection failed"
}
```

---

## 🔄 **PROGRESS TRACKING API**

### **Mark Section as Processing**
```http
POST /api/syndication/mark-processing
```

**Description**: Marks a section as currently being processed to prevent duplicate processing.

**Request Body**:
```json
{
  "post_id": 123,
  "section_id": 456,
  "platform_id": 1,
  "channel_type_id": 1,
  "process_id": 1
}
```

**Required Fields**:
- `post_id` (integer): Blog post ID
- `section_id` (integer): Section ID within the post
- `platform_id` (integer): Platform ID
- `channel_type_id` (integer): Channel type ID

**Optional Fields**:
- `process_id` (integer): Process ID (default: 1)

**Success Response** (200):
```json
{
  "status": "success",
  "message": "Section marked as processing"
}
```

**Error Response** (400):
```json
{
  "error": "Missing required field: post_id"
}
```

### **Mark Section as Completed**
```http
POST /api/syndication/mark-completed
```

**Description**: Marks a section as successfully completed after syndication processing.

**Request Body**:
```json
{
  "post_id": 123,
  "section_id": 456,
  "platform_id": 1,
  "channel_type_id": 1,
  "process_id": 1
}
```

**Success Response** (200):
```json
{
  "status": "success",
  "message": "Section marked as completed"
}
```

### **Mark Section as Failed**
```http
POST /api/syndication/mark-failed
```

**Description**: Marks a section as failed with an error message for retry purposes.

**Request Body**:
```json
{
  "post_id": 123,
  "section_id": 456,
  "platform_id": 1,
  "channel_type_id": 1,
  "process_id": 1,
  "error_message": "LLM API timeout after 30 seconds"
}
```

**Required Fields**:
- `post_id` (integer): Blog post ID
- `section_id` (integer): Section ID within the post
- `platform_id` (integer): Platform ID
- `channel_type_id` (integer): Channel type ID
- `error_message` (string): Error description

**Success Response** (200):
```json
{
  "status": "success",
  "message": "Section marked as failed"
}
```

### **Get Progress Summary**
```http
GET /api/syndication/progress-summary
```

**Description**: Retrieves a summary of syndication progress across all or specific platform/channel combinations.

**Query Parameters**:
- `platform_id` (integer, optional): Filter by platform ID
- `channel_type_id` (integer, optional): Filter by channel type ID

**Example Request**:
```http
GET /api/syndication/progress-summary?platform_id=1&channel_type_id=1
```

**Success Response** (200):
```json
{
  "status": "success",
  "summary": {
    "total_sections_available": 150,
    "progress_by_status": [
      {
        "status": "completed",
        "count": 45,
        "completed_count": 45,
        "pending_count": 0,
        "processing_count": 0,
        "failed_count": 0
      },
      {
        "status": "pending",
        "count": 100,
        "completed_count": 0,
        "pending_count": 100,
        "processing_count": 0,
        "failed_count": 0
      },
      {
        "status": "failed",
        "count": 5,
        "completed_count": 0,
        "pending_count": 0,
        "processing_count": 0,
        "failed_count": 5
      }
    ]
  }
}
```

---

## 📝 **SYNDICATION PIECES API**

### **Get Syndication Pieces**
```http
GET /api/syndication/pieces
```

**Description**: Retrieves syndication pieces for a specific blog post.

**Query Parameters**:
- `post_id` (integer, required): Blog post ID

**Example Request**:
```http
GET /api/syndication/pieces?post_id=123
```

**Success Response** (200):
```json
{
  "status": "success",
  "pieces": [
    {
      "id": 789,
      "original_content": "Original blog section content...",
      "generated_content": "Generated social media content...",
      "parameters_used": {
        "platform": "Facebook",
        "channel_type": "feed_post",
        "requirements": "Facebook feed post requirements..."
      },
      "interaction_metadata": {
        "post_id": "123",
        "section_id": "456",
        "platform_id": "1",
        "channel_type_id": "1"
      },
      "created_at": "2025-01-19T10:30:00Z",
      "prompt_name": "Social Media Syndication",
      "prompt_description": "Convert blog content to social media posts"
    }
  ]
}
```

### **Create Syndication Piece**
```http
POST /api/syndication/pieces
```

**Description**: Creates a new syndication piece and stores it in the database.

**Request Body**:
```json
{
  "post_id": 123,
  "section_id": 456,
  "platform_id": 1,
  "channel_type_id": 1,
  "process_id": 1,
  "original_content": "Original blog section content...",
  "generated_content": "Generated social media content...",
  "llm_model": "mistral",
  "llm_temperature": "0.7",
  "llm_max_tokens": "1000",
  "llm_provider": "ollama",
  "processing_time_ms": 2500,
  "platform_name": "Facebook",
  "channel_type_name": "feed_post",
  "requirements": "Facebook feed post requirements...",
  "prompt_used": "Convert this blog section into a Facebook feed post..."
}
```

**Required Fields**:
- `post_id` (integer): Blog post ID
- `section_id` (integer): Section ID within the post
- `platform_id` (integer): Platform ID
- `channel_type_id` (integer): Channel type ID
- `process_id` (integer): Process ID
- `original_content` (string): Original blog content
- `generated_content` (string): Generated syndication content

**Success Response** (200):
```json
{
  "status": "success",
  "message": "Syndication piece saved successfully",
  "piece_id": 789,
  "action": "created"
}
```

---

## 📊 **POST SECTIONS API**

### **Get Post Sections**
```http
GET /api/syndication/post-sections/{post_id}
```

**Description**: Retrieves all sections for a specific blog post.

**Path Parameters**:
- `post_id` (integer): Blog post ID

**Example Request**:
```http
GET /api/syndication/post-sections/123
```

**Success Response** (200):
```json
{
  "status": "success",
  "sections": [
    {
      "id": 456,
      "post_id": 123,
      "section_order": 1,
      "section_heading": "Introduction to Celtic Myths",
      "section_description": "An overview of Celtic mythology...",
      "content": "Full section content...",
      "polished": "Polished section content...",
      "image_path": "/path/to/section/image.jpg",
      "image_dimensions": "1200x630"
    },
    {
      "id": 457,
      "post_id": 123,
      "section_order": 2,
      "section_heading": "The Origins of Celtic Myths",
      "section_description": "Exploring the ancient roots...",
      "content": "Full section content...",
      "polished": "Polished section content...",
      "image_path": "/path/to/section/image2.jpg",
      "image_dimensions": "1200x630"
    }
  ]
}
```

---

## 🔧 **ERROR HANDLING**

### **Common Error Responses**

#### **400 Bad Request**
```json
{
  "error": "Missing required field: post_id"
}
```

#### **404 Not Found**
```json
{
  "error": "Post not found"
}
```

#### **500 Internal Server Error**
```json
{
  "error": "Database connection failed"
}
```

### **Error Codes**
- **400**: Bad Request - Missing or invalid parameters
- **404**: Not Found - Resource doesn't exist
- **500**: Internal Server Error - Server-side error

---

## 🔐 **AUTHENTICATION**

Currently, the syndication API endpoints do not require authentication. This may be added in future versions for security purposes.

---

## 📈 **RATE LIMITING**

No rate limiting is currently implemented. Consider adding rate limiting for production use to prevent abuse.

---

## 🧪 **TESTING**

### **Test Endpoints**
Use the following test data for API testing:

```bash
# Get next section
curl "http://localhost:5001/api/syndication/next-section?platform_id=1&channel_type_id=1"

# Mark as processing
curl -X POST "http://localhost:5001/api/syndication/mark-processing" \
  -H "Content-Type: application/json" \
  -d '{"post_id": 1, "section_id": 1, "platform_id": 1, "channel_type_id": 1}'

# Get progress summary
curl "http://localhost:5001/api/syndication/progress-summary"
```

---

## 📚 **RELATED DOCUMENTATION**

- **Automated Selection System**: `/docs/syndication/automated_selection_system.md`
- **Database Schema**: `/docs/syndication/database_schema.md`
- **Frontend Integration**: `/docs/syndication/frontend_integration.md`

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-19  
**Status**: **IMPLEMENTED AND WORKING**  
**Next Review**: After adding authentication and rate limiting
