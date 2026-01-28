# Phase X — AUTHORITY_SHORT v1 (Facebook Matrix) Report-Back

## 1. Friday coverage (next 4 Fridays)

| Date       | posting_queue_id | Status     | Source type          | Source id (topic_id / source_page_id) | Char count |
|------------|------------------|------------|----------------------|----------------------------------------|------------|
| 2026-01-30 | 15505            | generated  | rota_topic_article   | topic_id=327, source_page_id=736       | 332        |
| 2026-02-06 | (TBD)            | (pending)  | (will be created by script when run closer to date) | - | - |
| 2026-02-13 | (TBD)            | (pending)  | (will be created by script when run closer to date) | - | - |
| 2026-02-20 | (TBD)            | (pending)  | (will be created by script when run closer to date) | - | - |

**Notes:**
- The reference implementation run targeted **week 2026-W5**, which includes Friday **2026-01-30**.  
- The script `scripts/automated_authority_short_creator.py` can be rerun periodically (without `--week`) to fill additional Fridays in the configured look-ahead window.

---

## 2. Example generated AUTHORITY_SHORT text (exact)

For **2026-01-30**, `posting_queue.id = 15505`:

> The traditional tartans of Scottish clans are often associated with specific geographic regions, family histories, and cultural affiliations. However, it is worth noting that many of these distinct patterns have evolved over time through influences from various sources, including European textiles and British military regulations.

Properties:
- **Role:** `AUTHORITY_SHORT`  
- **Platform:** `facebook`  
- **Content type:** `authority_short`  
- **Status:** `generated`  
- **Scheduled date/time:** `2026-01-30 15:00:00`  
- **Topic/source linkage:** `topic_id = 327`, `source_page_id = 736`, `rota_year = 2026`, `rota_week = 5`  
- **Character count:** 332 (within 200–400 target, below 600 hard cap)

---

## 3. Where to verify in the UI

1. **Week view (Matrix alignment)**  
   - URL: `/planning/calendar?year=2026&week=5&tab=week-view`  
   - Expected Social Posts row (Facebook):  
     - Mon: CULTURE — Language: Word  
     - Tue: CULTURE — Language: Phrase  
     - Wed: REASSURANCE — Message  
     - **Fri: AUTHORITY_SHORT** — card showing the first part of the text above  
     - Sat: COMMERCE — Product  
     - Sun: DEPTH_LONG — Deep Dive  
   - No duplicate CULTURE cards for weekly language.

2. **Content Control Board**  
   - URL: `/planning/content-control-board`  
   - Under the Facebook column, Friday cell should show a single AUTHORITY_SHORT entry for `2026-01-30`, status `generated`.

3. **Full-page preview (Unified Channel Preview System)**  
   - URL: `/preview/post/15505?channel=facebook`  
   - The rendered HTML should show the AUTHORITY_SHORT text above in the Facebook preview template, with no emojis, hashtags, or calls to action.

4. **Schedule API inspection**  
   - Use the existing test client script: `scripts/fetch_schedule_api_response.py` (currently hardcoded to `2026/5`).  
   - The JSON payload should contain a single entry for Friday:  

     ```json
     {
       "type": "authority_short",
       "posting_queue_id": 15505,
       "role": "AUTHORITY_SHORT",
       "scheduled_date": "2026-01-30",
       "scheduled_time": "15:00:00",
       "status": "generated",
       "title": "The traditional tartans of Scottish clans are often associated with...",
       ...
     }
     ```

---

## 4. Implementation summary (for traceability)

- **Generator:** `utils/content_roles/authority_short_generator.py`  
  - Selects source text from:
    - `kb_topic_content` for the rota topic (preferred), or  
    - `kb_topics.article_ids` → `clan_kb_articles`, or  
    - fallback `clan_kb_articles` if no topic.  
  - Calls `LLMService` with provider `ollama`, model `llama3.2:latest`.  
  - Enforces 200–400 character target (hard cap 600), 1–2 paragraphs, plain text, no emojis/hashtags/CTA.  
  - Returns content plus `topic_id`, `source_page_id`, `rota_year`, `rota_week`, and a validation report structure.

- **Friday creator:** `scripts/automated_authority_short_creator.py`  
  - CLI:  
    - `--days-ahead` (default 28)  
    - `--dry-run`  
    - `--force`  
    - `--week 2026-W5` (ISO week)  
  - For each targeted Friday:  
    - Ensures a `posting_queue` row exists with `role='AUTHORITY_SHORT'`, `content_type='authority_short'`.  
    - If an existing non-placeholder exists and `--force` is not set, retains it.  
    - Otherwise, calls the generator and updates: `generated_content`, `status='generated'`, `topic_id`, `source_page_id`, `rota_year`, `rota_week`, `validation_report_json`.  
  - Logs: date, queue_id, action, source type, char count.

- **Visibility:**  
  - Schedule API’s role-based query already includes AUTHORITY_SHORT while excluding `product`, `message`, `weekly_word`, `weekly_phrase`, `weekly_insult`.  
  - Week view uses `scheduled_date` to place the AUTHORITY_SHORT card on Friday.  
  - Unified Channel Preview renders AUTHORITY_SHORT posts like any other Facebook feed post.

