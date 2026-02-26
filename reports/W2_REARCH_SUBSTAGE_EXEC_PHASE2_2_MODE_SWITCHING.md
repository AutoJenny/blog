# W2 Phase 2.2 — Substage mode switching (manual / assisted / auto)

Store per-post per-substage mode in `post.extra_settings.substage_modes`. API and UI for GET/PATCH; canonical-substages returns `current_mode`.

---

## Curl proof

**GET modes (verbatim):**

```bash
curl -s http://localhost:5000/api/posts/729/substage-modes | jq
```

Output:

```json
{
  "substage_modes": {},
  "success": true
}
```

**PATCH mode for ideas.generate_idea_set:**

```bash
curl -s -X PATCH http://localhost:5000/api/posts/729/substage-modes \
  -H "Content-Type: application/json" \
  -d '{"key":"ideas.generate_idea_set","mode":"assisted"}' | jq
```

Output:

```json
{
  "substage_modes": {
    "ideas.generate_idea_set": "assisted"
  },
  "success": true
}
```

**GET canonical-substages showing current_mode changed:**

```bash
curl -s http://localhost:5000/api/posts/729/canonical-substages | jq '.stages[] | select(.stage == "ideas") | .substages[] | {id, current_mode, can_execute}'
```

Output after PATCH:

```json
{
  "id": "generate_idea_set",
  "current_mode": "assisted",
  "can_execute": true
}
```

---

## UI

- Post Type Settings modal: for the selected substage (when from canonical registry), the **Substage mode** section shows:
  - **Mode:** dropdown (manual / assisted / auto); changing it PATCHes `/api/posts/<id>/substage-modes` with `{ key, mode }`.
  - **Min stage required:** from canonical payload.
  - **Can execute now:** Yes / No (from stage gating).

---

## Screenshot placeholder

- **reports/screenshots/W2_PHASE2_MODE_SWITCH_IDEAS.png** — Post Type Settings modal with Ideas → Generate Idea Set selected, showing Mode dropdown and Min stage / Can execute now.
