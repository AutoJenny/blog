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
import json

from config.database import db_manager
from .formatters.registry import get_formatter


def _fallback_html(channel: str, display_text: str, role: str, status: str, char_count: int) -> str:
    """Inline HTML when no channel template is used (e.g. non-Facebook)."""
    escaped_text = html.escape(display_text or "").replace("\n", "<br>")
    return f"""
<div class="channel-preview channel-preview-{html.escape(channel)}">
  <div class="channel-preview-meta">
    <span class="channel-preview-role">{html.escape(role)}</span>
    <span class="channel-preview-status">{html.escape(status)}</span>
    <span class="channel-preview-char-count">{char_count} chars</span>
  </div>
  <div class="channel-preview-body">
    {escaped_text or '<span class="channel-preview-empty">No preview text</span>'}
  </div>
</div>
""".strip()


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

        # Load basic post data from posting_queue (incl. validation_report_json for provenance/warnings)
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
                    angle_id,
                    validation_report_json
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

        # Merge in scheduling + linkage metadata (use ISO strings for JSON serializability)
        _date = post_data.get("scheduled_date")
        _time = post_data.get("scheduled_time")
        meta.update(
            {
                "scheduled_date": _date.isoformat() if hasattr(_date, "isoformat") else _date,
                "scheduled_time": _time.isoformat() if hasattr(_time, "isoformat") else str(_time) if _time is not None else None,
                "rota_year": post_data.get("rota_year"),
                "rota_week": post_data.get("rota_week"),
                "topic_id": post_data.get("topic_id"),
                "source_page_id": post_data.get("source_page_id"),
                "angle_id": post_data.get("angle_id"),
                "char_count": char_count,
            }
        )

        # Surface AUTHORITY_SHORT (and similar) provenance + validator output from validation_report_json
        try:
            raw_report = post_data.get("validation_report_json")
            if isinstance(raw_report, str):
                report = json.loads(raw_report) if raw_report else {}
            else:
                report = raw_report or {}
            source_used = report.get("source_used") or {}
            meta["source_type"] = source_used.get("type")
            meta["source_excerpt"] = report.get("source_excerpt")
            meta["validation_failed_rules"] = report.get("failed_rules") or []
        except (TypeError, ValueError):
            meta.setdefault("source_type", None)
            meta.setdefault("source_excerpt", None)
            meta.setdefault("validation_failed_rules", [])

        role = post_data.get("role") or ""
        status = post_data.get("status") or ""
        # Return data for template rendering (API/full-page will use channel template when available)
        return {
            "success": True,
            "post_id": post_id,
            "channel": channel_lower,
            "mode": mode,
            "variant": variant,
            "display_text": display_text,
            "meta": meta,
            "warnings": warnings,
            # Fallback inline HTML if caller does not use a channel template
            "html": _fallback_html(channel_lower, display_text, role, status, char_count),
        }

