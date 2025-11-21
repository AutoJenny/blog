# Changelog

## 2025-11-20 - Profile Post Theme Matching System Implementation

### Added
- **Vector Embeddings for Profile Matching**: Complete implementation of semantic matching system for profile posts
  - `utils/vector_search/post_extractor.py` - Extracts post content for embedding
  - `utils/profile_matching/post_matcher.py` - Finds similar products, suppliers, and categories
  - `utils/profile_matching/normalization.py` - Weighted random selection algorithm
  - `blueprints/header/api_seo_meta.py` - API endpoints for embedding generation and overrides
  - `templates/header/includes/vector_embeddings_panel.html` - UI panel for visualization
  - `static/js/header/vector-embeddings-panel.js` - Frontend functionality
  - `migrations/add_post_embeddings.sql` - Database schema updates

### Changed
- **Producer Embeddings**: Extended vector search to include producers/suppliers
  - Added `chunk_producer()` method to `ContentChunker`
  - Updated `scripts/generate_embeddings.py` to support `--producers` argument
  - 3 producers embedded and added to FAISS index (2,115 total vectors)

### Features
- **Post Content Extraction**: Extracts and combines content from `post_development` for embedding
- **Multi-Type Similarity Search**: Searches products, categories, and suppliers simultaneously
- **Intelligent Selection**: Weighted random selection algorithm with normalization
- **Manual Override**: Users can override automatic selection and save preferences
- **SEO Meta Integration**: Full UI integration on SEO Meta page

### Documentation
- `docs/PROFILE_POST_THEME_MATCHING_IMPLEMENTATION.md` - Complete implementation documentation
- Updated `docs/PROFILE_POST_THEME_MATCHING_ANALYSIS.md` to reflect implementation status

### Testing
- All core functionality tested and verified
- API endpoints working correctly
- Frontend UI functional
- Database operations confirmed

## 2025-01-XX - Post Type Isolation Audit & Implementation Plan

### Added
- **Post Type Audit**: Comprehensive audit of post type architecture (themes, profiles, recipes)
  - `docs/POST_TYPE_ISOLATION_AUDIT.md` - Complete analysis of isolation between post types
  - `docs/POST_TYPE_FIXES_IMPLEMENTATION_PLAN.md` - Detailed implementation plan for fixes
  - `docs/POST_TYPE_FIXES_SUMMARY.md` - Executive summary of fixes needed
- **Findings**: Identified three areas requiring attention:
  1. Missing `post_type` variables in routes (mostly resolved)
  2. Workflow substages visibility (needs naming convention and visual indicators)
  3. `illustration_method` deprecation (needs migration to `post_type`-based system)

### Documentation
- Audit confirms architecture is mostly robust with good isolation between types
- Implementation plan ready for 2-3 week execution
- Profile development can proceed safely with identified precautions

## 2025-01-XX - Publishing System: Removed Caching & Fixed Section Heading Quotes

### Changed
- **HTML Generation**: Removed all caching mechanisms - HTML is now always generated fresh
  - `clan_publisher.py` no longer loads from cache files
  - `preview_handler.py` no longer writes cache files
  - Template reloads on each render instead of being cached
- **Section Headings**: Added quote removal filter to all templates
  - Template filter: `{{ section.section_heading|replace('"', '')|replace("'", '')|trim }}`
  - Removes inverted commas from section headings on preview and published posts
  - Applied to: `clan_post_raw.html`, `post_preview.html`, `header/preview.html`, `clan_post.html`

### Fixed
- **Quote Display**: Section headings no longer display with quotes on live site
- **Cache Staleness**: Template updates now take effect immediately without server restart
- **HTML Consistency**: Preview and published HTML are now identical (except image URLs)

### Updated Files
- `blog-launchpad/clan_publisher.py` - Removed cache loading, always generates fresh HTML
- `blog-launchpad/publish/preview_handler.py` - Removed cache writing
- `blog-launchpad/publish/post_renderer.py` - Template reloads each time
- `templates/launchpad/clan_post_raw.html` - Added quote removal filter
- `templates/launchpad/post_preview.html` - Added quote removal filter
- `templates/header/preview.html` - Added quote removal filter
- `blog-launchpad/templates/clan_post.html` - Added quote removal filter

