"""
Channel Preview Renderer

Minimal implementation of the Unified Channel Preview System renderer,
as described in `docs/UNIFIED_CHANNEL_PREVIEW_SYSTEM.md`.

Responsibilities (v1):
- Load post data from posting_queue
- Normalise preview input fields
- Produce simple HTML suitable for embedding in preview UIs

This implementation intentionally keeps formatting simple and does not yet
implement the full formatter registry described in the docs. It can be
extended incrementally without breaking the API surface.
"""

from typing import Any, Dict
import html

from config.database import db_manager
from .formatters.registry import get_formatter


class ChannelPreviewRenderer:
    """
    Render a channel-specific HTML preview for a posting_queue post.

    Method signature is aligned with the design doc:

        def render(self, post_id: int, channel: str,
                   mode: str = 'preview', variant: str = 'full') -> Dict[str, Any]:
    """

    VALID_CHANNELS = {"facebook", "instagram", "x", "twitter", "tiktok", "generic"}

    def render(
        self,
        post_id: int,
        channel: str,
        mode: str = "preview",
        variant: str = "full",
    ) -> Dict[str, Any]:
        channel_lower = (channel or "facebook").lower()
        if channel_lower == "twitter":
            # Treat "twitter" as alias for "x"
            channel_lower = "x"

        if channel_lower not in self.VALID_CHANNELS:
            return {
                "success": False,
                "error": "Invalid channel",
                "error_code": "INVALID_CHANNEL",
            }

        # Load basic post data from posting_queue
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    platform,
                    channel_type,
                    role,
                    content_type,
                    status,
                    generated_content,
                    scheduled_date,
                    scheduled_time,
                    rota_year,
                    rota_week,
                    topic_id,
                    source_page_id,
                    angle_id
                FROM posting_queue
                WHERE id = %s
                """,
                (post_id,),
            )
            row = cursor.fetchone()

        if not row:
            return {
                "success": False,
                "error": "Post not found",
                "error_code": "POST_NOT_FOUND",
            }

        # Normalise into a simple dict
        post_data: Dict[str, Any] = dict(row)

        # Run channel formatter (preview and publish must share formatting rules).
        formatter = get_formatter(channel_lower)
        fmt_result = formatter.format(post_data, mode=mode, variant=variant)

        display_text = fmt_result.get("display_text", "")
        char_count = fmt_result.get("char_count", len(display_text))
        warnings = fmt_result.get("warnings", [])
        meta = fmt_result.get("meta", {}) or {}

        # Merge in scheduling + linkage metadata
        meta.update(
            {
                "scheduled_date": post_data.get("scheduled_date"),
                "scheduled_time": post_data.get("scheduled_time"),
                "rota_year": post_data.get("rota_year"),
                "rota_week": post_data.get("rota_week"),
                "topic_id": post_data.get("topic_id"),
                "source_page_id": post_data.get("source_page_id"),
                "angle_id": post_data.get("angle_id"),
                "char_count": char_count,
            }
        )

        # Escape for HTML; newlines become <br>
        escaped_text = html.escape(display_text).replace("\n", "<br>")

        role = post_data.get("role") or ""
        status = post_data.get("status") or ""

        # HTML wrapper; actual channel styling comes from the template in Phase 4.
        html_output = f"""
<div class="channel-preview channel-preview-{html.escape(channel_lower)}">
  <div class="channel-preview-meta">
    <span class="channel-preview-role">{html.escape(str(role))}</span>
    <span class="channel-preview-status">{html.escape(str(status))}</span>
    <span class="channel-preview-char-count">{char_count} chars</span>
  </div>
  <div class="channel-preview-body">
    {escaped_text or '<span class="channel-preview-empty">No preview text</span>'}
  </div>
</div>
""".strip()

        return {
            "success": True,
            "post_id": post_id,
            "channel": channel_lower,
            "mode": mode,
            "variant": variant,
            "html": html_output,
            "meta": meta,
            "warnings": warnings,
        }

