# Component Audit: publish_orchestrator.py

## File Location
`blog-launchpad/publish/publish_orchestrator.py`

## Purpose
Orchestrates the publication flow using ClanPublisher methods. Main entry point for publishing posts to clan.com.

## Functions

### `publish_post_to_clan(post_id)`
**Purpose**: Main orchestration function for publishing a post to clan.com.

**Flow**:
1. Load post data via `load_post_data(post_id)`
2. Load sections via `load_sections(post_id)`
3. Find header image via `get_header_image(post_id)` (from header_image_finder)
4. Prepare post for publication via `prepare_post_for_publication(post, header_image)`
5. Initialize `ClanPublisher()`
6. Process images via `publisher.process_images(post, sections)`
7. Generate HTML via `publisher.get_preview_html_content(post, sections, uploaded_images)`
8. Create/update post via `publisher.create_or_update_post(post, html_content, is_update, uploaded_images)`
9. Update database with results

**Issues Identified**:
1. ✅ Good: Clear step-by-step flow with logging
2. ⚠️ **RISK**: Step 3 comment says "single source of truth" but then Step 4 calls `prepare_post_for_publication` which may modify header_image
3. ⚠️ **RISK**: No error recovery - if any step fails, entire process fails
4. ✅ Good: Returns structured error messages

## Dependencies
- `clan_publisher.ClanPublisher`
- `config.database.db_manager`
- `publish.post_data_loader` (load_post_data, load_sections, prepare_post_for_publication)
- `publish.header_image_finder` (get_header_image)

## Integration Points
- **Called by**: Flask routes in `blueprints/launchpad/publishing.py`
- **Calls**: ClanPublisher, post_data_loader, header_image_finder

## Recipe-Specific Behavior
**NONE** - This module treats all post types identically.

## Critical Findings

### HIGH RISK
1. **Header Image Handling**: The comment says "single source of truth" but the flow is:
   - Step 3: Find header image
   - Step 4: Prepare post (which may modify header_image)
   - Step 5: Process images (which expects header_image in post dict)
   
   This creates a potential race condition or inconsistency if `prepare_post_for_publication` modifies the header_image.

2. **No Validation Before Processing**: No check that header_image path actually exists before attempting upload.

### MEDIUM RISK
1. **Error Handling**: If image processing fails, the entire publication fails. No partial success handling.

2. **Database Updates**: Database is updated AFTER successful publication, but if publication succeeds and database update fails, state is inconsistent.

## Recommendations
1. **IMMEDIATE**: Add validation that header_image path exists before processing
2. **SHORT TERM**: Clarify "single source of truth" - document which function is authoritative
3. **MEDIUM TERM**: Add transaction handling for database updates
4. **ONGOING**: Add retry logic for transient failures

