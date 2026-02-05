# Phase I-0 — Hybrid & Image Prompt Transparency (Audit + Design Only)

**Phase:** I-0  
**Title:** Hybrid & Image Prompt Transparency (Audit only; no code changes)  
**Date:** 2026-03-01  
**Scope:** Analysis, mapping, and interface design. Diagnostic only.

---

## 1. Why this phase exists (precise)

The system now has for **text** generation:

- Explicit prompts (text)
- Immutable runs
- Engine comparison
- Deterministic publishing

**Image** generation (Hybrid / image engines) does **not** meet the same guarantees:

- Image prompts are **implicit**, not inspectable in a single place
- Prompt inputs are entangled with business logic (e.g. role/theme “reassurance” or “Scottish heritage” bleeding into image intent)
- There is **no** prompt → run → asset trace equivalent to the text workbench
- Engine comparison exists structurally (e.g. workbench API lists image engines), but **image prompts are opaque**

This phase exists to **map and expose** the problem, not to solve it yet.

---

## 2. Image generation inventory (mandatory)

Concrete references only. For each entry point: file path, function name, caller(s), engine(s), where prompt is constructed, what inputs influence it.

---

### 2.1 Instagram Hybrid (script-driven, GPT-Image-1)

| Item | Value |
|------|--------|
| **File path** | `scripts/run_instagram_hybrid_phase1.py` |
| **Functions** | `ensure_generated`, `ensure_three_slides` |
| **Callers** | Same script: `run()` (and role-specific loops: HERITAGE, CULTURE, AUTHORITY, LANGUAGE, REASSURANCE, DEPTH). Invoked by CLI/cron/scheduler; no HTTP route in main app. |
| **Engine(s)** | GPT-Image-1 only, via `blueprints/imaging_generators.imaging_generate_gpt_image_1` |
| **Where prompt is constructed** | Inside `ensure_generated` (lines ~416–430) and `ensure_three_slides` (lines ~516–546). Built as Python f-strings in the script. |
| **Inputs that influence prompt** | **Explicit:** `post_data` (from `get_post_data_for_*_slot`; key field `generated_content` — first line or first 200 chars used as `subject_phrase`). `prompt_theme` (e.g. "Scottish heritage", "Scottish culture") passed into the function. `slot_dir` → `load_stock_selected(slot_dir)` → `reference_url` (stock image URL). `load_all_editorial_steer(slot_dir)` → `steer_combined` (editorial guidance text from slot dir). **Implicit:** Role/date → `section_id_prefix` and `prompt_theme` (e.g. hybrid_heritage, hybrid_culture) and “Variant N of 3” for slides. |

**Three-slide variant:** For each missing slide, prompt = `base_prompt + " Variant {slide_num} of 3."` (line ~544). Same base_prompt for all three; only the suffix differs.

**Editorial steer:** Appended as “Editorial guidance based on prior review:” + `steer_combined` + “Apply this guidance while preserving the overall intent of the image.” Stored in slot dir as `editorial_steer.txt` (and optional numbered files); not in DB.

---

### 2.2 Carousel generation (Instagram)

| Item | Value |
|------|--------|
| **File path** | `blueprints/launchpad/instagram_carousel.py` |
| **Function** | `api_auto_generate_carousel` (route `POST /api/instagram/carousel/auto-generate`) |
| **Callers** | UI “Auto-Generate Carousel” button; no other callers in repo. |
| **Engine(s)** | **None** in this file. Portrait “generation” is delegated to blog-images service. |
| **Where prompt is constructed** | **Not in this file.** This route: (1) selects next blog post, (2) calls `http://localhost:5005/api/portrait/generate-all/{post_id}` (blog-images app), (3) builds carousel slides from existing images, (4) generates caption (LLM), (5) creates posting_queue row. |
| **Inputs** | Post selection logic; blog-images service generates **portrait versions** from **existing optimized images** (crop/resize), not from an image-generation API. |

**Blog-images service** (`blog-images/app.py`):  
- `generate_all_portrait_versions` (route `/api/portrait/generate-all/<post_id>`)  
- Calls `generate_portrait_for_image` → `create_portrait_version(source_path, output_path)`.  
- **No prompt sent to any image engine.** Portraits are created from already-generated section/header images (which may have been produced earlier by imaging APIs using `post_section.image_prompts`).

**Hybrid carousel (3 real slides):**  
- Slide assets for Hybrid roles (HERITAGE, CULTURE, etc.) come from **run_instagram_hybrid_phase1.py** output (slide1/2/3_1080x1350.png per slot).  
- Resolution and payload building: `utils/instagram_payload.py` (e.g. `resolve_depth_carousel_assets`), `utils/instagram_hybrid_phase1.py` (e.g. `resolve_*_slide*_asset`).  
- **Prompt for those slides** is built only in `run_instagram_hybrid_phase1.py` as above; no prompt stored or exposed in carousel UI/API.

