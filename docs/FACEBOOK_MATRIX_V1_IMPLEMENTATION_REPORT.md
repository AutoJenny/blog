## Facebook Matrix v1 – Implementation Report

**Date:** 2026-01-27  
**Scope:** Facebook only (planning UIs, matrix, and intent hierarchy).  

This report documents:  
- How Facebook Matrix v1 (Mon–Sun) has been encoded as a single source of truth,  
- How planning UIs now present **Role-first, Angle-second** intent,  
- How legacy abstractions have been classified as **DRIVER / UI_ONLY / RETIRE**, and  
- Evidence that Sunday DEPTH_LONG remains rota-authoritative and weekly language posts remain in place.

---

## 1. Matrix v1 – Final Definition (Mon–Sun)

### 1.1 Conceptual Hierarchy (Locked)

All Facebook posts must be explainable by:

> **TOPIC (rota or stream) → ANGLE (variant / framing) → ROLE (editorial intent) → CHANNEL (facebook) → POST (`posting_queue`)**

- **Role** is the **primary driver** of daily intent.
- **Angle** is a secondary, reusable editorial framing (e.g. WORD / PHRASE / INSULT) that sits **inside** a Role.
- **Channel** is fixed here to **Facebook**.

### 1.2 Matrix v1 Table

Authoritative mapping (ISO weekday: 1=Mon … 7=Sun), implemented in `utils/facebook_matrix_v1.py` as `FACEBOOK_MATRIX_V1`.

| ISO Day | Day    | Role           | Expected Angle Behaviour             | Primary Topic / Source Hint                         |
|--------:|--------|----------------|--------------------------------------|-----------------------------------------------------|
| 1       | Mon    | `CULTURE`      | Fixed: `LANGUAGE: WORD`             | Weekly language pool (word); CULTURE slot           |
| 2       | Tue    | `CULTURE`      | Fixed: `LANGUAGE: PHRASE`           | Weekly language pool (phrase); CULTURE slot         |
| 3       | Wed    | `REASSURANCE`  | None (service framing only)         | Service principles / reassurance prompts            |
| 4       | Thu    | `CULTURE`      | Fixed: `LANGUAGE: INSULT`           | Weekly language pool (insult); CULTURE slot         |
| 5       | Fri    | `AUTHORITY_SHORT` | None (short assertion/context)   | Authority / provenance assertions                   |
| 6       | Sat    | `COMMERCE`     | Optional: `PRODUCT SPOTLIGHT`       | Product catalogue; soft commerce focus              |
| 7       | Sun    | `DEPTH_LONG`   | Fixed: `DEEP DIVE`                  | KB topic rota (rota-authoritative Deep Dive topic)  |

Implementation notes:

- The Matrix is encoded as `FacebookDayConfig` objects in `utils/facebook_matrix_v1.py`:
  - `role` (e.g. `"CULTURE"`),
  - `angle_hint` (e.g. `"LANGUAGE: WORD"`),
  - `topic_source_hint` (documentation-only hint for where content should draw from).
- Helper function `get_facebook_day_config(iso_weekday)` returns the config for any day, providing a single, inspectable source of truth.

**Indexing convention:** Matrix indexing uses **ISO weekday Mon=1 … Sun=7**. In JavaScript, `Date.getDay()` returns Sun=0 … Sat=6; the week-view converts via `getISOWeekday(date)`: `(date.getUTCDay() + 6) % 7 + 1` so that Mon=1 and Sun=7. The dates-line header and Social Posts row both derive the matrix key from the actual column date, not from column index alone.

---

## 2. DRIVER / UI_ONLY / RETIRE Classification

This table summarises where each relevant system now sits in the Facebook Matrix v1 world. (The detailed rationale is in `docs/PHASE_5_FACEBOOK_MATRIX_AND_UI_SOURCE_OF_TRUTH_AUDIT.md` §6.4.)

