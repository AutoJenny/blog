# Launchpad Blueprint - Deep Dive

**File**: `blueprints/launchpad_old.py` (2,202 lines)  
**Status**: Active in production, 30% modularized  
**Last Updated**: 2025-10-28

## Current Structure

### Active File
- **`blueprints/launchpad_old.py`** - Monolithic file containing all launchpad functionality
- All routes currently active via passthrough in `blueprints/launchpad/__init__.py`
- Currently being phased out in favor of modular structure

### Routes Summary (40 total)

#### Core Routes (2)
- `/` - Main launchpad dashboard
- `/health` - Health check

#### Publishing Routes (5)
- `/publishing` - Publishing management page
- `/api/publish/<int:post_id>` - Publish post to clan.com
- `/clan-api-data/<int:post_id>` - View API data
- `/clan-post-html/<int:post_id>` - View HTML content
- `/api/validate-publish/<int:post_id>` - Validate publish data

#### Syndication Routes (29)
- `/syndication` - Syndication dashboard
- `/syndication/dashboard` - Redirect to main
- `/syndication/<platform>/<channel>` - Platform configuration
- `/api/syndication/posts` - Get posts for syndication
- `/api/syndication/posts/<int:post_id>` - Get post details
- `/api/syndication/post-sections/<int:post_id>` - Get sections
- `/api/syndication/section-image-url/<int:post_id>/<int:section_id>` - Get image URL
- `/api/syndication/save-generated-content` - Save content
- `/api/syndication/get-generated-content/<int:item_id>/<content_type>` - Get content
- `/api/syndication/update-queue-status` - Update queue
- `/api/syndication/social-media-platforms` - Get platforms
- `/api/syndication/content-processes` - Get content processes
- `/api/queue` - Get posting queue
- `/api/queue/<int:item_id>` (DELETE) - Delete queue item
- `/api/queue/clear` - Clear queue
- `/api/queue/update-status` - Update queue status
- `/api/syndication/schedules` - Get schedules
- `/api/syndication/schedules` (POST) - Add schedule
- `/api/syndication/schedules/<int:schedule_id>` (DELETE) - Delete schedule
- `/api/syndication/schedules/test` - Test schedules
- `/api/syndication/schedules/clear` - Clear schedules
- `/api/syndication/llm-prompts/<int:process_id>` - Get prompts
- `/api/syndication/llm-prompts/<int:process_id>` (PUT) - Update prompts
- `/api/syndication/today-status` - Get today's status
- `/api/syndication/post-now` - Post now
- `/api/syndication/pieces` - Get syndication pieces
- `/api/social-media/timeline` - Get social media timeline
- `/api/syndication/facebook/credentials` (GET/POST) - Facebook credentials
- `/api/auto-replenish-all` (POST) - Auto replenish queues

#### Cross-Promotion Routes (1)
- `/cross-promotion` - Cross-promotion management

#### One-Click Blog Routes (1)
- `/one-click-blog` - One-click blog automation

#### General API Routes (3)
- `/api/posts` - Get all posts
- `/social-media-command-center` - Command center

### Helper Functions
- `get_post_with_development(post_id)` - Fetch post with development data
- `get_post_sections_with_images(post_id)` - Fetch sections with image metadata
- `find_header_image(post_id)` - Find header image path
- Various database query helpers

## Target Modular Structure

### Modules Created (Ready but Not Active)

#### 1. `blueprints/launchpad/core.py` (17 lines)
**Status**: ✅ Ready  
**Routes**: `/`, `/health`  
**Dependencies**: None

#### 2. `blueprints/launchpad/cross_promotion.py` (49 lines)
**Status**: ✅ Ready  
**Routes**: `/cross-promotion`  
**Dependencies**: `db_manager`

#### 3. `blueprints/launchpad/one_click_blog.py` (12 lines)
**Status**: ✅ Ready  
**Routes**: `/one-click-blog`  
**Dependencies**: None

#### 4. `blueprints/launchpad/publishing.py` (599 lines)
**Status**: ✅ Ready (but needs testing)  
**Routes**: 
- `/publishing`
- `/api/publish/<int:post_id>`
- `/clan-api-data/<int:post_id>`
- `/clan-post-html/<int:post_id>`
- `/api/validate-publish/<int:post_id>`

**Helper Functions**:
- `get_post_with_development()`
- `get_post_sections_with_images()`
- `find_header_image()`

**Dependencies**: 
- `db_manager`
- `blog-launchpad/clan_publisher.py`
- `config/paths.py`

#### 5. `blueprints/launchpad/syndication.py` (13 lines)
**Status**: 📦 Placeholder only  
**Routes**: None yet  
**Needs**: All 29 syndication routes extracted

#### 6. `blueprints/launchpad_utils.py` (136 lines)
**Status**: ✅ Active in both old and modular systems  
**Functions**: 
- `get_next_posting_slot()`
- `strip_html_doc()`

## Known Issues with Modular Structure

### Publishing Module Issues
- Created successfully but not integrated
- Previous attempt caused publishing failures
- Needs careful testing before activation
- Dependencies on external publisher class need verification

### Syndication Module Status
- Only has placeholder code
- ~1,400 lines still in `launchpad_old.py`
- Complex routing with 29 endpoints
- Shares dependencies with publishing module

## Activation Strategy

### Phase 1: Test Publishing Module (Current)
1. Keep `launchpad_old.py` active for stability
2. Test `publishing.py` module in isolation
3. Fix any integration issues
4. Gradually activate one module at a time

### Phase 2: Complete Syndication Extraction
1. Extract all 29 syndication routes
2. Create helper function module if needed
3. Ensure no route conflicts

### Phase 3: Full Activation
1. Update `blueprints/launchpad/__init__.py` to import all modules
2. Test all routes thoroughly
3. Remove `launchpad_old.py` once verified

### Phase 4: Cleanup
1. Delete `launchpad_old.py`
2. Delete backup files
3. Update documentation

## Dependencies

### External Dependencies
- `blog-launchpad/clan_publisher.py` - Publishing to clan.com
- `modules/llm_service.py` - LLM content generation
- `config/paths.py` - Path resolution
- `config/database.py` - Database access

### Internal Dependencies
- `blueprints/launchpad_utils.py` - Shared utilities
- Various helper functions for database queries

## Testing Strategy

Before removing `launchpad_old.py`:
1. ✅ Test all core routes (`/`, `/health`)
2. ✅ Test cross-promotion route
3. ✅ Test one-click-blog route
4. ⏳ Test all publishing routes (publish, validate, API data views)
5. ⏳ Test all syndication routes (29 endpoints)
6. ⏳ Test social media integration
7. ⏳ Test queue management
8. ⏳ Test scheduling functionality

## Notes

- The modular structure exists but is not active to avoid breaking production
- Publishing failed when previously attempted with modular structure
- Current approach: keep old system stable, build new system alongside
- Eventually will switch over once new system is proven stable