---

### 2.3 Blog_post section/header image generation (main app)

| Item | Value |
|------|--------|
| **File path** | `blueprints/imaging_api_generation.py` (sections), `blueprints/header/api_image_generation.py` (header) |
| **Functions** | `imaging_generate_image` (route `POST /api/image-generation/posts/<post_id>/sections/<section_id>/generate-image`); `api_generate_header_image` (route `POST /api/posts/<post_id>/generate-header-image`) |
| **Callers** | Authoring UI, one-click flows, scripts (e.g. `scripts/generate_portrait_only.py`), header blueprint UI. |
| **Engine(s)** | GPT-Image-1, DALL-E, SDXL — selected by request (`model_name`). Implementations in `blueprints/imaging_generators.py`: `imaging_generate_gpt_image_1`, `imaging_generate_dalle_image`, `imaging_generate_sdxl_image`. |
| **Where prompt is constructed** | **Section:** Prompt **read from DB**: `post_section.image_prompts` (JSON or string; key `image_prompt`). No construction in this blueprint; it is passed through to the generator. **Header:** Prompt **from request body**: `data.get('image_prompt')`. |
| **Inputs that influence prompt** | **Section:** Whatever was previously stored in `post_section.image_prompts` (from authoring “image prompts” step or automation). **Header:** Caller-supplied `image_prompt` in JSON body. |

**Upstream prompt production (section):**  
- `blueprints/automation_execute.execute_image_prompts`: Reads `llm_prompt` (name `'Image Prompts Generation'`), substitutes `[SECTION_TITLE]`, `[SECTION_DESCRIPTION]`, `[SECTION_CONTENT]`, etc. from `post_section` and `post_development`, calls LLM, writes result to `post_section.image_prompts`.  
- Authoring APIs (e.g. `blueprints/authoring_api_prompts.py`, authoring imaging) also produce/update `image_prompts`.  
- So section image “prompt” is **assembled** in automation/authoring (LLM + placeholder replacement); the **final string** sent to the image engine is whatever is in `post_section.image_prompts` at the time of the generate call. That final string is **not** stored as a dedicated “prompt used for this run” field; only the pre-generation content in `image_prompts` exists.

---

### 2.4 Authoring / header imaging (prompt from UI or pipeline)

| Item | Value |
|------|--------|
| **File path** | `blueprints/authoring_api_imaging.py`, `blueprints/authoring_api_prompts.py`, `blueprints/imaging_api_prompts.py`, `modules/prompt_renderers.py`, `modules/prompt_service.py` |
| **Functions** | Various: e.g. image prompt generation (LLM), prompt compression (SDXL char limit), model-specific renderers (DALLE3, GPT-Image-1, SDXL). |
| **Callers** | Authoring UI, automation pipeline (execute_image_prompts, etc.). |
| **Engine(s)** | Same as §2.3; selection by `model_key` / `imaging_model_selection` (e.g. `sdxl-lora`, `gpt-image-1`). |
| **Where prompt is constructed** | **Across multiple places:** LLM output (image prompt generation) → optional JSON extraction (`image_prompt` key) → optional compression/rendering per model (e.g. `modules/prompt_renderers.py`: `SDXLRenderer`, `GPTImage1Renderer`, `DALLE3Renderer`) with style/canonical inputs. |
| **Inputs** | Section/post context, style config, model-specific constraints (e.g. SDXL 400 chars), “reassurance”/tone logic in some flows. |

**Notable:** Prompt can be **assembled across multiple functions** (LLM → parse → compress → render). The **exact string** sent to the engine may depend on model_key and compression; it is **not** persisted as “prompt_snapshot” for a run.

---

### 2.5 Product image generation

| Item | Value |
|------|--------|
| **File path** | `utils/content_generation/product_image_handler.py` |
| **Functions** | `ProductImageHandler.fetch_product_images`, etc. |
| **Callers** | Product-related syndication/display logic. |
| **Engine(s)** | **None.** Fetches product image URLs from CLAN API / DB; no AI image generation. |
| **Where prompt is constructed** | N/A |
| **Inputs** | Product ID, SKU; no prompt. |

**Conclusion:** No image-generation entry point for products; out of scope for prompt transparency.

---

### 2.6 Weekly content (weekly_word, weekly_phrase, weekly_insult) images

