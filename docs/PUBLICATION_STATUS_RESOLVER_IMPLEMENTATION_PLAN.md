# Publication Status Resolver – Implementation Plan

**Date:** 2025-12-18  
**Owner:** Assistant (implementation on request)  
**Scope:** Unify how creation / publication status is determined and displayed for all calendar‑driven content and outputs.

---

## 1. Objectives

- **Single source of truth:** Centralize all logic that answers “does an output exist for this scheduled item, and what is its status?”.
- **ID‑only matching:** Resolve relationships **only by stable IDs** (`theme_id`, `recipe_id`, `profile_category_id`, `item_id`, `post_id`, `queue_id`), **never falling back to title / text matching**.
- **Consistent UI:** Ensure every place that shows a status pill or compact action row (week view, Future items, Channels schedule, week themes, one‑click, etc.) consumes the **same normalized status model**.
- **No silent fallbacks:** Eliminate all ad‑hoc status fallbacks embedded inside endpoints. Any unresolved/mismatched data must surface as an error we can fix at source.
- **Keep codebase lean:** Implement the resolver and refactors **without file bloat**:
  - No file should grow beyond **~500 lines**; larger modules must be split.
  - New helpers go into focused modules, not piled into existing mega‑files.
- **Document everything:** For each change, update or create reference docs in `docs/` so the behavior and dependencies are clear.

---

## 2. Current State (Short Recap)

**Canonical data sources:**

- `post` table: all blog‑style content (themed, recipe, profile, weekly word/phrase/insult, etc.).
- `calendar_week_posts_v2` view: associates posts with `(year, week)` context for scheduling, via `calendar_week_items`.
- `posting_queue` table: product / syndication posts for social channels.
- JSON rotation files under `data/calendar/schedule/`: per‑category week→item rotation.

**Key components already in place:**

- `static/js/planning/unified-item-card.js` – single UI component rendering:
  - Status pill + compact action row.
  - Uses `post_id`, `post_exists`, `post_status` to decide label/icons.
- Week view (`tab=week-view`):
  - Backend: `planning_api_calendar_schedule.api_calendar_schedule`.
  - Enriches theme/recipes/profiles with `post_id` + `post_status` from DB.
- Channels schedule (`tab=publication-schedule`):
  - Backend: `publication_dashboard.api_dashboard_schedule`.
  - Enriches items with `post_id`, `post_exists`, `post_status` via several DB lookups.
- Future items (`tab=scheduling`):
  - Backend: `planning_api_calendar_scheduling_cache.scheduling_all`.
  - Returns JSON‑only rotation entries with **no post linkage or status**.
- `/posts` index:
  - Uses `post` and `calendar_week_posts_v2` (via `calendar_week_items`) to display schedule and status.

**Problems:**

- Multiple, slightly different chunks of “find the post for this item and decide status”.
- Future items tab has *no* post linkage but now uses a post‑status UI, so everything appears “Not created”.
- Some historical code attempted title‑based matching; the user’s rule is now **ID‑only**, no title fallbacks.

Reference docs describing the current system:

- `docs/CALENDAR_SYSTEM_AUDIT.md`
- `docs/CALENDAR_SCHEDULING_ENDPOINTS.md`
- `docs/UNIFIED_ITEM_CARD_AUDIT.md`
- `docs/CURRENT_STATE_REPORT.md`

These will be explicitly referenced/updated in later sections.

---

## 3. Target Model and Rules

### 3.1 Normalized status model

We define a small, explicit enum for **display status**:

- `draft`
- `published`
- `scheduled` (for future outputs, esp. product posts)
- `error`
- `deleted` (only when explicitly needed)
- `none` / `null` (meaning “no output exists yet”)

All UIs consume **only** this normalized status string; raw DB values are hidden inside the resolver.

### 3.2 Resolver output contracts

**Post status (blog‑style content):**

```python
class PostStatusInfo(TypedDict):
    exists: bool          # True if a post row exists
    status: str | None    # normalized status enum or None
    post_id: int | None
    raw_status: str | None   # original DB value, for logging/debug
```

**Product / queue status:**

```python
class QueueStatusInfo(TypedDict):
    exists: bool
    status: str | None        # mapped from posting_queue.status
    queue_id: int | None
    raw_status: str | None
```

