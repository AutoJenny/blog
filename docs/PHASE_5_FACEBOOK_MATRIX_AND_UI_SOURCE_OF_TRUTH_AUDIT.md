## Phase 5 — Facebook Matrix & UI Source-of-Truth Audit

**Date:** 2026-01-27  
**Status:** 🔍 Discovery / Diagnostic Only (no code changes in this phase)  

This document answers: **“Where is the authoritative definition of what each day’s Facebook post is, and how many overlapping systems are currently expressing that intent?”**  
It focuses on:

- The **weekly Facebook matrix** (Mon–Sun),
- **Roles / DEPTH_LONG** vs older “post type” abstractions,
- The **calendar week view** and **Social Posts** UI,
- Any other systems that define or imply “what a day/post is for”.

No refactors or schema changes are proposed here; this is an inventory and analysis only.

---

## 1. Summary Findings (High-Level)

### 1.1 Single Source of Truth for Sunday (Locked)

- **Authoritative for Sunday 15:00 (Facebook):**
  - **Role:** `DEPTH_LONG` (Deep Dive)
  - **Slot Intent:** Defined by **Content Roles Framework** + **Facebook matrix** (Sunday = Deep Dive).
  - **Data & Execution:**
    - `posting_queue.role = 'DEPTH_LONG'`, `platform = 'facebook'`, `scheduled_date` = Sunday, `scheduled_time` = `15:00:00`.
    - **Generation & validation:** `blueprints/content_roles_api.py` (DEPTH_LONG endpoint), tied to `kb_topic_rota`.
    - **Planning UI:** Sunday cell in `/planning/content-control-board` and `/planning/calendar` (week view) shows this post and its role/status.
- **Conclusion:**  
  - For **Sunday**, the intent pipeline is already role- and rota-driven:
    - **Topic (rota)** → **Angle** (optional) → **Role (DEPTH_LONG)** → **Channel (Facebook)** → **Post (`posting_queue`)**.
  - Legacy/competing definitions for Sunday (e.g., “Scotland Today” or product slots) are **no longer authoritative for Sunday posting**, but some legacy labels remain in the UI and supporting tables.

### 1.2 Multiple Systems Describing Mon–Sat Intent

For **Monday–Saturday**, there are several overlapping systems:

1. **Weekly Social Focus matrix** (`weekly_social_focus`):
   - Data-backed per-day labels like **“From the Blog”, “Tartan Tuesday”, “Workshop Wednesday”, “Throwback Thursday”, “Family Friday”, “Product Spotlight”, “Scotland Today”**.
   - Shown in the **calendar week view “dates line”** (`.social-focus` elements under Mon–Sun headers).
   - **Today:** purely a **UI-planning descriptor**; does **not** directly create or schedule posts.

2. **Weekly Language & Product Content Types**:
   - `weekly_word`, `weekly_phrase`, `weekly_insult`, plus **product** and **message** entries.
   - Represent **weekly recurring content types** (words/phrases/insults) and **product posts**.
   - Shown as **“LANGUAGE: WORD / LANGUAGE: PHRASE / LANGUAGE: INSULT / PRODUCT / Deep Dive”** in the **Social Posts** row of the week view.

3. **Content Roles Framework** (`content_roles`, `posting_queue.role`):
   - New **role enum**: `REASSURANCE`, `AUTHORITY_SHORT`, `DEPTH_LONG`, `CULTURE`, `COMMERCE`, `LEGACY`.
   - Authoritative for **what a post is for**.
   - **Fully wired for Sunday DEPTH_LONG**; **not yet** the canonical driver for Mon–Sat in the calendar UI.

4. **Facebook Weekly Role Matrix (Policy)**:
   - Documented in roles docs & adviser briefs:
     - Mon: CULTURE
     - Tue: COMMERCE
     - Wed: CULTURE
     - Thu: COMMERCE
     - Fri: CULTURE
     - Sat: REASSURANCE
     - Sun: DEPTH_LONG
   - This matrix is **policy-locked** but not yet fully enforced in all UI surfaces for Mon–Sat.

**Key Tension:**  
Mon–Sat currently have **at least two conceptual descriptions**:

- A **legacy-ish, UI-only “social focus”** (e.g. “Tartan Tuesday”, “Product Spotlight”).
- A **role-based Facebook matrix** (CULTURE/COMMERCE/REASSURANCE), which is **partially surfaced** (e.g. in Content Control Board tooltips) but **not yet driving everything**.

