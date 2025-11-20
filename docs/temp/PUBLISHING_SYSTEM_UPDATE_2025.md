# Publishing System Updates - 2025

## Recent Changes

### 1. Removed All HTML Caching (2025-01-XX)

**Status**: ✅ COMPLETED

**What Changed**:
- Removed all HTML caching mechanisms from the publishing system
- `clan_publisher.py` no longer loads from cache files
- `preview_handler.py` no longer writes cache files
- System now always generates fresh HTML on every publish

**Why**:
- Cached HTML was causing issues where old HTML with quotes in section headings was being used
- Cache files prevented template updates from taking effect
- User requirement: "GET RID OF FUCKING CACHES"

**Implementation**:
- `clan_publisher.py`: Changed from loading cached HTML to always calling `render_post_html()` fresh
- `preview_handler.py`: Removed cache file writing
- `post_renderer.py`: Template now reloads on each render instead of being cached at module level

**Files Modified**:
- `blog-launchpad/clan_publisher.py` - Removed cache loading logic
- `blog-launchpad/publish/preview_handler.py` - Removed cache writing
- `blog-launchpad/publish/post_renderer.py` - Template reloads each time

---

### 2. Section Heading Quote Removal (2025-01-XX)

**Status**: ✅ COMPLETED

**What Changed**:
- Added template filter to remove quotes from section headings
- Template: `clan_post_raw.html` now uses `{{ section.section_heading|replace('"', '')|replace("'", '')|trim }}`
- Applied to all templates that display section headings

**Why**:
- Section headings in database contain quotes (e.g., `"Medieval Majesty Unfolds"`)
- These quotes were appearing on the live site
- User requirement: Remove inverted commas from section headings

**Implementation**:
- Template filter removes both double and single quotes
- Applied to: `clan_post_raw.html`, `post_preview.html`, `header/preview.html`, `clan_post.html`

**Files Modified**:
- `templates/launchpad/clan_post_raw.html` - Added quote removal filter
- `templates/launchpad/post_preview.html` - Added quote removal filter
- `templates/header/preview.html` - Added quote removal filter
- `blog-launchpad/templates/clan_post.html` - Added quote removal filter

---

## Current Architecture

### HTML Generation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    PREVIEW ROUTE                             │
│  /preview/<post_id>                                         │
│                                                              │
│  1. Load post data (prepare_post_data)                      │
│  2. Load sections (prepare_post_data)                       │
│  3. Render HTML: render_post_html()                          │
│     - Uses: clan_post_raw.html template                      │
│     - Template reloads each time (no caching)               │
│     - Section headings: quotes removed via filter            │
│  4. Wrap in preview template (CSS/styling only)             │
│  5. Display to user                                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ (SAME HTML GENERATION)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 PUBLISHING PROCESS                           │
│  publish_to_clan()                                          │
│                                                              │
│  1. Load post data (prepare_post_data)                      │
│  2. Load sections (prepare_post_data)                       │
│  3. Process images (upload to CDN)                          │
│  4. Generate HTML: render_post_html()                        │
│     - Uses: clan_post_raw.html template (SAME)              │
│     - Template reloads each time (no caching)                │
│     - Section headings: quotes removed via filter            │
│  5. Apply image URL replacements ONLY                        │
│  6. Send to Clan.com API                                     │
└─────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Single Template**: Both preview and publishing use `clan_post_raw.html`
2. **Single Rendering Function**: `render_post_html()` in `post_renderer.py`
3. **No Caching**: HTML is always generated fresh
4. **Template Reloads**: Template reloads on each render to ensure latest version
5. **Only Difference**: Image URL replacements for published version

---

## Template Details

### `clan_post_raw.html`

**Location**: `templates/launchpad/clan_post_raw.html`

**Section Heading Rendering**:
```jinja2
{% if section.section_heading %}
    <h2>{{ section.section_heading|replace('"', '')|replace("'", '')|trim }}</h2>
{% endif %}
```

**Key Features**:
- Removes double quotes (`"`)
- Removes single quotes (`'`)
- Trims whitespace
- Applied to all section headings

---

## Migration Notes

### What Was Removed

1. **Cache File Loading**: `clan_publisher.py` no longer checks for or loads cache files
2. **Cache File Writing**: `preview_handler.py` no longer writes cache files
3. **Template Caching**: Template is reloaded on each render instead of being cached at module level

### What Was Added

1. **Quote Removal Filter**: Template filter to remove quotes from section headings
2. **Template Reload Function**: `_get_template()` function that reloads template each time

---

## Testing

### Verification Steps

1. **Preview Test**: Visit `/preview/<post_id>` - section headings should have no quotes
2. **Publish Test**: Publish a post - section headings on live site should have no quotes
3. **Template Update Test**: Update template, republish - changes should appear immediately (no cache)

---

## Related Documentation

- `docs/temp/CRITICAL_PUBLICATION_PROCESS_FAILURE.md` - Original architecture documentation (now partially outdated - caching section needs update)
- `blog-launchpad/publish/post_renderer.py` - Single source of truth for HTML rendering
- `templates/launchpad/clan_post_raw.html` - Main publishing template

---

## Notes

- The system now generates fresh HTML on every publish, ensuring template changes take effect immediately
- No cache directories should exist - if found, they can be safely deleted
- Template reloads ensure the latest version is always used