Frontends (via unified item card) will only see `exists`, `status`, and the relevant ID (`post_id` or `queue_id`) re‑expressed as `post_id`/`post_status`/`post_exists` in JSON.

### 3.3 Matching rules (critical)

- **Primary key rule:** Matching must be done **by ID only**:
  - `theme` → `post.theme_id`
  - `recipe` → `post.recipe_id`
  - `profile_product` / `profile_surname` → `post.profile_category_id`
  - weekly word / phrase / insult → a dedicated ID column where available (to be confirmed; otherwise treat as “no automatic post linkage”).
- **No title fallbacks:**
  - No “ILIKE title” or equality on text columns is allowed in the resolver.
  - If IDs are missing or inconsistent, the resolver returns `exists=False, status=None`.
  - **Actionable outcome:** such mismatches are visible, and we must fix IDs or data at source (e.g., updating `post.theme_id`).
- **Contextual matching:**
-  - For themed blog posts, `(year, week)` context (via `calendar_week_posts_v2`) is the primary mapping from a calendar slot to its post.
  - For other categories, `(year, week)` may be used *only* to disambiguate between multiple candidate posts with the correct ID, but not as a replacement for an ID.
  - In ambiguous or inconsistent cases, resolver should:
    - Log a warning with enough detail.
    - Prefer the most recently created/updated row with the correct ID (if such logic is needed), or fail cleanly with `exists=False`.

These rules are **non‑negotiable constraints** to avoid hidden data issues.

---

## 4. New Module: `utils/publication_status_resolver.py`

### 4.1 Responsibilities

This module will be the **only** place that:

- Reads status information from:
  - `post`
  - `calendar_week_posts_v2`
  - `posting_queue`
- Maps raw DB states into the normalized display enum.
- Encapsulates all “how do we find the relevant post/output?” logic.

### 4.2 Public API

Planned functions (names subject to small tuning during implementation):

```python
def normalize_post_status(raw_status: str | None) -> str | None:
    ...

def normalize_queue_status(raw_status: str | None) -> str | None:
    ...

def resolve_post_for_calendar_item(
    category: str,
    item_id: int | None,
    *,
    year: int | None = None,
    week: int | None = None,
) -> PostStatusInfo:
    ...

def resolve_product_output(
    queue_id: int | None,
) -> QueueStatusInfo:
    ...
```

**Key points:**

- `category` is one of: `"theme"`, `"recipe"`, `"profile_product"`, `"profile_surname"`, `"weekly_word"`, `"weekly_phrase"`, `"weekly_insult"`.
- `item_id` is required for all categories except where the underlying schema doesn’t yet support an ID; in those cases the resolver returns `exists=False`.
- `(year, week)` are optional hints used **only** for narrowing down multiple valid rows with the same ID, not for matching by themselves.

### 4.3 Internal structure and file size constraints

To respect the **500‑line limit per file**, this module will be intentionally compact:

- `utils/publication_status_resolver.py`
  - ~150–250 lines:
    - Enum / constants for display statuses.
    - Small mapping functions `normalize_post_status` / `normalize_queue_status`.
    - A few short resolver functions that delegate to *category‑specific helpers*.
- If category‑specific resolver logic grows, we will split:
  - `utils/publication_status_resolver_post.py` (blog‑style content).
  - `utils/publication_status_resolver_queue.py` (posting_queue mapping).

We will **not** add this logic to existing large modules (like `publication_dashboard.py` or `planning_api_calendar_schedule.py`), to avoid bloat.

---

## 5. Backend Refactors by Area

### 5.1 Week view (`planning_api_calendar_schedule.api_calendar_schedule`)

**Current:**

- Already queries DB for theme/recipes/profiles and attaches `post_id` / `post_status` with some fallback logic (including historical title matching).

**Plan:**

1. Replace inline SQL and any title‑based fallbacks with calls to:
   - `resolve_post_for_calendar_item("theme", theme_id, year=year, week=week_number)`
   - `resolve_post_for_calendar_item("recipe", recipe_id, year=year, week=week_number)`
   - `resolve_post_for_calendar_item("profile_product", profile_category_id, ...)`
   - `resolve_post_for_calendar_item("profile_surname", profile_category_id, ...)`
2. Attach to the response:
   - `post_id` = `status_info["post_id"]`
   - `post_status` = `status_info["status"]`
3. Ensure no title matching remains; mismatched data should leave these fields `null`.

**Docs to update:**

