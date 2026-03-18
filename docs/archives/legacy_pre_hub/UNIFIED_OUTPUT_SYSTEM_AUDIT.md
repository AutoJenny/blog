# Unified Output System Audit

**Date:** 2025-12-18  
**Purpose:** Map how *planned* content and *actual* outputs are currently wired across the system, and identify the main failure points that a unified framework must address.

---

## 1. Key Data Structures (Current Reality)

### 1.1 Planning / Rotation Layer

- **`calendar_themes`** – Master list of themes (Content Items); used in:
  - Rotation JSON for `theme` (`data/calendar/schedule/theme/{year}.json`).
  - Theme selectors on planning UIs.
- **`calendar_recipes`** – Master list of recipes (Content Items).
- **`calendar_profile_sequence`** – Sequence lists for profile products/surnames:
  - For `profile_product` and `profile_surname` JSON files, `id` is `calendar_profile_sequence.post_id`.
- **`calendar_ideas`** – Weekly word/phrase/insult concepts (Content Items).
- **Rotation JSON files** (`docs/CALENDAR_SCHEDULING_JSON_FORMAT.md`):
  - One file per category/year, e.g. `theme`, `recipe`, `profile_product`, `weekly_word`, etc.
  - For each week:
    - `id` (category‑specific ID as above).
    - `position` (cyclic list slot).
    - Optional `title`.

**Observation:** Rotation JSON always knows *which content item* is planned for each week, but not which post/output (if any) was created.

### 1.2 Week Persistence V2 (Theme Selection + Post Assignments)

Per `docs/WEEK_PERSISTENCE_V2_SYSTEM.md` and `calendar_system_technical_documentation.md`:

- **`calendar_week_selection`**:
  - `(year, week_number)` → `selected_theme_id` (FK to `calendar_themes.id`).
  - One row per week; Source of truth for the *selected theme*.
- **`calendar_week_posts`**:
  - `(year, week_number, post_id)` rows.
  - Multiple posts per week allowed.
  - Intended to be the **canonical mapping between weeks and posts** (Outputs), regardless of content type.
- **Views**:
  - `calendar_week_selection_v2` – derived from `calendar_week_items`.
  - `calendar_week_posts_v2` – compatibility view showing only `item_type in ('recipe','profile')` from `calendar_week_items`.

**Reality check:**

- The Week Persistence V2 design is **only partially implemented**:
  - `calendar_week_posts` is used in some flows (recipes/profiles).
  - The new `calendar_week_items(_deprecated)` path is used for some themed posts but **only indirectly** via a view, and doesn’t expose a simple `(year, week) → blog post id` mapping for the main weekly article.

### 1.3 Actual Outputs

- **`post`**:
  - Primary store for blog‑style outputs (themed, recipe, profile, weekly word/phrase/insult, etc.).
  - Fields of interest:
    - `id`, `title`, `status`, `slug`, `created_at`, `updated_at`.
    - `recipe_id`, `recipe_week_number`.
    - `profile_type`, `profile_product_id`, `profile_category_id`.
    - `content_type_id`, `format_id`, `theme_id` (FK into taxonomy, *not* calendar themes).
- **`post_development`**:
  - Extended planning data for posts (expanded idea, sections, idea_seed, etc.).
  - Historically used for matching by `idea_seed` to link posts back to themes/ideas.
- **`posting_queue`**:
  - Outputs for social platforms (Facebook, Instagram, etc.).
  - Key fields: `id`, `platform`, `channel_type`, `content_type`, `scheduled_date`, `scheduled_time`, `status`, `product_id` or `section_id`.

**Observation:** Blog posts and social posts are stored in **different systems** (`post` vs `posting_queue`), with no unified Output abstraction yet.

### 1.4 Mapping / Resolver Utilities

- **`utils/week_post_resolver.py`**:
  - Given `(year, week)`, returns `post_id` by:
    - Preferring `calendar_week_posts` if present.
    - Falling back to legacy `calendar_schedule` in older docs.
  - Used in:
    - `planning_calendar.planning_calendar_ideas` to resolve the “current week” post.
- **`utils/calendar_resolver.py`**:
  - Resolves Content Items for categories (theme/recipe/profile/weekly…) using base lists and overrides.
  - Used for **rotation** (what item belongs in a given week), not for outputs.
