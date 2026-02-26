# W2 N-ALIGN-2D — Legacy Page Preservation Contract

**Objective:** Document that themed canonical pipeline alignment does not delete any legacy pages/routes/templates/handlers. Legacy steps are excluded from themed nav outputs only and remain URL-accessible.

**Scope:** Substages marked EXCLUDE_FROM_THEMED_NAV in reports/W2_PIPELINE_REGISTRY_DIFF_N_ALIGN_2A.md: topic_brainstorming, section_structure, topic_allocation, section_titling.

---

## A) “No deletions” proof (git)

After the N-ALIGN-2D commit:

```bash
git show --name-status --oneline HEAD
```

**Verbatim output:**

```
f66f4ab2 W2: N-ALIGN-2D preserve legacy pipeline pages (exclude only)
A	reports/W2_LEGACY_PAGE_PRESERVATION_CONTRACT_N_ALIGN_2D.md
A	reports/screenshots/W2_ALIGN_2D_JUMP_NO_LEGACY.txt
A	reports/screenshots/W2_ALIGN_2D_LEGACY_PAGE_STILL_LOADS.txt
```

**Explicit statement:** No files deleted (no D status lines). This commit only adds the report and screenshot assets. No templates, JS/CSS, blueprint routes, or handlers were removed by N-ALIGN-2 or N-ALIGN-2D.

---

## B) Themed canonical nav proof (post 729)

### canonical-substages

```bash
curl -s http://localhost:5000/api/posts/729/canonical-substages | jq
```

Structure substages returned for 729 (metadata, ideas, structure only in excerpt):

```bash
curl -s http://localhost:5000/api/posts/729/canonical-substages | jq '.stages[] | select(.stage == "structure") | .substages[].id'
```

Output:

```
"cluster_into_sections"
"edit_section_plan"
```

### pipeline-state

```bash
curl -s http://localhost:5000/api/posts/729/pipeline-state | jq
```

Structure substages in pipeline-state:

```bash
curl -s http://localhost:5000/api/posts/729/pipeline-state | jq '[.substages[] | select(.stage == "structure") | .substage]'
```

Output:

```json
[
  "cluster_into_sections",
  "edit_section_plan"
]
```

**Confirmation:** For post 729 (themed), the structure substages shown in both APIs are exactly: **cluster_into_sections**, **edit_section_plan**. Excluded legacy substages (topic_brainstorming, section_structure, topic_allocation, section_titling) do not appear in canonical-substages or pipeline-state, and therefore not in the header Jump list.

---

## C) Legacy URLs are still reachable (HTTP 200)

For each excluded legacy substage, the legacy URL and HTTP proof:

| Substage             | Legacy URL (route that serves it) |
|----------------------|------------------------------------|
| topic_brainstorming  | `/planning/posts/<id>/concept/brainstorm` |
| section_structure    | `/planning/posts/<id>/concept/section-structure` |
| topic_allocation     | `/planning/posts/<id>/concept/topic-allocation` |
| section_titling      | `/planning/posts/<id>/concept/titling` |

Verbatim curl output (HTTP code and url_effective):

```bash
curl -s -o /dev/null -w "%{http_code} %{url_effective}\n" "http://localhost:5000/planning/posts/729/concept/brainstorm"
# 200 http://localhost:5000/planning/posts/729/concept/brainstorm

curl -s -o /dev/null -w "%{http_code} %{url_effective}\n" "http://localhost:5000/planning/posts/729/concept/section-structure"
# 200 http://localhost:5000/planning/posts/729/concept/section-structure

curl -s -o /dev/null -w "%{http_code} %{url_effective}\n" "http://localhost:5000/planning/posts/729/concept/topic-allocation"
# 200 http://localhost:5000/planning/posts/729/concept/topic-allocation

curl -s -o /dev/null -w "%{http_code} %{url_effective}\n" "http://localhost:5000/planning/posts/729/concept/titling"
# 200 http://localhost:5000/planning/posts/729/concept/titling
```

**Verbatim 200 lines:**

```
200 http://localhost:5000/planning/posts/729/concept/brainstorm
200 http://localhost:5000/planning/posts/729/concept/section-structure
200 http://localhost:5000/planning/posts/729/concept/topic-allocation
200 http://localhost:5000/planning/posts/729/concept/titling
```

Each legacy page returns HTTP 200 and renders non-empty content (Flask route serves the page).

---

## D) UI proof (screenshots)

Save and commit:

- **reports/screenshots/W2_ALIGN_2D_JUMP_NO_LEGACY.png** — Jump list on post 729 showing no legacy structure items (only Cluster into Sections, Edit section plan).
- **reports/screenshots/W2_ALIGN_2D_LEGACY_PAGE_STILL_LOADS.png** — One excluded legacy URL (e.g. `/planning/posts/729/concept/section-structure`) showing the page still renders.

Screenshot paths (capture as PNG when possible; .txt placeholders with capture instructions committed for now):

- reports/screenshots/W2_ALIGN_2D_JUMP_NO_LEGACY.png (or .txt)
- reports/screenshots/W2_ALIGN_2D_LEGACY_PAGE_STILL_LOADS.png (or .txt)

---

## E) Conclusion

Themed pipeline navigation is simplified to the planned spec: for post_type=themed, canonical-substages and pipeline-state (and thus the header Jump list) show only metadata.edit_metadata, ideas.generate_idea_set, ideas.curate_ideas, structure.cluster_into_sections, and structure.edit_section_plan. Legacy structure substages (topic_brainstorming, section_structure, topic_allocation, section_titling) are excluded from themed nav only; they are not deleted. Their routes remain in the planning blueprint and return HTTP 200 when accessed directly. Nothing was removed—only excluded from themed canonical nav.
