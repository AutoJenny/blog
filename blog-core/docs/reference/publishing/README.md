# Blog Publishing System Documentation

## Overview

This directory contains documentation for the clan.com publishing system that has been ported from the legacy `blog_old` implementation. The system provides a complete pipeline for publishing blog posts with images to the clan.com website via their API.

## Documentation Structure

### Core Documentation
- **[clan_com_publishing_system.md](clan_com_publishing_system.md)** - Comprehensive guide to the clan.com publishing system
  - Architecture overview
  - API endpoints and configuration
  - Publishing process workflow
  - Error handling and troubleshooting
  - Integration requirements

### Legacy Documentation
- **[tech_briefing.md](tech_briefing.md)** - Original technical briefing from blog_old
  - Legacy system architecture
  - Component descriptions
  - Workflow processes

- **[publish_clan_help.md](publish_clan_help.md)** - Original user help documentation
  - Step-by-step publishing process
  - User interface guidance

## System Components

### Core Files
- `blog-core/scripts/post_to_clan.py` - Main publishing script (734 lines)
- `blog-core/legacy_app.py` - Legacy Flask integration with publishing endpoints

### Key Features
- **Complete API Integration** - clan.com createPost, editPost, uploadImage endpoints
- **Image Upload Pipeline** - Automatic image processing and URL rewriting
- **Content Processing** - HTML extraction and optimization
- **Status Tracking** - Workflow status management
- **Error Handling** - Comprehensive error handling and logging

## Integration Status

### ⚠️ IMPORTANT: Significant Updates Required

The legacy publishing system was designed for:
- **Eleventy (11ty)** static site generation
- **Markdown-based** content with front matter
- **Image library JSON** file management
- **Workflow status JSON** tracking

The current blog system uses:
- **Flask-based** dynamic content
- **PostgreSQL database** for content storage
- **Section-based** content structure
- **Different image handling** system

### Required Adaptations
1. **Content Source** - Convert database content to API format
2. **Build Process** - Replace Eleventy build with dynamic HTML generation
3. **Image Management** - Adapt to current image handling system
4. **Status Tracking** - Integrate with current workflow system
5. **Content Processing** - Update HTML extraction for current templates

## API Endpoints

### Clan.com API
- `POST https://clan.com/clan/blog_api/uploadImage` - Upload images
- `POST https://clan.com/clan/blog_api/createPost` - Create new posts
- `POST https://clan.com/clan/blog_api/editPost` - Edit existing posts

### Required Configuration
```bash
CLAN_API_BASE_URL=https://clan.com/clan/blog_api/
CLAN_API_USER=blog
CLAN_API_KEY=your_api_key_here
```

## Next Steps

1. **Analyze Current Architecture** - Understand content storage and management
2. **Design Integration Points** - Map legacy functionality to current system
3. **Create Content Adapters** - Convert database content to API format
4. **Implement Status Tracking** - Integrate with current workflow system
5. **Update Image Handling** - Adapt to current image management
6. **Test API Integration** - Verify clan.com API connectivity
7. **Create User Interface** - Build publishing controls in blog-launchpad

## Dependencies

### Python Dependencies
- `requests` - HTTP API calls
- `python-frontmatter` - Markdown front matter parsing
- `beautifulsoup4` - HTML parsing and manipulation
- `python-dotenv` - Environment variable management

## Security Considerations

- **API Key Management** - Store keys in environment variables
- **File Upload Security** - Validate file types and sizes
- **Content Validation** - Sanitize user-generated content

## Performance Considerations

- **Image Upload Optimization** - Compress images before upload
- **API Rate Limiting** - Respect clan.com API rate limits
- **Build Process Optimization** - Cache build artifacts

## Quick Start

1. **Review Documentation** - Start with `clan_com_publishing_system.md`
2. **Understand Architecture** - Read `tech_briefing.md` for legacy context
3. **Plan Integration** - Identify required adaptations for current system
4. **Test API Connectivity** - Verify clan.com API access
5. **Implement Core Features** - Start with content conversion and API calls

## Support

For questions about the publishing system:
1. Review the comprehensive documentation in `clan_com_publishing_system.md`
2. Check the legacy technical briefing in `tech_briefing.md`
3. Examine the original implementation in `blog-core/scripts/post_to_clan.py`
4. Review the legacy Flask integration in `blog-core/legacy_app.py`