| System / Concept                          | Classification | Role in Matrix v1                                                                                                                  |
|-------------------------------------------|----------------|-------------------------------------------------------------------------------------------------------------------------------------|
| `content_roles` + `posting_queue.role`    | **DRIVER**     | Canonical representation of editorial intent per post. Facebook Matrix v1 is expressed entirely as **Role per ISO weekday**.       |
| Facebook Matrix v1 (`facebook_matrix_v1`) | **DRIVER**     | Encodes day → Role (+ Angle hints) for Facebook, used as the **single source of daily intent** at code/documentation level.       |
| Weekly language streams (`weekly_word`/`phrase`/`insult`) | **DRIVER** | Continue to define **what language content exists** each week. In Matrix v1 they are **Angles** inside CULTURE slots.             |
| Product-post scheduling (`content_type='product'` etc.) | **DRIVER** | Defines when product posts exist. Under Matrix v1 they are **COMMERCE** role posts; day placement must converge on Saturday.      |
| `weekly_social_focus` (From the Blog, Tartan Tuesday, etc.) | **UI_ONLY** | Provides optional, human-friendly **day labels** only. Role/Matrix is now primary; these labels must not drive logic.           |
| `calendar_themes` (blog themes)           | **UI_ONLY**    | Blog planning only; **explicitly not** a driver for Facebook roles or daily intent.                                                |
| Legacy Deep Dive content type / flags     | **RETIRE**     | Replaced by `DEPTH_LONG` role. Any remaining `deep_dive`-style flags are treated as deprecated and should be phased out.          |
| LANGUAGE:* labels in calendar UI          | **UI_ONLY**    | Surface-level text (e.g. “Language: Word”) now treated as **Angle** labels; primary label is always the Role.                     |

---

## 3. Planning UI Changes – Role-First, Angle-Second

### 3.1 Calendar Week View (`/planning/calendar?tab=week-view`)

#### 3.1.1 “Dates Line” (Day Headers)

**Phase 5.1 (2026-01-27):** Headers are driven only by Matrix v1 and the **actual column date**. Legacy labels (`weekly_social_focus`) are no longer read or displayed in the dates line. `renderMatrixHeaders(dates)` computes ISO weekday from each date via `getISOWeekday(date)` and shows only `ROLE` and Angle hint (e.g. `CULTURE — Language: Word`). Language placement was corrected so Phrase appears on Tuesday (day 2) and Insult on Thursday (day 4), matching the Matrix.

Files:

- `templates/planning/calendar/week_view.html`
- `static/js/planning/calendar-week-view.js`
- `blueprints/planning_api_calendar_social_focus.py` (unchanged; not used for header rendering)

Behaviour before:

- Each day header (Mon–Sun) showed only the `weekly_social_focus.social_focus` label:
  - e.g. “From the Blog”, “Tartan Tuesday”, “Workshop Wednesday”, “Scotland Today”.
- This looked like a driver for daily intent, but in practice it was **planning-only** and not tied to roles.

Behaviour now:

- **Role-first display**, with Angle and (optional) legacy label as secondary text:
  - Implemented via `FACEBOOK_MATRIX_ROLES` and `FACEBOOK_MATRIX_ANGLE_HINTS` constants in `calendar-week-view.js`.
  - The `renderSocialFocuses(focuses)` function now constructs the header text as:
    - `ROLE` (from Matrix v1),  
    - `Angle hint` (e.g. `Language: Word` for Mon),  
    - `Legacy social_focus` label (e.g. “From the Blog”),  
    joined as:  
    `CULTURE — Language: Word — From the Blog`.
- When no `weekly_social_focus` entry exists:
  - The header still shows `ROLE` (+ Angle hint if applicable),
  - Making the Matrix visible even if social focus has not been configured.
- `weekly_social_focus` remains editable via the Social Focus modal but is **confirmed as UI-only**:
  - It is not read by any scheduling, role, or generation logic.

#### 3.1.2 Social Posts Row (Cards)

Files:

- `static/js/planning/calendar-week-view.js`
- `static/js/planning/unified-item-card.js`
- `blueprints/planning_api_calendar_schedule.py`

Behaviour before:

- `renderItems()` derived a **typeName** like:
  - `language: word`, `language: phrase`, `language: insult`, `product`, `Message`, `Deep Dive`.
