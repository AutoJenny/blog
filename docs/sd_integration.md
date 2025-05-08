# Stable Diffusion 3.5 (SD3.5) + ComfyUI Integration

## Overview

- **Purpose:** Local, robust image generation for blog posts using SD3.5 via ComfyUI.
- **Architecture:** Flask backend, ComfyUI as a subprocess, modern admin UI for prompt/image management.

## Directory Structure

- `~/ComfyUI/` — Upstream ComfyUI install (not in repo).
- `sd3.5_large_turbo_all_files/` — Large SD3.5 checkpoints, excluded from git.
- `app/static/comfyui_output/` — Generated images for UI display.
- `app/api/routes.py` — Flask endpoints for ComfyUI control and image generation.
- `app/templates/llm/images_configs.html` — UI for prompt/image generation (Simple/Advanced tabs).

## Installation & Setup

1. **Clone ComfyUI:**  
   `git clone https://github.com/comfyanonymous/ComfyUI.git ~/ComfyUI`
2. **Install dependencies:**  
   `cd ~/ComfyUI && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
3. **Download SD3.5 checkpoint:**  
   Save to `~/ComfyUI/models/checkpoints/` (not tracked by git).
4. **.gitignore:**  
   `sd3.5_large_turbo_all_files/` is excluded to prevent git commit hangs.

## Running & Managing ComfyUI

- **Status endpoint:**  
  `GET /api/v1/comfyui/status` — Checks if ComfyUI is running.
- **Start endpoint:**  
  `POST /api/v1/comfyui/start` — Starts ComfyUI if not running (runs as background process).
- **UI Integration:**  
  - "Advanced (ComfyUI)" tab in Images UI shows status, allows starting, and embeds ComfyUI via iframe.

## Image Generation Workflow

- **Simple tab:**  
  - Sends prompt to `/api/v1/images/generate` (Flask).
  - Flask builds ComfyUI workflow, POSTs to `http://localhost:8188/prompt`.
  - Waits for output image in `~/ComfyUI/output/`, copies to `app/static/comfyui_output/`.
  - Returns image URL for UI display.

- **Advanced tab:**  
  - Direct access to ComfyUI web UI via iframe.

- **CLIPLoader for SD3.5 Large:**  
  - SD3.5 Large checkpoints do not embed a CLIP model.
  - Workflow uses a separate `CLIPLoader` node and connects it to `CLIPTextEncode`.

## File Handling & Storage

- **Generated images:**  
  - Output images are copied to `app/static/comfyui_output/` for serving via Flask.
- **Large files:**  
  - All large model/checkpoint files are excluded from git.

## Extensibility & Roadmap

- **Prompt templates, styles, formats:**  
  - Managed via UI and API.
- **ImageSetting model:**  
  - Combines style/format for easy selection.
- **Future:**  
  - Support for more backends, batch operations, watermarking, approval workflows (see `/docs/temp/llm_images_mini_project.md`).

## Troubleshooting

- **Git hangs:**  
  - Caused by large files; fixed by `.gitignore` update.
- **CLIP errors:**  
  - Always use a `CLIPLoader` node for SD3.5 Large.

---

_See also: `/docs/temp/llm_images_mini_project.md` for broader image workflow plans and future extensibility._ 