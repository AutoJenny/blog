# Unified Channel Preview System

**Date:** 2026-01-25  
**Status:** ✅ **IMPLEMENTED** - Phase 4 complete  
**Purpose:** Technical documentation for the unified channel preview system

---

## Overview

The Unified Channel Preview System provides a single, reusable preview mechanism for all social media channels. Any post in Preview or Ready state can be previewed via a standard popup modal, using channel-specific templates and a shared formatter registry.

**Core Principle:** One preview system, reused everywhere. Preview is HTML-based for all channels.

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│              Unified Channel Preview System                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Preview API Endpoint                                    │
│     GET /api/preview/post/<post_id>                        │
│     Query: channel, mode, variant                          │
│                                                             │
│  2. Preview Renderer (Server-Side)                         │
│     - Loads post from posting_queue                        │
│     - Normalizes preview input fields                      │
│     - Calls channel formatter                              │
│     - Renders channel template                            │
│                                                             │
│  3. Channel Formatter Registry                             │
│     - get_formatter(channel)                               │
│     - Facebook formatter (reuses publish logic)           │
│     - Generic fallback                                     │
│     - Stubs for instagram/x/tiktok                        │
│                                                             │
│  4. Channel Preview Templates                              │
│     - templates/channel_previews/                          │
│     - facebook_feed.html                                   │
│     - generic_text.html                                    │
│     - instagram_post.html, x_post.html, tiktok_post.html  │
│                                                             │
│  5. Universal Preview Modal (Frontend)                     │
│     - Reusable across all planning surfaces                │
│     - Calls preview API                                    │
│     - Injects rendered HTML                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## API Endpoint

### Endpoint

**GET** `/api/preview/post/<post_id>`

**Query Parameters:**
- `channel` (required): `facebook` | `instagram` | `x` | `tiktok` | `generic`
- `mode` (optional): `preview` (default) - **Note:** `publish_simulation` mode is not supported
- `variant` (optional): `full` (default) | `compact`

**Response (Success):**
```json
{
  "success": true,
  "post_id": 12345,
  "channel": "facebook",
  "mode": "preview",
  "variant": "full",
  "html": "<div class=\"channel-preview facebook-preview\">...</div>"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Post not found",
  "error_code": "POST_NOT_FOUND"
}
```

**Error Codes:**
- `POST_NOT_FOUND` - Post ID does not exist in posting_queue
- `INVALID_CHANNEL` - Channel parameter is invalid
- `RENDER_FAILED` - Template rendering failed

**Implementation:** `blueprints/channel_preview_api.py`

---

## Preview Renderer

### Module

**File:** `utils/channel_preview/preview_renderer.py`

**Class:** `ChannelPreviewRenderer`

### Responsibilities

1. **Load Post Data**
   - Queries `posting_queue` with joins to `kb_topics`, `clan_kb_articles`, `content_angles`
   - Returns post data dictionary

2. **Normalize Preview Input**
   - Chooses best text field: `generated_content` → `generated_caption` → empty
   - Preserves metadata: role, platform, status, topic, angle, schedule

3. **Call Channel Formatter**
   - Gets formatter from registry: `get_formatter(channel)`
   - Calls: `formatter.format(post_data, mode, variant)`
   - Returns formatted output with `display_text`, `char_count`, `warnings`, `meta`

4. **Render Template**
   - Determines template name from channel
   - Renders via Jinja2 environment
   - Returns HTML string

### Method Signature

```python
def render(self, post_id: int, channel: str, mode: str = 'preview', 
           variant: str = 'full') -> Dict[str, Any]:
```

---

## Channel Formatter Registry

### Module

**File:** `utils/channel_preview/formatters/registry.py`

### Function

**`get_formatter(channel: str)`**

- Returns formatter instance for channel
- Always returns a formatter (falls back to generic)
- Case-insensitive channel matching

### Registered Formatters

