# New Image System Reference

## Overview
The new image system provides robust, modular support for image upload, generation, optimization, watermarking, and integration with the workflow and publishing systems. It is designed to be extensible, maintainable, and fully integrated with the existing blog workflow and database schema.

---

## Architecture
- **Direct PostgreSQL integration** (no SQLAlchemy)
- **Image processing**: Supports both uploaded and LLM-generated images
- **Watermarking**: Automated, configurable watermarking pipeline
- **Format optimization**: Images are optimized for web (e.g., WEBP, JPEG)
- **Workflow integration**: Images are linked to post sections and tracked through all workflow stages
- **Publishing integration**: Images are prepared for CDN upload and public URLs are managed
- **Preview integration**: Images display in preview templates with graceful error handling

---

## Database Tables
The following tables are central to the image system (see `/docs/reference/database/schema.md` for full schema):
- `image`
- `image_style`
- `image_format`
- `image_setting`
- `image_prompt_example`
- `post_section` (image-related fields)

Refer to `/docs/reference/database/schema.md` for field-level details and relationships.

---

## File System Structure
```
static/
├── uploads/
│   └── images/                    # Generated and uploaded images
│       └── section_<id>_<timestamp>_<hash>.png
├── images/
│   ├── posts/                     # Legacy post images
│   ├── site/                      # Site header/footer images
│   └── watermarked/               # Watermarked versions
```

**Important:** The `static/uploads/images/` directory is created automatically and is the canonical location for all generated and uploaded images.

---

## API Endpoints
**Note:** As of June 2024, all image-related API endpoints use `/api/images/*`. The `/api/v1/images/*` endpoints are deprecated and should not be used for new development.

All image-related API endpoints:
- **Image Generation**: `/api/images/generate` (POST)
- **Image Settings**: `/api/images/settings` (GET/POST/PUT/DELETE)
- **Image Styles/Formats**: `/api/images/styles`, `/api/images/formats`
- **Prompt Examples**: `/api/images/prompt_examples`
- **Image Upload**: `/api/images/upload` (POST, multipart/form-data)
- **Batch Generation**: `/api/posts/<post_id>/generate_images` (deprecated, see docs)

All endpoints now return JSON. The previous HTML-vs-JSON bug has been fixed.

For full request/response details, see `/docs/reference/api/current/`.

### Section Dropdown API
- **Endpoint:** `GET /api/workflow/posts/<post_id>/sections`
- **Usage:** Used by the image management panel to populate the section dropdown. Returns a list of all sections for the post, each with its `id` and `title` (and other fields).
- **UI Logic:** The dropdown is populated on page load and when sections are updated. Selecting a section updates the image management context.
- **Bug Fix:** A JS error in `setSectionId` referencing a missing DOM element was fixed by guarding the reference. This ensures the dropdown now populates correctly.

### Image Upload API
- **Endpoint:** `POST /api/images/upload`
- **Usage:** Uploads an image for a specific section. Expects `multipart/form-data` with fields:
  - `image`: the image file
  - `section_id`: the section to associate the image with
  - `post_id`: the post containing the section
- **Response:**
  - `201 Created` with `{ success: true, image_url, filename, section_id, post_id }` on success
  - `400` or `500` with `{ error: ... }` on error
- **UI Logic:** On successful upload, the section's `generated_image_url` is updated and the image appears in the manage tab and green panel.

---

## Preview System Integration

### Image Display in Preview
- **Template:** `app/templates/preview_post.html`
- **Route:** `/preview/<post_id>/` (canonical preview route)
- **Image Processing:** `app/preview/__init__.py` - `get_post_sections_with_images()`

### Image Field Mapping
The preview system handles two image field types:
1. **`image_id`** → Fetches from `image` table → Creates `section.image` object
2. **`generated_image_url`** → Direct URL → Creates `section.image` object with `path` and `alt_text`

### Template Image Rendering
```html
{% if section.image %}
<div class="section-image">
    <img src="{{ section.image.path }}" alt="{{ section.image.alt_text or 'Section image' }}" 
         onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
    <div class="image-error" style="display: none;">
        <small><strong>Image not found:</strong> {{ section.image.path }}</small>
    </div>
    <!-- Image metadata: captions, prompts, notes -->
</div>
{% endif %}
```

### Error Handling
- **Missing Images:** Graceful error display with image path for debugging
- **Broken URLs:** `onerror` handler hides broken images and shows error message
- **File System:** `static/uploads/images/` directory created automatically

---

## Workflow UI Integration

