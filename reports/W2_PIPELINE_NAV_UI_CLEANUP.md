# W2 Pipeline Navigation — UI Cleanup (N3-Cleanup)

Remove redundant navigation and duplicate theme headers on the Ideas page. Single source: global header (theme, stage, Current/Next/Jump). No backend or pipeline-state changes.

---

## 1️⃣ Grep proof of removal

```bash
grep -R "ideas-pipeline-panel" -n templates/
```

No matches (panel and all references removed).

```bash
grep -R "updateIdeasPipelinePanel" -n .
```

No matches in `templates/` or `static/` (function and listeners removed).

---

## 2️⃣ Screenshot placeholder

`reports/screenshots/W2_PIPELINE_NAV_UI_CLEANUP_RESULT.png`

Page should show:
- Global theme header only once (Theme | Irish tartans in main header)
- Header pipeline strip (Current → Next → Jump)
- No second pipeline panel on Ideas page
- No duplicate theme title block; content starts with Post Metadata → Generate Idea Set → Required Ideas

---

## 3️⃣ Git proof

```bash
git log -1 --oneline
```

```
4acaa6a6 W2: pipeline navigation UI cleanup remove duplicate panels
```

---

## Changes made

- **C1:** Removed `#ideas-pipeline-panel`, `#ideas-pipeline-current`, `#ideas-pipeline-next` from `ideas.html`. Removed `updateIdeasPipelinePanel`, `blog-pipeline-state-ready` listener, and `window.BlogPipelineState` usage. Removed pipeline-panel CSS from `static/css/planning/ideas.css`.
- **C2:** Removed duplicate "Theme: …" block (`#theme-display`) from Ideas content area; theme comes only from global header. Removed theme-display update in `loadPostMetadata`.
- **C3:** Trimmed spacing; no orphan CSS. Optional: added static line under Required Ideas: "To advance to Structure, you need at least: 10 selected ideas, 3 categories, 6 sections."

Header pipeline strip is unchanged and remains the single navigation source.
