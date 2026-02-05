# Changelog

## Phase I-1A — Blog_post Image Run Recording (2026-03-01)

- **Objective:** Bring blog_post section and header image generation up to the same transparency and auditability guarantees as text runs in the Unified Channel Workbench: be able to answer “Exactly what prompt, through which engine, produced this image, and when?”.
- **Changes:** Reused `generation_runs` for image runs. Section imaging endpoint (`imaging_api_generation.imaging_generate_image`) and header imaging endpoint (`header.api_image_generation.api_generate_header_image`) now create a `generation_runs` row before calling image generators (`gpt-image-1`, DALL-E, SDXL) and complete it after generation/optimization with `status`, `finished_at`, and `output_refs` (image paths). Prompt snapshots store the exact `image_prompt` string used; `engine_id` is recorded as `image/<model_name>`.
- **Guarantees:** No blog_post section/header image is generated without a corresponding run record; failure paths mark runs as `failed` with `error_message`. Existing HTTP contracts and publishing behaviour are unchanged. Hybrid/carousel code untouched.  
- **Deliverable:** docs/PHASE_I1A_BLOG_IMAGES_RUN_RECORDING_REPORT.md.

---

## Phase I-0 — Image Prompt Transparency Audit (2026-03-01)

- **Objective:** Audit image and hybrid prompt construction for transparency, determinism, and traceability. Design + audit only; no code changes.
- **Deliverable:** docs/PHASE_I0_IMAGE_PROMPT_TRANSPARENCY_AUDIT.md. Inventory of image-generation entry points (Instagram Hybrid, carousel, blog_post section/header, product, weekly content); prompt composition analysis; transparency gap (opaque vs partially transparent); mapping to workbench concepts; explicit non-goals.
- **Outcome:** Hybrid and carousel slides classified opaque; blog_post section/header partially transparent; enables decision on I-1/I-2/I-3 or stop.

---

## Phase H-5.1 — Publish Path Alignment (2026-03-01)

- **Objective:** Ensure all publishing and scheduling use the explicit “current output” selected in the Unified Channel Workbench. Backend wiring only; no UI, generator, or carousel changes.
- **Resolver:** `blueprints/launchpad_utils.resolve_current_posting_queue_id(content_ref, platform, channel_type, slot_identifier)` — workbench_current_outputs → generation_runs.output_refs.posting_queue_id → validate queue row; no fallback.
- **post_now:** launchpad_old, launchpad_scheduling, blog_post_syndication — for blog_post, resolve current output; 400 NO_CURRENT_OUTPUT if none or if item_id is not current.
- **schedule_tomorrow:** Same resolver rules for blog_post.
- **Scheduled executor:** get_due_posts includes post_id; for blog_post, skip unless queue row is the resolved current output.
- **Deliverable:** docs/PHASE_H51_PUBLISH_PATH_ALIGNMENT_REPORT.md.

---

## Phase H-5 — Engine Comparison & Current Output Selection (2026-03-01)

- **Objective:** Multi-engine comparison and explicit “current output” selection per slot in the Unified Channel Workbench. No generator or carousel changes.
- **Storage:** Table `workbench_current_outputs` (content_ref, platform, channel_type, slot_identifier, run_id, updated_at). Migration: migrations/20260301_create_workbench_current_outputs.sql. Slot = "primary" for blog_post.
- **API:** GET /launchpad/api/workbench/engines; GET/POST /launchpad/api/workbench/current-output; POST /launchpad/api/workbench/run accepts engine_id, slot_identifier.
- **UI:** Engine selector, “Run with engine”, Asset Comparison “Use this output”, “✓ Current” in Generation History, “Prompt for current output” in Inspector. workbench.js + workbench.html.
- **Deliverable:** docs/PHASE_H5_ENGINE_COMPARISON_REPORT.md.

---

## Phase G-1 — Matrix Run Ledger (2026-02-02)

- **Objective:** Introduce a Matrix Run Ledger that records in the database when the matrix was run, for which date window, for which platform(s), and whether it completed successfully. Write-once audit trail; no UI, scheduler, or automation.
- **Database:** New table `matrix_run_ledger` (id, platform, start_date, weeks_ahead, started_at, finished_at, status, report_path, created_at). One row per platform per run. Migration: `migrations/20260201_create_matrix_run_ledger.sql`.
- **Write path:** `scripts/pregenerate_matrix.py` inserts two rows at run start (status 'running'), updates at completion with finished_at, status (success/partial/failed), report_path. Ledger writes do not crash the run on failure (log and continue).
- **Verification:** Query `matrix_run_ledger WHERE platform = 'instagram' ORDER BY started_at DESC LIMIT 5` answers “Has Instagram been generated for week X?”.
- **Deliverable:** docs/PHASE_G1_MATRIX_RUN_LEDGER_REPORT.md.

---

## Phase G-0 — IG Matrix Population Fix (2026-02-01)

- **Objective:** Fix root cause of missing Instagram items in planning week-view: ensure IG receives the same role/day coverage as Facebook via a single, deterministic, auditable path.
- **Root cause:** Instagram `posting_queue` rows were never created for weeks 4 and 5 (and partial for week 5) because `pregenerate_matrix.py` was not run for those weeks, or only FB-only creators were run manually.
- **Single source of truth:** `scripts/pregenerate_matrix.py` is the ONLY supported mechanism for populating the weekly matrix for both Facebook and Instagram. Docstring updated to state this; no option to skip IG; idempotent and safe to re-run.
- **Backfill:** Ran `python scripts/pregenerate_matrix.py --start-date 2026-01-19 --weeks-ahead 8 --report temp/pregenerate_matrix_backfill_report.json`. Week 4: IG rows 0→4; Week 5: IG rows 10→21; Week 6 unchanged (idempotent).
- **Proof:** Before/after DB row counts and schedule API curl output for weeks 4 and 5 documented in report. Week-view now shows IG on appropriate days (Mon CULTURE, Wed REASSURANCE, Thu HERITAGE, Fri AUTHORITY_SHORT, Sun DEPTH_LONG).
- **Deliverable:** docs/IG_MATRIX_POPULATION_FIX_REPORT.md. No Hybrid, previews, SDXL, UI polish, or alerts touched.

---

## Phase E — Expand Hybrid Coverage to Match Human Browsing Reality (2026-01-31)

- **Objective:** Eliminate “most Instagram previews still show placeholders” by running the existing Hybrid system for a human-relevant browsing window (7 weeks: current week + next 6).
- **Scope:** Execution and coverage only. No new Hybrid logic, resolvers, UI, or automation proof. Phase D and Phase 3 paused.
- **Target window:** from_date 2026-01-29, weeks_ahead 7 (39 slots: 6 roles × 6–7 dates). Rationale: typical user scrolls current + next several weeks.
- **Execution:** Hybrid script run (and background run started) with `--from-date 2026-01-29 --weeks-ahead 7`. Before: 15/39 with images; after (as of report): 25/39; remainder fill via re-run or completed background run.
- **Success (UI-based):** Phase E complete only when Nick confirms in the UI that the majority of Slide 2 positions show real images when opening IG previews across the window; placeholders rare and explainable; status panel aligned.
- **Deliverable:** docs/PHASE_E_INSTAGRAM_COVERAGE_EXPANSION_REPORT.md.

---

## Phase D — Automate Hybrid Runs and Prove Quiet Operation (2026-01-31)

- **Objective:** Make the Instagram Hybrid system run automatically, daily, and quietly; prove it without human intervention.
- **Scope:** Automation + proof only. No imagery changes, UI redesign, generators, or cost work.
- **Execution mechanism:** launchd (Option A). Matches existing posting monitor pattern; more reliable than cron on macOS. Template: `docs/launchd_hybrid_phase1_template.plist`. Install to `~/Library/LaunchAgents/com.blog.instagram-hybrid-phase1.plist` (replace PROJECT_ROOT with repo path), then `launchctl load`.
- **Canonical invocation:** `python3 scripts/run_instagram_hybrid_phase1.py --weeks-ahead 3`. `--from-date` omitted; script now defaults to today (optional `--from-date` in `run_instagram_hybrid_phase1.py`).
- **Cadence:** Once every 24 hours at 06:00 (StartCalendarInterval). Logs: `logs/hybrid_phase1.out`, `logs/hybrid_phase1.err`. No retries, backoff, or new alert logic.
- **Proof:** Two automated runs ≥24h apart required; evidence (hybrid_run_summaries rows, UI quiet) documented in `docs/PHASE_D_AUTOMATION_AND_QUIET_OPERATION_REPORT.md`. Phase D not complete until both runs and UI verification are recorded.
- **Docs:** docs/PHASE_D_AUTOMATION_AND_QUIET_OPERATION_REPORT.md, docs/launchd_hybrid_phase1_template.plist, docs/kb/imagery/hybrid_phase1.md (Phase D section), docs/IMAGE_CAPABILITIES_INDEX.md (Phase D bullet).

---

## Phase C — Complete Instagram Image Coverage (Hybrid Only) (2026-01-31)

- **Objective:** Bring Instagram to operational readiness: every IG post that contractually requires an image (Slide 2) has a real image generated via the existing Hybrid pipeline for a 3-week forward window.
- **Scope:** Instagram only. Mon CULTURE, Tue LANGUAGE, Wed REASSURANCE, Thu HERITAGE, Fri AUTHORITY_SHORT, Sun DEPTH_LONG — Slide 2 only. Saturday PRODUCT out of scope. No new generators, prompts, UI, schema, or automation logic.
- **Forward window:** Default `--weeks-ahead` in `scripts/run_instagram_hybrid_phase1.py` set to 3 (Phase C minimum); usage line updated. Same from_date/weeks_ahead used for Hybrid runs, coverage evaluation, and reporting.
- **Execution:** Iterative fill until coverage complete: run Hybrid script (from_date 2026-01-29, weeks_ahead 3); one slot (DEPTH 2026-02-15) was missing; second live run generated it. Final run: coverage_status "complete", confidence_statement "Instagram imagery is complete for the next 3 weeks."
- **Report:** docs/PHASE_C_INSTAGRAM_IMAGE_COVERAGE_REPORT.md — coverage window, coverage table (per role: days covered, images generated, editorial steers, final status), final run summary, UI verification checklist (Nick), compliance statement.
- **No scope drift. Phase 3 (cost, SDXL) explicitly deferred.**

---

## Phase 2.6 — Hybrid Status Panel (Launchpad) (2026-02-06)

- **Objective:** Convert the Hybrid alert signal into a clear, confidence-building operational surface on the Launchpad. Read-only panel; no new automation, generators, or workflows.
- **Panel:** “Instagram Hybrid Status” card on `/launchpad/one-click-publication`, below the main heading. Shows: last run (from `run_timestamp`), coverage state (from `confidence_statement`), action-required summary (from `human_action_counts` when `any_human_action_required`), links “View in calendar” and “Hybrid documentation”. Data from `hybrid_run_summaries` only; no JSON parsing or recomputation.
- **Acknowledgement:** Opening the Launchpad sets `acknowledged_at` on the latest `hybrid_run_summaries` row. Header alerts for that run are suppressed until a subsequent run (new row). Migration: `migrations/20260206_add_acknowledged_at_to_hybrid_run_summaries.sql`.
- **Alerts API:** `get_alerts()` only returns stale/blocked/incomplete/human_action alerts when the latest row has `acknowledged_at IS NULL`. “No run ever” alert unchanged.
- **Files:** `blueprints/launchpad_old.py` (_get_hybrid_status_for_launchpad, one_click_publication passes hybrid_status); `templates/launchpad/includes/hybrid_status_panel.html` (new); `templates/launchpad/one_click_publication.html` (include panel); `blueprints/automation_pipeline.py` (get_alerts uses acknowledged_at).
- **Docs:** docs/kb/imagery/hybrid_phase1.md (“Hybrid Status Panel (Phase 2.6)”); docs/HYBRID_PHASE2_6_IMPLEMENTATION_REPORT.md.
- **No new imagery logic. No Run Hybrid button. No scheduler. No UI editors. No scope expansion.**

---

## Phase 2.5 — DB-backed Hybrid run alerts (2026-02-05)

- **Objective:** Make missed or problematic Instagram Hybrid imagery runs visible in the main UI header alert indicator. DB-backed alert source; no file scanning in request paths.
- **Database:** New table `hybrid_run_summaries` (migration `migrations/20260205_create_hybrid_run_summaries.sql`). One row per run: run_timestamp, platform, from_date, weeks_ahead, coverage_status, run_outcome, confidence_statement, summary_text, any_human_action_required, human_action_counts (JSONB), coverage_summary (JSONB), report_file_path. Index (platform, run_timestamp DESC).
- **Hybrid runner:** `scripts/run_instagram_hybrid_phase1.py` inserts one row after writing `temp/hybrid_phase1_report_<ts>.json`. On DB write failure, script exits non-zero and logs clearly.
- **Alerts API:** `GET /launchpad/one-click-publication/api/alerts` reads latest `hybrid_run_summaries` row for platform "instagram". Returns alerts for: no run ever (warning), run older than 24 h (warning), run_outcome blocked (error), coverage_status != complete (warning), any_human_action_required (warning). Alert payload includes title, message, severity, action_url (planning calendar week from from_date), action_text.
- **Frontend:** `static/js/shared/site-header.js` — `loadAlerts()` fetches the alerts API; mock specimen removed. Badge and dropdown unchanged; 30s polling preserved. New alert_type icons: hybrid_never, hybrid_stale, hybrid_blocked, hybrid_incomplete, hybrid_human_action.
- **Docs:** docs/kb/imagery/hybrid_phase1.md (section "Hybrid alerts & confidence (Phase 2.5)"); docs/IMAGE_CAPABILITIES_INDEX.md (§10 Phase 2.5); docs/CURRENT_STATE_REPORT.md (hybrid_run_summaries); docs/HYBRID_PHASE2_5_IMPLEMENTATION_REPORT.md; docs/evidence/hybrid_phase2_5/README.md.
- **No new UI pages, no schedulers, no imagery logic changes.**

---

## Phase 2.3 — Complete Instagram coverage + human confidence signals (2026-01-29)

- **Phase 2.3-A (Complete Instagram image coverage):** Extended Hybrid pipeline to REASSURANCE (Wednesday) and DEPTH_LONG (Sunday), using the same pattern as prior roles. No refactors. Storage: `static/content/instagram_hybrid/reassurance/<YYYY-MM-DD>/`, `static/content/instagram_hybrid/depth/<YYYY-MM-DD>/`. Utilities: build_stock_query_for_reassurance/depth, slot_dir_for_reassurance/depth, resolve_reassurance_slide2_asset, resolve_depth_slide2_asset. Payload: `day == 2 and role == "REASSURANCE"`, `day == 6 and role == "DEPTH_LONG"`. Script: iter_reassurance_wednesdays, iter_depth_sundays; REASSURANCE and DEPTH loops; coverage_summary reassurance_*, depth_*. Regeneration: --role reassurance (warn if not Wednesday), --role depth (warn if not Sunday).
- **Phase 2.3-B (Human confidence; no new imagery):** Report top-level coverage_status (complete | incomplete | attention_required), confidence_statement (one plain-English sentence derived from coverage counts). Per-slot human_action_required (boolean), human_action_reason (missing_image | editorial_steer_pending | generation_failed | null). Deterministic; clarifies state for Nick without reading logs.
- **No UI. No schema. No new imagery logic beyond day expansion.** Docs: docs/kb/imagery/hybrid_phase1.md (REASSURANCE/DEPTH subsections, "How Nick knows Instagram is 'done' for the week"), docs/IMAGE_CAPABILITIES_INDEX.md (§10 scope IG Monday–Sunday), docs/HYBRID_PHASE2_3_IMPLEMENTATION_REPORT.md.

---

## Phase 2.2 — Hybrid imagery for Instagram LANGUAGE Tuesdays (2026-01-29)

- **Objective:** Extend the existing Hybrid imagery pipeline to cover Instagram LANGUAGE posts on Tuesdays, using exactly the same Hybrid pattern as HERITAGE, CULTURE, and AUTHORITY_SHORT. Pure expansion of coverage.
- **Scope:** Instagram LANGUAGE Tuesday Slide 2 only. Slides 1 and 3 remain placeholder. Other roles’ behaviour unchanged.
- **Implementation:** Copy of HERITAGE/CULTURE/AUTHORITY pattern: separate slot directory `static/content/instagram_hybrid/language/<YYYY-MM-DD>/`, separate `build_stock_query_for_language`, `slot_dir_for_language`, `resolve_language_slide2_asset`; Tuesday LANGUAGE branch in `utils/instagram_payload.py` (runs before generic Tuesday weekly-PNG logic); LANGUAGE Tuesday loop in `scripts/run_instagram_hybrid_phase1.py`. Prompt theme: "Scottish language and words". Fallback query: "Scottish language words typography culture".
- **Reporting:** coverage_summary now includes language_tuesdays_total, language_with_generated_image, language_missing_generated_image, language_with_editorial_steer_pending; summary_text mentions LANGUAGE when applicable.
- **Regeneration:** `scripts/request_hybrid_regenerate.py` accepts `--role language` for Tuesday slots; validates that the date is a Tuesday (warns otherwise).
- **No UI, no schema, no refactors.** Docs: docs/kb/imagery/hybrid_phase1.md (LANGUAGE Tuesday §), docs/IMAGE_CAPABILITIES_INDEX.md (§10), docs/HYBRID_PHASE2_2_IMPLEMENTATION_REPORT.md.

---

## Phase 2.1 — Hybrid imagery for Instagram AUTHORITY_SHORT Fridays (2026-01-29)

- **Objective:** Extend the existing Hybrid imagery pipeline to cover Instagram AUTHORITY_SHORT posts on Fridays, using exactly the same Hybrid pattern as HERITAGE Thursdays and CULTURE Mondays. Coverage expansion only; no new mechanisms.
- **Scope:** Instagram AUTHORITY_SHORT Friday Slide 2 only. Slides 1 and 3 remain placeholder. HERITAGE and CULTURE behaviour unchanged.
- **Implementation:** Copy of HERITAGE/CULTURE pattern: separate slot directory `static/content/instagram_hybrid/authority/<YYYY-MM-DD>/`, separate `build_stock_query_for_authority`, `slot_dir_for_authority`, `resolve_authority_slide2_asset`; Friday AUTHORITY_SHORT branch in `utils/instagram_payload.py`; AUTHORITY Friday loop in `scripts/run_instagram_hybrid_phase1.py`. Same snapshot/generation/steer/iteration semantics. Prompt theme: "Scottish authority and tradition".
- **Reporting:** coverage_summary now includes authority_fridays_total, authority_with_generated_image, authority_missing_generated_image, authority_with_editorial_steer_pending; summary_text mentions AUTHORITY when applicable.
- **Regeneration:** `scripts/request_hybrid_regenerate.py` accepts `--role authority` for Friday slots; validates that the date is a Friday (warns otherwise).
- **No UI, no schema, no scheduler, no refactor of HERITAGE or CULTURE.** Docs: docs/kb/imagery/hybrid_phase1.md (AUTHORITY_SHORT Friday §), docs/IMAGE_CAPABILITIES_INDEX.md (§10), docs/HYBRID_PHASE2_1_IMPLEMENTATION_REPORT.md.

