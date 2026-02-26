# W2 Phase 3.2-H1 — LLM timeout increase to 180s

File: `blueprints/header/llm_service.py`

## Change

**Before:**

```python
response = requests.post(
    f"{self.providers[provider]['base_url']}/api/chat",
    json=data,
    timeout=60
)
```

**After:**

```python
# Phase 3.2-H1: Increase Ollama timeout headroom for large JSON generations.
LLM_TIMEOUT_SECONDS = 180

response = requests.post(
    f"{self.providers[provider]['base_url']}/api/chat",
    json=data,
    timeout=LLM_TIMEOUT_SECONDS
)
```

- Previous Ollama timeout: **60 seconds**.
- New Ollama timeout: **180 seconds**.
- OpenAI timeout (30s) is unchanged.
- No changes to model, prompts, temperatures, or token limits.

## Grep proof

```bash
grep -n "LLM_TIMEOUT_SECONDS" blueprints/header/llm_service.py
```

Output:

```text
9:LLM_TIMEOUT_SECONDS = 180
58:                    timeout=LLM_TIMEOUT_SECONDS
```