| Channel | Formatter | Status |
|---------|-----------|--------|
| `facebook` | `FacebookFormatter` | ✅ Active |
| `instagram` | `InstagramFormatter` | ⚠️ Stub (uses generic) |
| `x` / `twitter` | `XFormatter` | ⚠️ Stub (uses generic + char warning) |
| `tiktok` | `TikTokFormatter` | ⚠️ Stub (uses generic) |
| `generic` | `GenericFormatter` | ✅ Fallback |

### Formatter Interface

All formatters implement:

```python
def format(self, post_data: Dict[str, Any], mode: str = 'preview', 
           variant: str = 'full') -> Dict[str, Any]:
    """
    Returns:
        {
            'display_text': str,  # Formatted text
            'char_count': int,     # Character count
            'warnings': List[str],  # Warnings (if any)
            'meta': Dict           # Metadata
        }
    """
```

---

## Facebook Formatter

### Module

**File:** `utils/channel_preview/formatters/facebook.py`

### Key Feature

**Reuses publish formatting logic:**

- Extracts shared function: `_format_facebook_text()`
- Used by both preview and publish paths
- `utils/platform_publishers.py::format_message_for_facebook()` now delegates to shared function

### Formatting Rules

1. **Line breaks after em dashes:**
   - Pattern: `"— "` followed by lowercase → `"— \n\n"`

2. **Line breaks between sentences:**
   - Pattern: `".\n"` followed by capital → `".\n\n"`
   - Pattern: `". "` followed by capital → `".\n\n"`

3. **Normalize multiple newlines:**
   - Triple or more newlines → double newlines

### Warnings

- Warns if content > 5,000 chars (Facebook limit is 63,206)
- Warns if content > 10,000 chars (recommended threshold)

---

## Generic Formatter

### Module

**File:** `utils/channel_preview/formatters/generic.py`

### Behavior

- Passes through text as-is
- Preserves paragraphs/newlines
- Basic character count
- No channel-specific formatting

### Use Cases

- Fallback for unknown channels
- Channels without specific formatting rules
- Testing/debugging

---

## Channel Preview Templates

### Template Directory

**Location:** `templates/channel_previews/`

### Template Files

1. **`facebook_feed.html`**
   - Facebook post "card" mockup
   - Shows: page name, timestamp, text content, image region, reaction row
   - Includes "Preview" badge in preview mode
   - Shows metadata (role, status, char count, warnings) in preview mode

2. **`generic_text.html`**
   - Generic text preview
   - Simple header + text content
   - Shows metadata in preview mode

3. **`instagram_post.html`**
   - Instagram-style dark theme mockup
   - Shows: avatar, username, image, caption
   - Minimal implementation (can be enhanced)

4. **`x_post.html`**
   - X/Twitter-style mockup
   - Shows: avatar, username, handle, text, action buttons
   - Character count display (280 limit)

5. **`tiktok_post.html`**
   - TikTok-style mockup
   - Shows: avatar, username, video/image, caption
   - Minimal implementation (can be enhanced)

### Template Context Variables

All templates receive:
- `post` - Post data dictionary
- `formatted` - Formatter output (`display_text`, `char_count`, `warnings`, `meta`)
- `mode` - `'preview'` or `'publish_simulation'`
- `variant` - `'full'` or `'compact'`
- `channel` - Channel name

### Jinja2 Environment

**File:** `utils/channel_preview/jinja_env.py`

- Standalone Jinja2 environment (independent of Flask)
- Follows blog preview pattern
- Template directory: `templates/channel_previews/`

---

## Universal Preview Modal

### Components

1. **JavaScript:** `static/js/channel-preview-modal.js`
   - Class: `ChannelPreviewModal`
   - Global functions: `openChannelPreview()`, `closeChannelPreviewModal()`

2. **CSS:** `static/css/channel-preview-modal.css`
   - Modal styles
   - Channel-specific preview styles (Facebook, Instagram, X, TikTok)

