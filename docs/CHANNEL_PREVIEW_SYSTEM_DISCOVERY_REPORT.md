# Phase 4 — Unified Channel Preview System: Discovery & Audit Report

**Date:** 2026-01-25  
**Status:** 🔍 **DISCOVERY COMPLETE** — No design, no coding  
**Purpose:** Comprehensive audit of all existing preview, mock-up, and rendering mechanisms across the system

---

## Executive Summary

**Finding:** Multiple preview systems exist, but **no unified, channel-aware preview system** for social media content. Preview functionality is fragmented across:

1. **Blog Preview System** (canonical, well-documented) — Full HTML rendering for blog posts
2. **Social Media Previews** (ad-hoc, channel-specific) — Facebook feed post preview, Instagram carousel review, message manager preview
3. **Planning Surface Previews** (text-only, minimal) — Content Control Board, Sunday slot, posting queue
4. **Newsletter Preview** (separate system) — HTML/text rendering for newsletters

**Key Gaps:**
- No reusable preview abstraction
- No channel-specific formatting utilities
- Preview logic embedded in individual features
- Text truncation logic duplicated across surfaces
- No unified preview API

**Recommendation:** Design a unified Channel Preview System that:
- Reuses blog preview architecture (Jinja2 rendering, template-based)
- Extends to channel-specific formatting (Facebook, Instagram, X, etc.)
- Provides reusable preview components for planning surfaces
- Centralizes preview text truncation and formatting logic

---

## 1. Blog Preview System (Baseline Reference)

### 1.1 Architecture

**Location:** `blog-launchpad/publish/`

**Key Components:**

1. **Preview Handler** (`preview_handler.py`)
   - Route handler: `preview_post(post_id)`
   - Uses unified data preparation: `prepare_post_data(post_id)`
   - Uses unified rendering: `render_post_html(post, sections, image_replacements=None)`
   - Template: `templates/launchpad/post_preview.html`

2. **Post Renderer** (`post_renderer.py`)
   - **Single source of truth** for post HTML rendering
   - **Independent of Flask** — uses standalone Jinja2 environment
   - Template: `templates/launchpad/clan_post_raw.html`
   - Handles image path replacements (for publishing vs preview)
   - Recipe section inline styling support

3. **Post Data Loader** (`post_data_loader.py`)
   - Unified data preparation
   - Fetches post + sections from database
   - Handles image mappings

**Route:** `/preview/<post_id>/` (via blueprint registration)

**Template Structure:**
```
templates/launchpad/post_preview.html
  └─> Uses rendered_content from post_renderer
  └─> Wraps in preview UI (title, header image, red divider)
```

### 1.2 How Content is Passed

**Data Flow:**
1. `preview_post(post_id)` called
2. `prepare_post_data(post_id)` → returns `(post, sections)`
3. `render_post_html(post, sections, image_replacements=None)` → returns HTML string
4. HTML wrapped in preview template
5. Template renders with `{{ rendered_content|safe }}`

**Key Design Decision:**
- Preview shows **EXACT HTML** that will be published (except image paths)
- Template wrapper provides UI elements but does NOT modify content
- No caching — always generates fresh HTML

### 1.3 Layout / Formatting Decisions

**Template:** `templates/launchpad/clan_post_raw.html`
- Blog-specific HTML structure
- Section-based layout
- Image handling with captions
- Recipe section special handling

**Styling:**
- Uses `static/css/dist/clan_blog.css`
- Blog-specific typography and spacing
- Responsive design

**Image Handling:**
- Preview: Local paths (no replacements)
- Publishing: CDN URLs (via `image_replacements` dict)

### 1.4 Where Previews are Surfaced

**Primary Location:**
- Route: `/preview/<post_id>/`
- Full-page preview (not embedded)

**Documentation:**
- `blog-core/docs/reference/workflow/preview.md` — Comprehensive reference
- `blog-core/docs/reference/preview_system_comparison.md` — Legacy vs new comparison

### 1.5 Reuse Across Workflows

**Current Reuse:**
- ✅ Used by blog publication workflow
- ✅ Used by launchpad preview
- ❌ **NOT reused** for social media previews
- ❌ **NOT reused** for planning surfaces

### 1.6 Blog-Specific Assumptions

**Assumptions that make it blog-specific:**
1. **HTML structure** — Assumes blog post structure (header, sections, conclusion)
2. **Template inheritance** — Uses blog-specific base templates
3. **Styling** — Uses blog CSS (`clan_blog.css`)
4. **Image handling** — Assumes blog image structure (header image, section images)
5. **Content structure** — Assumes sections with headings, text, images

