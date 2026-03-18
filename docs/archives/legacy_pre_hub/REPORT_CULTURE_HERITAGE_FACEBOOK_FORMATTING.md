# Report: Culture / Heritage Facebook Formatting

**Date:** 2026-01-30  
**Scope:** Facebook culture_fact (Monday) and heritage_fact (Thursday) only. All other content types unchanged.

---

## 1. Files changed / added

| File | Change |
|------|--------|
| **utils/formatting/__init__.py** | **New.** Exposes `apply_culture_or_heritage_header`. |
| **utils/formatting/culture_headers.py** | **New.** Single shared formatter: header strings (A1), casing (A2), line breaks (A3), normalisation (A4), no DB/side effects. |
| **utils/platform_publishers.py** | In `publish_to_facebook()`: for culture_fact/heritage_fact, call `apply_culture_or_heritage_header(content_type, message_text)` before `format_message_for_facebook(content)`. |
| **utils/channel_preview/formatters/facebook.py** | Apply same `apply_culture_or_heritage_header(content_type, raw_text)` before `format_message_for_facebook(content)` so preview matches publish byte-for-byte. |
| **scripts/prove_preview_publish_parity.py** | Import and use `apply_culture_or_heritage_header` when computing publish text so parity test compares like-with-like for culture/heritage. |
| **scripts/backfill_culture_headers.py** | **New.** One-time backfill: target unpublished facebook culture_fact/heritage_fact rows; apply header; update if changed; CSV artefact; --dry-run (default) / --apply; idempotent (skip rows already starting with correct header). |
| **docs/BACKFILL_CULTURE_HEADERS_20260130.csv** | **Artefact.** queue_id, content_type, status, changed. |
| **docs/PARITY_PROOF_FACEBOOK_20260130.txt** | **Artefact.** Parity proof for culture_fact and heritage_fact IDs. |

---

## 2. Backfill counts (dry-run + apply)

- **Dry-run (first run):** Target rows: 22. Would change: 22. Sample IDs: 21086, 21087, 21089, 21090, …
- **Apply (first run):** Updated 22 row(s). Artefact: `docs/BACKFILL_CULTURE_HEADERS_20260130.csv`.
- **Idempotency (second run):** Backfill run again (dry-run): Target rows: 22. Would change: 0. (Rows already have correct header; script skips them.)

---

## 3. Example before/after text for one culture_fact

**Before (headerless):**
```
Why the Scottish thistle became a national symbol

The thistle was adopted after Norse invaders stepped on thistles and cried out, alerting Scots.
```

**After (with header):**
```
UNDERSTANDING SCOTLAND

Why the Scottish thistle became a national symbol

The thistle was adopted after Norse invaders stepped on thistles and cried out, alerting Scots.
```

Rules applied: header UPPERCASE (A1); two newlines between header and title (A3); one newline between title and body; normalisation (A4).

---

## 4. Parity proof output

**Command:** `PYTHONPATH=<project> python3 scripts/prove_preview_publish_parity.py --ids 21089,21086`

**Output:**
```
Facebook Preview/Publish Parity Proof
Run at: 2026-01-30T10:45:22.042729Z

post_id=21089 role=CULTURE content_type=culture_fact -> PASS

post_id=21086 role=HERITAGE content_type=heritage_fact -> PASS

Report written to docs/PARITY_PROOF_FACEBOOK_20260130.txt
```

Expected: PASS. Result: PASS for both culture_fact and heritage_fact.

---

## 5. QA acceptance checklist

| Item | Status |
|------|--------|
| **QA-1. Publish formatting** | culture_fact and heritage_fact posts begin with UNDERSTANDING SCOTLAND or SCOTTISH HERITAGE; exactly one blank line after header. (Verified via formatter output; live publish can be confirmed by publishing one of each.) |
| **QA-2. Preview parity** | Facebook preview text equals publish text; parity script PASS for IDs 21089 (culture_fact), 21086 (heritage_fact). |
| **QA-3. Retroactive queue correction** | Backfill run with --apply; 22 queued culture/heritage rows updated with headers; published rows not touched (target statuses: draft, pending, ready, approved only). |
| **QA-4. Non-regression** | message, authority_short, product, language, depth_long unchanged (formatter returns content unchanged when content_type not in culture_fact/heritage_fact). Saturday product behaviour unaffected. |
| **QA-5. Idempotency** | Re-run backfill (dry-run): 0 rows would be updated (all 22 already have correct header; script skips them). |

---

## 6. Safety constraints (A5) — confirmed

- No emojis, hashtags, CTAs, URLs, rewriting, or punctuation changes in the formatter.
- No fallback headers; empty/placeholder content remains gate for executor (no publish).
- Creators unchanged; headers are publish-time only (D2).
