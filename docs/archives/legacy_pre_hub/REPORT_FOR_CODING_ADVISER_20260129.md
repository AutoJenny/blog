# Report for Coding Adviser — Work Since Last Instructions

**Date:** 2026-01-29  
**Purpose:** Summary of everything implemented since the last adviser briefs (re-brief, Phase B, Phase B.2), plus doc/kb updates.

---

## 1. Context (fixed and agreed before this work)

The following were already signed off and remain frozen:

- **Facebook Matrix v1** — Complete and frozen. Weekday roles: Mon/Thu CULTURE, Tue CULTURE (language), Wed REASSURANCE (message), Fri AUTHORITY_SHORT, Sat COMMERCE (product), Sun DEPTH_LONG.
- **Execution refactor** — Centralized date-sensitive publishing via `scheduled_posting_executor.py`; `platform_publishers.publish_to_facebook(queue_id)`; workflows set `status='ready'` only; no date logic in platform code. Frozen.
- **Preview/publish parity (Facebook)** — Proven and documented. Parity script: `scripts/prove_preview_publish_parity.py` (optional `--culture` → `docs/PARITY_PROOF_FACEBOOK_CULTURE_YYYYMMDD.txt`).
- **CULTURE v1.1 Phase A** — Schema + migrations only. Approved and complete: `culture_library` table, `posting_queue.culture_library_id`. No generators in Phase A.
- **Phase B framework** — Generator (`utils/content_roles/culture_generator.py`), creator (`scripts/automated_culture_creator.py`), schedule API behaviour (Tue language only; Mon/Thu CULTURE via role rail). Complete. Do not proceed beyond Phase B without new approval (per brief).

---

## 2. Adviser’s last instructions (Phase B.2)

Phase B.2 brief: **Publish + Preview support for culture_fact**.

- Enable `content_type='culture_fact'` to preview via `/api/preview/post/<id>?channel=facebook` and `/preview/post/<id>?channel=facebook`.
- Enable publish via `platform_publishers.publish_to_facebook()`.
- Full parity between preview and publish (byte-for-byte).
- No changes to scheduling, selection, execution infrastructure, or schema.

---

## 3. Phase B.2 implementation (completed)

| Component | File | Change |
|-----------|------|--------|
| **Publish** | `utils/platform_publishers.py` | `publish_to_facebook()` treats `culture_fact` like `message`: text-led feed post using `generated_content`, `format_message_for_facebook()`, `/feed`. No CTA, no hashtag injection. |
| **Formatter** | `utils/channel_preview/formatters/facebook.py` | `FacebookFormatter.format()` includes `meta.category`. Same formatting as publish. |
| **Renderer** | `utils/channel_preview/preview_renderer.py` | SELECT includes `culture_library_id`. For `culture_fact` with `culture_library_id`, derive `category` from `culture_library` and add to post_data for meta. |
| **Template** | `templates/channel_previews/facebook_feed.html` | Optional small neutral label for `meta.category` (preview only; does not affect publish). |
| **Parity script** | `scripts/prove_preview_publish_parity.py` | Added `--output` and `--culture`; `--culture` writes to `docs/PARITY_PROOF_FACEBOOK_CULTURE_YYYYMMDD.txt`. |

**Report:** `docs/CULTURE_V1_1_PHASE_B2_REPORT.md` (verification checklist; parity is a hard gate).

**Non-scope respected:** No changes to Matrix logic, schedule API, generators/creators, execution scheduler, schema, non-Facebook channels.

---

## 4. Work after Phase B.2 (ingestion and heritage library)

### 4.1 Culture library ingestion

- **Goal:** Populate `culture_library` so the CULTURE Mon/Thu rota has content.
- **Script:** `scripts/ingest_culture_library_csv.py`
  - Reads CSV: category, title, body_text, source_note (extra columns tone, image_idea, etc. not stored).
  - Inserts into `culture_library` (active=TRUE).
  - `--run-migration`: creates `culture_library` table and indexes if they do not exist.
- **Source CSV:** `docs/CULTURE_v1_1_FINAL_INGESTION.csv`
- **Result:** **247 rows** in `culture_library`. Table created via script when missing (migrations `20260204_create_culture_library.sql` and `20260204_add_culture_library_id_to_posting_queue.sql` remain the canonical schema).

### 4.2 Heritage library (new table + ingestion)

- **Goal:** Support a second rota slot for heritage/clans content. User intent: refine publishing so culture posts run **once weekly** and the **other** slot is heritage/clans (coding to follow).
- **Migration:** `migrations/20260129_create_heritage_library.sql`
  - Creates `heritage_library` with same structure as `culture_library`: id, category, title, body_text, source_note, active, created_at.
  - Indexes on active and category.
