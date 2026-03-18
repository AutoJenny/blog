# STAGE UI ISOLATE 01 — Capture stderr/stdout deterministically per job

## Goal

Prove that every Cursor job has both stdout and stderr captured to disk and summarized in `job_status.json`, even when parsing fails or zero assistant events occur.

## Files changed

| File | Change |
|------|--------|
| `app/job_store.py` | Added `_sanitize_tail()`, `read_stream_tails()`, `ensure_stream_logs_exist()`; `update_status()` extended with `error_code`, `stdout_bytes`, `stderr_bytes`, `stdout_tail`, `stderr_tail`. |
| `app/job_runner.py` | Call `ensure_stream_logs_exist()` after set_running_proc; append_stderr when empty; on terminal state call `read_stream_tails()` and pass into `update_status()`. |

## Job folder layout

Each job dir: `cursor_stdout_raw.log`, `cursor_stderr.log`, `job_status.json` (with stdout_bytes, stderr_bytes, stdout_tail, stderr_tail).

## Verification

```bash
JOB_DIR="tasks/hub/jobs/<job_id>"
ls -la "$JOB_DIR"
wc -c "$JOB_DIR/cursor_stdout_raw.log" "$JOB_DIR/cursor_stderr.log"
tail -n 20 "$JOB_DIR/cursor_stdout_raw.log"
tail -n 20 "$JOB_DIR/cursor_stderr.log"
```
