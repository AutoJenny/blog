# Unified Output Refactor Plan

**Date:** 2025-12-18  
**Goal:** Translate the unified data model into a concrete, staged refactor of the codebase so that all calendar views and automation flows use a single mapping between planned Content Items and concrete Outputs, with one status model.

This plan is **documentation only** – no behaviour is changed by this file.

---

## 1. Guiding Principles

- **Single mapping layer:**  
  All “which output belongs to this week/slot?” questions must be answered by:
  - `calendar_week_posts` (for blog posts), and
  - an explicit view/helper over `posting_queue` (for social outputs),
  not by scattered heuristics.

- **ID‑based, week‑aware lookups:**  
  Once mapping rows exist, lookups are by `(year, week)` (and optionally `slot_type`/`day`), never by guessing via titles or `idea_seed`.

- **Outputs own status:**  
  Status comes from `post.status` and `posting_queue.status`, normalized to the unified enum; calendar code does not invent new status semantics.

- **Thin helpers, lean files:**  
  Introduce small helper modules rather than bloating existing blueprints; keep each file under ~500 lines by splitting where necessary.

- **Delete old heuristics:**  
  Once a new path is in place and tested, remove the old resolver/heuristic code instead of leaving it dormant.

---

## 2. Phase 3.A – Canonical Week→Blog Mapping

**Objective:** Make `calendar_week_posts` the single source of truth for “which blog post belongs to which week”, then use it consistently.

### 2.A.1 Introduce mapping helper module

New module (names tentative; actual path chosen to keep files small):

- `utils/week_blog_mapping.py`

Functions:

```python
def assign_blog_post_to_week(year: int, week: int, post_id: int, *, cursor=None) -> None:
    """Upsert (year, week, post_id) into calendar_week_posts."""

def get_blog_post_for_week(year: int, week: int, *, cursor=None) -> Optional[int]:
    """Return post_id for the primary blog output for that week, or None."""
```

Notes:

- Implementation uses `calendar_week_posts` directly:
  - Insert with `ON CONFLICT (year, week_number, post_id) DO NOTHING` (or update timestamps).
  - For reads, pick the most recently `created_at`/`updated_at` record when multiple rows exist.
- `cursor` is optional, so callers can share DB transactions where needed.

### 2.A.2 Wire creation/assignment flows to write mapping rows

Affected modules:

- `blueprints/planning_api_posts.py::confirm_calendar_idea`
- `blueprints/recipes.py` (recipe creation)
- `blueprints/planning_api_profiles.py` (profile creation)
- `blueprints/automation_core.py::create_post_from_item` (one‑click & auto‑create)

Tasks:

1. **Week Themes (themed posts):**
   - After `confirm_calendar_idea()` determines `post_id` and has `(year, week_number)`:
     - Call `assign_blog_post_to_week(year, week_number, post_id, cursor=cursor)`.
   - Remove any duplicate week‑mapping logic from this function that writes into other week tables.

2. **Recipes:**
   - `recipes.py` already writes to `calendar_week_posts` using inline SQL.
   - Replace this inline SQL with a call to `assign_blog_post_to_week`, so:
     - All recipe creations use the same helper.
     - Future changes to the mapping behaviour are centralized.

3. **Profiles:**
   - `planning_api_profiles.py` writes to `calendar_week_posts` when a profile is created with week/year.
   - Switch to `assign_blog_post_to_week` for the same reasons as recipes.

4. **One‑Click / auto‑create (`automation_core.create_post_from_item`):**
   - When `category` is a blog content type (theme, recipe, profile SKU) and `(year, week)` are provided:
     - After the post is created (or an existing post is reused), call `assign_blog_post_to_week(year, week, post_id, cursor=cursor)`.
   - Remove any reliance on later heuristics (e.g. trying to discover week context via calendar_week_items_deprecated).

### 2.A.3 Centralize week-based resolution

Module: `utils/week_post_resolver.py`

Tasks:

- Refactor `resolve_post_for_week(year, week, cursor=None)` to:
  - Use `get_blog_post_for_week` exclusively (no more `calendar_schedule` or title/idea_seed fallbacks).
  - Keep the public signature intact, so existing callers (e.g., `planning_calendar.planning_calendar_ideas`) remain valid.

### 2.A.4 Consumers: Week View and Friends

Update consumers to rely on mapping instead of heuristics:

- **Week view backend (`planning_api_calendar_schedule.api_calendar_schedule`):**
  - For themed posts:
    - Use `calendar_week_selection` to get `selected_theme_id`.
    - Use `get_blog_post_for_week(year, week)` to find blog post id (if any) for that week.
    - Attach `post_id` and normalized `status` by joining to `post`.
  - For recipes/profiles:
    - Continue to use existing category‑specific logic for details (titles, descriptions), but treat `calendar_week_posts` as the authoritative week→post mapping.

- **Planning UIs that use `resolve_post_for_week` (e.g., taxonomy/ideas views):**
  - Benefit automatically from the centralized mapping once `week_post_resolver` is updated.

