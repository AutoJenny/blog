# Phase-0 Image & Asset Discovery Inventory

**Scope:** /blog directory only. Still images only. Platforms: blog, newsletter, Facebook. No code/schema/data changes.

**Date:** 2026-01-30  
**Purpose:** Exhaustive first-pass discovery of all image-related assets, code, prompts, DB structures, and usage. No design, refactor, or build.

---

## 1. Image Asset Locations

### 1.1 Primary image directories (under /blog)

| Path | File types | Typical use | Pipeline | Status |
|------|------------|-------------|----------|--------|
| `static/content/posts/{post_id}/header/` | raw: .png; optimized: .jpg, .webp; portrait: .png/.jpg | Blog post header images (landscape/portrait) | Header imaging (authoring → header-image → optimise) | Active |
| `static/content/posts/{post_id}/sections/{section_id}/` | raw: .png, .jpeg; optimized: .jpg, .webp; watermarked: .webp; portrait subdirs | Blog section images | Section image generation → process → watermark | Active |
| `static/content/weekly_posts/weekly_word/`, `weekly_phrase/`, `weekly_insult/` | .png (e.g. `square_image.png`) | Facebook weekly content (1080×1080) | Weekly content workflow → ImageMagick renderer v2 | Active |
| `static/content/weekly_posts/test/`, `review_v2/`, `aesthetic_analysis/` | .png | Test/review outputs for weekly images | Test scripts, aesthetic analysis | Partial / test |
| `static/images/` | .png, .jpg, .webp, .ico, no-ext | Site assets: clan-watermark, placeholder, newsletter tile, favicon, brand-logo | Various (watermark ref, newsletter, site) | Active |
| `static/images/content/posts/` | Mixed (duplicates of static/content/posts in some setups) | **Uncertain:** may be legacy or symlink target | Unknown | Unclear |
| `static/images/newsletter/` | .jpg, .html, .txt (tile_base64) | Newsletter tile assets | Newsletter | Active |
| `blog-images/static/content/posts/` | Same structure as above (raw, optimized, watermarked, social subdirs) | Blog-images microservice content; overlaps with main `static/` | blog-images pipeline (process, watermark, resize) | Partial / legacy? |
| `blog-images/static/images/site/` | clan-watermark.png | Watermark asset for blog-images | blog-images scripts | Active (if blog-images used) |
| `blog-core/static/`, `blog-launchpad/static/`, `blog-post-info/static/`, `templates/core/static/` | .png, .jpg (site header/footer, brand-logo) | Subproject static assets; some duplicated | Subproject serving | Legacy / duplicated |
| `static/launchpad/site/`, `static/post_info/site/`, `static/site/` | header.jpg, footer.jpg | Layout imagery | Layout/templates | Active |

### 1.2 Watermark and site assets

| Asset | Location(s) | Used by |
|-------|-------------|---------|
| clan-watermark.png | `static/images/site/`, `blog-images/static/images/site/` | Weekly content renderer (LOGO_PATH in config), blog-images watermark script |
| placeholder.jpg | `static/images/placeholder.jpg` | Fallback / placeholder |
| Newsletter tile | `static/images/newsletter/tile.jpg`, tile_test.html, tile_base64.txt | Newsletter |
| Favicon, apple-touch-icon, brand-logo | `static/images/site/` | Site UI |

### 1.3 Excluded from inventory (per scope)

- Video files (not catalogued).
- `venv_*`, `**/venv/`, `**/node_modules/`, `**/__pycache__/` (ignored).
- Image files under `blog-core/sections_microservice/venv/`, `venv_sdxl/`, `blog-post-sections/venv/` (third-party; not project assets).

---

## 2. Image Generation & Processing Scripts

### 2.1 Generation (outputs image files)

