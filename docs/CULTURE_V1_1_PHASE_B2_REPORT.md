# CULTURE v1.1 — Phase B.2 Report (Publish + Preview for culture_fact)

**Status:** Phase B.2 implementation complete per instruction brief (2026-01-29)  
**Scope:** Facebook publish + preview for `content_type='culture_fact'` only. No scheduling, selection, execution infrastructure, or schema changes.

---

## 1. Implementation summary

| Component | File | Change |
|-----------|------|--------|
| Publish | `utils/platform_publishers.py` | `publish_to_facebook()` treats `culture_fact` like `message`: text-led feed post using `generated_content`, `format_message_for_facebook()`, `/feed` endpoint. No CTA, no hashtag injection. |
| Formatter | `utils/channel_preview/formatters/facebook.py` | `FacebookFormatter.format()` includes `meta.category` (from post_data). Same formatting as publish (`format_message_for_facebook`). No preview-only logic. |
| Renderer | `utils/channel_preview/preview_renderer.py` | SELECT includes `culture_library_id`. For `culture_fact` with `culture_library_id`, derive `category` from `culture_library` and add to post_data so meta has category. |
| Template | `templates/channel_previews/facebook_feed.html` | Optional small neutral label for `meta.category` (fact / symbol / place_name etc.). Does not affect publish output. |
| Parity script | `scripts/prove_preview_publish_parity.py` | Added `--output` and `--culture`; `--culture` writes to `docs/PARITY_PROOF_FACEBOOK_CULTURE_YYYYMMDD.txt`. |

---

## 2. Verification checklist (Phase B.2 “done”)

| Criterion | How to verify |
|-----------|----------------|
| **1. Publishing proof** | One `culture_fact` row with `status='ready'` publishes via `publish_to_facebook(queue_id)` (same path as message). Can be dry-run/logged if live posting disabled. |
| **2. Preview proof** | `/api/preview/post/<id>?channel=facebook` and `/preview/post/<id>?channel=facebook` render correctly for a culture_fact post (display_text from generated_content, optional category label). |
| **3. Parity proof** | Run: `python3 scripts/prove_preview_publish_parity.py --ids <culture_fact_id>,<authority_short_id>,<weekly_language_id> --culture`. Output: `docs/PARITY_PROOF_FACEBOOK_CULTURE_YYYYMMDD.txt`. Preview text === publish text (byte-for-byte) for all three. |
| **4. Non-regression** | No changes to execution scheduler, CULTURE generator/creator, or schema. |

---

## 3. Parity proof (mandatory)

- **Script:** `scripts/prove_preview_publish_parity.py`
- **Run for at least:** one culture_fact, one authority_short, one weekly_language (e.g. weekly_word).
- **Command:**  
  `python3 scripts/prove_preview_publish_parity.py --ids <culture_fact_id>,<authority_short_id>,<weekly_word_id> --culture`
- **Output:** `docs/PARITY_PROOF_FACEBOOK_CULTURE_YYYYMMDD.txt`
- **Condition:** Each listed post must show `PASS` (preview text === publish text byte-for-byte). Parity is a hard gate for Phase B.2 acceptance.

---

## 4. Definition of “done” (Phase B.2)

A culture_fact post that appears on Mon/Thu:

- Previews correctly via `/api/preview/post/<id>?channel=facebook` and `/preview/post/<id>?channel=facebook`.
- Publishes correctly to Facebook via `platform_publishers.publish_to_facebook(queue_id)`.
- Preview text is provably identical to publish text (parity proof).

No changes were made to scheduling, selection, or execution infrastructure.

---

## 5. Explicit non-scope (unchanged)

- Matrix logic, schedule API, generators/creators, culture library data  
- Execution scheduling logic, non-Facebook channels  
- Posting frequency or timing, schema  
- Instagram/X, image variants, editorial enhancements, analytics, additional CULTURE categories  

Stop. Do not proceed to those without a new brief.