- `createUnifiedItemCard()` used this as the primary label in the card header, so users saw:
  - Mixed conceptual levels (LANGUAGE, PRODUCT, DEEP DIVE) rather than Roles.

Behaviour now:

- `renderItems()` implements Role-first, Angle-second labelling for Facebook-relevant categories:
  - For weekly language slots:
    - `type === 'weekly-word' / 'weekly-phrase' / 'weekly-insult'`
    - Primary Role forced to `CULTURE` (if not already set on the item),
    - Angle labels:
      - `'weekly-word'` → `Language: Word`,
      - `'weekly-phrase'` → `Language: Phrase`,
      - `'weekly-insult'` → `Language: Insult`,
    - `typeName` passed to the card is:  
      `CULTURE — Language: Word` (etc.).
  - For product posts:
    - `type === 'product'`:
      - Primary Role forced to `COMMERCE` (if not already present),
      - Angle label: `Product`,
      - `typeName`: `COMMERCE — Product`.
  - For message posts:
    - `type === 'message'`:
      - Primary Role forced to `REASSURANCE`,
      - Angle label: `Message`,
      - `typeName`: `REASSURANCE — Message`.
  - For Sunday Deep Dive:
    - `type === 'depth_long'`:
      - Primary Role forced to `DEPTH_LONG`,
      - Angle label: `Deep Dive`,
      - `typeName`: `DEPTH_LONG — Deep Dive`.
- For non-Facebook categories (themes, recipes, events), behaviour is unchanged:  
  they retain descriptive type names (Theme, Recipe, Annual/Special, etc.), as they are outside the Facebook Matrix scope.

Effect:

- Every Facebook-relevant card in the Social Posts row now answers:
  - **“What Role is this serving?”** (first), and  
  - **“What specific Angle or category within that role?”** (second),  
  instead of mixing legacy labels and implied types.

### 3.2 Content Control Board (`/planning/content-control-board`)

Files:

- `templates/planning/content_control_board.html`
- `static/js/planning/content_control_board.js`

Current behaviour (post-Phase 4 and Phase 5 alignment):

- The Control Board was already **Role-centric** for Sunday:
  - Uses `getRoleDisplayName()` and `getRoleInfo()` to present `DEPTH_LONG` as “Deep Dive” with explanatory tooltip.
- For other days:
  - The matrix view uses per-slot Role information where available to show:
    - Role badge (e.g. `CULTURE`, `COMMERCE`, `REASSURANCE`),
    - Status (generated/validated/approved/scheduled),
    - Preview button (full-page preview route).
- No day-theme labels (e.g. “Tartan Tuesday”) are used as drivers in the Control Board.

Matrix v1 alignment:

- **Roles remain the primary labels** in:
  - Day × Channel matrix cells (Facebook column),
  - Drill-down panel (Role and Status sections),
  - Sunday planning grid (DEPTH_LONG).
- Angles (e.g. language variants) can appear in:
  - Drill-down content or descriptive text,
  - But are **not** used as primary cell labels.
- No additional day-theme logic has been introduced; any such labels are now clearly subordinate to Roles and do not influence behaviour.

### 3.3 Sunday Slot Panel (`/kb-topics/editor` – Sunday Deep Dive)

Files:

- `templates/kb_topics/rota_editor.html`
- `static/js/kb_topics/sunday_slot.js`

Behaviour:

- Already tightly aligned with DEPTH_LONG:
  - Generation, validation, approval, and scheduling all go through the content roles API for Sunday, which enforces:
    - `role = 'DEPTH_LONG'`,
    - Rota topic matching via `kb_topic_rota`.
- Preview:
  - Uses the **full-page preview route** (`/preview/post/<post_id>?channel=facebook`).
- No language/content-type or weekly_social_focus logic is consulted here.

Matrix v1 impact:

- Sunday slot panel is **already compliant** with Matrix v1:
  - Role is always `DEPTH_LONG`.
  - Angle is effectively “Deep Dive” as defined by the role and its validator.

---

## 4. Evidence and Checks

### 4.1 Sunday DEPTH_LONG – Rota-Authoritative (Unaffected)

