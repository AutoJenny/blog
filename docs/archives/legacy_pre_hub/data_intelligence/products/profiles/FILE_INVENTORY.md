# Product & Category Profiles - File Inventory

Complete list of all files created, modified, or extended for the Profiles feature.

---

## New Files Created

### Database Migrations

1. `migrations/create_producers_table.sql`
   - Creates `producers` table
   - Adds indexes

2. `migrations/add_profile_fields_to_post.sql`
   - Adds profile fields to `post` table
   - Adds indexes

3. `migrations/add_producer_id_to_clan_products.sql`
   - Adds `producer_id` to `clan_products`
   - Adds index

4. `migrations/add_specifications_to_clan_products.sql`
   - Adds `specifications` JSONB column
   - Adds GIN index

5. `migrations/add_heritage_to_categories.sql`
   - Adds heritage data columns to `clan_categories`
   - Adds GIN index

### Migration Scripts

6. `scripts/apply_profile_migrations.py`
   - Applies all Phase 1 migrations in order

7. `scripts/migrate_suppliers_to_producers.py`
   - Populates `producers` table from `clan_products.supplier_name`
   - Links products to producers

### Backend API Files

8. `blueprints/planning_api_calendar_profiles.py`
   - Calendar profiles API endpoint
   - Function: `api_calendar_profiles(year, week_number)`

9. `blueprints/planning_api_profiles.py`
   - Profile CRUD API endpoints
   - Functions: `api_create_profile()`, `api_get_profile()`, `api_update_profile()`, `api_delete_profile()`

### Data Collection Utilities

10. `utils/product_specifications_scraper.py`
    - Scrapes product specifications from clan.com pages
    - Class: `ProductSpecificationsScraper`

11. `utils/producer_research.py`
    - Web research for producer information
    - Class: `ProducerResearcher`

12. `utils/category_heritage_research.py`
    - LLM + web research for category heritage
    - Class: `CategoryHeritageResearcher`

13. `utils/representative_products_selector.py`
    - Selects representative products with price diversity
    - Class: `RepresentativeProductsSelector`

### Frontend Templates

14. `templates/profiles/product_profile.html`
    - Product profile page template

15. `templates/profiles/category_profile.html`
    - Category profile page template

16. `templates/profiles/index.html`
    - Profile index/browse page

17. `templates/planning/calendar/profile_modal.html`
    - Profile creation/editing modal

### Partial Templates

18. `templates/profiles/partials/_hero.html`
19. `templates/profiles/partials/_quick_facts.html`
20. `templates/profiles/partials/_category_context.html`
21. `templates/profiles/partials/_object_section.html`
22. `templates/profiles/partials/_maker_section.html`
23. `templates/profiles/partials/_context_section.html`
24. `templates/profiles/partials/_materials_section.html`
25. `templates/profiles/partials/_origins_section.html`
26. `templates/profiles/partials/_materials_methods_section.html`
27. `templates/profiles/partials/_cultural_meaning_section.html`
28. `templates/profiles/partials/_gallery.html`
29. `templates/profiles/partials/_representative_examples.html`
30. `templates/profiles/partials/_explore_links.html`
31. `templates/profiles/partials/_credits.html`
32. `templates/profiles/partials/_swatch_panel.html`

### Frontend JavaScript

33. `static/js/planning/profile-modal-core.js`
    - Profile modal JavaScript class
    - Class: `ProfileModal`
    - Global: `getProfileModal()`

### Frontend CSS

34. `static/css/profiles.css`
    - Profile page styles

35. `static/css/planning/profile-modal.css`
    - Profile modal styles

### Documentation

36. `docs/data_intelligence/products/section-types.md`
    - Section type definitions

37. `docs/data_intelligence/products/implementation-status.md`
    - Implementation status tracking

38. `docs/data_intelligence/products/PRODUCT_CATEGORY_PROFILES_DOCUMENTATION.md`
    - Complete technical documentation (this project)

39. `docs/data_intelligence/products/QUICK_START_GUIDE.md`
    - Quick start guide for new developers

40. `docs/data_intelligence/products/FILE_INVENTORY.md`
    - This file

---

## Modified Files

### Backend