---

## 2. Inventory of Systems Defining “What a Day/Post Is”

This section lists each relevant system and evaluates its semantics, usage, and overlap.

### 2.1 `weekly_social_focus` — Day-of-Week Social Focus Labels

| Field | Value |
| --- | --- |
| **Name / Identifier** | `weekly_social_focus` table & API |
| **Where It Lives (DB)** | `migrations/create_weekly_social_focus.sql` (`weekly_social_focus` table) |
| **Seed Data** | Lines 23–30 seed the seven focuses: `From the Blog`, `Tartan Tuesday`, `Workshop Wednesday`, `Throwback Thursday`, `Family Friday`, `Product Spotlight`, `Scotland Today`  (`migrations/create_weekly_social_focus.sql` L23–30) |
| **Backend** | `blueprints/planning_api_calendar_social_focus.py` (API endpoints `api_weekly_social_focus`, `api_weekly_social_focus_day`, CRUD) |
| **Frontend / UI** | `static/js/planning/calendar-week-view.js` (`renderSocialFocuses`) + `templates/planning/calendar/week_view.html` (day headers & `.social-focus` elements) |

**What It Represents**

- A **per-day “social focus”** string for each day of week, with extra metadata:
  - `social_focus` → label (e.g. “Tartan Tuesday”),
  - `format`, `purpose`, `example` → guidance text.
- Conceptually: **“What this day’s social media output should feel like / be about”**, at a **theme/creative** level.
- It is **not a role** and **not a concrete post type**.

**Who Consumes It**

- **Calendar Week View (UI only):**
  - `week_view.html` defines the structure:
    - Mon–Sun headers with `<div class="social-focus" data-day="N"></div>` (L87–115).
  - `calendar-week-view.js`:
    - `renderSocialFocuses(focuses)` builds a **map of `day_of_week` → focus** (`focusMap`) and writes `focus.social_focus` into each `.social-focus[data-day]` element (L1616–1639).
    - **This is exactly the “Mon 26 From the Blog / Tue 27 Tartan Tuesday … Sun 1 Scotland Today” line.**
- **Social Focus Modal**:
  - Same JS + `templates/planning/calendar/social_focus_modal.html` allow viewing/editing each day’s focus (still a planning-only tool).

**Is It Authoritative Today?**

- **For policy:**  
  - It **encodes a planning concept** (“Tartan Tuesday” etc.) that predates the Roles framework.
- **For actual posting & scheduling:**  
  - **No.** It does **not** create `posting_queue` rows, does not drive `content_roles`, and is not considered in `automation_execute` or `posting_queue` queries.
- Current docs (`docs/WEEKLY_SOCIAL_POST_CREATION_AUDIT.md` L117–121) explicitly state:
  - `weekly_social_focus` **does not create posts** and **does not handle weekly content**.

**Overlap with New Framework**

- **Overlaps conceptually with:**
  - **Facebook weekly matrix** (day-level intent),
  - **Roles** (CULTURE/COMMERCE/REASSURANCE).
- **Does not overlap with:**
  - **Angles** (no topic/angle binding),
  - **Sunday DEPTH_LONG** (Sunday Deep Dive is role + rota-based, independent of “Scotland Today” label).
- **Conflict:**  
  - For **Sunday**, the label “Scotland Today” is **still displayed**, even though the canonical Sunday role is `DEPTH_LONG` Deep Dive.
  - For **Tue/Thu**, “Product Spotlight” overlaps heavily with the **COMMERCE** role.

---

### 2.2 Weekly Language & Product Types (`weekly_word`, `weekly_phrase`, `weekly_insult`, `product`, `message`)

| Field | Value |
| --- | --- |
| **Name / Identifier** | Weekly language content types + product posts |
| **Where It Lives (DB)** | `calendar_ideas` / cyclic scheduling tables (ideas) and `posting_queue.content_type` (for created posts) |
| **Backend (Calendar)** | `blueprints/planning_api_calendar_schedule.py`, `planning_api_calendar_cyclic.py`, `planning_api_calendar_scheduling_cache.py` |
| **Backend (Execution)** | `blueprints/automation_core.py`, `automation_execute.py`, `publication_dashboard.py`, `posting_queue_view.py`, `posts.py` |
| **Frontend** | `static/js/planning/calendar-week-view.js` (week grid) + `templates/planning/calendar/week_view.html` / `includes/scheduling_content.html` / `includes/scheduling_scripts.html` |

