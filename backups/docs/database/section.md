# Section Table Documentation

## Overview
The `post_section` table represents discrete content blocks within a blog post. It's designed for content repurposing across different platforms and formats.

## Schema

### Core Fields
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | Primary Key | Unique identifier |
| `post_id` | Integer | Foreign Key (CASCADE) | Reference to parent post |
| `title` | String(200) | | Section heading |
| `subtitle` | String(200) | | Optional subheading |
| `content` | Text | Required | Main content |
| `position` | Integer | Required, Unique per post | Order within post |

### Media Fields
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `image_id` | Integer | Foreign Key (SET NULL) | Reference to image |
| `video_url` | String(500) | | External video link |
| `audio_url` | String(500) | | External audio link |
| `content_type` | String(50) | Default: 'text' | Content format |
| `duration` | Integer | | Media duration in seconds |

### Metadata Fields
| Field | Type | Description |
|-------|------|-------------|
| `keywords` | JSON | SEO and categorization |
| `social_media_snippets` | JSON | Platform-specific content |
| `section_metadata` | JSON | Additional metadata |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |

## Indexes
- `idx_post_section_position`: (post_id, position) - Unique ordering
- `idx_post_section_content_type`: content_type - Content filtering
- `idx_post_section_created`: created_at - Chronological queries

## JSON Structures

### Social Media Snippets
```json
{
    "tiktok": {
        "caption": "string",
        "hashtags": ["string"],
        "duration": "integer",
        "background_music": "string",
        "talking_points": ["string"]
    },
    "youtube": {
        "title": "string",
        "description": "string",
        "tags": ["string"],
        "timestamp_markers": [
            {"time": "integer", "description": "string"}
        ]
    },
    "instagram": {
        "caption": "string",
        "hashtags": ["string"],
        "carousel_images": ["string"],
        "story_segments": ["string"]
    }
}
```

### Section Metadata
```json
{
    "ai_generated": {
        "model": "string",
        "prompt_id": "string",
        "confidence": "float"
    },
    "seo": {
        "focus_keyword": "string",
        "readability_score": "integer"
    },
    "content_stats": {
        "complexity_level": "string",
        "target_audience": ["string"]
    }
}
```

## Relationships
- **Post**: Many-to-one (parent post)
- **Image**: Many-to-one (optional featured image)
- **Media**: Many-to-many (embedded media)

## Usage Examples

### Creating a Section
```python
section = PostSection(
    post_id=1,
    title="Introduction",
    content="Content here...",
    position=1,
    content_type="text",
    keywords=["keyword1", "keyword2"]
)
```

### Adding Social Media Content
```python
section.social_media_snippets = {
    "tiktok": {
        "caption": "Check this out!",
        "hashtags": ["trending", "viral"]
    }
}
```

## Best Practices
1. Keep sections focused on single topics
2. Use consistent section lengths
3. Include platform-specific metadata
4. Maintain proper position ordering
5. Use appropriate content types 