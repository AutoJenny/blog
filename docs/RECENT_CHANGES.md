# Recent changes

Summary of recent updates. Full detail is in **[CHANGELOG.md](CHANGELOG.md)**.

## 2026-01-30

- **Facebook preview/publish alignment and QA** — Preview formatter aligned with publish path for all content types (text-only: message, culture_fact, heritage_fact; image-post: product, weekly_*, etc.). Product price stripped in preview and publish. Parity script extended with `--platform facebook --weeks N`, `--qa-format`, exit code 0/1. New doc: [FACEBOOK_CULTURE_HERITAGE_FORMATTING.md](FACEBOOK_CULTURE_HERITAGE_FORMATTING.md).
- **Product price never in Facebook preview or publish** — `strip_price_from_caption()` in preview formatter and platform_publishers; template and meta do not show price.
- **Executor daily cap and idempotency** — One Facebook post per weekday (non-Saturday); atomic claim-before-publish; invariant validator; hotfix/cleanup scripts.

See [CHANGELOG.md](CHANGELOG.md) for artefacts, verification steps, and related docs.
