# Stable Diffusion 3.5 (SD3.5) + ComfyUI & LLM Image Generation Integration

## Overview

- **Purpose:** Local and cloud-based image generation for blog posts using SD3.5 (ComfyUI) and OpenAI DALL·E, with a modern admin UI for prompt/image management, batch operations, and review workflows.
- **Architecture:** Flask backend, ComfyUI as a subprocess, OpenAI API integration, admin UI for prompt libraries, settings, and review.

## Directory Structure

- `~/ComfyUI/` — Upstream ComfyUI install (not in repo).
- `sd3.5_large_turbo_all_files/` — Large SD3.5 checkpoints, excluded from git.
- `app/static/comfyui_output/` — Generated images for UI display.
- `app/api/routes.py` — Flask endpoints for ComfyUI, DALL·E, and image workflow.
- `app/templates/llm/images_prompts.html` — UI for prompt/settings library, batch/multi-provider testing.
- `app/templates/blog/develop.html` — Blog workflow UI: batch image generation, admin review/override. [DEPRECATED: now handled by workflow substages, develop.html removed]

## Installation & Setup

1. **ComfyUI:**
   - `git clone https://github.com/comfyanonymous/ComfyUI.git ~/ComfyUI`
   - `cd ~/ComfyUI && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
   - Download SD3.5 checkpoint to `~/ComfyUI/models/checkpoints/` (not tracked by git).
2. **.gitignore:**
   - `sd3.5_large_turbo_all_files/` is excluded to prevent git commit hangs.
3. **OpenAI DALL·E:**
   - Set `OPENAI_AUTH_TOKEN` in `.env` for API access.

## Running & Managing ComfyUI

- **Status:** `GET /api/v1/comfyui/status`
- **Start:** `POST /api/v1/comfyui/start`
- **UI Integration:**
  - "Advanced (ComfyUI)" tab in Images UI shows status, allows starting, and embeds ComfyUI via iframe.

## Image Generation Workflow

- **Prompt/Settings Library:**
  - Manage prompt examples, styles, formats, and settings in `/llm/images/prompts`.
  - Save reusable prompt+style+format+provider combos.
- **Batch/Multi-Provider Testing:**
  - Select multiple providers (SD, OpenAI) and compare results in the preview grid.
- **Blog Workflow Integration:**
  - In `/blog/develop/<post_id>`, use "Generate All Images for Sections" to batch-generate images for all post sections.
  - Inline admin review panel for each section: approve, reject, upload/replace, regenerate, and comment.

### SD3.5/ComfyUI
- Flask builds ComfyUI workflow, POSTs to `http://localhost:8188/prompt`.
- Waits for output image in `~/ComfyUI/output/`, copies to `app/static/comfyui_output/`.
- Returns image URL for UI display.
- Always uses a `CLIPLoader` node for SD3.5 Large.

### OpenAI DALL·E
- Sends prompt and settings to OpenAI API.
- Returns image URL for UI display.

## File Handling & Storage

- **Generated images:**
  - Output images are copied to `app/static/comfyui_output/` (SD) or referenced by URL (OpenAI).
- **Large files:**
  - All large model/checkpoint files are excluded from git.

## Admin Review & Override

- Inline review panel per section in blog workflow UI.
- Approve, reject, upload/replace, regenerate images.
- Set review status and leave admin comments.

## Error Handling & Feedback

- All admin actions provide inline status messages and error feedback.
- Robust error handling for network/API issues, file uploads, and regeneration.

## Extensibility & Roadmap

- Add new providers by extending backend and UI.
- Support for more advanced workflows, watermarking, and cloud storage.
- See `/docs/temp/llm_images_implementation_plan.md` for full roadmap.

## Usage & Testing Instructions

### 1. Test Image Generation (Prompt Library)
- Go to `/llm/images/prompts`.
- Create/select prompt, style, format, settings, and provider.
- Test with one or more providers; compare results in preview grid.

### 2. Batch Generate Images for Blog Post
- Go to `/blog/develop/<post_id>`.
- Click "Generate All Images for Sections" in the Images stage.
- Review results in the grid; use admin panel to approve/reject/upload/regenerate.

### 3. Manual Image Upload/Override
- In the admin review panel, use "Upload/Replace" to manually set an image for a section.

### 4. Regenerate Images
- Use the "Regenerate" button in the admin panel to trigger new image generation for a section.

## Troubleshooting

- **Git hangs:** Caused by large files; fixed by `.gitignore` update.
- **CLIP errors:** Always use a `CLIPLoader` node for SD3.5 Large.
- **API/network errors:** Inline error messages are shown in the UI; check server logs for details.
- **Image not appearing:** Ensure ComfyUI is running and output directory is writable.

---

_See also: `/docs/temp/llm_images_implementation_plan.md` for full implementation details and roadmap._ 