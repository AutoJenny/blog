"""
Prove preview/publish parity for Facebook formatting.

Compares the output of:
- utils.platform_publishers.format_message_for_facebook()
- utils.channel_preview.formatters.facebook.FacebookFormatter

for a set of posting_queue IDs, and writes a proof report to docs/.

QA: Use --platform facebook --weeks N to test upcoming/recent posts.
Exit code: 0 if all parity checks PASS; 1 if any FAIL or formatting checks fail.
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

from config.database import db_manager
from utils.platform_publishers import format_message_for_facebook
from utils.channel_preview.formatters.facebook import FacebookFormatter
from utils.formatting.culture_headers import (
    apply_culture_or_heritage_header,
    normalise_text_whitespace,
)

from utils.formatting.product_caption import strip_price_from_caption

# Header strings for culture/heritage (must match culture_headers.py)
_EXPECTED_FIRST_LINE = {
    "culture_fact": "UNDERSTANDING SCOTLAND",
    "heritage_fact": "SCOTTISH HERITAGE",
}


def fetch_post(post_id: int) -> dict:
    with db_manager.get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, platform, role, content_type, generated_content, generated_caption
            FROM posting_queue
            WHERE id = %s
            """,
            (post_id,),
        )
        row = cursor.fetchone()
    return dict(row) if row else {}


def first_diff(a: str, b: str) -> Tuple[int, str, str]:
    """Return first differing index and short window from each string."""
    max_len = min(len(a), len(b))
    for i in range(max_len):
        if a[i] != b[i]:
            start = max(0, i - 20)
            end = i + 20
            return i, a[start:end], b[start:end]
    if len(a) != len(b):
        # Difference is length only
        return max_len, a[max_len : max_len + 40], b[max_len : max_len + 40]
    return -1, "", ""


def check_formatting(post: dict, lines: List[str]) -> bool:
    """
    Optional QA: for culture_fact/heritage_fact verify correct header and normalisation.
    Returns True if checks pass or content type not applicable.
    """
    content_type = (post.get("content_type") or "").strip()
    if content_type not in ("culture_fact", "heritage_fact"):
        return True
    raw = (post.get("generated_content") or "").strip()
    if not raw:
        return True
    first_line = next((ln.strip() for ln in raw.split("\n") if ln.strip()), "")
    expected = _EXPECTED_FIRST_LINE.get(content_type)
    if expected and first_line != expected:
        lines.append(f"  [FORMAT] culture/heritage missing header: first line {repr(first_line[:40])}")
        return False
    # No run of 3+ newlines, no trailing spaces on any line, at most one trailing newline
    normalised = normalise_text_whitespace(raw)
    if "\n\n\n" in normalised:
        lines.append("  [FORMAT] culture/heritage: run of 3+ newlines (should be collapsed to 2)")
        return False
    if any(line != line.rstrip() for line in raw.split("\n")):
        lines.append("  [FORMAT] culture/heritage: trailing spaces on line(s)")
        return False
    return True


