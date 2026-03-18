# Report: Friday Still Shows “AUTHORITY SHORT / Authority post / Draft”

**Date:** 2026-01-29  
**Scope:** Diagnosis only — no code changes. Why the week-view Friday slot shows generic labels instead of actual AUTHORITY_SHORT content.

---

## 1. What the user sees

- **Friday slot:** “AUTHORITY SHORT”, “Authority post”, “Draft”.
- **Expected:** A real title (first line of generated text) and a non-draft status when content exists.

---

## 2. What is implemented

### 2.1 Creator (`scripts/automated_authority_short_creator.py`)

- **Role:** Ensures one AUTHORITY_SHORT post per Friday (Facebook, feed_post, content_type `authority_short`).
- **Flow:**
  1. For each upcoming Friday (or `--week`), if no row exists: insert a **skeleton** row with `generated_content = ''`, `status = 'draft'`.
  2. If a row exists with `content_type = 'authority_short'`:  
     - Only **skip regeneration** when: `status` in (`generated`, `ready`, `approved`, `scheduled`) **and** content is **not** placeholder (`AUTHORITY_SHORT placeholder`).  
     - So for a skeleton (empty content, `draft`) or failed row, the script **does** call the generator (unless `--dry-run`).
  3. **Step 2:** Call `AuthorityShortGenerator.generate_for_friday(target_date, queue_id)`.
  4. On **success:** UPDATE `generated_content`, set `status = 'ready'`, persist topic/source/validation.
  5. On **failure:** UPDATE `status = 'failed'`, persist `validation_report_json` (attempts, failed_rules, source_used); **no** update to `generated_content`, so it stays empty or unchanged.

### 2.2 Generator (`utils/content_roles/authority_short_generator.py`)

- **Source order:**  
  1. Rota topic for the ISO week of the Friday → `kb_topic_rota` (year/week) → `kb_topic_content` (aggregated_text) or `kb_topics.article_ids` → `clan_kb_articles`.  
  2. Fallback: first active `clan_kb_articles` row.
- **If no source text:** Returns `success: False`, `error: "No suitable source text found for AUTHORITY_SHORT"`; creator then sets `status = 'failed'`.
- **LLM:** Ollama `llama3.2:latest`, 3 attempts, mechanical validation (length, paragraphs, CTA deny-list, emoji/hashtag strip). On repeated validation failure, returns `success: False` with `validation_report_json` (attempts, failed_rules, source_used).

### 2.3 Schedule API (`blueprints/planning_api_calendar_schedule.py`)

- Role-based query returns all non-product/message/weekly_* posts for the week, including `authority_short`, with `generated_content`, `status`, etc.
- **Title derivation (lines 408–414):**  
  - `content = post['generated_content'] or post['generated_caption'] or ''`  
  - `first_line` = first line of content (trimmed, up to 50 chars).  
  - If `first_line` is empty → `title = f"{post['role']} Post"` (e.g. `"AUTHORITY_SHORT Post"`).  
  - If `first_line` contains “placeholder” or “short factual context” → `title = f"{post['role']} post"`.  
  - Otherwise → `title = first_line`.

### 2.4 Week-view front-end (`static/js/planning/calendar-week-view.js`)

- For role-based types (including `authority_short`): if `title` is generic (e.g. “AUTHORITY SHORT post”) or matches placeholder pattern, it tries `generated_content` first line as title.
- If there is no usable first line (empty or placeholder) → for `authority_short` it shows **“Authority post”**.
- **Post status** is mapped from `post_status` (e.g. `draft` from `status = 'draft'` or `'generated'`).

So: **“AUTHORITY SHORT” / “Authority post” / “Draft”** are the correct UI outcome when the underlying row has **empty or placeholder `generated_content`** and **status `draft` (or failed)**.

---

## 3. Why Friday shows generic content

The week-view is behaving as designed: it shows a generic label when there is no real content to show.

So the underlying issue is that **the posting_queue row for that Friday has no real generated content and is still in draft (or failed)**. That can only happen if:

1. **Generation was never run** for that Friday (skeleton created but creator not run again, or creator not run for that week at all), or  
2. **Generation was run but failed** (no source text, LLM error, or validation failure after 3 attempts), so the row stays with empty/unchanged `generated_content` and gets `status = 'failed'` or remains `draft` depending on code path.