3. **Template:** `templates/includes/channel_preview_modal.html`
   - Modal HTML structure
   - Loading spinner, error state, preview content area

### Usage

```javascript
// Open preview modal
openChannelPreview(postId, 'facebook', 'preview', 'full');

// Parameters:
// - postId: posting_queue.id
// - channel: 'facebook' | 'instagram' | 'x' | 'tiktok' | 'generic'
// - mode: 'preview' (default) | 'publish_simulation'
// - variant: 'full' (default) | 'compact'
```

### Modal Behavior

- Opens with loading spinner
- Calls `/api/preview/post/<postId>?channel=...&mode=...&variant=...`
- Injects returned HTML into modal body
- Shows error state on failure
- Closes on overlay click, ESC key, or close button

---

## UI Integration

### Content Control Board

**Location:** Drill-down panel

**Implementation:**
- Preview button added in `renderPostDetails()` method
- Button calls: `openChannelPreview(post.id, post.platform || 'facebook', 'preview', 'full')`
- Modal included in template

**File:** `static/js/planning/content_control_board.js` (line 746)

### Planning Calendar

**Location:** Week view item cards

**Implementation:**
- Preview button added in `createUnifiedItemCard()` function
- Button appears for items with `posting_queue_id` or `role` + `id`
- Modal included in template

**File:** `static/js/planning/unified-item-card.js` (line 393-410)

### Posting Queue View

**Location:** Actions column per row

**Implementation:**
- Preview button added in table row rendering
- Button calls: `openChannelPreview(item.id, item.platform || 'facebook', 'preview', 'full')`
- Modal included in template

**File:** `templates/posting_queue/view.html` (line 504)

### Sunday Slot Panel

**Location:** Generated content preview section

**Implementation:**
- Preview button added in `showGeneratedContent()` method
- Button appears after generation (when `currentPostId` exists)
- Button calls: `openChannelPreview(postId, 'facebook', 'preview', 'full')`
- Modal included in template

**File:** `static/js/kb_topics/sunday_slot.js` (line 490-514)

---

## Data Rules: What Is Previewable

A post is previewable if:
- It exists in `posting_queue`
- Status is one of: `generated`, `ready`, `approved`, `scheduled` (or any status with content)
- It has text content (`generated_content` or `generated_caption`)

**If missing content:**
- Preview template shows "No content available" state
- Does not crash or error

**Implementation:** `utils/channel_preview/preview_renderer.py::_load_post_data()`

---

## Formatting Logic Reuse

### Facebook Formatting

**Shared Function:** `utils/channel_preview/formatters/facebook.py::_format_facebook_text()`

**Used By:**
1. Preview path: `FacebookFormatter.format()`
2. Publish path: `utils/platform_publishers.py::format_message_for_facebook()`

**Refactoring:**
- Extracted shared formatting logic to `_format_facebook_text()`
- `format_message_for_facebook()` now delegates to shared function
- **No duplication** - single source of truth

---

## Template/Formatter Rules

### Template Rules

1. **All templates must:**
   - Accept `post`, `formatted`, `mode`, `variant`, `channel` context
   - Handle missing content gracefully
   - Show "Preview" badge when `mode == 'preview'`
   - Display metadata in preview mode

2. **Text Rendering:**
   - Split on `\n\n` for paragraphs
   - Replace `\n` with `<br>` within paragraphs
   - Use `<p>` tags for paragraphs

3. **Channel-Specific Styling:**
   - Facebook: White card on light gray background
   - Instagram: Dark theme
   - X: Dark theme with blue accents
   - TikTok: Dark theme

### Formatter Rules

1. **All formatters must:**
   - Implement `format(post_data, mode, variant)` method
   - Return dict with `display_text`, `char_count`, `warnings`, `meta`
   - Handle missing text gracefully

2. **Text Selection:**
   - Prefer `generated_content` over `generated_caption`
   - Fallback to empty string if neither exists

