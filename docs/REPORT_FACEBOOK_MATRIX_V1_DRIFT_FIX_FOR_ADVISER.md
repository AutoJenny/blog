# Report: Facebook Matrix v1 Drift Fix — Full Deliverables for Adviser

**Prepared for:** Adviser  
**Subject:** Work completed since receipt of the “Fix Facebook Matrix v1 drift” instructions  
**Scope:** Make Facebook Matrix v1 the single source of truth for both headers/labels and what gets scheduled each weekday in the Social Posts row.

---

## 1. Instructions Received

The coder was given a structured briefing to fix the drift between **Matrix v1 headers** (which were correct) and **scheduled items** (which still followed legacy rules). The problem was summarised as “truthy headers + messy reality”:

- **Tue/Thu:** extra product posts (legacy “product days”)
- **Sat:** reassurance message (legacy “message day” = Saturday)
- **Wed/Fri:** nothing scheduled (empty)

**Target behaviour (Matrix v1):**

| Day | Role | Content | Count |
|-----|------|---------|-------|
| Mon | CULTURE | Language: Word | 1 |
| Tue | CULTURE | Language: Phrase | 1 |
| Wed | REASSURANCE | Message | 1 |
| Thu | CULTURE | Language: Insult | 1 |
| Fri | AUTHORITY_SHORT | — | 1 |
| Sat | COMMERCE | Product Spotlight | 1 |
| Sun | DEPTH_LONG | Deep Dive | 1 |

**Non-goals for this pass:** No redesign of preview/angles/roles; no new channels; no new post formats.

---

## 2. Work Completed (Phases 5–7)

### Step 1 — Establish Ground Truth (DB-first)

**Objective:** For week 2026-W5 (and sources), produce the exact data the calendar week-view uses: posting_queue, language streams, product scheduling source, message/reassurance scheduling source.

**Delivered:**

- **Script:** `scripts/step1_matrix_ground_truth.py`  
  - Runs the briefing’s posting_queue SQL (Facebook, 2026-01-26..2026-02-01).  
  - Runs SQL for weekly language (`calendar_ideas`, `calendar_category_cycles`).  
  - Runs SQL for product config (`post_type_channel_config`, `daily_posts_schedule`).  
  - Runs SQL for message config and references `scripts/automated_message_post_creator.py`.

- **Command:**  
  `python3 scripts/step1_matrix_ground_truth.py --week 2026-W5`  
  Optional: `--out <path>` to write to a file.

- **Document:** `docs/DELIVERABLE_A_MATRIX_GROUND_TRUTH.md`  
  - Exact SQL used.  
  - Summary of 2026-W5: 21 posting_queue rows; products on Tue/Thu/Sat; message on Sat; no authority on Fri; language items present.  
  - Identification of sources: product weekdays from `daily_posts_schedule` (e.g. [2,4] and [7]); message from `publication_day = 6` in config and hardcoded Saturday in the message creator.

**Findings:** Product “weekdays” were Tue/Thu (and Sun in one schedule); message was Saturday-only in both config and code. Matrix v1 requires product on Saturday only and message on Wednesday only.

---

### Step 2 — Call-Chain Map (Week-View Schedule)

**Objective:** For `/planning/calendar?year=2026&week=5&tab=week-view`, document which backend endpoints and frontend logic supply and bucket schedule items by day.

**Delivered:**

- **Document:** `docs/DELIVERABLE_B_CALL_CHAIN_MAP.md`  
  - Backend: `GET /planning/api/calendar/schedule/<year>/<week_number>`, implemented in `blueprints/planning_api_calendar_schedule.py` (`api_calendar_schedule`).  
  - For each of products, messages, language, depth_long: which query/function returns them and where day filtering/bucketing happens (backend SQL vs frontend).  
  - Frontend: `static/js/planning/calendar-week-view.js` — `loadWeek()` fetches the schedule API; day buckets are `social-posts-row-day-1` … `social-posts-row-day-7`; word/phrase/insult go to fixed slots (1, 2, 4); products and messages go by `scheduled_date`; role-based posts by `scheduled_date`.  
  - Location of client-side “force role” logic: `renderItems()` ~L186–231, overwriting `primaryRole` when `item.role` was null (addressed in Step 3).

---

### Step 3 — Remove UI-Only Masking