**Reusability Assessment:**
- ✅ **Reusable:** Rendering architecture (Jinja2, template-based)
- ✅ **Reusable:** Data preparation pattern
- ❌ **Not reusable:** Blog-specific HTML structure
- ❌ **Not reusable:** Blog-specific CSS
- ✅ **Partially reusable:** Image handling (can be adapted)

---

## 2. Social / Non-Blog Preview Mechanisms

### 2.1 Facebook Feed Post Preview

**Location:** `templates/launchpad/facebook_feed_post_config_backup.html`

**Status:** ⚠️ **BACKUP FILE** — Appears to be deprecated/archived

**What it previews:**
- Facebook feed post structure
- Image preview (1200×630)
- Caption text
- Facebook UI mockup (page name, timestamp, like/comment/share buttons)

**Implementation:**
- Inline HTML/CSS mockup
- JavaScript updates preview as user edits
- Shows Facebook-style UI elements

**Channel Awareness:**
- ✅ **Channel-aware** — Facebook-specific UI mockup
- ✅ **Format-aware** — Shows image dimensions (1200×630)

**Authoritativeness:**
- ⚠️ **Indicative only** — Visual mockup, not actual Facebook rendering
- ⚠️ **Backup file** — May not be in active use

**Duplication:**
- Appears to be standalone — no shared logic with other previews

**File Paths:**
- Template: `templates/launchpad/facebook_feed_post_config_backup.html`
- Lines 870-924: Preview section with Facebook UI mockup

### 2.2 Instagram Carousel Review

**Location:** `templates/launchpad/instagram/carousel_review.html`

**Status:** ✅ **ACTIVE** — Used for Instagram carousel review

**What it previews:**
- Instagram carousel slides (images)
- Caption text
- Slide count
- Caption statistics (length, hashtags)

**Implementation:**
- Full-page review interface
- API endpoint: `/launchpad/api/instagram/carousel/preview/<post_id>`
- JavaScript renders slides in carousel preview container
- Shows Instagram-style dark theme UI

**Channel Awareness:**
- ✅ **Channel-aware** — Instagram-specific (carousel format)
- ✅ **Format-aware** — Shows slide structure

**Authoritativeness:**
- ✅ **Authoritative** — Shows actual carousel slides that will be posted

**Duplication:**
- Standalone implementation
- No shared logic with other previews

**File Paths:**
- Template: `templates/launchpad/instagram/carousel_review.html`
- JavaScript: Inline in template (lines 400-550)
- API: `blueprints/launchpad/instagram_carousel.py`

### 2.3 Message Manager Preview

**Location:** `static/js/message-manager-preview.js`

**Status:** ✅ **ACTIVE** — Used in LLM actions workflow

**What it previews:**
- Assembled message content from multiple elements
- Text-only preview (no channel-specific formatting)
- Character count statistics

**Implementation:**
- JavaScript class: `MessageManagerPreview`
- Assembles preview from enabled elements
- Updates preview display dynamically
- No channel-specific formatting

**Channel Awareness:**
- ❌ **Not channel-aware** — Generic text preview
- ❌ **Not format-aware** — Plain text only

**Authoritativeness:**
- ⚠️ **Indicative** — Shows assembled text, not formatted output

**Duplication:**
- Standalone JavaScript module
- No shared logic with other previews

**File Paths:**
- JavaScript: `static/js/message-manager-preview.js`
- Related: `static/js/preview-manager.js` (general preview manager)

### 2.4 Preview Manager (General)

**Location:** `static/js/preview-manager.js`

**Status:** ✅ **ACTIVE** — General preview management utility

**What it does:**
- Manages preview iframes and modes
- Handles live/static/fullscreen preview modes
- Auto-refresh functionality
- Preview container management

**Channel Awareness:**
- ❌ **Not channel-aware** — Generic preview container manager
- ❌ **Not format-aware** — Just manages display, not content formatting

**Authoritativeness:**
- ⚠️ **Infrastructure only** — Doesn't render content, just manages display

**Duplication:**
- Used by message manager and other preview systems
- Provides infrastructure, not content rendering

**File Paths:**
- JavaScript: `static/js/preview-manager.js`
- Also exists in: `static/llm_actions/js/preview-manager.js` (duplicate?)

### 2.5 Mini Preview Panel (Header Workspace)

**Location:** `static/js/header/mini-preview-panel.js`

**Status:** ✅ **ACTIVE** — Used in header workspace

**What it previews:**
- Post sections (description, draft content)
- Tab-based interface (Overview, Sections, etc.)
- Accordion-style section display

**Implementation:**
- JavaScript tab switching
- Loads sections via API: `/authoring/api/posts/${postId}/sections`
- Shows draft/polished content
- No channel-specific formatting

