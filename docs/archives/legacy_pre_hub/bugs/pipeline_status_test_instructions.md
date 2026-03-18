# Pipeline Status Test Instructions

## Manual Browser Testing Guide

This document provides step-by-step instructions for manually testing the pipeline status display and green dots functionality in the browser.

## Prerequisites

1. Server running on `http://localhost:5000`
2. Post ID 96 exists in the database (or use another valid post ID)
3. Browser with DevTools enabled

## Test Steps

### Step 1: Open the Page

1. Navigate to: `http://localhost:5000/launchpad/one-click-blog?post_id=96`
2. Wait for the page to fully load

### Step 2: Open DevTools Console

1. Press `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows/Linux)
2. Click on the "Console" tab
3. Clear any existing console messages

### Step 3: Check for Errors

**Expected Result:** No `ReferenceError: Can't find variable: data` error

**What to look for:**
- Check console for any red error messages
- Specifically look for "Failed to load post details:" errors
- Verify no `ReferenceError` appears

**If errors appear:**
- Note the exact error message
- Check the line number
- Verify which template is being served (check Network tab)

### Step 4: Test updateSelectedPostSummary Function Directly

1. In the Console, type:
   ```javascript
   await updateSelectedPostSummary(96)
   ```

2. Press Enter and wait for the promise to resolve

**Expected Result:**
- Function executes without errors
- No `ReferenceError` about `data` variable
- Console shows no error messages

**What to check:**
- If function doesn't exist, check if it's defined in the page
- If it throws an error, note the error message

### Step 5: Check Network Tab for API Calls

1. Open DevTools → Network tab
2. Refresh the page (F5 or Cmd+R)
3. Filter by "Fetch/XHR"

**Expected API Calls:**
1. `/planning/api/posts/96` - Should return 200
2. `/api/post-type-pipeline/posts/96/pipeline` - Should return 200
3. `/launchpad/one-click-blog/api/pipeline-status/96` - Should return 200

**What to verify:**
- All three API calls are made
- All return HTTP 200 status
- Response times are reasonable (< 1 second each)

**If API calls fail:**
- Check the response status code
- Check the response body for error messages
- Verify the endpoint URLs are correct

### Step 6: Verify Pipeline Status API Response

1. In Network tab, click on `/launchpad/one-click-blog/api/pipeline-status/96`
2. Click on "Response" tab
3. Verify the response structure

**Expected Response Structure:**
```json
{
  "success": true,
  "data": {
    "post_id": 96,
    "title": "...",
    "stages": {
      "calendar": {
        "status": "complete|in_progress|pending",
        "progress": 0-100,
        "substages": {
          "calendar_view": {
            "status": "complete|in_progress|pending",
            "progress": 0-100,
            "completed_at": "ISO8601 timestamp or null"
          },
          ...
        }
      },
      "planning": { ... },
      "authoring": { ... },
      "imaging": { ... },
      "header": { ... }
    }
  }
}
```

**What to verify:**
- `success` is `true`
- `data.stages` exists
- Each stage has `status`, `progress`, and `substages`
- Each substage has `status`, `progress`, and optionally `completed_at`

### Step 7: Verify Green Dots Appear

1. Scroll to the pipeline table on the page
2. Look for substages that should be marked as complete

**Expected Visual Indicators:**
- Green checkmark icon (✓) next to completed substages
- Button with class `complete` for completed substages
- "Completed X ago" text for completed substages

**What to check:**
- Find a substage that should be complete (e.g., "Ideas" if `expanded_idea` exists)
- Verify green checkmark appears
- Verify button state is correct

**If green dots don't appear:**
- Check if `updatePipelineStatusIndicators()` function is called
- Verify CSS classes are applied correctly
- Check browser console for JavaScript errors

### Step 8: Test with Different Post IDs

1. Try with a different post ID that has different completion statuses:
   ```javascript
   await updateSelectedPostSummary(78)  // or another post ID
   ```

2. Verify:
   - No errors occur
   - Green dots update correctly
   - Button states reflect completion status

### Step 9: Test Error Handling

1. Try with a non-existent post ID:
   ```javascript
   await updateSelectedPostSummary(999999)
   ```

**Expected Behavior:**
- Function should handle the error gracefully
- Console should show "Failed to load post details:" with error details
- Page should not crash

## Troubleshooting

### Issue: ReferenceError: Can't find variable: data

**Cause:** The `data` variable is not defined in the function scope.

**Solution:** Verify that:
1. Pipeline status API is being fetched
2. Response is stored in `pipelineStatusData` variable
3. All `data.sections` references have been replaced

### Issue: Green dots don't appear

**Possible Causes:**
1. `updatePipelineStatusIndicators()` function is not being called
2. Pipeline status API is not returning completion data
3. CSS classes are not being applied
4. DOM elements don't exist

**Debug Steps:**
1. Check if `updatePipelineStatusIndicators()` is defined
2. Add `console.log()` to verify function is called
3. Check Network tab to verify API response
4. Inspect DOM elements to see if classes are applied

### Issue: API endpoint returns 404

**Possible Causes:**
1. Blueprint not registered correctly
2. URL path is incorrect
3. Post doesn't exist

**Debug Steps:**
1. Verify blueprint registration in `unified_app.py`
2. Check the actual URL being called in Network tab
3. Verify post exists in database

### Issue: Template confusion (wrong template being served)

**Possible Causes:**
1. Browser cache serving old template
2. Route configuration issue
3. Template inheritance

**Debug Steps:**
1. Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
2. Clear browser cache
3. Check "View Page Source" to see which template rendered
4. Verify route in `blueprints/launchpad/one_click_blog.py`

## Success Criteria

All of the following should be true:

- ✅ No `ReferenceError: Can't find variable: data` in console
- ✅ All three API calls are made successfully
- ✅ Pipeline status API returns valid response structure
- ✅ Green dots appear for completed substages
- ✅ Button states (ready/dead/complete) update correctly
- ✅ No JavaScript errors in console
- ✅ Page loads without errors

## Additional Testing

### Test with curl

You can also test the API endpoint directly with curl:

```bash
curl http://localhost:5000/launchpad/one-click-blog/api/pipeline-status/96 | python3 -m json.tool
```

### Test with the provided script

Run the end-to-end test script:

```bash
./scripts/test_pipeline_status_display.sh http://localhost:5000 96
```

## Reporting Issues

If you find issues during testing:

1. Note the exact error message
2. Capture the console output
3. Note which step failed
4. Include the API response (if available)
5. Note browser and version
6. Update the bug report with findings


