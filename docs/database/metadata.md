# JSON Metadata Documentation

## Overview
This document describes the JSON structures used for metadata across different models in the blog system. These structures provide flexible storage for various types of metadata while maintaining consistency and searchability.

## Post Metadata

### SEO Metadata
```json
{
  "seo": {
    "title": "string(70)",
    "description": "string(160)",
    "keywords": ["string"],
    "canonical_url": "string",
    "robots": "string",
    "og": {
      "title": "string(100)",
      "description": "string(200)",
      "image": "string(url)",
      "type": "article"
    },
    "twitter": {
      "card": "summary_large_image",
      "title": "string(100)",
      "description": "string(200)",
      "image": "string(url)"
    }
  }
}
```

### Publishing Metadata
```json
{
  "publishing": {
    "schedule": {
      "publish_at": "datetime",
      "unpublish_at": "datetime",
      "timezone": "string"
    },
    "syndication": {
      "platforms": ["medium", "dev.to", "hashnode"],
      "status": {
        "medium": "published",
        "dev.to": "draft",
        "hashnode": "scheduled"
      },
      "urls": {
        "medium": "string(url)",
        "dev.to": "string(url)",
        "hashnode": "string(url)"
      }
    },
    "visibility": {
      "is_public": true,
      "access_level": "all|subscribers|members",
      "password": "string|null"
    }
  }
}
```

### Analytics Metadata
```json
{
  "analytics": {
    "views": {
      "total": "integer",
      "unique": "integer",
      "by_date": {
        "YYYY-MM-DD": {
          "total": "integer",
          "unique": "integer"
        }
      }
    },
    "engagement": {
      "avg_time": "float",
      "scroll_depth": "float",
      "interactions": {
        "likes": "integer",
        "comments": "integer",
        "shares": "integer"
      }
    },
    "referrers": {
      "source": {
        "count": "integer",
        "percentage": "float"
      }
    }
  }
}
```

## Section Metadata

### Content Metadata
```json
{
  "content": {
    "type": "text|image|video|code|embed",
    "format": "markdown|html|plain",
    "language": "string",
    "version": "integer",
    "word_count": "integer",
    "reading_time": "integer"
  }
}
```

### LLM Context
```json
{
  "llm": {
    "model": "string",
    "prompt": "string",
    "temperature": "float",
    "max_tokens": "integer",
    "completion": {
      "tokens": "integer",
      "duration": "float",
      "finish_reason": "string"
    },
    "metadata": {
      "purpose": "string",
      "quality_score": "float",
      "iterations": "integer"
    }
  }
}
```

### Template Metadata
```json
{
  "template": {
    "id": "integer",
    "version": "integer",
    "variables": {
      "name": {
        "type": "string|number|boolean",
        "required": "boolean",
        "default": "any"
      }
    },
    "styling": {
      "css_class": "string",
      "custom_styles": {}
    }
  }
}
```

## Media Metadata

### EXIF Data
```json
{
  "exif": {
    "camera": {
      "make": "string",
      "model": "string",
      "serial": "string"
    },
    "settings": {
      "iso": "integer",
      "aperture": "float",
      "shutter_speed": "string",
      "focal_length": "float"
    },
    "datetime": {
      "original": "datetime",
      "digitized": "datetime"
    },
    "gps": {
      "latitude": "float",
      "longitude": "float",
      "altitude": "float"
    }
  }
}
```

### AI Generation Metadata
```json
{
  "ai": {
    "generator": {
      "model": "string",
      "version": "string",
      "provider": "string"
    },
    "prompt": {
      "text": "string",
      "negative": "string",
      "seed": "integer"
    },
    "parameters": {
      "steps": "integer",
      "cfg_scale": "float",
      "sampler": "string"
    },
    "output": {
      "width": "integer",
      "height": "integer",
      "format": "string"
    }
  }
}
```

### Processing Metadata
```json
{
  "processing": {
    "original": {
      "filename": "string",
      "size": "integer",
      "dimensions": {
        "width": "integer",
        "height": "integer"
      }
    },
    "versions": {
      "thumbnail": {
        "path": "string",
        "width": "integer",
        "height": "integer"
      },
      "watermarked": {
        "path": "string",
        "text": "string",
        "position": "string"
      }
    },
    "optimizations": {
      "quality": "integer",
      "size_reduction": "float",
      "format_conversion": "string"
    }
  }
}
```

## Usage Guidelines

### Querying JSON Fields
```sql
-- Search in SEO metadata
SELECT * FROM post 
WHERE metadata->'seo'->>'title' LIKE '%search%';

-- Filter by syndication status
SELECT * FROM post 
WHERE metadata->'publishing'->'syndication'->'status'->>'medium' = 'published';

-- Get posts with specific analytics
SELECT * FROM post 
WHERE (metadata->'analytics'->'views'->>'total')::int > 1000;
```

### Updating JSON Fields
```sql
-- Update SEO title
UPDATE post 
SET metadata = jsonb_set(
  metadata,
  '{seo,title}',
  '"New SEO Title"'::jsonb
);

-- Add new analytics data
UPDATE post 
SET metadata = jsonb_set(
  metadata,
  '{analytics,views,by_date,2025-04-23}',
  '{"total": 100, "unique": 75}'::jsonb
);
```

## Best Practices

### Schema Management
1. Validate JSON structure before saving
2. Use consistent types for values
3. Handle missing fields gracefully
4. Version metadata schemas

### Performance
1. Index frequently queried JSON paths
2. Minimize deep nesting
3. Use appropriate JSON operators
4. Cache complex queries

### Data Integrity
1. Validate required fields
2. Maintain data types
3. Handle schema migrations
4. Backup metadata regularly

### Security
1. Sanitize user input
2. Validate JSON structure
3. Control access to sensitive data
4. Encrypt sensitive values 