**Channel Awareness:**
- ❌ **Not channel-aware** — Generic content preview
- ❌ **Not format-aware** — Plain text display

**Authoritativeness:**
- ⚠️ **Indicative** — Shows content state, not formatted output

**File Paths:**
- JavaScript: `static/js/header/mini-preview-panel.js`
- Template: `templates/header/includes/mini_preview_panel.html`
- CSS: `static/css/header/mini-preview-panel.css`

---

## 3. Planning & Calendar Surfaces

### 3.1 Content Control Board

**Location:** `templates/planning/content_control_board.html` + `static/js/planning/content_control_board.js`

**Status:** ✅ **ACTIVE** — Primary planning surface

**Preview Behavior:**

**Matrix View (Main Display):**
- Shows **text-only preview** (first ~80 characters)
- Function: `_get_preview(text, max_length=80)` in `blueprints/planning_api_content_control_board.py`
- Truncates at word boundary
- No channel-specific formatting
- No visual mockup

**Drill-Down Panel:**
- Shows full post content in `<div class="panel-content-text">`
- Simple text replacement: `content.replace(/\n/g, '<br>')`
- No channel-specific formatting
- No visual mockup

**Implementation:**
```javascript
// Matrix cell preview
<div class="post-preview">${post.preview || 'No preview'}</div>

// Drill-down panel
<div class="panel-content-text">${(post.generated_content || post.generated_caption || 'No content').replace(/\n/g, '<br>')}</div>
```

**Channel Awareness:**
- ❌ **Not channel-aware** — Generic text preview
- ❌ **Not format-aware** — Plain text only

**Authoritativeness:**
- ⚠️ **Indicative** — Text preview only, not formatted output

**Duplication:**
- Text truncation logic (`_get_preview`) is duplicated in posting queue view

**File Paths:**
- Template: `templates/planning/content_control_board.html`
- JavaScript: `static/js/planning/content_control_board.js`
- API: `blueprints/planning_api_content_control_board.py`
- CSS: `static/css/planning/content_control_board.css`

### 3.2 Sunday Slot (KB Topic Rota Editor)

**Location:** `templates/kb_topics/rota_editor.html` + `static/js/kb_topics/sunday_slot.js`

**Status:** ✅ **ACTIVE** — Phase 2/3 implementation

**Preview Behavior:**

**Generated Content Display:**
- Shows generated post text in `<div class="preview-content">`
- Plain text display: `content.textContent = data.content`
- Shows word count and validation status
- No channel-specific formatting
- No visual mockup

**Implementation:**
```javascript
showGeneratedContent(data) {
    const content = document.getElementById('sunday-preview-content');
    content.textContent = data.content;  // Plain text
    // Shows meta: word count, validation status
}
```

**Channel Awareness:**
- ⚠️ **Partially aware** — Knows it's for Facebook (Sunday DEPTH_LONG)
- ❌ **Not format-aware** — Plain text display only

**Authoritativeness:**
- ⚠️ **Indicative** — Shows generated text, not formatted Facebook post

**File Paths:**
- Template: `templates/kb_topics/rota_editor.html` (lines 118-123)
- JavaScript: `static/js/kb_topics/sunday_slot.js` (lines 490-514)
- CSS: `static/css/kb_topics/rota_editor.css`

### 3.3 Posting Queue View

**Location:** `templates/posting_queue/view.html`

**Status:** ✅ **ACTIVE** — Queue management interface

**Preview Behavior:**

**Content Preview Column:**
- Shows content preview (first ~100 characters)
- Content type-specific formatting:
  - Product posts: Product name or caption
  - Language posts: Word/phrase only (Scots text)
  - Other types: Caption or extracted text
- Truncates: `content.length > 100 ? content.substring(0, 100) + '...' : content`
- Removes newlines: `content.replace(/\n/g, ' ')`
- Shows thumbnail image if available

**Implementation:**
```javascript
// Format content based on type
if (item.content_type === 'product') {
    content = item.product_name || item.generated_caption || 'No content';
} else if (item.content_type && item.content_type.startsWith('weekly_')) {
    content = item.idea_title;  // Scots text only
} else {
    content = item.generated_caption || 'No content';
}

// Clean and truncate
content = content.replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();
const contentPreview = content.length > 100 ? content.substring(0, 100) + '...' : content;
```

**Channel Awareness:**
- ⚠️ **Partially aware** — Shows platform icon (Facebook, Instagram, etc.)
- ❌ **Not format-aware** — Plain text preview only

**Authoritativeness:**
- ⚠️ **Indicative** — Text preview only, not formatted output

