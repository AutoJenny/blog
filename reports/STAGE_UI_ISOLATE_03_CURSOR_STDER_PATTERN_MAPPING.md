# STAGE UI ISOLATE 03 — Cursor stderr pattern detection and error_code mapping

## Goal

Detect known Cursor failures from stderr and set job_status.error and job_status.error_code.

## Pattern list (_classify_stderr)

- Quota/usage: usage limit, spend limit, rate limit, quota, opus → CURSOR_QUOTA. Message: "Cursor usage/spend limit reached (see stderr)" + optional " Try model: ..."
- Auth: authentication, api key, auth required, 401 → CURSOR_AUTH. Message: "Cursor authentication required (CURSOR_API_KEY)"

Other codes: CURSOR_NO_OUTPUT, CURSOR_PROCESS_EXIT.

## Example

Stderr "You've hit your usage limit for Opus ..." → CURSOR_QUOTA. UI bubble shows the mapped message.