**Objective:** Stop overwriting `primaryRole` for product/message/language/depth_long in the calendar renderer. Show the role actually on the item or “UNSET_ROLE” plus content_type/category.

**Delivered:**

- **Code change:** `static/js/planning/calendar-week-view.js`  
  - Removed `primaryRole = primaryRole || 'CULTURE'` (and similar) for weekly-word/phrase/insult, product, message, depth_long.  
  - Introduced `displayRole = item.role || 'UNSET_ROLE'` and use it only for the visible label (e.g. `"UNSET_ROLE — Product"`, `"REASSURANCE — Message"` when role is set).  
  - `primaryRole` is no longer overwritten; it stays `item.role || null`.

- **Document:** `docs/DELIVERABLE_C_UI_OVERRIDES_REMOVED.md`  
  - List of overrides removed and where (file/function).  
  - Short description of new behaviour.

---

### Step 4 — Make Scheduling Matrix-Driven

**Objective:** Use Matrix v1 for when products, messages, and (where applicable) authority_short are scheduled. Concretely: product only on Saturday; message only on Wednesday; authority_short on Friday (creation path out of scope).

**Delivered:**

1. **Schedule API** (`blueprints/planning_api_calendar_schedule.py`)
   - Products: filter changed from “exclude Saturday” to “Saturday only”: `EXTRACT(ISODOW FROM pq.scheduled_date) = 6`.
   - Messages: filter changed from “Saturday only” to “Wednesday only”: `EXTRACT(ISODOW FROM pq.scheduled_date) = 3`.

2. **Message creator** (`scripts/automated_message_post_creator.py`)
   - `publication_day` set to `3` (Wednesday).  
   - `get_next_saturdays()` replaced by `get_next_publication_days()` using `self.publication_day`.  
   - New message rows insert `role = 'REASSURANCE'`.

3. **Product creator** (`scripts/automated_product_post_creator.py`)
   - In `get_active_schedules(platform)`, when `platform == 'facebook'`, each schedule’s `days` is overridden to `[6]` (Saturday only).  
   - New product rows insert `role = 'COMMERCE'`.

4. **Week-view frontend** (`static/js/planning/calendar-week-view.js`)
   - Message posts are placed by `scheduled_date` weekday (no longer hard-coded to Saturday). When the API only returns Wed messages, they appear on Wednesday.

5. **Authority_short (Friday)**  
   - Schedule API already returns role-based posts by `scheduled_date`; any row with `role = 'AUTHORITY_SHORT'` and Friday would be shown.  
   - No authority_short *creator* was added in this pass (explicitly out of scope).

---

### Step 5 — Backfill Script for Existing Weeks

**Objective:** Provide a script that, for a given ISO week, reassigns Facebook items to Matrix v1 weekdays and updates config so week-view matches the matrix without manual edits.

**Delivered:**

- **Script:** `scripts/backfill_matrix_v1_week.py`  
  - For each message in that week with `scheduled_date` on Saturday: set `scheduled_date` to Wednesday of that week, `scheduled_timestamp` accordingly, and `role = 'REASSURANCE'`.  
  - For each product in that week with `scheduled_date` not on Saturday: set `scheduled_date` to Saturday of that week, keep time where sensible, and `role = 'COMMERCE'`.  
  - Updates `post_type_channel_config`: `publication_day = 3` for `channel = 'facebook'` and `post_type = 'message'`.  
  - Does not create missing Wed message or Fri authority rows; it only reassigns existing ones and updates config.

- **Command for 2026-W5:**  
  `python3 scripts/backfill_matrix_v1_week.py --week 2026-W5`  
  Dry-run:  
  `python3 scripts/backfill_matrix_v1_week.py --week 2026-W5 --dry-run`

- **Document:** `docs/DELIVERABLE_D_BACKFILL.md`  
  - Script path, exact command, and the same before/after SQL as in Step 1.

---

### Step 6 — Verification and Docs Addendum (end of initial drift-fix)

**Objective:** Confirm Matrix v1 as the scheduling source of truth and document where legacy logic was changed.

**Delivered:**