**Duplication:**
- Text truncation logic duplicated from Content Control Board
- Content type formatting logic is unique to this view

**File Paths:**
- Template: `templates/posting_queue/view.html` (lines 280-510)
- Blueprint: `blueprints/posting_queue_view.py`

### 3.4 Planning Calendar (Week View)

**Location:** `templates/planning/calendar/` + `static/js/planning/calendar-week-view.js`

**Status:** ✅ **ACTIVE** — Calendar planning interface

**Preview Behavior:**

**Unified Item Cards:**
- Shows item titles and descriptions
- No content preview
- Shows scheduled time, status badges
- No channel-specific formatting

**Implementation:**
- Uses `createUnifiedItemCard()` function
- Shows metadata only (title, type, status)
- No content preview

**Channel Awareness:**
- ⚠️ **Partially aware** — Can have `dataset.channel` attribute
- ❌ **Not format-aware** — No content formatting

**File Paths:**
- JavaScript: `static/js/planning/unified-item-card.js`
- Template: Various calendar templates

---

## 4. Existing Abstractions (or Lack Thereof)

### 4.1 Preview-Related Code Patterns

**Search Results:**
- 425 files contain "preview" (case-insensitive)
- 30 files contain "render" (case-insensitive)
- 20 files contain "mock" (case-insensitive)

**Key Findings:**

1. **No Unified Preview Interface**
   - No abstract base class for previews
   - No shared preview API
   - Each preview system is standalone

2. **Preview Manager (Generic)**
   - `static/js/preview-manager.js` — Infrastructure only
   - Manages iframes and display modes
   - Does NOT render content

3. **Message Manager Preview**
   - `static/js/message-manager-preview.js` — Text assembly only
   - No channel-specific formatting

### 4.2 Channel-Specific Rendering Logic

**Found:**

1. **Facebook Formatting** (`utils/platform_publishers.py`)
   - Function: `format_message_for_facebook(message_text: str)`
   - Adds line breaks for better Facebook display
   - Pattern-based text transformation
   - **Used for publishing, NOT preview**

2. **Instagram Carousel Rendering**
   - `templates/launchpad/instagram/carousel_review.html`
   - Channel-specific template
   - Shows carousel structure

3. **Output Channel Resolver** (`utils/output_channel_resolver.py`)
   - Resolves pipeline definitions for output channels
   - Does NOT handle preview rendering
   - Infrastructure only

### 4.3 Preview Logic Embedded in Features

**Examples:**

1. **Content Control Board**
   - Preview truncation embedded in API: `_get_preview()` function
   - Text formatting embedded in JavaScript: `.replace(/\n/g, '<br>')`

2. **Posting Queue View**
   - Content formatting embedded in JavaScript template
   - Type-specific logic embedded in view

3. **Sunday Slot**
   - Preview display embedded in `showGeneratedContent()` method
   - No reusable component

---

## 5. Data & State

### 5.1 Preview Data Sources

**Persisted Data:**
- `posting_queue.generated_content` — Full post content
- `posting_queue.generated_caption` — Caption text
- `posting_queue.role` — Content role (for formatting rules)
- `posting_queue.platform` — Target platform

**Transient Generation:**
- Blog preview: Generated fresh each time (no caching)
- Instagram carousel: Generated from post sections
- Message manager: Assembled from elements

### 5.2 Preview Mode vs Ready/Published Mode

**Current State:**
- ❌ **No explicit preview mode flag**
- Preview is implicit (route-based: `/preview/<id>/`)
- Published mode: Image paths replaced with CDN URLs
- Preview mode: Local image paths

**Blog Preview Distinction:**
```python
# Preview: image_replacements=None
html_content = render_post_html(post, sections, image_replacements=None)

# Publishing: image_replacements=uploaded_images
upload_html = render_post_html(post, sections, image_replacements=uploaded_images)
```

### 5.3 Preview-Related Fields/Flags

**Found:**
- `posting_queue.status` — Indicates post state (generated, approved, scheduled, published)
- `posting_queue.role` — Content role (affects formatting rules)
- `posting_queue.platform` — Target platform (affects formatting)
- `posting_queue.angle_id` — Editorial angle (Phase 3)

**No Preview-Specific Flags:**
- No `is_preview` flag
- No `preview_mode` field
- Preview is determined by route/context

---

## 6. Documentation & Historical Artifacts

### 6.1 Active Documentation

**Found:**

1. **Blog Preview Reference** (`blog-core/docs/reference/workflow/preview.md`)
   - Comprehensive blog preview documentation
   - Content priority system
   - Image handling
   - Template structure

2. **Preview System Comparison** (`blog-core/docs/reference/preview_system_comparison.md`)
   - Legacy vs new system comparison
   - Missing elements analysis
   - Implementation recommendations

