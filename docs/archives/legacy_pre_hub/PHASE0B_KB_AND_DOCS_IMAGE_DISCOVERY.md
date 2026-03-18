# Phase-0B — Knowledge Base & Docs Discovery: Image Handling

**Scope:** Conceptual foundations for image handling. Sources: Knowledge Base (human-facing) and docs/ (including docs/archive). Topics: images, visuals, media, rendering, generation, watermarking, sourcing, copyright, preview/publish parity, presentation.

**Date:** 2026-01-30  
**Purpose:** Situational awareness only. No code, refactors, or synthesis. No Image Charter drafted.

---

## 1. Knowledge Base: Image-Related Material

KB structure is defined in `blueprints/knowledge_base.py` (KB_STRUCTURE). Image-relevant pages are HTML templates under `templates/knowledge_base/`.

| Title / identifier | Location in KB | Intended audience | Image-related concepts covered | Status | Tone |
|--------------------|----------------|-------------------|--------------------------------|--------|------|
| **Facebook** | channels → facebook | General / ops | Posting process (image + caption); content types (weekly square image, product image URL, culture/heritage); culture & heritage formatting; **preview matches publish**; product price never in preview/publish; image upload and posting | Current | Descriptive + normative (policy stated) |
| **Unified Channel Preview System** | backend → channel_preview | Coders / power users | Single preview mechanism; preview API and full-page preview; channel formatter/template; **preview/publish parity** (formatter reuses publish logic); Facebook template shows formatted text; adding new channel (template, formatter, registry) | Current | Descriptive + implementation pointers |
| **Weekly Words & Phrases** | content_types → social_posts → weekly_words_phrases | General / ops | Image generation: 1080×1080 square with ImageMagick; fonts (96pt Baskerville, usage, provenance, logo); **provenance** in grey text; config: `config/weekly_content_image_config.py` | Current | Descriptive |
| **Weekly Content** | content_types → weekly_content | General | Same as above: generates 1080×1080 images; ImageMagick; provenance; image styling config | Current | Descriptive |
| **Product Posts** | content_types → social_posts → product_posts | General / ops | Product **images** from catalog; product image URLs used directly (no upload); format: short captions, product images, hashtags; handles product image URL directly | Current | Descriptive |
| **Social Posts** | content_types → social_posts | General | Format: “square images, captions, hashtags”; distinction from blog posts | Current | Descriptive |
| **Automated Posting** | workflows → automated_posting | General / ops | Weekly: “creates square image (1080×1080)”; Product: “uses product image URL”; step “Prepare” includes image; posting_queue must have image & caption for image posts | Current | Descriptive |
| **Product Automation** | workflows → product_automation | General / ops | format_for_facebook / optimize_for_facebook: product image URL directly; comparison table: Image = “Generated square (1080×1080)” vs “Product image URL (from CDN)” | Current | Descriptive |
| **Content Roles** | backend → content_roles | Power users | Format-agnostic (text, image, video, carousel); provenance stored (topic_id, source_page_id, etc.); “Visual or descriptive” for some roles | Current | Descriptive |
| **Topic Rota** | backend → topic_rota | Power users | “Visual” interface (editor UI); no image asset policy | Current | Descriptive |
| **Getting Started — Overview** | getting_started → overview | General | “Imaging” = image generation and optimization; “Authoring” = image concepts, prompts, captions; “Instagram” = image-based (in development) | Current | Descriptive |