3. **Warnings:**
   - Channel-specific character limit warnings
   - Content quality warnings (optional)

---

## How to Add a New Channel Template

1. **Create Template File:**
   - Location: `templates/channel_previews/<channel>_<type>.html`
   - Example: `templates/channel_previews/instagram_carousel.html`
   - Must accept context: `post`, `formatted`, `mode`, `variant`, `channel`

2. **Create Formatter (if needed):**
   - Location: `utils/channel_preview/formatters/<channel>.py`
   - Inherit from `GenericFormatter` or implement `format()` method
   - Return: `{'display_text': str, 'char_count': int, 'warnings': List[str], 'meta': Dict}`

3. **Register Formatter:**
   - File: `utils/channel_preview/formatters/registry.py`
   - Add to `_formatters` dict: `_formatters['channel_name'] = ChannelFormatter()`

4. **Update Template Mapping:**
   - File: `utils/channel_preview/preview_renderer.py`
   - Add to `_get_template_name()` method's `template_map` dict

## How to Add a New Formatter

1. **Create Formatter Class:**
   ```python
   from utils.channel_preview.formatters.generic import GenericFormatter
   
   class MyChannelFormatter(GenericFormatter):
       def format(self, post_data, mode='preview', variant='full'):
           # Your formatting logic
           result = super().format(post_data, mode, variant)
           # Modify result as needed
           return result
   ```

2. **Register in Registry:**
   - File: `utils/channel_preview/formatters/registry.py`
   - Import your formatter
   - Add: `_formatters['channel_name'] = MyChannelFormatter()`

## Preview Surfaces

There are two ways to consume channel previews, both using the same renderer, templates, and formatter registry:

1. **Canonical full-page preview route (recommended):**
   - `GET /preview/post/<post_id>?channel=facebook`
   - Renders the channel preview HTML inside a simple, high-contrast page frame
   - Used by all planning surfaces via \"Preview\" buttons (opens in a new tab)

2. **Universal modal (optional / secondary):**
   - Modal HTML: `{% include 'includes/channel_preview_modal.html' %}` (mounted once under `<body>` in `base.html`)
   - CSS: `<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/channel-preview-modal.css') }}\">`
   - JS: `<script src=\"{{ url_for('static', filename='js/channel-preview-modal.js') }}\"></script>`
   - Can be used for inline preview UX, but the full-page route is the authoritative human-facing surface.

## Integration Checklist Per Surface

### Content Control Board

- ✅ Preview button added to drill-down panel and Sunday card
- ✅ Button opens `/preview/post/<id>?channel=facebook` in a new tab

### Planning Calendar (Week View)

- ✅ Preview button added to unified item cards for `posting_queue` items
- ✅ Button opens `/preview/post/<posting_queue_id>?channel=facebook` in a new tab

### Posting Queue View

- ✅ Preview button added to actions column
- ✅ Button can open `/preview/post/<id>?channel=<platform>` in a new tab

### Sunday Slot Panel

- ✅ \"Preview\" button added after generation
- ✅ Button opens `/preview/post/<post_id>?channel=facebook` in a new tab

---

## Backward Compatibility

### Blog Preview Unchanged

- ✅ Blog preview route (`/preview/<post_id>/`) remains unchanged
- ✅ Blog preview templates remain unchanged
- ✅ Blog preview rendering logic remains unchanged
- ✅ No breaking changes to existing blog preview functionality

### Planning Surfaces

- ✅ Compact text previews remain (for list views)
- ✅ Full-page preview route is the canonical human-facing preview surface
- ✅ Existing inline previews continue to work
- ✅ Modal preview is available as an enhancement but is no longer required for Phase 4 closure

---

## Known Limitations

### Phase 4 Scope

**Included:**
- Facebook preview (full implementation)
- Generic preview (fallback)
- Modal integration in 4 surfaces
- Formatter registry with stubs

