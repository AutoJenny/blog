# Unified Output Framework – Process Plan

**Date:** 2025-12-18  
**Scope:** Define a robust, sustainable framework that ties together *planned* and *actual* outputs (blog, social, etc.) with a single status model, and remove brittle heuristics and duplicated logic.

---

## 1. Terminology and Conceptual Model

To avoid the “posts/outputs” confusion, we standardise on:

- **Content Item**: The conceptual thing being created (e.g. “W51 Theme – Triskelion”, “Scotch Collops recipe”, “Weekly Insult: Yer heid’s full o wee broken gears”).  
  - These live primarily in planning tables (`calendar_themes`, `calendar_recipes`, `calendar_ideas`, etc.) and JSON rotation files.
- **Output**: A concrete deliverable on a specific channel and format, e.g.:
  - Blog article for W51 based on Triskelion.
  - Facebook product post from `posting_queue`.
  - Instagram carousel for a recipe.
- **Status**: A lifecycle state that applies uniformly to *all* outputs, regardless of channel:
  - `unstarted` – no concrete output exists yet.
  - `draft` – exists, but not ready / not scheduled.
  - `scheduled` – has a scheduled date/time on some channel.
  - `published` – has been delivered to the channel.
  - `error` – failed to publish / needs attention.
  - `cancelled` / `deleted` – explicitly cancelled or removed.

**Principle:** A W51 blog article is *one output type* alongside Facebook posts, tweets, etc.; “blog post” is not a separate conceptual universe.

---

## 2. Overall Process Plan

We will proceed in **phases**, with documentation and verification at each step.

### Phase 0 – Clarify and Document the Plan (this file)

- Capture:
  - Terminology and invariants.
  - High‑level phases for analysis and refactor.
  - File‑size constraints (no file > ~500 lines; split large modules rather than bloating).
- This plan is documentation only: **no code changes** in this phase.

### Phase 1 – System‑Wide Audit (Read‑Only)

**Goal:** Build a precise map of how planned content and outputs are currently wired, and where the failures/duplications are.

Activities:

- **Inventory data structures:**
  - Tables / views: `post`, `post_development`, `calendar_*` tables/views, `calendar_week_items(_deprecated)`, `calendar_week_posts`, `calendar_week_posts_v2`, `calendar_week_selection(_v2)`, `posting_queue`, JSON under `data/calendar/schedule/...`.
  - Identify which of these are *intended* to be authoritative for:
    - Planning / rotation.
    - Week persistence (which output belongs to which week/slot).
    - Channel‑specific scheduling.
- **Inventory endpoints and flows:**
  - Week Themes creation (`confirm_calendar_idea` and related).
  - One‑Click `create_post_from_item` and auto‑create logic.
  - Recipe and profile creation flows.
  - Publication dashboard and syndication endpoints.
  - Any legacy resolvers (`week_post_resolver`, ad‑hoc SQL) still in play.
- For each **flow**, document:
  - What IDs it **reads** (theme_id, recipe_id, profile_category_id, idea_id, etc.).
  - What it **writes** (new `post` rows, `calendar_week_*` rows, `posting_queue` rows).
  - How it currently computes or infers **status**.
  - Where it *should* persist a clean mapping between the Content Item and the Output, but doesn’t.

Deliverables:

- `docs/UNIFIED_OUTPUT_SYSTEM_AUDIT.md` (new) containing:
  - A concise map of:
    - Data structures.
    - Flows.
    - Identified failure points (e.g., missing theme→post mapping; status heuristics; duplicated logic).
  - No implementation, just analysis and diagrams/examples.

Constraints:

- Keep each doc under ~500 lines (split into multiple docs if necessary).
- No new fallback logic should be introduced during the audit.

### Phase 2 – Unified Data Model and Status Design

**Goal:** Specify a single, channel‑agnostic model that ties Content Items to Outputs plus their status.

Activities:

- Define the canonical **mapping layer** between planning and outputs, e.g.:

  ```text
  (content_item_id, content_type, year, week, slot, channel, format) → output_id
  ```

  where:

  - `output_id` is:
    - `post.id` for blog‑style outputs.
    - `posting_queue.id` (or a future `post_output_state.id`) for social outputs.
  - `status` is always drawn from the unified enum (`unstarted`/`draft`/`scheduled`/`published`/`error`/`cancelled`).