### Image Management Panel
**Template:** `app/templates/workflow/_image_management_panel.html`
**JavaScript:** `app/static/js/workflow/image_management.js`
**Integration:** `app/templates/workflow/index.html` (three-column layout for images substage)

### UI Components

#### 1. **Section Context Dropdown**
- **Purpose:** Select which section to manage images for
- **API:** `GET /api/workflow/posts/<post_id>/sections`
- **Features:** Auto-populates with all post sections, auto-selects first section
- **Bug Fix:** JS error in `setSectionId` fixed with null check

#### 2. **Tabbed Interface**
- **Generate Tab:** Image generation with provider, style, and format selection
- **Upload Tab:** Drag & drop file upload with preview
- **Manage Tab:** Image management with optimization, watermarking, and metadata

#### 3. **Generate Tab Features**
- **Provider Selection:** ComfyUI (Local), DALL-E (OpenAI), Stable Diffusion
- **Style Dropdown:** Populated from `/api/images/styles`
- **Format Dropdown:** Populated from `/api/images/formats`
- **Generate Button:** Creates image using `/api/images/generate`
- **Generate Prompt Button:** AI-assisted prompt generation

#### 4. **Upload Tab Features**
- **Drag & Drop Area:** Visual upload interface
- **File Browser:** Traditional file selection
- **Preview:** Image preview before upload
- **Upload to Section:** Associates image with selected section

#### 5. **Manage Tab Features**
- **Image Grid:** Displays all section images
- **Image Selection:** Click to select and view metadata
- **Action Buttons:** Optimize, Watermark, Download, Delete
- **Metadata Display:** Prompt, style, generation time, file size

#### 6. **Modal Components**
- **Image Preview Modal:** Full-size image viewing
- **Loading Overlay:** Progress indication during operations

### JavaScript Functionality

#### Core Methods
- `ImageManagement(postId, sectionId)` - Main class constructor
- `init()` - Initialize all components and load data
- `loadSectionsDropdown()` - Populate section selector
- `loadSectionImages()` - Load images for selected section
- `generateImage()` - Generate new image
- `uploadImageToSection()` - Upload file to section
- `updateSectionWithImage()` - Update section with new image

#### Event Handling
- **Tab Switching:** Smooth tab transitions
- **Drag & Drop:** File upload with visual feedback
- **Section Selection:** Context switching between sections
- **Image Selection:** Metadata display and action enabling

#### API Integration
- **Settings Loading:** `/api/images/settings`
- **Styles Loading:** `/api/images/styles`
- **Formats Loading:** `/api/images/formats`
- **Image Generation:** `/api/images/generate`
- **Image Upload:** `/api/images/upload`
- **Section Updates:** `/api/workflow/posts/<post_id>/sections/<section_id>`

### CSS Styling
**File:** `app/static/css/panels.css`
- **Dark Theme:** Consistent with existing workflow panels
- **Responsive Design:** Adapts to three-column layout
- **Interactive Elements:** Hover states and visual feedback
- **Loading States:** Spinner and progress indicators

## Usage Patterns
- **Upload or generate images** via the workflow UI or API
- **Configure settings** (style, format, watermark) using the settings endpoints
- **Link images to post sections** using the `post_section` table fields
- **Track image status** through workflow and publishing stages
- **Publish images** to CDN as part of the post publishing process
- **Preview images** in the preview system with proper error handling
- **Manage images** through the comprehensive workflow UI

---

## Database Field Reference

### `post_section` Image Fields
- `image_id` - References `image.id` (legacy system)
- `generated_image_url` - Direct file path (new system)
- `image_captions` - Image caption text
- `image_prompts` - Generation prompt used
- `image_meta_descriptions` - Additional image notes
- `image_prompt_example_id` - References `image_prompt_example.id`

### `image` Table Fields
- `id` - Primary key
- `path` - File system path
- `alt_text` - Alt text for accessibility
- `caption` - Image caption
- `prompt` - Generation prompt
- `metadata` - JSON metadata

---

## Legacy System Reference
For a detailed comparison and migration notes, see:
- `/docs/reference/images/legacy_image_pipeline.md`

---

## Further Reading
- **API Reference**: `/docs/reference/api/current/`
- **Database Schema**: `/docs/reference/database/schema.md`
- **Workflow Integration**: `/docs/reference/workflow/`
- **Preview System**: `/docs/reference/workflow/preview.md`

---

**Note:** For any new development, always check the above references to avoid duplication and ensure consistency with the canonical image system. 