---

## Phase 2.0 — Hybrid imagery for Instagram CULTURE Mondays (2026-01-29)

- **Objective:** Extend the existing Hybrid imagery pipeline to cover Instagram CULTURE posts on Mondays, using exactly the same Hybrid pattern as HERITAGE Thursdays. Pure coverage expansion; no new mechanisms.
- **Scope:** Instagram CULTURE Monday Slide 2 only. Slides 1 and 3 remain placeholder. HERITAGE behaviour unchanged.
- **Implementation:** Copy of HERITAGE pattern: separate slot directory `static/content/instagram_hybrid/culture/<YYYY-MM-DD>/`, separate `build_stock_query_for_culture`, `slot_dir_for_culture`, `resolve_culture_slide2_asset`; CULTURE Monday branch in `utils/instagram_payload.py`; CULTURE loop in `scripts/run_instagram_hybrid_phase1.py`. Same snapshot/generation/steer/iteration semantics.
- **Reporting:** coverage_summary now includes culture_mondays_total, culture_with_generated_image, culture_missing_generated_image, culture_with_editorial_steer_pending; summary_text mentions CULTURE when applicable.
- **Regeneration:** `scripts/request_hybrid_regenerate.py` accepts `--role culture` for Monday slots.
- **No UI, no schema, no scheduler, no refactor of HERITAGE.** Docs: docs/kb/imagery/hybrid_phase1.md (CULTURE Monday §), docs/IMAGE_CAPABILITIES_INDEX.md (§10), docs/HYBRID_PHASE2_0_IMPLEMENTATION_REPORT.md.

---

## Hybrid Phase 1.8 — Preview-driven editorial feedback loop (2026-01-31)

- **Control refinement only; no scope expansion.** Formalises the human-in-the-loop correction cycle: Instagram preview remains the only validation surface; feedback can be added, refined, and iterated without destabilising automation.
- **Multi-entry steer:** One slot = one feedback history. Files: editorial_steer.txt, editorial_steer_2.txt, editorial_steer_3.txt, … in the slot dir. All included in prompt as “Editorial guidance based on prior review:”; no summarise/normalise/reinterpret.
- **Generation iteration:** Monotonic counter per slot (generation_iteration.txt); report field generation_iteration (1, 2, 3, …).
- **Report extensions:** editorial_steer_entries, editorial_steer_combined_sha256, generation_iteration, regeneration_reason_present (in success, failure, and dry-run). No breaking changes to existing fields.
- **No UI, no auto-retry, no schema, no other days/generators.** Docs: docs/kb/imagery/hybrid_phase1.md (Phase 1.8), docs/IMAGE_CAPABILITIES_INDEX.md, docs/HYBRID_PHASE1_8_IMPLEMENTATION_REPORT.md.

---

## Hybrid Phase 1.7 — Slot-local editorial steer for regeneration (2026-01-31)

- **Objective:** Allow a human to attach a single free-text editorial note to one slot; the note is injected into the GPT-Image-1 prompt only when that slot is regenerated. Guided correction, not art direction.
- **Steer location:** Optional file `editorial_steer.txt` in the slot directory (`static/content/instagram_hybrid/heritage/<YYYY-MM-DD>/`). Missing or empty = no steer (Phase 1.6 behaviour).
- **Prompt:** When present and non-empty, appended verbatim: “Editorial guidance for regeneration:” + contents + “Apply this guidance while preserving the overall intent of the image.”
- **Report:** Per-slot fields added: `editorial_steer_present`, `editorial_steer_sha256`, `generation_used_editorial_steer`.
- **No UI, no schema, no global change.** Flow: add/edit editorial_steer.txt → request_hybrid_regenerate.py → main script.
- **Docs:** docs/kb/imagery/hybrid_phase1.md (Guided regeneration Phase 1.7), docs/IMAGE_CAPABILITIES_INDEX.md, docs/HYBRID_PHASE1_7_IMPLEMENTATION_REPORT.md.

---

## Hybrid Phase 1.6 — Human override & regeneration control (2026-01-31)

- **Objective:** Allow a human to cause a specific HERITAGE Thursday Slide 2 image to be regenerated without new UI, without affecting other slots/days/channels, and without breaking automation.
- **Mechanism:** Option A (sentinel file deletion). Absence of `generated_1080x1350.png` = eligible for regeneration; next script run reuses snapshot and generates a new image.
- **Helper script:** `scripts/request_hybrid_regenerate.py --slot-date YYYY-MM-DD` removes the generated image for that Thursday only. User then runs the normal Hybrid script; only that slot is regenerated.
- **Report:** Per-slot report now includes `snapshot_reused` (true when snapshot existed and generation ran this run) and `output_file_sha256` (SHA-256 of generated file when created). No snapshot re-run on regeneration.
- **Docs:** docs/kb/imagery/hybrid_phase1.md (Manual regeneration Phase 1.6), docs/IMAGE_CAPABILITIES_INDEX.md (§10 Phase 1.6), docs/HYBRID_PHASE1_6_IMPLEMENTATION_REPORT.md.

---

## Hybrid Phase 1.5 — Operationalised forward generation (2026-01-31)

- **Objective:** Make Hybrid Phase 1 reliably visible in the UI. Instagram Thursday HERITAGE previews must consistently show a real image for Slide 2 for upcoming weeks without manual intervention.
- **Change:** Hybrid HERITAGE Thursday images are now generated ahead of time so Instagram previews reliably show real imagery for upcoming weeks. No new behaviour; operational hardening only.
- **Run cadence:** Script `run_instagram_hybrid_phase1.py` is expected to be run at least once per week (manually or via cron), with `--from-date $(date +%Y-%m-%d)` and `--weeks-ahead 3`. No daemon or in-app scheduler.
- **Report:** JSON report now includes `slots_processed`, `slots_generated`, `slots_skipped_existing` for diagnosis.
- **Docs:** docs/kb/imagery/hybrid_phase1.md — Phase 1.5 run cadence and runbook section; idempotency confirmed (script skips existing snapshot/generated file).

---

## Hybrid Phase 1 — HERITAGE Thu IG Slide 2 (2026-01-31)

- **Objective:** Produce preview-approvable Instagram visuals for HERITAGE Thursday Slide 2 using Hybrid (stock-assisted reference → GPT-Image-1 generated output). Preview-first; no publishing.
- **Scope:** HERITAGE (Thursday) Slide 2 only; Slides 1 & 3 remain typographic placeholder.
- **Flow:** Deterministic query from post_data → photo_apis (Pexels/Unsplash) → snapshot per slot (stock_results.json, stock_selected.json) → deterministic selection (stable_hash % len) → GPT-Image-1 generation → 1080×1350 PNG (generated_1080x1350.png). Stock is reference only; output is generated_editorial_illustration.
- **Payload:** `utils/instagram_payload.py` — HERITAGE Slide 2: if generated_1080x1350.png exists for slot → use it; else if snapshot exists → placeholder + "Hybrid pending generation"; else → placeholder + "Hybrid missing snapshot".
- **Script:** `scripts/run_instagram_hybrid_phase1.py` (--from-date, --weeks-ahead, --dry-run). Pre-generation only; no live API during preview.
- **Storage:** `static/content/instagram_hybrid/heritage/<YYYY-MM-DD>/`. Report: `temp/hybrid_phase1_report_<timestamp>.json`.
- **Docs:** docs/HYBRID_PHASE1_IMPLEMENTATION_REPORT.md, docs/IMAGE_CAPABILITIES_INDEX.md (§10), docs/kb/imagery/hybrid_phase1.md.

---

## Instagram Preview Readiness — Phases A–C (2026-01-30)

### Phase A — Validator hygiene
- **Objective:** Run validator cleanly for future weeks without touching legacy data.
- **Change:** `scripts/validate_daily_cap_invariant.py` accepts optional `--from-date YYYY-MM-DD`. When provided, only rows with `scheduled_date >= from-date` are considered; range is `[from-date, from-date + weeks)`. Default behaviour unchanged when omitted.
- **Usage:** `validate_daily_cap_invariant.py --weeks 3 --platforms facebook instagram --from-date <today>`. Evidence: `temp/validator_forward_only_evidence.txt`.

### Phase B — Editorial preview UX
- **Objective:** Make Instagram previews comfortable to approve; no payload logic changes.
- **templates/channel_previews/instagram_feed.html:** Added small label "Instagram feed preview" near top; slide index indicators ("Slide 1 of 3", etc.); carousel grouped with `.instagram-carousel` / `.instagram-slide`. When a slide uses the typographic placeholder, overlay caption "Placeholder image (Phase 1)" (via `slide.is_placeholder` from payload).
- **utils/instagram_payload.py:** `_slide_spec` and all carousel builds now set `is_placeholder=True` when using the generic placeholder URL; formatter passes through to template.
- **Calendar clarity:** `static/js/planning/unified-item-card.js` adds class `platform-instagram` (or `platform-facebook`) to item cards when `item.platform` is set. `templates/planning/calendar/includes/week_view_styles.html` adds `.item-card.platform-instagram { border-left-width: 3px; border-left-color: #a855f7; }` so IG items are visually distinct. No logic change; CSS/class only.
- **No regressions:** Facebook previews unchanged; IG still routes to IG preview; no new endpoints.

### Phase C — First real Instagram visual (Tuesday LANGUAGE only)
- **Objective:** Replace placeholder for Tuesday with real weekly PNG resized to 1080×1350 (4:5) for Instagram only.
- **utils/instagram_payload.py:** When day == 1 (LANGUAGE) and `image_path` exists, `_weekly_image_to_ig_1080x1350(image_path)` produces an IG-sized image: centre-crop to 1080×1350, saved as `instagram_1080x1350.png` in the same directory as the weekly PNG (no new storage tables). Preview and publish use the same URL. If resize fails, fall back to typographic placeholder and append to payload warnings.
- **CULTURE, AUTHORITY_SHORT, DEPTH_LONG:** Unchanged; remain placeholder-only in Phase 1.

### Phase C-2 — Heritage (Thursday) Instagram Slide 2
- **Objective:** Add a second real Instagram visual pathway, limited to HERITAGE (Thursday); preview-first, no publishing, no new systems.
- **Carousel:** Thursday HERITAGE: Slide 1 = typographic placeholder, Slide 2 = curated heritage image (static directory), Slide 3 = typographic placeholder. No variation.
- **Storage:** `static/images/instagram/heritage/` (Option A). 3–6 images, semantic filenames (e.g. stone_cross.png, ruined_kirk.png). No metadata, no manifest, no DB.
- **Selection:** Deterministic in `utils/instagram_payload.py`: when day == 3 and role == HERITAGE, `_select_heritage_ig_slide2(post_data)` lists image files in directory (sorted), index = hash(scheduled_date) % len(files). Repeatable, preview- and publish-stable.
- **Caption:** For HERITAGE IG only, append one line at bottom: "Illustrative image". No credits, dates, or claims.
- **Config:** `config/instagram_assets.py` — `INSTAGRAM_HERITAGE_IMAGE_DIR`.
- **CULTURE, AUTHORITY, DEPTH, Tuesday LANGUAGE:** Unchanged. No schema changes; no publishing enabled; no new pipelines.

---

## Matrix generation: Instagram from shared sources (Approach A) (2026-01-30)

- **Objective:** Extend Matrix pre-generation so Instagram rows are originated from the same upstream sources as Facebook (one row per slot per platform), with no cloning and no schema changes. Per docs/INSTAGRAM_MATRIX_GENERATION_PLAN.md.
- **Approach A (shared selection):** Orchestrator selects upstream provenance once per slot (culture_library_id, idea_id, message_index, heritage_library_id, topic_id/source_page_id, product_id) and calls each creator twice (facebook, instagram) with the same selection. No creator reads the FB row for provenance.
- **Slot key:** Non-product days `(scheduled_date, role, content_type)`; Saturday products `(scheduled_date, scheduled_time, role, content_type)`.
- **Creators migrated:** All seven creators now expose `get_slot_dates(weeks_ahead, from_date)`, `select_for_slot(...)`, and `generate_for_slot(platform, slot_key, selection, dry_run, force)`. Legacy CLI behaviour retained (facebook-only when run standalone).
- **Orchestrator:** `scripts/pregenerate_matrix.py` runs all creators in-process with Approach A; no subprocess calls. Report structure is per-slot and per-platform (`report["slots"][content_type]` with `slot_key`, `selection_summary`, `platforms: { facebook: { outcome }, instagram: { outcome } }`).
- **Validator:** `scripts/validate_daily_cap_invariant.py` now validates per platform (`--platforms facebook instagram` default). At most one publishable row per (date, platform) for non-Saturday; Saturday product rules apply per platform. Exit non-zero on violation; report lists (date, platform, rule, row ids).
- **Idempotency:** Creators locate existing row by platform + slot_key; regenerate-in-place only for failed/empty/placeholder; otherwise skip.
- **Message provenance:** Wednesday message selection uses `message_index` (deterministic by year/week); no use of `generated_content` as provenance.
- **Deliverables:** Generation report for 2–3 weeks, validator output (both platforms), changelog. Instagram image provisioning unchanged (Phase 1 placeholder rules). No publishing or visual enhancement.
- **Evidence:** Live run with `--weeks-ahead 3` and `--report temp/matrix_generation_report_3weeks.json` completed with exit 0; all slot types show per-platform outcomes (skipped/created/regenerated). Validator `--weeks 3 --platforms facebook instagram` may report violations for dates that already had multiple publishable rows (e.g. 2026-01-30); resolve by cleaning duplicate/legacy rows or by validating a future-only window. Calendar: open planning week view and confirm both "FB:" and "IG:" entries per day; open IG preview for Mon, Tue, Sat.

---

## Planning calendar: channel-aware visibility and previews (2026-01-29)

- **Objective:** Editors can see and distinguish Facebook and Instagram posts in the planning calendar week view and open the correct preview for each.
- **Scope:** UI + routing only; no payload/image logic changes.
- **1. Instagram rows in calendar:** `planning_api_calendar_schedule.py` now includes `posting_queue` rows for both `platform IN ('facebook', 'instagram')` for Tuesday language, product, message, and role-based posts. One row per slot per channel (no merge/dedupe). Each schedule item includes `platform`.
- **2. Channel labels in UI:** Week view labels social post items with "FB: " or "IG: " prefix (e.g. "FB: CULTURE — Language: Word", "IG: COMMERCE — Product") so editors can tell which platform at a glance.
- **3. Channel-aware preview:** Calendar item Preview button and click already use `item.platform` in unified-item-card.js (`/preview/post/<queue_id>?channel=<platform>`). Full-page preview route `preview_views.py` now renders `instagram_feed.html` when `channel=instagram` (parity with API).
- **4. Row fallback:** Week view JS uses `social-posts-row` or `words-phrases-row` and `toggle-social-posts` or `toggle-words-phrases` so both template variants work.
- **Files touched:** `blueprints/planning_api_calendar_schedule.py`, `static/js/planning/calendar-week-view.js`, `blueprints/preview_views.py`. No payload or image code modified.

### Litmus test: one Instagram queue row (Option 1)
- **Script (frozen, diagnostic-only):** `scripts/diagnostics/create_one_instagram_queue_row.py` — was used once to duplicate one Facebook row into an Instagram row for a given week (`platform = 'instagram'`, `status = 'ready'`). **Do not run again.** See script header and `scripts/diagnostics/README.md`.
- **Test row:** One Instagram row was created for 2026-W07 (culture_fact, 2026-02-09) and is **left in place** as standing proof that the calendar shows IG and the preview path works. No creators or orchestrators changed. Can be cancelled later once real generation is in place.

---

## Instagram image provisioning Phase 1 (2026-01-29)

- **Scope:** Feed posts only; 3-slide carousel; one post per day. No new systems, no schema changes.
- **Single source of truth:** `utils/instagram_payload.get_instagram_payload(post_data)` used by Instagram preview formatter and `publish_to_instagram(queue_id)`. Carousel refs may be cached in existing `posting_queue.generated_content.instagram.*` (optional).
- **Placeholder:** One generic typographic image: `static/images/site/instagram_typographic_placeholder.png` (1080×1350, "CLAN"). Referenced via `config/instagram_assets.py`. Used for Mon/Wed/Thu/Fri/Sun (CULTURE, REASSURANCE, HERITAGE, AUTHORITY_SHORT, DEPTH_LONG).
- **Tuesday (LANGUAGE):** Existing weekly PNGs (`image_path`); same image 3×. **Saturday (PRODUCT):** Product URLs from clan_products; same image 3×.
- **Preview:** Instagram formatter + `templates/channel_previews/instagram_feed.html` + channel_preview_api wired for `channel=instagram`. Shows 3 slides + caption + disclosure/attribution.
- **Publish:** `utils/platform_publishers.publish_to_instagram(queue_id)` builds payload via same function, uploads 3 images via Instagram Graph API (reuses instagram_carousel_api helpers), updates queue status.
- **Implementation notes:** docs/INSTAGRAM_IMAGE_PROVISION_IMPLEMENTATION_NOTES.md.

---

## Instagram Image Provision Phase 1 — Corrective addendum (2026-01-29)

- **Doc:** docs/INSTAGRAM_IMAGE_PROVISION_PHASE1_ORDERS_ADDENDUM.md
- Tightens Phase 1 orders per adviser: (0) No schema changes. (1) Single source of truth function for Instagram payload (preview + publish). (2) Store carousel refs in existing generated_content JSON (e.g. generated_content.instagram.carousel), not new columns. (3) Preview: instagram formatter + instagram_feed.html + channel_preview_api. (4) publish_to_instagram calls same function. (5) Phase 1 allowed: Tue language PNGs, Sat product URLs, typographic cards; PD/generated deferred — Slide 2 typographic fallback for Mon/Thu/Fri/Sun. (6) No new automation imaging pipeline in Phase 1; provision deterministically at preview/publish time. (7) Evidence: full week preview, Tue + Sat carousels, one forced fallback.

---