### Documentation
- `docs/temp/PUBLISHING_SYSTEM_UPDATE_2025.md` - New documentation for recent changes

## 2025-01-09 - Snapshot Block Rewritten for Two-Paragraph Chatty Format

### Changed
- **Snapshot Block Compilation**: Completely rewritten to generate two separate chatty paragraphs
  - News paragraph: Chatty overview of news stories with embedded markdown links
  - Events paragraph: Chatty overview of events with embedded markdown links
  - LLM identifies related/overlapping topics and mentions them together naturally
  - Uses conversational, engaging language (3-5 sentences per paragraph)
- **Component Structure**: Reorganized into modular components
  - News Component: Fetches and displays top 5 news items with summaries
  - Events Component: Fetches and displays top 5 event items with summaries
  - Compile Function: Combines both into two LLM-generated paragraphs
- **UI Updates**: Updated editor to show separate components with individual "Generate" buttons
  - Each component has its own output area
  - "Compile Final Selection" button generates the two paragraphs
  - Preview displays two paragraphs separately with NEWS/EVENTS labels

### Fixed
- **LLM Service Method**: Fixed incorrect method call (use `execute_llm_request` instead of `generate`)
- **Event Listener**: Replaced inline onclick with proper event listener for compile button
- **Link Conversion**: Added markdown-to-HTML link conversion in preview route for email compatibility
- **Error Handling**: Removed all fallback text generation - now returns proper errors if LLM fails

### Updated Files
- `blueprints/newsletter.py` - Rewrote compile_snapshot endpoint, added component generation endpoints
- `templates/newsletter/partials/block_editor_snapshot.html` - Modular component UI with event listeners
- `templates/newsletter/partials/snapshot.html` - Two-paragraph preview display
- `docs/newsletter/blocks/snapshot.md` - Updated documentation

## 2025-11-19 - New Products Spotlight Enhanced with LLM Intro & Product Tracking

### Added
- **LLM-Generated Intro Paragraph**: New Products Spotlight now includes a brief intro paragraph
  - Generated by LLM reviewing the three selected products
  - Mentions products are recently added to website
  - Brief commentary on products based on descriptions
  - 2-3 sentences, ~50-75 words
- **Confirm Button**: Added "Confirm Selection & Generate Intro" button in editor
  - Generates intro paragraph via LLM
  - Marks products as launched in database (`newsletter_launched_at` timestamp)
  - Only marks products as launched when user confirms (not on initial selection)
- **Product Pool Management**: Implemented persistent product pool system
  - Stores up to 50 recent products in block payload
  - Enables consistent random selection without running out of options
  - Products selected from pool with category diversity
- **Product Tracking Service**: New service for tracking product launches
  - `mark_products_newsletter_launched()` - Sets `newsletter_launched_at` timestamp
  - `extract_product_ids_from_payload()` - Extracts product IDs from block payload
- **Custom Editor UI**: Replaced JSON editor with custom product selection interface
  - Shows current selection with thumbnails and SKU
  - "Re-choose Products" button for random selection
  - Preview of generated intro paragraph
  - Manual override option (collapsible)

### Changed
- **Title**: Changed from "Products Spotlight" to "New Products Spotlight" in preview
- **Product Selection**: Now selects 3 products (instead of 6) from recent products
  - Uses `first_seen_at` field (from clan.com sync) instead of `created_at`
  - Filters by `id > 10000` to exclude older products
  - Ensures category diversity (different specific categories)
- **Preview Display**:
  - Removed SKU from product display (only shown in editor)
  - Styled "Explore" link as button (smaller than "Read more" button)
  - Added intro paragraph display above products
- **Data Source**: Changed from `product` table to `clan_products` table
  - Uses `first_seen_at` for identifying new products
  - Includes `category_ids` for diversity filtering
  - Full clan.com URLs for product links

### Fixed
- **Clan.com API Date Fields**: Fixed extraction of `created_at` from getProducts API
  - Code was treating API response as list instead of dict
  - Now correctly extracts and parses `created_at` field
  - Created diagnosis document for CLAN.com team regarding missing `updated_at` field

