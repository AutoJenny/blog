# BlogForge CMS - Page Reference Documentation

## Overview

This directory contains comprehensive technical and logical documentation for each page in the BlogForge CMS. Each page is documented with its purpose, database operations, included modules, API endpoints, and role within the overall blog creation workflow.

## Directory Structure

The documentation is organized by the main workflow stages:

```
page-reference/
├── README.md                    # This file
├── calendar/                    # Calendar Stage
│   ├── calendar-view.md         # Calendar View substage
│   ├── idea-generation.md       # Idea Generation substage
│   └── week-ideas.md            # Week Ideas substage
├── planning/                    # Planning Stage
│   ├── topic-brainstorming.md   # Topic Brainstorming substage
│   ├── section-structure.md     # Section Structure Design substage
│   ├── topic-allocation.md      # Topic Allocation substage
│   └── section-titling.md       # Section Titling substage
├── authoring/                   # Authoring Stage
│   ├── drafting.md              # Drafting substage
│   ├── image-concepts.md        # Image Concepts substage
│   ├── image-prompts.md         # Image Prompts substage
│   └── image-captions.md        # Image Captions substage
├── imaging/                     # Imaging Stage
│   ├── image-generation.md      # Image Generation substage
│   └── optimise.md              # Optimise substage
└── header/                      # Header Stage
    ├── title-summary.md         # Title & Summary substage
    ├── header-image.md          # Header Image substage (COMPLETED)
    ├── seo-meta.md              # SEO & Meta substage
    ├── publishing-details.md    # Publishing Details substage
    └── final-review.md          # Final Review substage
```

## Blog Development Pipeline

The BlogForge CMS follows a structured 5-stage workflow for blog creation:

### 1. Calendar Stage
**Purpose**: Content planning and scheduling
- **Calendar View**: Weekly view of content schedule
- **Idea Generation**: AI-powered content suggestions
- **Week Ideas**: Week-specific content planning

### 2. Planning Stage
**Purpose**: Content structure and topic development
- **Topic Brainstorming**: Generate 50+ topic ideas
- **Section Structure Design**: Create logical content organization
- **Topic Allocation**: Distribute topics across sections
- **Section Titling**: Create compelling section titles

### 3. Authoring Stage
**Purpose**: Content creation and development
- **Drafting**: Create initial draft content
- **Image Concepts**: Develop visual concepts
- **Image Prompts**: Generate AI image prompts
- **Image Captions**: Create engaging captions

### 4. Imaging Stage
**Purpose**: Visual content generation and optimization
- **Image Generation**: Generate AI images using DALL-E/SDXL
- **Optimise**: Resize, compress, and watermark images

### 5. Header Stage
**Purpose**: Final content preparation and publishing
- **Title & Summary**: Generate post title and summary
- **Header Image**: Create main header image
- **SEO & Meta**: Generate SEO metadata
- **Publishing Details**: Set author, dates, status
- **Final Review**: Comprehensive review before publishing

## Documentation Standards

Each page reference document follows this structure:

### 1. Page Overview
- URL and routing information
- Purpose and role in workflow
- Stage and substage position

### 2. Technical Architecture
- Flask blueprint and route handlers
- Template structure and inheritance
- JavaScript modules and functionality

### 3. Database Operations
- Tables accessed and operations performed
- SQL queries and data flow
- Relationship mappings

### 4. API Endpoints
- Internal API endpoints used
- External service integrations
- Request/response patterns

### 5. Included Modules
- Template includes and components
- JavaScript classes and functions
- CSS and styling components

### 6. Workflow Integration
- Preceding and following stages
- Data dependencies and requirements
- State management and persistence

### 7. Key Features
- Core functionality highlights
- User interaction patterns
- AI/LLM integrations

## Database Architecture

The system uses PostgreSQL with 82+ tables organized into 10 logical groups:

1. **Core Content** (12 tables) - Posts, sections, workflows
2. **Image Management** (9 tables) - Processing, formats, styles
3. **Workflow System** (12 tables) - Stages, steps, configurations
4. **LLM & AI** (8 tables) - Models, prompts, interactions
5. **Platforms & Syndication** (11 tables) - Social media, distribution
6. **Credentials & Security** (6 tables) - API keys, user management
7. **Clan API Integration** (3 tables) - External product data
8. **UI & Configuration** (6 tables) - Interface settings
9. **Categories & Tags** (3 tables) - Content classification
10. **Backup Tables** (3 tables) - Historical data

## Workflow Database Structure

The workflow system uses a normalized database structure:

- **`workflow_stage_entity`**: Main workflow stages (calendar, planning, authoring, imaging, header)
- **`workflow_sub_stage_entity`**: Sub-stages within each main stage
- **`workflow_step_entity`**: Individual steps within sub-stages
- **`post_workflow_stage`**: Progress tracking for each post
- **`post_workflow_step_action`**: LLM action configurations
- **`workflow_field_mapping`**: Field mappings between stages

## Development Context

This documentation system was created as part of the BlogForge CMS migration from microservices to a unified Flask application. The system has evolved through multiple phases:

- **Phase 1**: Foundation setup and unified application structure
- **Phase 2**: Blueprint migration and service integration
- **Phase 3**: Static assets consolidation
- **Phase 4**: Configuration unification
- **Phase 5**: Testing and validation

The current architecture provides a solid foundation for content management with AI-powered generation, workflow management, and multi-platform syndication capabilities.

## Usage

Each page reference document serves as:
- **Technical Reference**: For developers working on specific pages
- **Architecture Guide**: For understanding system design and data flow
- **Workflow Documentation**: For understanding content creation process
- **API Reference**: For integration and extension development

## Contributing

When adding new pages or modifying existing ones:
1. Update the appropriate stage directory
2. Follow the established documentation structure
3. Include all database operations and API endpoints
4. Document any new dependencies or integrations
5. Update this README if new stages or substages are added
