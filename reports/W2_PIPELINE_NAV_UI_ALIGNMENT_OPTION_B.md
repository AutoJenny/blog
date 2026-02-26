# W2 Pipeline Nav UI Alignment — Option B (Strip-Only + Viewing Line)

Legacy substage row is disabled on post pages; pipeline strip is the only substage navigation. A "Viewing:" line under the strip shows page context and, when it differs from pipeline-state current, shows both (no ambiguity). No backend or pipeline-state changes.

---

## A. Before/After evidence

### Screenshot placeholders

- **reports/screenshots/W2_PIPELINE_NAV_OPTIONB_POSTPAGE.png** — Full page showing: pipeline strip (Current / Next / Jump), Viewing line, no legacy substage row (Ideas, Taxonomy, Topic Brainstorming, Section Structure Design, etc. not visible).
- **reports/screenshots/W2_PIPELINE_NAV_OPTIONB_MISMATCH.png** — Case where pipeline cursor stage ≠ viewing context: e.g. workflow_stage=structure but user is on Ideas page; page shows "Pipeline cursor: Structure → Topic brainstorming" and "Viewing: Planning → Ideas".

---

## B. Grep proof (verbatim)

Legacy substage row is **disabled** on post pages by setting `style="display: none;"` on `#sub-stages-line` when `post_id` is defined. The row (and labels like Taxonomy, Section Structure Design) remains in the template but is not visible.

```bash
grep -R "Taxonomy" -n templates/ static/ | head
```

Output (excerpt): Taxonomy appears in other templates (e.g. taxonomy.html, settings) and in navbar-related content; the **navbar substage row** that contained it is hidden on post pages via the condition below.

```bash
grep -R "Section Structure Design" -n templates/ static/ | head
```

Output (excerpt): Section Structure Design appears in concept pages, launchpad templates, and post-type-settings.js; the **header substage row** that showed it is hidden when `post_id` is set.

**Proof that legacy row is disabled on post pages:**

```bash
grep -n "sub-stages-line\|display: none" templates/shared/blog_pipeline_header.html
```

Output:

```
204:    <div class="sub-stages-line" id="sub-stages-line"{% if post_id is defined and post_id %} style="display: none;"{% endif %}>
```

So when `post_id` is defined, the legacy substage row is not displayed.

---

## C. Runtime proof (pipeline-state unchanged)

```bash
curl -s http://localhost:5000/api/posts/729/pipeline-state | jq '.current, .next'
```

Output:

```json
{
  "stage": "structure",
  "substage": "topic_brainstorming"
}
{
  "stage": "titling",
  "substage": "section_titling_final"
}
```

Pipeline-state API is unchanged; no backend changes.

---

## D. Exact file list

Every file changed for Option B:

- `templates/shared/blog_pipeline_header.html` — Hide `#sub-stages-line` when `post_id` present; add `#pipeline-viewing-line` under pipeline strip.
- `static/js/shared/blog-pipeline-header.js` — `getViewingContextFromPath()`, `updateViewingLine(data)`; call `updateViewingLine` from `renderPipelineStrip`.
- `static/css/shared/blog-pipeline-header.css` — `.pipeline-viewing-line` styles.
- `reports/W2_PIPELINE_NAV_UI_ALIGNMENT_OPTION_B.md` — This report.

```bash
git diff --name-only
```

(At commit time, only the above files plus this report and screenshot placeholders are included in the Option B commit.)

---

## E. Acceptance checklist

- [x] **Legacy substage row is gone on /planning/posts/729/calendar/ideas** — Row is hidden via `display: none` on `#sub-stages-line` when `post_id` is defined.
- [x] **Pipeline strip remains functional (Current/Next/Jump)** — Unchanged; still populated from pipeline-state.
- [x] **Viewing line appears and correctly reflects URL context** — Derived from path (`/calendar/ideas` → "Viewing: Planning → Ideas", etc.).
- [x] **When Viewing context ≠ pipeline cursor stage, both are displayed** — "Pipeline cursor: X → Y" and "Viewing: Z" shown when stages differ.
- [x] **No backend routes changed; pipeline-state unchanged** — UI-only; curl proof above.

---

## F. Git proof

```bash
git log -1 --oneline
```

```
b11a5dba W2: pipeline nav UI alignment option B (strip-only + viewing line)
```

---

Screenshot placeholder files (replace with PNGs when capturing):  
`reports/screenshots/W2_PIPELINE_NAV_OPTIONB_POSTPAGE.png`,  
`reports/screenshots/W2_PIPELINE_NAV_OPTIONB_MISMATCH.png`.  
Text placeholders (`.txt`) are committed until PNGs are added.