**What It Represents**

- Three **language-based weekly content streams**:
  - `weekly_word`, `weekly_phrase`, `weekly_insult`.
- **Product posts** and **message posts** as separate categories.
- In calendar scheduling:
  - `planning_api_calendar_schedule.py` L39–41:
    - Resolves weekly word/phrase/insult using cyclic resolver.
  - Adds them to the schedule array with `type` = `weekly_word`, `weekly_phrase`, `weekly_insult` and `title` / `description` (L134–160).
- In the **week view UI**:
  - **Scheduling view** (`templates/planning/calendar/scheduling.html` + `includes/scheduling_scripts.html`):
    - Build cells that display:
      - **TypeName** such as `language: word`, `language: phrase`, `language: insult` (L253–277 in `scheduling_scripts.html`).
  - **Week view / Social Posts row** (`calendar-week-view.js`):
    - `renderItems` maps `type` to a `typeName`:
      - `'weekly-word' → 'language: word'`,
      - `'weekly-phrase' → 'language: phrase'`,
      - `'weekly-insult' → 'language: insult'`,
      - `'product' → 'product'`,
      - `'depth_long' → 'Deep Dive'` (L175–185).
    - Later, `loadWeek` places:
      - `weekly_word` in Monday Social Posts cell,
      - `weekly_phrase` in Wednesday,
      - `weekly_insult` in Friday (L932–955).

**Who Consumes It**

- **Calendar Week View & Scheduling UIs:**
  - Display “LANGUAGE: WORD / PHRASE / INSULT / PRODUCT” as **category labels**.
- **Automation & Publication:**
  - Automation and posting scripts treat these as **content_type** values:
    - `automation_core.py` & `automation_execute.py` contain multiple branches for `weekly_word`, `weekly_phrase`, `weekly_insult`.
    - `publication_dashboard.py` and `posting_queue_view.py` include them in queries and type mapping (e.g. mapping `weekly_word` → display “Word”).

**Is It Authoritative Today?**

- **For those specific weekly content streams:** Yes.
  - They are the **only system that currently defines “Weekly Word”, “Weekly Phrase”, “Weekly Insult”**,
  - They drive automation & posting for those categories.
- **For the broader Facebook day intent:** No.
  - They **do not define** what Facebook’s **single daily role** is (e.g. CULTURE vs COMMERCE),
  - They simply represent one **class** of possible posts shown in the Social Posts row.

**Overlap with New Framework**

- **Partial overlap with Roles:**
  - Weekly language posts could map naturally into **CULTURE** (or later roles) but are not yet wired that way.
- **No direct overlap with Angles**:
  - They are defined as weekly rotations / language content streams, not editorial interpretations of topics.
- **Overlap with Social Focus & Matrix:**
  - The Social Posts row for Mon/Wed/Fri shows language content that may sit alongside other roles or focuses, but there is **no central binding** to the Facebook matrix yet.

---

### 2.3 Content Roles Framework (`content_roles`, `posting_queue.role`)

| Field | Value |
| --- | --- |
| **Name / Identifier** | Content Roles Framework (Roles) |
| **Where It Lives (DB)** | `content_roles` enum/lookup + `posting_queue.role` column |
| **Backend** | `blueprints/content_roles_api.py`, `utils/platform_publishers.py`, `utils/channel_preview/formatters/facebook.py`, generation/validation scripts |
| **Frontend** | `static/js/planning/content_control_board.js`, `static/js/planning/unified-item-card.js`, `templates/planning/content_control_board.html`, `templates/kb_topics/rota_editor.html` |

**What It Represents**

- **Canonical roles**:
  - `REASSURANCE`, `AUTHORITY_SHORT`, `DEPTH_LONG`, `CULTURE`, `COMMERCE`, `CULTURE`, `LEGACY`.
- For each post in `posting_queue`, `role` encodes **why the post exists** (job, not channel).
- For Sunday:
  - `DEPTH_LONG` is now fully enforced and visible on calendar & control board.

**Who Consumes It**

