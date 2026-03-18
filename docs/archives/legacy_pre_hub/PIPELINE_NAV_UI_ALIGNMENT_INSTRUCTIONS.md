# Instruction Set — Align Header Stages/Substages With Canonical Pipeline

## Problem

The page currently shows **two different taxonomies**:

| What you see | Source | Used by |
|--------------|--------|--------|
| **Planning**, Research, Authoring, Imaging, Header | Template (`blog_pipeline_header.html`) | Top-level stage buttons |
| Ideas, Taxonomy, Topic Brainstorming, Section Structure Design, Section Ideas, Section Titling | `get_substages_for_navbar()` → DB/config | Sub-stage row under Planning |
| **Current → Next → Jump** (e.g. “Structure → Topic brainstorming”, “Titling → Section titling (final)”) | `GET /api/posts/<id>/pipeline-state` → canonical registry | Pipeline strip |

The **canonical framework** (used by pipeline-state, advance-stage, and gates) is:

- **Stages:** metadata → ideas → structure → titling → authoring → imaging → review  
- **Substages (examples):** Edit metadata; Generate Idea Set; Topic brainstorming, Section structure, Section ideas, Section titling; Section titling (final); First drafts, Image concepts, …; Image generation, Optimise; Final review  

So the **navbar** (Planning + Ideas, Taxonomy, Topic Brainstorming, …) does **not** match the **pipeline strip** (Current/Next/Jump). It’s unclear that they describe the same pipeline.

---

## Canonical vs legacy mapping

| Canonical stage | Canonical substages (labels) | Legacy equivalent |
|-----------------|------------------------------|-------------------|
| **metadata** | Edit metadata | (inside Planning; often no dedicated link) |
| **ideas** | Generate Idea Set | Planning → Ideas |
| **structure** | Topic brainstorming, Section structure, Section ideas, Section titling | Planning → Topic Brainstorming, Section Structure Design, Section Ideas, Section Titling |
| **titling** | Section titling (final) | (inside Planning or separate) |
| **authoring** | First drafts, Image concepts, Image prompts, Image captions | Authoring → … |
| **imaging** | Image generation, Optimise | Imaging → … |
| **review** | Final review | Header → … |

**Research** in the current UI is an optional path (e.g. background research); it is **not** one of the seven canonical stages. The canonical spine is: metadata → ideas → structure → titling → authoring → imaging → review.

---

## Objective

Make the **visible header** use the **same stages and substages** as the canonical pipeline (and thus as the pipeline strip). After alignment:

- One clear pipeline on the page: **Theme | Stage: STRUCTURE** and **Current → Next → Jump**.
- Any stage/substage row in the header should show **canonical** stage names and substage labels (or be removed and only the pipeline strip used).

---

## Resolution options

### Option A — Drive header from canonical (recommended)

**Goal:** The sub-stage row (and optionally the top-level stage row) is built from the **canonical** registry so labels and order match the pipeline strip and Jump dropdown.

**Steps:**

1. **Add a template helper or endpoint** that returns canonical stages and substages for the navbar (filtered by `post_type`), with for each substage:
   - `stage` (canonical), `substage` (id), `label` (canonical title), `nav_url` (from existing `_get_pipeline_nav` logic or equivalent).

2. **In `blog_pipeline_header.html`:**
   - **Either:** Replace the current sub-stage groups (built from `get_substages_for_navbar`) with a **single sub-stage row** built from the canonical list (grouped by canonical stage: Metadata, Ideas, Structure, Titling, Authoring, Imaging, Review). Use the **canonical labels** (e.g. “Generate Idea Set”, “Topic brainstorming”, “Section structure”, “Section ideas”, “Section titling”, “Section titling (final)”).
   - **Or:** Keep the top-level buttons but rename them to the **canonical** stage names where they map 1:1 (e.g. “Ideas”, “Structure”, “Titling”, “Authoring”, “Imaging”, “Review”), and make the sub-stage row use the same canonical substage list and labels. “Planning” would be replaced by **Metadata**, **Ideas**, **Structure**, **Titling** as separate stage buttons if you want a 1:1 match.

