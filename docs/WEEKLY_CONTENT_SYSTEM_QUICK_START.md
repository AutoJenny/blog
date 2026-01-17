# Weekly Content System - Quick Start Guide

**Date:** 2026-01-17  
**Purpose:** Quick reference guide for using the weekly content image and caption generation system

---

## Overview

Automated system for creating Facebook posts for weekly Scots language content (word/phrase/insult) with:
- Square 1080×1080 images (ImageMagick)
- AI-generated captions (Ollama)
- Automatic posting to both Facebook pages

---

## Quick Start

### 1. Create a Weekly Content Post

```python
from utils.posting_queue_helpers import create_weekly_social_post

queue_id = create_weekly_social_post(
    idea_id=123,  # calendar_ideas.id
    content_type='weekly_word',  # or 'weekly_phrase', 'weekly_insult'
    platform='facebook',
    generated_content='Initial content',
    status='draft'
)
```

### 2. Execute Workflow

**Option A: Via Automation API**
```bash
# Format content
curl -X POST "http://localhost:5000/automation/execute_substage?post_id={queue_id}&stage=content&substage=format_for_facebook"

# Generate caption
curl -X POST "http://localhost:5000/automation/execute_substage?post_id={queue_id}&stage=content&substage=generate_caption"

# Add hashtags
curl -X POST "http://localhost:5000/automation/execute_substage?post_id={queue_id}&stage=content&substage=add_hashtags"

# Generate image
curl -X POST "http://localhost:5000/automation/execute_substage?post_id={queue_id}&stage=imaging&substage=optimize_for_facebook"

# Publish to Facebook
curl -X POST "http://localhost:5000/automation/execute_substage?post_id={queue_id}&stage=publish&substage=publish_to_facebook"
```

**Option B: Via Python**
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

**Option C: Via One-Click Publication UI**
- Navigate to publication dashboard
- Select weekly content item
- Choose Facebook output channel
- Execute substages in order

---

## Workflow Stages

### Content Stage
1. **`format_for_facebook`** - Extracts data from `calendar_ideas`, stores formatted data
2. **`generate_caption`** - Generates caption using Ollama (30 style variations)
3. **`add_translation`** - Verifies translation exists (for phrase/insult)
4. **`add_hashtags`** - Adds `#ScotsLanguage` hashtag

### Imaging Stage
1. **`optimize_for_facebook`** - Generates 1080×1080 square image using ImageMagick

### Publish Stage
1. **`publish_to_facebook`** - Posts to both Facebook pages using `/photos` endpoint

---

## Configuration

### Image Styling
Edit `config/weekly_content_image_config.py`:
- Colors (background, text, header/footer)
- Fonts (header, body, accent)
- Logo size and placement
- Margins and spacing

### Caption Prompts
Edit `config/weekly_content_caption_prompts.py`:
- System prompt rules
- Variation library (30 prompts)

---

## Output Locations

**Images:** `static/content/weekly_posts/{category}/{idea_id}/square_image.png`

**Database:** `posting_queue` table with metadata:
- `generated_caption` - Final caption text
- `image_path` - File system path to image
- `platform_post_id` - Facebook post ID
- `chosen_prompt_style_id` - Which variation was used
- `generation_timestamp` - When generated

---

## Troubleshooting

**Image not generating:**
- Check ImageMagick: `magick --version`
- Check logo exists: `static/images/site/clan-watermark.png`
- Check output directory permissions

**Caption not generating:**
- Check Ollama running: `curl http://localhost:11434/api/tags`
- Check model available: `llama3.2:latest`

**Facebook posting fails:**
- Check credentials configured for both pages
- Check image URL is publicly accessible
- Review error messages in logs

---

## Testing

Run comprehensive test:
```bash
python3 scripts/test_weekly_content_system.py
```

---

## Related Documentation

- `docs/WEEKLY_CONTENT_SYSTEM_TECHNICAL_REFERENCE.md` - Complete technical details
- `docs/temp/WEEKLY_CONTENT_IMAGE_CAPTION_IMPLEMENTATION_PLAN.md` - Implementation plan
- `docs/temp/GO_LIVE_CHECKLIST.md` - Go-live checklist

---

**Last Updated:** 2026-01-17
