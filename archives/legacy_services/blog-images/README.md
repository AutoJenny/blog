# Blog Images - Image Generation and Management

**Microservice that handles image generation and processing, designed to be embedded as an iframe within the main workflow interface.**

## ⚠️ CRITICAL: Iframe-Based Architecture

**This service is designed to work ONLY when embedded as an iframe within the main workflow interface:**

- **Main Workflow URL**: `http://localhost:5000/workflow/posts/1/planning/idea/initial_concept`
- **Iframe Embedding**: The main workflow embeds this service as an iframe with URL parameters
- **Required Parameters**: `stage`, `substage`, `step`, `post_id`
- **Direct Access**: Accessing `http://localhost:5005` directly will fail with missing parameters

### How It Works

1. **Main Workflow** (`http://localhost:5000/workflow/posts/1/planning/idea/initial_concept`) loads
2. **blog-core** embeds this service as an iframe with proper URL parameters when needed
3. **This service** receives context from URL parameters and initializes properly
4. **Direct access** to `http://localhost:5005` will fail because no parameters are provided

### Testing

**✅ CORRECT WAY TO TEST:**
```
http://localhost:5000/workflow/posts/1/planning/idea/initial_concept
```

**❌ INCORRECT WAY TO TEST:**
```
http://localhost:5005
```

## Overview
The blog-images project handles all image generation, processing, and management for the blog system. It supports multiple LLM providers, social media syndication, and automated image optimization workflows.

## Directory Structure Principles

### Core Principles
1. **Separation of Concerns**: Clear distinction between raw, optimized, social, and web versions
2. **Scalability**: Structure supports multiple content channels beyond just blog posts
3. **Error Handling**: Dedicated directories for failed generations and processing errors
4. **Future-Proofing**: Extensible structure for new platforms and content types
5. **Processing Pipeline**: Organized workflow from upload to final delivery
6. **Version Control Ready**: Structure supports image versioning and rollbacks

### File Organization Strategy
- **Entity-Based**: Content organized by post → section → image type
- **Stage-Based**: Each image type has raw → optimized → platform-specific versions
- **Platform-Agnostic**: Social media directories created on-demand
- **Error-Resilient**: Failed generations and processing errors are tracked separately

## Directory Structure

```
blog-images/static/
├── uploads/                           # Initial uploads (temporary staging)
│   └── images/                        # Generated and uploaded images
│       └── section_<id>_<timestamp>_<hash>.png
├── content/                           # Organized content by entity
│   ├── posts/                         # Blog post images
│   │   └── {post_id}/
│   │       ├── sections/              # Section-specific images
│   │       │   └── {section_id}/      # Uses actual DB section ID (e.g., 710, not section_710)
│   │       │       ├── raw/           # Original images (preserved)
│   │       │       ├── optimized/     # Web-optimized versions
│   │       │       ├── social/        # Platform-specific versions
│   │       │       │   ├── instagram/ # Square, Stories, Reels formats
│   │       │       │   ├── twitter/   # Landscape, Square formats
│   │       │       │   ├── linkedin/  # Professional formats
│   │       │       │   ├── tiktok/    # Vertical video formats
│   │       │       │   └── youtube/   # Various video formats
│   │       │       ├── web/           # Blog/web display versions
│   │       │       ├── failed/        # Failed generations
│   │       │       └── archive/       # Processing intermediates
│   │       ├── header/                # Post header images
│   │       │   ├── raw/
│   │       │   ├── optimized/
│   │       │   ├── social/
│   │       │   └── web/
│   │       └── featured/              # Featured images
│   │           ├── raw/
│   │           ├── optimized/
│   │           ├── social/
│   │           └── web/
│   ├── channels/                      # Future: other content channels
│   │   ├── newsletter/
│   │   ├── podcast/
│   │   └── video/
│   └── site/                          # Site-wide assets
│       ├── branding/
│       │   ├── logos/                 # Brand logos
│       │   ├── watermarks/            # Watermark assets
│       │   └── templates/             # Design templates
│       ├── social_templates/          # Platform-specific templates
│       │   ├── instagram/
│       │   ├── twitter/
│       │   ├── linkedin/
│       │   ├── tiktok/
│       │   └── youtube/
│       └── processing/
│           ├── watermarks/            # Processing watermarks
│           └── overlays/              # Text overlays
└── processing/                        # System processing
    ├── comfyui_output/                # AI generation output
    ├── temp/                          # Temporary files
    ├── cache/                         # Processing cache
    └── logs/                          # Processing logs
```

## Image Processing Workflow

### 1. Generation/Upload
- Images are initially generated or uploaded to `uploads/images/`
- Files are named: `section_<id>_<timestamp>_<hash>.png`
- This provides unique identification and prevents conflicts

### 2. Content Organization
- Images are moved to appropriate `content/posts/post_<id>/sections/section_<section_id>/` directories
- Each section maintains raw and optimized versions
- **Note:** Uses section ID (not order) to prevent misassignment when sections are reordered

### 3. Processing Pipeline
```
raw/ → optimized/ → social/[platform]/ → web/
```

### 4. Error Handling
- Failed generations are stored in `failed/` directory
- Processing errors are logged in `processing/logs/`
- Archive directory stores intermediate processing files

### 5. Social Media Preparation
- Each platform gets optimized versions in their specific formats
- Instagram: Square (1080x1080), Stories (1080x1920), Reels
- Twitter: Landscape (1200x675), Square (1200x1200)
- LinkedIn: Professional (1200x627)
- TikTok: Vertical video formats
- YouTube: Various video formats

### 6. Web Optimization
- Final web-ready versions for blog display
- Optimized for web performance (WebP, compression)

## File Naming Conventions

### Generated Images
- Format: `{descriptive_name}_{timestamp}_{hash}.{extension}`
- Example: `ancient_celtic_storytelling_20250725_143022_abc123.png`

### Optimized Images
- Format: `{descriptive_name}_optimized.{extension}`
- Example: `ancient_celtic_storytelling_optimized.webp`

### Social Media Images
- Format: `{type}_{dimensions}.{extension}`
- Example: `square_1080x1080.jpg`, `landscape_1200x675.jpg`

### Web Images
- Format: `{type}_{dimensions}.{extension}`
- Example: `blog_optimized_800x600.webp`

## Supported Providers

- **ComfyUI**: Local image generation
- **OpenAI DALL-E**: High-quality AI generation
- **Stable Diffusion**: Open-source model support

## API Endpoints

- `POST /api/images/generate` - Generate new images
- `POST /api/images/upload` - Upload images
- `POST /api/images/process` - Process for social platforms
- `GET /api/images/sections/<id>` - Get section images
- `PUT /api/images/sections/<id>` - Update section images

## Configuration

- Provider settings in `config/providers.py`
- Platform specifications in `config/platforms.py`
- Processing settings in `config/settings.py`

## Usage

1. Start the service: `python app.py`
2. Access the management interface at `/`
3. Generate or upload images through the API
4. Images are automatically processed through the pipeline
5. Social media versions are created for each platform

## Integration

This service integrates with:
- **blog-core**: Database access and shared utilities
- **blog-workflow**: Content generation and management
- **blog-launchpad**: Preview and publishing system

## Future Extensibility

### New Content Channels
The `content/channels/` directory is prepared for:
- Newsletter images
- Podcast artwork
- Video thumbnails and assets

### New Social Platforms
The structure easily accommodates new platforms by adding directories under `social/`

### Version Control
The structure supports future version control implementation with version directories

### CDN Integration
Optimized images are ready for CDN deployment with consistent naming conventions 