### Updated Files
- `blog-core/newsletter/services/products_intro_service.py` (new)
- `blog-core/newsletter/services/product_tracking.py` (new)
- `blog-core/newsletter/selectors/products.py` (refactored for pool management)
- `blog-core/newsletter/services/block_suggestion_service.py` (updated for pool)
- `blog-core/newsletter/services/block_editor_service.py` (updated confirmation logic)
- `blueprints/newsletter.py` (added intro generation and confirmation endpoints)
- `templates/newsletter/partials/block_editor_new_products.html` (new custom editor)
- `templates/newsletter/partials/new_products.html` (updated title, intro, button styling)
- `blog-launchpad/clan_cache.py` (fixed date field extraction)
- `docs/clan_products/API_DATE_FIELDS_DIAGNOSIS.md` (new)

## 2025-11-19 - Newsletter Preview Redesign with Cream Panels & Dark Brown Text

### Changed
- **Newsletter Preview Styling**: Complete redesign of preview appearance
  - Changed all panel backgrounds from off-white to very light cream (#fef9e7)
  - Updated all text colors from black/gray to very dark brown (#3d2817)
  - Changed borders from light gray to light brown (#e8dcc0)
  - Removed white container background - panels now show individually against dark tiled background
  - All panels have rounded corners (border-radius:8px) for email compatibility
  - Links now use brown color scheme (#6b4e3d) instead of blue
  - Consistent spacing and padding across all panels

### Fixed
- **Tile Background Loading**: Fixed path resolution for base64 tile data
- **Panel Structure**: Each section (header, blocks, footer) now has its own panel with rounded corners

### Updated Files
- All newsletter block partials (intro, snapshot, feature, products, spotlight, category, evergreen, closing)
- Main render template (removed white container, updated colors)
- Header and footer panels (matching cream/brown scheme)

## 2025-11-02 - Newsletter Intro Components Enhanced with LLM & Intelligent Compilation

### Enhanced
- **Events Component**: Now uses LLM to generate conversational comments
  - Fetches full event details including description from database
  - LLM analyzes event content and highlights what's interesting
  - Generates human-like commentary about cultural/historical significance
  - No longer just dry announcements - comments on what makes events notable
- **Theme Component**: Now uses LLM to generate conversational comments
  - Fetches full theme details including description, seasonal context, tags
  - LLM analyzes theme content and highlights relevance
  - Generates human-like commentary about why theme matters
  - No longer just "we're exploring X" - comments on what's interesting
- **Compile Function**: Completely rewritten to use LLM for intelligent compilation
  - LLM considers all three components as information (not sentences to repeat)
  - LLM decides best order (which creates best opening, which should close)
  - Rewrites into single coherent paragraph (2-4 sentences)
  - Weaves information together naturally - doesn't just concatenate
  - Creates welcoming introduction that flows into newsletter content
  - Filters out placeholder/loading messages before processing

### Changed
- **Events Generation**: Replaced simple template with LLM-based generation
  - Old: "Meanwhile, X has announced Y in Z."
  - New: LLM-generated comment about what's interesting about the event
- **Theme Generation**: Replaced simple template with LLM-based generation
  - Old: "This week we're exploring X, Y."
  - New: LLM-generated comment about why the theme matters
- **Compile Logic**: Replaced random shuffle + concatenation with LLM rewriting
  - Old: Randomly shuffled sentences and joined them
  - New: LLM creates coherent paragraph with intelligent ordering

## 2025-11-02 - Newsletter Intro Block Modular UI & LLM Weather Generation

### Added
- **Modular Intro Block Editor**: Reorganized intro block UI into separate component modules
  - Weather Component: Generates conversational weather summary
  - Events Component: Generates event announcement text
  - Theme Component: Generates theme introduction text
  - Each component has its own "Generate" button and output display
  - Compile section combines all three into final paragraph with varied order
- **New API Endpoints**:
  - `GET /newsletter/issue/<id>/block/<id>/generate-weather` - Generate weather component
  - `GET /newsletter/issue/<id>/block/<id>/generate-events` - Generate events component
  - `GET /newsletter/issue/<id>/block/<id>/generate-theme` - Generate theme component
  - `POST /newsletter/issue/<id>/block/<id>/compile-intro` - Compile all components
- **Weather Analysis Service** (`weather_analysis_service.py`):
  - Analyzes weather patterns over 3-week period (1 week before + target week + 1 week after)
  - Compares actual weather to seasonal norms
  - Identifies unusual conditions and trends
  - Uses LLM to generate conversational summaries (no hard-coded templates)

### Changed
- **Weather Summary Generation**: Now uses LLM instead of hard-coded templates
  - Removed all hard-coded phrases and examples
  - LLM analyzes actual weather data vs seasonal norms
  - Generates unique, natural summaries based on actual conditions
  - Prompt emphasizes avoiding clichés and using varied language
- **Intro Block UI**: Complete redesign
  - Old: Single "Regenerate Suggestions" button with suggestions list
  - New: Three separate component modules with individual generate buttons
  - Each module is self-contained with its own JavaScript functions
  - Final compiled paragraph displayed at top
  - Manual override section moved to collapsible details

### Improved
- **Weather Analysis**: 
  - Aggregates weather data over extended period (not just single day)
  - Compares to seasonal norms (winter/spring/summer/autumn averages)
  - Identifies patterns (chilly, mild, rainy, windy, stormy)
  - Detects unusual conditions (unseasonable temps, storms, etc.)
- **Text Generation**:
  - Varies sentence order for natural flow
  - More conversational tone throughout
  - Better integration of weather, events, and theme components

### Files Changed
- `blog-core/newsletter/services/weather_analysis_service.py` - NEW: Weather analysis and LLM generation
- `templates/newsletter/partials/block_editor_intro.html` - Complete rewrite: modular component UI
- `blueprints/newsletter.py` - Added 4 new API endpoints for component generation
- `blog-core/newsletter/selectors/intro.py` - Updated to use new weather analysis service
- `blog-core/newsletter/rendering/intro_text.py` - Updated to handle new component format

## 2025-11-02 - Newsletter Intro Block Fixes & Documentation

### Fixed
- **Regenerate Suggestions**: Fixed "Regenerate Suggestions" button in newsletter intro block
  - Made link validation optional for cached items (skip_validation=True) to improve performance
  - Added fallback logic when validation filters all items
  - Fixed JavaScript selector to find correct element with data-issue-id attribute
  - Improved error handling with content-type checking and better error messages
- **JavaScript Error Handling**: Enhanced error handling in block_editor_intro.html
  - Added element validation before DOM manipulation
  - Improved JSON parsing with content-type checks
  - Added HTML escaping for XSS protection
  - Better error messages displayed to users

### Improved
- **Suggestion Generation**: Optimized suggestion generation to skip link validation for cached items
  - Updated `generate_suggestions()` to accept `skip_validation` parameter
  - Updated all intro/snapshot selectors to use skip_validation=True
  - Added logging for debugging suggestion generation
- **Template Context**: Fixed template include to pass context properly with `with context` directive

### Documentation
- **Block Documentation**: Split block-editors.md into individual files per block type
  - Created detailed `docs/newsletter/blocks/intro.md` with complete file listings, line counts, JavaScript functions, API endpoints, and testing instructions
  - Created documentation files for all block types: snapshot, feature, products, category, evergreen, closing
  - Updated `docs/newsletter/block-editors.md` to be overview/index with links to individual blocks
  - Updated `docs/newsletter.md` to link to individual block documentation

### Files Changed
- `blog-core/newsletter/selectors/intro.py` - Added skip_validation parameter
- `blog-core/newsletter/selectors/snapshot.py` - Added skip_validation parameter
- `blog-core/newsletter/services/block_editor_service.py` - Updated to use skip_validation
- `blog-core/newsletter/services/suggestion_service.py` - Added skip_validation with fallback logic
- `blueprints/newsletter.py` - Improved error handling and logging
- `templates/newsletter/partials/block_editor_base.html` - Fixed template context passing
- `templates/newsletter/partials/block_editor_intro.html` - Fixed JavaScript selectors and error handling
- `docs/newsletter/blocks/*.md` - New detailed block documentation files

## 2025-01-XX - Product Tag Editor Enhancements

### Fixed
- **Title Filter**: Fixed title filter to work on currently displayed products with Enter key support
- **Product Count Display**: Fixed spacing in "products selected" text and count accuracy
- **Page Load**: Fixed automatic product loading on page initialization
- **API Endpoint**: Fixed `/products/tag-editor/api/search` to accept '*' query for fetching all products

### Improved
- Added `applyTitleFilterToCurrentProducts()` function for client-side filtering
- Improved title filter integration with other filters (search, category, tags)
- Increased pagination limit to 10000 products for better coverage
- Enhanced selected product count to reflect actual displayed products

## 2025-11-11 - Knowledge Base Integration

### Added
- **Knowledge Base Database Schema**: Created `clan_kb_categories` and `clan_kb_articles` tables with full-text search indexes and change detection support
- **Knowledge Base Cache Module** (`blog-launchpad/clan_kb_cache.py`): 
  - Fetches categories and articles from CLAN Knowledge Base API
  - Hash-based change detection for articles
  - Image downloading and local caching for feature images
  - On-demand sync functionality
  - Graceful handling of missing parent categories with PostgreSQL savepoints
- **Migration File**: `migrations/create_clan_kb_tables.sql` for creating KB tables
- **Documentation**: 
  - `docs/data_intelligence/knowledge_base/TABLE_STRUCTURE_PROPOSAL.md` (approved schema)
  - `docs/data_intelligence/knowledge_base/IMPLEMENTATION_STATUS.md` (implementation guide)
  - Updated `docs/data_intelligence/knowledge_base/README.md`

### Technical Details
- **Tables**: `clan_kb_categories` (167 categories), `clan_kb_articles` (29 articles stored)
- **Features**: Change tracking via `article_content_hash` and `last_content_change_at`
- **Image Caching**: Downloads feature images to `static/images/kb/` directory
- **Error Handling**: Uses PostgreSQL savepoints for per-category error isolation
- **API Integration**: Connects to `https://clan.com/clan/api/getKnowledgebaseCategories` and `getKnowledgebaseArticles`
- **Rate Limiting**: Handles HTTP 429 responses gracefully (some categories may need retry)

### Next Steps
- Integrate KB articles into vector search index
- Add KB search to content generator modal
- Use KB context in content generation prompts

## 2025-11-11 - Product Data Enhancement & Vector Search Update

### Product Data Fields
- **Additional Data**: Added `additional_data` (JSONB) field to `clan_products` table
  - Stores structured product attributes (material, pattern, shirt style, clan crest info, etc.)
  - Format: `{key: {label, value, code}}` structure from CLAN API
- **Dimensions**: Added `dimensions` (TEXT) field to `clan_products` table
  - Stores product dimensions when available from CLAN API
- **Database Migration**: Added columns with `ADD COLUMN IF NOT EXISTS` for safe upgrades
- **Storage**: Updated `store_single_product()` and `store_products()` to save new fields
- **Extraction**: Updated `ClanDataExtractor` to include new fields in extracted data

### UI Enhancements
- **Product Data Review Page**: Enhanced display of product information
  - Specifications section moved into Product Description panel (styled consistently)
  - Additional Information section added (displays additional_data with labels/values)
  - Dimensions displayed when available
  - All sections styled consistently (blurb, bullets, main description, specifications, additional data)
- **Styling**: Added CSS for new description sections (purple for specifications, teal for additional data)

### Vector Search System Enhancement
- **Chunking Updates**: Enhanced `ContentChunker` to include all product data fields
  - **Products now include**:
    - Product name and producer
    - Short description (blurb)
    - Full description (including bullet points)
    - **Specifications** (when available)
    - **Product Details** (additional_data: material, pattern, shirt style, clan crest info, etc.)
    - **Dimensions** (when available)
    - **Available Options** (configurable_options: sizes, colors, etc.)
    - Supplier information
  - **Categories now include**:
    - Category name and description
    - **Enhanced heritage data** (all 5 dimensions with new dictionary format):
      - Historical Origins (narrative, key themes, significant elements)
      - Cultural Significance (narrative, key themes, significant elements)
      - Evolution (narrative, key themes, significant elements)
      - Scottish Heritage Connections (narrative, key themes, significant elements)
      - Industrial Legacy (narrative, key themes, significant elements)
    - Handles both legacy string format and new dictionary format
- **Index Rebuild**: Regenerated all chunks and rebuilt FAISS vector index
  - 1,157 product chunks updated
  - 259 category chunks updated
  - Total: 1,416 vectors in index
  - All new fields now searchable via semantic search

### Technical Details
- **Transformer Updates**: `transform_product_for_ui()` now extracts `additional_data` and `dimensions` from API
- **Chunking Query**: Updated `process_all_products()` to fetch new fields from database
- **Heritage Data**: Updated `chunk_category()` to extract narratives, themes, and elements from new dictionary format

## 2025-11-XX - Newsletter Event Management

### Event Classification & Management
- **Event Recurrence Classification**: Added LLM-based classification system to identify annual vs one-off events
  - Enhanced prompt to emphasize festivals are annual events
  - Added heuristic pre-check: any event with "festival" in title = annual
  - Added known annual event keywords (hogmanay, celtic connections, royal highland show, etc.)
  - Classification filter added to Events Synopsis page with visual badges
  - Manual override capability on event detail page

### Event Editing & Deletion
- **Inline Editing**: Added direct editing capabilities on event detail page
  - Title: Click-to-edit with full-width input
  - Description: Textarea editing with Save/Cancel
  - Date Text: Raw date text field editing
  - Event Date: Inline date picker
  - Location: Inline text input
  - All edits save to both database columns and raw_data JSON
- **Delete Functionality**: Added delete button with confirmation dialog
  - Checks for soft delete column first, falls back to hard delete
  - Redirects to events list after successful deletion
- **API Endpoints**: 
  - `POST /newsletter/events/<id>/update` - Update any event field
  - `DELETE /newsletter/events/<id>` - Delete event (soft or hard delete)
  - `POST /newsletter/events/<id>/recurrence-type` - Update classification manually

### Database Schema
- **Event Recurrence Type**: Added `event_recurrence_type` column to `newsletter_source_item` table
  - Values: `'annual'`, `'one_off'`, or `NULL` (unclassified)
  - Indexed for efficient filtering
  - Migration: `migrations/add_event_recurrence_type.sql`

### Classification Service
- Created `event_classification_service.py` with LLM-based classification
- Includes heuristic fallback for known annual events
- Batch classification script: `classify_all_events.py`

### Technical Improvements
- Fixed missing `db_manager` imports in event update/delete routes
- Improved event detail service to include recurrence type in queries
- Enhanced event filtering to catch false positives (newsletter signups, accommodation listings, recurring patterns)

## 2025-11-01 (continued - evening)

- Section Titling: Fixed bug where only first section received title/description - now generates for all sections
- Section Titling: Enhanced LLM prompt to explicitly list all sections with themes and topics
- Section Titling: Added validation to ensure LLM generates exactly the correct number of section titles
- Section Titling: Fixed section matching logic bug that was overwriting outer loop variable
- Section Titling: Added direct writes to post_section table in addition to post_development.sections
- Idea Expansion: Enhanced Important Notes highlighting in prompt with mandatory requirements and explicit instructions
- Idea Expansion: Improved theme data fetching to handle cases where theme selected for week before post creation

## 2025-11-01 (continued)

- Page Headers: Replaced post ID display with date span, week number, and selected theme across all blog pipeline pages
- Page Headers: Added fallback logic to fetch theme from week schedule when post schedule doesn't include theme
- Page Headers: Removed stage prefix (Planning/Calendar) from header - now shows only week info and theme
- API: Updated planning_api_posts to include selected_theme_title in schedule responses
- UI: Added CSS styling for new header elements (prefix, week info, separator, theme)

## 2025-11-01

- Week View Navigation: Added localStorage persistence for calendar week view (remembers selected week/year across sessions).
- Week View Navigation: Added "This week" button to quickly jump to the current week.
- Week View Navigation: Replaced week number input with month/week picker interface showing all weeks organized by month with date ranges.
- Theme Selection: Fixed theme selection persistence on ideas week page - themes now save to calendar_schedule when selected.
- Theme Display: Fixed calendar week view to correctly show selected themes using idea_id from calendar_schedule.
- Idea Modal: Added delete button to unified idea/theme/event modal (only visible when editing existing items).
- API: Added DELETE endpoint for calendar events.
- API: Updated calendar_schedule endpoint to include idea_id in responses.

## 2025-10-31

- Week View: Added filters (Blog Themes, Events, Syndication) and integrated Facebook Product syndication schedule rendering per weekday with time.
- Week View: Introduced a single week-wide Blog Themes row above the grid with left-aligned titles.
- Week View: Added calendar day numbers to the right of each day header (Mon–Sun).
- Scheduling: Added backfill and purge endpoints to normalize and hard-delete legacy/inactive schedule rows; `get_schedules` now filters `is_active = true`.


