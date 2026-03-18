# Social Output View Design

**Date:** 2025-12-18  
**Goal:** Provide a single, explicit abstraction for *social Outputs* (posting_queue rows) so they can participate in the unified Output framework alongside blog Outputs, using ID‑only linkage to Content Items and a shared status model.

---

## 1. Scope and Requirements

- Treat social posts (Facebook, Instagram, Twitter, etc.) as **Outputs** in the same conceptual model as blog posts.
- Preserve the existing `posting_queue` table as the physical storage for social Outputs.
- Add a minimal, explicit ID link from weekly Content Items (weekly word/phrase/insult) to `posting_queue`:
  - Use a new `idea_id` column on `posting_queue` that points at `calendar_ideas.id`.
- Avoid title/text heuristics entirely; all linkage must be ID‑based.
- Keep changes small and well‑documented; avoid file bloat.

---

## 2. Data Sources

### 2.1 Content Items

- **Weekly items:**
  - `calendar_ideas` with classification:
    - `content_type = "weekly_word" | "weekly_phrase" | "weekly_insult"`.
    - `content_item_id = calendar_ideas.id`.
  - Planned per week via rotation JSON:
    - `data/calendar/schedule/weekly_word/{year}.json`
    - `data/calendar/schedule/weekly_phrase/{year}.json`
    - `data/calendar/schedule/weekly_insult/{year}.json`

- **Products:**
  - `clan_products`:
    - `content_type = "product"`.
    - `content_item_id = clan_products.id`.
  - Planned and used in product posting flows independently of the weekly calendar rotation.

### 2.2 Social Outputs (Physical Storage)

- **`posting_queue` table**

  Key fields:

  - `id` – primary key (queue row id).
  - `platform` – `"facebook"`, `"instagram"`, `"twitter"`, etc.
  - `content_type` – e.g. `"product"`, `"weekly_word"`, `"weekly_phrase"`, `"weekly_insult"`, …
  - `scheduled_date` / `scheduled_time` – when the post is due to be published.
  - `status` – raw queue status (e.g. `pending`, `ready`, `published`, `failed`, `cancelled`).
  - `product_id` – for product posts (FK → `clan_products.id`).
  - **`idea_id` (NEW)** – for weekly posts (FK → `calendar_ideas.id`), nullable:
    - `idea_id` is set for weekly word/phrase/insult queue rows.
    - `product_id` is used for product posts.

---

## 3. Logical Social Output Model

Conceptually we expose each social post as:

```text
SocialOutput {
  output_kind: "social_queue"
  output_id: posting_queue.id
  channel: "facebook" | "instagram" | "twitter" | ...
  content_format: string        # e.g. "product_post", "word_of_day", ...
  status: enum                  # unified status, via normalize_queue_status()

  year: int
  week: int
  day: int                      # 1–7 from scheduled_date (ISO weekday)

  content_type: string          # "product", "weekly_word", "weekly_phrase", "weekly_insult", ...
  content_item_id: int          # clan_products.id or calendar_ideas.id
}
```

This model is read‑only from the perspective of calendar views and dashboards; creation and updates still go through the existing posting_queue creation flows.

---

## 4. View / Helper Definition

### 4.1 Deriving Week and Day

For any `posting_queue` row with a non‑null `scheduled_date`:

- `year`, `week`, `day` are derived using ISO week rules:

```text
year = iso_year(scheduled_date)
week = iso_week(scheduled_date)
day  = iso_weekday(scheduled_date)   # 1 = Monday, 7 = Sunday
```

These values allow calendar UIs and dashboards to align social Outputs with the same `(year, week, day)` grid as blog Outputs.

### 4.2 Content Item Linkage

We define `(content_type, content_item_id)` for each row as:

- **Product posts:**

  ```text
  IF posting_queue.product_id IS NOT NULL:
      content_type   = 'product'
      content_item_id= posting_queue.product_id
  ```