- **`utils/publication_status_resolver.py`** (newer, partial):
  - Attempts to resolve post IDs by matching category + ID onto `post` columns.
  - Currently limited and constrained; does **not** address week mapping or all failure cases.

---

## 2. Major Flows and Their Linkages

### 2.1 Week Themes → Post Creation (`confirm_calendar_idea`)

Files:

- `blueprints/planning_calendar.py::planning_calendar_ideas_week`
- `blueprints/planning_api_posts.py::confirm_calendar_idea`
- `docs/WEEK_PERSISTENCE_V2_SYSTEM.md`

Flow:

1. User selects a theme for a week:
   - `POST /planning/api/calendar/select-theme` → writes to `calendar_week_selection` (or `_v2`).
2. User confirms a theme/topic to create a post:
   - `POST /planning/api/calendar/confirm-idea` (`confirm_calendar_idea`):
     - Reuses an existing post by `title`/`idea_seed` if `force_new` is false (status‑filtered).
     - Or creates a new `post` row (draft).
3. Week assignment:
   - According to docs, should:
     - Insert into `calendar_week_posts (year, week_number, post_id, ...)`.
   - In practice:
     - For themed posts:
       - Writes to `calendar_week_items` with `item_type='profile'` for the post, and a separate `item_type='theme'` row for the selected theme.
       - Does **not** consistently create a straightforward `(year, week, post_id)` row in `calendar_week_posts` for the main blog post.
4. Status tracking:
   - `post.status` is updated independently by other parts of the pipeline.

**Failure points:**

- The Week Themes flow does **not** guarantee that “W51’s main blog article” is recorded in `calendar_week_posts` in a way that the rest of the system uniformly consumes.
- Multiple representations of the same concept (theme selection in `calendar_week_selection`, posts in `calendar_week_items`) are not consistently joined back to a single “main blog post for this week” mapping.

### 2.2 One‑Click / Auto‑Create (`automation_core.create_post_from_item`)

Files:

- `blueprints/automation_core.py::create_post_from_item`
- `static/js/launchpad/one-click-blog-controller.js`
- Channel assignment docs (`config/channel_content_formats.py`, `docs/CHANNEL_CONTENT_FORMAT_IMPLEMENTATION_SUMMARY.md`)

Flow:

1. User triggers auto‑create from a calendar slot or from one‑click UI.
2. Backend:
   - Reads the Content Item (`calendar_themes`, `calendar_recipes`, `calendar_ideas`, etc.).
   - Determines `post_type`, `title`, and channel/content_format.
   - Checks for existing posts using a mix of:
     - `recipe_id` checks.
     - `calendar_week_posts_v2` + title/idea_seed heuristics for themes and weekly content.
   - If no existing post, creates a new `post` row and a `post_development` row.
   - Links recipes via `post.recipe_id`.
   - Links the new post to `calendar_week_items_deprecated` for week context (for some post types), but:
     - The mapping is via `item_type` + `item_id = post_id` rather than a simple `calendar_week_posts` entry that other code expects.
3. Displays:
   - Week view and dashboards then try to “discover” that post by week + title/idea_seed, not by a single canonical mapping.

**Failure points:**

- Overlaps with Week Themes in intent (create a post from a theme/slot), but writes to a different week‑persistence structure (`calendar_week_items_deprecated` vs `calendar_week_posts`).
- Uses **title/idea_seed based matching** in several places (despite your no‑fallback requirement), making behaviour fragile and hard to reason about.

### 2.3 Scheduling / Future Items (Rotation Overview)

Files:

- `blueprints/planning_api_calendar_scheduling_cache.py::scheduling_all`
- `templates/planning/calendar/includes/scheduling_scripts.html`
- `docs/CALENDAR_SCHEDULING_JSON_FORMAT.md`

Flow:

1. `GET /planning/api/calendar/scheduling/all`:
   - Loads rotation JSON for all categories/years.
   - For each `(year, week)`:
     - Builds a `schedule` array of items with type + ID + position (and sometimes title/description).
   - Does **not** originally include any post/output linkage.
2. Frontend renders each week row as a pure rotation view.

**Failure points:**

