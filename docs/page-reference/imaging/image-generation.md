# Sections Image Generation - Technical Reference

## Page Overview

**URL**: `/imaging/posts/<int:post_id>/sections/image-generation`  
**Blueprint**: `imaging`  
**Template**: `imaging/sections/image_generation.html`  
**Stage**: Imaging (Stage 4 of 5)  
**Substage**: Image Generation (Substage 1 of 2)  
**Purpose**: Generate individual AI images for each blog post section using prompts from the authoring stage

### Workflow Position
- **Preceded by**: Authoring Stage (Image Concepts, Prompts, Captions)
- **Current**: Image Generation substage (generates AI images for individual sections)
- **Followed by**: Optimise substage (resize, compress, watermark images)

## Technical Architecture

### Flask Route Handler
```python
@bp.route('/posts/<int:post_id>/sections/image-generation')
def imaging_sections_image_generation(post_id):
    """Image Generation page - standalone imaging workflow"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post data for header
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post
                WHERE id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
            if not post:
                return f"Post {post_id} not found", 404
            
            # Format dates for display
            post_created = post['created_at'].strftime('%Y-%m-%d %H:%M') if post['created_at'] else 'Unknown'
            post_updated = post['updated_at'].strftime('%Y-%m-%d %H:%M') if post['updated_at'] else 'Unknown'
            
        return render_template('imaging/sections/image_generation.html', 
                             post_id=post_id,
                             page_title='Image Generation',
                             post_title=post['title'],
                             post_status=post['status'],
                             post_created=post_created,
                             post_updated=post_updated,
                             currentStage='imaging',
                             currentSubstage='image-generation')
    except Exception as e:
        logger.error(f"Error rendering image generation page: {str(e)}")
        return f"Error: {str(e)}", 500
```

### Template Structure
- **Base Template**: `base.html` (dark theme)
- **Main Template**: `imaging/sections/image_generation.html`
- **Includes**: 5 specialized panel templates
- **JavaScript**: 6 main JavaScript modules (1000+ lines total)

### JavaScript Modules
1. **`imaging-workspace.js`** (156 lines)
   - Main coordination script
   - State management with localStorage persistence
   - Global event handling and accordion management

2. **`sections-panel.js`** (299 lines)
   - Batch selection and generation management
   - Section loading and rendering
   - Checkbox selection persistence
   - Sequential batch processing

3. **`image-generation-handler.js`** (355 lines)
   - Individual image generation orchestration
   - Prompt collection and validation
   - API integration and error handling
   - Real-time image display updates

4. **`model-selection.js`** (424 lines)
   - Model selection (SDXL LoRA, DALL-E 3, DALL-E 2)
   - Parameter management and validation
   - Configuration persistence
   - Event-driven communication

5. **`prompt-construction.js`** (518 lines)
   - Generated prompts display
   - Section selection handling
   - Prompt regeneration functionality
   - Multiple section support

6. **`output-panel.js`** (varies)
   - Image display and preview
   - Generation status updates
   - Error handling and notifications

## Database Operations

### Core Content Tables

#### `post` Table Operations
```sql
-- Post context retrieval
SELECT id, title, status, created_at, updated_at
FROM post
WHERE id = %s
```

#### `post_section` Table Operations
```sql
-- Section verification for image generation
SELECT id, section_order, section_heading
FROM post_section
WHERE id = %s AND post_id = %s

-- Section ID resolution by order
SELECT id FROM post_section
WHERE post_id = %s AND section_order = %s

-- Section data with image prompts
SELECT id, section_order, section_heading, image_prompts
FROM post_section
WHERE id = %s AND post_id = %s
```

### User Preferences Table

#### `ui_user_preferences` Table Operations
```sql
-- Save model selection configuration
INSERT INTO ui_user_preferences (user_id, preference_key, preference_value, preference_type, category, is_global)
VALUES (1, 'imaging_model_selection', %s, 'json', 'imaging', false)
ON CONFLICT (user_id, preference_key) 
DO UPDATE SET preference_value = %s, updated_at = NOW()
```