- Existing Sunday pipeline remains in place:
  - Generation endpoint checks rota topic (`kb_topic_rota`),
  - Validation enforces DEPTH_LONG rules,
  - Approval and scheduling write a `posting_queue` row with:
    - `role = 'DEPTH_LONG'`,
    - `platform = 'facebook'`,
    - Sunday `scheduled_date`, `scheduled_time = '15:00:00'`.
- Calendar week view, Content Control Board, and Sunday Slot panel all show:
  - Sunday slot as a **DEPTH_LONG Deep Dive**,  
  - With no competing product or legacy theme logic taking precedence.

### 4.2 Weekly Language Posts – Still 3× per Week

- `planning_api_calendar_schedule.py` still resolves:
  - `weekly_word`, `weekly_phrase`, `weekly_insult` via the cyclic resolver.
- Calendar week view:
  - Places:
    - Word on Monday (day 1),
    - Phrase on Wednesday (day 3),
    - Insult on Friday (day 5),
  - Now labelled as:
    - `CULTURE — Language: Word`,
    - `CULTURE — Language: Phrase`,
    - `CULTURE — Language: Insult`.
- No logic has been removed that would reduce the presence of weekly language content; only the **labelling and conceptual framing** have been updated to reflect Matrix v1.

### 4.3 No Conflicting Sources Remain Active for Facebook Daily Intent

- **Roles + Matrix v1** (`content_roles`, `posting_queue.role`, `facebook_matrix_v1`) are the **only drivers** of daily Facebook intent.
- `weekly_social_focus`:
  - Confirmed as **UI-only**:
    - Used exclusively in `renderSocialFocuses()` to add descriptive suffixes to the Role/Angle header line.
    - Not referenced in any posting, scheduling, or generation code paths.
- `calendar_themes`:
  - Remains blog-only and is not used anywhere in Facebook planning surfaces for daily intent.
- Legacy Deep Dive content-type paths:
  - Marked for retirement and superseded by Role (`DEPTH_LONG`), with UI now consistently using Role naming.

---

## 5. Summary for Stakeholders

- **Single Matrix:**  
  - Facebook now has a single, explicit Matrix v1 definition (Mon–Sun) implemented in code, docs, and UI.
- **Role-first UI:**  
  - Calendar week view and planning surfaces present **Role as the primary label** for Facebook content, with language/product/deep dive surfaced as **Angles** (secondary labels).
- **Legacy labels downgraded:**  
  - Day-theme labels like “Tartan Tuesday” and “Scotland Today” are now **decorative only**, never consulted by backend logic, and always appear **after** the Role in any composite label.
- **Sunday and language streams preserved:**  
  - Sunday DEPTH_LONG remains rota-authoritative and fully wired end-to-end.
  - Weekly language posts still appear three times per week; they are simply now framed as CULTURE-role Angles rather than pseudo-roles.

This alignment ensures that any Facebook post can now be answered with one, consistent explanation:

> **“What Role is this serving, and why is it on this day?”**  

and that answer comes from a **single Matrix and Role system**, not from a patchwork of legacy labels.

---

## 6. Addendum — Matrix v1 as scheduling source of truth (drift fix)

**Date:** 2026 (post–Phase 5.1)  
**Objective:** Make Facebook Matrix v1 the single source of truth for **what gets scheduled** each weekday, not only for headers/labels. Eliminate “truthy headers + messy reality” (extra product posts on Tue/Thu, message on Sat, empty Wed/Fri).

### 6.1 Where legacy schedulers were changed

