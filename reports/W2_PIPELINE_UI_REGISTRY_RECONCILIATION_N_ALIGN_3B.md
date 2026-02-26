# W2 N-ALIGN-3B — UI vs Registry Reconciliation (Report-Only)

No code changes. No filtering logic changes. Ground-truth capture only.

---

## Section A — UI Surface Capture (Authoritative User Reality)

Context: post `729` (themed), page `"/planning/posts/729/calendar/ideas"`.

### 1️⃣ Header Jump List

Console snippet:

```js
[...document.querySelectorAll('.pipeline-jump-item')]
  .map(el => el.textContent.trim())
```

**Raw array output:**

```json
[
  "Metadata → Edit metadata",
  "Ideas → Generate Idea Set",
  "Ideas → Curate ideas",
  "Structure → Cluster into Sections",
  "Structure → Edit section plan",
  "Titling → Section titling (final)",
  "Authoring → First drafts",
  "Authoring → Image concepts",
  "Authoring → Image prompts",
  "Authoring → Image captions",
  "Imaging → Image generation",
  "Imaging → Optimise",
  "Review → Final review"
]
```

**Count (Jump items):** `13`

### 2️⃣ Stages/Substages Modal (Settings Cog)

Console snippet (as instructed):

```js
[...document.querySelectorAll('#post-type-settings-modal .nav-tree-item')]
  .map(el => el.textContent.trim())
```

**Raw array output:**

```json
[]
```

**Count (`.nav-tree-item`):** `0`

**What is actually shown in the modal (equivalent tree items):**

Selector used (because `.nav-tree-item` does not exist in this modal implementation):

```js
[...document.querySelectorAll('#post-type-settings-modal .nav-stage-header, #post-type-settings-modal .nav-substage')]
  .map(el => el.textContent.trim())
```

**Raw array output:**

```json
[
  "Metadata",
  "Edit metadata",
  "Ideas",
  "Generate Idea Set",
  "Curate ideas",
  "Structure",
  "Cluster into Sections",
  "Edit section plan",
  "Titling",
  "Section titling (final)",
  "Authoring",
  "First drafts",
  "Image concepts",
  "Image prompts",
  "Image captions",
  "Imaging",
  "Image generation",
  "Optimise",
  "Review",
  "Final review"
]
```

**Count (modal tree items incl. stage headers):** `20`  
Breakdown: **7 stage headers** + **13 substage entries**.

### 3️⃣ Legacy Stage Row (if visible anywhere)

Console snippet:

```js
document.querySelectorAll('#sub-stages-line .substage-item').length
```

**Result:** `0`

### UI flat table (surfaces)

| Surface | Stage | Substage Label | Counted In UI |
|--------|-------|----------------|---------------|
| Jump | Metadata | Edit metadata | YES |
| Jump | Ideas | Generate Idea Set | YES |
| Jump | Ideas | Curate ideas | YES |
| Jump | Structure | Cluster into Sections | YES |
| Jump | Structure | Edit section plan | YES |
| Jump | Titling | Section titling (final) | YES |
| Jump | Authoring | First drafts | YES |
| Jump | Authoring | Image concepts | YES |
| Jump | Authoring | Image prompts | YES |
| Jump | Authoring | Image captions | YES |
| Jump | Imaging | Image generation | YES |
| Jump | Imaging | Optimise | YES |
| Jump | Review | Final review | YES |
| Modal | Metadata | (stage header) | YES (header item) |
| Modal | Metadata | Edit metadata | YES |
| Modal | Ideas | (stage header) | YES (header item) |
| Modal | Ideas | Generate Idea Set | YES |
| Modal | Ideas | Curate ideas | YES |
| Modal | Structure | (stage header) | YES (header item) |
| Modal | Structure | Cluster into Sections | YES |
| Modal | Structure | Edit section plan | YES |
| Modal | Titling | (stage header) | YES (header item) |
| Modal | Titling | Section titling (final) | YES |
| Modal | Authoring | (stage header) | YES (header item) |
| Modal | Authoring | First drafts | YES |
| Modal | Authoring | Image concepts | YES |
| Modal | Authoring | Image prompts | YES |
| Modal | Authoring | Image captions | YES |
| Modal | Imaging | (stage header) | YES (header item) |
| Modal | Imaging | Image generation | YES |
| Modal | Imaging | Optimise | YES |
| Modal | Review | (stage header) | YES (header item) |
| Modal | Review | Final review | YES |

**Total UI-visible substage entries (Jump):** 13  
**Total UI-visible substage entries (Modal, excluding stage headers):** 13  
**Total UI-visible nav items in modal (including stage headers):** 20

---

## Section B — Canonical Registry Capture

From code:

```bash
grep -R "CANONICAL_SUBSTAGES" -n utils/posts/
```

Verbatim output:

```
utils/posts/canonical_substages.py:36:CANONICAL_SUBSTAGES: Dict[str, List[Dict[str, Any]]] = {
utils/posts/canonical_substages.py:251:        substages_raw = CANONICAL_SUBSTAGES.get(stage, [])
utils/posts/canonical_substages.py:320:    for s in CANONICAL_SUBSTAGES.get(stage, []):
utils/posts/canonical_substages.py:327:        for s in CANONICAL_SUBSTAGES.get("ideas", []):
utils/posts/canonical_substages.py:331:    for canon_stage, substages in CANONICAL_SUBSTAGES.items():
Binary file utils/posts/__pycache__/canonical_substages.cpython-313.pyc matches
```