After this phase:

- If a blog post exists for a given week and has been assigned via any creation process, **all week‑based consumers will see it the same way**, driven by `calendar_week_posts`.

---

## 3. Phase 3.B – Future Items (Scheduling Overview)

**Objective:** Make the Future items view (scheduling tab) display the correct blog status by reading from the same mapping layer.

Modules:

- `blueprints/planning_api_calendar_scheduling_cache.py::scheduling_all`
- `templates/planning/calendar/includes/scheduling_scripts.html`

Tasks:

1. **Backend enrichment:**
   - While building each week row:
     - The rotation logic already knows `(year, week)` and that the `theme`/`recipe`/`profile` content is planned.
     - Use `get_blog_post_for_week(year, week)` to:
       - Attach `post_id` (or `null`) and normalized `post_status` to the relevant row(s) representing the blog slot (`theme_selection` or a dedicated “blog” cell).
   - Do **not** try to infer posts by title or by Content Item ID here; week mapping is the source of truth.

2. **Frontend:**
   - Ensure the unified item card receives `post_id` and `post_status` for the blog slot.
   - Remove any JS that tries to “recompute” existence from scratch; it should trust the backend fields.

After this phase, the Future items tab should show the same blog status for each week as the week view and `/posts`, driven solely by `calendar_week_posts`.

---

## 4. Phase 3.C – Publication Dashboard (Blog Channel)

**Objective:** Make the Channels schedule/blog publication dashboard use the same week→blog mapping instead of its own heuristics.

Module:

- `blueprints/publication_dashboard.py::api_dashboard_schedule`

Tasks:

1. **Replace theme/recipe/profile status logic:**
   - For the **blog** channel, stop using:
     - `calendar_week_posts_v2` joins to infer posts.
     - Title‑based lookups in `post`.
   - Instead:
     - For each `(year, week)` the dashboard considers:
       - Use `get_blog_post_for_week(year, week)` to find any assigned blog post id.
       - Join to `post` to get status and title.

2. **Preserve channel assignment logic:**
   - Keep using `post_type_channel_config` and rotation JSON to decide *which* weeks/days produce outputs for each channel.
   - Blog status is simply read from the same mapping + `post` as all other views.

Result:

- The blog row in the publication dashboard shows status consistent with:
  - `/posts`
  - Week view
  - Future items

---

## 5. Phase 3.D – Social Outputs Integration (High-Level)

**Objective:** Bring social outputs (posting_queue) into the same conceptual framework for status and week context, without overcomplicating the schema.

Modules (planned):

- `utils/social_output_view.py` (new helper module)
- `blueprints/publication_dashboard.py` (social parts)
- Potentially week view/scheduling syndication rows

Tasks:

1. **Helper view over posting_queue:**

   A small helper or SQL view that exposes:

   ```text
   platform, content_type, scheduled_date, scheduled_time,
   product_id / section_id,
   status,
   year, week, day  # derived from scheduled_date
   ```

   Normalized to:

   ```text
   channel, content_format, status
   ```

2. **Publication dashboard:**
   - Replace ad‑hoc SQL that reads `posting_queue` with calls to this helper.
   - Use `normalize_queue_status` for status mapping.

3. **Optional calendar views:**
   - Week view / Future items syndication rows can read from the same helper to show social outputs alongside blog status.

This phase ensures social posts appear in the same unified “Output + Status” picture without altering the blog mapping layer.

---

## 6. Phase 3.E – Deleting Redundant Code

Once the mapping‑based flows are in place and tested, remove or hard‑disable:

- **Heuristic resolvers:**
  - Title/idea_seed matching in `automation_core.create_post_from_item`.
  - Theme and weekly content guesses based on `calendar_week_posts_v2` in `publication_dashboard.api_dashboard_schedule`.
  - Any remaining fallbacks in `planning_api_calendar_schedule` that attempt to discover posts by title.

- **Superseded mapping logic:**
  - Uses of `calendar_week_items_deprecated` as a quasi‑mapping for blog posts where `calendar_week_posts` should be the source of truth.
  - Any leftover references to legacy `calendar_schedule` in week‑resolution code.

- **Experimental resolver modules:**
  - If status and mapping are fully driven by `calendar_week_posts` + `post` (and `posting_queue` for social), simplify or remove `utils/publication_status_resolver.py`, keeping only what is still structurally useful.

All removals should be accompanied by:

- Brief notes in `docs/UNIFIED_OUTPUT_IMPLEMENTATION_LOG.md`.
- Updates to existing docs that previously described the removed behaviours.

---

## 7. Phase 3.F – Documentation & Verification

For each of the above phases:

- **Docs:**
  - Update:
    - `docs/WEEK_PERSISTENCE_V2_SYSTEM.md` to clarify how `calendar_week_posts` is now used.
    - `docs/CALENDAR_SYSTEM_AUDIT.md` to point at the unified mapping and status model.
    - Any status‑related docs (e.g. `UNIFIED_ITEM_CARD_AUDIT.md`) to reflect the new source of truth.

