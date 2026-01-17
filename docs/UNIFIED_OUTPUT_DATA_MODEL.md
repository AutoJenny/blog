# Unified Output Data Model

**Date:** 2025-12-18  
**Goal:** Define a single, consistent model that connects planned content (themes, recipes, profiles, weekly items, products) to their concrete Outputs (blog articles, social posts, etc.) with a unified status lifecycle, so that “unstarted” is just another status and all calendar views show the same truth.

---

## 1. Core Concepts

### 1.1 Content Item

A **Content Item** is a planning‑level object that can produce one or more Outputs. Examples:

- Calendar theme: `calendar_themes.id`
- Calendar recipe: `calendar_recipes.id`
- Profile product/surname: `calendar_profile_sequence.post_id` (links to `post.id`)
- Weekly word/phrase/insult: `calendar_ideas.id` with classification
- Product: `clan_products.id`

We model Content Items as:

```text
ContentItem {
  content_type: enum( "theme", "recipe", "profile_product", "profile_surname",
                      "weekly_word", "weekly_phrase", "weekly_insult", "product", ... )
  content_item_id: int       # primary key in the category source table
}
```

The rotation JSON is essentially a precomputed mapping:

```text
(content_type, content_item_id, year, week)  # plus position
```

### 1.2 Output

An **Output** is a concrete deliverable on a specific channel in a specific format. Examples:

- Blog:
  - Article page for W51 (“What Makes the Triskelion Unique?...”) → `post.id = 705`.
- Facebook:
  - Product post for clan product 123 at 2025‑01‑27 17:00 → `posting_queue.id = 9001`.
- Twitter:
  - Tweet for a Weekly Word.

We conceptually model Outputs as:

```text
Output {
  output_kind: enum("blog_post", "social_queue")  # physical table family
  output_id: int                                  # either post.id or posting_queue.id
  channel: enum("blog", "facebook", "instagram", "twitter", "newsletter", ...)
  content_format: string   # e.g. "article", "product_post", "word_of_day"
}
```

Physical storage:

- `post` + related tables (sections, development, etc.) for `output_kind = "blog_post"`.
- `posting_queue` for `output_kind = "social_queue"`, with:
  - `product_id` linking to product Content Items (`clan_products.id`).
  - `idea_id` (NEW) linking to weekly Content Items (`calendar_ideas.id`) for weekly word/phrase/insult posts.

### 1.3 Output Status

Every Output has a lifecycle **status** from a unified enum:

- `unstarted` – no Output record exists yet for the slot.
- `draft` – exists but not scheduled / not ready.
- `scheduled` – has a scheduled date/time on its channel.
- `published` – delivered to the channel.
- `error` – posting/scheduling failed.
- `cancelled` / `deleted` – intentionally removed/stopped.

Status is *not* a property of the calendar view; it is read from the Output’s backing record:

- For blog posts (`post`):
  - `post.status` → normalized to the enum via `normalize_post_status`.
- For social posts (`posting_queue`):
  - `posting_queue.status` → normalized via `normalize_queue_status`.

When an Output does not (yet) exist, we treat status as **`unstarted`**.

---

## 2. Week/Slot Context

Most planning is expressed in terms of **weeks** (ISO year/week pair), sometimes with a further subdivision into “slots” (e.g. primary vs secondary blog posts, or weekday positions).

We model a **Slot** as:

```text
Slot {
  year: int
  week: int
  # optional refining dimensions:
  slot_type: enum("main_blog", "supporting_blog", "product_highlight", "weekly_word", ...)
  day: int | null          # 1–7 for day-specific outputs, null for week-level
}
```

The simplest “main blog article for week 51” is:

```text
(year=2025, week=51, slot_type="main_blog", day=null)
```

---

## 3. Canonical Mapping Layer

The heart of the new model is a **single mapping layer** that answers:

> For a given Content Item in a given Slot, which Outputs exist (by channel/format), and what are their statuses?