- **Addendum to implementation report:** `docs/FACEBOOK_MATRIX_V1_IMPLEMENTATION_REPORT.md` — new §6:
  - **§6.1** Table of where legacy schedulers were changed (schedule API, message creator, product creator, week-view rendering, UI masking, backfill script).  
  - **§6.2** Statement that Matrix v1 is the scheduling source of truth for Facebook (day-by-day role/content).  
  - **§6.3** Verification checklist: week-view screenshot, schedule API response, docs update.

- **CHANGELOG:** `docs/CHANGELOG.md` updated with an entry for “Facebook Matrix v1 scheduling drift fix,” listing changed components and new deliverables.

---

### Follow-Up: Schedule API Response and Dedupe

**Context:** The instructions had noted that the coder could “paste one network response payload from the calendar schedule API for week 5” to diagnose wrong/missing fields. The adviser questioned why the coder would ask the user to share that when the coder could obtain it.

**Actions taken:**

1. **Fetching the schedule API without a running server**
   - **Script:** `scripts/fetch_schedule_api_response.py`  
     - Uses Flask test client to call `GET /planning/api/calendar/schedule/2026/5`.  
     - Prints JSON (and can be run with logs suppressed).  
   - The schedule API response for 2026-W5 was obtained and inspected.

2. **Findings from the response**
   - Products: three items, all `scheduled_date: "2026-01-31"` (Saturday) — correct for Matrix v1.  
   - Messages: zero items — correct, because the API now only returns Wednesday messages and the existing message was still on Saturday in the DB until backfill.  
   - Role-based: one DEPTH_LONG on 2026-02-01 (Sunday) — correct.  
   - One posting_queue row (product with `role = 'COMMERCE'`) appeared twice: once as `type: "product"` and once as `type: "commerce"` from the role_posts query.

3. **Duplicate removed**
   - In `blueprints/planning_api_calendar_schedule.py`, the “role-based posts” query now excludes rows already covered by product/message:  
     `AND pq.content_type NOT IN ('product', 'message')`.  
   - Product and message rows are only returned by their own queries; each posting_queue row appears at most once in the schedule.

4. **Record of the response**
   - A summary of the captured schedule structure is in `docs/SCHEDULE_API_RESPONSE_2026_W5.json`.  
   - To regenerate the full response:  
     `python3 scripts/fetch_schedule_api_response.py`  
     (script currently hardcodes 2026/5).

---

## 3. Complete List of Deliverables

| Item | Type | Path |
|------|------|------|
| Step 1 ground-truth script | Script | `scripts/step1_matrix_ground_truth.py` |
| Step 1 report | Doc | `docs/DELIVERABLE_A_MATRIX_GROUND_TRUTH.md` |
| Call-chain map | Doc | `docs/DELIVERABLE_B_CALL_CHAIN_MAP.md` |
| UI overrides removed | Doc | `docs/DELIVERABLE_C_UI_OVERRIDES_REMOVED.md` |
| Backfill script | Script | `scripts/backfill_matrix_v1_week.py` |
| Backfill instructions | Doc | `docs/DELIVERABLE_D_BACKFILL.md` |
| Implementation report addendum | Doc | `docs/FACEBOOK_MATRIX_V1_IMPLEMENTATION_REPORT.md` (§6) |
| Schedule API fetch script | Script | `scripts/fetch_schedule_api_response.py` |
| Schedule API sample (2026-W5) | Doc | `docs/SCHEDULE_API_RESPONSE_2026_W5.json` |
| CHANGELOG entry | Doc | `docs/CHANGELOG.md` |

**Code/behaviour changes:**

- `blueprints/planning_api_calendar_schedule.py` — products Saturday-only, messages Wednesday-only; role_posts exclude product/message.
- `scripts/automated_message_post_creator.py` — publication_day=3, get_next_publication_days(), role=REASSURANCE on insert.
- `scripts/automated_product_post_creator.py` — Facebook product days overridden to [6], role=COMMERCE on insert.
- `static/js/planning/calendar-week-view.js` — UI role overrides removed (show actual role or “UNSET_ROLE”); messages placed by scheduled_date weekday.

---

## 4. How to Verify (For Adviser or QA)

1. **Run Step 1 (before backfill)**  
   `python3 scripts/step1_matrix_ground_truth.py --week 2026-W5`  
   Inspect posting_queue: products/message on legacy days.

2. **Run backfill for 2026-W5**  
   `python3 scripts/backfill_matrix_v1_week.py --week 2026-W5`  
   (Use `--dry-run` first if desired.)

