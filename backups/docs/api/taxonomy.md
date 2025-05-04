# Taxonomy API

## Overview
The Taxonomy API provides endpoints for managing categories and tags, enabling content organization and classification.

## Category Endpoints

### List Categories
```http
GET /api/v1/categories
```

#### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number |
| per_page | integer | Items per page |
| parent_id | integer | Filter by parent category |
| search | string | Search in name and description |
| sort | string | Sort field and direction |

#### Response
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "Technology",
      "slug": "tech",
      "description": "Tech-related posts",
      "parent_id": null,
      "post_count": 42,
      "created_at": "2025-04-23T15:34:10Z",
      "updated_at": "2025-04-23T15:34:10Z",
      "children": [
        {
          "id": 2,
          "name": "Programming",
          "slug": "programming",
          "parent_id": 1
        }
      ]
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 10,
    "total": 100
  }
}
```

### Get Category
```http
GET /api/v1/categories/{slug}
```

#### Response
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "name": "Technology",
    "slug": "tech",
    "description": "Tech-related posts",
    "parent_id": null,
    "metadata": {
      "seo": {
        "title": "Technology Blog Posts",
        "description": "Latest tech articles"
      }
    },
    "created_at": "2025-04-23T15:34:10Z",
    "updated_at": "2025-04-23T15:34:10Z",
    "children": [],
    "posts": [
      {
        "id": 1,
        "title": "Sample Post",
        "slug": "sample-post"
      }
    ]
  }
}
```

### Create Category
```http
POST /api/v1/categories
```

#### Request Body
```json
{
  "name": "New Category",
  "slug": "new-category",
  "description": "Category description",
  "parent_id": 1,
  "metadata": {
    "seo": {
      "title": "SEO Title",
      "description": "SEO Description"
    }
  }
}
```

### Update Category
```http
PUT /api/v1/categories/{slug}
```

#### Request Body
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "parent_id": 2,
  "metadata": {
    "seo": {
      "title": "Updated SEO Title"
    }
  }
}
```

### Delete Category
```http
DELETE /api/v1/categories/{slug}
```

### Get Category Tree
```http
GET /api/v1/categories/tree
```

#### Response
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "Technology",
      "slug": "tech",
      "children": [
        {
          "id": 2,
          "name": "Programming",
          "slug": "programming",
          "children": []
        }
      ]
    }
  ]
}
```

## Tag Endpoints

### List Tags
```http
GET /api/v1/tags
```

#### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number |
| per_page | integer | Items per page |
| search | string | Search in name |
| sort | string | Sort field and direction |
| min_posts | integer | Minimum post count |

#### Response
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "Python",
      "slug": "python",
      "description": "Python programming",
      "post_count": 15,
      "created_at": "2025-04-23T15:34:10Z",
      "updated_at": "2025-04-23T15:34:10Z"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 10,
    "total": 100
  }
}
```

### Get Tag
```http
GET /api/v1/tags/{slug}
```

#### Response
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "name": "Python",
    "slug": "python",
    "description": "Python programming",
    "metadata": {
      "seo": {
        "title": "Python Programming Posts",
        "description": "Articles about Python"
      }
    },
    "created_at": "2025-04-23T15:34:10Z",
    "updated_at": "2025-04-23T15:34:10Z",
    "posts": [
      {
        "id": 1,
        "title": "Python Tips",
        "slug": "python-tips"
      }
    ]
  }
}
```

### Create Tag
```http
POST /api/v1/tags
```

#### Request Body
```json
{
  "name": "New Tag",
  "slug": "new-tag",
  "description": "Tag description",
  "metadata": {
    "seo": {
      "title": "SEO Title",
      "description": "SEO Description"
    }
  }
}
```

### Update Tag
```http
PUT /api/v1/tags/{slug}
```

#### Request Body
```json
{
  "name": "Updated Tag",
  "description": "Updated description",
  "metadata": {
    "seo": {
      "title": "Updated SEO Title"
    }
  }
}
```

### Delete Tag
```http
DELETE /api/v1/tags/{slug}
```

### Merge Tags
```http
POST /api/v1/tags/merge
```

#### Request Body
```json
{
  "source_tags": ["tag1", "tag2"],
  "target_tag": "main-tag"
}
```

## Batch Operations

### Batch Create Tags
```http
POST /api/v1/tags/batch
```

#### Request Body
```json
{
  "tags": [
    {
      "name": "Tag 1",
      "description": "Description 1"
    },
    {
      "name": "Tag 2",
      "description": "Description 2"
    }
  ]
}
```

### Batch Delete
```http
POST /api/v1/tags/batch-delete
```

#### Request Body
```json
{
  "slugs": ["tag1", "tag2", "tag3"]
}
```

## Error Responses

### Not Found
```json
{
  "status": "error",
  "error": {
    "code": "TAXONOMY_NOT_FOUND",
    "message": "Category/Tag not found"
  }
}
```

### Validation Error
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "name": ["Name is required"],
      "slug": ["Slug already exists"]
    }
  }
}
```

## Best Practices

### Category Management
1. Maintain hierarchy integrity
2. Handle orphaned categories
3. Update post counts
4. Validate parent relationships

### Tag Management
1. Normalize tag names
2. Handle synonyms
3. Maintain consistency
4. Track usage statistics

### Performance
1. Cache taxonomy trees
2. Batch operations
3. Index search fields
4. Optimize queries

### Security
1. Validate input
2. Check permissions
3. Sanitize metadata
4. Protect operations

## Usage Examples

### Create Category
```bash
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "New Category", "description": "Description"}' \
     https://api.blog.com/v1/categories
```

### Update Tag
```bash
curl -X PUT \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "Updated Tag", "description": "New description"}' \
     https://api.blog.com/v1/tags/tag-slug
```

### Get Category Tree
```bash
curl -H "Authorization: Bearer <token>" \
     https://api.blog.com/v1/categories/tree
``` 