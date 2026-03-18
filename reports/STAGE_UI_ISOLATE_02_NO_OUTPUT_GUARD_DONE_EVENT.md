# STAGE UI ISOLATE 02 — No assistant output as terminal failure + UI shows error

## Goal

When no assistant/delta/result within NO_ASSISTANT_OUTPUT_SECONDS (default 30s), mark job terminal and append done event. UI must render that error in the assistant bubble.

## Implementation

- Guard: NO_ASSISTANT_OUTPUT_SECONDS (env, default 30). On trigger: kill process, flush stderr, read_stream_tails(), update_status(state=failed, error=..., error_code=CURSOR_NO_OUTPUT or classified), append_event(done with stdout_tail, stderr_tail).
- UI: applyDone() sets bubble to data.error || data.detail when state is failed or cancelled.

## Example done event (cursor_events.jsonl)

```json
{"event":"done","state":"failed","error":"No assistant output produced","error_code":"CURSOR_NO_OUTPUT","stdout_tail":"...","stderr_tail":"..."}
```

## DOM

Assistant bubble shows the error string instead of "(Job started…)".
