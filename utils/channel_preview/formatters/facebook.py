"""
Facebook channel preview formatter.

Reuses the same text formatting logic as the Facebook publish path
(culture/heritage headers then utils.platform_publishers.format_message_for_facebook)
so that preview and publish remain in sync. For product posts, returns
display_text (caption, price stripped per policy) plus product_image_url,
product_name, product_link for template to render image + caption. Emojis preserved (UTF-8).
"""

from typing import Any, Dict

from utils.platform_publishers import format_message_for_facebook
from utils.formatting.culture_headers import apply_culture_or_heritage_header
from utils.formatting.product_caption import strip_price_from_caption


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
        For culture/heritage: header + title + body (same as publish).
        For product: caption as display_text (price stripped per policy); product_image_url,
        product_name, product_link in meta for template to show image + caption.
        """
        content_type = (post_data.get("content_type") or "").strip()

        # Text-only path (publish uses generated_content): message, culture_fact, heritage_fact
        if content_type in ("message", "culture_fact", "heritage_fact"):
            raw_text = (post_data.get("generated_content") or "").strip()
            content = apply_culture_or_heritage_header(content_type, raw_text) if raw_text else ""
            display_text = format_message_for_facebook(content) if content else ""
            char_count = len(display_text)
            return {
                "display_text": display_text,
                "char_count": char_count,
                "warnings": [],
                "meta": {
                    "role": post_data.get("role"),
                    "status": post_data.get("status"),
                    "content_type": content_type,
                    "platform": post_data.get("platform"),
                    "category": post_data.get("category"),
                },
            }

        # Image-post path (publish uses generated_caption): product, weekly_*, etc.
        if content_type == "product":
            # Product: strip price per policy; pass product meta for template
            caption = (post_data.get("generated_caption") or "").strip()
            caption_no_price = strip_price_from_caption(caption) if caption else ""
            display_text = format_message_for_facebook(caption_no_price) if caption_no_price else ""
            char_count = len(display_text)
            image_path = post_data.get("image_path") or ""
            product_image_url = (
                image_path
                if image_path and (image_path.startswith("http://") or image_path.startswith("https://"))
                else (post_data.get("product_image_url") or "")
            )
            return {
                "display_text": display_text,
                "char_count": char_count,
                "warnings": [],
                "meta": {
                    "role": post_data.get("role"),
                    "status": post_data.get("status"),
                    "content_type": content_type,
                    "platform": post_data.get("platform"),
                    "category": post_data.get("category"),
                    "product_image_url": product_image_url or None,
                    "product_name": post_data.get("product_name"),
                    "product_link": post_data.get("product_link"),
                },
            }

        # Other image-post types (weekly_phrase, weekly_word, weekly_insult, etc.): use caption as published
        caption = (post_data.get("generated_caption") or "").strip()
        display_text = format_message_for_facebook(caption) if caption else ""
        char_count = len(display_text)
        return {
            "display_text": display_text,
            "char_count": char_count,
            "warnings": [],
            "meta": {
                "role": post_data.get("role"),
                "status": post_data.get("status"),
                "content_type": content_type,
                "platform": post_data.get("platform"),
                "category": post_data.get("category"),
            },
        }

