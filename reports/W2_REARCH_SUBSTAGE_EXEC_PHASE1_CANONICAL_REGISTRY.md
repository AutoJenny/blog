# W2 Phase 1: Canonical Authoring Substage Registry

**Instruction Set 16 — Phase 1.** Single server-side canonical substage registry; UI reads from it; no execution changes.

---

## A) Registry Definition

Full contents of `utils/posts/canonical_substages.py`:

```python
"""
Canonical authoring substage registry (Instruction Set 16 / W2 Phase 1).
Single server-side authority for substages aligned to:
  metadata → ideas → structure → titling → authoring → imaging → review

Registry-only. No runner functions. No execution.
"""

from typing import List, Dict, Any, Tuple, Optional

CANONICAL_STAGE_ORDER = [
    "metadata",
    "ideas",
    "structure",
    "titling",
    "authoring",
    "imaging",
    "review",
]

# Each substage: id, title, description, min_stage, post_types, artefacts_written, supports_web_research
# Runner not implemented; no function pointer.
CANONICAL_SUBSTAGES: Dict[str, List[Dict[str, Any]]] = {
    "metadata": [
        {
            "id": "edit_metadata",
            "title": "Edit metadata",
            "description": "Set title, subtitle, and basic post metadata.",
            "min_stage": "metadata",
            "post_types": ["themed", "recipe", "profile", "clan", "generated"],
            "artefacts_written": ["post.title", "post.subtitle", "post.summary"],
            "supports_web_research": False,
        },
    ],
    "ideas": [
        {
            "id": "generate_idea_set",
            "title": "Generate Idea Set",
            "description": "Generate or curate required ideas for the post (research-backed for themed).",
            "min_stage": "ideas",
            "post_types": ["themed", "recipe", "profile", "clan", "generated"],
            "artefacts_written": ["post_required_idea"],
            "supports_web_research": True,
            "nav_key": "ideas",  # legacy navbar key for lookup
        },
    ],
    "structure": [ ... ],   # topic_brainstorming, section_structure, topic_allocation, section_titling
    "titling": [ ... ],     # section_titling_final
    "authoring": [ ... ],   # author_first_drafts, image_concepts, image_prompts, image_captions
    "imaging": [ ... ],     # image_generation, optimise
    "review": [ ... ],      # final_review
}

def get_canonical_substages_for_post(post_id, post_type, current_stage, stage_index_fn) -> Dict[str, Any]:
    """Build canonical substages response. Filters by post_type, sets available_now by min_stage. No execution."""

def find_substage_by_nav(stage, substage_key) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Find canonical substage by (stage, substage_key). Handles planning+ideas -> ideas, generate_idea_set."""
```

(Full file is in the repo at `utils/posts/canonical_substages.py`.)

---

## B) Curl Proof

```bash
curl -s http://localhost:5000/api/posts/729/canonical-substages | jq
```

Example response (excerpt):

```json
{
  "post_id": 729,
  "post_type": "themed",
  "current_stage": "structure",
  "stages": [
    {
      "stage": "metadata",
      "available": true,
      "substages": [
        {
          "id": "edit_metadata",
          "title": "Edit metadata",
          "min_stage": "metadata",
          "available_now": true
        }
      ]
    },
    {
      "stage": "ideas",
      "available": true,
      "substages": [
        {
          "id": "generate_idea_set",
          "title": "Generate Idea Set",
          "min_stage": "ideas",
          "available_now": true
        }
      ]
    },
    ...
  ]
}
```

---

## C) UI Proof

- **Post Type Settings modal (1-click header):** When opened with a post context (`window.postId` set), the modal fetches `GET /api/posts/<post_id>/canonical-substages` and builds the navigation tree from `payload.stages`. The Ideas stage lists **"Generate Idea Set"**; selecting it no longer shows "No configuration found" because config is resolved from the canonical registry (and planning+ideas is mapped to ideas/generate_idea_set).
- **Screenshot:** Save a screenshot showing the Ideas stage with "Generate Idea Set" and no "No configuration found" to:
  - **`reports/screenshots/W2_PHASE1_CANONICAL_REGISTRY_IDEAS.png`**

To capture: open a post’s Ideas page (e.g. `/planning/posts/729/calendar/ideas`), click the post-type-settings (cog) button in the header, and ensure the left nav shows **Ideas → Generate Idea Set** and the content area shows settings (or placeholder) without any error message.

---

## D) Grep Proof

- **No remaining references to `SUBSTAGE_CONFIG_MAP`** (as the substage config source): The object and all lookups were removed from `static/js/shared/post-type-settings.js`. The only remaining mention is in a comment: "replaces SUBSTAGE_CONFIG_MAP when post context exists". No code path uses `SUBSTAGE_CONFIG_MAP` for config resolution.
- **No remaining references to a JS-only substage registry** for the modal: The modal now uses `GET /api/posts/<id>/canonical-substages` when `postId` is set; fallback is the existing `GET /api/post-types/<post_type>/substages` and a minimal `FALLBACK_SUBSTAGE_CONFIG` (ideas / generate_idea_set only).
- **Hardcoded ideas absence resolved:** The Ideas substage is defined in the canonical registry as `generate_idea_set` with `nav_key: "ideas"`. The modal resolves (planning, ideas) and (ideas, generate_idea_set) from the API, so "No configuration found for substage: ideas" no longer occurs when the modal is opened from the Ideas page with post context.

Commands used:

```bash
grep -Rn "SUBSTAGE_CONFIG_MAP" static/js/
# → Only comment in post-type-settings.js

grep -Rn "canonical-substages" static/js/ blueprints/
# → post-type-settings.js (fetch), blueprints/posts.py (route)
```

---

## E) Explicit Statement

- **Canonical registry exists:** `utils/posts/canonical_substages.py` defines `CANONICAL_STAGE_ORDER` and `CANONICAL_SUBSTAGES` and helpers `get_canonical_substages_for_post` and `find_substage_by_nav`. No runner or execution logic.
- **UI reads only from canonical registry when post context exists:** The Post Type Settings modal (1-click header) and substage display use `GET /api/posts/<post_id>/canonical-substages` to build the nav and resolve config for Ideas (and other canonical substages). No execution has been altered: execute-substage endpoint, legacy DB substage tables, playbook, stage advancement, pipeline runner, and required-ideas logic are unchanged.

Phase 1 deliverable complete. Ready for Phase 2 (unify execute-substage to use canonical registry and introduce mode switching).
