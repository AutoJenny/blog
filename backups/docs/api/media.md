# Media API

## Overview
The Media API provides endpoints for managing media assets, including image uploads, processing, and metadata management.

## Endpoints

### List Media
```http
GET /api/v1/media
```

#### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number |
| per_page | integer | Items per page |
| type | string | Filter by media type (image, video, etc.) |
| search | string | Search in title and metadata |
| sort | string | Sort field and direction |
| has_watermark | boolean | Filter by watermark status |

#### Response
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "filename": "image.jpg",
      "filepath": "/uploads/2025/04/image.jpg",
      "mimetype": "image/jpeg",
      "size": 1024567,
      "width": 1920,
      "height": 1080,
      "title": "Sample Image",
      "alt_text": "A beautiful landscape",
      "created_at": "2025-04-23T15:34:10Z",
      "updated_at": "2025-04-23T15:34:10Z",
      "urls": {
        "original": "/media/image.jpg",
        "thumbnail": "/media/image-thumb.jpg",
        "watermarked": "/media/image-watermark.jpg"
      }
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 10,
    "total": 100
  }
}
```

### Get Media
```http
GET /api/v1/media/{id}
```

#### Response
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "filename": "image.jpg",
    "filepath": "/uploads/2025/04/image.jpg",
    "mimetype": "image/jpeg",
    "size": 1024567,
    "width": 1920,
    "height": 1080,
    "format": "jpeg",
    "has_watermark": false,
    "title": "Sample Image",
    "alt_text": "A beautiful landscape",
    "caption": "Scenic mountain view",
    "credit": "John Doe",
    "created_at": "2025-04-23T15:34:10Z",
    "updated_at": "2025-04-23T15:34:10Z",
    "urls": {
      "original": "/media/image.jpg",
      "thumbnail": "/media/image-thumb.jpg",
      "watermarked": "/media/image-watermark.jpg"
    },
    "metadata": {
      "exif": {},
      "ai": {}
    }
  }
}
```

### Upload Media
```http
POST /api/v1/media
Content-Type: multipart/form-data
```

#### Request Body
```http
title: "Sample Image"
alt_text: "A beautiful landscape"
caption: "Scenic mountain view"
credit: "John Doe"
file: [binary data]
```

#### Response
```json
{
  "status": "success",
  "data": {
    "id": 2,
    "filename": "uploaded.jpg",
    // ... full media object
  }
}
```

### Update Media
```http
PUT /api/v1/media/{id}
```

#### Request Body
```json
{
  "title": "Updated Title",
  "alt_text": "Updated description",
  "caption": "New caption",
  "credit": "Jane Doe",
  "metadata": {
    "custom_field": "value"
  }
}
```

### Delete Media
```http
DELETE /api/v1/media/{id}
```

## Image Processing

### Create Watermark
```http
POST /api/v1/media/{id}/watermark
```

#### Request Body
```json
{
  "text": "© My Blog 2025",
  "position": "bottom-right",
  "opacity": 0.7,
  "size": 24
}
```

### Create Thumbnail
```http
POST /api/v1/media/{id}/resize
```

#### Request Body
```json
{
  "width": 300,
  "height": 200,
  "mode": "cover",
  "quality": 85
}
```

### Optimize Image
```http
POST /api/v1/media/{id}/optimize
```

#### Request Body
```json
{
  "quality": 85,
  "format": "webp",
  "strip_metadata": false
}
```

## Batch Operations

### Batch Upload
```http
POST /api/v1/media/batch
Content-Type: multipart/form-data
```

#### Request Body
```http
files[]: [binary data]
files[]: [binary data]
metadata: {
  "default_credit": "John Doe",
  "process_options": {
    "create_thumbnail": true,
    "optimize": true
  }
}
```

### Batch Process
```http
POST /api/v1/media/batch/process
```

#### Request Body
```json
{
  "media_ids": [1, 2, 3],
  "operations": [
    {
      "type": "watermark",
      "params": {
        "text": "© My Blog 2025"
      }
    },
    {
      "type": "optimize",
      "params": {
        "quality": 85
      }
    }
  ]
}
```

## Error Responses

### Upload Error
```json
{
  "status": "error",
  "error": {
    "code": "UPLOAD_ERROR",
    "message": "File upload failed",
    "details": {
      "size": "File too large",
      "type": "Invalid file type"
    }
  }
}
```

### Processing Error
```json
{
  "status": "error",
  "error": {
    "code": "PROCESSING_ERROR",
    "message": "Image processing failed",
    "details": {
      "operation": "watermark",
      "reason": "Invalid parameters"
    }
  }
}
```

## Best Practices

### File Management
1. Validate file types
2. Check file sizes
3. Use secure filenames
4. Implement cleanup

### Image Processing
1. Preserve originals
2. Cache processed versions
3. Use appropriate formats
4. Optimize for web

### Metadata
1. Extract EXIF data
2. Validate metadata
3. Preserve attribution
4. Update timestamps

### Performance
1. Use chunked uploads
2. Process async
3. Cache results
4. Clean unused files

### Security
1. Validate file types
2. Scan for malware
3. Control access
4. Protect originals

## Usage Examples

### Basic Upload
```bash
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -F "file=@image.jpg" \
     -F "title=My Image" \
     https://api.blog.com/v1/media
```

### Process Image
```bash
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"text": "© 2025", "position": "bottom-right"}' \
     https://api.blog.com/v1/media/1/watermark
```

### Batch Upload
```bash
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -F "files[]=@image1.jpg" \
     -F "files[]=@image2.jpg" \
     -F 'metadata={"default_credit":"John Doe"}' \
     https://api.blog.com/v1/media/batch
``` 