| Item | Value |
|------|--------|
| **File path** | `utils/weekly_content_image_renderer_v2.py`, `scripts/regenerate_weekly_content_images.py`, `scripts/automated_weekly_content_workflow.py` |
| **Functions** | `render_weekly_content_image` (or equivalent) in renderer; workflow calls renderer after caption/hashtags. |
| **Callers** | Automated weekly content workflow; regenerate script. |
| **Engine(s)** | **None.** ImageMagick-based typographic layout (text, fonts, positioning). No prompt sent to DALL-E/GPT-Image-1/SDXL. |
| **Where prompt is constructed** | N/A (no AI prompt). |
| **Inputs** | Idea/section text, category, config (fonts, colours). |

**Conclusion:** Not an AI image-generation path; no prompt to make transparent.

---

## 3. Prompt composition analysis

### 3.1 Instagram Hybrid (run_instagram_hybrid_phase1.py)

- **Semantic intent:** Injected via `prompt_theme` (e.g. "Scottish heritage", "Scottish culture") and `subject_phrase` (first line of `post_data["generated_content"]` or fallback to `prompt_theme`). Role (HERITAGE, CULTURE, etc.) drives `section_id_prefix` and the theme string.
- **Content category leaking into image prompt:** Yes. Matrix role (HERITAGE, CULTURE, AUTHORITY, LANGUAGE, REASSURANCE, DEPTH) determines `prompt_theme` and slot; “reassurance” or “depth” is effectively a content category that becomes part of the prompt text.
- **Tone/emotion:** “Style: atmospheric, non-photographic, suitable for Instagram.” “Composition: portrait 4:5, centre-weighted, minimal or no text.” Editorial steer appends human-written guidance (tone/emotion) from slot dir files.
- **Content-derived:** `subject_phrase` from `generated_content`; `reference_url` from stock selection (reference only).
- **System-injected:** Fixed strings (style, composition), “Reference for mood and composition only: {url}”, “Variant N of 3”, editorial steer wrapper.
- **Style constraints:** Hardcoded in the f-string (atmospheric, non-photographic, portrait 4:5, etc.).
- **Safety filters:** None explicitly in prompt construction; engine/API may apply their own.
- **Assembled across functions:** Yes. Base prompt in `ensure_generated` / `ensure_three_slides`; editorial steer from `load_all_editorial_steer(slot_dir)`; variant suffix in loop. **Prompt text cannot be reconstructed after the fact** from DB — it exists only at call time in the script and is not stored.

### 3.2 Carousel (auto-generate)

- **Prompt for portraits:** No prompt; blog-images creates portraits from existing images.  
- **Prompt for Hybrid slides:** Built only in run_instagram_hybrid_phase1.py; not stored; not visible in carousel UI or API.

### 3.3 Blog_post section/header (imaging_api_generation, header api_image_generation)

- **Semantic intent:** Section prompt comes from LLM-generated / authoring `post_section.image_prompts`; header from request. Intent is whatever the LLM or user put in; no single “semantic intent” layer in this file.
- **Content category / tone:** Can leak from upstream (automation_execute uses section_heading, draft, expanded_idea); header is fully caller-defined.
- **Assembled across functions:** Section: yes (execute_image_prompts or authoring → DB → imaging_api_generation reads and passes through). The **exact** string sent to the engine is not stored as a run artifact; only the pre-run `image_prompts` column. So **reconstruction** of the exact prompt sent is possible only if no compression/rendering is applied; if SDXL compression or model-specific renderer is used, the final prompt is not persisted.
- **Prompt not reconstructable after the fact:** For section images, the string sent to the engine may differ from `post_section.image_prompts` (e.g. after compression). That final string is not stored. For header, prompt is in request only unless the caller logs or stores it.

---

## 4. Transparency gap analysis

For each path, answers to: Can the exact prompt sent to the engine be reconstructed? Displayed to the user? Edited before generation? Can two engines receive the same prompt deterministically?

| Path | Reconstruct exact prompt? | Display to user? | Edit before generation? | Same prompt to two engines? | Classification |
|------|----------------------------|------------------|--------------------------|-----------------------------|----------------|
| **Instagram Hybrid** | No. Built in script; not stored. Editorial steer in slot dir; combined prompt never persisted. | No. No UI shows it. | No. Only by editing script or slot files (editorial_steer). | No. Single engine (GPT-Image-1); prompt built per run, not reusable. | ❌ **Opaque** |
| **Carousel (Hybrid slides)** | No. Same as Hybrid; prompt lives only in run_instagram_hybrid_phase1. | No. | No. | No. | ❌ **Opaque** |
| **Carousel (blog_post portraits)** | N/A (no prompt; crop/resize). | N/A | N/A | N/A | N/A (no engine prompt) |
| **Blog_post section images** | Partially. Stored prompt is `post_section.image_prompts`; final string may be compressed/rendered and is not stored. | Partially. Authoring can show/edit `image_prompts`; not necessarily the exact string sent. | Yes (edit `image_prompts`). | Theoretically yes if same string passed to both; in practice model-specific rendering can change it. | ⚠️ **Partially transparent** |
| **Blog_post header images** | No. Prompt in request only; not stored as run artifact. | Depends on UI (may show request field). | Yes (caller sends prompt). | Yes if caller sends same string. | ⚠️ **Partially transparent** |
| **Authoring / pipeline (section)** | Same as blog_post section; final sent prompt not always stored. | Partially (authoring shows/edits prompts). | Yes. | Depends on pipeline; model-specific renderers can differ. | ⚠️ **Partially transparent** |
| **Product** | N/A | N/A | N/A | N/A | N/A |
| **Weekly content** | N/A | N/A | N/A | N/A | N/A |