## Instagram Image Provision Phase 1 — Implementation orders (2026-01-29)

- **Doc:** docs/INSTAGRAM_IMAGE_PROVISION_PHASE1_ORDERS.md
- Implementation directive for coder: scope (feed only, 1/day, 3-image carousel), hard constraints, allowed image classes, mandatory carousel structure, Matrix→provisioning mapping (Mon–Sun), sourcing rules, storage/attachment (existing only), preview/publish parity, disclosure/attribution, fallback handling, prohibited implementations, deliverables (implementation notes, test evidence, changelog), acceptance criteria.

---

## Instagram Image Provision Plan v1 (2026-01-29)

- **Doc:** docs/INSTAGRAM_IMAGE_PROVISION_PLAN.md
- Feed posts only; 1/day; default 3-image carousel. Authority: Charter + Capabilities Index.
- Matrix→image mapping (Mon–Sun): CULTURE, LANGUAGE, REASSURANCE, HERITAGE, AUTHORITY_SHORT, PRODUCT, DEPTH_LONG. All images map to existing classes; no new systems. Disclosure/attribution (caption footer); fallback typographic_card; explicit “must NOT do” list.

---

## Image Capabilities Index — Phase-0B alignment (2026-01-29)

- Expanded Image Capabilities Index to cover header/section images, watermarking, and diagnostics (Phase-0B alignment).
- New doc: docs/IMAGE_CAPABILITIES_INDEX.md (sections 1–9). Sections 7–9: header and section images (blog/longform), watermarking and AI disclosure, image failures and diagnostics.
- Cross-links added: IMAGE_CAPABILITY_CHARTER.md and KB Image Policy Overview now point to IMAGE_CAPABILITIES_INDEX.md for implementation routing.

---

## Image policy KB and Charter vs Instagram sanity check (2026-01-29)

### A) KB summary page
- **Location:** Backend → Image Policy Overview (`/kb/backend/image_policy`).
- **Template:** `templates/knowledge_base/backend/image_policy.html`.
- **Purpose:** Summarises how images are handled across CLAN content and channels; points to Charter as authoritative. Covers core principles, image classes, channels (Facebook, Instagram, Blog/Newsletter), and “Where to find the rules”. Explicit note: Charter takes precedence over this KB page.

### B) Charter vs Instagram v1 sanity check
- **Doc:** `docs/CHARTER_INSTAGRAM_V1_SANITY_CHECK.md`.
- **Content:** Confirms Charter does not over-constrain Instagram (carousels, disclosure, no photorealism required); does not under-constrain (blocks fake historical, silent AI, ad-hoc types). Instagram v1 day-by-day mapping (Culture → Depth) with default image classes; no exceptions. Note: AI disclosure placement (caption footer/hashtag) to be added later to Instagram channel docs only.

---

## Facebook preview/publish alignment and QA (2026-01-30)

### Scope (instruction doc: cleanup, QA, docs before next platform)
- **1.1 Preview/publish alignment:** Text-only path (message, culture_fact, heritage_fact) uses generated_content + shared formatter; image-post path (product, weekly_*, etc.) uses generated_caption. Preview formatter now branches explicitly so weekly_phrase/weekly_word/weekly_insult use generated_caption (same as publish). Product continues to strip price in both preview and publish.
- **1.2 Backfill idempotency:** Re-ran `scripts/backfill_culture_headers.py` in dry-run; 22 target rows, 0 would change. Doc note added: run only once or when header rules change; idempotency confirmed.
- **1.3 Parity/QA script:** `scripts/prove_preview_publish_parity.py` extended with `--platform facebook --weeks N` (fetch IDs from queue for next N weeks), `--qa-format` (culture/heritage header present, newline collapse, no trailing spaces), and exit code 0/1 (PASS/FAIL). Product path uses strip_price_from_caption in script to match publish.
- **1.4 Backfill:** Already applied previously; dry-run confirms zero rows to change.
- **1.5 Documentation:** New `docs/FACEBOOK_CULTURE_HERITAGE_FORMATTING.md` — header strings (UNDERSTANDING SCOTLAND, SCOTTISH HERITAGE), composition (two newlines after header, one between title and body), newline rules (collapse 3+ to 2, no trailing spaces), parity script usage, backfill note. `docs/README.md` and `docs/PREVIEW_FACEBOOK_MATCH_PUBLISH.md` updated with links.
- **1.6 Clean state:** `scripts/validate_daily_cap_invariant.py --weeks 4` passed. Parity script `--platform facebook --weeks 2 --qa-format` passed for 18 posts (authority_short, weekly_*, product, depth_long, culture_fact, message, heritage_fact).

### Artefacts
- **docs/FACEBOOK_CULTURE_HERITAGE_FORMATTING.md** — Facebook culture/heritage header and formatting rules.
- **scripts/backfill_culture_headers.py** — Doc note: run only once or when headers change; idempotency note.
- **scripts/prove_preview_publish_parity.py** — `--platform facebook --weeks N`, `--qa-format`, exit code 0/1; product uses strip_price_from_caption.

---

## Product price never in Facebook preview or publish (2026-01-30)

### Policy
Product price must never appear in Facebook preview text or in published product posts.

### Implementation
- **Helper:** `utils/formatting/product_caption.py` — `strip_price_from_caption(text)` removes £/$/bare decimal amounts (e.g. £43.99, $43.99, 43.99) from product caption text; collapses whitespace.
- **Preview:** `utils/channel_preview/formatters/facebook.py` — for product posts, caption is passed through `strip_price_from_caption` before `format_message_for_facebook`; meta no longer includes `product_price`; template does not show price.
- **Publish:** `utils/platform_publishers.py` — for product image posts, caption is passed through `strip_price_from_caption` before sending to Facebook API.
- **Docs:** `docs/PREVIEW_FACEBOOK_MATCH_PUBLISH.md` updated (product caption policy, no price in template).

### Verification
- `/api/preview/post/<id>?channel=facebook` for product posts returns display_text and HTML without price; verified for post 21482.

---

## Executor daily cap and idempotency (2026-01-30)

### Objective
Fix “Multiple posts published in one day” (Facebook Matrix): publish exactly one post per day (Mon–Fri + Sun), Saturday allowed multiple product posts. Prevent at executor layer.

### Short-term containment
- **Hotfix:** `scripts/hotfix_cancel_surplus_today.py` — cancel surplus Facebook rows for today (status='cancelled', error_message); output `docs/HOTFIX_CANCELLED_IDS_YYYYMMDD.csv`.
- **Executor guard:** In `scripts/scheduled_posting_executor.py`: after get_due_posts(), apply daily cap (group by platform+scheduled_date; Facebook non-Saturday keep one per date, Saturday keep all product rows and cancel non-product); cancel surplus in DB; then publish only the capped list.

### Long-term fix
- **Deterministic selection:** Priority AUTHORITY_SHORT → DEPTH_LONG → HERITAGE → CULTURE → message → weekly_* → product; tie-break lowest id. Implemented in `apply_daily_cap()`.
- **Atomic claim:** Before publish, `UPDATE posting_queue SET status='publishing' WHERE id=? AND status IN ('ready','pending')`; proceed only if rowcount==1. Prevents duplicate publish on re-run or race.
- **Stats:** eligible_after_validation, cancelled_surplus, blocked_wrong_day; log “Executor cap: date X had N eligible, kept id=Y, cancelling N-1 surplus”.
- **Dry-run:** `--dry-run` logs due posts, cap selection, and would-cancel; no DB updates or publishing.
- **Cleanup script:** `scripts/cleanup_surplus_daily_posts.py` — scan forward N weeks (default 12), cancel surplus per date, output `docs/CLEANUP_SURPLUS_POSTS_YYYYMMDD.csv`. Options: `--weeks N`, `--dry-run`.
- **Shared publishable predicate:** `utils/publishable_predicate.py` — PUBLISHABLE_STATUSES, SCHEDULED_DUE_FRAGMENT. Used by hotfix, cleanup, invariant validator; executor predicate matches.
- **Invariant validator:** `scripts/validate_daily_cap_invariant.py` — fails if any non-Saturday date in next N weeks has >1 publishable Facebook row. Options: `--weeks N`, `--platform facebook`.
- **psycopg IN clause:** Hotfix, cleanup, invariant validator use `status IN (%s, %s)` with PUBLISHABLE_STATUSES[0]/[1] for psycopg3 compatibility.

### Closure (5-post incident, completed 2026-01-30)
- **Correlation:** `docs/EXECUTOR_CORRELATE_PUBLISHED_POSTS.md` §3 — filled mapping for scheduled_date 2026-01-29; pre-cap executor commit (8a77286); conclusion: 5 separate queue rows published by pre-cap run; guard prevents recurrence.
- **Closure reply:** `docs/CLOSURE_REPLY_EXECUTOR_DAILY_CAP.md` — completed: correlation, commit hashes, confirmation (grep apply_daily_cap + claim), invocation (launchd → background_posting_monitor.sh → scheduled_posting_executor.py).
- **Correlation helper:** `scripts/correlation_query_5post_incident.py` — query posting_queue for a given scheduled_date and print mapping.

### Artefacts and docs
- **docs/BRIEF_EXECUTOR_DAILY_CAP_AND_IDEMPOTENCY.md** — Repo brief for this fix.
- **docs/REPORT_EXECUTOR_DAILY_CAP_20260130.md** — Report-back (summary, evidence, artefacts, risk notes, §9 closure reference).
- **docs/EXECUTOR_CORRELATE_PUBLISHED_POSTS.md** — Correlation query and mapping (closure task filled).
- **docs/CLOSURE_REPLY_EXECUTOR_DAILY_CAP.md** — Final closure reply (completed by coder).
- **docs/HOTFIX_CANCELLED_IDS_YYYYMMDD.csv**, **docs/CLEANUP_SURPLUS_POSTS_YYYYMMDD.csv** — Generated by hotfix and cleanup runs (cleanup writes CSV only when rows to cancel).
- **docs/REPORT_FOR_CODING_ADVISER_20260130.md** — Adviser report (all work since last instructions).

### Non-scope
- No changes to creators, publish formatting, or channel preview. Phase C1: Facebook publishing remains only via scheduled_posting_executor.

---

## P1 caveats: resolve behaviour, DB target logging, other platforms (2026-01-29)

### Resolve behaviour and rollback
- **Confirmed:** `scripts/p1_duplicate_scan_and_migrate.py --resolve` performs **DELETE** (not UPDATE to cancelled). Duplicate rows are permanently removed; rollback relies on backups/archives.
- **Doc:** `docs/P1_RESOLVE_ROLLBACK_AND_BACKUP.md` — documents DELETE behaviour, rollback (no CSV ID archive at run time; backup recommended before future --resolve), and policy note.
- **Script:** Docstring updated to reference the rollback doc.

### Single DB target (creator / validator / schedule API)
- **Config:** `config/unified_config.py` — added `get_database_target_for_logging()` (host, port, dbname, user; no password).
- **Pregenerate:** `scripts/pregenerate_matrix.py` — logs DB target once at startup (stderr).
- **Validator:** `scripts/validate_planning_calendar_p1.py` — logs DB target once at start of main() (stderr).
- **Schedule API:** `blueprints/planning_api_calendar_schedule.py` — logs DB target once on first call to `api_calendar_schedule()` (logger.info). Ensures pregenerate, validator, and schedule API all show the same DB target when run against the same config.

### Other platforms
- **Doc:** `docs/P1_OPERATIONAL_REPORT_20260129.md` — section 6 expanded with minimum steps to make other channels equally safe: add equivalent partial unique indexes per platform (or platform-agnostic); ensure publish paths go through validated executor gate.

---

## Phase P1 — Operational completion (2026-01-29)

### Summary
- **Migration:** Duplicate scan resolved 490 duplicate slot rows; migration parsing fixed (comment stripping); P1 unique indexes applied and verified.
- **Tuesday eligibility:** Pool sufficient (99/104/105 per type); 90-day exclusion blocks 2–5 per week; no “No eligible idea” in 12-week report; script `scripts/tuesday_eligibility_report.py` added.
- **Pre-generation:** `--weeks-ahead 12` run succeeded (exit 0; all slots filled); re-run showed idempotency (0 new inserts for Mon/Tue/Wed/Thu/Sun; Sat 8 in-place regens; Fri stats bug: “Created” counts retained slots).
- **Validation:** `scripts/validate_planning_calendar_p1.py` added; 2026-W6, W10, W14 validated (one post per day, correct types, non-placeholder Fri/Sun).
- **Report:** `docs/P1_OPERATIONAL_REPORT_20260129.md`; JSON reports in `docs/P1_PREGEN_REPORT_20260129.json` and `docs/P1_PREGEN_REPORT_20260129_rerun.json`.

---

## Phase P1 — Matrix pre-generation (execution) (2026-01-29)

### Objective
Reliable, fully automated, idempotent pre-generation of all 7 Matrix slots (8–12 weeks ahead). One slot = one row; authority-short model everywhere; single orchestration pass.

### P1.1 — Normalised creators (Mon–Sun)
- **Monday:** `scripts/automated_culture_creator.py` — SELECT slot; if none INSERT then fill from culture_library; if valid SKIP; if failed/empty/placeholder UPDATE in place. Returns created/regenerated/skipped/failed.
- **Tuesday:** `scripts/automated_weekly_content_creator.py` — One row per Tuesday (language); SELECT slot; if none INSERT; if valid SKIP; if failed UPDATE in place (same or new idea_id). 90-day exclusion; rotation (week_number-1)%3.
- **Wednesday:** `scripts/automated_message_post_creator.py` — SELECT slot; if none INSERT with next message in CSV; if valid SKIP; if failed UPDATE with next message in rotation (never retry same).
- **Thursday:** `scripts/automated_heritage_creator.py` — Same pattern as culture; heritage_library; 90-day repeat avoidance.
- **Friday:** `scripts/automated_authority_short_creator.py` — Reference implementation; no behaviour change.
- **Saturday:** `scripts/automated_product_post_creator.py` — SELECT slot; if none INSERT; if valid SKIP; if failed re-pick product and UPDATE same row (product_id, status draft). Content filled by workflow.
- **Sunday:** `scripts/automated_depth_long_creator.py` (new) — Same pattern as authority_short; kb_topic_rota + DepthLongGenerator; INSERT skeleton then generate; UPDATE on failure.

### P1.2 — Orchestrator
- **scripts/pregenerate_matrix.py** — Invokes creators in order Mon→Sun; accepts --weeks-ahead (default ≥8), --platform (default facebook), --dry-run, --force, --report &lt;file&gt;; emits JSON report; exit non-zero if any creator exited non-zero.

### DB enforcement
- **migrations/20260129_p1_one_row_per_slot_unique_indexes.sql** — Partial unique indexes: culture_fact (platform, scheduled_date); Tuesday language (platform, scheduled_date); message (platform, scheduled_date); HERITAGE (platform, scheduled_date); AUTHORITY_SHORT (platform, scheduled_date); product (platform, scheduled_date, scheduled_time); depth_long (platform, scheduled_date). All WHERE platform = 'facebook'.

### Deliverables
- Normalised creators (Mon–Sat); new Sunday depth_long creator; pregenerate_matrix.py; DB migration; CHANGELOG + this entry.

### Non-regression
- Matrix weekday rules, publishing logic, preview/publish parity, generator content rules unchanged.

---

## Phase P1 locked plan (2026-01-29)

### Objective
Record the final locked plan before the formal Phase P1 brief: decisions (automate all days; authority_short model everywhere), P1.1/P1.2 scope, agreed regeneration behaviour (message = next in rotation; product = re-pick and UPDATE; Tuesday = UPDATE in place; DB partial unique indexes), and locked creator surface area (7 creators + pregenerate_matrix.py).

### Added
- **docs/PHASE_P1_LOCKED_PLAN.md**: Single reference for the locked plan. Formal brief to follow with acceptance criteria, non-regression rules, and DB constraints.

---

## Phase P1 confirmation and creator list (2026-01-29)

### Objective
Reply to locked decisions (automate Sunday; one row per slot, reuse/regenerate in place) and immediate questions before formal Phase P1 brief.

### Added
- **docs/PREGENERATE_MATRIX_P1_CONFIRMATION_AND_CREATOR_LIST.md**: (1) Confirmation of both decisions; (2) Blockers/concerns: none; design choices for message (regenerate = next message in rotation?) and product (regenerate = re-pick product and UPDATE?); optional partial unique indexes per slot for DB enforcement; (3) Final list: 7 creators (Mon–Sun, including new automated_depth_long_creator.py) + pregenerate_matrix.py as orchestrator. Locked surface area for P1.

---

## Pre-generate Matrix — creator inventory and concerns (2026-01-29)

### Objective
Reply to briefing “automated pre-generation of the Matrix (8–12 weeks ahead)” before formal Phase brief: definitive creator list and candid concerns.

### Added
- **docs/PREGENERATE_MATRIX_CREATOR_INVENTORY_AND_CONCERNS.md**: (1) List of all scripts that create posting_queue rows (Mon–Sat; Sunday = API only, no batch script), which days/slots, automated or manual, skip-if-exists and regenerate-if-failed behaviour; (2) Concerns: Sunday has no batch creator; only authority_short regenerates in place (others create new row when failed → duplicate risk); Tuesday never retries failed slot; source dependencies (KB rota, libraries, CSV, schedule, products); idempotency/duplicate notes; recommendation to decide “update failed row vs cancel-then-create” and Sunday automation before locking orchestration.

---

## Friday AUTHORITY_SHORT generic content — report only (2026-01-29)

### Objective
Document why the week-view Friday slot still shows “AUTHORITY SHORT / Authority post / Draft” instead of actual generated content. No code changes.

### Report
- **docs/REPORT_FRIDAY_AUTHORITY_SHORT_GENERIC_CONTENT.md**: What is implemented (creator, generator, schedule API, week-view); why the UI shows generic labels (row has empty/placeholder `generated_content` and status draft/failed); likely causes (creator not run for that week, or generation failed — no source text or LLM/validation); no automation found for `automated_authority_short_creator.py`; recommended next steps (inspect row and `validation_report_json`, verify rota/KB for week, run creator with `--force`, consider scheduling the script).

### Remaining known issues
- No automated run of the authority-short creator; dependency on `kb_topic_rota` / `kb_topic_content` / `clan_kb_articles` for the target week — if empty, generation fails with “No suitable source text”.

---

## Week-View Distribution Fix to Approved Matrix (2026-01-29)

### Objective
Week view shows exactly the intended slots (Mon CULTURE, Tue Language, Wed Message, Thu HERITAGE, Fri AUTHORITY, Sat Commerce, Sun Depth) for current and future weeks.