3. **Preview System Enhancement Plan** (`blog-core/docs/temp/preview_system_enhancement_plan.md`)
   - Enhancement plan for blog preview
   - Content prioritization system
   - Placeholder system

### 6.2 Historical/Archived Artifacts

**Found:**

1. **CLAN Blog Preview Implementation Plan** (`blog-core/docs/~archive/temp/clan_blog_preview_implementation_plan.md`)
   - Historical implementation plan
   - Blog preview front-end replication
   - Status: Mostly complete

2. **Article Structure & Preview UI Plans** (Multiple files in `~archive/temp/`)
   - Wireframes, mockups, implementation checklists
   - Status: Archived, not implemented

3. **Facebook Posting Implementation Plan** (`blog-launchpad/docs/temp/facebook_posting_implementation_plan.md`)
   - Facebook posting hub design
   - Mentions preview functionality
   - Status: Planning phase

### 6.3 Abandoned/Partial Implementations

**Found:**

1. **Facebook Feed Post Config Backup** (`templates/launchpad/facebook_feed_post_config_backup.html`)
   - Contains Facebook post preview mockup
   - Status: ⚠️ **BACKUP FILE** — May not be active
   - Has Facebook UI mockup (lines 870-924)

2. **Multiple Preview Templates**
   - `templates/post_info/post_preview.html`
   - `templates/llm_actions/preview_post.html`
   - `blog-llm-actions/templates/preview_post.html`
   - Status: May be duplicates or legacy

---

## 7. Inventory Summary

### 7.1 Preview Systems by Status

| System | Status | Channel-Aware | Format-Aware | Authoritative | Location |
|--------|--------|---------------|--------------|---------------|----------|
| **Blog Preview** | ✅ Active | ❌ No | ❌ No (blog-specific) | ✅ Yes | `blog-launchpad/publish/` |
| **Instagram Carousel** | ✅ Active | ✅ Yes | ✅ Yes | ✅ Yes | `templates/launchpad/instagram/` |
| **Facebook Feed Post** | ⚠️ Backup | ✅ Yes | ✅ Yes | ⚠️ Indicative | `templates/launchpad/facebook_feed_post_config_backup.html` |
| **Message Manager** | ✅ Active | ❌ No | ❌ No | ⚠️ Indicative | `static/js/message-manager-preview.js` |
| **Content Control Board** | ✅ Active | ❌ No | ❌ No | ⚠️ Indicative | `templates/planning/content_control_board.html` |
| **Sunday Slot** | ✅ Active | ⚠️ Partial | ❌ No | ⚠️ Indicative | `templates/kb_topics/rota_editor.html` |
| **Posting Queue** | ✅ Active | ⚠️ Partial | ❌ No | ⚠️ Indicative | `templates/posting_queue/view.html` |
| **Mini Preview Panel** | ✅ Active | ❌ No | ❌ No | ⚠️ Indicative | `static/js/header/mini-preview-panel.js` |
| **Newsletter Preview** | ✅ Active | ❌ No | ⚠️ Partial | ✅ Yes | `blueprints/newsletter_preview.py` |

### 7.2 Preview Systems by Purpose

**Full-Page Previews:**
- Blog preview (`/preview/<post_id>/`)
- Instagram carousel review (`/launchpad/instagram/carousel/review/<post_id>`)
- Newsletter preview (`/newsletter/issue/<issue_id>/preview`)

**Embedded Previews:**
- Content Control Board (matrix cells + drill-down)
- Sunday slot (generated content display)
- Posting queue (content preview column)
- Mini preview panel (header workspace)

**Mockup Previews:**
- Facebook feed post config (backup file)
- Message manager (text assembly)

---

## 8. Reuse Assessment

### 8.1 Can Be Reused As-Is

**✅ Blog Preview Architecture:**
- **Component:** Jinja2 rendering pattern (`post_renderer.py`)
- **Reusability:** High — Template-based rendering is channel-agnostic
- **Adaptation Needed:** Template structure (blog-specific → channel-specific)
- **Recommendation:** **REUSE** — Extract rendering engine, create channel-specific templates

**✅ Post Data Loader:**
- **Component:** `prepare_post_data(post_id)`
- **Reusability:** High — Data preparation is content-agnostic
- **Adaptation Needed:** None for blog posts, may need extension for social posts
- **Recommendation:** **REUSE** — Already unified, can be extended

### 8.2 Can Be Adapted