Programmatic extraction of registry IDs (via importing `utils.posts.canonical_substages.CANONICAL_SUBSTAGES`) produced:

```
COUNT 17
metadata	edit_metadata
ideas	generate_idea_set
ideas	curate_ideas
structure	cluster_into_sections
structure	edit_section_plan
structure	topic_brainstorming
structure	section_structure
structure	topic_allocation
structure	section_titling
titling	section_titling_final
authoring	author_first_drafts
authoring	image_concepts
authoring	image_prompts
authoring	image_captions
imaging	image_generation
imaging	optimise
review	final_review
```

**Total canonical registry substages:** `17`

---

## Section C — Canonical Output for Post 729

### canonical-substages (post 729)

```bash
curl -s http://localhost:5000/api/posts/729/canonical-substages | jq
```

Returned stage/substage IDs (flattened):

```
metadata	edit_metadata
ideas	generate_idea_set
ideas	curate_ideas
structure	cluster_into_sections
structure	edit_section_plan
titling	section_titling_final
authoring	author_first_drafts
authoring	image_concepts
authoring	image_prompts
authoring	image_captions
imaging	image_generation
imaging	optimise
review	final_review
```

**Total themed-visible canonical substages (729):** `13`

### pipeline-state (post 729)

```bash
curl -s http://localhost:5000/api/posts/729/pipeline-state | jq
```

Flattened:

```
metadata	edit_metadata	Edit metadata
ideas	generate_idea_set	Generate Idea Set
ideas	curate_ideas	Curate ideas
structure	cluster_into_sections	Cluster into Sections
structure	edit_section_plan	Edit section plan
titling	section_titling_final	Section titling (final)
authoring	author_first_drafts	First drafts
authoring	image_concepts	Image concepts
authoring	image_prompts	Image prompts
authoring	image_captions	Image captions
imaging	image_generation	Image generation
imaging	optimise	Optimise
review	final_review	Final review
```

---

## Section D — Diff Table

Master reconciliation table (includes all registry substages + notes about legacy-only items).

| Substage ID | Label | In UI Jump | In Modal | In Canonical Registry | In Canonical for 729 | Notes |
|------------|-------|------------|----------|------------------------|----------------------|-------|
| edit_metadata | Edit metadata | YES | YES | YES | YES | — |
| generate_idea_set | Generate Idea Set | YES | YES | YES | YES | — |
| curate_ideas | Curate ideas | YES | YES | YES | YES | — |
| cluster_into_sections | Cluster into Sections | YES | YES | YES | YES | — |
| edit_section_plan | Edit section plan | YES | YES | YES | YES | — |
| topic_brainstorming | Topic brainstorming | NO | NO | YES | NO | Legacy structure substage; excluded from themed canonical outputs |
| section_structure | Section structure | NO | NO | YES | NO | Legacy structure substage; excluded from themed canonical outputs |
| topic_allocation | Section ideas | NO | NO | YES | NO | Legacy structure substage; excluded from themed canonical outputs |
| section_titling | Section titling | NO | NO | YES | NO | Legacy structure substage; excluded from themed canonical outputs |
| section_titling_final | Section titling (final) | YES | YES | YES | YES | — |
| author_first_drafts | First drafts | YES | YES | YES | YES | — |
| image_concepts | Image concepts | YES | YES | YES | YES | — |
| image_prompts | Image prompts | YES | YES | YES | YES | — |
| image_captions | Image captions | YES | YES | YES | YES | — |
| image_generation | Image generation | YES | YES | YES | YES | — |
| optimise | Optimise | YES | YES | YES | YES | — |
| final_review | Final review | YES | YES | YES | YES | — |

Note: the modal additionally shows **stage headers** (Metadata/Ideas/Structure/Titling/Authoring/Imaging/Review). These are UI navigation items but are **not** canonical substages (no substage ID).

---

## Section E — Reconciliation Statement

- Total canonical registry substages = **17**
- Total themed-visible canonical substages (729) = **13**
- Total UI-visible substages (Jump + Modal) = **13**

Discrepancy explanation (plain language): The canonical registry still defines 17 substages, including 4 legacy structure substages (topic_brainstorming, section_structure, topic_allocation, section_titling). For themed post 729, the canonical outputs (canonical-substages and pipeline-state) return only 13 substages, excluding those 4 legacy structure items, and the UI Jump list mirrors that filtered pipeline-state view. The “~21” perception comes from counting **both** stage headers and substages in the Settings modal: the modal renders **20** tree items total (7 stage headers + 13 substages), even though the substage count remains 13. Additionally, the legacy substage row is not present in the DOM on this post page (`0` items), so it is not contributing to the count here.

---

### Authoritative count statement (3 lines)

Canonical registry substages (code) = **17**  
Canonical substages for themed post 729 (API) = **13**  
UI-visible substages for post 729 (Jump + Modal) = **13**  \n