| File | Trigger | Inputs | Outputs | Idempotent? | Status |
|------|---------|--------|---------|-------------|--------|
| `utils/weekly_content_image_renderer_v2.py` | Called by automation (optimize_for_facebook stage) and `regenerate_weekly_content_images.py` | Scots text, translation, category, config (canvas 1080×1080, fonts, logo) | PNG to `static/content/weekly_posts/{category}/{idea_id}/square_image.png` | Overwrites output path | Production |
| `utils/weekly_content_image_renderer.py` | Legacy/replaced by v2 | Similar | Similar | Overwrites | Legacy |
| `modules/image_generation/services.py` | API (e.g. authoring/imaging) | DALL-E: prompt, post_id, section_id; SDXL: subprocess | DALL-E: download to `static/content/posts/{post_id}/sections/{section_id}/raw/{section_id}.png` | No (new file per run) | Active |
| `blueprints/imaging_generators.py` | Header/section image generation API | Model (DALL-E, GPT-Image-1, SDXL), prompt, params | Writes to post section raw/ or header raw/ | No | Active |
| `blueprints/header/api_image_generation.py` | POST `/api/posts/<id>/generate-header-image` | image_prompt, model_name, parameters, optional reference_image_url | Landscape + portrait, then optimize; writes to header raw/ and optimized/ | No | Active |
| `scripts/generate_sdxl_lora.py`, `generate_sdxl_lora_integrated.py` | Manual / one-off | Prompt, model params | **Uncertain** (SDXL output path) | Unknown | Partial / one-off |
| `scripts/generate_portrait_only.py` | Manual | **Uncertain** | Portrait variant | Unknown | Partial |
| `blog-images/scripts/generate_dalle_image.py` | Manual / blog-images app | DALL-E API, prompt | Saves to blog-images static content path | No | Partial (blog-images) |
| `scripts/regenerate_weekly_content_images.py` | Manual | posting_queue rows (weekly content) | Re-runs v2 renderer for each; overwrites square_image.png | Overwrites | Production (maintenance) |

### 2.2 Processing (resize, crop, composite, watermark)

| File | Trigger | Inputs | Outputs | Idempotent? | Status |
|------|---------|--------|---------|-------------|--------|
| `utils/weekly_content_image_renderer_v2.py` | As above | Base image + text layers + logo path | Composite 1080×1080 with ImageMagick (resize, composite) | Overwrites | Production |
| `blog-images/scripts/process_images.py` | Manual / blog-images | raw/ dirs under blog-images structure | Optimized + watermark; writes to optimized/, watermarked/ | Can re-run (overwrites) | Partial (blog-images) |
| `blog-images/scripts/watermark_optimized.py` | Manual | optimized/ dirs | Watermarked to watermarked/ (bottom-right watermark, “AI-generated” text) | Can re-run | Partial |
| `blog-images/scripts/resize_to_facebook.py` | Manual | Optimized image path | 1200×630 (Facebook OG) with padding; PIL | Can re-run | Partial |
| `blog-images/resize_section_images.py` | **Uncertain** | **Uncertain** | Resize for sections | Unknown | Unclear |
| `config/weekly_content_image_config.py` | Imported by renderer v2 | N/A (config only) | N/A | N/A | Active |

### 2.3 Invocation context

- **Scheduled/automation:** Weekly content image is generated in automated_weekly_content_workflow (stage: optimize for Facebook) via renderer v2; path stored in `posting_queue.image_path`.
- **API/UI:** Header and section images via blueprints (header, imaging, authoring); modules/image_generation used for DALL-E.
- **One-off/maintenance:** `regenerate_weekly_content_images.py`, blog-images scripts (process, watermark, resize), generate_sdxl_lora*, generate_portrait_only.

---

## 3. LLM Prompts Involving Images

### 3.1 Image concepts and prompts (blog sections)

| Location | Purpose | Intended output | Referenced by |
|----------|---------|-----------------|---------------|
| `blueprints/automation_execute.py` (execute_image_concepts) | Generate image concepts per section | JSON image concepts → `post_section.image_concepts` | Automation API |
| `blueprints/automation_execute.py` (execute_image_prompts) | Generate image prompts per section | JSON image prompts → `post_section.image_prompts` | Automation API |
| `blueprints/authoring_api_prompts.py` | Build image prompt from concepts; generate captions | image_prompt text; image captions | Authoring API (image prompts, captions) |
| `blueprints/authoring_api_concepts.py` | Persist image concepts | `post_section.image_concepts` | Authoring |
| DB: `llm_prompts` (e.g. “Header montage description”) | Describe montage for header/section | Text description for image generation | automation_execute (prompt_id for concepts/prompts) |