**⚠️ Instagram Carousel Review:**
- **Component:** Carousel preview template and JavaScript
- **Reusability:** Medium — Channel-specific but pattern is reusable
- **Adaptation Needed:** Generalize to "carousel preview" pattern, make channel-agnostic
- **Recommendation:** **ADAPT** — Extract carousel preview pattern, make channel-configurable

**⚠️ Facebook Formatting Function:**
- **Component:** `format_message_for_facebook()` in `utils/platform_publishers.py`
- **Reusability:** Medium — Facebook-specific but pattern is reusable
- **Adaptation Needed:** Generalize to channel-specific formatters
- **Recommendation:** **ADAPT** — Create channel formatter registry

### 8.3 Should Be Retired

**❌ Facebook Feed Post Config Backup:**
- **Component:** `templates/launchpad/facebook_feed_post_config_backup.html`
- **Status:** Backup file, may not be active
- **Recommendation:** **VERIFY THEN RETIRE** — Check if still in use, if not, archive

**❌ Duplicate Preview Templates:**
- **Components:** Multiple `preview_post.html` templates in different locations
- **Status:** May be duplicates or legacy
- **Recommendation:** **AUDIT THEN CONSOLIDATE** — Identify active templates, remove duplicates

### 8.4 Conflicts with Unified Approach

**⚠️ Text Truncation Logic:**
- **Location:** Duplicated in Content Control Board and Posting Queue
- **Conflict:** Different truncation lengths (80 vs 100 chars)
- **Recommendation:** **CENTRALIZE** — Create unified preview text utility

**⚠️ Content Formatting Logic:**
- **Location:** Embedded in Posting Queue view JavaScript
- **Conflict:** Type-specific logic scattered across views
- **Recommendation:** **CENTRALIZE** — Create unified content formatter

---

## 9. Gaps Identified

### 9.1 What Does Not Exist

**❌ Unified Preview API:**
- No single endpoint for "preview this content for this channel"
- Each preview system has its own API/route

**❌ Channel-Specific Formatting Utilities:**
- No reusable formatters for Facebook, Instagram, X, etc.
- Only `format_message_for_facebook()` exists (for publishing, not preview)

**❌ Preview Component Library:**
- No reusable preview components for planning surfaces
- Each surface implements its own preview display

**❌ Channel-Aware Preview Templates:**
- No templates that render content as it will appear on specific channels
- Blog preview is blog-specific, not channel-agnostic

**❌ Preview Text Utility:**
- Text truncation logic duplicated across surfaces
- No unified preview text formatter

### 9.2 Where Preview Logic is Being Reinvented

**Text Truncation:**
- Content Control Board: `_get_preview(text, max_length=80)`
- Posting Queue: `content.substring(0, 100) + '...'`
- **Reinvention:** Same logic, different implementations

**Content Formatting:**
- Posting Queue: Type-specific formatting (product, language, etc.)
- Content Control Board: Simple text replacement
- **Reinvention:** Similar logic, different implementations

**Preview Display:**
- Sunday Slot: `content.textContent = data.content`
- Content Control Board: `content.replace(/\n/g, '<br>')`
- **Reinvention:** Similar display needs, different implementations

### 9.3 Where No Preview Exists But Needed

**Planning Surfaces:**
- Content Control Board: Text-only preview (needs channel mockup)
- Sunday Slot: Plain text preview (needs Facebook mockup)
- Posting Queue: Text preview (needs channel-specific formatting)

**Generation Workflows:**
- Angle proposal: No preview of generated angles
- Content generation: No preview before approval

**Multi-Channel Planning:**
- No unified preview across channels
- No side-by-side channel comparison

---

## 10. Risks & Conflicts

### 10.1 Duplicated Logic

**Text Truncation:**
- **Risk:** Inconsistent behavior across surfaces
- **Location:** Content Control Board (80 chars) vs Posting Queue (100 chars)
- **Impact:** Medium — User confusion, maintenance burden

**Content Formatting:**
- **Risk:** Inconsistent display of same content
- **Location:** Posting Queue (type-specific) vs Content Control Board (generic)
- **Impact:** Medium — User confusion

### 10.2 Multiple Sources of Truth

**Preview Text Generation:**
- Content Control Board API: `_get_preview()` function
- Posting Queue JavaScript: Inline truncation
- **Conflict:** Two different implementations of same concept

**Content Display:**
- Blog preview: Full HTML rendering
- Planning surfaces: Plain text display
- **Conflict:** Different representations of same content

### 10.3 UI Surfaces Requiring Refactoring

**If Unified System Introduced:**

1. **Content Control Board**
   - Matrix cells: Currently text-only, would need channel mockup component
   - Drill-down panel: Currently plain text, would need formatted preview
   - **Refactoring Effort:** Medium

