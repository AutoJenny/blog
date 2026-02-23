# Status and Stage Meanings

**Date:** 2026-02-23  
**Audience:** Content authors, editors

---

## Post Status (Database)

| Status | Meaning |
|--------|---------|
| **draft** | Post in progress; not ready for publish |
| **in_process** | Marked ready; can be published |
| **published** | Successfully published to Clan.com |
| **archived** | Archived (no longer active) |
| **deleted** | Soft-deleted |

---

## Workflow Stage (Internal Progression)

Inside draft posts, a **workflow stage** tracks how far you've progressed:

| Stage | Meaning |
|-------|---------|
| **idea** | Post created; planning started |
| **structured** | Section outline designed |
| **drafted** | All sections have draft content |
| **imaged** | All sections have images |
| **essentials_complete** | Title, subtitle, header image set |
| **ready** | Preflight OK; marked ready (status=in_process) |
| **published** | Post live on Clan.com |

---

## Stage Integrity

If you remove content (e.g. delete a draft, remove the header image), the stage **auto-downgrades** to match the current data. You can't stay at a higher stage if the criteria are no longer met.

---

## Override (Admin Only)

Some actions can be **overridden** when blocked by stage:

- Add `?override=1` to the URL
- Or send `{ "override": true }` in the request body

Override bypasses the stage gate. Use only when you need to fix a post manually. Normal workflow does not require override.

---

## Block Types — What Stops You?

| Block | Meaning |
|-------|---------|
| **Automation disabled** | Automation is turned off for this post or for this week. Turn it on in post settings or in the week view (Planning → Week View → Automation toggle). |
| **Stage blocked** | The post hasn’t reached the stage needed for this action. Complete the earlier work (e.g. drafts, images, essentials) first. |
| **Output blocked** | The post isn’t output-ready yet. For blog: finish title, summary, header image, and SEO meta. The Launchpad Output Readiness section shows what’s missing. |

---

## Week Automation Controls

In **Planning → Week View**, each week has:

- **Automation** — On/Off. If Off, automation skips that week.
- **Lock** — If Locked, automation cannot modify posts for that week.

---

## Related

- `docs/kb/blog_post_workflow.md` — How to publish
- `docs/POST_STATUS_MANAGEMENT.md` — Status and reuse rules
- `docs/workflow/workflow_stage_model.md` — Technical reference