### Diagnosis (§1)
- **Monday blank:** No culture_fact row for 2026-01-26; culture creator (a) didn’t cover past weeks, (b) treated “any CULTURE” (role) as slot filled, so didn’t create culture_fact.
- **Tuesday blank:** 8 language rows existed; schedule API returned one Tuesday item but without scheduled_date/scheduled_time, so week-view couldn’t place it.
- **Saturday:** 5 product rows returned; grid showed 5 cards (Option A: cap to 1 in grid).

### Fixes
- **scripts/automated_culture_creator.py:** culture_post_exists() now checks content_type='culture_fact' (not role CULTURE). Added --start-date for backfill. Default --weeks-ahead 12.
- **scripts/automated_heritage_creator.py:** Default --weeks-ahead 12.
- **blueprints/planning_api_calendar_schedule.py:** Tuesday language: query selects scheduled_date/scheduled_time; status IN (ready, pending, generated, published, scheduled); prefer ready then published then newest; schedule item includes scheduled_date and scheduled_time so week-view can place it. Saturday: cap product list to 1 for grid (Option A).

### Backfill
- Ran culture creator with --start-date 2026-01-01 --weeks-ahead 8; Monday 2026-01-26 now has one culture_fact (id 21247).

### Report
- **docs/REPORT_WEEK_VIEW_DISTRIBUTION_FIX.md**: Full diagnosis, root causes, predicate, verification, and option choice.

---

## Phase H1 — HERITAGE (Thursday) (2026-01-29)

### Objective
Bring heritage_fact to full parity with culture_fact, fixed to Thursday. Wiring + symmetry only; no invention, no refactors. Preview == publish; 90-day repeat avoidance.

### Schema
- **posting_queue.heritage_library_id**: Migration `migrations/20260129_add_heritage_library_id_to_posting_queue.sql` (FK to heritage_library; index). Applied if not present.
- **content_roles**: Migration `migrations/20260129_add_heritage_to_content_roles.sql` — INSERT HERITAGE role so posting_queue.role = 'HERITAGE' is valid.

### Generator
- **utils/content_roles/heritage_generator.py**: Library-driven selection from heritage_library; 90-day exclusion via posting_queue.heritage_library_id; deterministic seed `{year}-W{week}-THU-HERITAGE`; returns heritage_library_id, title, body_text, category, source_note, generated_content.

### Creator
- **scripts/automated_heritage_creator.py**: Thursday-only; lookahead 4 weeks; one row per Thursday (platform=facebook, content_type=heritage_fact, role=HERITAGE, scheduled_time=15:00, status=ready); idempotent (no duplicate HERITAGE for same date).

### Executor
- **scripts/scheduled_posting_executor.py**: `culture_fact` → (1,) Monday only; `heritage_fact` → (4,) Thursday only. No other content types changed.

### CULTURE creator (Monday only)
- **scripts/automated_culture_creator.py**: CULTURE_DAYS = (1,); iter_monday_dates (no Thursday); added typing.Optional. Thursday reserved for HERITAGE.

### Publish
- **utils/platform_publishers.py**: heritage_fact in text-only path with message/culture_fact (generated_content, format_message_for_facebook, /feed; no CTA/hashtag).

### Preview
- **utils/channel_preview/preview_renderer.py**: SELECT heritage_library_id; for content_type=heritage_fact load category from heritage_library into post_data; existing template category label used.

### Schedule API
- **blueprints/planning_api_calendar_schedule.py**: Comment only — Thursday HERITAGE (heritage_fact), Monday CULTURE (culture_fact). Role-based query already returns both; no logic change.

### Parity proof
- **scripts/prove_preview_publish_parity.py**: Added `--heritage` → output `docs/PARITY_PROOF_FACEBOOK_HERITAGE_YYYYMMDD.txt`.
- **docs/PARITY_PROOF_FACEBOOK_HERITAGE_20260129.txt**: All three (heritage_fact, culture_fact, weekly_language) = PASS.

### Report
- **docs/REPORT_PHASE_H1_HERITAGE_COMPLETE.md**: Phase H1 report-back (file list, confirmations, parity path).

### Non-scope (unchanged)
CULTURE generator, publish path, preview path; execution logic beyond weekday map; no angles, images, Instagram, analytics.

---

## CULTURE + Heritage library ingestion (2026-01-29)

### Objective
Populate culture_library and add heritage_library for publishing rotas (culture once weekly + heritage/clans slot; coding to follow).

### Culture library ingestion
- **Script:** `scripts/ingest_culture_library_csv.py` — reads CSV (category, title, body_text, source_note), inserts into `culture_library`. `--run-migration` creates table if missing.
- **Source:** `docs/CULTURE_v1_1_FINAL_INGESTION.csv`
- **Result:** 247 rows in `culture_library` (active). Used by CULTURE Mon/Thu rota (culture_fact).

### Heritage library (new table + ingestion)
- **Migration:** `migrations/20260129_create_heritage_library.sql` — creates `heritage_library` (same structure as culture_library: id, category, title, body_text, source_note, active, created_at).
- **Script:** `scripts/ingest_heritage_library_csv.py` — same CSV format; `--run-migration` creates table if missing.
- **Source:** `docs/HERITAGE_LINEAGE_v1_0_FINAL_INGESTION_PATCHED.csv`
- **Result:** 216 rows in `heritage_library` (active). For heritage/clans slot in publishing rota (coding to follow).

### Key tables
- `culture_library` — CULTURE v1.1 Mon/Thu culture_fact posts; 90-day repeat via posting_queue.culture_library_id.
- `heritage_library` — Heritage/clans rota; separate table for second slot (once weekly culture + once heritage).

---

## Facebook Automated Posting — Phase C1 (Safety & Alignment) and Phase C2 (Queue Hygiene) (2026-01-29)

### Phase C1 — Single gate and Matrix v1.1 validation
- **Objective:** Facebook posts are published only through a single, validated gate; content adheres to Matrix v1.1 weekday schedule.
- **blueprints/posts.py:** `api_publish_post(queue_id)` no longer calls `publish_to_facebook()`; returns 403. Manual publish disabled for date safety.
- **blueprints/automation_execute.py:** `execute_publish_to_facebook()` no longer calls `publish_to_facebook()`; returns 403. Workflow cannot publish to Facebook.
- **scripts/scheduled_posting_executor.py:** Sole code path for Facebook publishing. Added `validate_content_schedule()` enforcing Matrix v1.1: language (weekly_word/phrase/insult) Tuesday only; culture_fact Mon/Thu; message Wed; authority_short Fri; product Sat; depth_long Sun. Legacy language on non-Tuesday days are hard-blocked at execution time.
- **Report:** `docs/REPORT_PHASE_C1_SAFETY_AND_ALIGNMENT.md`.

### Phase C2 — Queue hygiene and prevention
- **Objective:** Clean up data inconsistencies in `posting_queue` and prevent duplicate language posts.
- **Cleanup:** `scripts/phase_c2_queue_cleanup.py` cancelled 338 non-Tuesday language rows (ready/pending) and 2 duplicate product rows; exported IDs to `docs/PHASE_C2_AFFECTED_IDS_*.csv`.
- **Migration:** `migrations/20260129_add_unique_facebook_language_queue.sql` added partial unique index `idx_posting_queue_facebook_language_unique` on `(platform, content_type, idea_id, scheduled_date)` for Facebook language posts, preventing duplicate language rows at DB level.
- **Reports:** `docs/REPORT_PHASE_C2_QUEUE_HYGIENE.md` (analysis), `docs/REPORT_PHASE_C2_EXECUTION.md` (execution and verification).

---

## CULTURE v1.1 Phase B.2 — Publish + Preview for culture_fact (2026-01-29)

### Objective
Enable `content_type='culture_fact'` to preview and publish to Facebook with parity (preview text === publish text byte-for-byte). No changes to scheduling, selection, or execution infrastructure.

### Changed
- **utils/platform_publishers.py**: `publish_to_facebook()` treats `culture_fact` like `message`: text-led feed post using `generated_content`, `format_message_for_facebook()`, `/feed`. No CTA, no hashtag injection.
- **utils/channel_preview/formatters/facebook.py**: `FacebookFormatter.format()` includes `meta.category`. Same formatting as publish.
- **utils/channel_preview/preview_renderer.py**: SELECT includes `culture_library_id`; for `culture_fact` with `culture_library_id`, derive `category` from `culture_library` for meta.
- **templates/channel_previews/facebook_feed.html**: Optional small neutral label for `meta.category` (preview only; does not affect publish).
- **scripts/prove_preview_publish_parity.py**: Added `--output` and `--culture`; `--culture` writes to `docs/PARITY_PROOF_FACEBOOK_CULTURE_YYYYMMDD.txt`.

### Added
- **docs/CULTURE_V1_1_PHASE_B2_REPORT.md**: Phase B.2 report and verification checklist. Parity proof is a hard gate for acceptance.

### Non-scope (unchanged)
Matrix logic, schedule API, generators/creators, execution scheduler, schema, non-Facebook channels.

---

## CULTURE v1.1 Phase B (2026-01-29)

### Objective
Mon/Thu = library CULTURE (culture_fact), Tue = rotating language only; 90-day avoidance; no execution/preview/schema changes.

### Changed
- **utils/content_roles/culture_generator.py**: Added `category` to return of `pick_culture_for_slot()`.
- **scripts/automated_culture_creator.py**: Default look-ahead 4 weeks (28 days); docstring updated.
- **blueprints/planning_api_calendar_schedule.py**: Comment that Mon/Thu CULTURE (culture_fact) appear via role rail; Tuesday language resolver-only.

### Added
- **docs/CULTURE_V1_1_PHASE_B_REPORT.md**: Phase B report (schedule API excerpt, sample posting_queue rows, 90-day confirmation). Do not proceed beyond Phase B without new approval.

### Non-scope (unchanged)
Execution, preview, Facebook formatter, AUTHORITY_SHORT, DEPTH_LONG, schema/migrations, product/message logic.

---

## Centralized Date-Sensitive Posting Architecture (2026-01-29)

### Objective
Single source of truth for date validation; all publishing via centralized scheduler and platform publishers. No date logic in platform-specific code.

### Changed
- **scripts/scheduled_posting_executor.py**: Fixed undefined `scheduled_str` in debug log (use `scheduled_timestamp` or `scheduled_date` + `scheduled_time`).
- **scripts/posting_executor.py**: Replaced with thin wrapper that runs `scheduled_posting_executor.main()` for backward compatibility (monitoring, legacy cron).
- **blueprints/monitoring.py**: Added `scheduled_posting_executor` log file to posting log list.

### Already in place (no code change)
- **utils/platform_publishers.py**: `publish_to_facebook(queue_id)` handles weekly content, product, and message posts; stubs for Instagram/Twitter/LinkedIn. No date checking.
- **blueprints/automation_execute.py**: `execute_publish_to_facebook()` deprecated; delegates to `platform_publishers.publish_to_facebook()`.
- **scripts/automated_weekly_content_workflow.py**, **scripts/automated_product_post_workflow.py**: Only set status to `ready`; no direct publishing.
- **scripts/background_posting_monitor.sh**: Step 7 runs `scheduled_posting_executor.py`.

### Verification
- `python3 scripts/posting_executor.py` and `python3 scripts/scheduled_posting_executor.py` run successfully; scheduler validates dates and routes to platform publishers.

---

## Facebook Matrix v1 — Friday AUTHORITY_SHORT editorial hardening (2026-01-28)

### Objective
Tighten AUTHORITY_SHORT content quality, provenance, and reviewer visibility without changing scheduling, Matrix rules, or formatter flow.

### Changed
- **AuthorityShortGenerator** (`utils/content_roles/authority_short_generator.py`): Mechanical validation with rule IDs (emoji/hashtag/CTA/paragraph/length/list); strip-and-record for emoji/hashtags; CTA deny-list; 1–2 paragraphs, 200–400 chars target, hard cap 600; `validation_report_json` includes `source_used`, `source_excerpt`, `failed_rules`; on failure after 3 attempts returns `attempts`, `failed_rules`, `source_used`.
- **AuthorityShortCreator** (`scripts/automated_authority_short_creator.py`): On success sets `status = 'ready'`; on failure persists `validation_report_json` (attempts, failed_rules, source_used); logging includes `status=ready`, `source_type`, `failed_rules_count`.
- **Preview** (`utils/channel_preview/preview_renderer.py`, `blueprints/channel_preview_api.py`, `blueprints/preview_views.py`): Load `validation_report_json`; merge `source_type`, `source_excerpt`, `validation_failed_rules` into meta; Facebook uses canonical template `templates/channel_previews/facebook_feed.html` for API and full-page preview.
- **Facebook preview template** (`templates/channel_previews/facebook_feed.html`): Collapsible **Source** block (type, topic ID, article ID, optional excerpt); **Validator warnings** block when `validation_failed_rules` non-empty.

### Added
- **Parity proof** (`scripts/prove_preview_publish_parity.py`): Compares publish formatter vs preview formatter byte-for-byte; writes `docs/PARITY_PROOF_FACEBOOK_YYYYMMDD.txt`. Evidence: 3/3 PASS for AUTHORITY_SHORT (15505), DEPTH_LONG (11823), weekly_word (667).
- **Evidence artifacts**: `docs/SCHEDULE_EXCERPT_2026_W5_FRIDAY_ONLY_15505.json`, `docs/PREVIEW_API_15505.json`, `docs/PREVIEW_PAGE_15505_HEAD.html`, `docs/PREVIEW_INVALID_CHANNEL_15505.json`.

### Verification
- Friday 2026-W5 (id 15505): status=ready, source_type=rota_topic_article, topic_id/source_page_id/rota_year/rota_week set; preview shows Source (details) and no validator warnings when compliant.

---

## Phase 6 — Facebook Matrix v1 completion (role enforcement + REASSURANCE on Wed)

### Objective
O1: Every Facebook social post must have an explicit `posting_queue.role`; no item shows "UNSET_ROLE".  
O2: REASSURANCE (message) post appears on Wednesday and is visible in the calendar.

### Changed
- **Weekly language creation** (`utils/posting_queue_helpers.create_weekly_social_post`): Insert `role = 'CULTURE'` for weekly_word/phrase/insult.
- **Schedule API** (`blueprints/planning_api_calendar_schedule.py`): Product and message queries select and return `pq.role`; product/message schedule items include `role`. Weekly_word/phrase/insult (resolver-based) items include `role: 'CULTURE'`.

### Added
- **Phase 6 report script** (`scripts/phase6_role_and_message_report.py`): O1 Step 1 — list Facebook rows with role IS NULL; O2 Step 1 — list message posts for a test week (e.g. 2026-W5). Output: `docs/PHASE6_ROLE_AND_MESSAGE_REPORT_2026W5.txt`.
- **Role backfill** (`scripts/backfill_facebook_role_null.py`): Assign role by content_type (weekly_* → CULTURE, message → REASSURANCE, product → COMMERCE, depth_long → DEPTH_LONG). Dry-run: `python3 scripts/backfill_facebook_role_null.py --dry-run`; apply: `python3 scripts/backfill_facebook_role_null.py`.
- **Implementation report** (`docs/FACEBOOK_MATRIX_V1_IMPLEMENTATION_REPORT.md`): New §7 “Role enforcement (Phase 6)” — canonical mapping, enforcement at creation, schedule API surfacing role, REASSURANCE on Wednesday, backfill script.
- **Report-back** (`docs/PHASE6_REPORT_BACK.md`): What was broken, what was changed, what is now guaranteed.

### Verification
- O1: After `backfill_facebook_role_null.py`, query `posting_queue` for `platform='facebook'` and `content_type IN (...)` and `role IS NULL` → 0 rows.
- O2: For 2026-W5, after `backfill_matrix_v1_week.py --week 2026-W5`, the message (id 4631) is on Wednesday with role REASSURANCE and appears in the calendar.

---

## Facebook Matrix v1 scheduling drift fix (post–Phase 5.1)

### Objective
Make Facebook Matrix v1 the single source of truth for **what gets scheduled** each weekday (not only headers/labels). Remove “truthy headers + messy reality”: extra product posts on Tue/Thu, message on Sat, empty Wed/Fri.

### Changed
- **Schedule API** (`blueprints/planning_api_calendar_schedule.py`): Products filtered to Saturday only (`ISODOW = 6`); messages to Wednesday only (`ISODOW = 3`).
- **Message creator** (`scripts/automated_message_post_creator.py`): `publication_day = 3` (Wednesday); `get_next_publication_days()`; new message rows get `role = 'REASSURANCE'`.
- **Product creator** (`scripts/automated_product_post_creator.py`): For Facebook, product schedules overridden to Saturday only (`days = [6]`); new product rows get `role = 'COMMERCE'`.
- **Week-view** (`static/js/planning/calendar-week-view.js`): Message posts render on their `scheduled_date` weekday (Wed); removed UI-only role overrides — display uses `item.role` or `"UNSET_ROLE"` plus content_type.

### Added
- **Step 1 ground truth** (`scripts/step1_matrix_ground_truth.py`) and `docs/DELIVERABLE_A_MATRIX_GROUND_TRUTH.md`.
- **Call-chain map** (`docs/DELIVERABLE_B_CALL_CHAIN_MAP.md`).
- **UI overrides removed** (`docs/DELIVERABLE_C_UI_OVERRIDES_REMOVED.md`).
- **Backfill** (`scripts/backfill_matrix_v1_week.py`) and `docs/DELIVERABLE_D_BACKFILL.md`. Command for 2026-W5: `python3 scripts/backfill_matrix_v1_week.py --week 2026-W5`.
- **Implementation report addendum** (§6) in `docs/FACEBOOK_MATRIX_V1_IMPLEMENTATION_REPORT.md`: legacy scheduler changes, Matrix v1 as scheduling source of truth, verification checklist.

### Non-goals (this pass)
- No redesign of preview/angles/roles hierarchy; no new channels; no new post formats.
- Friday AUTHORITY_SHORT: schedule API already returns role-based posts by `scheduled_date`; creation path (authority_short scheduler) is out of scope.

---

## 2026-01-25 - Phase 4: Unified Channel Preview System

### Added
- **Unified Channel Preview System** - Single preview system for all social media channels
  - New API endpoint: `GET /api/preview/post/<post_id>` with channel/mode/variant parameters
  - Preview renderer (`utils/channel_preview/preview_renderer.py`) - Channel-agnostic rendering engine
  - Channel formatter registry with Facebook formatter (reuses publish formatting logic)
  - Generic fallback formatter and stubs for Instagram/X/TikTok
  - Channel preview templates (Facebook, Instagram, X, TikTok, Generic)
  - Universal preview modal component (reusable across all planning surfaces)
  - Preview buttons integrated into:
    - Content Control Board drill-down panel
    - Planning Calendar week view (unified item cards)
    - Posting Queue view
    - Sunday Slot panel (KB Topic Rota Editor)
