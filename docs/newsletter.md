# Newsletter Module

This document outlines the newsletter system: schema, flows, UI, adapters, and file-size guardrails.

## Schema (Postgres)
- `newsletter_issue(id, target_week, status, subject, preheader, last_sent_at, created_at, updated_at)`
- `newsletter_block(id, issue_id, type, enabled, position, payload_json, pinned_ids, created_at, updated_at)`
- `newsletter_evergreen(id, topic, text, length, season, region_tags, last_used_at, created_at, updated_at)`
- `newsletter_category_feature(id, title, body_html, topic, approved, last_used_at, created_at, updated_at)`
- `newsletter_snapshot_source(id, name, base_url, type, enabled, api_key_ref, created_at, updated_at)`
- `newsletter_rotation(id, topic, cooldown_weeks, weight, created_at, updated_at)`
- `newsletter_send_log(id, issue_id, provider, provider_id, sent_at, checksum, created_at)`

Migration: `migrations/20251030_create_newsletter_tables.sql`.

## High-level flow
1. Auto-draft (weekly) builds an issue with blocks.
2. Editor adjusts via `/newsletter` UI: toggle/pin/override.
3. QA checks: links/images/alt.
4. Preview HTML, approve, and send via adapter.

## UI & Endpoints
- `/newsletter` dashboard (list + new draft + autodraft)
- `/newsletter/issue/:id` issue page (blocks list, actions)
- `/newsletter/issue/:id/preview` HTML preview
- `/newsletter/issue/:id/qa` checks
- POST `/newsletter/issue/:id/approve`
- POST `/newsletter/issue/:id/send` (adapter=preview default)
- POST `/newsletter/autodraft` (weekly autodraft trigger)

## Rendering
- Templates under `templates/newsletter/partials/` per block.
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