| System | File(s) | Change |
|--------|---------|--------|
| **Schedule API (products)** | `blueprints/planning_api_calendar_schedule.py` | Product query: `ISODOW = 6` (Saturday only). Was `ISODOW != 6`. |
| **Schedule API (messages)** | `blueprints/planning_api_calendar_schedule.py` | Message query: `ISODOW = 3` (Wednesday only). Was `ISODOW = 6`. |
| **Message creator** | `scripts/automated_message_post_creator.py` | `publication_day = 3` (Wednesday); `get_next_publication_days()` replaces `get_next_saturdays()`; new message rows get `role = 'REASSURANCE'`. |
| **Product creator** | `scripts/automated_product_post_creator.py` | For `platform == 'facebook'`, `get_active_schedules()` overrides `days` to `[6]` (Saturday only). New product rows get `role = 'COMMERCE'`. |
| **Week-view message rendering** | `static/js/planning/calendar-week-view.js` | Message posts render on their `scheduled_date` weekday (Matrix v1: Wednesday), not hard-coded Saturday. |
| **UI role masking removed** | `static/js/planning/calendar-week-view.js` | No overwriting of `primaryRole` for product/message/language/depth_long; display uses `item.role` or `"UNSET_ROLE"` plus content_type. See `docs/DELIVERABLE_C_UI_OVERRIDES_REMOVED.md`. |
| **Backfill** | `scripts/backfill_matrix_v1_week.py` | For a given ISO week: move message Sat→Wed, products non-Sat→Sat, set roles, update `post_type_channel_config` message to `publication_day = 3`. See `docs/DELIVERABLE_D_BACKFILL.md`. |

### 6.2 Matrix v1 scheduling source of truth (Facebook)

- **Mon:** CULTURE (Language: Word) — 1 item. Driven by cyclic resolver + weekly language creator.
- **Tue:** CULTURE (Language: Phrase) — 1 item. Same.
- **Wed:** REASSURANCE (Message) — 1 item. Driven by `automated_message_post_creator` (publication_day=3) and schedule API `ISODOW = 3`.
- **Thu:** CULTURE (Language: Insult) — 1 item. Same as Mon/Tue.
- **Fri:** AUTHORITY_SHORT — 1 item. Schedule API returns role-based posts by `scheduled_date`; creation path (authority_short scheduler) is out of scope for this pass.
- **Sat:** COMMERCE (Product) — 1 item. Driven by `automated_product_post_creator` (Facebook days overridden to [6]) and schedule API `ISODOW = 6`.
- **Sun:** DEPTH_LONG (Deep Dive) — 1 item. Unchanged; rota-authoritative.

No parallel “product days” or “message day” logic remains for Facebook: product/message scheduling is gated by Matrix v1 weekday mapping in the code paths above.

### 6.3 Verification checklist

1. **Week-view:** Screenshot of headers + Social Posts row for 2026-W5 showing one item per day and roles matching matrix (no Tue/Thu products, Sat product only, Wed message only). After backfill, Fri may still be empty until an authority_short creator exists.
2. **Schedule API:** Capture `/planning/api/calendar/schedule/2026/5` and confirm each item has the expected `role` and `scheduled_date` (products on Sat, messages on Wed).
3. **Docs:** This addendum; `DELIVERABLE_A_MATRIX_GROUND_TRUTH.md`, `DELIVERABLE_B_CALL_CHAIN_MAP.md`, `DELIVERABLE_C_UI_OVERRIDES_REMOVED.md`, `DELIVERABLE_D_BACKFILL.md`.

---

## 7. Role enforcement (Phase 6)

**Objective:** Every Facebook social post must have an explicit `posting_queue.role`; no item should appear as "UNSET_ROLE". REASSURANCE (message) must appear on Wednesday.

### 7.1 Canonical role assignment (Matrix v1)

| content_type / source | Role |
|------------------------|------|
| weekly_word / weekly_phrase / weekly_insult | CULTURE |
| message | REASSURANCE |
| product | COMMERCE |
| depth_long | DEPTH_LONG |

No inference beyond this table.

### 7.2 Enforcement at creation time

- **Weekly language:** `utils/posting_queue_helpers.create_weekly_social_post` inserts `role = 'CULTURE'`. Schedule API appends `role: 'CULTURE'` for weekly_word/phrase/insult items (resolver-based).
- **Message:** `scripts/automated_message_post_creator` inserts `role = 'REASSURANCE'`; `publication_day = 3` (Wednesday).
- **Product:** `scripts/automated_product_post_creator` inserts `role = 'COMMERCE'`.
- **depth_long:** Already set by content-roles / Sunday-slot path.

### 7.3 Schedule API surfacing role

Product and message queries in `planning_api_calendar_schedule` select `pq.role` and include `role` in the appended schedule item so the week-view receives it and does not show "UNSET_ROLE" when role is set.