- **Content Control Board:**
  - `ContentControlBoard.getRoleDisplayName()` maps roles to human labels:
    - `DEPTH_LONG` → “Deep Dive”,
    - `COMMERCE` → “Product Spotlight”,
    - `CULTURE` → “Cultural Detail”, etc. (L770–779).
  - `getRoleInfo()` uses roles to provide tooltips aligned with the locked matrix:
    - **CULTURE**: “personality and rhythm (Mon/Wed/Fri)”,
    - **COMMERCE**: “Product Spotlight — make products visible (Tue/Thu)”,
    - **DEPTH_LONG**: “Deep Dive — long-form expertise (Sunday)”.
- **Platform publishing & preview:**
  - Facebook formatter and preview use `role` to determine constraints, but not yet for most Mon–Sat surface behaviour.

**Is It Authoritative Today?**

- **For Sunday:** Yes (DEPTH_LONG).
- **For Mon–Sat:** Partially:
  - The **policy** is locked through this framework (CULTURE/COMMERCE/REASSURANCE).
  - The **UI + data** are not yet consistently driven by `role` for Facebook Mon–Sat.

**Overlap with New/Legacy Systems**

- Overlaps conceptually with:
  - `weekly_social_focus` (both talk about “what this day is for”),
  - Weekly language / product types (both talk about “what kind of post this is”).
- Distinct from:
  - `calendar_themes` (blog themes) and `weekly_social_focus` (day focus tags) which are **decorative/plan-level**.

---

### 2.4 `calendar_themes` — Week-Wide Blog Themes (for completeness)

| Field | Value |
| --- | --- |
| **Name / Identifier** | `calendar_themes` |
| **Where It Lives (DB)** | `migrations/create_calendar_themes_table.sql` |
| **Backend** | `blueprints/planning_api_themes.py`, `planning_api_calendar_ideas.py`, `planning_api_posts.py`, header prompt compilation (`header/api_prompt_compilation.py`) |
| **Frontend** | Blog planning UIs, blog pipeline header (`static/js/shared/blog-pipeline-header.js`) |

**What It Represents**

- Week-wide **blog themes** used for blog post planning and ideas, **not** social posts.

**Who Consumes It**

- Blog pipeline & calendar ideas surfaces for **blog content**.

**Is It Authoritative for Facebook?**

- **No.** It is explicitly **blog-focused** (`docs/ANGLES_LAYER_FINAL_SPECIFICATION.md` §6.2) and intentionally **not reused** for social roles or channel matrices.

**Overlap**

- Conceptually related to “week-wide editorial topics”, but:
  - Facebook roles + Angles layer are **explicitly separated** from `calendar_themes`.

---

## 3. Explicit Conflicts and Duplication

### 3.1 Sunday: “Scotland Today” vs DEPTH_LONG Deep Dive

- **UI Label:**  
  - Sunday header in week view shows “Scotland Today” via `weekly_social_focus` (social_focus for day 7).
- **Canonical Role:**  
  - Content Roles + FB matrix define Sunday 15:00 as **DEPTH_LONG (Deep Dive)**.
- **Actual Posts:**
  - Sunday Deep Dive posts now have:
    - `posting_queue.role = 'DEPTH_LONG'`,
    - `platform = 'facebook'`,
    - scheduled at Sunday 15:00,
    - surfaced in Control Board and week view.
- **Conflict:**
  - The **visual “Scotland Today” label** implies a different intent (news/aspirational Scotland content vs deep expertise) and is **no longer aligned with the actual role-based Sunday Deep Dive**.
  - This is **not mechanically harmful** (it doesn’t create posts), but **creates conceptual drift** if left as-is.

### 3.2 “Product Spotlight” vs COMMERCE Role

- **From `weekly_social_focus`:**
  - Saturday (6) is seeded as “Product Spotlight”.
- **From Roles/Matrix:**
  - COMMERCE role is meant for **Tue/Thu** in the adviser’s matrix.
- **From Control Board Role Tooltips:**
  - COMMERCE tooltip: “Product Spotlight — make products visible (Tue/Thu)” (`getRoleInfo()`).
- **Conflict:**
  - The **same phrase “Product Spotlight”** is:
    - used as a **day-level social focus** (Saturday, via `weekly_social_focus`), and
    - used as the **display-name for COMMERCE role** (Tue/Thu).
  - This may suggest COMMERCE=Saturday only, which **contradicts** the locked Facebook role matrix.

### 3.3 “Deep Dive” as Legacy Post Type vs `DEPTH_LONG` Role

- **Legacy usage:**
  - `templates/planning/calendar/content_generator_modal.html` includes `<option value="deep_dive">Deep Dive</option>`, which predates the role system.
  - Weekly calendar labels used to show “Deep Dive” as a content type (without roles).
