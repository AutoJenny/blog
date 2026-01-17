# Weekly Content Image & Caption Generation System - Technical Reference

**Date:** 2026-01-17  
**Status:** ✅ **FULLY AUTOMATED - PRODUCTION READY**  
**Purpose:** Complete technical documentation for the automated weekly content (word/phrase/insult) social media post generation system

**Automation Status:** ✅ **COMPLETE** - System automatically creates, processes, and publishes weekly content with zero manual intervention

---

## Overview

This system automates the creation of Facebook posts for weekly Scots language content:
- **Square images (1080×1080)** generated with ImageMagick
- **Social media captions** generated using Ollama with 30 style variations
- **Automatic posting** to both Facebook pages

**Content Types Supported:**
- `weekly_word` - Single Scots words
- `weekly_phrase` - Scots phrases
- `weekly_insult` - Scots insults

**Output Channels:**
- Facebook (fully implemented)
- Instagram (configuration ready, implementation pending)
- Twitter (configuration ready, implementation pending)

---

## Architecture

### System Flow

```
calendar_ideas (source data)
    ↓
extract_weekly_content_data()
    ↓
format_for_facebook() → generate_caption() → add_hashtags()
    ↓
optimize_for_facebook() [ImageMagick image generation]
    ↓
publish_to_facebook() [Posts to both FB pages]
```

### Database Schema

**Table: `posting_queue`** (extended with metadata columns)

```sql
-- Weekly content metadata columns (added 2026-01-17)
generated_caption TEXT,              -- AI-generated caption text
pinned_comment TEXT,                 -- Optional pinned comment
chosen_prompt_style_id INTEGER,      -- Prompt variation ID (1-30)
image_path TEXT,                     -- File system path to generated image
ollama_model VARCHAR(100),          -- Ollama model used (e.g., 'llama3.2:latest')
generation_timestamp TIMESTAMPTZ    -- When caption/image were generated
```

**Indexes:**
- `idx_posting_queue_generation_timestamp` - Query by generation time
- `idx_posting_queue_prompt_style_id` - Analytics on prompt styles

---

## Core Components

### 1. Configuration Files

#### `config/weekly_content_image_config.py`

**Purpose:** Styling configuration for image generation (tweakable without code changes)

**Key Settings:**
- **Canvas:** 1080×1080 square
- **Colors:**
  - Background: `#1e3a5f` (deep blue)
  - Main text: `#f5f1e8` (warm ivory)
  - Header/Footer: `#8fa8c4` (pale blue - recedes)
- **Typography:**
  - Header: Arial-Bold, 48pt
  - Main phrase: Baskerville-Italic, 96pt
  - Translation: Arial, 40pt
  - Footer: Arial, 24pt
- **Logo:** 20% of canvas width, bottom-right corner
- **Margins:** 90px top/bottom, safe margins for text

**Usage:** Import and use constants directly:
```python
from config.weekly_content_image_config import (
    CANVAS_SIZE, BG_COLOR, TEXT_COLOR, HEADER_FOOTER_COLOR,
    HEADER_FONT, BODY_FONT, ACCENT_FONT, LOGO_PATH, etc.
)
```

#### `config/weekly_content_caption_prompts.py`

**Purpose:** Ollama prompt templates and variation library

**Components:**
- **System Prompt:** Defines rules (1 question, includes translation, no hashtags, etc.)
- **Variation Library:** 30 different style prompts (nostalgia, locality, playful, education, etc.)

**Usage:**
```python
from config.weekly_content_caption_prompts import (
    SYSTEM_PROMPT, VARIATION_PROMPTS, get_variation_prompt
)
```

---

### 2. Data Extraction

#### `utils/weekly_content_data_extractor.py`

**Function:** `extract_weekly_content_data(idea_id, category)`

**Purpose:** Extracts data from `calendar_ideas` and formats for generator

**Data Contract:**
```python
{
    'category': 'weekly_word|weekly_phrase|weekly_insult',
    'title': 'SCOTS WORD OF THE WEEK',
    'scots_text': 'braw',
    'translation': 'good, fine',
    'series_footer': 'Scots Language Series',
    'logo_path': '/absolute/path/to/logo.png',
    'output_path': '/absolute/path/to/output/image.png',
    'notes': 'Optional notes from idea_description',
    'idea_id': 123
}
```

**Translation Parsing:**
- Expects format: `"Translation: ... | Provenance: ..."`
- Falls back gracefully if format differs
- Uses `idea_title` as Scots text source

---

### 3. Caption Generation

#### `utils/weekly_content_caption_generator.py`

