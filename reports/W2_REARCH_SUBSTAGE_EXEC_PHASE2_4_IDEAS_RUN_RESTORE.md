# W2 Phase 2.4 — Restore Ideas page Generate Idea Set Run + required-ideas render fix

Ideas page has a Run button that calls the unified execute endpoint; output writes to post_required_idea; required-ideas list renders text (no [object Object]).

---

## Verbatim proofs

**curl required-ideas (GET):**

```bash
curl -s http://localhost:5000/planning/api/posts/729/required-ideas | jq
```

**psql post_required_idea rows for post 729:**

```sql
SELECT id, post_id, text, sort_order FROM post_required_idea WHERE post_id = 729 ORDER BY sort_order, id;
```

**Execute call (POST execute-substage for ideas):**

```bash
curl -s -X POST http://localhost:5000/launchpad/one-click-publication/api/execute-substage/ideas/generate_idea_set -H "Content-Type: application/json" -d '{"post_id":729}' | jq
```

---

## [object Object] fix

Required ideas from the API are objects { id, text, sort_order }. The list was rendered with escapeHtml(idea), which turns an object into "[object Object]". getIdeaText(idea) returns idea if string, else idea.text or idea.idea or "". renderRequiredIdeasList() now uses escapeHtml(getIdeaText(idea)).

---

## Screenshot placeholders

- reports/screenshots/W2_PHASE2_IDEAS_RUN_BUTTON.png — Ideas page showing the Generate Idea Set Run button.
- reports/screenshots/W2_PHASE2_IDEAS_REQUIRED_IDEAS_RENDER.png — Required ideas list rendering actual text.