**Summary:**  
- **❌ Opaque:** Instagram Hybrid (and Hybrid carousel slides).  
- **⚠️ Partially transparent:** Blog_post section/header and authoring flows (prompt exists in DB or request but exact engine input not always stored; display/edit possible in some UIs).  
- **✅ Transparent:** None of the image paths fully meet “reconstruct, display, edit, same prompt to two engines” with a single stored prompt and run record.

---

## 5. Mapping to workbench concepts (no redesign)

Map existing image generation onto **existing** workbench concepts only: Prompt (text or spec), Generation run, Engine, Output/asset, Slot. Only show where current code does **not** fit the model.

| Concept | Text workbench (H-3/H-5) | Instagram Hybrid | Blog_post section/header image |
|--------|---------------------------|-------------------|----------------------------------|
| **Prompt** | Stored in `workbench_prompts` (text_prompt); one per (content_ref, platform, channel_type). | Not stored. Built in script from post_data + slot dir (stock URL, editorial_steer). | Section: `post_section.image_prompts` (not workbench_prompts). Header: request body only. |
| **Generation run** | `generation_runs` row: content_ref, platform, channel_type, engine_id, prompt_snapshot, output_refs, slot_identifier. | No run row. Script writes files to slot dir; no DB run record. | No `generation_runs` row for imaging_api_generation or header API. |
| **Engine** | Chosen in UI; stored in run. | Hardcoded: GPT-Image-1 only. | Chosen in request (model_name); not recorded in a run. |
| **Output / asset** | `output_refs.posting_queue_id` → posting_queue. | File path (e.g. slide1_1080x1350.png) in slot dir; referenced by instagram_payload / instagram_hybrid_phase1 resolvers. | File path on disk; section/header paths. Not linked to a run or workbench current output. |
| **Slot** | `slot_identifier = 'primary'` for blog_post. | One slot = one (role, date) dir; three slides = three files (slide1/2/3). No slot_identifier in DB. | Section = section_id; header = 'header'. No slot_identifier in workbench sense. |

**Where current code does not fit:**

- **Hybrid:** No prompt storage, no generation_runs, no engine choice in UI, no “current output” or run history. Slot is a directory, not a workbench slot.
- **Blog_post images:** Prompt lives in post_section or request, not workbench_prompts. No generation_runs for image calls; no link from “current output” to an image run. Engine is request-scoped, not stored per run.
- **Carousel:** Consumes Hybrid output files or blog-images portraits; no prompt or run model for those assets in the workbench.

---

## 6. Explicit non-goals (must be stated)

Phase I-0 does **not**:

- Change image prompts
- Re-architect Hybrid
- Add UI
- Add engine logic
- Introduce SDXL tuning
- Touch carousel behaviour

This document is **diagnostic only**.

---

## 7. Design authority (unchanged)

The auditor did **not**:

- “Fix” image prompts
- Simplify logic
- Propose alternative architectures
- Merge carousel and workbench
- Add convenience behaviour

**Suggestions** (if any) may appear only in a clearly marked appendix.

---

## 8. Appendix: Suggestions (clearly marked)

Optional; for use when deciding Phase I-1 and beyond.

- **I-1 (image prompt persistence + run recording):** Mirror H-3 for image: store image prompt per (content_ref, platform, channel_type) or per slot; create a `generation_runs`-like row for each image generation (engine_id, prompt_snapshot, output_refs). Hybrid would require a way to persist the constructed prompt and record a run when calling `imaging_generate_gpt_image_1`.
- **I-2 (image engine comparison):** Reuse workbench engine list and “Run with engine” pattern for image; ensure the **same** prompt (stored or resolved) can be sent to multiple engines and runs compared.
- **I-3 (slot-level control):** Map Hybrid slots (and carousel slides) to slot_identifier; allow “current output” per slot (e.g. slide 1, 2, 3) so publishing uses the selected run’s asset.

No pressure to proceed until the audit is complete.

---

## 9. Stop statement (required)

**Phase I-0 audited image and hybrid prompt construction for transparency, determinism, and traceability. No code, UI, schema, or generation behaviour was modified.**
