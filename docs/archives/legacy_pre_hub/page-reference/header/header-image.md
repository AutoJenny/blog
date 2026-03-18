# Header Image Page - Technical Reference

## Model-Aware Header Imaging

The Header Image page now integrates with the model-aware imaging system:

### Shared Model Selection
- **Cross-Page Consistency**: Model selection is shared between Sections Imaging and Header Imaging
- **Unified API**: Both pages use the same model specifications and selection endpoints
- **Persistent Configuration**: Model choice persists across page navigation

### Header-Specific Rendering
- **Collage Prompts**: Header images use a collage-style prompt compiled from all section prompts
- **Model-Specific Optimization**: 
  - SDXL: Tag-style collage with artistic enhancements
  - DALL-E: Descriptive collage with natural language
- **Automatic Compilation**: Combines prompts from all sections with image prompts

### Event Logging
- **Header Events**: Header image generation is logged to `image_generation_event` table
- **Section ID**: Uses `NULL` for section_id to distinguish from section images
- **Audit Trail**: Includes collage compilation details and generation timing

## Page Overview

**URL**: `/header/posts/<int:post_id>/header-image`  
**Blueprint**: `header`  
**Template**: `header/header_image.html`  
**Stage**: Header (Stage 5 of 5)  
**Substage**: Header Image (Substage 2 of 5)  
**Purpose**: Create and manage the main header image for blog posts using AI generation

### Workflow Position
- **Preceded by**: Title & Summary substage (creates post title and summary)
- **Current**: Header Image substage (creates main header image)
- **Followed by**: SEO & Meta substage (generates SEO metadata)
- **Then**: Publishing Details substage (sets author, dates, status)
- **Finally**: Final Review substage (comprehensive review before publishing)

## Technical Architecture

### Flask Route Handler
```python
@bp.route('/posts/<int:post_id>/header-image')
def header_header_image(post_id):
    """Header Image substage - Create header image with caption and alt text"""
    return render_template('header/header_image.html', post_id=post_id, blueprint_name='header')
```

### Template Structure
- **Base Template**: `base.html` (dark theme)
- **Main Template**: `header/header_image.html`
- **Includes**: 7 specialized panel templates
- **JavaScript**: 4 main JavaScript modules (627+ lines total)

### JavaScript Modules
1. **`prompt-builder-panel-image-prompts.js`** (627 lines)
   - Prompt compilation from all post sections
   - Model selection communication
   - Character limit management
   - Style guidelines enforcement

2. **`image-generation-panel.js`** (241 lines)
   - Image generation via API calls
   - Progress management
   - Preview display
   - Integration with imaging microservice

3. **`image-details-panel.js`** (162 lines)
   - Metadata management (caption, alt text, title)
   - Auto-save functionality
   - Database updates

4. **`step4-field.js`** (new file)
   - Step 4 field management
   - Compiled prompt handling

## Database Operations

### Core Content Tables

#### `post` Table Operations
```sql
-- Context retrieval
SELECT title, summary FROM post WHERE id = %s

-- Header image linking
UPDATE post 
SET header_image_id = %s, updated_at = CURRENT_TIMESTAMP 
WHERE id = %s
```

#### `image` Table Operations
```sql
-- Image metadata storage
INSERT INTO image (filename, original_filename, path, image_prompt, alt_text, caption)
VALUES (%s, %s, %s, %s, %s, %s)
RETURNING id

-- Image retrieval
SELECT i.id, i.filename, i.path, 
       i.alt_text, i.caption, i.image_prompt
FROM post p
JOIN image i ON p.header_image_id = i.id
WHERE p.id = %s
```

### Workflow System Tables

#### `workflow_step_prompt` Table
```sql
-- Prompt retrieval for image generation (step 65)
SELECT 
    sp.system_prompt,
    tp.prompt_text as task_prompt
FROM workflow_step_prompt wsp
JOIN llm_prompt sp ON wsp.system_prompt_id = sp.id
JOIN llm_prompt tp ON wsp.task_prompt_id = tp.id
WHERE wsp.step_id = 65
```

#### `post_section` Table
- Queries to gather image prompts from all post sections
- Used for header image prompt compilation
- Integration with authoring stage data

### LLM & AI Tables
- **`llm_prompt`**: Prompt templates for image generation
- **`llm_action`**: AI action definitions for image processing
- **`llm_interaction`**: AI interaction logs

## API Endpoints

### Internal API Endpoints

#### Image Generation
```http
POST /header/api/posts/<post_id>/generate-header-image
Content-Type: application/json

{
    "image_prompt": "string",
    "model_name": "dall-e-3|sdxl",
    "parameters": {
        "quality": 50,
        "watermark": true,
        "text_overlay": true,
        "overlay_text": "AI-generated header image"
    }
}
```

#### Image Retrieval
```http
GET /header/api/posts/<post_id>/get-header-image
```

#### Prompt Compilation
```http
POST /header/api/posts/<post_id>/compile-header-prompt
Content-Type: application/json

{
    "model": "dall-e-3|sdxl"
}
```

#### Image Details Update
```http
POST /header/api/posts/<post_id>/update-image-details
Content-Type: application/json

{
    "caption": "string",
    "alt_text": "string",
    "title": "string"
}
```

### External Service Integration
- **`/authoring/api/posts/<post_id>/sections`**: Gets section data for prompt compilation
- **Imaging Microservice**: DALL-E 3 and SDXL image generation
- **Image Processing**: Watermarking and optimization

