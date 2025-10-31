# Newsletter Module

This document outlines the newsletter system: schema, flows, UI, adapters, and file-size guardrails.

## Schema (Postgres)
- `newsletter_issue(id, target_week, status, subject, preheader, theme_id, last_sent_at, created_at, updated_at)`
- `newsletter_block(id, issue_id, type, enabled, position, payload_json, description, suggested_items, auto_selected_item_id, manual_override, created_at, updated_at)`
- `newsletter_evergreen(id, topic, text, length, season, region_tags, last_used_at, created_at, updated_at)`
- `newsletter_category_feature(id, title, body_html, topic, approved, last_used_at, created_at, updated_at)`
- `newsletter_snapshot_source(id, name, base_url, type, enabled, api_key_ref, created_at, updated_at)`
- `newsletter_rotation(id, topic, cooldown_weeks, weight, created_at, updated_at)`
- `newsletter_send_log(id, issue_id, provider, provider_id, sent_at, checksum, created_at)`
- `newsletter_source_item(id, source_name, title, url, published_at, event_date, location, category, raw_data, signal_score, freshness_score, combined_score, cached_at, created_at)`
- `newsletter_source_cache(id, source_name, last_fetched_at, last_status, notes, created_at, updated_at)`
- `newsletter_block_type(type, description)` - default descriptions for block types

Migrations:
- `migrations/20251030_create_newsletter_tables.sql` - Initial schema
- `migrations/20251030_add_theme_id_to_newsletter_issue.sql` - Theme integration
- `migrations/20251030_add_block_descriptions.sql` - Block type descriptions
- `migrations/20251031_add_newsletter_source_items.sql` - Source aggregation system

## High-level flow
1. **Source prefetch** (daily): External sources (RSS, Reddit, HTML) are fetched, scored, and cached in `newsletter_source_item`.
2. **Auto-draft** (weekly): Builds an issue with blocks using unified suggestion system:
   - Intro: Aggregates weather/event/community suggestions
   - Snapshot: Single-item from source suggestions
   - Feature/Products/Category/Evergreen: Content from existing selectors
   - All blocks store `suggestions` array in payload for editor override
3. **Editor workflow**: `/newsletter/issue/:id` UI provides:
   - Suggestions list with scores
   - Auto-select toggle (enabled by default)
   - Manual override textarea
   - Preview and block management
4. **QA checks**: Validates links (including suggestion URLs), images, alt text, and content safety for suggestions.
5. **Preview, approve, send**: Platform-agnostic HTML via adapter.

## UI & Endpoints

### Dashboard
- `GET /newsletter` - Dashboard (list + new draft + autodraft)
- `POST /newsletter/issue` - Create new issue
- `POST /newsletter/autodraft` - Weekly autodraft trigger

### Issue Management
- `GET /newsletter/issue/:id` - Issue editor (blocks list with suggestion UI)
- `POST /newsletter/issue/:id/theme` - Update theme selection
- `POST /newsletter/issue/:id/delete` - Soft delete issue
- `GET /newsletter/issue/:id/preview` - HTML preview
- `GET /newsletter/issue/:id/qa` - QA checks
- `POST /newsletter/issue/:id/approve` - Approve issue
- `POST /newsletter/issue/:id/send` - Send (adapter=preview default)

### Block Editor API (JSON)
- `GET /newsletter/issue/:id/block/:block_id/suggestions` - Get suggestions for block
- `POST /newsletter/issue/:id/block/:block_id/select-suggestion` - Apply a suggestion
- `POST /newsletter/issue/:id/block/:block_id/override` - Save manual override
- `GET /newsletter/issue/:id/block/:block_id/preview` - Preview block HTML

### Block Management
- `POST /newsletter/block/:id/toggle` - Enable/disable block
- `POST /newsletter/block/:id/update` - Update block payload
- `POST /newsletter/block/:id/delete` - Delete block
- `POST /newsletter/issue/:id/block/add` - Add new block
- `POST /newsletter/block/:id/move` - Move block up/down

## Source Aggregation System

External content is aggregated from multiple sources:
- **RSS Feeds**: BBC Scotland, Met Office (via `RSSAdapter`)
- **Reddit API**: /r/Scotland, /r/Highlands (via `RedditAdapter`)
- **HTML Scrapers**: Historic Environment Scotland, Museums/Galleries "What's On" pages (via `HTMLAdapter`)

All sources are normalized to common shape, scored (freshness + signal), and cached in `newsletter_source_item`.

### Scoring Rules
- **Freshness**: Items in -3 to +10 day window get higher scores
- **Signal**: Source authority (BBC=10.0, Met Office=9.0, Reddit=6.0-8.0 based on engagement)
- **Diversity**: Prefers mix of categories (weather/event/community)
- **Safety**: Filters political keywords, title length limits, requires valid URLs

See `blog-core/newsletter/services/scoring.py` and `blog-core/newsletter/services/suggestion_service.py`.

## Block Editors

Block editors provide suggestion-based content selection with human override. See [Block Editors Documentation](block-editors.md) for detailed information.

- **Intro Block**: Aggregates weather/event/community suggestions, generates 2-3 sentence text
- **Snapshot Block**: Single-item focus from source suggestions
- **Other Blocks**: Feature, Products, Category, Evergreen use existing selectors with suggestion storage

All blocks support:
- Auto-select toggle (enabled by default)
- Suggestions list with scores
- Manual override textarea
- Preview functionality

## Rendering
- Templates under `templates/newsletter/partials/` per block type.
- Block editors under `templates/newsletter/partials/block_editor_*.html`.
- `templates/newsletter/render.html` composes blocks; platform-agnostic HTML.

## Adapters
- Interface in `newsletter/adapters/base.py`.
- Implemented: `preview` (stores last send), stubs for Mailchimp and SES.
- Choose via config later; templates remain unchanged.

## File-size guardrail
- Policy: split any file approaching ~400–500 LOC into smaller modules/partials.
- Enforced by structure and a repo script (see below).

## File-size check script
Run the guardrail checker to warn on large files:

```
python3 scripts/check_file_sizes.py --max-loc 500
```

It prints warnings for `.py` and `.html` files exceeding the limit (excluding `venv`, `static`, `node_modules`).

## Notes
- UTMs added in renderers/selectors; require alt text for images.
- External sources must include publisher + link only (no full reproductions).

