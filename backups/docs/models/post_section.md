# PostSection Model Documentation

## Overview
The PostSection model represents a discrete section of content within a blog post. It is designed to support content repurposing across different platforms and formats, making it ideal for creating micro-content for social media platforms like TikTok, YouTube, and Instagram.

## Model Structure

### Core Fields
```python
id: Integer (Primary Key)
post_id: Integer (Foreign Key -> Post, with CASCADE delete)
title: String(200)
subtitle: String(200)
content: Text (Required)
position: Integer (Required, unique per post)
```

### Media Fields
```python
image_id: Integer (Foreign Key -> Image, with SET NULL on delete)
image: Relationship to Image model
video_url: String(500)
audio_url: String(500)
content_type: String(50) (Default: 'text')
duration: Integer (in seconds, for video/audio)
```

### Metadata Fields
```python
keywords: JSON
social_media_snippets: JSON
metadata: JSON
created_at: DateTime
updated_at: DateTime
```

### Database Indexes
- `idx_post_section_position`: Composite index on (post_id, position) for unique ordering
- `idx_post_section_content_type`: Index on content_type for filtering
- `idx_post_section_created`: Index on created_at for chronological queries

## Content Repurposing Features

### Social Media Integration
The `social_media_snippets` field stores platform-specific content versions:

```json
{
    "tiktok": {
        "caption": "Short, engaging caption",
        "hashtags": ["relevant", "tags"],
        "duration": 60,
        "background_music": "music_url",
        "talking_points": ["key point 1", "key point 2"]
    },
    "youtube": {
        "title": "SEO-optimized title",
        "description": "Detailed description",
        "tags": ["relevant", "tags"],
        "timestamp_markers": [
            {"time": 0, "description": "Intro"},
            {"time": 30, "description": "Main point"}
        ]
    },
    "instagram": {
        "caption": "Instagram-specific caption",
        "hashtags": ["relevant", "tags"],
        "carousel_images": ["url1", "url2"],
        "story_segments": ["segment1", "segment2"]
    }
}
```

### Metadata Structure
The `metadata` field can store additional information:

```json
{
    "ai_generated": {
        "model": "gpt-4",
        "prompt_id": "xyz",
        "confidence": 0.95
    },
    "seo": {
        "focus_keyword": "main topic",
        "readability_score": 85
    },
    "content_stats": {
        "complexity_level": "intermediate",
        "target_audience": ["beginners", "enthusiasts"]
    }
}
```

## Helper Methods

### Content Management
```python
to_dict(): Dict
    """Convert the section to a dictionary representation."""

get_social_media_content(platform: str) -> Dict
    """Retrieve platform-specific content."""

set_social_media_content(platform: str, content: Dict)
    """Store platform-specific content."""
```

### Properties
```python
has_media: bool
    """Check if the section has any media content."""

word_count: int
    """Get the word count of the content."""

reading_time: float
    """Estimate reading time in seconds."""
```

## Usage Examples

### Creating a New Section
```python
section = PostSection(
    post_id=1,
    title="Introduction to Scottish Tartans",
    subtitle="Understanding the history and significance",
    content="Detailed content here...",
    position=1,
    content_type="text",
    keywords=["tartan", "scotland", "history"],
)
```

### Adding Social Media Content
```python
section.set_social_media_content("tiktok", {
    "caption": "Discover the fascinating world of Scottish tartans! 🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "hashtags": ["ScottishHistory", "Tartan", "KiltCulture"],
    "duration": 60,
    "talking_points": [
        "Origin of tartans",
        "Clan significance",
        "Modern usage"
    ]
})
```

## Best Practices

1. **Content Organization**
   - Keep sections focused on a single topic or theme
   - Use clear, descriptive titles and subtitles
   - Maintain consistent section lengths for better content flow

2. **Media Management**
   - Store high-quality media assets
   - Include descriptive alt text and captions
   - Consider mobile-first viewing experience

3. **Social Media Optimization**
   - Adapt content style for each platform
   - Use platform-specific features and formats
   - Include relevant hashtags and keywords

4. **Metadata Management**
   - Keep SEO metadata current
   - Track content performance metrics
   - Document AI-generated content appropriately

## Future Considerations

The PostSection model is designed to be extensible for future content types and platforms:

1. **Additional Platforms**
   - LinkedIn articles
   - Twitter threads
   - Pinterest pins

2. **Enhanced Media Support**
   - 3D model integration
   - AR/VR content
   - Interactive elements

3. **Analytics Integration**
   - Platform-specific performance metrics
   - A/B testing results
   - Engagement tracking

4. **AI Integration**
   - Automated content repurposing
   - Smart content suggestions
   - Performance optimization 