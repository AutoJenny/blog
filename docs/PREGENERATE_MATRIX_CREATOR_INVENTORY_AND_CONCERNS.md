# Pre-Generate Matrix: Creator Inventory and Concerns

**Date:** 2026-01-29  
**Purpose:** Reply to briefing “Next phase: automated pre-generation of the Matrix (8–12 weeks ahead)” — definitive creator list and candid concerns before formalising the orchestration layer.

---

## 1. List of existing creator scripts

Scripts that **create or update posting_queue rows** (insert/update), with slot, automation, and skip/regenerate behaviour.

| # | Filename | Slot (Day) | Source / content type | Automated? | Skip if exists? | Regenerate if failed/empty? |
|---|----------|------------|------------------------|-----------|------------------|-----------------------------|
| 1 | `scripts/automated_culture_creator.py` | **Monday** | culture_library → culture_fact | **No** | Yes: skip if **non-failed** culture_fact exists for that date | **No** — if only a failed row exists, it **creates a new row** (duplicate possible) |
| 2 | `scripts/automated_weekly_content_creator.py` | **Tuesday** | calendar_ideas (word/phrase/insult rotating) → weekly_word / weekly_phrase / weekly_insult | **Yes** (background_posting_monitor.sh) | Yes: skip if **any** CULTURE language post exists for that Tuesday (any status) | **No** — if a failed post exists, it **skips**; slot stays failed |
| 3 | `scripts/automated_message_post_creator.py` | **Wednesday** | data/facebook_messages.csv → message | **Yes** (background_posting_monitor.sh) | Yes: skip if **any** message post exists for that date with status **!= 'failed'** | **No** — if only failed exists, it **creates a new row** (duplicate possible) |
| 4 | `scripts/automated_heritage_creator.py` | **Thursday** | heritage_library → heritage_fact | **No** | Yes: skip if **non-failed** HERITAGE post exists for that date | **No** — if only failed exists, it **creates a new row** (duplicate possible) |
| 5 | `scripts/automated_authority_short_creator.py` | **Friday** | KB rota / kb_topic_content / clan_kb_articles → authority_short | **No** | Skip only if row exists with status in (generated, ready, approved, scheduled) **and** content not placeholder | **Yes** — reuses same row: create skeleton then generate, or regenerate in place for draft/failed/placeholder |
| 6 | `scripts/automated_product_post_creator.py` | **Saturday** | daily_posts_schedule + clan_products → product | **Yes** (background_posting_monitor.sh) | Yes: skip if **any** product post exists for that date/time with status **not in (published, failed)** | **No** — if slot has failed only, it **creates a new row** for same slot (duplicate possible) |
| 7 | **No script** — Content Roles API only | **Sunday** | KB rota + DepthLongGenerator → depth_long | **No** (API only) | N/A | N/A |

### 1.1 Other code paths that insert into posting_queue (not Matrix pre-generation)

