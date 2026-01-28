"""
Prove preview/publish parity for Facebook formatting.

Compares the output of:
- utils.platform_publishers.format_message_for_facebook()
- utils.channel_preview.formatters.facebook.FacebookFormatter

for a set of posting_queue IDs, and writes a proof report to docs/.
"""

import argparse
from datetime import datetime
from typing import List, Tuple

from config.database import db_manager
from utils.platform_publishers import format_message_for_facebook
from utils.channel_preview.formatters.facebook import FacebookFormatter


def fetch_post(post_id: int) -> dict:
    with db_manager.get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, platform, role, content_type, generated_content
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


def prove_for_ids(ids: List[int]) -> str:
    formatter = FacebookFormatter()
    lines: List[str] = []
    lines.append("Facebook Preview/Publish Parity Proof")
    lines.append(f"Run at: {datetime.utcnow().isoformat()}Z")
    lines.append("")

    for post_id in ids:
        post = fetch_post(post_id)
        if not post:
            lines.append(f"post_id={post_id} -> FAIL (not found)")
            lines.append("")
            continue

        role = post.get("role")
        content_type = post.get("content_type")
        raw = (post.get("generated_content") or "").strip()

        publish_text = format_message_for_facebook(raw) if raw else ""

        preview_result = formatter.format(post, mode="preview", variant="full")
        preview_text = preview_result.get("display_text", "")

        same = publish_text == preview_text
        status = "PASS" if same else "FAIL"

        lines.append(f"post_id={post_id} role={role} content_type={content_type} -> {status}")

        if not same:
            idx, a_win, b_win = first_diff(publish_text, preview_text)
            lines.append(f"  First differing index: {idx}")
            lines.append(f"  publish window: {repr(a_win)}")
            lines.append(f"  preview window: {repr(b_win)}")

        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prove Facebook preview/publish parity.")
    parser.add_argument(
        "--ids",
        required=True,
        help="Comma-separated posting_queue IDs (e.g. 15505,123,456)",
    )
    args = parser.parse_args()

    ids = [int(x.strip()) for x in args.ids.split(",") if x.strip()]

    report = prove_for_ids(ids)

    today = datetime.utcnow().strftime("%Y%m%d")
    path = f"docs/PARITY_PROOF_FACEBOOK_{today}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    print(f"\nReport written to {path}")


if __name__ == "__main__":
    main()