- `docs/CALENDAR_SYSTEM_AUDIT.md` – section describing week‑view data enrichment.
- New section in this plan (later referenced) summarizing resolver usage.

### 5.2 Publication dashboard (`publication_dashboard.api_dashboard_schedule`)

**Current:**

- Has extensive, bespoke logic to:
  - Infer `post_id` for themes/recipes/profiles/weekly items via a mix of ID and title rules.
  - Normalize `post.status` via `get_display_status`.

**Plan:**

1. Strip out per‑category SQL that attempts matching.
2. For each calendar‑derived item:
   - Determine `category` and `item_id` from JSON/DB.
   - Call `resolve_post_for_calendar_item(category, item_id, year=year, week=week)`.
3. For product posts:
   - Call `resolve_product_output(queue_id)` and map to the same status enum.
4. Attach:
   - `post_id`, `post_exists`, `post_status` based on resolver output.

**Docs to update:**

- `docs/PUBLICATION_SCHEDULE_STATUS_REPORT.md` – replace the ad‑hoc status mapping description with a pointer to the resolver.

### 5.3 Future items / scheduling (`planning_api_calendar_scheduling_cache.scheduling_all`)

**Current:**

- Returns pure rotation entries constructed by `build_schedule_item`, with no knowledge of posts or outputs.

**Plan:**

1. After `week_items` are assembled for each `(year, week)` row:
   - For each `item`:
     - Determine `(category, item_id)` from `item["type"]` and category mapping.
     - Call `resolve_post_for_calendar_item(category, item_id, year=year, week=week)`.
2. Mutate each `item` to include:

```python
item["post_id"] = status_info["post_id"]
item["post_exists"] = status_info["exists"]
item["post_status"] = status_info["status"]
```

3. Keep `build_schedule_item` small; if enrichment logic gets large, move it into a helper function.
4. The JSON contract remains compatible but now carries status data, so `unified-item-card` can display accurate badges.

**Docs to update:**

- `docs/CALENDAR_SCHEDULING_ENDPOINTS.md` – describe the enriched fields in `/planning/api/calendar/scheduling/all`.
- `docs/CALENDAR_SYSTEM_AUDIT.md` – adjust the “NO DB queries” statement to reflect the new, deliberate status enrichment.

### 5.4 Week themes status (`planning_api_calendar_schedule.api_calendar_idea_status`)

**Current:**

- Uses `calendar_week_selection(_v2)` + `calendar_week_posts(_v2)` and its own logic to derive `post.id` / `status`.

**Plan:**

1. Simplify:
   - Validate that the requested `theme_id` matches the selection for `(year, week)` as it does now.
   - If mismatched, return “Week has different theme selected”.
2. If the theme matches for that week:
   - Call `resolve_post_for_calendar_item("theme", theme_id, year=year, week=week_number)`.
   - Return the normalized status structure.

**Docs to update:**

- Add a brief section to `docs/CALENDAR_SYSTEM_AUDIT.md` describing Week Themes → resolver dependency.

### 5.5 `/posts` index (only if needed)

The `/posts` blueprint already treats `post.status` as canonical; no resolver is strictly required.  
We will:

- Leave `/posts` using raw `post.status` for now (already consistent with resolver’s source).
- Optionally add a helper or note in docs clarifying that `/posts` is the “ground truth” view.

---

## 6. Frontend Integration

### 6.1 Unified item card usage assumptions

After backend refactors, **all callers** of `window.createUnifiedItemCard` must follow a simple rule:

- If they want a status pill, they must pass an item with:

```js
{
  post_id: number | null,
  post_exists: boolean | undefined,
  post_status: string | null
}
```

The resolver will guarantee these fields are consistent; frontends just forward them.

### 6.2 Views to verify

- Week view (`calendar-week-view.js`):
  - Already passes through `post_id` / `post_status` from `api_calendar_schedule`.
  - After backend change, only verify that the UI uses the enriched fields (no extra guessing).
- Scheduling (`scheduling_scripts.html`):
  - Already sends the raw item into `createUnifiedItemCard`.
  - After backend enrichment, this will automatically pick up accurate status with **no JS changes** beyond optional logging cleanups.
- Publication schedule (`publication_schedule_scripts.html`):
  - Already passes `post_id`, `post_exists`, `post_status` from `/publication/api/dashboard/schedule`.
  - After refactor, these fields will come from the resolver instead of bespoke logic.