**Function:** `generate_weekly_content_caption(category, scots_text, translation, notes, ...)`

**Purpose:** Generates Facebook captions using Ollama with variation library

**Process:**
1. Selects prompt variation (random or specified by `prompt_style_id`)
2. Builds user prompt with content data
3. Calls Ollama via `LLMService.execute_llm_request()`
4. Parses JSON response (with fallback if parsing fails)
5. Returns structured result

**Output:**
```python
{
    'caption': 'Main caption text',
    'pinned_comment': 'Optional pinned comment',
    'alt_caption_1': 'Alternative option 1',
    'alt_caption_2': 'Alternative option 2',
    'chosen_prompt_style_id': 3,
    'variation_seed': 42,
    'ollama_model': 'llama3.2:latest'
}
```

**Error Handling:**
- Falls back to simple caption if Ollama fails
- Robust JSON parsing with regex extraction
- Logs errors but continues

---

### 4. Image Rendering

#### `utils/weekly_content_image_renderer.py`

**Function:** `render_weekly_content_image(category, title, scots_text, translation, series_footer, logo_path, output_path)`

**Purpose:** Generates square 1080×1080 images using ImageMagick

**ImageMagick Command Structure:**
1. **Base canvas:** 1080×1080 solid color background
2. **Header:** Top annotation (pale blue, 48pt)
3. **Main phrase:** Center annotation (cream, 96pt, italic)
4. **Translation:** Below phrase (cream, 40pt)
5. **Footer:** Bottom annotation (pale blue, 24pt)
6. **Logo:** Composite in bottom-right (20% scale, separate command)

**Technical Details:**
- Uses `magick` command (ImageMagick v7 compatible)
- Logo composited in separate step for reliability
- Footer added twice (in main command and after logo) to ensure visibility
- Handles missing logo gracefully

**Output:**
- PNG file at specified `output_path`
- 1080×1080 pixels
- ~40-60KB file size

---

### 5. Substage Execution Functions

#### `blueprints/automation_execute.py`

**Functions:**

1. **`execute_format_for_facebook(post_id, data)`**
   - Extracts data from `calendar_ideas` via `idea_id`
   - Stores formatted data in `posting_queue.generated_content` (JSON)

2. **`execute_generate_caption(post_id, data)`**
   - Generates caption using Ollama
   - Stores in `posting_queue.generated_caption`
   - Stores metadata (prompt_style_id, ollama_model, timestamp)

3. **`execute_add_translation(post_id, data)`**
   - Verifies translation exists (no-op for now, translation already in data)

4. **`execute_add_hashtags(post_id, data)`**
   - Adds `#ScotsLanguage` hashtag to caption (max 1 per briefing)

5. **`execute_optimize_for_facebook(post_id, data)`**
   - Generates square image using ImageMagick
   - Stores `image_path` in `posting_queue`

6. **`execute_publish_to_facebook(post_id, data)`**
   - Converts local image path to public URL
   - Posts to both Facebook pages using `/photos` endpoint
   - Updates status to 'published' and stores `platform_post_id`

---

### 6. Workflow Configuration

#### `config/output_channel_stages.py`

**Weekly Content Facebook Pipeline:**

```python
('weekly_word', 'facebook'): {
    'stages': ['content', 'imaging', 'publish'],
    'substages': {
        'content': ['format_for_facebook', 'generate_caption', 'add_hashtags'],
        'imaging': ['optimize_for_facebook'],
        'publish': ['publish_to_facebook']
    }
}
```

**Phrase/Insult Pipeline:**
- Includes `add_translation` substage in content stage

---

### 7. Integration

#### `blueprints/automation_core.py`

**Substage Router:** `execute_substage()`

Routes weekly content substages to execution functions:
- `content` stage → `format_for_facebook`, `generate_caption`, `add_hashtags`, `add_translation`
- `imaging` stage → `optimize_for_facebook`
- `publish` stage → `publish_to_facebook`

---

## Facebook Posting Implementation

### Posting to Both Pages

**Pattern:** Follows same pattern as product posting (`execute_facebook_post()`)

**Process:**
1. Get credentials for both pages from `platform_credentials` table:
   - Page 1: `page_id`, `page_access_token` (Scotweb CLAN)
   - Page 2: `page_id_2`, `page_access_token_2` (CLAN by Scotweb)

2. Convert local image path to public URL:
   - Images in `static/content/weekly_posts/...`
   - Flask serves `/static/...` URLs automatically
   - Converts: `static/content/...` → `http://domain.com/static/content/...`