### Image Processing Tables
- **Image generation functions**: `imaging_generate_dalle_image()`, `imaging_generate_sdxl_image()`
- **Image optimization**: `optimize_image_with_watermark()`
- **File storage**: Organized in `/static/content/posts/{post_id}/sections/{section_id}/raw/`

## API Endpoints

### Internal API Endpoints

#### Image Generation
```http
POST /imaging/api/image-generation/posts/<post_id>/sections/<section_id>/generate-image
Content-Type: application/json

{
    "model_name": "sdxl-lora|dall-e-3|dall-e-2",
    "parameters": {
        "width": 1792,
        "height": 1024,
        "steps": 30,
        "cfg": 5.5,
        "seed": null,
        "lora_scale": 0.85
    },
    "image_prompt": "string"
}
```

#### Flexible Section ID Support
```http
POST /imaging/api/image-generation/posts/<post_id>/sections/<section_id>/generate-image
```
- Supports numeric section IDs (e.g., `803`)
- Supports string section IDs (e.g., `section_1`)
- Automatically resolves to database section ID

#### Image Optimization
```http
POST /imaging/api/optimize/posts/<post_id>/sections/<section_id>/optimize-image
Content-Type: application/json

{
    "quality": 50,
    "overlay_text": "AI-generated image",
    "watermark": true,
    "text_overlay": true
}
```

#### Sections Data Retrieval
```http
GET /imaging/api/posts/<post_id>/sections
```

#### Model Configuration Save
```http
POST /imaging/api/llm/save-config
Content-Type: application/json

{
    "model": "sdxl-lora",
    "parameters": {
        "width": 1792,
        "height": 1024,
        "steps": 30,
        "cfg": 5.5,
        "lora_scale": 0.85
    }
}
```

### External Service Integration
- **DALL-E API**: OpenAI image generation service
- **SDXL LoRA**: Local ComfyUI integration
- **Image Processing**: Watermarking and optimization services

## Included Modules

### Template Includes (5 panels)

1. **Sections Panel** (`shared/sections_panel.html`)
   - Section selection and batch management
   - Checkbox-based multi-selection
   - Batch generation controls
   - Selection persistence in localStorage

2. **Model Selection Panel** (`imaging/includes/model_selection_panel.html`)
   - Model selection dropdown (SDXL LoRA, DALL-E 3, DALL-E 2)
   - Model-specific parameter controls
   - LoRA scale management
   - Configuration persistence

3. **LLM Prompts Panel** (`authoring/includes/llm_prompts_panel.html`)
   - Shared authoring panel for prompt management
   - Cross-stage integration

4. **Prompt Construction Panel** (`imaging/includes/prompt_construction_panel.html`)
   - Generated image prompts display
   - Section-specific prompt viewing
   - Prompt regeneration functionality
   - Multiple section support

5. **Debugging Panel** (`imaging/includes/debugging_panel_image_generation.html`)
   - Development and debugging tools
   - Data inspection capabilities

6. **Output Panel** (`imaging/right/output_panel_image_generation.html`)
   - Image display and preview
   - Generation status updates
   - Error handling and notifications

### Shared Components
- **`shared/blog_pipeline_header.html`**: Navigation and workflow context
- **`shared/data_display.html`**: Data tab content
- **`shared/sections_panel.html`**: Section management interface

## Workflow Integration

### Data Dependencies
- **From Authoring Stage**: 
  - `image_prompts` field in `post_section` table
  - `image_concepts` field for visual concepts
  - `image_captions` field for captions
- **From Planning Stage**: Section structure and organization

### Data Outputs
- **Generated Images**: Stored in `/static/content/posts/{post_id}/sections/{section_id}/raw/`
- **Image Metadata**: File paths and generation parameters
- **User Preferences**: Model selections saved to `ui_user_preferences`

### State Management
- **localStorage Persistence**: 
  - `imaging_selected_sections_{postId}`: Selected section IDs
  - `imaging_selected_section_{postId}`: Currently highlighted section
  - `imaging-{key}`: Various imaging state variables
