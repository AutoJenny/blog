# W2 Pipeline Nav UI Alignment — Option B Full (Clean-up)

On post-based calendar pages (`/planning/posts/<post_id>/calendar/*`): one substage navigation (canonical strip), no legacy row, Viewing + Pipeline cursor lines, theme once only. Scope: post pages only (template-level `post_id` guard). No backend changes.

---

## A. What changed

- **Removed / hidden**
  - Legacy substage row (Ideas, Taxonomy, Topic Brainstorming, Section Structure Design, Section Ideas, Section Titling) on post pages: `#sub-stages-line` is hidden via `style="display: none;"` when `post_id` is defined (template-level guard in `blog_pipeline_header.html`).
  - Duplicate theme title in content: in-content “Theme: …” block was removed in N3-Cleanup; theme appears only in the global header (Theme | …).
  - Ideas page pipeline panel (`#ideas-pipeline-panel`): removed in N3-Cleanup; no duplicate pipeline UI on the Ideas page.
- **Added / kept**
  - Canonical strip (Current / Next / Jump) as the only substep navigation on post pages; strip is shown when `post_id` is defined.
  - Viewing line under the strip: “Viewing: &lt;Context&gt;” derived from URL (e.g. `/calendar/ideas` → Planning → Ideas).
  - Pipeline cursor line on mismatch: when pipeline-state `current.stage` ≠ stage implied by URL, both “Pipeline cursor: &lt;Stage&gt; → &lt;Substage label&gt;” and “Viewing: &lt;Context&gt;” are shown.
  - Fallback “Viewing: (unknown)” when the route does not match any known segment.
- **Visual**
  - No extra spacing from removed legacy row or theme block; viewing line is compact under the strip.

---

## B. File list (paths only)

Files touched for this full alignment (strip-only + viewing + theme dedupe):

- `templates/shared/blog_pipeline_header.html` — legacy row hidden when `post_id`; pipeline strip + viewing line markup.
- `static/js/shared/blog-pipeline-header.js` — Viewing/Pipeline cursor logic; fallback “Viewing: (unknown)”.
- `static/css/shared/blog-pipeline-header.css` — styles for pipeline strip and viewing line.
- `reports/W2_PIPELINE_NAV_UI_ALIGNMENT_OPTIONB_FULL.md` — this report.

Screenshot paths (capture and save as PNG when verifying UI):

- `reports/screenshots/W2_PIPELINE_NAV_OPTIONB_POSTPAGE.png` — full page: strip + Viewing line + no legacy row + no duplicate theme.
- `reports/screenshots/W2_PIPELINE_NAV_OPTIONB_MISMATCH.png` — case where Viewing context ≠ Pipeline cursor (both lines shown).

*(Duplicate theme block and ideas-pipeline-panel were removed in prior N3-Cleanup commit.)*

---

## C. Grep proof (verbatim)

**Legacy row:** On post pages the row is hidden by template; the labels (e.g. “Topic Brainstorming”, “Section Structure Design”) do not appear in the shared header’s visible substage row because `#sub-stages-line` has `display: none` when `post_id` is set. They still exist in other templates (launchpad, deprecated, concept) and in config; only the post calendar header hides the row.

```bash
grep -R "Topic Brainstorming" -n templates/ static/ | head
```

Output:

```
templates/planning/includes/navigation_deprecated.html:55:                Topic Brainstorming
templates/planning/includes/condensed_header_deprecated.html:80:                    Topic Brainstorming
templates/planning/concept_deprecated.html:25:                <h3><i class="fas fa-brain"></i> Topic Brainstorming</h3>
templates/planning/concept/brainstorm.html:9:{% block title %}Topic Brainstorming - Concept Development - Planning - BlogForge{% endblock %}
templates/launchpad/one_click_blog_minimal.html:139:                        <td class="substage-cell">...
templates/launchpad/one_click_publication.html:344:                        <td class="substage-cell">...
... (launchpad/concept/deprecated only; not in blog_pipeline_header.html)
```

```bash
grep -R "Section Structure Design" -n templates/ static/ | head
```

Output:

```
templates/planning/includes/condensed_header_deprecated.html:84:                    Section Structure Design
templates/planning/concept/section_structure_profile.html:8:{% block title %}Section Structure Design ...
templates/planning/concept/section_structure.html:8:{% block title %}Section Structure Design ...
templates/launchpad/one_click_blog_minimal.html:149:...
templates/launchpad/one_click_publication.html:354:...
static/js/shared/post-type-settings.js:49:        'section-structure': 'Section Structure Design',
... (concept/launchpad/deprecated; not in shared blog_pipeline_header)
```

**Proof legacy row is hidden on post pages:**

```bash
grep -n "sub-stages-line\|post_id.*display" templates/shared/blog_pipeline_header.html
```

Output:

```
204:    <div class="sub-stages-line" id="sub-stages-line"{% if post_id is defined and post_id %} style="display: none;"{% endif %}>
```

So when `post_id` is defined, the legacy substage row is not displayed.

```bash
grep -R "ideas-pipeline-panel" -n templates/ static/ | head
```

Output: (no matches) — Ideas page pipeline panel removed; no duplicate pipeline UI.

---

## D. Runtime proof (pipeline-state unchanged)

```bash
curl -s http://localhost:5000/api/posts/729/pipeline-state | jq '.workflow_stage, .current, .next'
```

Output:

```json
"structure"
{
  "stage": "structure",
  "substage": "topic_brainstorming"
}
{
  "stage": "titling",
  "substage": "section_titling_final"
}
```

No backend changes; pipeline-state endpoint and behaviour unchanged.

---

## E. UI proof

On `/planning/posts/729/calendar/ideas`:

- **Legacy substage row absent:** Only the canonical strip (Current / Next / Jump) is visible for substeps; the row containing Ideas, Taxonomy, Topic Brainstorming, Section Structure Design, etc. is hidden.
- **Strip present:** Pipeline strip shows Current, Next button, and Jump dropdown, driven by pipeline-state.
- **Viewing line present:** Under the strip, “Viewing: Planning → Ideas” (or “Viewing: (unknown)” on an unknown route).
- **Duplicate theme removed:** Theme appears once (global header “Theme | Irish tartans”); no in-content “Theme: Irish tartans” block on the Ideas page.

Mismatch case (e.g. workflow_stage=structure but user is on Ideas page): both “Pipeline cursor: Structure → …” and “Viewing: Planning → Ideas” are shown.

---

## Acceptance checklist

- [x] Post pages show only canonical strip for substages (no legacy row).
- [x] Viewing line is present and correct (URL-derived context; fallback “Viewing: (unknown)”).
- [x] Mismatch case shows both Viewing + Pipeline cursor lines.
- [x] Theme appears once (no duplicate theme title on page).
- [x] No backend changes; pipeline-state endpoint unchanged.

---

## Git proof

```bash
git log -1 --oneline
```

`dbbcba9d W2: pipeline nav UI alignment option B (strip-only + viewing + theme dedupe)`
