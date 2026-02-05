# Phase I-1A — Blog_post Image Prompt Transparency & Run Recording (Report)

**Phase:** I-1A  
**Title:** Blog_post Image Prompt Transparency & Run Recording (API-level only)  
**Date:** 2026-03-01  
**Preconditions:** H-3/H-5 run model in place; I-0 audit complete.

---

## 1. Inventory of blog_post image entry points touched

Only **blog_post** header and section image generation endpoints were modified. No Hybrid or carousel code was touched.

| Area | File | Function / Route | Notes |
|------|------|------------------|-------|
| **Section images** | `blueprints/imaging_api_generation.py` | `imaging_generate_image(post_id, section_id)` → `POST /api/image-generation/posts/<post_id>/sections/<section_id>/generate-image` | Generates landscape and/or portrait section images using model `model_name` (`gpt-image-1`, `dall-e-*`, `sdxl-*`). Prompt read from `post_section.image_prompts`. |
| **Header images** | `blueprints/header/api_image_generation.py` | `api_generate_header_image(post_id)` → `POST /api/posts/<post_id>/generate-header-image` | Generates header landscape + portrait and optimizes to `image_archive`/`images`. Prompt supplied in request body (`image_prompt`). |
| **Run utilities (reused)** | `blueprints/launchpad/workbench_api.py` | `_create_run_record`, `_complete_run_record` | Previously used only for text workbench runs. Now also used by imaging endpoints to write `generation_runs` rows for blog_post images. |

No other image entry points (Instagram Hybrid scripts, weekly_content renderer, product image handlers) were changed.

---

## 2. Prompt snapshot example (before → after render)

### 2.1 Section image (blog_post)

- **Source of truth (DB):** `post_section.image_prompts` (string), e.g.:

```json
{
  "image_prompt": "Illustration of a weaver working at a loom in a small Scottish mill, warm light, focus on hands and texture of the tartan. No text in the image."
}
```

- **Resolved prompt used for the run (Phase I-1A):**

```json
{
  "image_prompt": "Illustration of a weaver working at a loom in a small Scottish mill, warm light, focus on hands and texture of the tartan. No text in the image."
}
```

This JSON is stored in `generation_runs.prompt_snapshot` for the section image run.

### 2.2 Header image (blog_post)

- **Request payload (caller):**

```json
{
  "image_prompt": "Moody landscape of the Highlands at dusk, low clouds, loch in the distance, space for title text above horizon.",
  "model_name": "gpt-image-1",
  "parameters": { "size": "1536x1024", "portrait_size": "1024x1536", "quality": "high" }
}
```

- **Resolved prompt stored as snapshot:**

```json
{
  "image_prompt": "Moody landscape of the Highlands at dusk, low clouds, loch in the distance, space for title text above horizon."
}
```

The imaging generators may add their own internal reference text, but from the API layer the **exact string passed to the model** is the `image_prompt` captured above.

---

## 3. Run record JSON example

Example row from `generation_runs` for a section image (simplified to the relevant fields):

```json
{
  "id": 5123,
  "content_ref": 95,
  "platform": "facebook",
  "channel_type": "blog_post",
  "engine_id": "image/gpt-image-1",
  "trigger": "user",
  "slot_identifier": "primary",
  "status": "success",
  "started_at": "2026-03-01T11:32:10.123456Z",
  "finished_at": "2026-03-01T11:32:18.987654Z",
  "prompt_snapshot": {
    "image_prompt": "Illustration of a weaver working at a loom in a small Scottish mill, warm light, focus on hands and texture of the tartan. No text in the image."
  },
  "output_refs": {
    "type": "blog_post_section_image",
    "post_id": 95,
    "section_id": 3,
    "landscape_generated": true,
    "portrait_generated": true,
    "landscape_path": "/static/content/posts/95/sections/3/landscape/raw/3.png",
    "portrait_path": "/static/content/posts/95/sections/3/portrait/raw/3_portrait.png"
  },
  "error_message": null
}
```

Header image example (same table, different `type` in `output_refs`):

```json
{
  "id": 5124,
  "content_ref": 95,
  "platform": "facebook",
  "channel_type": "blog_post",
  "engine_id": "image/gpt-image-1",
  "trigger": "user",
  "slot_identifier": "primary",
  "status": "success",
  "prompt_snapshot": {
    "image_prompt": "Moody landscape of the Highlands at dusk, low clouds, loch in the distance, space for title text above horizon."
  },
  "output_refs": {
    "type": "blog_post_header_image",
    "post_id": 95,
    "landscape_raw": "/static/content/posts/95/header/landscape/raw/header.png",
    "portrait_raw": "/static/content/posts/95/header/portrait/raw/header_portrait.png",
    "landscape_optimized": "/static/content/posts/95/header/landscape/optimized/header.jpg",
    "portrait_optimized": "/static/content/posts/95/header/portrait/optimized/header_portrait.jpg"
  },
  "error_message": null
}
```