1. `blueprints/planning.py`
   - Added route: `@bp.route('/api/calendar/profiles/<year>/<week_number>')`
   - Added routes: `@bp.route('/api/profiles')` (POST) and `@bp.route('/api/profiles/<id>')` (GET, PUT, DELETE)
   - Modified imports (fixed `planning_titling` import)

2. `blueprints/clan_cache.py`
   - Added endpoint: `@bp.route('/api/clan/products/<sku>/scrape-specifications', methods=['POST'])`
   - Function: `scrape_product_specifications(sku)`

### Frontend

3. `templates/planning/calendar/week_view.html`
   - Added Profiles row HTML
   - Added Profiles filter pill
   - Added Profiles filter styling
   - Included `profile_modal.html`
   - Added CSS link for `profile-modal.css`
   - Added JS script for `profile-modal-core.js`

4. `static/js/planning/calendar-week-view.js`
   - Added profile loading: `profilesPromise = fetchJSON(...)`
   - Added profile rendering in `loadWeek()` function
   - Added profile item rendering in `renderItems()` function
   - Added `showProfiles` filter toggle
   - Added profiles filter to `updateFilterVisuals()`
   - Added profiles filter to toggle event listeners

---

## Extended Files (No Changes, But Used)

### Existing Systems Used

1. **Blog System**
   - `post` table (extended with profile fields)
   - `post_section` table (used for profile sections)
   - `post_images` table (used for profile images)
   - `post_tags` table (used for profile tags)

2. **Calendar System**
   - `calendar_week_posts` table (used for profile scheduling)
   - `post_type_config` system (used for default weekday)

3. **Product/Category System**
   - `clan_products` table (extended with profile fields)
   - `clan_categories` table (extended with heritage fields)
   - Existing product/category APIs

4. **LLM System**
   - `blueprints.llm_actions.LLMService` (used for category heritage analysis)

---

## File Count Summary

- **New Files**: 40
- **Modified Files**: 4
- **Total Files**: 44

### By Category

- **Migrations**: 5 SQL files
- **Migration Scripts**: 2 Python files
- **Backend API**: 2 Python files
- **Data Utilities**: 4 Python files
- **Templates**: 19 HTML files (3 main + 16 partials)
- **JavaScript**: 1 JS file
- **CSS**: 2 CSS files
- **Documentation**: 4 MD files

---

## Dependencies

### Python Packages
- `psycopg` / `psycopg2` - Database access
- `beautifulsoup4` - HTML parsing for scraping
- `requests` - HTTP requests for scraping and research
- Flask - Web framework (already in use)

### JavaScript Libraries
- Font Awesome - Icons (already in use)
- Lightbox2 - Gallery lightbox (referenced in templates)

### External Services
- OpenAI API (optional, for LLM analysis)
- Ollama (fallback, for LLM analysis)
- Web Search API (placeholder, for producer/category research)

---

## Testing Checklist

### Database
- [ ] Verify `producers` table exists and has data
- [ ] Verify profile fields exist in `post` table
- [ ] Verify `producer_id` exists in `clan_products`
- [ ] Verify `specifications` column exists in `clan_products`
- [ ] Verify heritage columns exist in `clan_categories`

### API Endpoints
- [ ] Test `GET /planning/api/calendar/profiles/<year>/<week>`
- [ ] Test `POST /planning/api/profiles`
- [ ] Test `GET /planning/api/profiles/<id>`
- [ ] Test `PUT /planning/api/profiles/<id>`
- [ ] Test `DELETE /planning/api/profiles/<id>`
- [ ] Test `POST /api/clan/products/<sku>/scrape-specifications`

### Frontend
- [ ] Test profile modal opens from calendar
- [ ] Test product search in modal
- [ ] Test category selection in modal
- [ ] Test profile creation
- [ ] Test profile appears in calendar
- [ ] Test profile click handler

### Data Tools
- [ ] Test product specifications scraper
- [ ] Test producer research (placeholder)
- [ ] Test category heritage research (requires LLM)
- [ ] Test representative products selector

---

## Notes

- All migrations have been applied successfully
- Profile system is functional for creation and scheduling
- Public viewing routes not yet implemented
- Newsletter integration pending
- Auto-tagging pending

---

**Last Updated**: 2025-01-27

