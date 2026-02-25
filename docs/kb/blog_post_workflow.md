# Blog Post Workflow — User Guide

**Date:** 2026-02-23  
**Audience:** Content authors, editors

---

## Overview

A blog post progresses through stages from idea to published. The system enforces this progression so you can't skip ahead—for example, you must have drafted all sections before adding images.

---

## Workflow Stages

| Stage | What it means | What you do next |
|-------|---------------|------------------|
| **idea** | Post created; planning started | Complete expanded idea, taxonomy, section structure |
| **structured** | Section outline exists | Write drafts for each section |
| **drafted** | All sections have content | Add images to sections |
| **imaged** | All sections have images | Set title, subtitle, header image |
| **essentials_complete** | Publish essentials filled | Run Preflight, Mark Ready |
| **ready** | Marked ready to publish | Publish to Clan.com |
| **published** | Live on Clan.com | — |

---

## How to Advance

When you've completed the work for a stage, an **"Advance to [stage]"** button appears (on authoring and launchpad pages). Click it to move to the next stage.

You can't advance until the criteria are met—for example, to go from drafted to imaged, every section must have an image.

---

## How to Publish a Post

1. Complete all sections (drafted)
2. Add images to all sections (imaged)
3. Set **title**, **subtitle**, and **header image** (essentials_complete)
4. Open **Launchpad → Publishing**
5. Expand **Publish Essentials** for your post
6. Click **Preflight** to check requirements
7. Click **Mark Ready** (sets status to in_process)
8. Click **Publish** to send to Clan.com

---

## If a Route Is Blocked

If you see a message like *"Post is at stage 'idea'. This action requires stage: structured, drafted"*:

- Complete the required work for the earlier stage first
- Or use **Override** (admin only): add `?override=1` to the URL

---

## Choosing the Week’s Blog Post (Governance Panel)

On the **homepage**, open the **Governance** panel to see the current week’s scheduled content and **Blog Candidates** (ideas that can become the week’s blog post).

- **Select** one candidate with the radio button — that becomes “this week’s blog” (the selection is saved).
- **Start Blog Post** — Converts the selected idea into a draft post and links it to the week. You can then open the post from the panel or from Planning.
- **+ New Idea** — Add a new idea for the week (title and optional summary).
- **Edit / Move / Delete** — Edit the idea, move it to another week, or remove it from the list (delete deactivates the idea for this week).

If a candidate has already been converted, the panel shows **Open Post** instead of Start Blog Post, and the **Blog** row appears in the scheduled table at the top.

---

## Week-Level Controls (Planning Calendar)

In the **Week View**, you can:

- **Automation On/Off** — Controls whether automation runs for that week
- **Lock** — When locked, automation cannot modify posts for that week

---

## Related

- `docs/kb/status_and_stage_guide.md` — Status and stage meanings, block types
- `docs/kb/how_to_publish.md` — Publishing checklist
- `docs/workflow/workflow_stage_model.md` — Technical reference
- `docs/page-reference/planning/governance-panel.md` — Governance panel (technical)