- **Documentation:**
  - `docs/UNIFIED_CHANNEL_PREVIEW_SYSTEM.md` - Complete technical documentation
  - Updated `docs/CONTENT_ROLES_FRAMEWORK.md` - Note about preview system
  - Updated `docs/ANGLES_LAYER_FINAL_SPECIFICATION.md` - Note about preview as separate layer

### Changed
- `utils/platform_publishers.py::format_message_for_facebook()` - Now delegates to shared formatter function
- Facebook formatting logic extracted to `utils/channel_preview/formatters/facebook.py::_format_facebook_text()`
- Ensures consistency between preview and publish paths

### Technical Details
- Preview renderer is independent of Flask (uses standalone Jinja2 environment)
- Follows blog preview architecture pattern (template-based rendering)
- Formatters are reusable for both preview and publish paths
- All previews use HTML-based rendering (no client-side formatting)
- Blog preview system remains completely unchanged

---

## 2026-01-23 - Content Roles Framework (Foundation)

### Database Schema
- **Created `content_roles` table** with 5 canonical roles:
  - `REASSURANCE` - Reduce anxiety and friction
  - `AUTHORITY_SHORT` - Establish quiet credibility
  - `DEPTH_LONG` - Demonstrate embedded knowledge (requires weekly topic)
  - `CULTURE` - Provide personality and rhythm
  - `COMMERCE` - Make products visible and concrete
- **Extended `posting_queue` table** with role framework columns:
  - `role` (VARCHAR(50)) - References `content_roles.role_code`
  - `topic_id` (INTEGER) - References `kb_topics.id` (for topic-bound roles)
  - `source_page_id` (INTEGER) - References specific KB article
  - `rota_year` (INTEGER) - Year of rota week when post was generated
  - `rota_week` (INTEGER) - ISO week number when post was generated
- All new columns are **nullable** for backward compatibility
- Created indexes for efficient role and topic queries

### Documentation
- **Created comprehensive framework documentation** (`docs/CONTENT_ROLES_FRAMEWORK.md`)
  - Core concept and global rules
  - Detailed role definitions with constraints
  - Facebook Content Matrix (v1 - LOCKED)
  - Database schema reference
  - Implementation strategy (incremental)
- **Created KB page** (`templates/knowledge_base/backend/content_roles.html`)
  - User-facing documentation in Knowledge Base
  - Accessible at `/kb/backend/content_roles`
- **Added to KB navigation** in backend systems section

### Framework Principles
- **One post = one role only** - Roles are mutually exclusive
- **Roles are channel-agnostic and format-agnostic**
- **Roles are enforced by system logic**, not editorial habit
- **Scheduling logic operates on roles** (role-first, not topic-first)
- **QA logic validates against role constraints**

### Facebook Content Matrix (v1 - LOCKED)
- Defined 7 fixed schedule rails (Mon-Sun with specific times and roles)
- Role → Topic binding rules (only DEPTH_LONG requires weekly topic)
- Role quotas (soft constraints for validation)
- Formatting constraints per role
- Scheduler logic specification (role-first approach)

### Implementation Status
- ✅ **Phase 1: Foundation** - COMPLETE
  - Database schema implemented
  - Documentation created
  - Framework defined
- ⏳ **Phase 2: Facebook v1** - NEXT
  - Facebook schedule rails implementation
  - Role-specific prompt templates
  - Scheduler logic
  - Validation system

**Note:** Existing post creation processes are **NOT changed** by this migration. Framework will be implemented incrementally.

## 2026-01-25 - Content Roles Framework Phase 2: Sunday DEPTH_LONG Proof of Concept

### Core Implementation ✅
- **Schedule Rail Definition** (`config/content_roles_schedule_rails.py`)
  - Sunday 15:00 UK time, DEPTH_LONG role
  - Isolated from existing posting logic
- **Generation Pipeline** (`utils/content_roles/depth_long_generator.py`)
  - Fetches KB article text (bounded to ~2000 words)
  - Calls LLM with role-specific system prompts
  - Enforces topic_id and source_page_id requirements
  - Returns generated content with validation issues
- **Validation System** (`utils/content_roles/validator.py`)
  - Word count validation (120-220 words)
  - Paragraph count validation (≥3 paragraphs)
  - Forbidden phrase detection
  - Source page presence verification
  - Stores validation report as JSONB
- **API Endpoints** (`blueprints/content_roles_api.py`)
  - `/api/content-roles/facebook/sunday/check` - Check rail existence
  - `/api/content-roles/facebook/sunday/generate` - Generate post
  - `/api/content-roles/facebook/sunday/<id>/validate` - Re-validate
  - `/api/content-roles/facebook/sunday/<id>/approve` - Manual approval
  - `/api/content-roles/facebook/sunday/<id>/schedule` - Schedule for Sunday 15:00 UK

### Database Extensions
- **Added approval fields** to `posting_queue`:
  - `approved_at` (TIMESTAMP) - When post was approved
  - `approved_by` (VARCHAR(100)) - Who approved it
  - `validation_report_json` (JSONB) - Validation results

### UI Components
- **Sunday Slot Panel** in Topic Rota Editor (`/kb-topics/editor`)
  - Week selector
  - Topic and source article selection
  - Generate, Regenerate, Approve, Schedule actions
  - Status display and validation feedback
- **Content Control Board** (`/planning/content-control-board`)
  - Weekly matrix view (Days × Channels)
  - Role badges with tooltips
  - Status indicators (Empty, Generated, Validation failed, Approved, Scheduled, Published)
  - Drill-down panel with full post details
  - Role-centric view toggle
- **Roles Reference Page** (`/planning/content-roles`)
  - Detailed explanations of all 5 roles
  - Progressive disclosure design

### Workflow
- **Manual Generation** - User selects week, topic, source article
- **Automatic Validation** - Runs on generation, stores results
- **Manual Approval** - Required before scheduling (blocks if validation fails)
- **Scheduling** - Calculates Sunday date from rota week, sets scheduled_date/time
- **Isolated Lane** - Parallel to existing posting, no conflicts

### Status
- ✅ **Core Implementation** - COMPLETE
- ⏳ **Publishing Integration** - PENDING
  - Scheduled posts don't publish automatically yet
  - Need to extend `publish_to_facebook()` to handle `role='DEPTH_LONG'`
  - Need to ensure `scheduled_posting_executor.py` picks up role-based posts

**Note:** This is a proof of concept for one post type (Sunday DEPTH_LONG). All other posting logic remains unchanged.

## 2026-01-23 - KB Topic Rota System Enhancements

### Diversity Algorithm Improvements
- **Enhanced consecutive week penalties:**
  - Same topic type: 70% penalty (diversity_score × 0.3)
  - Same parent topic: 80% penalty (diversity_score × 0.2)
  - High similarity (>0.75): 60% penalty
  - Moderate similarity (>0.65): 40% penalty
- **Improved diversity checks:**
  - Most recent week checked more strictly
  - Includes parent_id and level in recent topics
  - Caps diversity score at 0.3 for consecutive similar topics
- **Better selection:**
  - Recent topics ordered most-recent-first
  - Lookback reduced to 4 weeks (from 6)
  - Similarity threshold lowered to 0.65 (from 0.7)

### Topic Exclusion & Usage Tracking
- Added `is_excluded` flag to prevent topics from appearing in rota generation
- Added `is_used` flag to track when topics have been used for content generation
- Used topics only reused after all unused topics have been used
- UI controls to exclude/include topics from library and timeline
- Group-level exclusion (exclude parent + all children at once)
- Reset Used button to clear all used flags when cycle completes

### Granular Topic Discovery
- Created `discover_hierarchical_topics_granular.py` script with improved parameters:
  - `broad_clusters=25` (increased from 15)
  - `min_broad_size=6` (lowered from 10)
  - `granular_threshold=0.82` (increased from 0.75)
  - `min_granular_size=2` (lowered from 3)
- Results: 25 Level 1 topics (instead of 8), average 27.8 articles per topic (instead of 86.4)

### UI Integration
- Topic Rota Editor integrated into BlogForge house style (extends base.html)
- Added to header navigation (Content dropdown)
- Added to homepage (Calendar & Planning section)
- Filter improvements: hides parent groups when all topics filtered out

## 2026-01-23 - KB Topic Display in Calendar Week View

### Added
- **Week Topic Display:** KB topic now displayed in calendar week view date bar
  - Shows below week date range (Year, Week, dates)
  - Centered display with topic name
  - Includes "edit..." link to rota editor (`/kb-topics/editor`)
  - Automatically loads topic for current week from rota
  - Hides when no topic assigned to week
  - API endpoint: `GET /api/kb-topics/rota?year=X&week=Y`

### Fixed
- **Navigation Robustness:** Changed week navigation to use URL updates instead of JavaScript handlers
  - Navigation buttons now update URL directly and reload page
  - More reliable - works even if JavaScript fails
  - Week loading now reads from URL parameters first (not WeekContext)
- **API Response:** Fixed `/api/kb-topics/rota` to return 200 OK instead of 404 when no topic exists
  - Prevents browser console errors for weeks without topics
  - Returns `{success: false}` in JSON body instead of 404 status

### Technical Details
- Topic display element: `#week-topic` in week view template
- Function: `loadWeekTopic(year, weekNumber)` in `calendar-week-view.js`
- Navigation: `navigateWeek(delta)` function updates URL parameters
- Styling: Centered flex layout with border separator

---

## 2026-01-22 - KB Topic Rota System: Hierarchical Discovery & Enhanced Rota

### Enhanced
- **Hierarchical Topic Discovery:** ✅ **IMPLEMENTED** - Multi-level topic discovery system
  - **Level 1:** Broad themes (e.g., "Tartan Patterns & Variations")
  - **Level 2:** Granular sub-topics (e.g., "Line Widths and Balance in Tartan Design")
  - Uses hierarchical clustering with configurable thresholds (0.80-0.90 for ultra-granular topics)
  - Creates parent-child relationships in database schema
  - New script: `scripts/discover_hierarchical_topics.py`
  - New module: `utils/kb_topic_discovery/hierarchical_discovery.py`

- **LLM-Based Semantic Topic Naming:** ✅ **IMPLEMENTED**
  - Uses Ollama (llama3.2:latest) for semantic understanding
  - Generates meaningful, contextualized topic names (not keyword-based)
  - Understands concepts and relationships, not just word groups
  - Examples: "Line Widths and Balance in Tartan Design" (semantic) vs "Tartan Kilt Your" (avoided)

- **Enhanced Rota Generator:** ✅ **UPDATED**
  - **Default behavior:** Includes all topics in rotation (2.8-year rotation for 144 topics)
  - Auto-calculates weeks to include all topics when `include_all_topics=True`
  - Prioritizes unused topics to ensure complete coverage
  - Configurable: Can still generate shorter rotations (e.g., 52 weeks) if needed
  - Parameters: `weeks=None` (auto-calculate), `include_all_topics=True` (default)

- **Database Schema Updates:**
  - Added hierarchical columns to `kb_topics`: `parent_id`, `level`, `is_broad`
  - Supports parent-child relationships between broad and granular topics

### Current System State
- **144 topics discovered:** 8 broad themes (Level 1), 136 granular sub-topics (Level 2)
- **2.8-year rota generated:** 144 weeks, includes all topics
- **Semantic topic names:** LLM-generated, meaning-based
- **Hierarchical structure:** Parent-child relationships established

### Documentation Updates
- Updated `docs/KB_TOPIC_ROTA_SYSTEM.md` with hierarchical discovery details
- Updated `templates/knowledge_base/backend/topic_rota.html` with new features
- Added hierarchical discovery script documentation

---

## 2026-01-22 - KB Topic Rota System Implementation

### Added
- **KB Topic Rota System:** ✅ **FULLY IMPLEMENTED** - Perpetual topic discovery and weekly scheduling system
  - **Feasibility Analysis:** `docs/KB_TOPIC_EXTRACTION_FEASIBILITY.md` - Confirms vectorized KB data supports topic extraction
  - **Implementation Plan:** `docs/KB_TOPIC_ROTA_SYSTEM_IMPLEMENTATION_PLAN.md` - Detailed 5-6 week implementation plan
  - **System Goal:** Perpetual system that discovers new angles in KB data and distributes them in diverse weekly schedule
  - **Integration:** Designed to feed separate social media production processes for channel-specific formatting

### Key Features Planned
- **Unsupervised Topic Discovery:** Clustering KB articles by semantic similarity (no manual topic lists)
- **Diversity Scheduling:** Ensures non-repetitive, interesting weekly rota (avoids similar topics in consecutive weeks)
- **Cross-Category Topics:** Identifies recurring themes that span multiple KB sections
- **Content Aggregation:** Combines relevant content from multiple articles for each topic
- **Social Media Interface:** Provides topics + aggregated content for channel-specific formatting (Facebook, Instagram, Twitter, Blog)

### Technical Approach
- **Clustering:** K-means, DBSCAN, or hierarchical clustering on KB embeddings
- **Topic Naming:** LLM-based generation from cluster content
- **Diversity Algorithm:** Similarity-based scoring to ensure variety
- **Perpetual Operation:** Automatic discovery when new KB content added
- **Database Schema:** 5 new tables (topics, similarity, rota, history, content)

### Documentation
- `docs/KB_TOPIC_EXTRACTION_FEASIBILITY.md` - Feasibility analysis and Q&A
- `docs/KB_TOPIC_ROTA_SYSTEM_IMPLEMENTATION_PLAN.md` - Complete implementation plan
- Updated `templates/knowledge_base/backend/vector_search.html` - Added future topic discovery section

### Implementation
- **Database Schema:** 5 tables created (topics, similarity, rota, history, content)
- **Core Modules:** Clustering, similarity, diversity, rota generation, content aggregation
- **API Endpoints:** 5 endpoints for rota management and content retrieval
- **Scripts:** Discovery script and automated runner for perpetual operation
- **Integration:** Registered in unified_app.py and background_posting_monitor.sh

### Documentation
- `docs/KB_TOPIC_ROTA_SYSTEM.md` - Complete technical documentation
- `templates/knowledge_base/backend/topic_rota.html` - KB page for system
- Updated vector search KB page to reflect implementation
- Updated implementation plan to reflect completion

### Status
✅ **IMPLEMENTED** - System fully operational and ready for use

---

## 2026-01-22 - Timeline Filtering & Message Posts Display Fixes

### Fixed
- **Timeline Non-Compliant Posts**: Fixed Upcoming Posts timeline showing non-compliant and duplicate posts
  - **Root Cause**: Timeline API was showing all posts from `posting_queue` without filtering for schedule compliance
  - **Solution**: 
    - Filter out weekly content posts on wrong weekdays (weekly_word must be Monday, weekly_phrase must be Wednesday, weekly_insult must be Friday)
    - Deduplicate posts: keep only one post per content_type per day (prefers oldest when duplicates exist)
    - Log filtered posts for debugging
- **Message Posts Display**: Fixed message posts showing "message #4630" instead of actual message text
  - **Root Cause**: Timeline API wasn't including `generated_content` field and title logic didn't handle message posts
  - **Solution**: 
    - Added `generated_content` to timeline API query
    - Use first line of `generated_content` as title for message posts (up to 60 chars)
    - Added 'message' to content type display mapping

### Changed
- **Timeline API** (`blueprints/posts.py::api_posts_timeline()`):
  - Added weekday compliance filtering for weekly content posts
  - Added deduplication logic (one post per content_type per day)
  - Added `generated_content` field to query for message posts
  - Enhanced title determination to handle message posts
- **Status Display Consistency**: Removed status display for message posts (like language posts)
  - Messages are automated and don't need status shown (redundant)
  - Keeps UI consistent across all automated post types
- **Message Post Status**: Changed message posts to be created as 'ready' instead of 'draft'
  - Messages are text-only and don't need workflow (no image generation)
  - Updated existing draft message posts to 'ready' status

### Technical Details
- File: `blueprints/posts.py`
- API endpoint: `GET /api/posts/timeline`
- Filtering rules:
  - `weekly_word`: Monday only (weekday 1)
  - `weekly_phrase`: Wednesday only (weekday 3)
  - `weekly_insult`: Friday only (weekday 5)
  - Deduplication: keeps oldest post when multiple exist for same type/day
- File: `static/js/planning/unified-item-card.js` - Removed status display for messages
- File: `scripts/automated_message_post_creator.py` - Create messages as 'ready' status

### Status
✅ **PRODUCTION READY** - Timeline now only shows compliant posts following schedule rules

---

## 2026-01-22 - Publication Schedule Scheduled Time Display Fix

### Fixed
- **Scheduled Time Display**: Fixed issue where Word and Phrase posts weren't showing scheduled times in publication schedule view
  - **Root Cause**: Published posts were excluded from queue lookup, config had `publication_time = NULL` for weekly content, and weird times (00:04) from auto-publishing were being displayed
  - **Solution**: 
    - Include published posts in queue lookup to get historical times
    - Prefer "normal" times (hour >= 8) over weird times (like 00:04 from auto-publishing)
    - Default to 09:00 for weekly content if no time found in queue or config
    - Filter out weird times in favor of intended times
- **Time Resolution Logic**: Enhanced to check multiple sources in priority order:
  1. `posting_queue` for non-published automated Facebook posts (prefer normal times)
  2. `post_type_channel_config.publication_time` (config time)
  3. Default 09:00 for weekly content (matches creation script default)

### Changed
- **Publication Schedule API** (`blueprints/publication_dashboard.py`):
  - Query now includes published posts (not just non-published)
  - Added logic to prefer normal times (hour >= 8) over weird times
  - Added default fallback to 09:00 for weekly content
  - Improved time lookup to handle multiple posts per type/day

### Technical Details
- File: `blueprints/publication_dashboard.py`
- API endpoint: `GET /publication/api/dashboard/schedule`
- All automated Facebook posts now show scheduled times correctly
- Documentation: `docs/PUBLICATION_SCHEDULE_VIEW.md` - Complete reference guide

### Status
✅ **PRODUCTION READY** - All scheduled times now display correctly for Word, Phrase, Insult, and Product posts

---

## 2026-01-20 - Weekly Content Image Font & Layout Adjustments (Final)

### Changed
- **Scots Content Font Sizes**: Increased by 50%
  - **Word**: 324pt (was 216pt, originally 144pt)
  - **Phrase/Insult**: 117pt (was 78pt, originally 52pt) - both use same size for consistency
