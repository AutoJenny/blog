# Recent changes

Summary of recent updates. Full detail is in **[CHANGELOG.md](CHANGELOG.md)**.

## 2026-02-23

- **Governance panel & blog candidates** — Homepage Governance modal shows current week’s scheduled content and Blog Candidates (ideas). One candidate can be selected as “this week’s blog”; **Start Blog Post** converts an idea to a draft and links it via the same week-item (no separate theme row). Delete deactivates a candidate; + New Idea adds an idea for the week. Technical ref: [governance-panel.md](page-reference/planning/governance-panel.md). User ref: [blog_post_workflow.md](kb/blog_post_workflow.md).
- **Docs & KB** — New technical doc: `docs/page-reference/planning/governance-panel.md`. ARCHITECTURE_V2_OVERVIEW, calendar_seed_model, calendar-ideas, quick-reference, and KB (blog_post_workflow, how_to_publish, status_and_stage_guide) updated for Governance and convert flow.

## 2026-01-30

- **Facebook preview/publish alignment and QA** — Preview formatter aligned with publish path for all content types (text-only: message, culture_fact, heritage_fact; image-post: product, weekly_*, etc.). Product price stripped in preview and publish. Parity script extended with `--platform facebook --weeks N`, `--qa-format`, exit code 0/1. New doc: [FACEBOOK_CULTURE_HERITAGE_FORMATTING.md](FACEBOOK_CULTURE_HERITAGE_FORMATTING.md).
- **Product price never in Facebook preview or publish** — `strip_price_from_caption()` in preview formatter and platform_publishers; template and meta do not show price.
- **Executor daily cap and idempotency** — One Facebook post per weekday (non-Saturday); atomic claim-before-publish; invariant validator; hotfix/cleanup scripts.

See [CHANGELOG.md](CHANGELOG.md) for artefacts, verification steps, and related docs.