### 3.2 Header / collage prompts

| Location | Purpose | Intended output | Referenced by |
|----------|---------|-----------------|---------------|
| `blueprints/header/api_prompt_compilation.py` | Compile section prompts into header collage prompt | Single prompt for header image | Header image generation |
| Header image generation (api_image_generation, imaging) | Collage-style prompt for header | Header image (landscape/portrait) | Header blueprint, imaging |

### 3.3 Captions paired with images

| Location | Purpose | Referenced by |
|----------|---------|---------------|
| `blueprints/automation_execute.py` (execute_image_captions) | Generate image captions for sections | Automation API; writes to `post_section` |
| `blueprints/authoring_api_prompts.py` (api_generate_image_captions) | Generate captions for a section | Authoring API |

### 3.4 Weekly content (no LLM for image pixels)

- Weekly content **image** is drawn by ImageMagick (renderer v2) from Scots text and config; no LLM image generation.
- **Caption** for weekly posts: `utils/weekly_content_caption_generator.py` + prompts in `config/weekly_content_caption_prompts.py` (LLM text only).

### 3.5 Product posts (Facebook)

- Product image: from `clan_products.image_url` (external URL); no generation in repo.
- Caption: `utils/product_post_caption_generator.py` (LLM); prompt instructs “Do NOT include the price”.

---

## 4. Database Structures

### 4.1 Tables storing image paths, URLs, or metadata

| Table | Relevant columns | Read/write by | Active |
|-------|------------------|---------------|--------|
| `posting_queue` | `image_path` (TEXT) – path to weekly square image (1080×1080) | Executor, automation, preview renderer, backfill | Yes |
| `post` | `header_image_id` (FK to `images`) | header_image_finder, blog-images app, migrations | Yes (schema exists; usage may vary) |
| `post_section` | `image_concepts`, `image_prompts`, `image_captions`, `image_search_terms` (JSONB); legacy: image_id, generated_image_url dropped in image_storage_restructure | automation_execute, authoring APIs, imaging | Yes |
| `images` | id, filename, original_filename, file_path, file_size, mime_type, width, height, alt_text, caption, image_prompt, notes, metadata | image_storage_restructure; post_images links to it | Yes |
| `post_images` | post_id, image_id, image_type (header_raw, header_optimized, section_*, etc.), section_id | header_image_finder (load_header_image_from_db), blog-images app | Yes |
| `clan_products` | `image_url` (product image URL) | Product post workflow, preview, publish, launchpad | Yes |
| `newsletter_clearance_promotions` | `image_url` (TEXT NOT NULL) | Newsletter clearance | Yes |
| `weekly_highlights_items` | `selected_image_url`, `remote_image_url`, selected_image_caption, selected_image_credit | Newsletter weekly highlights | Yes |
| `newsletter_source_item` | `available_images` (JSONB), selected_image_url, selected_image_caption, selected_image_credit, remote_image_url | Newsletter source items (quirky news); image extraction | Yes (per docs) |
| `image_prompt_override` | Per-section/model overrides for image prompts | Model-aware imaging | Yes |
| `image_generation_event` | Log of generation (model, params, prompts, timing) | Imaging blueprint | Yes |
| `section_image_mappings` (in backup) | local_image_path, clan_uploaded_url, image_filename, image_size_bytes, image_dimensions | Legacy backup; **uncertain** if still present in live schema | Uncertain |

### 4.2 Migrations of note

- `migrations/20260117_add_weekly_content_metadata_to_posting_queue.sql` – adds `image_path` to posting_queue.
- `migrations/image_storage_restructure.sql` – creates `images`, `post_images`; drops old image columns from `post_section`.
- `migrations/migrate_image_to_images.sql` – migrates `post.header_image_id` from old `image` to `images`.
- `migrations/create_weekly_highlights_tables.sql` – selected_image_url, remote_image_url.
- `migrations/add_newsletter_clearance_promotions_table.sql` – image_url.
- `migrations/add_image_search_terms_to_post_section.sql` – image_search_terms JSONB.
- `migrations/create_model_aware_imaging_tables.sql` – image_prompt_override, image_generation_event.

