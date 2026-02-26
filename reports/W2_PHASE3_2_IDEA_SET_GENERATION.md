# W2 Phase 3.2 — Diversity-first idea set generation (ideas.generate_idea_set)

Handler: `execute_generate_idea_set(post_id, data)` in `blueprints/automation_execute.py`.

## Behaviour (implemented)

- Uses `LLMService` with a strict JSON contract to generate **30–60** ideas for themed posts.
- Each idea has:
  - `text` (non-empty, trimmed, max ~1000 chars)
  - `category` (one of the fixed set below)
  - `rationale` (non-empty, 1-sentence style; fallback is synthesised if missing)
  - `source_urls` (JSON array of up to 3 strings, normalised)
  - `rank` (1..N, sequential and unique)
- Controlled category set (hard-coded list, no dynamic invention):

```text
history_timeline
definitions_differences
material_craft
regional_variation
myths_misconceptions
notable_examples
modern_revival
how_to_practical
sources_further_reading
```

- Storage semantics (replace-all):
  - `DELETE FROM post_required_idea WHERE post_id = %s`
  - Insert rows with:
    - `post_id`
    - `text`
    - `category`
    - `rationale`
    - `source_urls` (JSONB)
    - `rank`
    - `sort_order = rank - 1`
    - `is_selected = TRUE`
    - `created_by = 'llm'`
    - `updated_at` via default.

- Validation and diversity:
  - If `len(ideas) < 30` → **400**: `"Generated only N ideas; at least 30 required."`
  - If `len(ideas) > 60` → trimmed to 60 (ranks recomputed 1..N).
  - Compute `categories = {idea.category}`.
  - If `len(categories) < 4`:
    - Regenerate **once**.
    - If still `< 4` → **400** with:

      ```text
      Insufficient category diversity in generated ideas (have X categories).
      ```

---

## Execution attempts in this environment

### Direct Python call (no running Flask server)

Command:

```bash
cd /Users/autojenny/Documents/projects/blog && python3 - << 'EOF'
from blueprints.automation_execute import execute_generate_idea_set

result = execute_generate_idea_set(729, {})
print(result)
EOF
```

Output (LLM backend timeout — Ollama not reachable in this environment):

```text
Error executing LLM request: HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=60)
execute_generate_idea_set failed: LLM generation failed: HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=60)
({'success': False, 'error': "LLM generation failed: HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=60)"}, 500)
```

### Intended HTTP entrypoint (for when Flask is running)

Once the Flask app is running on port 5000, the canonical entrypoint is:

```bash
curl -s -X POST \
  http://localhost:5000/launchpad/one-click-publication/api/execute-substage/ideas/generate_idea_set \
  -H "Content-Type: application/json" \
  -d '{"post_id":729}' | jq
```

In this environment the Flask app was not running (and `python` was not available to start it), so this curl could not be executed end‑to‑end here. The handler itself is callable and fails solely due to the LLM backend timing out (see Python call above).

---

## Current SQL state for post 729 (before successful LLM run)

Because the LLM call failed, no new rows were written by the handler in this environment. The following queries show the **current** state for `post_id = 729`:

### Aggregate counts

```bash
psql -d blog -c "SELECT post_id,
       COUNT(*) AS total,
       COUNT(*) FILTER (WHERE is_selected) AS selected,
       COUNT(DISTINCT category) AS categories
FROM post_required_idea
WHERE post_id = 729
GROUP BY post_id;"
```

Output:

```text
 post_id | total | selected | categories 
---------+-------+----------+------------
     729 |     1 |        1 |          0
(1 row)
```

### Category breakdown

```bash
psql -d blog -c "SELECT category, COUNT(*) FROM post_required_idea WHERE post_id = 729 GROUP BY category ORDER BY COUNT(*) DESC;"
```

Output:

```text
 category | count 
----------+-------
          |     1
(1 row)
```

### Sample rows

```bash
psql -d blog -c "SELECT id, rank, category, is_selected,
       left(text,120) AS text,
       left(coalesce(rationale,''),120) AS rationale
FROM post_required_idea
WHERE post_id = 729
ORDER BY rank NULLS LAST, id
LIMIT 10;"
```

Output:

```text
 id | rank | category | is_selected |     text      | rationale 
----+------+----------+-------------+---------------+-----------
  5 |      |          | t           | Irish tartans | 
(1 row)
```

---

## Notes and next steps

- The **code-level** behaviour for Phase 3.2 is implemented as specified:
  - 30–60 ideas.
  - Fixed category set.
  - Diversity gate (≥ 4 distinct categories, with one regeneration).
  - Replace-all write to `post_required_idea` with `is_selected = TRUE`, `created_by = 'llm'`, `rank` and `sort_order` aligned.
- The **acceptance test** for post 729 (30–60 rows, all selected, ≥ 4 categories) cannot be demonstrated here because the LLM provider at `http://localhost:11434` is timing out.
- Once the Ollama service is available in your environment and Flask is running, re-running the curl above should:
  - Populate `post_required_idea` for post 729 with 30–60 rows.
  - Satisfy the aggregate constraints in the SQL checks.