**KB items with no image-specific content (confirmed):** channels/overview, content_types/blog_posts (and subpages themed/recipe/profile/generated), content_types/overview, interfaces/*, workflows/overview. Newsletter channel page not read; **uncertain** if it describes newsletter image handling.

**Summary:** KB image material is **channel- and content-type-specific** (Facebook, weekly, product, preview). It describes **what** (square images, product URLs, preview matches publish, price policy) and **where** (config files, formatter) but does not define editorial standards for imagery, authenticity, AI-generated disclosure, or heritage sensitivity. Provenance appears as **metadata** (e.g. weekly content “provenance in grey text”) and in content roles (source provenance), not as image-attribution policy.

---

## 2. Docs/: Image-Related Material

### 2.1 Policy / high-level behaviour (coder-oriented)

| File path | Scope | Image-related concepts | Policy / mechanism / implementation | Status | Cross-refs |
|-----------|--------|------------------------|-------------------------------------|--------|------------|
| `docs/PREVIEW_FACEBOOK_MATCH_PUBLISH.md` | Preview must match Facebook publish | Product: image at top, caption, **no price** (policy); culture/heritage: header + body; shared formatter; price stripped in preview and publish | Policy + mechanism | Authoritative | culture_headers, product_caption, platform_publishers, facebook_feed.html |
| `docs/FACEBOOK_CULTURE_HERITAGE_FORMATTING.md` | Culture/heritage text formatting | Header strings, newline rules, parity script; **no image-specific** rules | Policy + mechanism | Authoritative | culture_headers, parity script |
| `docs/UNIFIED_CHANNEL_PREVIEW_SYSTEM.md` | Single preview system for all channels | Preview API, formatter registry, channel templates; Facebook formatter reuses publish logic; **preview/publish parity**; product/culture handling | Mechanism + implementation | Authoritative | preview_renderer, formatters, channel_preview_api |

### 2.2 Pipelines and workflows (implementation)

| File path | Scope | Image-related concepts | Policy / mechanism / implementation | Status | Cross-refs |
|-----------|--------|------------------------|-------------------------------------|--------|------------|
| `docs/WEEKLY_CONTENT_SYSTEM_TECHNICAL_REFERENCE.md` | Weekly content end-to-end | Square 1080×1080; ImageMagick; canvas, colours, fonts, logo; `image_path` in posting_queue; optimize_for_facebook stage | Mechanism + implementation | Authoritative | weekly_content_image_renderer_v2, config/weekly_content_image_config.py |
| `docs/WEEKLY_CONTENT_AESTHETIC_ANALYSIS_AND_OPTIMIZATION.md` | Weekly image layout/aesthetics | Font sizes, spacing, vertical balance; “provenance” as visual block; no policy on attribution | Mechanism (layout) | Current | Renderer, config |
| `docs/WEEKLY_CONTENT_IMAGE_OPTIMIZATION_PARAMETERS.md` | Weekly image parameters | Layout and sizing parameters | Implementation | Current | Config |
| `docs/FINAL_LAYOUT_SPECIFICATION_IMPLEMENTED.md` | Weekly image layout spec | Provenance block position, spacing, content band; aesthetic fixes | Implementation | Current | Renderer v2 |
| `docs/image_storage_migration_summary.md` | Migration to images/post_images | New `images` and `post_images` tables; file layout raw/optimized; removal of old post_section image columns | Implementation | Authoritative (historical) | migrations/image_storage_restructure.sql |

### 2.3 Blog / authoring imaging (sections and header)

| File path | Scope | Image-related concepts | Policy / mechanism / implementation | Status | Cross-refs |
|-----------|--------|------------------------|-------------------------------------|--------|------------|
| `docs/page-reference/authoring/image-concepts.md` | Image concepts step | Concepts from section content; no generation; separation from “prompt styling”; output: concepts + selected concept | Mechanism | Authoritative | authoring, post_section.image_concepts |
| `docs/page-reference/authoring/image-prompts.md` | Image prompts step | Prompts from concepts; style; constraints (“no text, no watermark in frame”); builder v2 | Mechanism | Authoritative | authoring_api_prompts, post_section.image_prompts |
| `docs/page-reference/imaging/image-generation.md` | Sections image generation | Model-aware imaging; DALL-E, GPT-Image-1, SDXL; prompt rendering; event logging; optimise substage | Mechanism + implementation | Authoritative | imaging_generators, image_generation_event |
| `docs/page-reference/header/header-image.md` | Header image page | Model-aware; collage prompt from sections; landscape/portrait; event logging | Mechanism + implementation | Authoritative | header api_image_generation, imaging_generators |
| `docs/model_aware_imaging_implementation.md` | Model-aware system | Model specs, canonical prompt, renderers, overrides, event logging; shared between sections and header | Implementation | Authoritative | image_prompt_override, image_generation_event, PromptService |
| `docs/refactoring/01_component_audit_header_image_finder.md` | Header image resolution | Single source of truth: DB then filesystem; path normalization; risks (inconsistent paths, dual schema) | Mechanism + audit | Outdated / partial (audit) | header_image_finder.py |
| `docs/analysis/RECIPE_VS_THEME_IMAGE_HANDLING_ANALYSIS.md` | Recipe vs theme images | Process identical; post_images + images; no fallbacks; section filtering differs | Mechanism | Authoritative | post_data_loader, imaging_api_generation |
| `docs/header_image_layout_proposal.md` | Header UI layout | Panel simplification; landscape/portrait display; no asset policy | Implementation (UI) | Partial | Header template |
| `docs/diagnostics/image_generation_diagnostic_report.md` | Failure investigation | Silent failures; DB not updated with filenames; filesystem vs DB consistency | Implementation / debugging | Partial (diagnostic) | imaging_api_generation |

### 2.4 Product and profile images

| File path | Scope | Image-related concepts | Policy / mechanism / implementation | Status | Cross-refs |
|-----------|--------|------------------------|-------------------------------------|--------|------------|
| `docs/PROFILE_IMAGE_DATA_REVIEW.md` | Product image data for profiles | clan_products.image_url; API all_images (on-demand); not stored | Mechanism | Current | clan_products, API |
| `docs/clan_products/schema.md` | clan_products table | image_url field | Implementation | Authoritative | DB |

### 2.5 Newsletter and external sources

| File path | Scope | Image-related concepts | Policy / mechanism / implementation | Status | Cross-refs |
|-----------|--------|------------------------|-------------------------------------|--------|------------|
| `docs/newsletter/quirky-news-image-additions.md` | Newsletter image harvesting | Extract images (same-domain); caption/credit; **remote_image_url to avoid copyright infringement**; available_images JSONB; selected_image_url, remote_image_url | Policy (copyright) + mechanism | Partial (plan) | newsletter_source_item, weekly_highlights_items |
| `docs/newsletter/quirky-news-implementation.md` | Quirky news implementation | available_images, selected_image_url, remote_image_url; image extraction service | Mechanism | Partial | blog-core (path uncertain under /blog) |
| `docs/create_weekly_highlights_tables.sql` (migrations) | weekly_highlights_items | selected_image_url, remote_image_url “Re-served URL to avoid copyright issues” | Policy (comment) + schema | Authoritative | DB |

### 2.6 Archive (historical)

| File path | Scope | Image-related concepts | Status |
|-----------|--------|------------------------|--------|
| `docs/archive/phase_2_4_completion_summary.md` | Phase 2.4 completion | Images blueprint; multi-type uploads (header, featured, section); directory structure; image serving | Outdated (pre-unification) |
| `docs/archive/phase_2_3_completion_summary.md` | Static consolidation | Brand assets; content images; clan-watermark | Outdated |
| `docs/archive/phase_3_completion_summary.md` | Static assets | Brand/header/footer images; content images; optimization | Outdated |
| `docs/archive/unification_complete_summary.md` | Unification | images.py blueprint; image management | Outdated |

---

## 3. Concepts Already Defined (Implicit or Explicit)

### Explicit in docs or KB

- **Preview/publish parity:** Preview must show exactly what will publish (Facebook); same formatter for text; product image + caption in preview; price never in preview or publish.
- **Product image:** Use product URL from clan_products; no local generation or upload for product posts.
- **Weekly content image:** 1080×1080 square; ImageMagick; configurable (config file); logo in corner; provenance as visual element; path in posting_queue.image_path.
- **Channel preview:** Single system; channel-specific formatter and template; formatter reuses publish logic where applicable.
- **Image concepts vs prompts:** Concepts = visual ideas from section content; prompts = styled prompt text for generation; concepts before prompts.
- **Model-aware imaging:** Multiple models (SDXL, DALL-E, GPT-Image-1); model-specific prompt rendering; overrides per section/model; event logging.
- **Header image:** Collage prompt from sections; landscape and portrait; resolution: DB (post_images + images) then filesystem (static/content/posts/{id}/header/).
- **Section images:** Stored via images + post_images; types (raw, optimized, etc.); no fallback to filesystem in post_data_loader (per recipe/theme analysis).
- **Copyright / re-serving (newsletter):** “Re-serve images via remote URLs to avoid copyright infringement”; selected_image_url vs remote_image_url; same-domain extraction.
- **Watermarking (blog-images):** Script adds watermark and “AI-generated image” text; newsletter credits (caption, credit) for selected image.

### Implicit or scattered

- **AI-generated disclosure:** “AI-generated image” text in blog-images script; no single policy document stating when/where to disclose.
- **Provenance:** Used as (1) weekly content metadata/visual block (source of phrase/word), (2) content roles (source page/topic), (3) newsletter (caption/credit). Not defined as a cross-channel image-attribution policy.
- **Heritage/cultural sensitivity:** Not mentioned in image context in KB or docs searched.
- **Single source of truth for header image:** header_image_finder defines order (DB then filesystem) but audit doc notes path and schema risks; no canonical “charter” for where header images live.
- **Blog section pipeline:** Concepts → prompts → generation → optimise/watermark; documented in page-reference and model_aware; blog-images vs main app pipeline ownership **uncertain** in docs.

---

## 4. Gaps (Concepts Missing or Only Partially Covered)

- **Editorial standards for images:** No KB or doc that states editorial rules for imagery (tone, appropriateness, authenticity, or heritage sensitivity).
- **When to show “AI-generated”:** Only one script (blog-images watermark) adds the label; no policy for weekly content, header, or section images.
- **Provenance as image attribution:** Provenance is content/source metadata and a visual block in weekly images; no unified definition for “image provenance” or attribution across blog, newsletter, social.
- **Newsletter image implementation status:** Plan and schema exist; implementation location (blog-core path under /blog) and whether remote_image_url serving is live are **uncertain**.
- **Blog-images vs main app:** Two possible pipelines (blog-images microservice vs unified app blueprints); docs do not state which is canonical for production section/header processing.
- **Instagram:** Explicitly out of scope for Phase-0; KB marks “in development” or “planned”; no image-specific guidance.
- **Image lifecycle and retention:** No doc describing retention, archival, or deletion of generated or scraped images.
- **Failure and fallbacks:** Diagnostic doc notes silent failures and DB/filesystem inconsistency; no single “image failure and fallback policy”.

---

## 5. Ambiguities / Conflicts Between KB and Docs

### Overlaps

- **Preview matches publish:** KB (Facebook, channel_preview) and docs (PREVIEW_FACEBOOK_MATCH_PUBLISH, UNIFIED_CHANNEL_PREVIEW_SYSTEM) both state it; consistent.
- **Weekly image:** KB describes 1080×1080, ImageMagick, config; docs (WEEKLY_CONTENT_SYSTEM_TECHNICAL_REFERENCE, aesthetic/layout docs) give mechanism; KB font size (96pt) differs from current config (72pt base in code) — **minor inconsistency** (KB may be outdated).
- **Product image URL:** KB and docs agree: use product URL directly, no upload.

### Divergence / tension

- **Header image source:** Docs (header_image_finder audit) describe DB-first then filesystem; refactoring/archive refer to images blueprint and multi-type uploads. No KB page explains “where header images come from” for editors; coders get mechanism but path/schema risks are in an audit, not a single canonical doc.
- **Watermarking:** Newsletter = caption/credit + remote URL (copyright). Blog section = “AI-generated” + watermark image (blog-images script). Weekly = logo composite only. No doc or KB states a single “watermarking and disclosure” policy across channels.
- **Provenance:** KB uses “provenance” for weekly content (source of phrase) and content roles (source page). Newsletter docs use “credit” and “caption.” Recipe/theme analysis does not use “provenance” for images. Term is used in different senses.

### Implicit in one, explicit in the other

- **Price never in product preview/publish:** Explicit in docs (policy + code); KB states it briefly; both aligned.
- **Model-aware imaging:** Fully explicit in docs (page-reference, model_aware_imaging); KB “Imaging” is one line (generation and optimization); no KB page describes models or prompt rendering.
- **Image concepts vs prompts:** Explicit in docs (authoring image-concepts, image-prompts); KB overview mentions “image concepts, prompts, captions” but does not define the split.

---

## 6. Summary (½–1 page)

### What conceptual ground is already covered well

- **Preview/publish parity** for Facebook is clearly stated in both KB and docs: same formatter, product image + caption, no price. Parity script and formatting docs give coders a single reference.
- **Weekly content images** are well defined: 1080×1080, ImageMagick, config-driven, logo, provenance as visual element, path in posting_queue. Technical reference and layout/aesthetic docs support implementation.
- **Product images** are simple and consistent: use catalog URL only; no generation or upload; stated in KB and docs.
- **Channel preview system** is documented as one reusable mechanism with formatters and templates; KB and UNIFIED_CHANNEL_PREVIEW_SYSTEM align.
- **Model-aware imaging** (blog sections and header) is documented in page-reference and model_aware_implementation; concepts vs prompts separation is clear in authoring docs.

### What is fragmented

- **Watermarking and “AI-generated” disclosure:** Newsletter (copyright, credit, remote URL), blog section (watermark + text), weekly (logo only). No single policy or concept document.
- **Provenance:** Used for source metadata (content), weekly visual block, and newsletter credit; no unified definition for image attribution.
- **Header image resolution:** Behaviour (DB then filesystem) is in code and audit; no single “header image charter” for editors or coders; path/schema risks noted only in refactoring audit.
- **Blog section pipeline:** Authoring and imaging docs describe flow; blog-images microservice has its own docs and scripts; ownership (who writes final optimized/watermarked files) is unclear.

### What appears to be missing entirely

- **Editorial or brand guidance** for images: when to use which type, tone, appropriateness, heritage or cultural sensitivity. KB and docs are technical/operational, not editorial.
- **Single “image policy” or charter** that ties together: disclosure (AI-generated), attribution (provenance/credit), copyright (re-serving), and channel-specific rules (price, format).
- **Image lifecycle:** Retention, archival, or deletion of generated or scraped images.
- **Failure and fallback policy:** What to show or do when an image is missing or generation fails; currently only a diagnostic report, not policy.

---

*End of Phase-0B discovery. No docs, KB, or structure were changed. No Image Charter drafted.*