3. Post to each page separately:
   - Uses Facebook Graph API `/photos` endpoint
   - Payload: `url` (image URL), `caption`, `published=True`
   - Handles success/failure for each page independently

4. Update database:
   - Stores first successful `post_id` as `platform_post_id`
   - Updates status to 'published' if any page succeeds
   - Updates status to 'failed' if all pages fail
   - Stores error messages if failures occur

**API Endpoint:**
```
POST https://graph.facebook.com/v18.0/{page_id}/photos
```

**Payload:**
```python
{
    'url': 'http://domain.com/static/content/weekly_posts/.../square_image.png',
    'caption': 'Generated caption text...',
    'published': True,
    'access_token': 'page_access_token'
}
```

---

## File Structure

```
utils/
├── weekly_content_data_extractor.py      # Extract data from calendar_ideas
├── weekly_content_caption_generator.py   # Ollama caption generation
└── weekly_content_image_renderer.py      # ImageMagick image rendering

config/
├── weekly_content_image_config.py        # Styling configuration
└── weekly_content_caption_prompts.py     # Prompt templates (30 variations)

blueprints/
├── automation_execute.py                 # Substage execution functions
└── automation_core.py                    # Substage router (updated)

utils/
└── posting_queue_helpers.py              # Helper functions (extended)

migrations/
└── 20260117_add_weekly_content_metadata_to_posting_queue.sql
```

---

## Usage Examples

### Creating a Weekly Content Post

```python
from utils.posting_queue_helpers import create_weekly_social_post

queue_id = create_weekly_social_post(
    idea_id=123,
    content_type='weekly_word',
    platform='facebook',
    generated_content='Initial content',
    status='draft'
)
```

### Executing Workflow

**Via API:**
```bash
# Format content
POST /automation/execute_substage?post_id={queue_id}&stage=content&substage=format_for_facebook

# Generate caption
POST /automation/execute_substage?post_id={queue_id}&stage=content&substage=generate_caption

# Add hashtags
POST /automation/execute_substage?post_id={queue_id}&stage=content&substage=add_hashtags

# Generate image
POST /automation/execute_substage?post_id={queue_id}&stage=imaging&substage=optimize_for_facebook

# Publish to Facebook
POST /automation/execute_substage?post_id={queue_id}&stage=publish&substage=publish_to_facebook
```

**Via Python:**
```python
from blueprints.automation_execute import (
    execute_format_for_facebook,
    execute_generate_caption,
    execute_add_hashtags,
    execute_optimize_for_facebook,
    execute_publish_to_facebook
)

execute_format_for_facebook(queue_id, {})
execute_generate_caption(queue_id, {})
execute_add_hashtags(queue_id, {})
execute_optimize_for_facebook(queue_id, {})
execute_publish_to_facebook(queue_id, {})
```

---

## Configuration Reference

### Image Styling (`config/weekly_content_image_config.py`)

**Canvas:**
- `CANVAS_SIZE = 1080` - Square 1080×1080

**Colors:**
- `BG_COLOR = "#1e3a5f"` - Deep blue background
- `TEXT_COLOR = "#f5f1e8"` - Warm ivory for main content
- `HEADER_FOOTER_COLOR = "#8fa8c4"` - Pale blue for header/footer (recedes)

**Typography:**
- `HEADER_FONT = "Arial-Bold"` - Header font
- `BODY_FONT = "Baskerville-Italic"` - Main phrase font (96pt)
- `ACCENT_FONT = "Arial"` - Translation/footer font

**Logo:**
- `LOGO_SCALE = 0.20` - 20% of canvas width
- `LOGO_CORNER = "bottom-right"` - Placement
- `LOGO_PADDING = 40` - Pixels from edge

**Layout:**
- `TOP_MARGIN = 90` - Header spacing
- `BOTTOM_MARGIN = 90` - Footer spacing
- `SAFE_MARGIN = 90` - Text safe area

### Caption Prompts (`config/weekly_content_caption_prompts.py`)

**System Prompt Rules:**
- Short, friendly Scots cultural tone
- Include Scots phrase + translation
- Exactly 1 question only
- No hashtags (or at most 1)
- No obscenity
- No targeting protected traits
- Never invent provenance

**Variation Library:** 30 style prompts (nostalgia, locality, playful, education, memory, etc.)

---

## Error Handling

### Image Generation
- Missing logo: Warns but continues without logo
- ImageMagick failure: Returns error message, doesn't crash
- File size validation: Checks output file exists and is reasonable size

### Caption Generation
- Ollama unavailable: Returns fallback caption
- JSON parsing failure: Falls back to simple caption format
- Missing translation: Handles gracefully