- **New usage:**
  - `ContentControlBoard.getRoleDisplayName()` uses `DEPTH_LONG → "Deep Dive"`.
  - `calendar-week-view.js` `renderItems()` maps type `'depth_long'` to `"Deep Dive"`, aligning the **card label** with the role.
- **Conflict:**
  - **Today**, “Deep Dive” can refer to:
    - A **role** (`DEPTH_LONG`),
    - A **legacy value** (`deep_dive` in old generator modal),
    - A **card label** derived from either.
  - This is *mostly* converged (the role is winning), but the existence of the old `<option value="deep_dive">` is a sign of **legacy overlap**.

### 3.4 “LANGUAGE: WORD / PHRASE / INSULT” vs Roles

- **UI:**
  - Social Posts row shows `language: word`, `language: phrase`, `language: insult` for weekly word/phrase/insult.
- **Back-end semantics:**
  - Content types `weekly_word`, `weekly_phrase`, `weekly_insult` are treated as **standalone categories** (with their own automation).
- **Roles:**
  - These streams do **not yet have roles** attached (`posting_queue.role` is not systematically set for them).
- **Conflict / Duplication:**
  - They represent **intent** (education, culture, humour), but that intent is **not codified as roles**.  
  - They co-exist with the upcoming weekly role matrix, which may also want to describe **what happens on Mon/Wed/Fri**.

---

## 4. What Currently Drives Each Day (Facebook)

### 4.1 Sunday — Deep Dive (DEPTH_LONG) — **Correct & Locked**

- **Intent:**  
  - `DEPTH_LONG` role, Sunday Deep Dive, 15:00, topic-bound to `kb_topic_rota`.
- **Data:**
  - `posting_queue` row with `role='DEPTH_LONG'`, `platform='facebook'`, Sunday `scheduled_date`, `scheduled_time='15:00:00'`.
- **Generation/Validation:**
  - `content_roles_api` DEPTH_LONG endpoint with rota topic enforcement.
- **Surfaces:**
  - **Control Board** Sunday cell.
  - **Calendar Week View** Sunday Social Posts row (via `posting_queue` + `renderItems(..., 'depth_long', ...)`).
  - **Sunday Slot panel**.
  - **Preview** via unified preview system + full-page route.
- **Other labels present:**
  - `weekly_social_focus` still sets Sunday’s “Scotland Today” label in the header, but does **not** control posting.

### 4.2 Mon–Sat — Current Drivers

- **Weekly Social Focus (`weekly_social_focus`):**
  - Drives the **UI header labels**: “From the Blog”, “Tartan Tuesday”, “Workshop Wednesday”, “Throwback Thursday”, “Family Friday”, “Product Spotlight”, “Scotland Today”.
  - **No direct scheduling or posting.**

- **Weekly Language & Product Streams:**
  - Drive **what appears in the Social Posts row**:
    - Mon: weekly word,
    - Wed: weekly phrase,
    - Fri: weekly insult,
    - plus product posts on their scheduled days.
  - These have **automation and posting logic** but are **not yet tied to roles**.

- **Facebook Weekly Role Matrix (Policy):**
  - Defines roles per day (CULTURE/COMMERCE/REASSURANCE) but:
    - Is currently **enforced only for Sunday** (DEPTH_LONG).
    - For Mon–Sat, lives primarily in documentation + Control Board display/tooltip text, but not yet as **mechanically enforced** as Sunday.

---

## 5. Recommended Single Source of Truth (Proposal Only)

> **Note:** This section is design guidance only. No code changes have been made in this phase.

### 5.1 Canonical Levels and Their Responsibilities

The recommendation is to adopt the following canonical hierarchy for Facebook, consistent with existing specs:

1. **Topic & Rota (Existing):**
   - `kb_topic_rota` defines **weekly topics**.
   - Already authoritative for Sunday DEPTH_LONG.

2. **Angles (Existing, Sunday-focused):**
   - Formal editorial interpretations of topics.
   - Will remain the **storyline layer** between topic and role.

3. **Roles (Canonical for Intent):**
   - **Single source of truth** for **“what job this post does”**.
   - The **Facebook matrix** (Mon–Sun) should be expressed entirely in terms of **role per day**, e.g.:
     - Mon: `CULTURE`,
     - Tue: `COMMERCE`,
     - Wed: `CULTURE`,
     - Thu: `COMMERCE`,
     - Fri: `CULTURE`,
     - Sat: `REASSURANCE`,
     - Sun: `DEPTH_LONG`.