3. **Map URLs:** Reuse the same `nav_url` logic used by pipeline-state (e.g. ideas → `/planning/posts/<id>/calendar/ideas`, structure → `/planning/posts/<id>/calendar/structure`, etc.). Existing routes (e.g. concept/section_structure, concept/titling) stay; the navbar just links to them with canonical labels.

4. **Research:** Decide whether to (a) keep Research as a separate top-level button that does **not** sit in the canonical spine (with a short tooltip: “Optional research”), or (b) remove it from the main pipeline row and access it via Jump or a separate “Research” link.

**Result:** The page shows the same stages/substages as “Current / Next / Jump” and the backend. No duplicate mental model.

---

### Option B — Pipeline strip only (simplest)

**Goal:** Remove the **legacy sub-stage row** (Ideas, Taxonomy, Topic Brainstorming, Section Structure Design, …) and use **only** the pipeline strip (Current / Next / Jump) for substage-level navigation.

**Steps:**

1. In `blog_pipeline_header.html`, **hide or remove** the `sub-stages-line` block (the row that contains the sub-stage groups from `get_substages_for_navbar`).

2. Keep the **top-level** stage buttons (Planning, Research, Authoring, Imaging, Header) only if they still add value (e.g. jump to a section); they become “coarse” links. Optionally add a short line above or below: “Pipeline: use Current / Next / Jump below.”

3. Ensure the **pipeline strip** is always visible when `post_type` is set (it already is), so users have a single place for “where I am” and “what’s next.”

**Result:** No second list of substages; one pipeline spine (Current → Next → Jump). The legacy labels disappear from the header; canonical labels are only in the strip and in Jump.

---

### Option C — Add clarity without changing structure

**Goal:** Keep both rows but make the **mapping** obvious so users know they refer to the same pipeline.

**Steps:**

1. Add a single line **above** the sub-stage row, e.g.:  
   **“Pipeline: Metadata → Ideas → Structure → Titling → Authoring → Imaging → Review.”**

2. In the “Stage: …” line (early-stage indicator), use the **canonical** stage name (e.g. “Stage: STRUCTURE (5 sections)”) so it matches the pipeline strip.

3. Optionally, in the sub-stage row, show **canonical** labels in parentheses where they differ from legacy, e.g. “Topic Brainstorming (Topic brainstorming)” until a full rename is done.

**Result:** Users see that the pipeline strip and the navbar describe the same sequence, even if labels still differ slightly.

---

## Recommendation

- Prefer **Option A** if you want one consistent pipeline everywhere (navbar = canonical = pipeline strip).
- Use **Option B** if you want the smallest change and are happy with “coarse” stage buttons + pipeline strip only for substeps.

---

## Implementation notes (for Option A)

- **Canonical data source:** `utils/posts/canonical_substages.py` (`CANONICAL_STAGE_ORDER`, `CANONICAL_SUBSTAGES`) and/or `GET /api/posts/<id>/pipeline-state` (which already returns `substages[]` with `stage`, `substage`, `label`, `nav_url`).
- **Nav URL mapping:** Reuse the same logic as in `blueprints/posts.py` (`_get_pipeline_nav`) so navbar links match Jump behaviour.
- **Post-type filtering:** Only show stages/substages that apply to the current `post_type` (canonical registry already has `post_types` per substage).
- **No backend change to pipeline-state or advance-stage:** This is UI-only alignment; keep using the canonical registry and pipeline-state API as they are.

---

## Acceptance

- On the Ideas page (and any post page), it is **clear** that the pipeline is: **metadata → ideas → structure → titling → authoring → imaging → review**.
- The **labels** visible in the header (or in the pipeline strip only) match the **canonical** substage names (e.g. “Generate Idea Set”, “Topic brainstorming”, “Section structure”, “Section ideas”, “Section titling”, “Section titling (final)”).
- There is **no** conflicting second list (e.g. “Ideas, Taxonomy, Topic Brainstorming, Section Structure Design, Section Ideas, Section Titling”) unless it is explicitly the same list with the same labels and order as the canonical pipeline.