No new frontend logic is planned beyond **removing any remaining ad‑hoc status or existence checks** once everything is verified.

---

## 7. File Size and Structure Constraints

To honour the “no file exceeds ~500 lines” rule and avoid future bloat:

- New resolver logic lives in its own module(s), not inside existing large blueprints.
- When modifying large files:
  - If an addition would push the file beyond ~500 lines, consider extracting:
    - Shared query utilities into `utils/` modules.
    - Sub‑routes into smaller, dedicated blueprints.
- We will track approximate sizes during implementation and note any file that remains over 500 lines with a TODO in docs for later refactor, rather than silently expanding it further.

This plan itself is the first step in systematically observing that constraint.

---

## 8. Documentation Plan

For each implementation step we will:

1. **Update existing docs**:
   - `docs/CALENDAR_SYSTEM_AUDIT.md` – to reflect the resolver and enriched scheduling data.
   - `docs/CALENDAR_SCHEDULING_ENDPOINTS.md` – to describe additional output fields.
   - `docs/UNIFIED_ITEM_CARD_AUDIT.md` – to note that status is now guaranteed to come from the resolver.
2. **Add new doc(s) as needed**:
   - A short `docs/PUBLICATION_STATUS_RESOLVER_REFERENCE.md` describing:
     - Public functions of `utils/publication_status_resolver.py`.
     - Status enums.
     - Category→ID mapping rules.
3. **Log changes in the changelog**:
   - Append an entry to `docs/CHANGELOG.md` summarizing:
     - Creation of the resolver.
     - Refactors to week view, scheduling, and publication schedule endpoints.

All docs must clearly state the **ID‑only matching rule** and the prohibition on title fallbacks.

---

## 9. Testing and Verification Strategy

### 9.1 Automated / programmatic checks

- **Unit‑style tests for the resolver (where feasible)**:
  - For each category, feed in known DB fixtures where the relationship is clean and confirm:
    - Correct `exists`, `status`, and `post_id`/`queue_id`.
  - Cases where IDs are missing must return `exists=False`.
- **Endpoint checks (manual or scripted curl):**
  - `/planning/api/calendar/schedule/2025/51` – ensure theme entry includes correct `post_id`/`post_status` for Triskelion.
  - `/planning/api/calendar/scheduling/all?...` – confirm its `data.weeks` rows carry the same `post_*` data as week view.
  - `/publication/api/dashboard/schedule?year=2025&week=51` – confirm enriched items match `/posts` and resolver.

### 9.2 UI verification (browser + curl)

- Week view / Future items / Channels schedule:
  - Confirm that **for every item where `/posts` shows a post**, the badge is not “Not created” and matches the normalized status.
  - Confirm that items with no post truly do show “Not created”.
- Edge cases:
  - Deleted posts: badges should reflect `deleted` or `none` as agreed in normalization.
  - Product posts: status mapping from `posting_queue.status` must be consistent.

All testing steps will be described in a short section at the end of `docs/PUBLICATION_STATUS_RESOLVER_REFERENCE.md` when that doc is created.

---

## 10. Phased Implementation Plan

1. **Create resolver module** (`utils/publication_status_resolver.py`):
   - Implement normalization functions and basic ID‑based lookups for `post` and `posting_queue`.
   - Keep under ~250 lines.
   - Add the new reference doc skeleton in `docs/PUBLICATION_STATUS_RESOLVER_REFERENCE.md`.
2. **Refactor week view backend**:
   - Swap inline logic in `api_calendar_schedule` to use the resolver.
   - Verify week view status for known weeks (e.g., Triskelion).
3. **Refactor publication dashboard backend**:
   - Replace per‑category status code in `api_dashboard_schedule` with resolver calls.
   - Confirm channels schedule status vs `/posts`.
4. **Enrich scheduling backend**:
   - Update `scheduling_all` to call the resolver for each item.
   - Confirm Future items tab reflects real status for Triskelion and other items.
5. **Align week themes status endpoint**:
   - Replace local post lookup in `api_calendar_idea_status` with resolver call.
6. **Doc updates & cleanup**:
   - Update/extend the docs listed in §8.
   - Remove or clearly mark any remaining status logic that doesn’t go through the resolver.

Only after this planning document is in place (this step) will any code edits begin, and each phase will be kept small enough to avoid breaching file size constraints.