- **Weekly items (NEW, via idea_id):**

  ```text
  ELSE IF posting_queue.idea_id IS NOT NULL:
      content_type   = posting_queue.content_type  # 'weekly_word', 'weekly_phrase', 'weekly_insult'
      content_item_id= posting_queue.idea_id       # FK → calendar_ideas.id
  ```

  This gives a stable, ID‑only link from a weekly Content Item (in `calendar_ideas`) to all its associated social Outputs.

- **Other content types:**

  - For any future posting patterns, the same scheme can be extended either by:
    - Adding a new FK column on `posting_queue`, or
    - Defining a mapping rule in a helper function that interprets existing fields.

### 4.3 Channel and Content Format

- `channel` is a normalized version of `platform`:

  ```text
  channel = LOWER(platform)      # 'facebook', 'instagram', 'twitter', ...
  ```

- `content_format` is derived from a mapping of `(content_type, channel_type)`:

  Examples:

  - `content_type = 'product'` → `content_format = 'product_post'`.
  - `content_type = 'weekly_word'` → `content_format = 'word_of_day'`.
  - `content_type = 'weekly_phrase'` → `content_format = 'phrase_of_day'`.
  - `content_type = 'weekly_insult'` → `content_format = 'insult_of_day'`.

The exact mapping is defined alongside channel configuration docs, not hard‑coded in the view.

### 4.4 Status Normalization

- `status` is normalized from `posting_queue.status` via `normalize_queue_status()`:

  - `pending`, `ready` → `scheduled`
  - `published` → `published`
  - `failed`, `error` → `error`
  - `cancelled` → `deleted`
  - Unknown values are surfaced as‑is for diagnostics.

This puts social Outputs on the same status enum as blog Outputs.

---

## 5. Intended Consumers

### 5.1 Publication Dashboard

- The social columns (Facebook, Twitter, etc.) will:
  - Read from `SocialOutputView` (or the helper) for the requested `(year, week)`.
  - Display:
    - `title` / description from joined product/idea tables if needed.
    - Unified `status` (scheduled / published / error / deleted).
  - Avoid any direct `posting_queue` status logic in the blueprint.

### 5.2 Future Items / Scheduling

- When rendering weekly word/phrase/insult rows for a given `(year, week)`:
  - The backend can:
    - Use rotation JSON to determine which weekly Content Items are planned.
    - Use `SocialOutputView` to answer “which social Outputs exist for this Content Item this week, and what is their status?”.
  - This lets the UI indicate, per Content Item, whether social posts are already queued/published without guessing from other fields.

### 5.3 Week View (Optional)

- The week view can remain focused on blog Outputs, or:
  - Optionally surface a compact indicator that weekly items have social Outputs scheduled/published, based solely on `SocialOutputView`.

---

## 6. Non‑Goals and Constraints

- **No fallbacks to text matching:**
  - The view/helper must never infer Content Items by matching `title` or body text.
  - If `idea_id` or `product_id` are missing, the row simply has no Content Item linkage and should not be shown as such in calendar‑driven views.

- **No schema bloat:**
  - Only the minimal `idea_id` column is added to `posting_queue`.
  - Any further generalization (e.g. `content_item_type`/`content_item_id`) would be a separate, explicitly approved change.

- **Backwards compatibility:**
  - Existing product posts continue to use `product_id`; the new `idea_id` is additive.
  - The view/helper is introduced and wired into consumers in a controlled, phased way to avoid regressions.

---

## 7. Next Steps (Implementation Plan Link)

Implementation steps for this design are tracked in:

- `docs/UNIFIED_OUTPUT_REFACTOR_PLAN.md` – Phase “Social Outputs & Weekly Items”
- `docs/UNIFIED_OUTPUT_IMPLEMENTATION_LOG.md` – per‑change notes as wiring is added

This document defines the **contract** for social Outputs; code changes will follow it and stay within these constraints.