- **Translation Font Sizes**: Increased by 50%
  - **Word**: 54pt (was 36pt)
  - **Phrase/Insult**: 51pt (was 34pt)
- **Examples Quotes**: 48pt (50% bigger, was 32pt) with max width 1520px (was 760px) to reduce wrapping
- **Provenance Text**: 39pt (50% bigger, was 26pt) with max width 1440px (was 720px) to reduce wrapping
- **Translation Position**: Moved down 50px
- **Provenance Position**: Moved down 50px
- **Phrase/Insult Alignment**: Both use same Y position (198px) to prevent title overlap

### Technical Details
- File: `utils/weekly_content_image_renderer_v2.py`
- All changes maintain the two-tier layout structure while improving readability
- Phrase and Insult now use fixed Y position (198px) instead of vertical centering to ensure consistent alignment

---

## 2026-01-20 - Automated Posting Control System

### Added
- **Master Switch for Automated Posting**: New system-wide control to enable/disable all automated posting
  - Database table: `system_config` with key `automated_posting_enabled`
  - UI controls on homepage "Calendar & Planning" panel (top right)
  - UI controls on calendar page header (top right)
  - Toggle switch, status indicator, and manual trigger button
- **API Endpoints**: New endpoints for controlling automated posting
  - `GET /api/automated-posting/status` - Get current state
  - `POST /api/automated-posting/toggle` - Toggle on/off
  - `POST /api/automated-posting/trigger` - Manual publish (bypasses switch)
- **Scheduled Posting Executor Enhancement**: Updated to check automation switch before publishing
  - Returns early with all posts marked as 'skipped' when switch is OFF
  - Supports `--bypass-switch` flag for manual triggers
  - Comprehensive logging when posting is disabled

### Changed
- **Scheduled Posting Executor**: Now checks `automated_posting_enabled` switch before any publishing
  - File: `scripts/scheduled_posting_executor.py`
  - Method: `process_due_posts()` now has early return when switch is OFF
  - All automated entry points respect the switch

### Technical Details
- Migration: `migrations/add_automated_posting_control.sql`
- Blueprint: `blueprints/automated_posting_api.py`
- Documentation: `docs/AUTOMATED_POSTING_CONTROL_SYSTEM.md`
- Updated KB templates: `templates/knowledge_base/workflows/automated_posting.html`, `templates/knowledge_base/channels/facebook.html`
- Updated docs: `docs/AUTOMATED_POSTING_SIMPLIFIED.md`

### Security
- Default state: ENABLED (safer - allows posting)
- Error handling: Defaults to ENABLED on database errors (safer)
- Bypass flag: Only set via manual API trigger (intentional)

---

## 2026-01-27 - Facebook Matrix v1 Alignment (Planning UIs)

### Added
- **Facebook Matrix v1 Config:** New `utils/facebook_matrix_v1.py` module encoding the authoritative Mon–Sun mapping of ISO weekday → Role (+ fixed Angle and topic source hints) for Facebook.
- **Matrix v1 Implementation Report:** `docs/FACEBOOK_MATRIX_V1_IMPLEMENTATION_REPORT.md` documenting the matrix, DRIVER/UI_ONLY/RETIRE classifications, and planning UI behaviour.

### Changed
- **Calendar Week View (Week Tab):**
  - Updated `static/js/planning/calendar-week-view.js` so the “dates line” (day headers) shows **Role-first, Angle-second**, with optional legacy `weekly_social_focus` labels as a decorative suffix only (e.g. `CULTURE — Language: Word — From the Blog`).
  - Updated Social Posts row card labelling so weekly language, product, message, and DEPTH_LONG items display Role as the primary label and language/product/deep dive as secondary Angle descriptors (e.g. `COMMERCE — Product`, `REASSURANCE — Message`, `DEPTH_LONG — Deep Dive`).
- **Phase 5 Audit Doc:** Extended `docs/PHASE_5_FACEBOOK_MATRIX_AND_UI_SOURCE_OF_TRUTH_AUDIT.md` with an explicit DRIVER / UI_ONLY / RETIRE classification table for Facebook-related systems (roles, weekly_social_focus, weekly language types, product scheduling, calendar_themes, legacy Deep Dive flags).

### Notes
- Behaviour of Sunday DEPTH_LONG generation/validation/scheduling is unchanged and remains rota-authoritative.
- Weekly language posts (Word, Phrase, Insult) still appear three times per week; they are now framed explicitly as CULTURE-role Angles in the planning UI rather than pseudo-roles.

---

## 2026-01-27 - Phase 5.1: Calendar Week-View Header Misalignment Fix

### Fixed
- **Dates-line day→Matrix mapping:** Headers now derive Role/Angle from the **actual column date** using ISO weekday (Mon=1 … Sun=7). Added `getISOWeekday(date)` and `renderMatrixHeaders(dates)` so the “dates line” is driven by `dates[i]` and `FACEBOOK_MATRIX_*[iso]` only.
- **Legacy labels removed from headers:** `weekly_social_focus` is no longer read or displayed in the calendar dates line; headers show only `ROLE` and Angle hint (e.g. `CULTURE — Language: Word`, `REASSURANCE`, `DEPTH_LONG — Deep Dive`).
- **Language placement vs Matrix v1:** Phrase and Insult were on Wed (day 3) and Fri (day 5). They are now on **Tue (day 2)** and **Thu (day 4)** to match Matrix v1 (Mon=Word, Tue=Phrase, Thu=Insult).

### Added
- **Debug table:** When the week view loads, the console logs a 7-line table per column: `Mon 2026-01-26 getDay=? iso=? matrixKey=? role=? angle=?` so ISO mapping can be verified.
- **Docs:** `docs/FACEBOOK_MATRIX_V1_IMPLEMENTATION_REPORT.md` now states: “Matrix indexing uses ISO weekday Mon=1 … Sun=7; JS converts Date.getDay() accordingly.”

### Technical details
- `static/js/planning/calendar-week-view.js`: `getISOWeekday()`, `renderMatrixHeaders(dates)`, placement of phrase/insult to day 2 and 4, debug log, and removal of legacy label usage in headers.
- `renderSocialFocuses(focuses)` is now a no-op for the header path; the modal may still call it after refetch, but the header is always updated by `renderMatrixHeaders(dates)` in `loadWeek`.

---

## 2026-01-19 - Calendar Item Navigation Improvements

### Added
- **Pipeline Button**: Calendar items with existing posts now display a pipeline button (sitemap icon) that navigates directly to the first workflow stage
  - Recipes: Navigate to `/posts/{postId}/sections/drafting` (recipes skip planning stages)
  - Themes: Navigate to `/planning/posts/{postId}/calendar/ideas`
  - Profiles: Navigate to `/planning/posts/{postId}/calendar/taxonomy`
- **Clickable Titles**: Item titles are now clickable when a post exists, providing an alternative way to navigate to the pipeline

### Changed
- **Info Button Behavior**: Info button now only appears for items without posts (where it opens the modal). Items with posts use the pipeline button instead
- **Recipe Navigation**: Fixed recipe navigation to go directly to drafting stage (`/posts/{postId}/sections/drafting`) instead of attempting to access taxonomy (which redirects)

### Fixed
- **Recipe Info Button**: Fixed broken info button for recipes - now navigates to pipeline instead of non-existent page
- **Pipeline Button Function**: Fixed pipeline button to properly navigate to first workflow stage with year/week parameters preserved
- **WorkflowNavigation Duplicate Error**: Fixed duplicate class definition error by adding proper guards
- **Recipe Title Display**: Fixed recipe title not displaying in header - now fetches and displays post title correctly
- **API Ideas Endpoint**: Fixed SQL GROUP BY error in `/planning/api/calendar/ideas/week/{week}` endpoint that was causing 500 errors on calendar page load

### Technical Details
- Updated `static/js/planning/unified-item-card.js` with `navigateToPipeline()` function
- Updated `templates/planning/calendar/includes/publication_schedule_scripts.html` with navigation logic
- Fixed `normalizedSubstage` undefined error in `blog-pipeline-header.js`
- Added recipe title fetching in header initialization

---

## 2025-01-19 - Post Status Management and Workflow Improvements

### Fixed
- **Critical Bug:** Post reuse logic now correctly excludes published posts
  - All post lookup queries now only reuse posts in workflow states: `draft`, `in_process` (corrected enum values)
  - Published posts are never reused - new posts always start as `draft`
  - Fixed in: `blueprints/planning_api_posts.py`, `blueprints/automation_core.py`, `blueprints/automation_calendar.py`
  - Added helper functions in `utils/post_status_helpers.py` for consistent status validation
  - Documentation: `docs/POST_STATUS_MANAGEMENT.md`
- **Subtitle Field Integration:** Updated all pages to use `subtitle` field instead of `expanded_idea`
  - Ideas page: Auto-generates and saves subtitle (expanded idea description) from theme
  - Taxonomy page: Checks for subtitle before allowing taxonomy generation
  - Brainstorm page: Uses subtitle when generating topics
  - Fixed auto-save to persist generated subtitles immediately
- **Workflow Navigation:** Fixed Next button routing
  - Corrected navigation from Ideas → Taxonomy (was incorrectly going to Brainstorm)
  - Updated to build URLs directly from substage keys instead of using API incorrectly
- **Preview Link:** Preview link now updates dynamically with correct post ID
- **Taxonomy Display:** Header now shows both category and sub-category (e.g., "Culture & Life: Modern Celebrations")
- **Taxonomy Auto-Save:** Removed manual save button, implemented auto-save with visual feedback

### Added
- `utils/post_status_helpers.py` - Helper functions for post status validation
- `docs/POST_STATUS_MANAGEMENT.md` - Complete documentation of status flow and reuse rules

### Changed
- **Ideas Page:** Subtitle auto-generates from theme and auto-saves immediately after generation
- **Taxonomy Page:** Auto-saves taxonomy assignments when any field changes (debounced 500ms)
- **Brainstorm Page:** Now uses subtitle field instead of expanded_idea endpoint

---

## 2026-01-18 - Text Wrapping for Weekly Content Images

### Changed
- **Image Text Wrapping**: Implemented automatic text wrapping for long phrases and insults
  - Always uses full 96pt font size (no font size reduction)
  - Manual pre-processing splits text into lines at word boundaries when text exceeds 55 characters per line
  - Uses ImageMagick `label:` with actual newlines (`\n`) for multi-line text rendering
  - Prevents text truncation at image edges for all content types (words, phrases, insults)
- **Image Generation**: Updated `utils/weekly_content_image_renderer.py` to handle text wrapping automatically
  - Wrapping applies to all weekly content types (weekly_word, weekly_phrase, weekly_insult)
  - Integrated into automated posting workflow via `execute_optimize_for_facebook()`

### Technical Details
- **Wrapping Logic**: Pre-processes `scots_text` to split into lines at word boundaries
- **Character Limit**: 55 characters per line (safe estimate for 96pt italic Baskerville at 800px width)
- **Font Size**: Always maintains 96pt font size regardless of text length
- **Implementation**: Uses ImageMagick `label:` operation with newline characters for multi-line rendering

### Status
✅ **PRODUCTION READY** - Text wrapping fully integrated into automated posting workflow

---

## 2026-01-18 - Monitoring System with Status Indicator and Reporting

### Added
- **Monitoring Module in Header**: Traffic light status indicator (green=running, red=stopped) in top right of all pages
- **Monitoring Report Page**: Full event monitoring with filtering (`/monitoring/report`)
  - Filter tabs: All Events, Automated Postings, Administrative
  - Real-time status updates (every 30s for status, 60s for events)
  - Start/Stop controls for background monitor
- **Enhanced Publication Messages**: Detailed log messages showing queue_id, content_type, pages count, and content preview
- **API Endpoints**: 
  - `GET /monitoring/status` - Get monitoring status
  - `POST /monitoring/start` - Start monitoring
  - `POST /monitoring/stop` - Stop monitoring
  - `GET /monitoring/api/events` - Get events with filtering
- **Documentation**: `docs/MONITORING_SYSTEM_REFERENCE.md` - Complete monitoring system reference

### Changed
- **Publication Log Messages**: Enhanced to include context (queue_id, content_type, pages, content preview)
- **Event Filtering**: Strict filtering for Automated Postings tab to show only actual publication events
- **Background Monitor Log Parsing**: Distinguishes monitor messages from script outputs

### Technical Details
- **Blueprint**: `blueprints/monitoring.py` - All monitoring endpoints
- **Templates**: `templates/monitoring/report.html`, `templates/shared/header.html` (monitoring module)
- **JavaScript**: `static/js/shared/monitoring-module.js` - Status updates
- **Event Categories**: 
  - `posting` - Actual publication events (weekly content, product posts)
  - `admin` - Infrastructure/monitoring messages
- **Log Sources**: Reads from individual script log files (last 200 lines each)

### Status
✅ **PRODUCTION READY** - Full monitoring system operational with status indicator and detailed reporting

---

## 2026-01-17 - Weekly Content Full Automation System

### Added
- **Full Automation Pipeline**: Weekly content now publishes automatically with zero manual intervention
  - **Automatic Creation**: `scripts/automated_weekly_content_creator.py` - Creates posting_queue entries 1 week in advance based on calendar schedule
  - **Automatic Workflow**: `scripts/automated_weekly_content_workflow.py` - Executes all workflow stages automatically (format → caption → image → publish)
  - **Automatic Publishing**: Updated `scripts/posting_executor.py` to handle weekly content posts using weekly content workflow
- **Background Monitor Integration**: Updated `scripts/background_posting_monitor.sh` to include weekly content automation steps
- **Documentation**: 
  - `docs/WEEKLY_CONTENT_AUTOMATION_COMPLETE.md` - Complete automation guide
  - Updated technical reference with automation details

### Changed
- **Posting Executor**: Now detects weekly content posts and uses appropriate workflow (`execute_publish_to_facebook` for weekly content, `execute_facebook_post` for products)
- **Background Monitor**: Added weekly content creation and workflow execution steps

### Technical Details
- **Creation**: Checks upcoming 7 days, resolves items from calendar schedule, creates draft posts with scheduled_date/time
- **Workflow**: Processes up to 10 draft posts per run, executes all stages, publishes if due or sets to 'ready'
- **Publishing**: Handles both `status='ready'` and `status='pending'`, checks scheduled_date/time, publishes at correct time
- **Monitoring**: All scripts log to dedicated log files for troubleshooting

### Test Results
✅ Created 6 posts for 2 upcoming weeks automatically  
✅ Generated images and captions for all posts  
✅ Published posts that were due (scheduled date in past)  
✅ Set future posts to 'ready' status  
✅ All posts published to both Facebook pages successfully

### Status
✅ **FULLY AUTOMATED** - System requires zero manual intervention. Weekly content publishes automatically on schedule.

---

## 2026-01-17 - Weekly Content Image & Caption Generation System

### Added
- **Weekly Content Social Media Automation**: Complete system for automated Facebook posting of weekly word/phrase/insult content
  - **Image Generation**: Square 1080×1080 images using ImageMagick with branded typography
  - **Caption Generation**: Ollama-powered caption generation with 30 style variation prompts
  - **Facebook Integration**: Posts to both Facebook pages (Scotweb CLAN and CLAN by Scotweb) using `/photos` endpoint
- **Database Schema**: Extended `posting_queue` table with metadata columns:
  - `generated_caption`, `pinned_comment`, `chosen_prompt_style_id`
  - `image_path`, `ollama_model`, `generation_timestamp`
- **Configuration Files**:
  - `config/weekly_content_image_config.py` - Styling configuration (colors, fonts, layout, logo)
  - `config/weekly_content_caption_prompts.py` - System prompt and 30 variation prompts
- **Utility Modules**:
  - `utils/weekly_content_data_extractor.py` - Extracts data from `calendar_ideas`
  - `utils/weekly_content_caption_generator.py` - Generates captions using Ollama
  - `utils/weekly_content_image_renderer.py` - Generates images using ImageMagick
- **Substage Execution Functions** (in `blueprints/automation_execute.py`):
  - `execute_format_for_facebook()` - Formats content for Facebook
  - `execute_generate_caption()` - Generates caption with Ollama
  - `execute_add_translation()` - Verifies translation
  - `execute_add_hashtags()` - Adds hashtags to caption
  - `execute_optimize_for_facebook()` - Generates square image
  - `execute_publish_to_facebook()` - Posts to both Facebook pages
- **Workflow Integration**: Updated `config/output_channel_stages.py` to include `generate_caption` in weekly content Facebook workflows
- **Documentation**:
  - `docs/WEEKLY_CONTENT_SYSTEM_TECHNICAL_REFERENCE.md` - Complete technical reference
  - `docs/temp/WEEKLY_CONTENT_IMAGE_CAPTION_IMPLEMENTATION_PLAN.md` - Implementation plan
  - `docs/temp/GO_LIVE_CHECKLIST.md` - Go-live checklist
  - `docs/temp/TESTING_GUIDE.md` - Testing procedures

### Changed
- **ImageMagick Compatibility**: Updated to use `magick` command (v7 compatible)
- **Logo Handling**: Improved error handling for missing logo files
- **Font Configuration**: Updated to use system fonts (Arial, Baskerville) for compatibility
- **Workflow Configuration**: Added `generate_caption` substage to weekly content Facebook pipelines

### Technical Details
- **Image Generation**: 1080×1080 square images with layered typography (header, main phrase, translation, footer, logo)
- **Caption Rules**: Exactly 1 question, includes translation, max 1 hashtag, friendly Scots cultural tone
- **Facebook Posting**: Uses same pattern as product posting - posts to both pages using `/photos` endpoint
- **Image URLs**: Converts local file paths to public URLs for Facebook API
- **Error Handling**: Graceful fallbacks for missing logo, Ollama failures, partial Facebook posting failures

### Files Created
- `config/weekly_content_image_config.py`
- `config/weekly_content_caption_prompts.py`
- `utils/weekly_content_data_extractor.py`
- `utils/weekly_content_caption_generator.py`
- `utils/weekly_content_image_renderer.py`
- `migrations/20260117_add_weekly_content_metadata_to_posting_queue.sql`
- `migrations/run_migration_weekly_content_metadata.py`
- `scripts/test_weekly_content_system.py`
- `docs/WEEKLY_CONTENT_SYSTEM_TECHNICAL_REFERENCE.md`

### Files Modified
- `blueprints/automation_execute.py` - Added 6 substage execution functions
- `blueprints/automation_core.py` - Updated substage router
- `utils/posting_queue_helpers.py` - Added `get_posting_queue_row()` helper
- `config/output_channel_stages.py` - Added `generate_caption` to workflows

