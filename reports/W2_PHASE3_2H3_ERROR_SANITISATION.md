# W2 Phase 3.2-H3 — LLM error sanitisation

Scope: `execute_generate_idea_set` in `blueprints/automation_execute.py`.

## Old behaviour (before H3)

When the LLM call or JSON parsing failed, `_generate_ideas_once` raised an exception (e.g. `RuntimeError('LLM generation failed: ...')` or `ValueError('LLM response is not valid JSON.')`), and the outer handler returned the raw exception text to the client:

```python
except Exception as e:
    logger.error("execute_generate_idea_set failed: %s", e)
    return {"success": False, "error": str(e)}, 500
```

Example client-facing error (from earlier runs):

```json
{
  "error": "LLM generation failed: HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=60)",
  "output_channel": "blog",
  "success": false
}
```

This exposed internal transport details (`HTTPConnectionPool`, host/port, and timeout internals) to the UI.

## New behaviour (after H3)

The exception is still raised inside `_generate_ideas_once`, but `execute_generate_idea_set` now:

- Logs the full exception (with stack trace) **server-side only**, and
- Returns a generic, sanitised error body to the client.

New exception handling block:

```python
except Exception as e:
    # Phase 3.2-H3: sanitize LLM/backend errors for clients; log full details server-side only.
    logger.error(
        "execute_generate_idea_set failed for post %s: %s",
        post_id,
        e,
        exc_info=True,
    )
    return {
        "success": False,
        "error": "LLM backend unavailable or exceeded timeout; generation aborted.",
    }, 500
```

## New client-facing error example

If the LLM call fails (backend unavailable / timeout / invalid JSON), a client calling:

```bash
curl -s -X POST \
  http://localhost:5000/launchpad/one-click-publication/api/execute-substage/ideas/generate_idea_set \
  -H "Content-Type: application/json" \
  -d '{"post_id":729}' | jq
```

will now see a response of the form:

```json
{
  "success": false,
  "error": "LLM backend unavailable or exceeded timeout; generation aborted."
}
```

All low-level details (HTTPConnectionPool, hostnames, stack traces) are preserved only in the server logs, not returned to the UI.