- **Script:** `scripts/ingest_heritage_library_csv.py`
  - Same CSV column usage as culture ingest; `--run-migration` creates `heritage_library` if missing.
- **Source CSV:** `docs/HERITAGE_LINEAGE_v1_0_FINAL_INGESTION_PATCHED.csv`
- **Result:** **216 rows** in `heritage_library`. Categories include lineage_system, diaspora_connection, etc.

**No publishing logic was added for heritage.** The table and data are in place; wiring the heritage/clans slot into the schedule and execution is intended as the next coding phase.

---

## 5. Current state summary

| Area | State |
|------|--------|
| **Execution** | Single gate: `scheduled_posting_executor.py`. No changes. |
| **culture_fact** | Publish + preview supported; parity script available. |
| **culture_library** | 247 rows; used by CULTURE Mon/Thu (culture_fact) rota. |
| **heritage_library** | 216 rows; table and data ready; **no schedule/execution integration yet**. |
| **Publishing refinement** | Intent: once weekly culture + once weekly heritage/clans. **Coding to follow**; no implementation in this pass. |

---

## 6. Key files and scripts (reference)

### Migrations
- `migrations/20260204_create_culture_library.sql` — culture_library table (Phase A).
- `migrations/20260204_add_culture_library_id_to_posting_queue.sql` — posting_queue.culture_library_id (Phase A).
- `migrations/20260129_create_heritage_library.sql` — heritage_library table.

### Scripts
- `scripts/ingest_culture_library_csv.py` — Ingest culture CSV into culture_library; `--run-migration` to create table.
- `scripts/ingest_heritage_library_csv.py` — Ingest heritage CSV into heritage_library; `--run-migration` to create table.
- `scripts/prove_preview_publish_parity.py` — Parity proof; `--culture` for Phase B.2 output path.
- `scripts/automated_culture_creator.py` — Creates Mon/Thu culture_fact queue rows from culture_library (unchanged).
- `scripts/scheduled_posting_executor.py` — Sole Facebook publish path (unchanged).

### Docs
- `docs/CULTURE_V1_1_REBRIEF_CONFIRMATION_AND_PHASE_A_REPORT.md` — Phase A approval; Phase B on hold until explicit approval.
- `docs/CULTURE_V1_1_PHASE_B_REPORT.md` — Phase B (generator, creator, schedule API).
- `docs/CULTURE_V1_1_PHASE_B2_REPORT.md` — Phase B.2 (publish + preview for culture_fact).
- `docs/CHANGELOG.md` — Entries for Phase B.2, culture + heritage ingestion.
- `docs/README.md` — Feature list updated (CULTURE v1.1, heritage library, ingest scripts).
- `docs/quick-reference.md` — Key tables updated (culture_library, heritage_library, ingest commands).

---

## 7. Non-regression confirmation

- No changes to execution scheduler logic.
- No changes to CULTURE generator or creator (beyond prior Phase B).
- No changes to Matrix logic, schedule API selection rules, or product/message logic.
- No schema changes to posting_queue beyond existing culture_library_id (Phase A).
- New schema limited to heritage_library (new table) and ingestion scripts.

---

## 8. Known issues (report only, no code)

- **Friday AUTHORITY_SHORT:** Week-view Friday slot may still show “AUTHORITY SHORT / Authority post / Draft” when the posting_queue row has empty or failed content. See **docs/REPORT_FRIDAY_AUTHORITY_SHORT_GENERIC_CONTENT.md** for: what is implemented, why the UI shows generic labels, likely causes (creator not run for that week, or generation failed — no source text or LLM/validation), and recommended next steps (inspect row and validation_report_json, verify rota/KB, run creator with --force, consider scheduling the script). No automation was found for `automated_authority_short_creator.py`.

---

## 9. Next steps (for coding)

- **Publishing refinement:** Implement once-weekly culture slot + once-weekly heritage/clans slot (select from heritage_library, 90-day or similar repeat rules, queue rows with appropriate content_type/role and linkage to heritage_library when that design is agreed).
- **Parity proof:** Run `scripts/prove_preview_publish_parity.py --ids <culture_fact_id>,<authority_short_id>,<weekly_word_id> --culture` and confirm PASS for Phase B.2 sign-off if not already done.

---

**Report complete.** All recent developments are reflected in CHANGELOG, docs/README, quick-reference, and this report.