### Migration
- **Database**: `migrations/20260117_add_weekly_content_metadata_to_posting_queue.sql` - Adds 6 metadata columns and 2 indexes

### Status
✅ **Production Ready** - All components implemented and tested. Ready for end-to-end testing with real data.

---

## 2025-12-18 - Unified Output Framework: Completion Phase

### Added
- **Weekly Social Post Creation**: `automation_core.py::create_post_from_item()` now creates `posting_queue` rows for weekly content when social-only formats are detected, with proper `idea_id` linkage
- **Documentation**: Created reference docs and updated core system documentation
  - `docs/PUBLICATION_STATUS_RESOLVER_REFERENCE.md` - Complete API reference for status resolver
  - `docs/WEEKLY_SOCIAL_POST_CREATION_AUDIT.md` - Audit of all creation points
  - `docs/DOCUMENTATION_CLEANUP_AUDIT.md` - Documentation cleanup analysis
  - `docs/STATUS_DISPLAY_VERIFICATION_REPORT.md` - Testing and verification results

### Changed
- **Documentation Updates**:
  - `docs/CALENDAR_SYSTEM_AUDIT.md` - Updated to clarify `calendar_week_items` is canonical, added status resolver section
  - `docs/CALENDAR_SCHEDULING_ENDPOINTS.md` - Documented status enrichment in scheduling API
  - `docs/UNIFIED_OUTPUT_IMPLEMENTATION_LOG.md` - Documented Phase 1.2 completion

### Verified
- **Status Display Consistency**: All calendar views (week view, scheduling, publication schedule) show consistent status
- **Triskelion Example**: Previously problematic theme now shows correct "published" status across all views
- **Social Output Linkage**: `SocialOutputView` correctly handles both `idea_id=NULL` (legacy) and `idea_id IS NOT NULL` (new) cases

### Technical Details
- Weekly social posts are created automatically when `create_post_from_item` is called for weekly content with social-only formats
- All weekly social posts created through this flow have `idea_id` properly populated
- Status resolver ensures ID-only matching with no title heuristics
- All documentation is now current and accurate

## 2025-12-18 - Unified Output Framework: Social Outputs Integration

### Added
- **Social Output View Helper** (`utils/social_output_view.py`): Unified abstraction for social Outputs (posting_queue rows) that exposes them in the same conceptual framework as blog Outputs
  - `get_social_outputs_for_week()` - returns all social Outputs for a week slot
  - `get_social_outputs_for_content_item()` - returns social Outputs for a specific Content Item
  - Normalizes channel, content_format, status, and Content Item linkage (ID-only)
- **Posting Queue Helpers** (`utils/posting_queue_helpers.py`): Utility functions for creating weekly social posts with proper `idea_id` linkage
  - `create_weekly_social_post()` - creates posting_queue row with idea_id for weekly Content Items
  - `update_weekly_social_post_idea_id()` - backfill helper for existing rows
- **Schema Migration**: Added `idea_id` column to `posting_queue` table for ID-only linkage to weekly Content Items (`calendar_ideas.id`)

### Changed
- **Publication Dashboard**: Refactored to use `SocialOutputView` helper instead of ad-hoc `posting_queue` queries
  - All social Outputs (products + weekly items) now use unified abstraction
  - Status normalization is consistent via `normalize_queue_status`
  - Content Item linkage is explicit (ID-only, no text matching)
- **Documentation**: Created/updated unified output framework docs
  - `docs/SOCIAL_OUTPUT_VIEW.md` - design and API reference
  - `docs/UNIFIED_OUTPUT_DATA_MODEL.md` - notes `idea_id` linkage for weekly items
  - `docs/UNIFIED_OUTPUT_REFACTOR_PLAN.md` - added Phase 4 section
  - `docs/UNIFIED_OUTPUT_IMPLEMENTATION_LOG.md` - tracks all changes

### Technical Details
- Migration `20251218_add_idea_id_to_posting_queue.sql` adds nullable `idea_id` column + index
- `SocialOutputView` maps `product_id` → `content_type="product"` and `idea_id` → `content_type="weekly_word/phrase/insult"`
- Weekly social posts created going forward should use `create_weekly_social_post()` helper to ensure `idea_id` is populated
- Existing weekly social posts will have `idea_id=NULL` until recreated; `SocialOutputView` handles both cases gracefully

## 2025-12-15 - Preview Page Fixes & Calendar System Migration Completion

### Fixed
- **Preview Cross-Promotion Widgets**: Moved widget HTML auto-generation from publish-only path to preview loader (`cross_promotion_loader.py`) so x-marketing widgets appear in preview without needing to publish first
- **Image Captions Priority**: Section `image_captions` from authoring page now takes priority over generic archive captions in preview
- **Brainstorm Timeout**: Reduced comprehensive brainstorm from 50 to 30 topics, surface real LLM error messages instead of generic "Failed to generate topics"
- **Section Structure Validation**: Reject sections with empty title/description and return clear error messages
- **Header Image Prompt Assembly**: Fixed 500 errors by removing `calendar_schedule` fallbacks, now uses `calendar_week_selection_v2` view exclusively
- **Preview Page**: Removed `calendar_schedule` dependency from `post_data_loader.py` that was causing 500 errors

### Changed
- **Calendar System Migration**: Completed removal of all `calendar_schedule` fallbacks from:
  - `automation_calendar.py` (hard-disabled legacy endpoints with 410 responses)
  - `posts.py` (post listing now uses `calendar_week_posts_v2` or bare post rows)
  - `planning_api_brainstorm.py` (theme context now uses `calendar_week_selection_v2` only)
  - `header/api_prompt_compilation.py` (prompt assembly uses V2 structures exclusively)

### Technical Details
- Preview now auto-selects random category/product if none configured and generates widget HTML on-the-fly
- Image caption logic prioritizes `post_section.image_captions` over `image_archive.caption`
- All calendar-related endpoints now fail clearly with 500 errors if V2 tables/views are missing (no silent fallbacks)

## 2025-12-11 - Calendar Legends & Action Rows Unification

### Changed
- Standardized calendar legend pills (Theme, Recipe, Profile, Word, Phrase, Insult, Annual, Special, Syndication) across week view, scheduling, and publication schedule tabs with consistent colors.
- Updated publication schedule cards to use a compact action row with a single status pill above the Play/Rocket/Info buttons and tightened event binding to prevent duplicate handlers after create/update flows.
- Added a compact action row to the One-Click Publication page with create/open/calendar controls and shared status pill styling for calendar-linked posts.

### Notes
- Ensures all planning calendar tabs and one-click workflows present the same minimal UI and avoid duplicated buttons after updates.

## 2025-12-07 - Calendar Scheduling: Display Title Cleanup

### Changed
- **Surname Profile Titles**: Removed "Clan Profile" suffix from all 150 surname profile post titles
  - Titles now display as just the clan name (e.g., "Langlands" instead of "Langlands Clan Profile")
- **Weekly Word/Phrase Titles**: Removed "Weekly Word:" and "Weekly Phrase:" prefixes from all entries
  - Words display as just the word (e.g., "braw" instead of "Weekly Word: braw")
  - Phrases display as just the phrase (e.g., "Haud yer wheesht" instead of "Weekly Phrase: Haud yer wheesht")
- **Column Headers**: Simplified header labels
  - "Product Profile" → "Product"
  - "Surname Profile" → "Surname"

### Technical Details
- Updated `utils/calendar_schedule_builder.py` to JOIN with post table for profile types to load titles
- Fixed ambiguous column reference in SQL queries by qualifying `profile_type` with table alias
- Added `post_title` field to display API response for profile types
- Rebuilt all JSON schedules for 2025-2027 with cleaned titles

## 2025-12-07 - Calendar Scheduling: JSON-Backed System with Enhanced Modals

### Added
- **JSON-Backed Calendar Scheduling System**: Complete refactor to use pre-computed JSON files for fast display
  - New JSON schedule files in `data/calendar/schedule/` with directory-per-category layout
  - JSON builder (`utils/calendar_schedule_builder.py`) generates 52-week schedules using cyclic logic
  - JSON loader (`utils/calendar_json_loader.py`) reads schedules with graceful error handling
  - Display API (`blueprints/planning_api_calendar_scheduling_cache.py`) serves range-based week arrays
- **List Management APIs**: Base cyclic list operations (`blueprints/planning_api_calendar_cyclic.py`)
  - `POST /planning/api/calendar/list/reorder` - Reorder items with two-phase update strategy
  - `POST /planning/api/calendar/list/add` - Add new items
  - `POST /planning/api/calendar/list/delete` - Delete items with position shifting
  - `POST /planning/api/calendar/item/update` - Update item content
  - `GET /planning/api/calendar/list/get` - Get current list with metadata
- **Override Management**: Week-specific overrides (`blueprints/planning_api_calendar_overrides.py`)
  - `POST /planning/api/calendar/override/set` - Set week override
  - `POST /planning/api/calendar/override/remove` - Remove override
  - `POST /planning/api/calendar/override/rebuild-year` - Force rebuild
- **Sequence Manager UI**: New template (`templates/planning/calendar/sequence_manager.html`) for managing base lists
- **Enhanced Modals**: Updated scheduling modal with separate fields for words/phrases
  - Translation, Usage 1, Usage 2, and Notes fields for weekly words/phrases
  - ESC key support to close modals
  - Week selector shows date ranges (W49 1 Dec - 7 Dec) instead of position numbers
- **Data Import**: Imported full datasets from CSV files
  - 104 themes with descriptions from `data/themes_w_descriptions.csv`
  - 98 weekly words from `data/scottish_word_of_the_week.csv`
  - 104 weekly phrases from `data/scots_phrase_of_the_week.csv`

### Changed
- **Scheduling Display**: Range-based JSON backend replaces database-heavy queries
  - Navigation controls (<< Year, < Month, Month >, Year >>) for time navigation
  - Range awareness label showing current week range
  - Drag & drop reordering with proper cyclic position calculation
- **Modal Interface**: Enhanced editing experience
  - Separate input fields for translation, usage examples, and notes
  - Week/year selector with dropdown showing date ranges
  - Improved field visibility based on category type
- **Database Operations**: Two-phase update strategy prevents unique constraint violations
  - Items moved to temporary negative positions before final placement
  - Atomic transactions ensure data consistency

### Technical Details
- Created `config/calendar_settings.py` for centralized configuration
- Implemented cyclic formula: `position = ((week - cycle_start_week) % list_length) + 1`
- JSON files include descriptions for themes, words, and phrases
- Comprehensive documentation in `docs/CALENDAR_SCHEDULING_*.md` files
- Test suite with fixtures and validation tests

### Files Modified
- `templates/planning/calendar/scheduling.html` - Enhanced modal and drag & drop
- `blueprints/planning_api_calendar_scheduling_cache.py` - JSON-backed display API
- `blueprints/planning_api_calendar_cyclic.py` - List management with two-phase updates
- `utils/calendar_schedule_builder.py` - JSON generation with descriptions
- `utils/calendar_json_loader.py` - Robust JSON loading with format detection

## 2025-01-XX - Navbar UI Refactoring & Post Type Header

### Changed
- **Navbar UI Improvements**:
  - Moved post type indicator from page title to navbar header with deep blue background
  - Updated Process/Data toggle colors to red tones (mid-red active, deep red/brown inactive) for better visual distinction from stage buttons
  - Improved Preview button styling for clearer button appearance
  - Removed separator from profile post title (post type now displayed in navbar header)
- **Content Category Banners**: Removed "Content Category" banners from Planning and Authoring stage templates
- **Profile Section Drafting**: Updated to use technical section names and extracted data chunks for better context

### Added
- **Profile Section Drafting Prompt**: New script `scripts/add_profile_section_drafting_prompt.py` for generating marketing text from raw data chunks
- **Post Type Header**: Small header at top of navbar showing "Post type: PROFILE" (or other types) with deep blue background

### Technical Details
- Modified `templates/shared/blog_pipeline_header.html` to restructure navbar with post type header
- Updated `static/css/shared/blog-pipeline-header.css` with new toggle colors and header styling
- Removed post type badge JavaScript function (now rendered server-side)
- Updated profile section drafting API to include technical section names and data chunks in prompts

## 2025-11-20 - Profile Post Theme Matching System Implementation

### Added
- **Vector Embeddings for Profile Matching**: Complete implementation of semantic matching system for profile posts
  - `utils/vector_search/post_extractor.py` - Extracts post content for embedding
  - `utils/profile_matching/post_matcher.py` - Finds similar products, suppliers, and categories
  - `utils/profile_matching/normalization.py` - Weighted random selection algorithm
  - `blueprints/header/api_seo_meta.py` - API endpoints for embedding generation and overrides
  - `templates/header/includes/vector_embeddings_panel.html` - UI panel for visualization
  - `static/js/header/vector-embeddings-panel.js` - Frontend functionality
  - `migrations/add_post_embeddings.sql` - Database schema updates

### Changed
- **Producer Embeddings**: Extended vector search to include producers/suppliers
  - Added `chunk_producer()` method to `ContentChunker`
  - Updated `scripts/generate_embeddings.py` to support `--producers` argument
  - 3 producers embedded and added to FAISS index (2,115 total vectors)

### Features
- **Post Content Extraction**: Extracts and combines content from `post_development` for embedding
- **Multi-Type Similarity Search**: Searches products, categories, and suppliers simultaneously
- **Intelligent Selection**: Weighted random selection algorithm with normalization
- **Manual Override**: Users can override automatic selection and save preferences
- **SEO Meta Integration**: Full UI integration on SEO Meta page

### Documentation
- `docs/PROFILE_POST_THEME_MATCHING_IMPLEMENTATION.md` - Complete implementation documentation
- Updated `docs/PROFILE_POST_THEME_MATCHING_ANALYSIS.md` to reflect implementation status

### Testing
- All core functionality tested and verified
- API endpoints working correctly
- Frontend UI functional
- Database operations confirmed

## 2025-01-XX - Post Type Isolation Audit & Implementation Plan

### Added
- **Post Type Audit**: Comprehensive audit of post type architecture (themes, profiles, recipes)
  - `docs/POST_TYPE_ISOLATION_AUDIT.md` - Complete analysis of isolation between post types
  - `docs/POST_TYPE_FIXES_IMPLEMENTATION_PLAN.md` - Detailed implementation plan for fixes
  - `docs/POST_TYPE_FIXES_SUMMARY.md` - Executive summary of fixes needed
- **Findings**: Identified three areas requiring attention:
  1. Missing `post_type` variables in routes (mostly resolved)
  2. Workflow substages visibility (needs naming convention and visual indicators)
  3. `illustration_method` deprecation (needs migration to `post_type`-based system)

### Documentation
- Audit confirms architecture is mostly robust with good isolation between types
- Implementation plan ready for 2-3 week execution
- Profile development can proceed safely with identified precautions

## 2025-01-XX - Publishing System: Removed Caching & Fixed Section Heading Quotes

### Changed
- **HTML Generation**: Removed all caching mechanisms - HTML is now always generated fresh
  - `clan_publisher.py` no longer loads from cache files
  - `preview_handler.py` no longer writes cache files
  - Template reloads on each render instead of being cached
- **Section Headings**: Added quote removal filter to all templates
  - Template filter: `{{ section.section_heading|replace('"', '')|replace("'", '')|trim }}`
  - Removes inverted commas from section headings on preview and published posts
  - Applied to: `clan_post_raw.html`, `post_preview.html`, `header/preview.html`, `clan_post.html`

### Fixed
- **Quote Display**: Section headings no longer display with quotes on live site
- **Cache Staleness**: Template updates now take effect immediately without server restart
- **HTML Consistency**: Preview and published HTML are now identical (except image URLs)

### Updated Files
- `blog-launchpad/clan_publisher.py` - Removed cache loading, always generates fresh HTML
- `blog-launchpad/publish/preview_handler.py` - Removed cache writing
- `blog-launchpad/publish/post_renderer.py` - Template reloads each time
- `templates/launchpad/clan_post_raw.html` - Added quote removal filter
- `templates/launchpad/post_preview.html` - Added quote removal filter
- `templates/header/preview.html` - Added quote removal filter
- `blog-launchpad/templates/clan_post.html` - Added quote removal filter

### Documentation
- `docs/temp/PUBLISHING_SYSTEM_UPDATE_2025.md` - New documentation for recent changes

## 2025-01-09 - Snapshot Block Rewritten for Two-Paragraph Chatty Format

### Changed
- **Snapshot Block Compilation**: Completely rewritten to generate two separate chatty paragraphs
  - News paragraph: Chatty overview of news stories with embedded markdown links
  - Events paragraph: Chatty overview of events with embedded markdown links
  - LLM identifies related/overlapping topics and mentions them together naturally
  - Uses conversational, engaging language (3-5 sentences per paragraph)
- **Component Structure**: Reorganized into modular components
  - News Component: Fetches and displays top 5 news items with summaries
  - Events Component: Fetches and displays top 5 event items with summaries
  - Compile Function: Combines both into two LLM-generated paragraphs
- **UI Updates**: Updated editor to show separate components with individual "Generate" buttons
  - Each component has its own output area
  - "Compile Final Selection" button generates the two paragraphs
  - Preview displays two paragraphs separately with NEWS/EVENTS labels

### Fixed
- **LLM Service Method**: Fixed incorrect method call (use `execute_llm_request` instead of `generate`)
- **Event Listener**: Replaced inline onclick with proper event listener for compile button
- **Link Conversion**: Added markdown-to-HTML link conversion in preview route for email compatibility
- **Error Handling**: Removed all fallback text generation - now returns proper errors if LLM fails

### Updated Files
- `blueprints/newsletter.py` - Rewrote compile_snapshot endpoint, added component generation endpoints
- `templates/newsletter/partials/block_editor_snapshot.html` - Modular component UI with event listeners
- `templates/newsletter/partials/snapshot.html` - Two-paragraph preview display
- `docs/newsletter/blocks/snapshot.md` - Updated documentation

## 2025-11-19 - New Products Spotlight Enhanced with LLM Intro & Product Tracking

### Added
- **LLM-Generated Intro Paragraph**: New Products Spotlight now includes a brief intro paragraph
  - Generated by LLM reviewing the three selected products
  - Mentions products are recently added to website
  - Brief commentary on products based on descriptions
  - 2-3 sentences, ~50-75 words
- **Confirm Button**: Added "Confirm Selection & Generate Intro" button in editor
  - Generates intro paragraph via LLM
  - Marks products as launched in database (`newsletter_launched_at` timestamp)
  - Only marks products as launched when user confirms (not on initial selection)
