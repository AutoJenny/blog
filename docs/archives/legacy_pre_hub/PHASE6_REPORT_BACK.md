# Phase 6 — Facebook Matrix v1 Completion: Report-Back

**What was broken**

1. **UNSET_ROLE:** Many Facebook social posts (language, product, message) had `posting_queue.role = NULL`. The calendar correctly showed "UNSET_ROLE" instead of masking it, so Matrix v1 was not enforced at data level.
2. **Missing REASSURANCE on Wednesday:** The schedule API correctly returned only Wednesday messages (Matrix v1), but the existing message for 2026-W5 was scheduled on Saturday. So zero messages appeared for that week, and Matrix v1’s “one REASSURANCE on Wed” was not visible.

**What was changed**

**O1 — Every Facebook social post has an explicit role**

- **Canonical mapping:** weekly_word / weekly_phrase / weekly_insult → CULTURE; message → REASSURANCE; product → COMMERCE; depth_long → DEPTH_LONG.
- **Creation time:**
  - `utils/posting_queue_helpers.create_weekly_social_post` inserts `role = 'CULTURE'`.
  - `scripts/automated_message_post_creator` already inserted `role = 'REASSURANCE'` (drift fix).
  - `scripts/automated_product_post_creator` already inserted `role = 'COMMERCE'` (drift fix).
- **Schedule API:** Product and message queries select and return `role`; weekly_word/phrase/insult items from the resolver are emitted with `role: 'CULTURE'` so the UI never shows "UNSET_ROLE" for those when the payload is used.
- **Backfill:** `scripts/backfill_facebook_role_null.py` sets role on existing rows where role IS NULL using the mapping above. Dry-run: `python3 scripts/backfill_facebook_role_null.py --dry-run`. Apply: `python3 scripts/backfill_facebook_role_null.py`.

**O2 — REASSURANCE on Wednesday**

- **Existence:** For 2026-W5, `scripts/phase6_role_and_message_report.py` shows one Facebook message (id 4631): `scheduled_date` 2026-01-31 (Saturday), `status` ready, `role` NULL. So the message existed but on the wrong day and without role.
- **Creation logic:** Message creator already uses `publication_day = 3` (Wednesday) and inserts `role = 'REASSURANCE'` (drift fix).
- **Visibility:** Schedule API returns only Wed messages (`ISODOW = 3`). Week-view places messages by `scheduled_date`. To make the existing 2026-W5 message visible on Wednesday, run:  
  `python3 scripts/backfill_matrix_v1_week.py --week 2026-W5`  
  That moves the message from Sat to Wed and sets `role = 'REASSURANCE'`; it then appears in the calendar under Wednesday.

**What is now guaranteed**

1. **Role at creation:** New Facebook posts from the weekly-language, message, and product creators are inserted with the correct role (CULTURE, REASSURANCE, COMMERCE). The schedule API surfaces role for product, message, and weekly language so the week-view can show it.
2. **Backfill:** After `backfill_facebook_role_null.py`, no Facebook row in the relevant content types should have role NULL. After `backfill_matrix_v1_week.py` for a given week, that week’s message is on Wednesday with role REASSURANCE and is visible in the calendar.
3. **Verification:**  
   - O1: Query `posting_queue` where `platform = 'facebook'` and `content_type IN ('weekly_word','weekly_phrase','weekly_insult','product','message','depth_long')` and `role IS NULL` → expect 0 rows after role backfill.  
   - O2: For 2026-W5, after `backfill_matrix_v1_week.py`, the schedule API returns one message with `scheduled_date` on Wednesday and `role` REASSURANCE; week-view shows it under Wednesday.

**Deliverables**

- `scripts/phase6_role_and_message_report.py` — O1 Step 1 (role-less list) and O2 Step 1 (message posts for test week).
- `docs/PHASE6_ROLE_AND_MESSAGE_REPORT_2026W5.txt` — Saved report for 2026-W5.
- `scripts/backfill_facebook_role_null.py` — Backfill role where NULL; dry-run required.
- `docs/FACEBOOK_MATRIX_V1_IMPLEMENTATION_REPORT.md` — New §7 “Role enforcement (Phase 6)” and confirmation that REASSURANCE is live and visible on Wednesday once the week backfill is run.