4. **Channel / Platform (Existing):**
   - Platform-specific expression, already well defined.

5. **Legacy/Decorative Layers (UI-only after mapping):**
   - `weekly_social_focus` labels,
   - Weekly language & content-type descriptors (`language: word`, etc.),
   - Older labels like “Deep Dive” as a content type.

### 5.2 Proposed Treatment of Existing Systems

**1. Roles + Facebook Matrix → **Single Source of Truth** for Daily Intent**

- **Keep and strengthen:**
  - `posting_queue.role` and `content_roles` as the **only authoritative representation** of **post intent**.
  - Formalise the Facebook matrix as:
    - A small, **role-by-day configuration** (e.g. `facebook_role_schedule` or similar) which:
      - maps `day_of_week → role`,
      - is read by both generation logic and UI.

**2. `weekly_social_focus` → UI Decoration Mapped to Roles**

- **Keep as UI-only decoration**, but:
  - Explicitly document and implement that:
    - Each `weekly_social_focus.day_of_week` is **mapped to a canonical role** for that day.
    - The label (e.g. “Tartan Tuesday”) is **presentation only**, not a separate source of intent.
  - Example mapping:
    - Mon – “From the Blog” → `CULTURE` (or another agreed role),
    - Tue – “Tartan Tuesday” → `CULTURE` or `AUTHORITY_SHORT` (depending on final strategy),
    - Thu – “Throwback Thursday” → `AUTHORITY_SHORT` or `CULTURE`,
    - Sat – “Product Spotlight” → `COMMERCE` (if Saturday is later redefined), etc.
- **For Sunday specifically:**
  - Decide whether:
    - `Scotland Today` is retired, or
    - mapped explicitly to **DEPTH_LONG** in documentation, or
    - repurposed as a **superficial caption** for the Deep Dive slot.

**3. Weekly Language Streams (`weekly_word`, `weekly_phrase`, `weekly_insult`) → Map or Isolate**

- Two options (to be decided later, not implemented now):
  1. **Map to Roles:**
     - E.g. treat `weekly_word` and `weekly_phrase` as **CULTURE** posts when scheduled to Facebook.
     - Ensure `posting_queue.role` is set accordingly when these become actual Facebook posts.
  2. **Isolate as Non-Matrix Streams:**
     - Treat them as **separate, non-Facebook-matrix** content streams which may or may not be scheduled to Facebook.
     - In that case, always display them as **secondary** to the main daily role slot (distinct styling).

**4. Legacy “Deep Dive” Type vs `DEPTH_LONG` Role**

- **Retain `DEPTH_LONG` as the only canonical definition of Deep Dive**.
- **Mark any legacy uses** of `"deep_dive"` (e.g. in generator modals) as:
  - either wrappers around requesting `role=DEPTH_LONG`,
  - or deprecated UI paths to be removed.

---

## 6. Systems to Retire, Re-map, or Keep (Proposal)

> **No changes have been made; this is a recommendation for future implementation phases.**

### 6.1 Retire (or Mark as Legacy)

- **Legacy Deep Dive content type (`deep_dive` in UI options):**
  - Replace with explicit “Sunday Deep Dive (DEPTH_LONG)” role-based controls.
  - Ensure **roles** are the only underlying representation of Deep Dive.

### 6.2 Re-Map

- **`weekly_social_focus` labels:**
  - Keep the table and editor, but:
    - Document that each `social_focus` is **cosmetic** and must be **mapped to a canonical role** for that day.
    - For Sunday, ensure the label is consistent with `DEPTH_LONG` or clearly marked as legacy.
- **Weekly language streams & product post labels in Social Posts row:**
  - When used for Facebook posts, ensure any created `posting_queue` rows receive a **role** consistent with the Facebook matrix.

### 6.3 Keep as UI-Only Decoration

- **Calendar Week View Filters & Badges:**
  - Filters like “Words”, “Syndication”, “Annual”, “Special” (week view header filters) can remain as **UI affordances**, not intent definitions, provided they’re clearly documented as such.
- **Calendar themes (`calendar_themes`)**:
  - Remain **blog-focused** and **unchanged**, per Angles spec.

---

## 6.4 DRIVER / UI_ONLY / RETIRE Classification Table