3. **Run Step 1 again (after backfill)**  
   Same command as in (1).  
   Confirm message on Wed, products on Sat, roles REASSURANCE/COMMERCE where updated.

4. **Fetch schedule API**  
   `python3 scripts/fetch_schedule_api_response.py`  
   Confirm: products only on 2026-01-31 (Sat), one DEPTH_LONG on 2026-02-01 (Sun), no duplicate rows, messages only if/when a Wed message exists.

5. **Week-view in browser**  
   Open `/planning/calendar?year=2026&week=5&tab=week-view`.  
   After backfill: Sat shows products only; Wed shows message; Sun shows Deep Dive; labels show actual role or “UNSET_ROLE” (no forced role).

---

## 5. Current State and Limits

- **Matrix v1 as scheduling source of truth:** Implemented for Facebook for product (Sat), message (Wed), and language (Mon/Tue/Thu). Sunday DEPTH_LONG unchanged.  
- **Friday AUTHORITY_SHORT:** Schedule API will show any posting_queue row with `role = 'AUTHORITY_SHORT'` on its `scheduled_date`. No authority_short *creator* was built in this pass, so Friday remains empty until that exists.  
- **Config:** Backfill updates `post_type_channel_config` so message has `publication_day = 3`. Product “day” for Facebook is overridden in code to Saturday only, not by DB config.  
- **No parallel Facebook product/message logic:** Product and message scheduling for Facebook are driven only by the Matrix v1 rules in the code paths above.

---

## 6. Summary for Adviser

---

## 3. Phase 6 — Role Enforcement & REASSURANCE on Wednesday

After the initial drift-fix, Phase 6 closed two structural gaps:

1. **UNSET_ROLE:** Many Facebook social posts (weekly language, product, message) had `posting_queue.role = NULL`. The week-view correctly surfaced this as “UNSET_ROLE”, revealing that Matrix v1 was not enforced at the data level.  
2. **Missing REASSURANCE:** The schedule API filtered messages to Wednesday (Matrix v1), but the only message for 2026-W5 was still on Saturday, so no message appeared in the grid.

### 3.1 Data-level role enforcement

- **Canonical mapping** (Matrix v1):  
  - `weekly_word` / `weekly_phrase` / `weekly_insult` → `CULTURE`  
  - `message` → `REASSURANCE`  
  - `product` → `COMMERCE`  
  - `depth_long` → `DEPTH_LONG`
- **At creation time:**
  - `utils/posting_queue_helpers.create_weekly_social_post` now inserts `role = 'CULTURE'` for weekly language posts.
  - `scripts/automated_message_post_creator` inserts `role = 'REASSURANCE'` (and `publication_day = 3`, Wednesday).
  - `scripts/automated_product_post_creator` inserts `role = 'COMMERCE'`.
- **Schedule API:**  
  - Product and message queries select and return `pq.role` so the UI no longer has to infer roles.  
  - Resolver-based weekly language schedule items (Word/Phrase/Insult) include `role: 'CULTURE'`.
- **Backfill for historical rows:**  
  - `scripts/backfill_facebook_role_null.py` assigns roles to all existing Facebook rows where `role IS NULL` and `content_type IN ('weekly_word','weekly_phrase','weekly_insult','product','message','depth_long')`.  
  - After running this, there are zero role-less rows for the relevant types.

### 3.2 Restoring REASSURANCE on Wednesday

- For 2026-W5, the report script `scripts/phase6_role_and_message_report.py` showed one Facebook `message` row (id 4631) on **Saturday** with `role = NULL`.  
- The Matrix week backfill (`scripts/backfill_matrix_v1_week.py --week 2026-W5`) now:
  - Moves that message from Saturday → Wednesday of the same week.
  - Sets `role = 'REASSURANCE'`.
  - Keeps the date/time consistent with the Wednesday rail.
- The schedule API (which already filters messages to `ISODOW = 3`) now returns that row, and the week-view renders a single REASSURANCE card on Wednesday for Facebook.

---

## 4. Phase 7 — Weekly Language De-duplication & Friday Completion

Phase 7 addressed two remaining issues:

1. **Weekly language duplication:** Weekly language was appearing twice in the Social Posts row: once from the Matrix resolver (Word/Phrase/Insult) and again from weekly-language `posting_queue` rails that had been given `role = 'CULTURE'`.  
2. **Empty Friday slot:** Matrix v1 requires an `AUTHORITY_SHORT` slot on Friday; structurally, that role had not yet been wired end-to-end.

### 4.1 Weekly language de-duplication

Design principle: **Matrix slots are authoritative; workflow rails must not echo them.**

- Resolver-based items for weekly language (`weekly_word`,`weekly_phrase`,`weekly_insult`) remain the **only visible** CULTURE language cards in the grid:
  - Mon: Word  
  - Tue: Phrase  
  - Thu: Insult
- Weekly-language `posting_queue` rows still exist and are used for:
  - generation,  
  - approval,  
  - preview,  
  - publishing,  
  but they are **not** surfaced as extra CULTURE cards in week view.
- Implementation:
  - The role-based query in `blueprints/planning_api_calendar_schedule.py` now excludes weekly-language content types, alongside product and message:

    ```sql
    AND pq.content_type NOT IN (
      'product',
      'message',
      'weekly_word',
      'weekly_phrase',
      'weekly_insult'
    )
    ```

  - Frontend (`calendar-week-view.js`) simply renders what the schedule API returns; no new masking logic has been added.

### 4.2 Friday AUTHORITY_SHORT completion

- A minimal **AUTHORITY_SHORT rail** was introduced for Facebook:
  - New script: `scripts/automated_authority_short_creator.py`.
  - For upcoming Fridays, if no `posting_queue` row exists with:
    - `platform = 'facebook'`  
    - `role = 'AUTHORITY_SHORT'`  
    - `scheduled_date = <Friday>`  
    - `status != 'failed'`  
    then the script inserts a placeholder AUTHORITY_SHORT post:
    - `role = 'AUTHORITY_SHORT'`  
    - `platform = 'facebook'`  
    - `channel_type = 'feed_post'`  
    - `content_type = 'authority_short'`  
    - `generated_content` = short factual/placeholder statement  
    - `scheduled_date` = Friday  
    - `scheduled_time` = 15:00 (UK)  
    - `status = 'draft'`
- These posts are surfaced via the existing role-based branch in the schedule API and appear:
  - as a single AUTHORITY_SHORT card on **Friday** in week view,  
  - in the Friday/Facebook cell of the Content Control Board,  
  - with normal preview behaviour (same pipeline as other posting_queue-driven posts).

---

## 5. Current State (Post–Phase 7)

For Facebook, after Phases 5–7:

- **Mon:** CULTURE — Language: Word (resolver-driven; posting_queue rails exist but are workflow-only).  
- **Tue:** CULTURE — Language: Phrase.  
- **Wed:** REASSURANCE — Message (exactly one, from message creator / backfill).  
- **Thu:** CULTURE — Language: Insult.  
- **Fri:** AUTHORITY_SHORT — one short authority/context post (from the new AUTHORITY_SHORT creator).  
- **Sat:** COMMERCE — Product Spotlight (grouped view of posting_queue products with `role = 'COMMERCE'`).  
- **Sun:** DEPTH_LONG — Deep Dive, rota-authoritative.

Weekly language now appears **once and only once** per Matrix day in the grid, Friday is no longer structurally empty, and `posting_queue.role` is consistently enforced and surfaced for all relevant Facebook posts.

---

## 6. Editorial hardening (2026-01-28)

Friday AUTHORITY_SHORT is now **production-grade** and **preview parity** is locked:

- **Mechanical validation:** Rule-enumerated checks (emoji, hashtag, CTA deny-list, 1–2 paragraphs, 200–400 chars, no list formatting); 3-attempt loop; on failure `status = 'failed'` with `validation_report_json` (attempts, failed_rules, source_used).
- **Lifecycle:** Compliant output → `status = 'ready'`; week-view shows Friday as Ready.
- **Provenance:** `topic_id`, `source_page_id`, `rota_year`, `rota_week`, `source_excerpt` in validation report; preview template shows collapsible Source and Validator warnings.
- **Parity:** `docs/PARITY_PROOF_FACEBOOK_YYYYMMDD.txt` — 3/3 PASS (AUTHORITY_SHORT 15505, DEPTH_LONG 11823, weekly_word 667). Evidence artifacts in `docs/` (schedule excerpt, preview API/page, invalid-channel response).
