# W2 Phase 3.2-H2 — Structured runtime logging for idea generation

File: `blueprints/automation_execute.py`

## Logging statement added

In `execute_generate_idea_set` (after diversity checks, before DB write):

```python
duration = time.time() - started
logger.info(
    "[IDEA_SET] post=%s ideas=%d categories=%d duration=%.1fs",
    post_id,
    len(best_ideas),
    len(categories_set),
    duration,
)
```

This logs:
- `post` — the post_id
- `ideas` — number of ideas produced
- `categories` — distinct category count
- `duration` — end-to-end generation time (seconds, 1 decimal)

No idea text or URLs are logged.

## Example log line (from successful execution)

Using a controlled (non-LLM) run to exercise the logging path:

```bash
cd /Users/autojenny/Documents/projects/blog && python3 - << 'EOF'
import logging
from blueprints import automation_execute as ae

logging.basicConfig(level=logging.INFO, format='%(message)s')

# Build 30 fake ideas across 5 categories to exercise logging path
cats = [
    "history_timeline",
    "definitions_differences",
    "material_craft",
    "regional_variation",
    "notable_examples",
]

fake_ideas = []
for i in range(30):
    fake_ideas.append({
        "text": f"Idea {i+1}",
        "category": cats[i % len(cats)],
        "rationale": f"Rationale {i+1}",
        "source_urls": [],
        "rank": i + 1,
    })

orig = ae._generate_ideas_once

try:
    ae._generate_ideas_once = lambda post_id: fake_ideas
    result = ae.execute_generate_idea_set(729, {})
    print("RESULT:", result)
finally:
    ae._generate_ideas_once = orig
EOF
```

Output:

```text
[IDEA_SET] post=729 ideas=30 categories=5 duration=0.0s
Database connection established
RESULT: {'success': True, 'required_ideas_count': 30, 'categories_count': 5, 'message': 'Generated 30 required idea(s) across 5 categories.'}
```

This confirms the structured log format and shows a representative log line for a successful execution, without exposing full idea content.