**Explicitly Excluded:**
- Multi-channel orchestration
- Bulk preview generation
- Preview history/versioning
- Advanced channel-specific features (Instagram carousel preview, X thread preview, etc.)

**Stubs (Can Be Enhanced Later):**
- Instagram formatter (currently uses generic)
- X formatter (generic + char warning)
- TikTok formatter (generic)

---

## Testing

### Manual Test Checklist

1. ✅ **Content Control Board**
   - Generate Sunday Deep Dive post
   - Open drill-down panel
   - Click "Preview" button
   - Modal opens with Facebook preview

2. ✅ **Planning Calendar**
   - Navigate to week with Sunday Deep Dive
   - Click preview button on item card
   - Modal opens with Facebook preview

3. ✅ **Posting Queue**
   - View posting queue
   - Click preview icon on row
   - Modal opens with channel-appropriate preview

4. ✅ **Sunday Slot Panel**
   - Generate post in Sunday slot
   - Click "Preview in Modal" button
   - Modal opens with Facebook preview

5. ✅ **Blog Preview**
   - Navigate to `/preview/<post_id>/`
   - Blog preview still works unchanged

### Consistency Tests

- Same post previewed from different surfaces must render identically
- All previews use same API endpoint
- All previews use same formatter for same channel

---

## File Structure

### Python Modules

```
utils/channel_preview/
├── __init__.py
├── preview_renderer.py      # Main renderer
├── jinja_env.py              # Jinja2 environment
└── formatters/
    ├── __init__.py
    ├── registry.py           # Formatter registry
    ├── generic.py            # Generic formatter
    ├── facebook.py           # Facebook formatter
    ├── instagram.py          # Instagram formatter (stub)
    ├── x.py                  # X formatter (stub)
    └── tiktok.py             # TikTok formatter (stub)
```

### Templates

```
templates/
├── channel_previews/
│   ├── facebook_feed.html
│   ├── generic_text.html
│   ├── instagram_post.html
│   ├── x_post.html
│   └── tiktok_post.html
└── includes/
    └── channel_preview_modal.html
```

### Static Assets

```
static/
├── js/
│   └── channel-preview-modal.js
└── css/
    └── channel-preview-modal.css
```

### API

```
blueprints/
└── channel_preview_api.py
```

---

## User Guide: How to Preview a Sunday Deep Dive

1. **Generate Post:**
   - Navigate to `/kb-topics/editor`
   - Select week, topic, and source article
   - Optionally propose/select an angle
   - Click "Generate"

2. **Preview from Sunday Slot:**
   - After generation, click "Preview in Modal" button
   - Modal opens with Facebook preview

3. **Preview from Content Control Board:**
   - Navigate to `/planning/content-control-board`
   - Click on Sunday cell
   - Drill-down panel opens
   - Click "Preview" button

4. **Preview from Planning Calendar:**
   - Navigate to `/planning/calendar`
   - Find Sunday Deep Dive in week view
   - Click preview icon on item card

5. **Preview from Posting Queue:**
   - Navigate to `/posting-queue`
   - Find post in table
   - Click preview icon in actions column

**Note:** All previews use the same unified system and show identical formatting.

## Related Documentation

- **Discovery Report:** `docs/CHANNEL_PREVIEW_SYSTEM_DISCOVERY_REPORT.md`
- **Content Roles Framework:** `docs/CONTENT_ROLES_FRAMEWORK.md`
- **Angles Layer:** `docs/ANGLES_LAYER_IMPLEMENTATION.md`
- **KB Page:** `/kb/backend/channel_preview`

---

## Changelog

**2026-01-25: Phase 4 Implementation Complete**
- Unified preview API endpoint created
- Preview renderer implemented
- Channel formatter registry created
- Facebook formatter reuses publish logic
- Channel preview templates created
- Universal preview modal component created
- Integrated into 4 planning surfaces
- Blog preview remains unchanged

---

**End of Documentation**
