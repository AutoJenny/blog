"""
Generic channel preview formatter.

Passes text through with minimal normalisation. Used for channels that
do not yet have bespoke formatting rules.
"""

from typing import Any, Dict


class GenericFormatter:
    """
    Minimal formatter implementation for generic preview.
    """

    def format(
        self,
        post_data: Dict[str, Any],
        mode: str = "preview",
        variant: str = "full",
    ) -> Dict[str, Any]:
        text = (post_data.get("generated_content") or "").strip()
        char_count = len(text)
        return {
            "display_text": text,
            "char_count": char_count,
            "warnings": [],
            "meta": {
                "role": post_data.get("role"),
                "status": post_data.get("status"),
                "content_type": post_data.get("content_type"),
                "platform": post_data.get("platform"),
            },
        }

