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

## API Endpoints
All image-related API endpoints are documented in `/docs/reference/api/current/`:
- **Image Generation**: `/api/v1/images/generate` (POST)
- **Image Settings**: `/api/v1/images/settings` (GET/POST/PUT/DELETE)
- **Image Styles/Formats**: `/api/v1/images/styles`, `/api/v1/images/formats`
- **Prompt Examples**: `/api/v1/images/prompt_examples`
- **Batch Generation**: `/api/v1/posts/<post_id>/generate_images` (deprecated, see docs)

For full request/response details, see `/docs/reference/api/current/images.md` and `/docs/reference/api/current/posts.md`.

---

## Usage Patterns
- **Upload or generate images** via the workflow UI or API
- **Configure settings** (style, format, watermark) using the settings endpoints
- **Link images to post sections** using the `post_section` table fields
- **Track image status** through workflow and publishing stages
- **Publish images** to CDN as part of the post publishing process

---

## Legacy System Reference
For a detailed comparison and migration notes, see:
- `/docs/reference/images/legacy_image_pipeline.md`

---

## Further Reading
- **API Reference**: `/docs/reference/api/current/`
- **Database Schema**: `/docs/reference/database/schema.md`
- **Workflow Integration**: `/docs/reference/workflow/`

---

**Note:** For any new development, always check the above references to avoid duplication and ensure consistency with the canonical image system. 