---

## 5. Scraping & External Image Ingestion

### 5.1 Scrapers / external image sources

| Component | Purpose | Storage / usage | Status |
|-----------|---------|-----------------|--------|
| `blog-core/newsletter/sources/clan_clearance_scraper.py` | Scrape clan.com clearance page (products) | Returns product dicts including `image_url`; used for newsletter clearance promotions | Active |
| Newsletter: image extraction (docs) | Extract images from article pages during ingestion | `newsletter_source_item.available_images` (JSONB); selected_image_url, remote_image_url | Documented; implementation in blog-core (e.g. image_extraction_service, prefetch) – **uncertain** if in main /blog tree |
| Product images | clan.com product images | No download in repo; `clan_products.image_url` and product post use URL as-is for Facebook/preview | Active |

### 5.2 Storage locations for scraped/ingested images

- **Newsletter:** Docs describe same-domain image extraction and optional “remote image serving”; storage in DB (URLs and metadata). No local image folder explicitly catalogued for newsletter in this sweep; **uncertain**.
- **Clearance:** Scraper returns URLs; newsletter_clearance_promotions stores image_url; no local download catalogued.

### 5.3 Deduplication / hashing

- No image hashing or deduplication logic identified in the searched code (product URL used as-is; newsletter docs do not describe hashing in scope).

### 5.4 Copyright / provenance

- `weekly_highlights_items`: selected_image_credit, selected_image_caption; remote_image_url “to avoid copyright issues” (migration comment).
- Newsletter docs: “re-serve images via remote URLs to avoid copyright infringement”.
- blog-images watermark script: adds “AI-generated image” text.

---

## 6. Observed Image Usage by Content Type

### 6.1 Blog posts

- **Header:** Resolved via `blog-launchpad/publish/header_image_finder.py` (filesystem: `static/content/posts/{post_id}/header/{optimized|watermarked|raw}/` then DB `post_images` + `images`/`image_archive`). Used for blog display and publishing.
- **Sections:** Section images under `static/content/posts/{post_id}/sections/{section_id}/` (raw, optimized, watermarked, portrait where present). Pipeline: concepts → prompts → generation (DALL-E/SDXL/GPT-Image-1) → process/optimise/watermark. Stored in `images` + `post_images` and/or filesystem paths.
- **Uncertain:** Extent to which `blog-images/` static vs main `static/` is used in production (both have similar structure).

### 6.2 Newsletter

- **Clearance:** `newsletter_clearance_promotions.image_url` (product image URLs from scraper).
- **Weekly highlights / source items:** `weekly_highlights_items.selected_image_url`, `remote_image_url`; `newsletter_source_item.available_images`, selected_image_url, remote_image_url (from extraction docs).
- **Tile:** `static/images/newsletter/tile.jpg` (and tile_base64, tile_test.html) for newsletter tile.
- **Uncertain:** Whether all newsletter image code lives under /blog or partly in blog-core only.

### 6.3 Facebook posts

- **Weekly content:** Image = generated square 1080×1080 from `utils/weekly_content_image_renderer_v2.py`; path in `posting_queue.image_path` (e.g. `static/content/weekly_posts/weekly_word/1094/square_image.png`). Uploaded to clan.com then posted to Facebook (platform_publishers).
- **Product:** Image = `clan_products.image_url` (external URL); no local file; passed to Facebook as URL.
- **Other image posts (e.g. future):** Executor expects `image_path` and `generated_caption`; product uses URL; weekly uses filesystem path.

### 6.4 Preview tooling

- **Channel preview (Facebook):** `utils/channel_preview/preview_renderer.py` loads `posting_queue` + clan_products; product uses `product_image_url` (from DB); template shows product image or text. Weekly/product image_path or product_image_url used for display.
- **Header image finder:** Used by launchpad/publish to resolve header for posts.

