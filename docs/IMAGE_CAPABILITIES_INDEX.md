# Image Capabilities Index

**Purpose:** Implementation routing for image handling. Use this index to find where generation, attachment, disclosure, and diagnostics live. Policy is in `docs/IMAGE_CAPABILITY_CHARTER.md`.

---

## 1. Model-aware imaging (concepts → prompts → generation → optimise)

**Use when:** Blog sections or header images are generated from prompts.

- Docs:
  - docs/page-reference/authoring/image-concepts.md
  - docs/page-reference/authoring/image-prompts.md
  - docs/page-reference/imaging/image-generation.md
  - docs/page-reference/header/header-image.md
  - docs/model_aware_imaging_implementation.md

---

## 2. Weekly content image pipeline

**Use when:** Weekly words/phrases/insults need 1080×1080 square images.

- Docs:
  - docs/WEEKLY_CONTENT_SYSTEM_TECHNICAL_REFERENCE.md
  - docs/WEEKLY_CONTENT_AESTHETIC_ANALYSIS_AND_OPTIMIZATION.md
- Notes: ImageMagick; config in config/weekly_content_image_config.py; provenance block; image_path in posting_queue.

---

## 3. Product image handling

**Use when:** Product posts need images.

- Docs:
  - docs/PREVIEW_FACEBOOK_MATCH_PUBLISH.md
  - docs/clan_products/schema.md
- Notes: URL-only from clan_products; no generation; price never in preview or publish.

---

## 4. Preview and publish parity

**Use when:** Channel preview must match published output.

- Docs:
  - docs/UNIFIED_CHANNEL_PREVIEW_SYSTEM.md
  - docs/PREVIEW_FACEBOOK_MATCH_PUBLISH.md
- Notes: Shared formatter; Facebook parity; product/culture/heritage handling.

---

## 5. Newsletter and external image re-serving

**Use when:** Newsletter or external sources need images without copyright risk.

- Docs:
  - docs/newsletter/quirky-news-image-additions.md
  - docs/newsletter/quirky-news-implementation.md
- Notes: remote_image_url; caption/credit; available_images, selected_image_url.

---

## 6. Policy and image classes

**Use when:** You need binding rules on image types, disclosure, or attribution.

- Docs:
  - docs/IMAGE_CAPABILITY_CHARTER.md
- KB: Backend → Image Policy Overview (summary only; Charter is authoritative).

---

## 7. Header and section images (blog / longform)

**Use when:** You need to attach images to blog posts, longform content, or
content that is not a simple social post.

- Systems:
  - images / post_images tables (canonical)
- Docs:
  - docs/page-reference/header/header-image.md
  - docs/image_storage_migration_summary.md
  - docs/analysis/RECIPE_VS_THEME_IMAGE_HANDLING_ANALYSIS.md
- Notes:
  - Header images are resolved from the database first, filesystem second
  - Section images use post_images joins; no ad-hoc filesystem access
  - Do not introduce new image attachment mechanisms without updating this system

---

## 8. Watermarking and AI disclosure

**Use when:** You need to indicate that an image is AI-generated or illustrative.

- Existing mechanisms:
  - Blog section images: watermark + "AI-generated image" text
  - Weekly images: logo only (no AI disclosure)
  - Newsletter images: caption/credit and remote_image_url
- Docs:
  - docs/page-reference/imaging/image-generation.md
  - docs/newsletter/quirky-news-image-additions.md
- Notes:
  - Disclosure is channel-specific
  - Do not invent new disclosure styles without checking IMAGE_CAPABILITY_CHARTER.md

---

## 9. Image failures and diagnostics

**Use when:** Image generation or attachment fails silently or unexpectedly.

- Docs:
  - docs/diagnostics/image_generation_diagnostic_report.md
- Known issues:
  - DB updated without filesystem write
  - Filesystem present but DB missing reference
- Policy:
  - Failures must be logged
  - Fallback is typographic_card unless otherwise specified

---

## 10. Explicit non-goals (do not reimplement)

Do NOT create new systems for:
- Image generation
- Image storage or attachment
- Image preview rendering
- Image disclosure or watermarking

If your requirement resembles any section above, extend the existing
mechanism instead of building a parallel one.

---

**Cross-reference for channel work (e.g. Instagram):** When you create any Instagram planning doc (even a scratch spec), include this sentence: *"This channel implementation uses existing image capabilities as indexed in docs/IMAGE_CAPABILITIES_INDEX.md."*
