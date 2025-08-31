# Social Media Syndication Framework Proposal

**Date**: August 31, 2025  
**Status**: Temporary Documentation  
**Purpose**: Framework design for channel-neutral social media posting system

## Table of Contents
1. [Current Architecture Analysis](#current-architecture-analysis)
2. [Proposed Channel-Neutral Framework](#proposed-channel-neutral-framework)
3. [UI Design Specifications](#ui-design-specifications)
4. [Backend Architecture](#backend-architecture)
5. [Database Extensions](#database-extensions)
6. [Key Benefits](#key-benefits)
7. [Implementation Phases](#implementation-phases)

---

## Current Architecture Analysis

### Existing Structure
1. **Generic Route**: `/syndication/<platform_name>/<channel_type>` - Handles any platform/channel combination
2. **Facebook Specific**: `/syndication/facebook/feed-post` - Redirects to generic route
3. **Database Schema**: Uses `platforms`, `channel_types`, `content_processes`, `process_configurations`, and `channel_requirements` tables
4. **Template**: Currently uses `facebook_feed_post_config.html` for all platforms

### Current Strengths
- ✅ **Platform Agnostic**: Generic routing system already exists
- ✅ **Database Normalization**: Well-structured schema for platforms and channels
- ✅ **Requirements System**: `channel_requirements` table for platform-specific needs
- ✅ **Process Management**: Content processes with configurations and execution tracking

---

## Proposed Channel-Neutral Framework for Social Media Posting

### 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Syndication Dashboard                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Facebook  │ │   Twitter   │ │  LinkedIn   │          │
│  │  ┌───────┐  │ │  ┌───────┐  │ │  ┌───────┐  │          │
│  │  │Feed   │  │ │  │Tweet  │  │ │  │Article│  │          │
│  │  │Post   │  │ │  │       │  │ │  │       │  │          │
│  │  └───────┘  │ │  └───────┘  │ │  └───────┘  │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                Channel-Neutral Post Builder                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Content Selection                      │   │
│  │  • Post Selection (from Clan.com published)        │   │
│  │  • Image Selection (header + section images)       │   │
│  │  • Text Generation (AI-powered captions)           │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Platform-Specific Formatting             │   │
│  │  • Facebook: /photos endpoint, caption + image     │   │
│  │  • Twitter: /tweets endpoint, text + media        │   │
│  │  • LinkedIn: /ugcPosts endpoint, article + image  │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┘   │
│  │              Scheduling & Publishing                │   │
│  │  • Immediate publish vs. scheduled                 │   │
│  │  • Batch operations for series                     │   │
│  │  • Error handling & retry logic                    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## UI Design Specifications

### A. Content Selection Section
```
┌─────────────────────────────────────────────────────────────┐
│ 📝 Content Selection                                        │
├─────────────────────────────────────────────────────────────┤
│ [🔍 Search Posts] [📅 Filter by Date] [🏷️ Filter by Tags] │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Selected Post: "The Art of Scottish Storytelling..."   │ │
│ │ 📖 Summary: Discover the captivating tales...          │ │
│ │ 🖼️ Header Image: ✅ Available                          │ │
│ │ 📸 Section Images: 3 available                         │ │
│ │ 🔗 Clan.com URL: https://clan.com/blog/...            │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### B. Post Configuration Section
```
┌─────────────────────────────────────────────────────────────┐
│ ✏️ Post Configuration                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Caption Template:                                           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ {hook_question} {key_insight} {call_to_action}         │ │
│ │ {blog_url}                                              │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ AI-Generated Caption:                                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Did you know Scotland's storytelling traditions...     │ │
│ │ Discover the captivating tales that shaped...          │ │
│ │ Read more: https://clan.com/blog/...                   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [✏️ Edit Caption] [🤖 Regenerate with AI]                │
└─────────────────────────────────────────────────────────────┘
```

### C. Image & Media Section
```
┌─────────────────────────────────────────────────────────────┐
│ 🖼️ Media Selection                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Primary Image:                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [🖼️ Header Image] [📸 Section 1] [📸 Section 2]      │ │
│ │                                                         │ │
│ │ Preview: [Image Preview]                                │ │
│ │ Size: 1200×630 px ✅                                    │ │
│ │ Format: JPEG ✅                                          │ │
│ │ File Size: 2.1 MB ✅                                    │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [📤 Upload Custom Image] [🎨 Edit Image]                  │
└─────────────────────────────────────────────────────────────┘
```

### D. Publishing & Scheduling Section
```
┌─────────────────────────────────────────────────────────────┐
│ 🚀 Publishing Options                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Publish Mode:                                               │
│ ○ Publish Now                                              │
│ ● Schedule for Later                                       │
│ ○ Save as Draft                                            │
│                                                             │
│ Schedule Settings:                                          │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 📅 Date: [2025-01-31]                                  │ │
│ │ 🕐 Time: [14:30]                                        │ │
│ │ 🌍 Timezone: [UTC]                                      │ │
│ │ Unix Timestamp: 1735670400                              │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [📚 Add to Series] [📤 Test Post] [🚀 Publish]            │
└─────────────────────────────────────────────────────────────┘
```

---

## Backend Architecture

### A. Core Classes

```python
class SocialMediaPostBuilder:
    """Channel-neutral post builder for all platforms"""
    
    def __init__(self, platform_name, channel_type):
        self.platform = platform_name
        self.channel = channel_type
        self.post_data = None
        self.media_data = None
        
    def select_post(self, post_id):
        """Select a post from Clan.com published posts"""
        
    def generate_caption(self, template_type="engagement"):
        """Generate platform-optimized caption using AI"""
        
    def prepare_media(self, image_type="header"):
        """Prepare media for platform requirements"""
        
    def build_payload(self):
        """Build platform-specific API payload"""
        
    def validate_payload(self):
        """Validate against platform requirements"""
        
    def schedule_post(self, publish_time):
        """Schedule post for later publication"""
        
    def publish_now(self):
        """Publish post immediately"""

class FacebookPostBuilder(SocialMediaPostBuilder):
    """Facebook-specific post builder"""
    
    def build_payload(self):
        """Build Facebook /photos endpoint payload"""
        return {
            "caption": self.caption + " " + self.blog_url,
            "url": self.image_url,
            "published": False,
            "scheduled_publish_time": self.publish_timestamp
        }
    
    def validate_payload(self):
        """Validate Facebook-specific requirements"""
        # Check image dimensions, file size, caption length
        # Validate scheduled time (≥10 min from now)
```

### B. API Endpoints

```python
# Post Builder API
@app.route('/api/syndication/post-builder/<platform>/<channel>', methods=['POST'])
def build_social_post(platform, channel):
    """Build a social media post for any platform/channel"""

# Content Selection API
@app.route('/api/syndication/available-posts', methods=['GET'])
def get_available_posts():
    """Get posts available for syndication"""

# Caption Generation API
@app.route('/api/syndication/generate-caption', methods=['POST'])
def generate_caption():
    """Generate AI-powered caption for social media"""

# Publishing API
@app.route('/api/syndication/publish/<platform>/<channel>', methods=['POST'])
def publish_social_post(platform, channel):
    """Publish post to social media platform"""

# Scheduling API
@app.route('/api/syndication/schedule/<platform>/<channel>', methods=['POST'])
def schedule_social_post(platform, channel):
    """Schedule post for later publication"""
```

---

## Database Extensions

### A. New Tables

```sql
-- Social media posts table
CREATE TABLE social_media_posts (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id),
    platform_name VARCHAR(50),
    channel_type VARCHAR(50),
    caption TEXT,
    media_urls TEXT[],
    publish_status VARCHAR(20), -- 'draft', 'scheduled', 'published', 'failed'
    scheduled_time TIMESTAMP,
    published_time TIMESTAMP,
    platform_post_id VARCHAR(100), -- ID returned by platform
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Post series table for batch operations
CREATE TABLE post_series (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    description TEXT,
    platform_name VARCHAR(50),
    channel_type VARCHAR(50),
    posts JSONB, -- Array of post configurations
    schedule_pattern JSONB, -- Cron-like scheduling
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Key Benefits of This Framework

### A. Channel Neutrality
- **Single Interface**: One UI for all platforms
- **Consistent Workflow**: Same process regardless of platform
- **Easy Extension**: Add new platforms without UI changes

### B. AI Integration
- **Smart Captions**: AI-generated, platform-optimized text
- **Content Adaptation**: Automatically adjust for platform requirements
- **Engagement Optimization**: Data-driven caption strategies

### C. Scalability
- **Batch Operations**: Schedule multiple posts in series
- **Template System**: Reusable caption and media templates
- **Error Handling**: Robust retry and failure management

### D. Platform Compliance
- **Requirement Validation**: Automatic checking against platform rules
- **Media Optimization**: Automatic image resizing and format conversion
- **API Compliance**: Platform-specific payload building

---

## Implementation Phases

### Phase 1: Core Framework
- Basic post builder interface
- Facebook integration
- Content selection from Clan.com

### Phase 2: AI Enhancement
- Caption generation
- Content optimization
- Engagement prediction

### Phase 3: Multi-Platform
- Twitter integration
- LinkedIn integration
- Cross-platform scheduling

### Phase 4: Advanced Features
- Series management
- Analytics dashboard
- A/B testing

---

## Facebook API Requirements

Based on the provided Facebook API specification:

### Endpoint
```
POST https://graph.facebook.com/{PAGE_ID}/photos
```

### Payload Structure
```json
{
  "caption": "<your unique caption text> <your blog URL>",
  "url": "https://yourcdn.com/path/to/unique-image.jpg",
  "published": true,
  "access_token": "PAGE_ACCESS_TOKEN",
  "published": false,
  "scheduled_publish_time": 1735670400
}
```

### Key Notes
- Use `/photos` (not `/feed`) to control the image per post
- Put the blog URL inside caption so it's clickable
- Image formats: JPEG/PNG/GIF (GIF shows first frame)
- Size ≤ ~25 MB; recommended 1200×630 px
- Repeat one request per post (each with a new caption and new image url/source)

---

## Next Steps

1. **Review and refine** this framework proposal
2. **Implement Phase 1** with Facebook integration
3. **Create database schema** for social media posts
4. **Build UI components** for post builder interface
5. **Integrate with existing** Clan.com publishing system

---

**Document Status**: Temporary - For review and discussion  
**Last Updated**: August 31, 2025  
**Author**: AI Assistant  
**Review Required**: Yes
