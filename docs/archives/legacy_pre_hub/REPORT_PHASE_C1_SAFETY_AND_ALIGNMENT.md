# Phase C1 Report — Safety & Alignment

**Date:** 2026-01-29  
**Scope:** Phase C1 remediation only (Safety & Alignment). No C2/C3.

---

## 1. Publish paths: before, after, and changes

### 1.1 Paths that could result in a Facebook post (before C1)

| Path | File | Function / trigger | Called `publish_to_facebook()`? | Weekday validation? |
|------|------|--------------------|---------------------------------|----------------------|
| Central executor | `scripts/scheduled_posting_executor.py` | `route_to_platform_publisher()` after `get_due_posts()` | Yes | Yes (was Mon/Wed/Fri for language; now Matrix v1.1) |
| Manual API | `blueprints/posts.py` | `api_publish_post(queue_id)` — `POST /api/posts/<id>/publish` | Yes | No |
| Workflow / automation | `blueprints/automation_execute.py` | `execute_publish_to_facebook(queue_id, data)` | Yes | No |
| Automation core | `blueprints/automation_core.py` | When substage == `publish_to_facebook` | No (returns 403 before call) | N/A |

So before C1, three code paths could call `publish_to_facebook()`: the executor (with validation), the manual API (no validation), and `execute_publish_to_facebook()` (no validation). Automation core already returned 403 before invoking the latter.

### 1.2 Paths after C1

| Path | Change | Result |
|------|--------|--------|
| **scheduled_posting_executor** | Unchanged as sole caller of `publish_to_facebook()`. Validation updated to Matrix v1.1 (see below). | **Only** path that can publish to Facebook. |
| **blueprints/posts.api_publish_post** | No longer calls `publish_to_facebook()`. Always returns 403 with a fixed message. | Disabled; manual publish cannot bypass validation. |
| **automation_execute.execute_publish_to_facebook** | No longer calls `publish_to_facebook()`. Always returns `({"success": False, "error": "..."}, 403)`. | Disabled; workflow cannot publish to Facebook. |
| **automation_core** | No code change (already returned 403 before calling execute_publish_to_facebook). | Still blocked. |

**Confirmed cause:** Wrong-day and duplicate posts occurred because (1) legacy Thursday language rows existed in the queue, and (2) paths that called `publish_to_facebook()` without weekday validation (manual API and/or `execute_publish_to_facebook`) could publish those rows.  
**Proposed change (implemented):** Only the executor may call `publish_to_facebook()`. All other paths return 403 and do not call the publisher.

---

## 2. Code diff summary (file-by-file)

### 2.1 `blueprints/posts.py`

- **Function:** `api_publish_post(queue_id)` (route `POST /api/posts/<int:queue_id>/publish`).
- **Change:** Removed all logic that loaded the post from the DB and called `publish_to_facebook(queue_id)`. The handler now immediately returns `403` with a JSON body explaining that Facebook publishing must go through the scheduled posting executor and that manual publish is disabled for date safety.
- **Observed behaviour:** Before, a client could publish any ready Facebook post by ID, including language on Thursday. After, the same request receives 403 and no publish occurs.

### 2.2 `blueprints/automation_execute.py`

- **Function:** `execute_publish_to_facebook(queue_id, data)`.
- **Change:** Removed the call to `publish_to_facebook(queue_id)` and the tuple return on success/failure. The function now only logs a warning and returns `({"success": False, "error": "Facebook publishing must go through scheduled_posting_executor. This path is disabled for date safety."}, 403)`.
- **Observed behaviour:** Before, workflow or any caller of this function could publish any queue row. After, callers always get 403 and no publish occurs.

### 2.3 `scripts/scheduled_posting_executor.py`