2. **Sunday Slot**
   - Preview section: Currently plain text, would need Facebook mockup
   - **Refactoring Effort:** Low (already has preview container)

3. **Posting Queue**
   - Content preview column: Currently text truncation, would need channel formatting
   - **Refactoring Effort:** Medium

4. **Planning Calendar**
   - Item cards: Currently metadata only, may need content preview
   - **Refactoring Effort:** Low (optional enhancement)

### 10.4 Regression Risks

**If Unified System Introduced:**

1. **Blog Preview**
   - **Risk:** Low — Blog preview is well-isolated
   - **Mitigation:** Keep blog preview as-is, extend for channels

2. **Instagram Carousel**
   - **Risk:** Medium — Active system, may conflict
   - **Mitigation:** Integrate carousel preview into unified system

3. **Planning Surfaces**
   - **Risk:** Medium — Multiple surfaces depend on current preview behavior
   - **Mitigation:** Maintain backward compatibility, gradual migration

---

## 11. Recommendations (Non-Prescriptive)

### 11.1 Areas Suitable for Reuse

**✅ Blog Preview Rendering Architecture:**
- **Recommendation:** Extract rendering engine from blog preview
- **Rationale:** Template-based, channel-agnostic core
- **Approach:** Create `ChannelPreviewRenderer` class, reuse Jinja2 pattern

**✅ Post Data Preparation:**
- **Recommendation:** Extend `prepare_post_data()` for social posts
- **Rationale:** Already unified, can be extended
- **Approach:** Add social post data preparation alongside blog post

**✅ Instagram Carousel Pattern:**
- **Recommendation:** Generalize carousel preview pattern
- **Rationale:** Good pattern for multi-slide content
- **Approach:** Extract carousel preview component, make channel-configurable

### 11.2 Areas That Should Be Deprecated

**❌ Facebook Feed Post Config Backup:**
- **Recommendation:** Verify usage, then archive
- **Rationale:** Backup file, may not be active
- **Approach:** Check route registration, remove if unused

**❌ Duplicate Preview Templates:**
- **Recommendation:** Audit and consolidate
- **Rationale:** Multiple templates may cause confusion
- **Approach:** Identify active templates, remove duplicates

**❌ Embedded Preview Logic:**
- **Recommendation:** Extract to unified utilities
- **Rationale:** Duplicated logic across surfaces
- **Approach:** Create preview text utility, content formatter utility

### 11.3 Architectural Directions

**✅ Template-Based Rendering:**
- **Direction:** Extend blog preview's template-based approach
- **Rationale:** Proven pattern, channel-agnostic core
- **Approach:** Create channel-specific templates, reuse rendering engine

**✅ Component-Based Preview:**
- **Direction:** Create reusable preview components
- **Rationale:** Planning surfaces need embedded previews
- **Approach:** Create React/Vanilla JS components for channel mockups

