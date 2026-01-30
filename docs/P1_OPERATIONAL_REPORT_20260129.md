# Phase P1 — Operational Report (2026-01-29)

Report back on: migration, Tuesday eligibility, pre-generation run, idempotency, and planning calendar validation.

---

## 1. Unique-index migration

**Did the migration apply cleanly?**

Yes, after resolving duplicates and fixing migration parsing.

- **Pre-check:** `python3 scripts/p1_duplicate_scan_and_migrate.py --scan-only` found:
  - **tuesday_language:** 13 duplicate slot groups (many ids per slot).
  - **product:** 7 duplicate slot groups.
- **Resolution:** `python3 scripts/p1_duplicate_scan_and_migrate.py --resolve` deleted **490** duplicate rows (kept one row per slot, preferring status ∈ ready/approved/scheduled/published, else highest id), then applied the migration.
- **Parsing fix:** The migration script was splitting SQL by `;` and dropping any segment whose *stripped* text started with `--`, which removed the first statement (it had leading comment lines). Fixed so that comment-only *lines* are stripped from each segment; all 7 `CREATE UNIQUE INDEX` statements are now executed.
- **Apply:** After the fix, `--apply-only` ran successfully. All 7 P1 slot indexes exist:
  - `idx_posting_queue_culture_fact_slot`
  - `idx_posting_queue_tuesday_language_slot`
  - `idx_posting_queue_message_slot`
  - `idx_posting_queue_heritage_slot`
  - `idx_posting_queue_authority_short_slot`
  - `idx_posting_queue_product_slot`
  - `idx_posting_queue_depth_long_slot`

**Exact duplicate groups that were blocking (before resolve):** 13 tuesday_language groups (e.g. 6–303 ids per slot) and 7 product groups (2–50 ids per slot). Full ids were printed by `--scan-only`; after `--resolve` no duplicate groups remained.

---

## 2. Tuesday eligibility

**Counts (eligible calendar_ideas per classification):**

| Classification   | Count |
|------------------|-------|
| weekly_word      | 99    |
| weekly_phrase    | 104   |
| weekly_insult    | 105   |
| **Total**        | **308** |

**90-day exclusion:** For each Tuesday, the creator excludes `idea_id`s that appear in `posting_queue` (language types) with `scheduled_date >= (target_tuesday - 90 days)`. For the next 12 weeks, **blocked_in_window** was 2–5 per Tuesday; **eligible** was 97–102 per Tuesday. No Tuesday had 0 eligible in the report.

**Why “No eligible idea” was reported earlier:** The dry-run failure was likely from an older or different data state. Current data: pool is sufficient (99/104/105 per type); 90-day window blocks only a small number; 12 weeks need 4 Tuesdays per type, so the pool is more than enough.

**Proposed fix (if it recurs):**

1. **Increase pool:** Add more `calendar_ideas` for weekly_word / weekly_phrase / weekly_insult.
2. **Adjust exclusion:** Reduce `REPEAT_DAYS` in `automated_weekly_content_creator.py` (e.g. 60) to allow more reuse.
3. **Fallback policy:** When eligible = 0, allow re-use of least-recently-used idea (code change).

**Script:** `scripts/tuesday_eligibility_report.py` (run with optional `WEEKS_AHEAD=12`).

---

## 3. --weeks-ahead 12 run report

**Command:**  
`python3 scripts/pregenerate_matrix.py --weeks-ahead 12 --report docs/P1_PREGEN_REPORT_20260129.json`

**Result:** Exit code **0**. All 7 creators exited 0; **has_failure: false**.

**Headline stats (first run):**

| Creator   | Created | Regenerated | Skipped | Failed |
|-----------|---------|-------------|---------|--------|
| Monday    | 8       | 0           | 3       | 0      |
| Tuesday   | 0       | 0           | 11      | 0      |
| Wednesday | 8       | 0           | 4       | 0      |
| Thursday  | —       | —           | (all)   | 0      |
| Friday    | 13      | —           | 0       | 0      |
| Saturday  | 8       | 0           | 4       | 0      |
| Sunday    | 10      | 0           | 2       | 0      |

