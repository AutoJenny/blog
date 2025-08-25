# Changes Log

## 2025-01-22 - Post Info Substage Layout Implementation

### Problem
The workflow UI needed a new layout for the Post Info substage that would show post metadata (title, introduction, tags, meta description) in a dedicated panel, while also displaying sections information in a more compact format.

### Solution
**New Post Info Layout Implementation:**

1. **Conditional Layout Logic**:
   - **Post Info substage**: Special layout with blue Post Info panel + green Sections accordion
   - **Other writing substages**: Standard two-panel layout (LLM Actions + Sections)

2. **Blue Post Info Panel**:
   - **Background**: Dark blue (#1e3a8a) with blue border (#3b82f6)
   - **Fields**: Post Title, Introduction, Tags, Meta Description
   - **Layout**: 2-column grid with proper spacing and styling
   - **Save Button**: Blue-themed save functionality

3. **Green Sections Accordion**:
   - **Background**: Green (#013828) with green border (#065f46)
   - **Compact Display**: Shows sections information in a condensed format
   - **Placeholder Content**: Ready for integration with blog-post-sections microservice

### Technical Details
- **Template Changes**: Modified `blog-core/templates/workflow.html`
- **Conditional Rendering**: Uses Jinja2 `{% if current_substage == 'post_info' %}` logic
- **Responsive Design**: Grid layout adapts to different screen sizes
- **Consistent Styling**: Matches existing workflow UI design patterns

### Files Modified
- `blog-core/templates/workflow.html` - Added conditional Post Info layout

### Status
✅ **COMPLETED** - New Post Info layout is working and ready for integration with blog-post-info microservice.

### Next Steps
- Integrate with blog-post-info microservice for real data
- Connect save functionality to database operations
- Enhance sections accordion with actual sections data

---

## 2025-01-20 - Fixed Context Panel and Task Prompt Panel Dropdowns

### Problem
The Context panel and Task Prompt panel dropdowns were not populating with system prompts and task prompts on the workflow page (port 5001). The dropdowns showed "Select system prompt..." and "Select task prompt..." but remained empty.

### Root Cause
The blog-core service (port 5001) was missing critical workflow API endpoints that the working blog service (port 5000) had:

1. **Missing `/api/workflow/prompts/all`** - Returns system and task prompts from the `llm_prompt` table
2. **Missing `/api/workflow/steps/<step_id>/prompts`** - Gets/saves prompts for specific steps
3. **Missing `/api/workflow/posts/<post_id>/development`** - Gets post development fields
4. **Missing `/api/workflow/fields/available`** - Gets available fields for dropdowns

### Solution
Added the missing workflow API endpoints to `blog-core/app.py`:

1. **`GET /api/workflow/prompts/all`** - Returns all prompts with type classification (system/task)
2. **`GET /api/workflow/steps/<step_id>/prompts`** - Returns saved prompts for a specific step
3. **`POST /api/workflow/steps/<step_id>/prompts`** - Saves prompts for a specific step
4. **`GET /api/workflow/posts/<post_id>/development`** - Returns all development fields for a post
5. **`GET /api/workflow/fields/available`** - Returns available fields from post_development table

### Technical Details
- All endpoints use PostgreSQL with psycopg2 and DictCursor
- Proper error handling and JSON responses
- Consistent with the working implementation from the blog service (port 5000)
- Maintains microservice architecture compatibility

### Testing
- Created `test_workflow_api.py` to verify all endpoints are working
- All API endpoints return 200 status codes
- System prompts are being loaded correctly (3 found in test)
- Workflow page loads successfully
- LLM actions content loads and displays correctly

### Files Modified
- `blog-core/app.py` - Added missing workflow API endpoints
- `blog-core/docs/reference/api.md` - Updated API documentation
- `blog-core/docs/changes_log.md` - This file

### Files Added
- `blog-core/test_workflow_api.py` - Test script for workflow API endpoints

### Status
✅ **RESOLVED** - Context panel and Task Prompt panel dropdowns now populate correctly with system prompts and task prompts from the database.

### Next Steps
- Monitor the workflow page to ensure dropdowns continue to work correctly
- Consider adding more comprehensive error handling for edge cases
- May need to expand field availability based on step configuration in the future

---

## 2025-01-20 - Phase 2: LLM Actions Integration Fixed (CORRECTED APPROACH)

### Problem
The blog-core service (port 5001) was trying to fetch and embed LLM Actions content from port 5002, but this approach was destroying the layout and functionality of the LLM Actions module. The content extraction was breaking the UI and preventing proper initialization.

### Root Cause
1. **Incorrect integration approach** - Trying to extract and embed HTML content was breaking the layout and JavaScript functionality
2. **Content extraction complexity** - Regex-based content extraction was unreliable and destroyed the UI structure
3. **Service separation violation** - The approach was undermining the purpose of having separate services

### Solution
**Phase 2 Implementation (CORRECTED):**

1. **Reverted to iframe-based integration**:
   - **Removed embeddable content endpoint** - This was causing layout and functionality issues
   - **Restored direct iframe embedding** - Uses `<iframe>` to embed the full LLM Actions service
   - **Maintains complete service separation** - Each service runs independently with full functionality

2. **Updated workflow template**:
   - **Replaced content fetching** with direct iframe embedding
   - **Simplified JavaScript** - Removed complex content extraction and script execution
   - **Preserved all functionality** - LLM Actions service runs completely independently

3. **Service independence**:
   - **Port 5002 (LLM Actions)** serves its complete, working interface
   - **Port 5001 (Blog-core)** embeds it via iframe without any modification
   - **No content extraction** - Eliminates all layout and functionality issues

### Technical Details
- **LLM Actions Service** (`blog-llm-actions/app.py`):
  - **Removed** `/api/llm-actions/embed` endpoint (was causing issues)
  - **Restored** original `/` endpoint functionality
  - **Maintains** all original layout, styling, and JavaScript functionality

- **Blog-Core Service** (`blog-core/templates/workflow.html`):
  - **Replaced** content fetching with iframe embedding
  - **Simplified** JavaScript to basic iframe management
  - **Preserved** real-time communication capabilities

- **Integration Method**:
  ```html
  <iframe 
      src="http://localhost:5002/?stage={{ current_stage }}&substage={{ current_substage }}&step={{ current_step }}&post_id={{ current_post_id }}"
      style="width: 100%; height: 600px; border: none; border-radius: 8px;"
  ></iframe>
  ```

### Testing
- ✅ LLM Actions service loads correctly on port 5002
- ✅ Blog-core workflow page loads correctly on port 5001
- ✅ Iframe embeds LLM Actions without layout issues
- ✅ All URL combinations work (planning/idea/initial_concept, planning/research/interesting_facts, etc.)
- ✅ Redirect functionality works (302 status for incomplete URLs)
- ✅ Service separation maintained - no code vandalism between services

### Files Modified
- `blog-llm-actions/app.py` - **Removed** problematic `/api/llm-actions/embed` endpoint
- `blog-core/app.py` - **Reverted** `/api/llm-actions/content` to use direct LLM Actions URL
- `blog-core/templates/workflow.html` - **Replaced** content fetching with iframe embedding

### Status
✅ **RESOLVED** - LLM Actions integration now works correctly using iframe embedding. The services remain completely separate and independent, preventing any code vandalism between them.

### Key Benefits
- **Service Independence**: Each service runs completely independently
- **No Layout Issues**: Iframe preserves all original styling and functionality
- **No Code Vandalism**: Changes to one service don't affect the other
- **Simplified Integration**: No complex content extraction or script manipulation
- **Reliable Functionality**: All LLM Actions features work as designed

### Next Steps
- Monitor the iframe integration to ensure it remains stable
- Consider adding iframe communication for enhanced integration features
- Maintain service separation as the primary architectural principle

---

## 2025-01-20 - Iframe Height Optimization (Simplified)

### Problem
The iframe was cutting off most of the LLM Actions content and using scrollbars, creating a poor user experience. Additionally, there were CORS errors and JavaScript errors when trying to access iframe content from different ports.

### Solution
**Simplified iframe height approach:**

1. **Increased default height**:
   - Changed from 600px to 1500px fixed height
   - Added CSS rule for minimum height of 1500px
   - Removed complex dynamic height detection to avoid CORS issues

2. **Simplified height management**:
   - Removed CORS-dependent height detection
   - Set large fixed height (1500px) to show full content
   - Removed periodic height checks that were causing errors

3. **Eliminated CORS issues**:
   - Removed attempts to access iframe content from different port
   - Simplified message handling to avoid cross-origin errors
   - Removed problematic JavaScript that was causing errors

4. **Improved user experience**:
   - No more scrollbars cutting off content
   - Full content visibility with large height
   - No JavaScript errors or CORS warnings

### Technical Details
- **CSS**: Set `min-height: 3000px` and `max-height: none` for iframe
- **JavaScript**: Simple height setting without CORS-dependent operations
- **Iframe**: Fixed height of 3000px to show full content
- **Container**: Changed overflow from `hidden` to `visible` to prevent content cutoff
- **Error prevention**: Removed all cross-origin access attempts

### Testing
- ✅ Iframe now shows full content without scrollbars
- ✅ No CORS errors or JavaScript errors
- ✅ Very large height (3000px) provides full content visibility
- ✅ Container overflow fixed to prevent content cutoff
- ✅ Simplified approach is more reliable
- ✅ Better user experience with no error messages

### Files Modified
- `blog-core/templates/workflow.html` - Simplified iframe height management

### Status
✅ **RESOLVED** - Iframe now displays full LLM Actions content without scrollbars, CORS errors, or JavaScript errors. 