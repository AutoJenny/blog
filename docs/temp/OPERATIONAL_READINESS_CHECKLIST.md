# Weekly Content System - Operational Readiness Checklist

**Date:** 2026-01-17  
**Status:** Implementation complete, testing and integration needed

---

## ✅ Completed

1. **Database Migration** - ✅ RUN
   - All 6 metadata columns added to `posting_queue`
   - Indexes created
   - Verified successfully

2. **Core Components** - ✅ IMPLEMENTED
   - Configuration files
   - Data extraction
   - Caption generation
   - Image rendering
   - Substage execution functions
   - Integration with automation_core.py

3. **Assets Verified** - ✅ CHECKED
   - Logo exists: `static/images/site/clan-watermark.png`
   - ImageMagick installed (note: uses `magick` command in v7)

---

## ⚠️ Required Before Production

### 1. Fix ImageMagick Command (CRITICAL)

**Issue:** ImageMagick v7 uses `magick` instead of `convert`

**File:** `utils/weekly_content_image_renderer.py`

**Change needed:**
```python
# Line ~50: Change from:
cmd = ['convert']

# To:
cmd = ['magick', 'convert']  # or just ['magick'] depending on syntax
```

**Action:** Update the command builder to use `magick` command

---

### 2. Integrate Facebook Image Posting (CRITICAL)

**Issue:** `execute_publish_to_facebook()` is a placeholder. Current Facebook posting only handles link posts, not image posts.

**Files to modify:**
- `blueprints/automation_execute.py` - `execute_publish_to_facebook()`
- May need new function in `blueprints/launchpad/blog_post_syndication.py`

**What's needed:**
1. Upload image to Facebook (requires multipart/form-data POST to `/photos` endpoint)
2. Post with caption using the uploaded photo ID
3. Handle both Facebook pages (if configured)
4. Store `platform_post_id` in `posting_queue`
5. Update status to 'published'

**Reference:** Facebook Graph API v18.0 `/photos` endpoint

**Action:** Implement image upload and posting logic

---

### 3. Add Caption Generation to Workflow (IMPORTANT)

**Issue:** Caption generation is a separate substage, but should be integrated into the workflow.

**Current workflow (from `config/output_channel_stages.py`):**
- `format_for_facebook` → `add_hashtags` → `optimize_for_facebook` → `publish_to_facebook`

**Missing:** `generate_caption` step

**Options:**
1. Add `generate_caption` as a substage in the workflow
2. Integrate caption generation into `format_for_facebook`

**Action:** Decide on approach and update workflow configuration

---

### 4. Test Each Component (REQUIRED)

#### 4.1 Test Data Extraction
```python
from utils.weekly_content_data_extractor import extract_weekly_content_data

# Get a real idea_id from calendar_ideas
data = extract_weekly_content_data(idea_id=123, category='weekly_word')
print(data)
```

**Verify:**
- Returns all required fields
- Handles missing translation gracefully
- Creates output directory

#### 4.2 Test Caption Generation
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

**Verify:**
- Ollama responds correctly
- JSON parsing works
- Caption follows rules (1 question, includes translation)
- Fallback works if Ollama fails

#### 4.3 Test Image Generation
```python
from utils.weekly_content_image_renderer import render_weekly_content_image

result = render_weekly_content_image(
    category='weekly_word',
    title='SCOTS WORD OF THE WEEK',
    scots_text='braw',
    translation='good, fine',
    series_footer='Scots Language Series',
    logo_path='/absolute/path/to/logo.png',
    output_path='/absolute/path/to/output.png'
)
```

**Verify:**
- Image is 1080×1080
- All text layers render correctly
- Logo composites properly
- File is created and readable

#### 4.4 Test Complete Workflow
1. Create `posting_queue` row:
   ```python
   from utils.posting_queue_helpers import create_weekly_social_post
   
   queue_id = create_weekly_social_post(
       idea_id=123,
       content_type='weekly_word',
       platform='facebook',
       generated_content='Initial content'
   )
   ```

2. Execute substages via API:
   - `POST /automation/execute_substage` with `stage=content`, `substage=format_for_facebook`
   - `POST /automation/execute_substage` with `stage=content`, `substage=generate_caption`
   - `POST /automation/execute_substage` with `stage=content`, `substage=add_hashtags`
   - `POST /automation/execute_substage` with `stage=imaging`, `substage=optimize_for_facebook`
   - `POST /automation/execute_substage` with `stage=publish`, `substage=publish_to_facebook`

3. Verify database:
   - Check `posting_queue` row has all metadata
   - Verify `image_path` points to valid file
   - Verify `generated_caption` is populated

---

### 5. Font Verification (RECOMMENDED)

**Check if fonts are available:**
```bash
# Check system fonts
fc-list | grep -i montserrat
fc-list | grep -i "libre.*baskerville"
fc-list | grep -i inter

# Or on macOS:
system_profiler SPFontsDataType | grep -i montserrat
```

**If fonts missing:**
- Install fonts, OR
- Update `config/weekly_content_image_config.py` to use system fonts that are available

**Action:** Verify fonts or update config

---

### 6. Error Handling Improvements (RECOMMENDED)

**Current gaps:**
- ImageMagick command failures may not be caught properly
- Long Scots phrases may overflow (text wrapping not fully implemented)
- Missing logo should be handled more gracefully

**Action:** Add comprehensive error handling and validation

---

### 7. Workflow Configuration Update (IMPORTANT)

**File:** `config/output_channel_stages.py`

**Current configuration:**
```python
('weekly_word', 'facebook'): {
    'stages': ['content', 'imaging', 'publish'],
    'substages': {
        'content': ['format_for_facebook', 'add_hashtags'],
        'imaging': ['optimize_for_facebook'],
        'publish': ['publish_to_facebook']
    }
}
```

**Should include:**
- `generate_caption` in content stage (or integrate into format)
- `add_translation` for phrase/insult types

**Action:** Update workflow configuration

---

## 📋 Testing Checklist

- [ ] Data extraction works with real `calendar_ideas` data
- [ ] Caption generation returns valid captions
- [ ] Image generation creates 1080×1080 images
- [ ] All text is readable and properly positioned
- [ ] Logo appears in correct corner
- [ ] Complete workflow executes end-to-end
- [ ] Database metadata is populated correctly
- [ ] Error handling works for missing data
- [ ] Long phrases wrap text properly
- [ ] Facebook posting works (after integration)

---

## 🚀 Quick Start Guide

Once all items above are complete:

1. **Create a test weekly content post:**
   ```python
   from utils.posting_queue_helpers import create_weekly_social_post
   
   queue_id = create_weekly_social_post(
       idea_id=<real_idea_id>,
       content_type='weekly_word',
       platform='facebook',
       generated_content='Test content'
   )
   ```

2. **Execute workflow via automation API:**
   - Use the One-Click Publication interface, OR
   - Call substage execution endpoints directly

3. **Verify results:**
   - Check `posting_queue` table
   - Verify image file exists
   - Check Facebook post (if integration complete)

---

## 📝 Notes

- **ImageMagick v7:** Uses `magick` command instead of `convert`
- **Facebook API:** Requires image upload via `/photos` endpoint for image posts
- **Caption Generation:** Currently separate substage, consider integrating into format step
- **Fonts:** May need to install or configure system fonts
- **Error Handling:** Add more robust validation and fallbacks

---

**Next Priority Actions:**
1. Fix ImageMagick command (5 min)
2. Integrate Facebook image posting (1-2 hours)
3. Test complete workflow (30 min)
4. Update workflow configuration (10 min)
