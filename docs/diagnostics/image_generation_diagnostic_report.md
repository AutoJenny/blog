# Image Generation Diagnostic Report

**Date:** 2025-11-26  
**Status:** Investigation Complete, Fixes Pending  
**Post ID:** 97  
**Sections Affected:** Section 4 (ID: 863), Section 7 (ID: 866)

---

## Problem Summary

During batch image generation for post 97, 14/14 images were reported as running (landscape & portrait for 7 sections), but images did not appear for Section 4 (ID: 863) and Section 7 (ID: 866).

## Investigation Findings

### File System State

- **Section 4 (ID: 863)**: Directory `static/content/posts/97/sections/863/landscape/raw/` exists but is empty
- **Section 7 (ID: 866)**: Directory `static/content/posts/97/sections/866/landscape/raw/` exists but is empty
- **Other sections (1, 2, 3, 5, 6)**: Images exist in their respective directories

### Log Analysis

- **Section 863**: Log shows "Starting landscape generation for section 863" at 08:44:20, but no completion or error logs
- **Section 866**: Log shows "Starting landscape generation for section 866" at 08:49:14, but no completion or error logs
- **No errors logged**: Silent failures suggest timeout, unhandled exception, or API-level issue

### Database State

All sections (including 1-7) have:
- `image_prompts`: Present (JSON with `image_prompt` field)
- `image_filename`: `NULL` for all sections

**Critical Finding**: The image generation API does NOT update the database with image filenames after successful generation. Even when images are generated successfully, the `post_section.image_filename` field remains `NULL`.

### Root Cause Analysis

#### For Sections 4 and 7 Specifically

1. Generation started (logs confirm API calls were made)
2. No completion logs, suggesting:
   - API call timed out or failed silently
   - Generator function returned an error that wasn't logged
   - Network/API issue during generation
   - Exception caught but not logged

#### System-Wide Issue

The image generation API (`blueprints/imaging_api_generation.py`) does not update the database with image filenames. It only:
- Generates images and saves them to the filesystem
- Returns success/failure in the JSON response
- Does NOT persist image metadata to the database

## Code Flow Analysis

**Batch Generation Flow:**
1. `static/js/imaging/sections-panel.js` → `batchGenerateSelected()` iterates through selected sections
2. Calls `window.imageGenerationHandler.handleGenerateImage(sectionId)` for each section
3. `static/js/imaging/image-generation-handler.js` → `handleGenerateImage()` makes POST to `/imaging/api/image-generation/posts/{post_id}/sections/{section_id}/generate-image`
4. `blueprints/imaging_api_generation.py` → `imaging_generate_image()` calls generator functions
5. `blueprints/imaging_generators.py` → `imaging_generate_gpt_image_1()` generates and saves images

**Missing Step**: After successful generation, no database update occurs to record the image filename or link the image to the section.

## Recommended Fixes

### 1. Add Database Persistence

**File**: `blueprints/imaging_api_generation.py`

After successful image generation (around lines 138 and 178), add code to:
- Insert image record into `images` table
- Create `post_images` link with `image_type = 'section_landscape'` or `'section_portrait'`
- Update `post_section` table if `image_filename` column exists (legacy support)

### 2. Improve Error Handling

**File**: `blueprints/imaging_generators.py`

- Add detailed logging at each step of `imaging_generate_gpt_image_1()`
- Add timeout handling with proper error messages
- Add file write verification after saving images
- Log full API responses for debugging

### 3. Add Retry Logic

**File**: `blueprints/imaging_api_generation.py`

- Wrap generator calls in retry logic (3 attempts with 5-second delay)
- Only retry on transient errors (timeouts, network issues)
- Don't retry on permanent errors (invalid prompt, API key issues)

### 4. Improve Frontend Error Handling

**File**: `static/js/imaging/image-generation-handler.js`

- Add request timeout (3 minutes)
- Improve error message display
- Show partial success when only one orientation succeeds

## Testing Procedures

### Manual Retry for Failed Sections

1. Navigate to `http://localhost:5000/imaging/posts/97/sections/image-generation?year=2025&week=48`
2. Select only Section 4 (ID: 863)
3. Click "Generate All" (or individual generate button)
4. Monitor browser console and network tab
5. Check logs in real-time: `tail -f unified_app.log | grep -E "863|IMAGE_GENERATION"`
6. Verify files are created: `ls -la static/content/posts/97/sections/863/landscape/raw/`
7. Verify database records: Query `images` and `post_images` tables
8. Repeat for Section 7 (ID: 866)

### Verification Checklist

- [ ] Images generated successfully for sections 863 and 866
- [ ] Files exist in filesystem at expected paths
- [ ] Database records created in `images` table
- [ ] `post_images` links created with correct `image_type`
- [ ] No errors in logs during generation
- [ ] Frontend displays images correctly
- [ ] Batch generation progress accurately reflects success/failure

## Next Steps

1. Implement database persistence (Task 4 from plan)
2. Improve error handling and logging (Task 5 from plan)
3. Add retry logic (Task 6 from plan)
4. Test with failed sections
5. Verify all fixes work correctly
6. Update this report with results

## Related Files

- `blueprints/imaging_api_generation.py` - Main API endpoint
- `blueprints/imaging_generators.py` - Image generation functions
- `static/js/imaging/image-generation-handler.js` - Frontend handler
- `static/js/imaging/sections-panel.js` - Batch generation logic
- `utils/week_post_resolver.py` - Week/post resolution (unrelated but referenced)

## Notes

- The system uses `images` and `post_images` tables for image storage, NOT `post_section.image_filename`
- Check if `images` table has `file_path` as UNIQUE constraint before implementing fixes
- GPT-Image-1 API may have rate limits or timeout issues that need investigation

