# Weekly Content System - Testing Guide

**Date:** 2026-01-17  
**Purpose:** Guide for testing the weekly content image and caption generation system

---

## Quick Test

Run the comprehensive test script:

```bash
python3 scripts/test_weekly_content_system.py
```

This will test:
1. Data extraction from `calendar_ideas`
2. Caption generation with Ollama
3. Image generation with ImageMagick
4. Complete end-to-end workflow

---

## Manual Testing

### 1. Test Data Extraction

```python
from utils.weekly_content_data_extractor import extract_weekly_content_data

# Replace with actual idea_id from calendar_ideas
data = extract_weekly_content_data(idea_id=123, category='weekly_word')
print(data)
```

**Expected output:**
- Dictionary with all required fields
- `scots_text`, `translation`, `output_path`, etc.

### 2. Test Caption Generation

```python
from utils.weekly_content_caption_generator import generate_weekly_content_caption

result = generate_weekly_content_caption(
    category='weekly_word',
    scots_text='braw',
    translation='good, fine',
    notes='Common in Edinburgh'
)
print(result['caption'])
```

**Expected output:**
- Caption with exactly 1 question
- Includes Scots text and translation
- JSON structure with alternatives

### 3. Test Image Generation

```python
from utils.weekly_content_image_renderer import render_weekly_content_image

result = render_weekly_content_image(
    category='weekly_word',
    title='SCOTS WORD OF THE WEEK',
    scots_text='braw',
    translation='good, fine',
    series_footer='Scots Language Series',
    logo_path='/path/to/logo.png',  # or None
    output_path='/path/to/output.png'
)
print(result)
```

**Expected output:**
- `success: True`
- Image file at `output_path`
- File size > 1KB
- Dimensions: 1080×1080

### 4. Test Complete Workflow

```python
from utils.posting_queue_helpers import create_weekly_social_post
from blueprints.automation_execute import (
    execute_format_for_facebook,
    execute_generate_caption,
    execute_add_hashtags,
    execute_optimize_for_facebook
)

# Create queue row
queue_id = create_weekly_social_post(
    idea_id=123,
    content_type='weekly_word',
    platform='facebook',
    generated_content='Test'
)

# Execute substages
execute_format_for_facebook(queue_id, {})
execute_generate_caption(queue_id, {})
execute_add_hashtags(queue_id, {})
execute_optimize_for_facebook(queue_id, {})

# Verify results
from utils.posting_queue_helpers import get_posting_queue_row
row = get_posting_queue_row(queue_id)
print(row['generated_caption'])
print(row['image_path'])
```

---

## Verification Checklist

After running tests, verify:

- [ ] Data extraction returns all required fields
- [ ] Caption includes Scots text and translation
- [ ] Caption has exactly 1 question
- [ ] Image file is created (1080×1080)
- [ ] Image is readable (not corrupted)
- [ ] All text is visible and properly positioned
- [ ] Logo appears (if available)
- [ ] Database metadata is populated
- [ ] No errors in logs

---

## Troubleshooting

### Caption Generation Fails

**Issue:** Ollama not responding or JSON parsing fails

**Solutions:**
- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Verify model is available: `llama3.2:latest`
- Check logs for error details

### Image Generation Fails

**Issue:** ImageMagick command fails

**Solutions:**
- Verify ImageMagick installed: `magick --version`
- Check font availability
- Verify logo path (if using)
- Check output directory permissions

### Data Extraction Fails

**Issue:** Idea not found or missing fields

**Solutions:**
- Verify `idea_id` exists in `calendar_ideas`
- Check `item_classification` is set correctly
- Ensure `idea_title` and `idea_description` are populated

---

## Next Steps After Testing

Once all tests pass:

1. ✅ System is ready for integration
2. ⚠️  Facebook image posting integration still needed
3. 📝 Review generated images for quality
4. 🔧 Adjust styling in `config/weekly_content_image_config.py` if needed
