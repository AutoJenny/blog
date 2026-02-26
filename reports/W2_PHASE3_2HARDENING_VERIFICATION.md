# W2 Phase 3.2 — Hardening verification (timeout, logging, error handling)

Scope: runtime behaviour of `ideas.generate_idea_set` after H1–H3.

---

## Final HTTP call (post 729)

Command:

```bash
curl -s -X POST \
  http://localhost:5000/launchpad/one-click-publication/api/execute-substage/ideas/generate_idea_set \
  -H "Content-Type: application/json" \
  -d '{"post_id":729}' | jq
```

Example response when the LLM backend is unavailable or times out:

```json
{
  "error": "LLM backend unavailable or exceeded timeout; generation aborted.",
  "output_channel": "blog",
  "success": false
}
```

This confirms:
- **No stack trace leakage**.
- **No raw HTTPConnectionPool(...)** details in the client response.
- Error is a single, sanitised line as required.

---

## SQL counts for post 729 (after earlier successful generation)

Command:

```bash
psql -d blog -c "
SELECT post_id,
       COUNT(*) AS total,
       COUNT(*) FILTER (WHERE is_selected) AS selected,
       COUNT(DISTINCT category) AS categories
FROM post_required_idea
WHERE post_id = 729
GROUP BY post_id;
"
```

Output:

```text
 post_id | total | selected | categories 
---------+-------+----------+------------
     729 |    30 |       30 |          5
(1 row)
```

This reflects the **most recent successful generation** run (via the controlled test harness in H2), which:
- Produced **30** ideas.
- Marked **all 30** as `is_selected = TRUE`.
- Covered **5** distinct categories (≥ 4).

---

## Logging verification

From the H2 controlled execution (monkey-patched `_generate_ideas_once` to bypass the LLM but exercise the logging path), the log output included:

```text
[IDEA_SET] post=729 ideas=30 categories=5 duration=0.0s
```

confirming the structured log format:

- Prefix: `[IDEA_SET]`
- Fields: `post`, `ideas`, `categories`, `duration` (seconds).

This log is emitted **only** on successful executions, and does not contain idea text or URLs.

---

## Summary

After H1–H3:

- **Timeout headroom:** Ollama calls now use `LLM_TIMEOUT_SECONDS = 180` (previously 60), reducing the likelihood of spurious timeouts for large JSON generations.
- **Structured logging:** `execute_generate_idea_set` logs `[IDEA_SET] post=… ideas=… categories=… duration=…s` for successful runs, making runtime behaviour observable without leaking payloads.
- **Error sanitisation:** All LLM/backend exceptions are logged server-side with full stack traces but are exposed to the client only as a single, generic error string, with no transport or stack details.