- **Class:** `ScheduledPostingExecutor`.
- **Changes:**
  1. **Matrix v1.1 weekday rules (C1.2 + C1.3)**  
     Replaced `validate_weekly_content_schedule()` with `validate_content_schedule()` and a class-level Matrix:
     - **Language** (`weekly_word`, `weekly_phrase`, `weekly_insult`): allowed **Tuesday only** (weekday 2). At most one language post (any of the three types) per week already published; otherwise the candidate is blocked.
     - **culture_fact:** Monday (1), Thursday (4).
     - **message:** Wednesday (3).
     - **authority_short:** Friday (5).
     - **product:** Saturday (6).
     - **depth_long:** Sunday (7).
     - Any `content_type` not in this matrix is not restricted (validation returns True).
  2. **Hard block legacy language on non-Tuesday (C1.3)**  
     Language rows with `scheduled_date` on any day other than Tuesday fail `validate_content_schedule()` (weekday not in `(2,)`) and are never returned as valid; they are never published by the executor.
  3. **Application of validation**  
     In `get_due_posts()`, the previous “weekly content only” check was replaced with a single call to `validate_content_schedule(post)` for every candidate post. So all Matrix content types are validated by weekday; language on Thursday is blocked at execution time.
  4. **scheduled_str / logging**  
     `scheduled_str` is set before `valid_posts.append(post)` and then used in `logger.debug()`, so the previous `NameError` risk in the validation loop is removed.

- **Observed behaviour:** Only posts that pass both date and Matrix v1.1 content-schedule validation are published. Thursday language (and any non-Tuesday language) is blocked; Tuesday language is allowed subject to the one-per-week rule.

---

## 3. Verification note

### 3.1 Thursday language cannot publish

- **Code:** In `scheduled_posting_executor.py`, `_CONTENT_WEEKDAY_MATRIX` sets `weekly_word`, `weekly_phrase`, and `weekly_insult` to `(2,)` (Tuesday only). In `validate_content_schedule()`, if `weekday not in allowed`, the function returns `False` and the post is not added to `valid_posts`. So any language row with `scheduled_date` on Thursday (weekday 4) fails validation and is never passed to `publish_to_facebook()`.
- **Other paths:** `api_publish_post` and `execute_publish_to_facebook` no longer call `publish_to_facebook()`; they return 403. So no path can publish Thursday language.

### 3.2 Tuesday language still can publish

- **Code:** A language row with `scheduled_date` on Tuesday (weekday 2) passes the weekday check. It is then subject only to the “one language post per week” check (no other language post already published for that ISO week). If that check passes, the post remains in `valid_posts` and is published by `route_to_platform_publisher()` → `publish_to_facebook(queue_id)`.
- **Flow:** Monitor runs `scheduled_posting_executor.py` periodically; `get_due_posts()` returns only posts that pass `validate_scheduled_date()` and `validate_content_schedule()`; the executor then calls `publish_to_facebook()` only for those posts. So Tuesday language that is due by time and is the only language post for that week will be published.

### 3.3 Single validated gate

- **Observed behaviour:** Every Facebook publish now goes through `scheduled_posting_executor.py`: it is the only place that calls `publish_to_facebook()`.
- **Confirmed cause:** All other call sites were disabled (403, no call to the publisher).

### 3.4 Verification run

A short Python check was run against the executor’s `validate_content_schedule()`:

- A language post with `scheduled_date` = Thursday (2026-01-29, weekday 4) returns `False` and is logged as `BLOCKED: ... scheduled for weekday 4 (allowed: (2,))`.
- A language post with `scheduled_date` = Tuesday (2026-01-27) passes the weekday check; it is then subject to the one-per-week DB check (in the run, another language post already existed for that week, so it was correctly blocked by that rule). When there is no other language post for the week, Tuesday language would be published.

---

## 4. Summary

- **Which publish paths existed before:** Executor (with old Mon/Wed/Fri language validation), manual `api_publish_post`, and `execute_publish_to_facebook`.
- **Which remain:** Only the executor; it is the single authoritative gate.
- **Which were disabled or rerouted:** Manual API and `execute_publish_to_facebook` were disabled (return 403, no call to `publish_to_facebook()`). Nothing was rerouted; the executor was already the intended gate and now is the only one.
- **Alignment:** Executor weekday validation now matches Matrix v1.1 (language Tuesday only; culture_fact Mon/Thu; message Wed; authority_short Fri; product Sat; depth_long Sun). Legacy language on any non-Tuesday day is hard-blocked at execution time.

Phase C1 is complete. No C2 or C3 work was done. Pending approval before proceeding to Phase C2.