- The Future Items tab, by design, originally knew **only what is planned**, not what outputs exist.
- Later attempts (including my own) tried to retrofit post status into this path without first establishing a canonical mapping, leading to partial and inconsistent enrichment.

### 2.4 Publication Dashboard / Channels Schedule

Files:

- `blueprints/publication_dashboard.py::api_dashboard_schedule`
- `templates/planning/calendar/includes/publication_schedule_scripts.html`
- `posting_queue` docs (`blog-launchpad/docs/database/posting_queue_schema.md`)

Flow:

1. For the blog channel:
   - Uses rotation JSON + various DB lookups to infer `post_id` and `post_status` for each slot.
   - Historically:
     - Looked at `calendar_week_posts_v2`, `post.recipe_id`, `post.profile_category_id`, and sometimes `post.title`.
2. For product posts:
   - Reads from `posting_queue` and maps to Facebook channel days/times.

**Failure points:**

- Blog channel scheduling logic reimplements its own “find the post for this slot” process instead of reading a shared mapping.
- Product posts live in a **completely separate scheduling universe**, with different status semantics and no unified Output model.

---

## 3. Status Computation and Display

### 3.1 Where Status Comes From Today

- `/posts`:
  - Uses `post.status` directly, normalized via `get_display_status()` (now backed by `normalize_post_status`).
- Week view / Future items / Channels schedule:
  - Historically:
    - Mixed inferences from `calendar_week_posts_v2`, `post.title`, `post_development.idea_seed`, or no status at all.
  - After recent changes:
    - Some paths now consult `post` directly, but do so with *different* heuristics and incomplete mapping for themes.
- One‑click:
  - Computes its own notion of “post exists or not” based on whether `post_id` is known in the one‑click session.

### 3.2 Unified Status Intent vs Reality

Intent (from docs and your requirements):

- A week slot (e.g. W51 theme) should have a clear state:
  - `unstarted` – no post/output exists yet.
  - `draft` / `scheduled` / `published` – taken from the actual Output record (`post` or `posting_queue`).

Reality:

- For many slots (including your W51 Triskelion theme):
  - A post **exists** and is visible on `/posts`.
  - The week persistence/mapping layer does **not** record “this post is the main blog output for W51 theme”.
  - Downstream displays either:
    - Fail to find the post, or
    - Guess incorrectly based on titles or week context.

---

## 4. Primary Failure Points (High Level)

1. **No single canonical mapping layer from Content Items to Outputs.**
   - Week Persistence V2 (`calendar_week_posts`) is only partially used.
   - Themed posts are sometimes linked via `calendar_week_items` instead, and not exposed in a simple `(year, week, post_id)` form.
2. **Creation flows do not reliably write mapping rows.**
   - `confirm_calendar_idea()` and `create_post_from_item()` both create posts, but:
     - Recipes/profiles are mapped more cleanly (via `recipe_id` and calendar_week_posts).
     - Themed posts and weekly content rely on softer signals (idea_seed, title) or write into different tables than the resolvers expect.
3. **Status is recomputed in multiple places instead of read from one model.**
   - `/posts`, week view, Future items, and publication dashboard each have their own status logic.
   - This makes it easy for one view to show “published” while another shows “Not created”.
4. **Blog vs social outputs are conceptually split.**
   - Blog uses `post` + Week Persistence V2; social uses `posting_queue` + daily schedules.
   - There is no shared “Output” abstraction with a unified status enum.

---

## 5. Implications for the Unified Framework

Based on this audit, any robust solution must:

1. **Introduce or adopt a single mapping layer** that:
   - Connects each planned Content Item (theme/recipe/profile/weekly) and week/slot to its concrete Outputs (blog post IDs, queue IDs).
   - Is written to at the time of creation/assignment, not guessed later.
2. **Make Week Persistence V2 (or its successor) the only source of “which blog post belongs to which week/slot”.**
   - All views and resolvers must stop trying to infer this independently.
3. **Make status a property of Outputs, not of views.**
   - Unified enum, taken from `post.status` and `posting_queue.status`, exposed through one narrow API.
4. **Have planning UIs (week view, scheduling, dashboard, one‑click) act as read‑only consumers of that mapping + status, plus actions to change it, but never re‑implement the logic.**

These are the constraints and failure points the next phase (unified data model and refactor plan) will address.