- **Model Configuration**: Saved to database via `ui_user_preferences`
- **Section Selection**: Checkbox state and highlighting persistence

## Key Features

### AI-Powered Generation
- **SDXL LoRA**: Local generation with watercolor/inwash style (1792x1024)
- **DALL-E 3**: OpenAI service for photorealistic images (1792x1024, HD quality)
- **DALL-E 2**: OpenAI service for artistic images (1024x1024)
- **Parameter Control**: Fine-grained control over generation parameters

### Batch Processing
- **Multi-Selection**: Checkbox-based section selection
- **Sequential Generation**: Processes selected sections one by one
- **Progress Tracking**: Real-time status updates during batch operations
- **Error Handling**: Graceful handling of individual section failures

### User Experience
- **Section Highlighting**: Click-to-highlight for preview
- **Independent Selection**: Checkbox selection separate from highlighting
- **Auto-Selection**: Optional auto-select all sections on first load
- **State Persistence**: All selections and configurations saved
- **Real-time Updates**: Live image display during generation

### Integration Features
- **Cross-Stage Data**: Uses prompts from authoring stage
- **Flexible Section IDs**: Supports both numeric and string section identifiers
- **Model Communication**: Event-driven communication between panels
- **API Consistency**: Unified API endpoints for different models

## Technical Specifications

### Image Dimensions
- **SDXL LoRA**: 1792x1024 (custom dimensions)
- **DALL-E 3**: 1792x1024 (predefined sizes)
- **DALL-E 2**: 1024x1024 (predefined sizes)

### File Storage Structure
```
/static/content/posts/{post_id}/sections/{section_id}/
├── raw/           # Original generated images
├── optimized/     # Processed and compressed images
└── watermarked/   # Final images with watermarks
```

### Model Parameters
- **SDXL LoRA**:
  - Width: 1792 (default)
  - Height: 1024 (default)
  - Steps: 30 (default)
  - CFG Scale: 5.5 (default)
  - LoRA Scale: 0.85 (default)
  - Seed: Random (default)

- **DALL-E 3**:
  - Size: 1792x1024 (default)
  - Quality: standard (default)
  - Style: natural (default)

### Database Constraints
- **Section References**: Foreign key constraints to `post_section` table
- **User Preferences**: Unique constraints on user_id and preference_key
- **Image Storage**: File system based storage with database metadata

## JSON Files and Hardcoded Content

### JSON Data Handling
- **Image Prompts**: Stored as JSON in `post_section.image_prompts` field
- **Image Concepts**: Stored as JSON in `post_section.image_concepts` field
- **Model Configuration**: Saved as JSON in `ui_user_preferences.preference_value`
- **localStorage Data**: Serialized as JSON for persistence

### Hardcoded Content
- **Default Parameters**: Hardcoded default values in JavaScript
  - SDXL: width=1792, height=1024, steps=30, cfg=5.5, lora_scale=0.85
  - DALL-E: size=1792x1024, quality=standard, style=natural
- **Placeholder Text**: "AI-generated image" watermark text
- **Error Messages**: Standardized error messages in JavaScript
- **API Endpoints**: Hardcoded endpoint URLs in JavaScript modules

### Specimen Data
- **LoRA Configuration**: Hardcoded "Aether Watercolor & Ink" LoRA
- **Default Seeds**: Random seed generation for SDXL
- **Fallback Values**: Default model selection and parameter values

## End-to-End Data Flow

### 1. Page Load
1. **Route Handler**: Fetches post data from `post` table
2. **Template Rendering**: Loads all panel templates
3. **JavaScript Initialization**: Initializes all modules
4. **Section Loading**: Fetches sections via `/imaging/api/posts/{postId}/sections`
5. **State Restoration**: Restores saved selections from localStorage

### 2. Section Selection
1. **User Interaction**: Click on section item or checkbox
2. **Event Handling**: `sectionSelected` custom event dispatched
3. **State Update**: Updates `currentSectionId` and highlights UI
4. **Persistence**: Saves selection to localStorage
5. **Panel Updates**: Updates prompt construction and output panels