## Included Modules

### Template Includes (7 panels)

1. **Mini Preview Panel** (`mini_preview_panel.html`)
   - Post title, summary, and status display
   - Quick context for header image creation

2. **Model Selection Panel** (`model_selection_panel.html`)
   - DALL-E 3 vs SDXL model selection
   - Event-driven communication with other panels

3. **Prompt Builder Panel** (`prompt_builder_panel_image_prompts.html`)
   - Image prompt compilation from all sections
   - Model configuration display
   - Prompt assembly with system instructions
   - Character limit monitoring
   - Style guidelines enforcement

4. **Image Generation Panel** (`image_generation_panel.html`)
   - Image generation interface
   - Progress tracking
   - Source prompts display
   - Image preview

5. **Image Details Panel** (`image_details_panel.html`)
   - Caption, alt text, and title management
   - Auto-save functionality
   - Image preview with metadata

6. **Image Preview Panel** (`image_preview_panel.html`)
   - Generated/existing image display
   - Dimensions and status information

7. **Output Panel** (`output_panel_header_image.html`)
   - Final review and output management
   - Integration with next workflow steps

### Shared Components
- **`shared/blog_pipeline_header.html`**: Navigation and workflow context
- **`shared/data_display.html`**: Data tab content
- **Accordion Management**: Database-backed state persistence

## Workflow Integration

### Data Dependencies
- **From Planning Stage**: Topic structure and section organization
- **From Authoring Stage**: Section content and image prompts
- **From Imaging Stage**: Generated section images (for reference)

### Data Outputs
- **Header Image**: Generated and optimized image file
- **Image Metadata**: Caption, alt text, title
- **Post Reference**: Links image to post via `header_image_id`

### State Management
- **Accordion States**: Saved to database for persistence
- **Form Data**: Auto-saved on input changes
- **Generation Progress**: Real-time status updates
- **Model Selection**: Communicated across panels via events

## Key Features

### AI-Powered Generation
- **DALL-E 3**: Photorealistic images (1792x1024, HD quality)
- **SDXL**: Artistic watercolor style (2358x1048 custom dimensions)
- **Prompt Compilation**: Intelligently combines prompts from all post sections
- **Style Guidelines**: Enforces watercolor, brushstrokes, and collage requirements

### Image Processing
- **Automatic Watermarking**: Applied during generation
- **Optimization**: Resize, compress, and optimize images
- **Multiple Formats**: Raw, optimized, and watermarked variants
- **File Organization**: Structured storage in `/static/content/posts/{post_id}/header/`

### User Experience
- **Real-time Preview**: Live image display during generation
- **Progress Tracking**: Visual progress indicators
- **Auto-save**: Automatic form data persistence
- **State Persistence**: Accordion and panel states saved to database
- **Error Handling**: Comprehensive error messages and recovery

### Integration Features
- **Model Communication**: Event-driven communication between panels
- **Workflow Navigation**: Seamless integration with blog pipeline
- **Database Consistency**: Atomic operations with rollback support
- **API Integration**: RESTful endpoints for all operations

## Technical Specifications

### Image Dimensions
- **DALL-E 3**: 1792x1024 (closest to target 2358x1048)
- **SDXL**: 2358x1048 (custom dimensions)
- **Target Ratio**: Optimized for blog header display

### File Storage Structure
```
/static/content/posts/{post_id}/header/
├── raw/           # Original generated images
├── optimized/     # Processed and compressed images
└── watermarked/   # Final images with watermarks
```

### Database Constraints
- **Image References**: Foreign key constraints to `post` table
- **Workflow Tracking**: Progress saved in `post_workflow_stage`
- **Prompt Management**: Linked to `workflow_step_prompt` system

### Performance Considerations
- **Connection Pooling**: Efficient database connections
- **Image Caching**: Optimized image serving
- **Async Operations**: Non-blocking image generation
- **State Management**: Minimal database queries for UI updates

## Error Handling

### Generation Errors
- **API Failures**: Graceful fallback and user notification
- **Model Errors**: Clear error messages with retry options
- **File System Errors**: Automatic cleanup and recovery

### Database Errors
- **Connection Issues**: Automatic retry with exponential backoff
- **Constraint Violations**: User-friendly error messages
- **Transaction Failures**: Rollback and state restoration

### User Interface Errors
- **Validation Errors**: Real-time form validation
- **Network Errors**: Offline state handling
- **State Corruption**: Automatic state recovery

## Future Enhancements

### Planned Features
- **Batch Generation**: Generate multiple header images
- **Style Presets**: Predefined style configurations
- **Advanced Editing**: In-browser image editing
- **A/B Testing**: Multiple header image variants

### Technical Improvements
- **Caching Layer**: Redis-based image caching
- **CDN Integration**: Global image distribution
- **API Rate Limiting**: Protection against abuse
- **Monitoring**: Comprehensive performance metrics

## Related Documentation

- **[System Overview](../system-overview.md)**: Overall system architecture
- **[Database Architecture](../database_architecture.md)**: Database structure and relationships
- **[Workflow Navigation System](../workflow_navigation_system.md)**: Workflow system documentation
- **[API Reference](../api_reference.md)**: Complete API documentation
- **[Header Stage Overview](./README.md)**: Header stage documentation
 