**✅ Channel Formatter Registry:**
- **Direction:** Centralize channel-specific formatting
- **Rationale:** Currently scattered (Facebook formatter exists, others don't)
- **Approach:** Create formatter registry, implement per-channel formatters

**✅ Preview API Layer:**
- **Direction:** Create unified preview API
- **Rationale:** Currently each system has its own API
- **Approach:** Create `/api/preview/<channel>/<content_id>` endpoint

---

## 12. Explicit Uncertainties

### 12.1 Active vs Archived Files

**Uncertainty:** Which preview templates are actively used?

**Files in Question:**
- `templates/launchpad/facebook_feed_post_config_backup.html` — Backup file?
- `templates/post_info/post_preview.html` — Active or legacy?
- `templates/llm_actions/preview_post.html` — Active or legacy?
- `blog-llm-actions/templates/preview_post.html` — Active or legacy?

**Action Required:** Audit route registration to determine active templates

### 12.2 Preview Manager Duplication

**Uncertainty:** Are there multiple preview manager implementations?

**Files Found:**
- `static/js/preview-manager.js`
- `static/llm_actions/js/preview-manager.js`
- `blog-llm-actions/static/js/preview-manager.js`

**Action Required:** Determine if these are duplicates or serve different purposes

### 12.3 Channel Formatting Scope

**Uncertainty:** What channel-specific formatting is needed beyond Facebook?

**Current State:**
- Facebook: `format_message_for_facebook()` exists (for publishing)
- Instagram: Carousel preview exists (for review)
- X/Twitter: No formatting found
- TikTok: No formatting found

**Action Required:** Define channel formatting requirements before implementation

### 12.4 Preview Mode Distinction

**Uncertainty:** Should preview mode be explicit or implicit?

**Current State:**
- Blog preview: Implicit (route-based, image_replacements=None)
- Social previews: No clear preview/publish distinction

**Action Required:** Define preview mode model (flag, route, context?)

---

## 13. Evidence & File References

### 13.1 Blog Preview System

**Core Files:**
- `blog-launchpad/publish/preview_handler.py` — Preview route handler
- `blog-launchpad/publish/post_renderer.py` — Single source of truth for HTML rendering
- `blog-launchpad/publish/post_data_loader.py` — Unified data preparation
- `templates/launchpad/post_preview.html` — Preview template wrapper
- `templates/launchpad/clan_post_raw.html` — Blog post HTML template

**Documentation:**
- `blog-core/docs/reference/workflow/preview.md` — Comprehensive reference
- `blog-core/docs/reference/preview_system_comparison.md` — Legacy vs new comparison

### 13.2 Social Media Previews

**Instagram Carousel:**
- `templates/launchpad/instagram/carousel_review.html` — Review interface
- `blueprints/launchpad/instagram_carousel.py` — API endpoints

**Facebook Feed Post:**
- `templates/launchpad/facebook_feed_post_config_backup.html` — Backup file with preview mockup (lines 870-924)

**Message Manager:**
- `static/js/message-manager-preview.js` — Text assembly preview
- `static/js/preview-manager.js` — Generic preview manager

### 13.3 Planning Surfaces

**Content Control Board:**
- `templates/planning/content_control_board.html` — Main template
- `static/js/planning/content_control_board.js` — JavaScript (lines 379-405, 626-748)
- `blueprints/planning_api_content_control_board.py` — API (lines 406-425: `_get_preview()` function)

**Sunday Slot:**
- `templates/kb_topics/rota_editor.html` — Template (lines 118-123)
- `static/js/kb_topics/sunday_slot.js` — JavaScript (lines 490-514)

**Posting Queue:**
- `templates/posting_queue/view.html` — Template (lines 280-510)
- `blueprints/posting_queue_view.py` — API

### 13.4 Formatting Utilities

**Facebook Formatting:**
- `utils/platform_publishers.py` — `format_message_for_facebook()` function (lines 26-68)

**Channel Resolution:**
- `utils/output_channel_resolver.py` — Pipeline resolution (not preview)
- `utils/social_output_view.py` — Social output normalization (not preview)

### 13.5 Historical Artifacts

**Archived Plans:**
- `blog-core/docs/~archive/temp/clan_blog_preview_implementation_plan.md`
- `blog-core/docs/temp/preview_system_enhancement_plan.md`
- `blog-launchpad/docs/temp/facebook_posting_implementation_plan.md`

---

## 14. Summary & Next Steps

### 14.1 Key Findings

1. **Blog Preview System** is well-architected and can serve as reference model
2. **No unified preview system** exists for social media channels
3. **Preview logic is fragmented** across multiple surfaces
4. **Text truncation logic is duplicated** (80 vs 100 chars)
5. **Channel-specific formatting** exists only for Facebook (publishing, not preview)
6. **Instagram carousel preview** is channel-aware but standalone
7. **Planning surfaces** use text-only previews (no channel mockups)

### 14.2 Critical Gaps

1. ❌ No unified preview API
2. ❌ No channel-specific preview templates
3. ❌ No reusable preview components
4. ❌ No channel formatter registry
5. ❌ Text truncation logic duplicated

### 14.3 Reuse Opportunities

1. ✅ Blog preview rendering architecture (Jinja2, template-based)
2. ✅ Post data preparation pattern
3. ⚠️ Instagram carousel preview pattern (needs generalization)
4. ⚠️ Facebook formatting function (needs extension to preview)

### 14.4 Recommended Next Steps

**Before Design:**
1. **Audit active templates** — Determine which preview templates are in use
2. **Resolve duplicates** — Consolidate preview manager implementations
3. **Define channel requirements** — What formatting is needed per channel?

**Design Phase:**
1. **Extract blog preview architecture** — Create channel-agnostic rendering engine
2. **Design channel formatter registry** — Centralize channel-specific formatting
3. **Design preview component library** — Reusable components for planning surfaces
4. **Design unified preview API** — Single endpoint for channel previews

---

## 15. Definition of Done (Discovery Phase)

✅ **Complete:** All preview-related systems identified and documented  
✅ **Complete:** Reuse assessment provided for each system  
✅ **Complete:** Gaps explicitly stated  
✅ **Complete:** Risks and conflicts identified  
✅ **Complete:** Recommendations provided (non-prescriptive)  
✅ **Complete:** Evidence and file references included  
✅ **Complete:** Uncertainties explicitly called out  

**Status:** Discovery phase complete. Ready for design phase.

---

**End of Discovery Report**
