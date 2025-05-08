# Stable Diffusion 3.5 (SD3.5) + ComfyUI Integration Memo

**Last updated:** [In progress, see chat log for timestamp]

## Current Progress
- Chosen interface: **ComfyUI** (recommended for SD3.5, robust on Mac Studio/Apple Silicon)
- ComfyUI has been cloned and installed in `~/ComfyUI`.
- Python virtual environment set up and all dependencies installed.
- ComfyUI starts successfully and is accessible at [http://localhost:8188](http://localhost:8188).
- The SD3.5 model checkpoint is being downloaded (user is saving to `~/Downloads`).
- The ComfyUI checkpoints directory is ready: `~/ComfyUI/models/checkpoints/`

## Navigation & UI Update (2025-05-07)
- **Images** is now a top-level menu item in the main header, visible on every page.
- All `/llm/images/*` pages use a consistent, modern-styled tab system:
  - **Level 2:** Image Configs, Image Prompts, Image Previews
  - **Level 3 (under Configs):** Simple, Advanced (ComfyUI)
- This ensures a clear, unified navigation experience for all image-related features.

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

## Update 2024-07-09: SD 3.5 Large + CLIPLoader Fix
- SD 3.5 Large checkpoints do **not** embed a CLIP model. You must use a separate `CLIPLoader` node in ComfyUI and select `clip_g.safetensors`.
- The API workflow and backend have been updated to use a `CLIPLoader` node and connect its output to the `CLIPTextEncode` node.
- This resolves the error: `CLIPTextEncode ERROR: clip input is invalid: None`.
- If you add SD 3.5 Large in the ComfyUI UI, always add a `CLIPLoader` node and connect it to your text encoder.

## Note: The directory `sd3.5_large_turbo_all_files/` (used for large comfyUI files and checkpoints) is now excluded from git via `.gitignore` to prevent issues with large files causing git commit hangs.

---

_This memo will be updated as progress continues. See also: `/docs/temp/llm_images_mini_project.md` for broader image workflow plans._ 