### 3.1 Logical Mapping Schema

Conceptually, we want a table or view like:

```text
ContentOutputAssignment {
  # Planning dimension
  content_type: enum(...)
  content_item_id: int
  year: int
  week: int
  slot_type: string          # e.g. "main_blog", "weekly_word", ...
  day: int | null            # for date-sensitive outputs

  # Output dimension
  output_kind: enum("blog_post", "social_queue")
  output_id: int             # FK into post or posting_queue
  channel: string            # "blog", "facebook", ...
  content_format: string     # "article", "product_post", "word_of_day", ...

  # Derived / denormalized for fast access
  status: enum("unstarted","draft","scheduled","published","error","cancelled")
  created_at: timestamp
  updated_at: timestamp
}
```

Notes:

- For **blog outputs**, `output_kind = 'blog_post'`, `output_id = post.id`, `channel = 'blog'`.
- For **social outputs**, `output_kind = 'social_queue'`, `output_id = posting_queue.id`, `channel` and `content_format` taken from `posting_queue`.
- There may be multiple Outputs per `(content_item_id, year, week)` (e.g. blog + Facebook + Instagram).

### 3.2 Relationship to Existing Tables

We want to **reuse** as much of the existing schema as possible, by layering on top rather than rewriting the world.

#### 3.2.1 Week Persistence V2 – Blog Outputs

Current V2 design:

- `calendar_week_selection` – `(year, week) → selected_theme_id` (Content Item).
- `calendar_week_posts` – `(year, week, post_id)` (Outputs), but:
  - It does **not** distinguish between multiple slots or content types.
  - It is not consistently written for themed posts today.

Proposed use:

- Treat `calendar_week_posts` as the **canonical mapping for blog outputs**:
  - Each row is an Output where:

    ```text
    output_kind = "blog_post"
    output_id   = post_id
    channel     = "blog"
    content_format = "article" (or derived from post_type/taxonomy)
    year, week  as-is
    ```

- Slot semantics:
  - For now, the “main blog article” per week is either:
    - The most recently created/updated `calendar_week_posts` row for that week, or
    - A row with a specific `slot_type` stored in `metadata` (if we want to support multiple blog slots later).
  - This can be exposed via a small view:

    ```sql
    CREATE VIEW calendar_week_blog_main AS
    SELECT
      year,
      week_number,
      post_id
    FROM calendar_week_posts
    -- e.g. ORDER BY created_at DESC and pick first in code
    ;
    ```

#### 3.2.2 Posting Queue – Social Outputs

`posting_queue` already contains:

- Platform (`platform`), `content_type`, `scheduled_date/time`, `status`.
- `product_id` or `section_id` to identify the source content.

We can interpret each row as an Output:

```text
output_kind   = "social_queue"
output_id     = posting_queue.id
channel       = platform (normalized: facebook/instagram/twitter/etc.)
content_format= derived from content_type/channel_type (e.g. "product_post")
status        = normalize_queue_status(posting_queue.status)
```

Week/Slot association:

- We can compute `(year, week, day)` from `scheduled_date`, and `slot_type` from `content_type` (e.g. product highlight).
- For content that is derived from a Content Item (e.g. `product_id` or `section_id`), `content_type` + `content_item_id` come directly from those FKs.

#### 3.2.3 Rotation JSON – Planned Content

The rotation JSON remains the **source for planned Content Items per week**:

- It does *not* know about outputs; it only tells us which Content Item should appear in which week.
- When creating/assigning Outputs, we always know:
  - The Content Item (`content_type`, `content_item_id` from JSON or DB).
  - The Slot (`year`, `week`, possibly `day`).
  - We then create an Output (rows in `post` or `posting_queue`) and insert a row in `calendar_week_posts` or interpret `posting_queue` accordingly.

---

## 4. Lifecycle: From Planned to Actual

### 4.1 Creation / Assignment Rules

Whenever the user or automation **creates an Output from a planned slot**, the system **must**:

1. Identify the **Content Item** and **Slot**:
   - From rotation JSON + context: `(content_type, content_item_id, year, week, slot_type, day)`.
2. Create or reuse the Output record:
   - Blog: create or reuse `post` row.
   - Social: create or reuse `posting_queue` row.
3. Persist the **mapping**:
   - Blog: insert into `calendar_week_posts (year, week_number, post_id, ...)` if not already present.
   - Social: the `posting_queue` row already contains `scheduled_date` and product/section; we can treat it as self‑mapped but expose it through a unified view.
4. Status:
   - Determined by the Output record’s `status` field.
   - `unstarted` = no Output for that ContentItem+Slot in the mapping layer.

### 4.2 Reading for Display

Every calendar‑style view (week view, Future items, Channels schedule, one‑click context) then answers:

> For each week/slot and category, which Content Item is planned, which Outputs exist, and what are their statuses?

By:

1. Reading the **planned rotation**:
   - From JSON (for scheduling) or `calendar_week_selection` (for selected theme).
2. Looking up Outputs in the **mapping layer**:
   - Blog:
     - Use `calendar_week_posts` (or a view) to get `post_id` for the week.
   - Social:
     - Use `posting_queue` filtered by week/channel/content_type.
3. Joining to Output tables for **status**:
   - `post.status` → `draft/published/...`.
   - `posting_queue.status` → `scheduled/published/error/...`.

Views **do not guess**; they simply:

- Show “Not started”/`unstarted` when no Output exists in the mapping.
- Show `draft/scheduled/published` according to Output status.

---

## 5. Transitional Considerations

### 5.1 Existing Inconsistencies (e.g., Triskelion)

Cases like the W51 Triskelion blog post illustrate that:

- A `post` exists but was not recorded in `calendar_week_posts`.
- Some flows write to `calendar_week_items_deprecated` instead, or rely on title/idea_seed matching.

Under the unified model:

- Those posts must either:
  - Be **backfilled** into `calendar_week_posts` (for the appropriate week), or
  - Remain *unattached* to any week slot (and thus not shown as the main weekly blog output).
- Backfill can be done once via a migration script that:
  - Analyses recent themed posts (by known week context).
  - Inserts missing `calendar_week_posts` rows where the relationship is obvious.

### 5.2 Incremental Rollout

To avoid destabilizing everything at once:

- **Stage A (Blog only):**
  - Make `calendar_week_posts` the single source of truth for “which blog post belongs to which week”.
  - Ensure all creation/assignment flows for themed/recipe/profile blog posts:
    - Insert/update `calendar_week_posts` rows.
  - Update week view/Future items/dashboard to rely solely on this mapping for blog status.
- **Stage B (Social outputs):**
  - Define a thin view over `posting_queue` that exposes Output fields and week/day/channel in the same shape.
  - Integrate that into the same conceptual Output model so that social scheduling and status appear alongside blog status.

---

## 6. How This Supports the Unified Framework

This data model directly supports the requirements from the audit and your constraints:

- **Single truth for planned vs actual:**
  - Planned Content Items: rotation JSON + `calendar_week_selection`.
  - Actual Outputs: `post` + `calendar_week_posts` (blog), `posting_queue` (social).
  - Mapping ensures every created Output can be found by week/slot.
- **Unified status:** 
  - Status is always taken from `post.status` or `posting_queue.status`, normalized to the shared enum.
  - `unstarted` is simply “no Output row for this Content Item/Slot”.
- **No guessing:** 
  - No resolver is allowed to invent relationships by titles or seeds.
  - All consumers read from the mapping and Output tables/views.
- **Extensible:** 
  - New channels/formats can be added as new Output kinds or additional rows in the mapping layer, without changing the conceptual model.

This document will guide the refactor plan (`UNIFIED_OUTPUT_REFACTOR_PLAN.md`) and the subsequent implementation phases so that all calendar views and automation logic work against this unified, explicit structure instead of scattered heuristics.