- **Product Pool Management**: Implemented persistent product pool system
  - Stores up to 50 recent products in block payload
  - Enables consistent random selection without running out of options
  - Products selected from pool with category diversity
- **Product Tracking Service**: New service for tracking product launches
  - `mark_products_newsletter_launched()` - Sets `newsletter_launched_at` timestamp
  - `extract_product_ids_from_payload()` - Extracts product IDs from block payload
- **Custom Editor UI**: Replaced JSON editor with custom product selection interface
  - Shows current selection with thumbnails and SKU
  - "Re-choose Products" button for random selection
  - Preview of generated intro paragraph
  - Manual override option (collapsible)

### Changed
- **Title**: Changed from "Products Spotlight" to "New Products Spotlight" in preview
- **Product Selection**: Now selects 3 products (instead of 6) from recent products
  - Uses `first_seen_at` field (from clan.com sync) instead of `created_at`
  - Filters by `id > 10000` to exclude older products
  - Ensures category diversity (different specific categories)
- **Preview Display**:
  - Removed SKU from product display (only shown in editor)
  - Styled "Explore" link as button (smaller than "Read more" button)
  - Added intro paragraph display above products
- **Data Source**: Changed from `product` table to `clan_products` table
  - Uses `first_seen_at` for identifying new products
  - Includes `category_ids` for diversity filtering
  - Full clan.com URLs for product links

### Fixed
- **Clan.com API Date Fields**: Fixed extraction of `created_at` from getProducts API
  - Code was treating API response as list instead of dict
  - Now correctly extracts and parses `created_at` field
  - Created diagnosis document for CLAN.com team regarding missing `updated_at` field

### Updated Files
- `blog-core/newsletter/services/products_intro_service.py` (new)
- `blog-core/newsletter/services/product_tracking.py` (new)
- `blog-core/newsletter/selectors/products.py` (refactored for pool management)
- `blog-core/newsletter/services/block_suggestion_service.py` (updated for pool)
- `blog-core/newsletter/services/block_editor_service.py` (updated confirmation logic)
- `blueprints/newsletter.py` (added intro generation and confirmation endpoints)
- `templates/newsletter/partials/block_editor_new_products.html` (new custom editor)
- `templates/newsletter/partials/new_products.html` (updated title, intro, button styling)
- `blog-launchpad/clan_cache.py` (fixed date field extraction)
- `docs/clan_products/API_DATE_FIELDS_DIAGNOSIS.md` (new)

## 2025-11-19 - Newsletter Preview Redesign with Cream Panels & Dark Brown Text

### Changed
- **Newsletter Preview Styling**: Complete redesign of preview appearance
  - Changed all panel backgrounds from off-white to very light cream (#fef9e7)
  - Updated all text colors from black/gray to very dark brown (#3d2817)
  - Changed borders from light gray to light brown (#e8dcc0)
  - Removed white container background - panels now show individually against dark tiled background
  - All panels have rounded corners (border-radius:8px) for email compatibility
  - Links now use brown color scheme (#6b4e3d) instead of blue
  - Consistent spacing and padding across all panels

### Fixed
- **Tile Background Loading**: Fixed path resolution for base64 tile data
- **Panel Structure**: Each section (header, blocks, footer) now has its own panel with rounded corners

### Updated Files
- All newsletter block partials (intro, snapshot, feature, products, spotlight, category, evergreen, closing)
- Main render template (removed white container, updated colors)
- Header and footer panels (matching cream/brown scheme)

## 2025-11-02 - Newsletter Intro Components Enhanced with LLM & Intelligent Compilation

### Enhanced
- **Events Component**: Now uses LLM to generate conversational comments
  - Fetches full event details including description from database
  - LLM analyzes event content and highlights what's interesting
  - Generates human-like commentary about cultural/historical significance
  - No longer just dry announcements - comments on what makes events notable
- **Theme Component**: Now uses LLM to generate conversational comments
  - Fetches full theme details including description, seasonal context, tags
  - LLM analyzes theme content and highlights relevance
  - Generates human-like commentary about why theme matters
  - No longer just "we're exploring X" - comments on what's interesting
- **Compile Function**: Completely rewritten to use LLM for intelligent compilation
  - LLM considers all three components as information (not sentences to repeat)
  - LLM decides best order (which creates best opening, which should close)
  - Rewrites into single coherent paragraph (2-4 sentences)
  - Weaves information together naturally - doesn't just concatenate
  - Creates welcoming introduction that flows into newsletter content
  - Filters out placeholder/loading messages before processing

### Changed
- **Events Generation**: Replaced simple template with LLM-based generation
  - Old: "Meanwhile, X has announced Y in Z."
  - New: LLM-generated comment about what's interesting about the event
- **Theme Generation**: Replaced simple template with LLM-based generation
  - Old: "This week we're exploring X, Y."
  - New: LLM-generated comment about why the theme matters
- **Compile Logic**: Replaced random shuffle + concatenation with LLM rewriting
  - Old: Randomly shuffled sentences and joined them
  - New: LLM creates coherent paragraph with intelligent ordering

## 2025-11-02 - Newsletter Intro Block Modular UI & LLM Weather Generation

### Added
- **Modular Intro Block Editor**: Reorganized intro block UI into separate component modules
  - Weather Component: Generates conversational weather summary
  - Events Component: Generates event announcement text
  - Theme Component: Generates theme introduction text
  - Each component has its own "Generate" button and output display
  - Compile section combines all three into final paragraph with varied order
- **New API Endpoints**:
  - `GET /newsletter/issue/<id>/block/<id>/generate-weather` - Generate weather component
  - `GET /newsletter/issue/<id>/block/<id>/generate-events` - Generate events component
  - `GET /newsletter/issue/<id>/block/<id>/generate-theme` - Generate theme component
  - `POST /newsletter/issue/<id>/block/<id>/compile-intro` - Compile all components
- **Weather Analysis Service** (`weather_analysis_service.py`):
  - Analyzes weather patterns over 3-week period (1 week before + target week + 1 week after)
  - Compares actual weather to seasonal norms
  - Identifies unusual conditions and trends
  - Uses LLM to generate conversational summaries (no hard-coded templates)

### Changed
- **Weather Summary Generation**: Now uses LLM instead of hard-coded templates
  - Removed all hard-coded phrases and examples
  - LLM analyzes actual weather data vs seasonal norms
  - Generates unique, natural summaries based on actual conditions
  - Prompt emphasizes avoiding clichés and using varied language
- **Intro Block UI**: Complete redesign
  - Old: Single "Regenerate Suggestions" button with suggestions list
  - New: Three separate component modules with individual generate buttons
  - Each module is self-contained with its own JavaScript functions
  - Final compiled paragraph displayed at top
  - Manual override section moved to collapsible details

### Improved
- **Weather Analysis**: 
  - Aggregates weather data over extended period (not just single day)
  - Compares to seasonal norms (winter/spring/summer/autumn averages)
  - Identifies patterns (chilly, mild, rainy, windy, stormy)
  - Detects unusual conditions (unseasonable temps, storms, etc.)
- **Text Generation**:
  - Varies sentence order for natural flow
  - More conversational tone throughout
  - Better integration of weather, events, and theme components

### Files Changed
- `blog-core/newsletter/services/weather_analysis_service.py` - NEW: Weather analysis and LLM generation
- `templates/newsletter/partials/block_editor_intro.html` - Complete rewrite: modular component UI
- `blueprints/newsletter.py` - Added 4 new API endpoints for component generation
- `blog-core/newsletter/selectors/intro.py` - Updated to use new weather analysis service
- `blog-core/newsletter/rendering/intro_text.py` - Updated to handle new component format

## 2025-11-02 - Newsletter Intro Block Fixes & Documentation

### Fixed
- **Regenerate Suggestions**: Fixed "Regenerate Suggestions" button in newsletter intro block
  - Made link validation optional for cached items (skip_validation=True) to improve performance
  - Added fallback logic when validation filters all items
  - Fixed JavaScript selector to find correct element with data-issue-id attribute
  - Improved error handling with content-type checking and better error messages
- **JavaScript Error Handling**: Enhanced error handling in block_editor_intro.html
  - Added element validation before DOM manipulation
  - Improved JSON parsing with content-type checks
  - Added HTML escaping for XSS protection
  - Better error messages displayed to users

### Improved
- **Suggestion Generation**: Optimized suggestion generation to skip link validation for cached items
  - Updated `generate_suggestions()` to accept `skip_validation` parameter
  - Updated all intro/snapshot selectors to use skip_validation=True
  - Added logging for debugging suggestion generation
- **Template Context**: Fixed template include to pass context properly with `with context` directive

### Documentation
- **Block Documentation**: Split block-editors.md into individual files per block type
  - Created detailed `docs/newsletter/blocks/intro.md` with complete file listings, line counts, JavaScript functions, API endpoints, and testing instructions
  - Created documentation files for all block types: snapshot, feature, products, category, evergreen, closing
  - Updated `docs/newsletter/block-editors.md` to be overview/index with links to individual blocks
  - Updated `docs/newsletter.md` to link to individual block documentation

### Files Changed
- `blog-core/newsletter/selectors/intro.py` - Added skip_validation parameter
- `blog-core/newsletter/selectors/snapshot.py` - Added skip_validation parameter
- `blog-core/newsletter/services/block_editor_service.py` - Updated to use skip_validation
- `blog-core/newsletter/services/suggestion_service.py` - Added skip_validation with fallback logic
- `blueprints/newsletter.py` - Improved error handling and logging
- `templates/newsletter/partials/block_editor_base.html` - Fixed template context passing
- `templates/newsletter/partials/block_editor_intro.html` - Fixed JavaScript selectors and error handling
- `docs/newsletter/blocks/*.md` - New detailed block documentation files

## 2025-01-XX - Product Tag Editor Enhancements

### Fixed
- **Title Filter**: Fixed title filter to work on currently displayed products with Enter key support
- **Product Count Display**: Fixed spacing in "products selected" text and count accuracy
- **Page Load**: Fixed automatic product loading on page initialization
- **API Endpoint**: Fixed `/products/tag-editor/api/search` to accept '*' query for fetching all products

### Improved
- Added `applyTitleFilterToCurrentProducts()` function for client-side filtering
- Improved title filter integration with other filters (search, category, tags)
- Increased pagination limit to 10000 products for better coverage
- Enhanced selected product count to reflect actual displayed products

## 2025-11-11 - Knowledge Base Integration

### Added
- **Knowledge Base Database Schema**: Created `clan_kb_categories` and `clan_kb_articles` tables with full-text search indexes and change detection support
- **Knowledge Base Cache Module** (`blog-launchpad/clan_kb_cache.py`): 
  - Fetches categories and articles from CLAN Knowledge Base API
  - Hash-based change detection for articles
  - Image downloading and local caching for feature images
  - On-demand sync functionality
  - Graceful handling of missing parent categories with PostgreSQL savepoints
- **Migration File**: `migrations/create_clan_kb_tables.sql` for creating KB tables
- **Documentation**: 
  - `docs/data_intelligence/knowledge_base/TABLE_STRUCTURE_PROPOSAL.md` (approved schema)
  - `docs/data_intelligence/knowledge_base/IMPLEMENTATION_STATUS.md` (implementation guide)
  - Updated `docs/data_intelligence/knowledge_base/README.md`

### Technical Details
- **Tables**: `clan_kb_categories` (167 categories), `clan_kb_articles` (29 articles stored)
- **Features**: Change tracking via `article_content_hash` and `last_content_change_at`
- **Image Caching**: Downloads feature images to `static/images/kb/` directory
- **Error Handling**: Uses PostgreSQL savepoints for per-category error isolation
- **API Integration**: Connects to `https://clan.com/clan/api/getKnowledgebaseCategories` and `getKnowledgebaseArticles`
- **Rate Limiting**: Handles HTTP 429 responses gracefully (some categories may need retry)

### Next Steps
- Integrate KB articles into vector search index
- Add KB search to content generator modal
- Use KB context in content generation prompts

## 2025-11-11 - Product Data Enhancement & Vector Search Update

### Product Data Fields
- **Additional Data**: Added `additional_data` (JSONB) field to `clan_products` table
  - Stores structured product attributes (material, pattern, shirt style, clan crest info, etc.)
  - Format: `{key: {label, value, code}}` structure from CLAN API
- **Dimensions**: Added `dimensions` (TEXT) field to `clan_products` table
  - Stores product dimensions when available from CLAN API
- **Database Migration**: Added columns with `ADD COLUMN IF NOT EXISTS` for safe upgrades
- **Storage**: Updated `store_single_product()` and `store_products()` to save new fields
- **Extraction**: Updated `ClanDataExtractor` to include new fields in extracted data

### UI Enhancements
- **Product Data Review Page**: Enhanced display of product information
  - Specifications section moved into Product Description panel (styled consistently)
  - Additional Information section added (displays additional_data with labels/values)
  - Dimensions displayed when available
  - All sections styled consistently (blurb, bullets, main description, specifications, additional data)
- **Styling**: Added CSS for new description sections (purple for specifications, teal for additional data)

### Vector Search System Enhancement
- **Chunking Updates**: Enhanced `ContentChunker` to include all product data fields
  - **Products now include**:
    - Product name and producer
    - Short description (blurb)
    - Full description (including bullet points)
    - **Specifications** (when available)
    - **Product Details** (additional_data: material, pattern, shirt style, clan crest info, etc.)
    - **Dimensions** (when available)
    - **Available Options** (configurable_options: sizes, colors, etc.)
    - Supplier information
  - **Categories now include**:
    - Category name and description
    - **Enhanced heritage data** (all 5 dimensions with new dictionary format):
      - Historical Origins (narrative, key themes, significant elements)
      - Cultural Significance (narrative, key themes, significant elements)
      - Evolution (narrative, key themes, significant elements)
      - Scottish Heritage Connections (narrative, key themes, significant elements)
      - Industrial Legacy (narrative, key themes, significant elements)
    - Handles both legacy string format and new dictionary format
- **Index Rebuild**: Regenerated all chunks and rebuilt FAISS vector index
  - 1,157 product chunks updated
  - 259 category chunks updated
  - Total: 1,416 vectors in index
  - All new fields now searchable via semantic search

### Technical Details
- **Transformer Updates**: `transform_product_for_ui()` now extracts `additional_data` and `dimensions` from API
- **Chunking Query**: Updated `process_all_products()` to fetch new fields from database
- **Heritage Data**: Updated `chunk_category()` to extract narratives, themes, and elements from new dictionary format

## 2025-11-XX - Newsletter Event Management

### Event Classification & Management
- **Event Recurrence Classification**: Added LLM-based classification system to identify annual vs one-off events
  - Enhanced prompt to emphasize festivals are annual events
  - Added heuristic pre-check: any event with "festival" in title = annual
  - Added known annual event keywords (hogmanay, celtic connections, royal highland show, etc.)
  - Classification filter added to Events Synopsis page with visual badges
  - Manual override capability on event detail page

### Event Editing & Deletion
- **Inline Editing**: Added direct editing capabilities on event detail page
  - Title: Click-to-edit with full-width input
  - Description: Textarea editing with Save/Cancel
  - Date Text: Raw date text field editing
  - Event Date: Inline date picker
  - Location: Inline text input
  - All edits save to both database columns and raw_data JSON
- **Delete Functionality**: Added delete button with confirmation dialog
  - Checks for soft delete column first, falls back to hard delete
  - Redirects to events list after successful deletion
- **API Endpoints**: 
  - `POST /newsletter/events/<id>/update` - Update any event field
  - `DELETE /newsletter/events/<id>` - Delete event (soft or hard delete)
  - `POST /newsletter/events/<id>/recurrence-type` - Update classification manually

### Database Schema
- **Event Recurrence Type**: Added `event_recurrence_type` column to `newsletter_source_item` table
  - Values: `'annual'`, `'one_off'`, or `NULL` (unclassified)
  - Indexed for efficient filtering
  - Migration: `migrations/add_event_recurrence_type.sql`

### Classification Service
- Created `event_classification_service.py` with LLM-based classification
- Includes heuristic fallback for known annual events
- Batch classification script: `classify_all_events.py`

### Technical Improvements
- Fixed missing `db_manager` imports in event update/delete routes
- Improved event detail service to include recurrence type in queries
- Enhanced event filtering to catch false positives (newsletter signups, accommodation listings, recurring patterns)

## 2025-11-01 (continued - evening)

- Section Titling: Fixed bug where only first section received title/description - now generates for all sections
- Section Titling: Enhanced LLM prompt to explicitly list all sections with themes and topics
- Section Titling: Added validation to ensure LLM generates exactly the correct number of section titles
- Section Titling: Fixed section matching logic bug that was overwriting outer loop variable
- Section Titling: Added direct writes to post_section table in addition to post_development.sections
- Idea Expansion: Enhanced Important Notes highlighting in prompt with mandatory requirements and explicit instructions
- Idea Expansion: Improved theme data fetching to handle cases where theme selected for week before post creation

## 2025-11-01 (continued)

- Page Headers: Replaced post ID display with date span, week number, and selected theme across all blog pipeline pages
- Page Headers: Added fallback logic to fetch theme from week schedule when post schedule doesn't include theme
- Page Headers: Removed stage prefix (Planning/Calendar) from header - now shows only week info and theme
- API: Updated planning_api_posts to include selected_theme_title in schedule responses
- UI: Added CSS styling for new header elements (prefix, week info, separator, theme)

## 2025-11-01

- Week View Navigation: Added localStorage persistence for calendar week view (remembers selected week/year across sessions).
- Week View Navigation: Added "This week" button to quickly jump to the current week.
- Week View Navigation: Replaced week number input with month/week picker interface showing all weeks organized by month with date ranges.
- Theme Selection: Fixed theme selection persistence on ideas week page - themes now save to calendar_schedule when selected.
- Theme Display: Fixed calendar week view to correctly show selected themes using idea_id from calendar_schedule.
- Idea Modal: Added delete button to unified idea/theme/event modal (only visible when editing existing items).
- API: Added DELETE endpoint for calendar events.
- API: Updated calendar_schedule endpoint to include idea_id in responses.

## 2025-10-31

- Week View: Added filters (Blog Themes, Events, Syndication) and integrated Facebook Product syndication schedule rendering per weekday with time.
- Week View: Introduced a single week-wide Blog Themes row above the grid with left-aligned titles.
- Week View: Added calendar day numbers to the right of each day header (Mon–Sun).
- Scheduling: Added backfill and purge endpoints to normalize and hard-delete legacy/inactive schedule rows; `get_schedules` now filters `is_active = true`.