- **blueprints/content_roles_api.py** — INSERT for **depth_long** only when `/facebook/sunday/generate` (POST) is called; then optional schedule endpoint. No batch script; no “next N weeks” loop.
- **blueprints/launchpad/** (blog_post_syndication, launchpad_content, instagram_carousel), **utils/posting_queue_helpers.py**, **blueprints/content_roles_api.py** — other flows (launchpad, manual, tests). Not part of the Matrix pre-generation pass.

### 1.2 Automation (who runs what)

- **background_posting_monitor.sh** (runs in a loop, not cron):  
  - `automated_weekly_content_creator.py`  
  - `automated_weekly_content_workflow.py`  
  - `automated_message_post_creator.py`  
  - `automated_product_post_creator.py`  
  - `automated_product_post_workflow.py`  
  - `automated_posting.py`  
  - `scheduled_posting_executor.py`  
  - (Monday) `kb_topic_discovery_runner.py`  
- **Not run by monitor:** culture_creator, heritage_creator, authority_short_creator. No cron/launchd found in repo for those three.

### 1.3 Horizon / look-ahead (current defaults)

| Script | Parameter | Default |
|--------|-----------|---------|
| automated_culture_creator | --weeks-ahead | 12 |
| automated_heritage_creator | --weeks-ahead | 12 |
| automated_authority_short_creator | --days-ahead | 28 |
| automated_message_post_creator | days_ahead (create_message_posts) | 28 |
| automated_product_post_creator | days_ahead (create_product_posts) | 28 (main()), 7 (class default) |
| automated_weekly_content_creator | weeks_ahead | 52 |

---

## 2. Concerns and risks

### 2.1 Sunday DEPTH_LONG — no batch creator

- **Current state:** Sunday depth_long is created only via **Content Roles API** (`/facebook/sunday/generate` + store). A human or other caller must supply topic_id, source_page_id, rota_year, rota_week (and optional angle_id). There is **no script** that iterates the next N weeks and creates/regenerates Sunday posts.
- **Risk:** An orchestration script that “fills all Matrix slots” cannot fill Sunday without either (a) a new **automated_depth_long_creator.py** (or similar) that uses rota + generator in a loop, or (b) the orchestrator calling the existing API per week (needs topic/rota resolution and error handling). Without one of these, Sunday will remain a gap in any “single pre-generation pass”.

### 2.2 “Regenerate if failed” is inconsistent

- **Authority_short:** Only one that **regenerates in place** (reuses queue id, UPDATEs same row for draft/failed/placeholder).
- **Culture, heritage, message, product:** When the only existing row for the slot is **failed**, they **create a new row** (or, for Tuesday, skip and leave the slot failed). None of them UPDATE the failed row.
- **Risk:** Duplicate rows per slot (e.g. one failed, one ready) unless the orchestration layer or creators are changed to “reuse/update failed row” or “cancel failed row then create.” Duplicates could confuse the schedule API or executor if not constrained (e.g. unique constraint or “pick latest non-failed per slot”).

### 2.3 Tuesday: failed slot never retried

- **Weekly content creator:** Skips if **any** CULTURE language post exists for that Tuesday (no status filter). So if the only row is **failed**, it skips and never creates a replacement.
- **Risk:** A failed Tuesday slot stays failed until manual intervention (delete/cancel the failed row or add “regenerate if failed” logic).

### 2.4 Source dependencies that can cause repeated failure

- **Friday (authority_short):** Depends on **kb_topic_rota** for the ISO week, then **kb_topic_content** or **kb_topics.article_ids** → **clan_kb_articles**. If rota is empty for a week or KB content is missing, generation returns “No suitable source text” and the row stays failed. Documented in `docs/REPORT_FRIDAY_AUTHORITY_SHORT_GENERIC_CONTENT.md`.
- **Sunday (depth_long):** Same KB/rota dependency; plus today there is no automated loop, so “frequent failure” is less visible but would apply once a batch creator exists.
- **Tuesday:** Depends on **calendar_ideas** (weekly_word/phrase/insult) and 90-day exclusion from posting_queue. If the pool is exhausted or all ideas are excluded, “No eligible idea” and the slot is skipped (error count incremented).
- **Wednesday:** Depends on **data/facebook_messages.csv**. If the file is missing or empty, no posts created. Simple and stable if the file is maintained.
- **Saturday:** Depends on **daily_posts_schedule** (active product schedule) and **clan_products** (products not posted recently). If no schedule or no products, no posts.

### 2.5 Idempotency and duplicates

- **Culture, heritage:** No unique constraint on (platform, content_type, scheduled_date). So “create when non-failed doesn’t exist” can create a second row when one failed row exists. Safe to re-run only if “exists” is defined as “any row for that slot” and we either update the failed row or cancel it before creating.
- **Message:** No unique constraint on (platform, content_type, scheduled_date). Same duplicate risk when the only existing row is failed.
- **Product:** check_existing_post uses (scheduled_date, scheduled_time); if the only row is failed, it’s not “existing,” so a second row can be created for the same slot.
- **Tuesday:** Unique index exists for Facebook language posts (Phase C2); duplicate insert would fail at DB level. So idempotent for “create” but “skip if any exists” means failed slots are never retried.
- **Authority_short:** No duplicate for same date (single row per Friday, reused and updated). Idempotent for “create + generate” with --force.

### 2.6 What might reasonably stay manual (for now)

- **Sunday depth_long:** Editorial choice of topic/angle per week may be intentional. Automating “pick from rota and generate” is feasible, but if product owner wants a human to confirm topic before generation, that could stay manual until the process is standardised.
- **Approval gates:** Some roles store status as `generated` (e.g. depth_long) and may have a separate approval step before “ready.” The brief said “no editorial refinement” — so treating “generated” as “slot filled” for coverage reporting may be enough; any approval workflow stays as-is.

### 2.7 Order of execution and pre-flight checks

- **Order:** Running creators in a fixed order (e.g. Mon → Tue → … → Sun) is fine. Dependencies are per-slot (rota, libraries, CSV, schedule table), not between slots.
- **Pre-flight:** A single orchestration script could check before running:  
  - culture_library / heritage_library have rows;  
  - data/facebook_messages.csv exists and non-empty;  
  - kb_topic_rota has rows for the target weeks (for authority_short and, if added, depth_long);  
  - daily_posts_schedule has an active product schedule;  
  - clan_products has candidates;  
  - calendar_ideas has eligible ideas for Tuesday.  
  Missing data would cause generation failures; surfacing this in a report (or non-zero exit) would make “gaps visible immediately.”

---

## 3. Summary

- **Creator inventory:** Six scripts cover Mon–Sat; Sunday has no batch creator (API only). Three of the six (Tuesday, Wednesday, Saturday) are run by background_posting_monitor.sh; culture, heritage, and authority_short are not.
- **Skip/regenerate:** Only authority_short “regenerates in place.” The others either skip (Tuesday: even when failed) or create a new row when the only existing one is failed (culture, heritage, message, product), which can create duplicates.
- **Risks:** Sunday gap without a new batch path or API loop; duplicate rows unless we define “slot filled” and/or add update/cancel logic for failed rows; Tuesday failed slots never retried; Friday (and Sunday if automated) depend on KB/rota being populated.
- **Recommendation:** Before locking the orchestration design, decide (a) whether Sunday should get an automated_depth_long_creator (or API-loop) and (b) whether “regenerate if failed” means “update same row” or “cancel failed then create one” to avoid duplicates and align with a single “slot = one row” model.

Once the Phase brief is issued with acceptance criteria (including “no duplicate rows per slot” and “failed slots retried or reported”), implementation can align creators and the single pre-generation pass accordingly.