### 7.4 REASSURANCE on Wednesday

- **Creation:** Message creator schedules on Wednesday and sets `role = 'REASSURANCE'`.
- **Visibility:** Schedule API filters messages to `ISODOW = 3` (Wednesday). Week-view places message items by `scheduled_date` weekday. If an existing message is on Saturday, run `scripts/backfill_matrix_v1_week.py --week 2026-W5` to move it to Wednesday and set `role = 'REASSURANCE'`; it then appears in the calendar.
- **Proof:** For 2026-W5, report `docs/PHASE6_ROLE_AND_MESSAGE_REPORT_2026W5.txt` shows one message (id 4631) with `scheduled_date` 2026-01-31 (Saturday), `status` ready, `role` NULL. After `backfill_matrix_v1_week.py --week 2026-W5`, that row has Wednesday date and role REASSURANCE and is returned by the schedule API.

### 7.5 Backfill for existing NULL roles

- **Script:** `scripts/backfill_facebook_role_null.py`
- **Mapping:** content_type → role as in §7.1.
- **Dry-run:** `python3 scripts/backfill_facebook_role_null.py --dry-run` to log every change without writing.
- **Apply:** `python3 scripts/backfill_facebook_role_null.py` to set role on all Facebook rows where role IS NULL and content_type in (weekly_word, weekly_phrase, weekly_insult, product, message, depth_long).
- **Verification:** After run, query `posting_queue` for `platform = 'facebook'` and `content_type IN (...)` and `role IS NULL` — result should be zero rows.

---

## 8. Friday AUTHORITY_SHORT — production-grade and preview parity (2026-01-28)

**Objective:** Friday AUTHORITY_SHORT is editorially complete (rota/KB sourced, Ollama-generated, mechanically validated), lands as `status = 'ready'`, and preview shows source provenance and validator output. Preview and publish use the same formatter (parity proven).

### 8.1 Friday slot (production-grade)

- **Creation:** `scripts/automated_authority_short_creator.py` — one post per Friday (15:00), `role = 'AUTHORITY_SHORT'`, `content_type = 'authority_short'`. Source: rota topic for ISO week (preferred), then KB topic article, then fallback article. Generator: `utils/content_roles/authority_short_generator.py` (Ollama, mechanical validation, 3-attempt loop, hard fail with `validation_report_json`: attempts, failed_rules, source_used).
- **Lifecycle:** On successful generation + validation → `status = 'ready'`. On failure → `status = 'failed'`; `validation_report_json` persisted for audit.
- **Provenance:** `posting_queue` row stores `topic_id`, `source_page_id`, `rota_year`, `rota_week`, `validation_report_json` (including `source_used`, `source_excerpt`, `failed_rules`).

### 8.2 Preview parity and reviewer visibility

- **Parity:** Facebook preview uses the same formatter as publish (`utils.platform_publishers.format_message_for_facebook` via `utils/channel_preview/formatters/facebook.py`). Proof: `scripts/prove_preview_publish_parity.py` — 3/3 PASS for AUTHORITY_SHORT (15505), DEPTH_LONG (11823), weekly_word (667). Report: `docs/PARITY_PROOF_FACEBOOK_YYYYMMDD.txt`.
- **Canonical template:** `templates/channel_previews/facebook_feed.html` used by `/api/preview/post/<id>?channel=facebook` and `/preview/post/<id>?channel=facebook`. Template shows: role/status/char count; formatted post text; **Validator warnings** (when `validation_failed_rules` non-empty); collapsible **Source** (type, topic ID, article ID, source excerpt from `validation_report_json`).
- **No fallback snippet:** Invalid channel returns JSON `success: false`, `error_code: INVALID_CHANNEL`; no generic HTML.

### 8.3 Evidence and regression guards

- Schedule: `docs/SCHEDULE_EXCERPT_2026_W5_FRIDAY_ONLY_15505.json` — exactly one Friday AUTHORITY_SHORT (id 15505).
- Preview: `docs/PREVIEW_API_15505.json`, `docs/PREVIEW_PAGE_15505_HEAD.html`, `docs/PREVIEW_INVALID_CHANNEL_15505.json`.