---

## 4. Proof steps (run lifecycle)

These steps use existing endpoints; only internal DB writes were added.

### 4.1 Section image run

1. **Precondition:** `post_section.image_prompts` populated for the target section (`image_prompts` JSON or string with `image_prompt` key/content).
2. **Call imaging API:**

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "model_name": "gpt-image-1",
        "parameters": { "size": "1536x1024", "portrait_size": "1024x1536", "quality": "high" }
      }' \
  http://localhost:5000/imaging/api/image-generation/posts/95/sections/3/generate-image
```

3. **Observe response:** JSON with `success: true` (or errors), `landscape_generated`, `portrait_generated`, and image paths.
4. **Verify run row:** Query `generation_runs`:

```sql
SELECT id, content_ref, platform, channel_type, engine_id, status, prompt_snapshot, output_refs
FROM generation_runs
WHERE content_ref = 95 AND channel_type = 'blog_post'
ORDER BY id DESC
LIMIT 1;
```

5. **Check fields:** `prompt_snapshot.image_prompt` matches the prompt used; `engine_id` matches `"image/gpt-image-1"`; `output_refs.section_id` and paths match the files on disk; `status` is `success` if at least one orientation was generated.

### 4.2 Header image run

1. **Call header imaging API:**

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "image_prompt": "Moody landscape of the Highlands at dusk, low clouds, loch in the distance, space for title text above horizon.",
        "model_name": "gpt-image-1",
        "parameters": { "size": "1536x1024", "portrait_size": "1024x1536", "quality": "high" }
      }' \
  http://localhost:5000/header/api/posts/95/generate-header-image
```

2. **Observe response:** JSON with `success: true`, `landscape_raw`, `portrait_raw`, `landscape_optimized`, `portrait_optimized`.
3. **Verify run row:** Similar `SELECT` query filtered by `content_ref = 95`, `channel_type = 'blog_post'`, `engine_id LIKE 'image/%'`.
4. **Check fields:** `prompt_snapshot.image_prompt` equals the `image_prompt` sent; `output_refs.type = 'blog_post_header_image'`; paths in `output_refs` match the returned JSON and files on disk; `status` is `success` on 200, or `failed` with `error_message` on 500.

In both cases:

- If run creation fails, the endpoint returns **500** and does **not** call the generator (no image without a run).
- If generator or optimization fails, `_complete_run_record` is called with `status='failed'` and `error_message` set.

---

## 5. Explicit list of what was NOT done

- No Hybrid code (scripts or resolvers) was modified.
- No carousel routes or payload builders were changed.
- No generator internals were changed (`imaging_generate_gpt_image_1`, `imaging_generate_dalle_image`, `imaging_generate_sdxl_image` remain untouched).
- No new UI layouts or buttons were added; imaging UIs reuse existing endpoints.
- No image prompt editing UI was introduced; prompts remain in `post_section.image_prompts` or request payloads.
- No engine comparison UI or slot-level image replacement UI was added.
- No changes were made to non-blog_post image flows (products, weekly content, Instagram Hybrid).

---

## 6. Acceptance criteria checklist

| Criterion | Status |
|----------|--------|
| No image is generated without a corresponding run record (for blog_post section/header imaging APIs) | **Met** — `_create_run_record` is called before generator invocations; on failure the request is aborted. |
| Stored prompt matches exactly what the engine received (API-level prompt argument) | **Met** — `prompt_snapshot.image_prompt` stores the exact string passed as `image_prompt` into the generator functions. |
| Engine id is recorded per run | **Met** — `engine_id = "image/<model_name>"` (e.g. `image/gpt-image-1`, `image/sdxl-lora`). |
| Existing publishing behaviour unchanged | **Met** — HTTP routes, request/response shapes, and image file paths are unchanged; only additional DB writes occur. |
| FB and IG blog_post paths both work | **Met** — Imaging endpoints remain platform-agnostic; run records default `platform='facebook'` when not provided but do not affect publishing paths. |
| No Hybrid code touched | **Met** — All changes are confined to section/header imaging APIs and run helpers. |

---

## 7. Stop statement (verbatim)

**Phase I-1A introduced prompt snapshot persistence and immutable run recording for blog_post image generation. No generator internals, UI layouts, Hybrid logic, or carousel behaviour were modified.**

