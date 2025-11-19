# Newsletter Feature Block

## Overview

The Feature block highlights a recent blog post from the site.

**Purpose**: Showcase latest published blog post with hero image

**Status**: ✅ Implemented

## Data Sources

- Latest published blog post from `post` table
- Requires: `status='published'` and `header_image_id` (hero image)

## Payload Structure

```json
{
  "id": 123,
  "title": "Post title",
  "url": "/posts/slug",
  "excerpt": "Post summary",
  "hero_image": "/path/to/image.jpg"
}
```

## Files

- `blog-core/newsletter/selectors/blog_feature.py` - Selects latest published post
- Uses universal block editor UI

## API Endpoints

Same as intro block (shared endpoints).

