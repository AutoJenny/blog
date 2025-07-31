# Blog Post Info Microservice

**Microservice that manages post metadata, designed to be embedded as an iframe within the main workflow interface.**

## ⚠️ CRITICAL: Iframe-Based Architecture

**This service is designed to work ONLY when embedded as an iframe within the main workflow interface:**

- **Main Workflow URL**: `http://localhost:5000/workflow/posts/1/planning/idea/initial_concept`
- **Iframe Embedding**: The main workflow embeds this service as an iframe with URL parameters
- **Required Parameters**: `stage`, `substage`, `step`, `post_id`
- **Direct Access**: Accessing `http://localhost:5004` directly will fail with missing parameters

### How It Works

1. **Main Workflow** (`http://localhost:5000/workflow/posts/1/planning/idea/initial_concept`) loads
2. **blog-core** embeds this service as an iframe with proper URL parameters when needed
3. **This service** receives context from URL parameters and initializes properly
4. **Direct access** to `http://localhost:5004` will fail because no parameters are provided

### Testing

**✅ CORRECT WAY TO TEST:**
```
http://localhost:5000/workflow/posts/1/planning/idea/initial_concept
```

**❌ INCORRECT WAY TO TEST:**
```
http://localhost:5004
```

## Overview

The `blog-post-info` microservice is responsible for managing post metadata, including titles, subtitles, descriptions, tags, categories, and SEO information. It provides a centralized API for post metadata operations and a web interface for managing this information.

## Port

**Port 5004**

## Features

### Current Features
- **Post Metadata Management**: CRUD operations for post titles, subtitles, descriptions
- **SEO Management**: Handle meta descriptions, keywords, and SEO optimization data
- **Tag & Category Management**: Manage post tags and categories
- **RESTful API**: Clean API endpoints for other microservices to consume
- **Web Dashboard**: User-friendly interface for viewing and editing post metadata

### Planned Features
- **Metadata Validation**: Ensure metadata meets SEO and publishing standards
- **Bulk Operations**: Update multiple posts' metadata at once
- **Metadata Templates**: Pre-defined metadata templates for different post types
- **Analytics Integration**: Track metadata performance and SEO metrics
- **Social Media Metadata**: Manage Open Graph and Twitter Card metadata

## API Endpoints

### Core Post Info
- `GET /api/post-info/<post_id>` - Get post metadata
- `PUT /api/post-info/<post_id>` - Update post metadata
- `GET /api/post-info` - List all posts with metadata

### SEO Operations
- `GET /api/post-info/<post_id>/seo` - Get SEO-specific metadata
- `PUT /api/post-info/<post_id>/seo` - Update SEO metadata

### Health & Status
- `GET /health` - Service health check
- `GET /` - Web dashboard

## Database Usage

### Tables Used
- **`post`**: Core post information (title, subtitle, summary, status)
- **`post_development`**: Extended metadata (main_title, intro_blurb, tags, categories, seo_optimization)

### Data Flow
1. **Read Operations**: Combines data from both `post` and `post_development` tables
2. **Write Operations**: Updates appropriate tables based on field type
3. **Validation**: Ensures data consistency across tables

## Architecture

### Microservice Responsibilities
- **blog-core** (Port 5000): Workflow UI and navigation
- **blog-launchpad** (Port 5001): Preview and publishing hub
- **blog-llm-actions** (Port 5002): LLM operations
- **blog-post-sections** (Port 5003): Section content management
- **blog-post-info** (Port 5004): Post metadata management ← **This Service**

### Integration Points
- **blog-core**: Workflow UI can fetch/update post metadata
- **blog-launchpad**: Preview system can display metadata
- **blog-post-sections**: Sections can reference post metadata
- **blog-llm-actions**: LLM operations can read/write metadata

## Development Setup

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Access to shared blog database

### Installation
```bash
cd blog-post-info
pip install -r requirements.txt
```

### Environment Variables
```bash
DATABASE_URL=postgresql://username@localhost/blog
SECRET_KEY=your-secret-key
PORT=5004
```

### Running the Service
```bash
python app.py
```

The service will be available at `http://localhost:5004`

## Data Migration

### From Legacy System
The service currently reads from existing `post_development` table fields:
- `main_title` → Post title
- `subtitle` → Post subtitle  
- `intro_blurb` → Post description
- `tags` → Post tags
- `categories` → Post categories
- `seo_optimization` → SEO metadata

### Future Migration
Planned migration to dedicated `post_info` table for cleaner separation of concerns.

## API Examples

### Get Post Metadata
```bash
curl http://localhost:5004/api/post-info/53
```

### Update Post Title
```bash
curl -X PUT http://localhost:5004/api/post-info/53 \
  -H "Content-Type: application/json" \
  -d '{"title": "New Post Title"}'
```

### Update SEO Metadata
```bash
curl -X PUT http://localhost:5004/api/post-info/53/seo \
  -H "Content-Type: application/json" \
  -d '{"tags": "scotland,history,culture", "seo_optimization": "SEO content here"}'
```

## Contributing

1. Follow the microservice architecture patterns
2. Maintain backward compatibility with existing database schema
3. Add comprehensive error handling and logging
4. Update this README when adding new features

## Future Roadmap

### Phase 1: Core Metadata (Current)
- Basic CRUD operations
- Web dashboard
- API endpoints

### Phase 2: Enhanced Features
- Metadata validation
- Bulk operations
- Templates system

### Phase 3: Advanced Features
- Analytics integration
- Social media metadata
- Performance optimization 