# Facebook culture/heritage header and formatting rules

**Purpose:** Ensure preview and publish show exactly the same text for culture_fact (Monday) and heritage_fact (Thursday) posts. Same rules apply to message posts for consistency; only culture_fact and heritage_fact get the authoritative header.

## Header strings (exact)

| content_type  | First line (header)   |
|--------------|------------------------|
| culture_fact | UNDERSTANDING SCOTLAND |
| heritage_fact| SCOTTISH HERITAGE      |

Defined in `utils/formatting/culture_headers.py` as `_HEADERS`. Message and other text-only types do not get a header; the formatter is a no-op for them.

## Composition

- **Final text:** `HEADER + "\n\n" + title_line + "\n" + body`
  - Two newlines after the header.
  - One newline between title (first non-empty line of content) and body (remaining lines).

## Newline and whitespace rules

- **Input normalisation (before applying header):**
  - Line endings: `\r\n` and `\r` → `\n`
  - Trim each line (strip leading/trailing spaces)
  - Remove leading and trailing blank lines
  - Collapse runs of **3 or more** blank lines to **2**
- **Output:**
  - No trailing spaces on any line
  - At most one trailing newline (prefer none)

Shared helper: `normalise_text_whitespace()` in `utils/formatting/culture_headers.py`. Used by both preview (`utils/channel_preview/formatters/facebook.py`) and publish (`utils/platform_publishers.py`).

## Parity script

Run whenever format logic changes:

```bash
# By IDs
PYTHONPATH=. python3 scripts/prove_preview_publish_parity.py --ids 21089,21086,21482

# Upcoming/recent posts (next N weeks)
PYTHONPATH=. python3 scripts/prove_preview_publish_parity.py --platform facebook --weeks 2

# With formatting QA (header present, newline collapse, no trailing spaces)
PYTHONPATH=. python3 scripts/prove_preview_publish_parity.py --platform facebook --weeks 2 --qa-format
```

Exit code: **0** = all PASS, **1** = one or more FAIL.

## Backfill

One-time backfill for existing queue rows missing the header: `scripts/backfill_culture_headers.py`. Run **only once or when header rules change**; do not run on every deployment. Idempotent: rows whose first non-empty line is already the correct header are skipped. Use `--dry-run` to confirm zero changes before/after.

## Related docs

- `docs/PREVIEW_FACEBOOK_MATCH_PUBLISH.md` — Preview/publish parity (culture, heritage, product, weekly).
- `utils/formatting/culture_headers.py` — Source of header strings and normalisation.