- **Verification:**
  - For a representative set of weeks (including problematic ones like W51/Triskelion):
    - Use `curl` to inspect:
      - `/planning/api/calendar/schedule/{year}/{week}`
      - `/planning/api/calendar/scheduling/all?...`
      - `/publication/api/dashboard/schedule?year={year}&week={week}`
      - `/planning/api/posts/{post_id}`
    - Confirm:
      - The same blog `post_id` appears in `calendar_week_posts` and is surfaced consistently across endpoints.
      - Status labels in UI match `post.status` (normalized) and `posting_queue.status` for social outputs.

This refactor plan will guide the subsequent implementation phase, keeping changes scoped, traceable and aligned with the unified Output framework. Actual code changes will follow this plan step by step, with progress documented in the implementation log and in chat.

---

## 8. Phase 4 – Social Outputs & Weekly Items Integration

**Objective:** Bring social posts (products, weekly word/phrase/insult) into the same unified Output framework as blog posts, with explicit Content Item linkage and consistent status resolution.

### 8.1 Schema: Add `idea_id` to `posting_queue`

**Migration:** `migrations/20251218_add_idea_id_to_posting_queue.sql`

- Adds nullable `idea_id INTEGER` column to `posting_queue`.
- Adds index `idx_posting_queue_idea_id` for lookups.
- **Backwards compatible:** existing product posts unaffected.

**Purpose:** Enable ID-only linkage between weekly Content Items (`calendar_ideas.id`) and social Outputs in `posting_queue`.

### 8.2 Social Output View Helper

**New module:** `utils/social_output_view.py` (~250 lines)

**Functions:**
- `get_social_outputs_for_week(year, week, ...)` – returns all social Outputs for a week slot.
- `get_social_outputs_for_content_item(content_type, content_item_id, ...)` – returns social Outputs for a specific Content Item.

**Output structure:**
- Normalized `channel`, `content_format`, `status` (via `normalize_queue_status`).
- Slot context: `(year, week, day)` derived from `scheduled_date`.
- Content Item linkage: `(content_type, content_item_id)` mapped from `product_id` or `idea_id`.

**Rules:**
- Products: `content_type="product"`, `content_item_id=product_id`.
- Weekly items: `content_type` from `posting_queue.content_type` (weekly_word/phrase/insult), `content_item_id=idea_id`.

### 8.3 Populate `idea_id` in Creation Flows

**Where to populate:**

When any endpoint or automation creates a `posting_queue` row for weekly word/phrase/insult Content Items:

1. Determine the `calendar_ideas.id` for the weekly Content Item (from rotation JSON or explicit selection).
2. Set `idea_id = calendar_ideas.id` in the INSERT statement.
3. Keep `content_type` set to `"weekly_word"`, `"weekly_phrase"`, or `"weekly_insult"` to distinguish subtypes.

**Note:** This is a **forward-looking change**. Existing weekly social posts in `posting_queue` will have `idea_id=NULL` until they are recreated or backfilled. The `SocialOutputView` handles both cases gracefully.

### 8.4 Integrate into Publication Dashboard

**File:** `blueprints/publication_dashboard.py::api_dashboard_schedule`

**Changes:**
- Replace ad-hoc `posting_queue` queries with `get_social_outputs_for_week()`.
- Use normalized status from `SocialOutputView` (already normalized via `normalize_queue_status`).
- Fetch product/idea titles separately for display, but rely on `content_item_id` for linkage.

**Result:** All social Outputs (products + weekly items) appear in the publication dashboard with consistent status and explicit Content Item linkage.

### 8.5 Future: Optional Integration into Scheduling/Future Items

**Optional enhancement:** The Future Items tab (`planning_api_calendar_scheduling_cache.scheduling_all`) could:

- For each weekly Content Item + Slot from rotation JSON:
  - Query `get_social_outputs_for_content_item("weekly_word", idea_id, year=year, week=week)`.
  - Attach social status metadata to the weekly item entries.

This would show "scheduled" or "published" badges for weekly social posts alongside the planned Content Item, without changing any creation logic.

### 8.6 Documentation Updates

**New docs:**
- `docs/SOCIAL_OUTPUT_VIEW.md` – design and API reference for the social Output abstraction.

**Updated docs:**
- `docs/UNIFIED_OUTPUT_DATA_MODEL.md` – notes that `posting_queue` links to products via `product_id` and weekly items via `idea_id`.
- `docs/UNIFIED_OUTPUT_REFACTOR_PLAN.md` – this section.

**Implementation log:**
- Each change documented in `docs/UNIFIED_OUTPUT_IMPLEMENTATION_LOG.md` with date, file, and what was changed.

---

**Status:** Phase 4.A (schema + helper) and Phase 4.B (dashboard integration) are complete. Phase 4.C (populate `idea_id` in creation flows) is pending identification of all weekly social post creation endpoints. 