### 3. Image Generation Process
1. **Prompt Collection**: Retrieves `image_prompts` from `post_section` table
2. **Model Selection**: Gets current model and parameters from UI
3. **API Call**: Sends request to `/imaging/api/image-generation/posts/{postId}/sections/{sectionId}/generate-image`
4. **Image Generation**: Calls appropriate generation function (DALL-E or SDXL)
5. **File Storage**: Saves image to `/static/content/posts/{postId}/sections/{sectionId}/raw/`
6. **Response**: Returns image path and success status
7. **UI Update**: Updates output panel with generated image

### 4. Batch Processing
1. **Selection**: User selects multiple sections via checkboxes
2. **Batch Start**: `batchGenerateSelected()` method called
3. **Sequential Processing**: Processes each selected section individually
4. **Progress Updates**: Real-time progress updates via callbacks
5. **Error Handling**: Continues processing even if individual sections fail
6. **Completion**: Final status update and UI reset

### 5. State Persistence
1. **Model Configuration**: Saved to `ui_user_preferences` table
2. **Section Selection**: Saved to localStorage
3. **Panel States**: Accordion states saved to localStorage
4. **User Preferences**: Model and parameter preferences persisted

## Error Handling

### Generation Errors
- **API Failures**: Graceful fallback with user notification
- **Model Errors**: Clear error messages with retry options
- **File System Errors**: Automatic cleanup and recovery
- **Network Errors**: Timeout handling and retry logic

### Database Errors
- **Connection Issues**: Automatic retry with exponential backoff
- **Constraint Violations**: User-friendly error messages
- **Transaction Failures**: Rollback and state restoration

### User Interface Errors
- **Validation Errors**: Real-time form validation
- **State Corruption**: Automatic state recovery from localStorage
- **Missing Data**: Graceful handling of missing prompts or sections

## Logical Problems Identified

### 1. Section ID Inconsistency
- **Problem**: Mixed use of numeric IDs (803) and string IDs (section_1)
- **Impact**: Confusion in section resolution and data handling
- **Evidence**: Code comments about "invalid numeric section IDs"

### 2. Prompt Data Format Inconsistency
- **Problem**: `image_prompts` field sometimes contains JSON, sometimes plain text
- **Impact**: Parsing errors and inconsistent prompt handling
- **Evidence**: Multiple parsing attempts in JavaScript code

### 3. Model Selection Communication
- **Problem**: Model selection not consistently communicated between panels
- **Impact**: Potential mismatches between selected model and generation parameters
- **Evidence**: Multiple event systems for model communication

### 4. Batch Processing Logic
- **Problem**: Complex batch processing with mixed selection states
- **Impact**: Confusion between highlighting and batch selection
- **Evidence**: Separate handling for "selected" vs "highlighted" sections

### 5. State Management Complexity
- **Problem**: Multiple state management systems (localStorage, database, in-memory)
- **Impact**: Potential state inconsistencies and synchronization issues
- **Evidence**: Multiple state persistence mechanisms

## Future Enhancements

### Planned Features
- **Unified Section ID System**: Consistent section identification
- **Enhanced Batch Processing**: Improved batch generation with better progress tracking
- **Model Integration**: Better integration between header and sections imaging
- **Advanced Error Recovery**: More sophisticated error handling and recovery

### Technical Improvements
- **State Management**: Unified state management system
- **API Consistency**: Standardized API endpoints and data formats
- **Performance Optimization**: Caching and optimization improvements
- **Monitoring**: Comprehensive logging and monitoring

## Related Documentation

- **[System Overview](../system-overview.md)**: Overall system architecture
- **[Database Architecture](../database_architecture.md)**: Database structure and relationships
- **[Workflow Navigation System](../workflow_navigation_system.md)**: Workflow system documentation
- **[API Reference](../api_reference.md)**: Complete API documentation
- **[Header Image Page](./header/header-image.md)**: Related header image generation
- **[Imaging Stage Overview](./README.md)**: Imaging stage documentation