### 3.1 Automation

- **No cron/launchd/shell** in the repo runs `automated_authority_short_creator.py`. It must be run manually or by some external scheduler.
- If that script is not run (or not run for the week the user is viewing), Friday will stay as a skeleton: empty content, draft.

### 3.2 Generation failure paths

- **No source text:**  
  - `kb_topic_rota` has no row for that ISO week, or  
  - `kb_topic_content` has no aggregated text for the rota topic, and  
  - `kb_topics.article_ids` / `clan_kb_articles` path also yields no text, and  
  - Fallback “first active article” is missing or empty.  
  → Generator returns “No suitable source text”; creator sets `status = 'failed'`, leaves `generated_content` empty.

- **LLM or validation failure:**  
  - Ollama down, model error, or content repeatedly fails mechanical/validator rules.  
  → After 3 attempts, generator returns `success: False`; creator sets `status = 'failed'` and keeps existing (e.g. empty) `generated_content`.

### 3.3 Placeholder check in creator

- Creator only treats content as “placeholder” if it **starts with** `"AUTHORITY_SHORT placeholder"`.  
- Skeleton is inserted with `generated_content = ''`. So empty content is **not** treated as placeholder; the creator will still attempt generation when it finds that row (unless dry-run). So the “generic” display is not due to the creator incorrectly skipping generation for empty content.

---

## 4. Summary: root cause and remaining known issues

| Item | Conclusion |
|------|------------|
| **Why UI shows “AUTHORITY SHORT / Authority post / Draft”** | The Friday row in `posting_queue` has empty or placeholder `generated_content` and status `draft` or `failed`. API and week-view correctly show a generic title and “Draft” in that case. |
| **Why content might be missing** | (1) Authority-short creator not run for that week (no automation found). (2) Generation failed: no source text for that week’s rota/KB, or LLM/validation failure. |
| **Implemented and working** | Creator (skeleton + call generator); generator (rota → KB → fallback, LLM, validation); schedule API (role-based query, title from content); week-view (generic vs real title, status). |
| **Remaining known issues** | No automated run of `automated_authority_short_creator.py`; dependency on `kb_topic_rota` / `kb_topic_content` / `clan_kb_articles` for the target week — if rota or KB is empty, generation fails with “No suitable source text”. |

---

## 5. Recommended next steps (no code in this report)

1. **Inspect the specific Friday row**  
   - For the week the user is viewing: `SELECT id, status, generated_content, validation_report_json, scheduled_date FROM posting_queue WHERE role = 'AUTHORITY_SHORT' AND content_type = 'authority_short' AND scheduled_date = '<that_friday>';`  
   - If `status = 'failed'`, read `validation_report_json` for `attempts`, `failed_rules`, `source_used` to see whether the failure was “no source” or validation/LLM.

2. **Verify source data for that week**  
   - Rota: `SELECT * FROM kb_topic_rota WHERE scheduled_year = <year> AND scheduled_week = <week>;`  
   - If present, check `kb_topic_content` for that `topic_id` and `clan_kb_articles` for active articles.

3. **Run the creator for that week**  
   - e.g. `python3 scripts/automated_authority_short_creator.py --week 2026-W5` (or the relevant ISO week).  
   - With `--force` if the row already exists but is draft/failed, to force regeneration.  
   - Check logs and DB: if it still fails, use step 1 and 2 to see whether the blocker is missing rota/KB or LLM/validation.

4. **Automation (optional)**  
   - If Friday content should always be generated in advance, add a scheduled run of `automated_authority_short_creator.py` (e.g. weekly) with sufficient `--days-ahead` or `--week` coverage.

---

## 6. References

- **Creator:** `scripts/automated_authority_short_creator.py`  
- **Generator:** `utils/content_roles/authority_short_generator.py`  
- **Schedule API:** `blueprints/planning_api_calendar_schedule.py` (role-based query and title logic, lines 376–446)  
- **Week-view:** `static/js/planning/calendar-week-view.js` (title fallback for authority_short, lines 226–247)  
- **Phase X report:** `docs/PHASE_X_AUTHORITY_SHORT_V1_REPORT_BACK.md`  
- **KB rota:** `docs/KB_TOPIC_ROTA_SYSTEM.md`
