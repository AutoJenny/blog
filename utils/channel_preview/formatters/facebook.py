"""
Facebook channel preview formatter.

Reuses the same text formatting logic as the Facebook publish path
(`utils.platform_publishers.format_message_for_facebook`) so that
preview and publish remain in sync.
"""

from typing import Any, Dict

from utils.platform_publishers import format_message_for_facebook


class FacebookFormatter:
    """
    Format posting_queue post data for Facebook preview.
    """

    def format(
        self,
        post_data: Dict[str, Any],
        mode: str = "preview",
        variant: str = "full",
    ) -> Dict[str, Any]:
        """
        Return formatted display text and metadata for preview.
        """
        raw_text = (post_data.get("generated_content") or "").strip()

        # Reuse publish formatting logic for line breaks etc.
        display_text = format_message_for_facebook(raw_text) if raw_text else ""

        char_count = len(display_text)

        return {
            "display_text": display_text,
            "char_count": char_count,
            "warnings": [],
            "meta": {
                "role": post_data.get("role"),
                "status": post_data.get("status"),
                "content_type": post_data.get("content_type"),
                "platform": post_data.get("platform"),
            },
        }

