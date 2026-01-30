# Preview matches Facebook publish (images, emojis, formatting)

**Purpose:** The Preview page shows exactly what will publish on Facebook—header/title/body for culture/heritage, product image + caption, emojis preserved, no raw JSON.

**Implementation (instruction doc: "Preview should match real Facebook post"):**

1. **Shared formatter** — `utils/formatting/culture_headers.py`:
   - `normalise_text_whitespace(text)` — single helper for line endings, trim, collapse 3+ blank lines to 2, no trailing spaces, at most one trailing newline. Re-used by culture/heritage and any future type.
   - `apply_culture_or_heritage_header(content_type, raw_text)` — culture_fact → UNDERSTANDING SCOTLAND, heritage_fact → SCOTTISH HERITAGE; header + "\n\n" + title + "\n" + body; same as publish.

2. **Preview renderer** — `utils/channel_preview/preview_renderer.py`:
   - Loads posting_queue with LEFT JOIN clan_products for product posts (product_name, product_image_url, product_price, product_link, generated_caption, image_path).

3. **Facebook formatter** — `utils/channel_preview/formatters/facebook.py`:
   - Culture/heritage: apply_culture_or_heritage_header then format_message_for_facebook (same as publish).
   - Product: display_text = caption (formatted, **price stripped per policy** via `strip_price_from_caption`); meta includes product_image_url, product_name, product_link (no product_price).
   - Emojis preserved (UTF-8; no stripping).

4. **Product caption policy (no price)** — `utils/formatting/product_caption.py`:
   - `strip_price_from_caption(text)` removes £/$/bare decimal amounts from product captions. Used in preview formatter and in publish path (`utils/platform_publishers.py`) for product posts so price never appears in preview or published text.

5. **Template** — `templates/channel_previews/facebook_feed.html`:
   - Product: image at top (product_image_url), then title, link, caption (display_text); **price never shown** (policy). No raw JSON.
   - Culture/heritage/message: styled text block with whitespace-pre-wrap (newlines preserved).
   - UTF-8; emojis display correctly.

6. **Publish path** — `utils/platform_publishers.py`: culture/heritage use apply_culture_or_heritage_header; product uses image_path + generated_caption with **price stripped** (strip_price_from_caption) before sending to Facebook. Emoji preservation unchanged.

7. **Parity script** — `scripts/prove_preview_publish_parity.py`: culture/heritage use shared formatter; product uses generated_caption for publish_text; include product IDs in parity checks.

**QA:** Culture/heritage preview shows header + two blank lines + title + one blank line + body. Product preview shows image, title, link, caption (no price). Parity test includes culture_fact, heritage_fact, product.

**Formatting rules:** Header strings and newline rules are documented in [FACEBOOK_CULTURE_HERITAGE_FORMATTING.md](FACEBOOK_CULTURE_HERITAGE_FORMATTING.md). Run the parity script whenever format logic changes.