- Decide:
  - Which *existing* tables/views will be used, extended, or deprecated (`calendar_week_posts`, `calendar_week_items_summary`, etc.).
  - Where the canonical mapping lives (e.g., a cleaned‑up `calendar_week_posts` or a new `output_assignments` table).
- Precisely define:
  - How “unstarted” is represented (e.g., absence of an output row versus an explicit state).
  - How multiple outputs for the same content item/week/channel are handled (if allowed).

Deliverables:

- `docs/UNIFIED_OUTPUT_DATA_MODEL.md` (new):
  - Diagrams showing Content Items, Outputs, and Mapping.
  - Clear explanation of how blog and social outputs are represented uniformly.
  - Explicit rules for:
    - ID usage.
    - Status transitions.
    - How “planned but not yet created” is represented.

### Phase 3 – Refactor Plan (Code‑Level, Still No Changes)

**Goal:** Translate the data model into a concrete, staged refactor plan with small, safe steps.

Activities:

- For each area:
  - Calendar creation flows (Week Themes, one‑click, recipe/profile creation).
  - Week view backend / scheduling backend / publication dashboard backend.
  - One‑click / automation flows.
- Specify:
  - Exactly which functions will be **changed** to:
    - Write mapping entries at the moment Outputs are created.
    - Stop guessing status or output IDs later.
  - Which functions will be **deleted or hard‑disabled** as obsolete (resolvers, heuristics, fallbacks).
  - How each change will keep files under 500 lines (splitting out helpers where needed).

Deliverables:

- `docs/UNIFIED_OUTPUT_REFACTOR_PLAN.md`:
  - Per‑module change lists.
  - Ordering of phases.
  - Expected side‑effects and how they’ll be tested.

### Phase 4 – Implementation (Stepwise, with Progress Logging)

**Goal:** Implement the refactor incrementally and verifiably.

Implementation Rules:

- **One small slice at a time**:
  - E.g. “Make Week Themes creation write correct mapping rows and update one view to consume them.”
  - After each slice:
    - Run `curl` checks for the affected endpoints.
    - Sanity‑check the corresponding UI via the browser.
    - Update docs and a short change log.
- **No file bloat**:
  - If a file is approaching ~500 lines, split out helpers (`*_helpers.py`, focused `utils/` modules) instead of adding more.
- **Delete, don’t layer**:
  - When a new mapping‑based path is in place, remove the old heuristic logic for that path instead of leaving it dormant.

Progress Documentation:

- Maintain a short running log in `docs/UNIFIED_OUTPUT_IMPLEMENTATION_LOG.md` with entries like:

  ```text
  2025-12-20 – Phase 4.1:
    - Updated create_post_from_item() to write mapping rows for themed posts.
    - Updated week-view backend to read mapping instead of guessing.
    - Verified W51 Triskelion status via curl + browser (week-view, scheduling, dashboard).
  ```

This gives a traceable history of what changed and why, without bloating any one file.

### Phase 5 – Final Cleanup and Legacy Removal

**Goal:** Remove dead code and ensure the docs match the new reality.

Activities:

- Identify and remove:
  - Legacy schedulers/resolvers that no longer align with the unified framework.
  - Old docs that describe superseded models (mark as archived or delete).
- Ensure all “status” logic is:
  - Driven by the unified status enum.
  - Reading from the agreed mapping layers and not from ad‑hoc queries.

Deliverables:

- Updated core docs (e.g. `CALENDAR_SYSTEM_AUDIT.md`, `CALENDAR_SCHEDULING_ENDPOINTS.md`, any status‑related reports) to reference the new framework.
- `docs/UNIFIED_OUTPUT_FINAL_REPORT.md` summarising:
  - New architecture.
  - Removed components.
  - Remaining limitations, if any.

---

## 3. Progress Reporting Expectations

- At the end of **each major phase** (and at smaller milestones inside Phase 4), I will:
  - Update the relevant doc(s) under `docs/`.
  - Provide a short summary in chat:
    - What was analysed or changed.
    - Which files are now the source of truth for that part of the system.
    - How it was verified (curl/browser/API checks).
- No further code changes will be made without first:
  - Updating the appropriate planning doc to reflect the intended modifications.
  - Keeping individual files lean and responsibilities well‑scoped.

This document is the anchor for that process; subsequent docs and code changes will explicitly reference it so the framework remains understandable and maintainable over time.