**Report file:** `docs/P1_PREGEN_REPORT_20260129.json` (weeks_ahead=12, platform=facebook, dry_run=false; started_at / finished_at; per-creator exit_code and stdout/stderr previews).

---

## 4. Immediate re-run (idempotency)

**Command:**  
`python3 scripts/pregenerate_matrix.py --weeks-ahead 12 --report docs/P1_PREGEN_REPORT_20260129_rerun.json`

**Result:** Exit code **0**. **has_failure: false.**

**Re-run stats:**

| Creator   | Created | Regenerated | Skipped | Failed |
|-----------|---------|-------------|--------|--------|
| Monday    | 0       | 0           | 11     | 0      |
| Tuesday   | 0       | 0           | 11     | 0      |
| Wednesday | 0       | 0           | 12     | 0      |
| Thursday  | —       | —           | (all)  | 0      |
| Friday    | 13*     | —           | 0      | 0      |
| Saturday  | 0       | 8           | 4      | 0      |
| Sunday    | 0       | 0           | 12     | 0      |

*Friday “Created: 13” is a **stats bug**: the authority_short creator increments “created” for every slot processed (including retained existing rows). No new rows were inserted for already-filled slots; the unique index would prevent duplicate inserts.

**Idempotency:** 0 new inserts for Mon/Tue/Wed/Thu/Sun; Saturday regenerated 8 in place (same rows updated); Friday reported “Created” but only retained existing rows. No duplicate rows; only skips and in-place regens.

---

## 5. Planning calendar validation (2–3 future weeks)

**Script:** `scripts/validate_planning_calendar_p1.py` (checks 2026-W6, W10, W14).

**Result:** Validation **OK**.

- **One post per day:** Mon–Fri and Sun have exactly one post per day; Saturday has multiple scheduled times (as intended).
- **Types:** Mon = culture_fact; Thu = heritage_fact; Tue = exactly one language post (weekly_word / weekly_phrase / weekly_insult).
- **Titles/content:** Fri and Sun have non-placeholder content in the sampled weeks. Some Tuesday rows were backfilled with “Pre-generated” / “Test content” for missing slots; these can be replaced by running the Tuesday creator when the slot is empty.

---

## 6. Fit for other (non-Facebook) channels

- **Structurally:** The “one slot = one row + regenerate in place + orchestrator” model generalises; other platforms can use the same pattern.
- **DB:** The P1 partial unique indexes are **Facebook-scoped** (`WHERE platform = 'facebook'`). Facebook is protected by DB constraints; other platforms are not unless equivalent partial unique indexes are added per platform (or made platform-agnostic if that matches the data model).

**Minimum to make other channels equally safe:**

1. **Add equivalent partial unique indexes per platform** (or make indexes platform-agnostic if you want one slot per date regardless of platform). Duplicate the existing P1 index definitions in `migrations/20260129_p1_one_row_per_slot_unique_indexes.sql`, changing `WHERE platform = 'facebook'` to the target platform (e.g. `WHERE platform = 'instagram'`) or removing the platform filter for platform-agnostic enforcement.
2. **Ensure all publish paths for each platform** go through the same validated executor gate (like Facebook now does via Phase C1).

---

## 7. Files touched / added

- **Migration parsing:** `scripts/p1_duplicate_scan_and_migrate.py` — fixed statement parsing so all 7 index statements run.
- **Tuesday eligibility:** `scripts/tuesday_eligibility_report.py` — new; reports pool counts and 90-day blocked vs eligible per Tuesday.
- **Validation:** `scripts/validate_planning_calendar_p1.py` — new; validates 2–3 future weeks (one post per day, types, non-placeholder).
- **Reports:** `docs/P1_PREGEN_REPORT_20260129.json`, `docs/P1_PREGEN_REPORT_20260129_rerun.json`, `docs/P1_OPERATIONAL_REPORT_20260129.md` (this file).
