# Stable Diffusion 3.5 (SD3.5) + ComfyUI Integration Memo

**Last updated:** [In progress, see chat log for timestamp]

## Current Progress
- Chosen interface: **ComfyUI** (recommended for SD3.5, robust on Mac Studio/Apple Silicon)
- ComfyUI has been cloned and installed in `~/ComfyUI`.
- Python virtual environment set up and all dependencies installed.
- ComfyUI starts successfully and is accessible at [http://localhost:8188](http://localhost:8188).
- The SD3.5 model checkpoint is being downloaded (user is saving to `~/Downloads`).
- The ComfyUI checkpoints directory is ready: `~/ComfyUI/models/checkpoints/`

## Next Steps (after model download completes)
1. **Move the SD3.5 checkpoint** from `~/Downloads` to `~/ComfyUI/models/checkpoints/`.
2. **Restart ComfyUI** and verify the model loads (check logs and web UI).
3. **Test image generation** via the ComfyUI web UI and API.
4. **Integrate with blog backend:**
   - Add a Flask API endpoint to send prompts to ComfyUI and save images.
   - Update the blog UI to use this endpoint for image generation.
5. **Document API usage and integration details here as we proceed.**

## How to Continue
- Wait for the SD3.5 model download to finish.
- Notify the assistant of the filename and location.
- The assistant will move the file and guide you through the next steps.

## Update 2025-05-07: ImageSetting Model and API
- Added `ImageSetting` model (name, style, format) to combine style and format into a single selectable setting.
- CRUD API endpoints available at `/api/v1/images/settings`.
- Next: Integrate ImageSetting selection and management into the `/llm/images/prompts` UI, above the Style/Format menus.

## Update 2025-05-07: ImageSetting UI in /llm/images/prompts
- Added a new ImageSetting menu above Style/Format in the Image Prompts UI.
- Users can select, create, edit, and delete ImageSettings (name, style, format) from this menu.
- Selecting an ImageSetting auto-selects the corresponding Style and Format in the menus below.
- Includes a modal for adding/editing settings, and full JS integration for CRUD operations.

---

_This memo will be updated as progress continues. See also: `/docs/temp/llm_images_mini_project.md` for broader image workflow plans._ 