The table below classifies the key systems discussed above according to their intended role in the Facebook Matrix v1 world. This classification is conceptual; implementation will follow in the dedicated Matrix v1 report.

| System / Table / Concept                    | Where It Lives (examples)                                                                                   | Classification | Notes                                                                                                                                                         |
|---------------------------------------------|--------------------------------------------------------------------------------------------------------------|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `content_roles` + `posting_queue.role`      | `content_roles` table/enum, `posting_queue.role`, `blueprints/content_roles_api.py`                          | **DRIVER**     | Canonical source of post intent (Role). Facebook Matrix v1 must be expressed entirely in terms of Role per day.                                              |
| Facebook Matrix (policy)                    | Roles docs, adviser briefs (now `utils/facebook_matrix_v1.py`)                                              | **DRIVER**     | Day → Role mapping (Mon–Sun) + fixed language angles is the single source of truth for daily Facebook intent.                                               |
| `weekly_social_focus`                       | `weekly_social_focus` table, `planning_api_calendar_social_focus.py`, `calendar-week-view.js` dates line    | **UI_ONLY**    | Provides legacy day labels (e.g. “Tartan Tuesday”, “Scotland Today”) as optional, decorative hints. Must never drive backend logic or scheduling decisions. |
| Weekly language content types               | `weekly_word`, `weekly_phrase`, `weekly_insult` in `calendar_ideas`, `planning_api_calendar_schedule.py`    | **DRIVER**     | Drivers for language content streams. Under Matrix v1 they are **Angles** inside CULTURE slots, not standalone roles.                                        |
| Product post scheduling for Facebook        | `posting_queue.content_type = 'product'`, `post_type_channel_config`, `planning_api_calendar_schedule.py`   | **DRIVER**     | Determines when product posts exist. Under Matrix v1 these are COMMERCE-role posts; day placement must align with the Matrix over time (Sat spotlight).      |
| `calendar_themes` (week-wide blog themes)   | `calendar_themes` table, `planning_api_themes.py`, blog planning UIs                                         | **UI_ONLY**    | Blog-only planning; **not** a driver for Facebook roles or daily intent.                                                                                     |
| Legacy “Deep Dive” content type / flags     | Old generator options (e.g. `value="deep_dive"`), any non-role Deep Dive markers                             | **RETIRE**     | Replaced by `DEPTH_LONG` Role. Any surviving flags should be treated as legacy and migrated or removed.                                                      |
| LANGUAGE:* labelling in calendar UI         | `calendar-week-view.js`, `scheduling_scripts.html` (“language: word/phrase/insult”)                         | **UI_ONLY**    | Becomes **Angle** labelling only (secondary). Primary label must be the Role (CULTURE).                                                                      |
| Social Posts row product/message labels     | Social Posts panel in week view, publication dashboard                                                       | **UI_ONLY**    | Must be normalised to Role-first (COMMERCE / REASSURANCE) with “Product” or “Message” as secondary descriptors only.                                         |

---

## 7. Definition of Done (For This Audit)

This report establishes:

- **The current authoritative definition for Facebook Sunday**, which is now:
  - `Topic (rota)` → `Angle` (optional) → `Role (DEPTH_LONG)` → `Channel (Facebook)` → `Post (posting_queue)`.
- **The fact that Mon–Sat currently have overlapping abstractions**:
  - **Weekly social focus labels** (`weekly_social_focus`),
  - **Weekly language/product content types** (`weekly_word`/`phrase`/`insult`/product),
  - **Roles & Facebook matrix** (policy-level, partially realised mechanically).
- **Explicit conflicts**, including:
  - “Scotland Today” vs Sunday Deep Dive,
  - “Product Spotlight” as both role label and Saturday focus,
  - “Deep Dive” as legacy type vs `DEPTH_LONG` role.

The recommended path forward is to:

- **Elevate Roles + Facebook matrix to the sole canonical source of daily Facebook intent**,
- **Re-map or demote `weekly_social_focus` and weekly language/product labels** to **UI decoration** or **secondary classifications**,
- **Ensure every future Mon–Sat Facebook post is role-backed** (`posting_queue.role`), with any labels (e.g. “Tartan Tuesday”) treated as surface-level presentation only.

Only after these recommendations are accepted should engineering:

- Lock the Facebook matrix implementation for Mon–Sat, and  
- Re-implement or adjust Mon–Sat generation and scheduling accordingly.