### Facebook Posting
- Missing credentials: Returns error, doesn't crash
- One page fails: Continues with other page, reports partial success
- Both pages fail: Updates status to 'failed', stores error message
- Image URL inaccessible: Facebook API returns error, handled gracefully

---

## Dependencies

### External Tools
- **ImageMagick v7** - Image generation (uses `magick` command)
- **Ollama** - Caption generation (requires `llama3.2:latest` model)

### Python Packages
- `subprocess` - ImageMagick command execution
- `json` - Data serialization
- `requests` - Facebook API calls
- `psycopg` - Database access (via `db_manager`)

### Assets
- Logo: `static/images/site/clan-watermark.png`
- Fonts: System fonts (Arial, Baskerville) - no installation required

---

## Testing

### Test Script
`scripts/test_weekly_content_system.py` - Comprehensive test script

**Tests:**
1. Data extraction from `calendar_ideas`
2. Caption generation with Ollama
3. Image generation with ImageMagick
4. Complete end-to-end workflow

**Run:**
```bash
python3 scripts/test_weekly_content_system.py
```

### Manual Testing

**Test Data Extraction:**
```python
from utils.weekly_content_data_extractor import extract_weekly_content_data
data = extract_weekly_content_data(idea_id=123, category='weekly_word')
```

**Test Caption Generation:**
```python
from utils.weekly_content_caption_generator import generate_weekly_content_caption
result = generate_weekly_content_caption(
    category='weekly_word',
    scots_text='braw',
    translation='good, fine'
)
```

**Test Image Generation:**
```python
from utils.weekly_content_image_renderer import render_weekly_content_image
result = render_weekly_content_image(
    category='weekly_word',
    title='SCOTS WORD OF THE WEEK',
    scots_text='braw',
    translation='good, fine',
    series_footer='Scots Language Series',
    logo_path='/path/to/logo.png',
    output_path='/path/to/output.png'
)
```

---

## Troubleshooting

### Image Not Generating
- **Check ImageMagick:** `magick --version`
- **Check fonts:** Verify Arial/Baskerville available
- **Check logo path:** Verify logo file exists
- **Check permissions:** Output directory must be writable

### Caption Not Generating
- **Check Ollama:** `curl http://localhost:11434/api/tags`
- **Check model:** Verify `llama3.2:latest` is available
- **Check logs:** Look for JSON parsing errors

### Facebook Posting Fails
- **Check credentials:** Verify both page tokens configured
- **Check image URL:** Verify image is publicly accessible
- **Check API response:** Review error messages in logs
- **Check permissions:** Verify page tokens have `pages_manage_posts` permission

---

## Automation

### Fully Automated Workflow

The system is **fully automated** and requires no manual intervention:

1. **Automatic Creation** (`scripts/automated_weekly_content_creator.py`):
   - Runs daily via background monitor
   - Creates `posting_queue` entries 1 week in advance
   - Based on calendar schedule (`resolve_item_for_week()`)

2. **Automatic Workflow Execution** (`scripts/automated_weekly_content_workflow.py`):
   - Processes draft posts automatically
   - Executes all workflow stages (format → caption → image → publish)
   - Publishes immediately if scheduled time has passed

3. **Automatic Publishing** (`scripts/posting_executor.py`):
   - Publishes 'ready' posts at scheduled time
   - Handles both product posts and weekly content

**Background Monitor:** `scripts/background_posting_monitor.sh` runs every 5 minutes

**See:** `docs/WEEKLY_CONTENT_AUTOMATION_COMPLETE.md` for full automation details

---

## Future Enhancements

### Planned
- Instagram posting integration
- Twitter posting integration
- Text wrapping for long phrases
- Multiple caption selection UI
- A/B testing for prompt variations

### Potential Improvements
- Image caching to avoid regeneration
- Batch processing for multiple weekly posts
- Analytics on prompt style performance

---

## Related Documentation

- `docs/temp/WEEKLY_CONTENT_IMAGE_CAPTION_IMPLEMENTATION_PLAN.md` - Implementation plan
- `docs/temp/OPERATIONAL_READINESS_CHECKLIST.md` - Pre-launch checklist
- `docs/temp/GO_LIVE_CHECKLIST.md` - Go-live checklist
- `docs/temp/TESTING_GUIDE.md` - Testing procedures
- `docs/WEEKLY_SOCIAL_POST_CREATION_AUDIT.md` - Audit of posting_queue creation points

---

**Last Updated:** 2026-01-17  
**Version:** 1.0  
**Status:** Production Ready
