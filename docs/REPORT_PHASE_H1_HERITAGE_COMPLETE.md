# Phase H1 — HERITAGE (Thursday) Implementation Report

**Status:** Complete  
**Date:** 2026-01-29

---

## 1. Short confirmation

Phases A–H are complete. Thursday HERITAGE (`heritage_fact`) is implemented at full parity with CULTURE (`culture_fact`), fixed to Thursday, with preview == publish and 90-day repeat avoidance.

---

## 2. File list (all files touched)

| File | Change |
|------|--------|
| `migrations/20260129_add_heritage_library_id_to_posting_queue.sql` | Already present; applied to DB |
| `migrations/20260129_add_heritage_to_content_roles.sql` | **New** — INSERT HERITAGE into `content_roles` |
| `utils/content_roles/heritage_generator.py` | **Existing** — no change this session |
| `scripts/automated_heritage_creator.py` | **New** — Thursday-only creator |
| `scripts/automated_culture_creator.py` | **Modified** — Monday only (iter_monday_dates, CULTURE_DAYS = (1,)); added `Optional` import |
| `scripts/scheduled_posting_executor.py` | **Modified** — `culture_fact`: (1,); added `heritage_fact`: (4,) |
| `utils/platform_publishers.py` | **Modified** — `heritage_fact` in text-only path with `message` / `culture_fact` |
| `utils/channel_preview/preview_renderer.py` | **Modified** — SELECT `heritage_library_id`; category from `heritage_library` for `heritage_fact` |
| `scripts/prove_preview_publish_parity.py` | **Modified** — `--heritage` flag → `docs/PARITY_PROOF_FACEBOOK_HERITAGE_YYYYMMDD.txt` |
| `blueprints/planning_api_calendar_schedule.py` | **Modified** — Comment only: Thursday HERITAGE, Monday CULTURE |
| `docs/PARITY_PROOF_FACEBOOK_HERITAGE_20260129.txt` | **New** — Parity proof output |
| `docs/REPORT_PHASE_H1_HERITAGE_COMPLETE.md` | **New** — This report |

---

## 3. Confirmation

- **No CULTURE logic was altered** beyond restricting CULTURE to Monday only (creator and executor map). CULTURE generator, publish path, and preview path are unchanged.
- **No execution logic was altered** beyond the weekday map in `scheduled_posting_executor.py`: `culture_fact` → (1,), `heritage_fact` → (4,).

---

## 4. Parity proof file path

`docs/PARITY_PROOF_FACEBOOK_HERITAGE_20260129.txt`

All three IDs (heritage_fact, culture_fact, weekly_language) = PASS; byte-for-byte parity for preview vs publish formatting.

---

## 5. One-sentence confirmation

**Thursday HERITAGE is now production-ready and repeat-safe.**

---

## Acceptance summary

| Phase | Acceptance | Result |
|-------|-------------|--------|
| H1.A | Migration exists; no data mutated; no other schema touched | ✅ `heritage_library_id` column + index; HERITAGE role in `content_roles` |
| H1.B | Generator stable for same week; 90-day exclusion; no side effects | ✅ `heritage_generator.py` (pre-existing) |
| H1.C | Running script twice does not duplicate; Thursdays only | ✅ Idempotent; Thursday-only iteration |
| H1.D | heritage_fact Thursday; other weekdays blocked; no change to other types | ✅ Map updated |
| H1.E | Thursday shows HERITAGE; one card; no culture/language leak | ✅ Role-based query returns HERITAGE; comment updated |
| H1.F | heritage_fact publishes; output matches preview | ✅ Text-only path in `platform_publishers.py` |
| H1.G | Preview renders; category label; no preview-only formatting differences | ✅ Renderer + existing template category block |
| H1.H | All three parity = PASS; byte-for-byte | ✅ Proof file written |

No further refinement (angles, images, Instagram, analytics) has been done; none will be done without a new brief.