---

## 7. Open Questions / Uncertainties

1. **blog-images vs main static:** Whether blog-images microservice is still the canonical pipeline for blog post section/header processing, or whether all production flows use main-repo `static/` and blueprints only. Both contain similar directory trees and scripts.
2. **post.header_image_id vs filesystem:** In production, whether header is resolved primarily from DB (`post_images` + `images`) or from filesystem (header_image_finder). Migration and header_image_finder suggest both may exist.
3. **section_image_mappings:** Present in backup SQL; not confirmed in current migrations list as still in use.
4. **Newsletter image extraction:** Implementation (e.g. image_extraction_service, prefetch) referenced in docs; need to confirm paths under /blog and whether remote_image_url serving is implemented.
5. **Duplicate static roots:** Multiple copies of header/footer/brand assets (blog-core, blog-launchpad, post_info, templates/core); which are served in production.
6. **static/images/content/posts vs static/content/posts:** Whether both are used or one is legacy/symlink.
7. **generate_sdxl_lora*, generate_portrait_only:** Exact output paths and whether they are still run.
8. **image_archive table:** Referenced in header_image_finder; not listed in migrations searched; may be legacy or alternate name for `images`.

---

*End of Phase-0 Image & Asset Discovery Inventory. No code, schema, or data was modified.*

---

## 8. First Impressions (optional)

**What seems solid and reusable**

- **Weekly content images:** Single pipeline (renderer v2 + config), clear output path (`static/content/weekly_posts/{category}/{id}/square_image.png`), used by executor and automation. Config in one place (`config/weekly_content_image_config.py`). Idempotent regeneration script exists.
- **Posting_queue.image_path:** One column for weekly image path; used consistently by executor, preview, and automation.
- **Product images for Facebook:** No local generation; `clan_products.image_url` used end-to-end (preview, publish). Simple and consistent.
- **Header image finder:** Single module (header_image_finder) with filesystem-first then DB fallback; clear contract for “where to find header”.
- **Model-aware imaging:** DB tables (image_prompt_override, image_generation_event), shared model specs, and docs (page-reference/imaging, header/header-image) give a clear picture of section/header generation flow.

**What seems fragile or one-off**

- **blog-images vs main static:** Two parallel directory trees (blog-images/static/content/ and static/content/) with similar layout; scripts in blog-images (process, watermark, resize) may or may not be the ones used in production. Risk of confusion and duplicate outputs.
- **Multiple static roots:** header.jpg/footer.jpg/brand-logo in blog-core, blog-launchpad, post_info, templates/core; which is canonical is unclear.
- **One-off scripts:** generate_sdxl_lora*, generate_portrait_only, blog-images scripts (process_images, watermark_optimized, resize_to_facebook) look manual or microservice-specific; not clearly wired into unified app.
- **Legacy renderer:** weekly_content_image_renderer.py (v1) still present; v2 is the one in use; v1 could be removed or clearly marked legacy to avoid mistakes.
- **Watermarking:** Two implementations (blog-images PIL-based script vs weekly content logo composite in ImageMagick); different purposes (section “AI-generated” text vs weekly logo) but no single documented policy.

**Where gaps obviously exist**

- **Newsletter images:** Docs describe extraction and remote_image_url; implementation location under /blog and whether remote serving is live are uncertain. No clear catalogue of newsletter image folders in this sweep.
- **Unified image table usage:** `images` and `post_images` exist and are used by header_image_finder and migrations; many code paths still use filesystem paths directly (e.g. static/content/posts/...). Gap between “canonical DB-backed images” and “path-based” usage.
- **Section image pipeline:** Multiple stages (concepts → prompts → generation → optimise/watermark); unclear whether blog-images pipeline or main app blueprints write the final optimized/watermarked files used in production.
- **No image hashing/dedup:** Product and newsletter use URLs; no shared deduplication or integrity checks for generated or scraped images.
- **Instagram:** Explicitly out of scope; no inventory of Instagram-specific image paths or formats beyond directory placeholders (social/instagram) in blog-images structure.