def fetch_ids_facebook_weeks(weeks: int) -> List[int]:
    """Return posting_queue IDs for platform=facebook with scheduled_date in next N weeks."""
    with db_manager.get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id FROM posting_queue
            WHERE platform = 'facebook'
              AND scheduled_date >= CURRENT_DATE
              AND scheduled_date <= CURRENT_DATE + %s::integer
            ORDER BY scheduled_date, id
            """,
            (weeks * 7,),
        )
        return [r["id"] for r in cursor.fetchall()]


def prove_for_ids(ids: List[int], check_format: bool = False) -> Tuple[str, bool]:
    formatter = FacebookFormatter()
    lines: List[str] = []
    lines.append("Facebook Preview/Publish Parity Proof")
    lines.append(f"Run at: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    all_passed = True

    for post_id in ids:
        post = fetch_post(post_id)
        if not post:
            lines.append(f"post_id={post_id} -> FAIL (not found)")
            lines.append("")
            all_passed = False
            continue

        role = post.get("role")
        content_type = (post.get("content_type") or "").strip()

        if check_format and not check_formatting(post, lines):
            all_passed = False
            lines.append(f"post_id={post_id} role={role} content_type={content_type} -> FAIL (format)")
            lines.append("")
            continue

        # Align with publish path: text-only (message, culture_fact, heritage_fact) use generated_content; image-post use generated_caption
        if content_type in ("message", "culture_fact", "heritage_fact"):
            raw = (post.get("generated_content") or "").strip()
            content = apply_culture_or_heritage_header(content_type, raw)
            publish_text = format_message_for_facebook(content) if content else ""
        elif content_type == "product":
            caption = (post.get("generated_caption") or "").strip()
            caption_no_price = strip_price_from_caption(caption) if caption else ""
            publish_text = format_message_for_facebook(caption_no_price) if caption_no_price else ""
        else:
            # Other image-post types (weekly_*, etc.): publish uses generated_caption
            caption = (post.get("generated_caption") or "").strip()
            publish_text = format_message_for_facebook(caption) if caption else ""

        preview_result = formatter.format(post, mode="preview", variant="full")
        preview_text = preview_result.get("display_text", "")

        same = publish_text == preview_text
        status = "PASS" if same else "FAIL"
        if not same:
            all_passed = False

        lines.append(f"post_id={post_id} role={role} content_type={content_type} -> {status}")

        if not same:
            idx, a_win, b_win = first_diff(publish_text, preview_text)
            lines.append(f"  First differing index: {idx}")
            lines.append(f"  publish window: {repr(a_win)}")
            lines.append(f"  preview window: {repr(b_win)}")

        lines.append("")

    return "\n".join(lines), all_passed


def main() -> int:
    parser = argparse.ArgumentParser(description="Prove Facebook preview/publish parity.")
    parser.add_argument(
        "--ids",
        default=None,
        help="Comma-separated posting_queue IDs (e.g. 15505,123,456). Omit if using --platform facebook --weeks N.",
    )
    parser.add_argument(
        "--platform",
        default=None,
        choices=["facebook"],
        help="Platform to test (currently only facebook). Use with --weeks to fetch IDs from queue.",
    )
    parser.add_argument(
        "--weeks",
        type=int,
        default=None,
        metavar="N",
        help="Fetch IDs for posts scheduled in the next N weeks (requires --platform facebook).",
    )
    parser.add_argument(
        "--qa-format",
        action="store_true",
        help="Also run formatting QA: culture/heritage header present, newline collapse, no trailing spaces.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (default: docs/PARITY_PROOF_FACEBOOK_YYYYMMDD.txt)",
    )
    parser.add_argument(
        "--culture",
        action="store_true",
        help="Write to docs/PARITY_PROOF_FACEBOOK_CULTURE_YYYYMMDD.txt (Phase B.2 parity proof)",
    )
    parser.add_argument(
        "--heritage",
        action="store_true",
        help="Write to docs/PARITY_PROOF_FACEBOOK_HERITAGE_YYYYMMDD.txt (Phase H1 parity proof)",
    )
    args = parser.parse_args()

    if args.ids:
        ids = [int(x.strip()) for x in args.ids.split(",") if x.strip()]
    elif args.platform == "facebook" and args.weeks is not None and args.weeks > 0:
        ids = fetch_ids_facebook_weeks(args.weeks)
        if not ids:
            print("No Facebook posts found for the next {} weeks.".format(args.weeks))
            return 0
        print("Testing {} post(s) (platform=facebook, next {} weeks).".format(len(ids), args.weeks))
    else:
        parser.error("Provide either --ids or --platform facebook --weeks N")

    report, all_passed = prove_for_ids(ids, check_format=args.qa_format)

    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    if args.output:
        path = args.output
    elif args.culture:
        path = f"docs/PARITY_PROOF_FACEBOOK_CULTURE_{today}.txt"
    elif args.heritage:
        path = f"docs/PARITY_PROOF_FACEBOOK_HERITAGE_{today}.txt"
    else:
        path = f"docs/PARITY_PROOF_FACEBOOK_{today}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    print(f"\nReport written to {path}")
    if all_passed:
        print("PASS: all parity (and formatting) checks passed.")
    else:
        print("FAIL: one or more parity or formatting checks failed.")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

