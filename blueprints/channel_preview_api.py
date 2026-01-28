"""
Channel Preview API Blueprint

Implements the `/api/preview/post/<post_id>` endpoint described in
`docs/UNIFIED_CHANNEL_PREVIEW_SYSTEM.md`.

This wraps `ChannelPreviewRenderer` and returns JSON suitable for use by
frontend preview modals and tools.
"""

from flask import Blueprint, request, jsonify, render_template

from utils.channel_preview.preview_renderer import ChannelPreviewRenderer

bp = Blueprint("channel_preview_api", __name__, url_prefix="/api/preview")


@bp.route("/post/<int:post_id>", methods=["GET"])
def preview_post_api(post_id: int):
    """
    Preview API endpoint.

    GET /api/preview/post/<post_id>

    Query parameters:
        channel: facebook|instagram|x|tiktok|generic (default: facebook)
        mode: preview (default/only)
        variant: full|compact (default: full)
    """
    channel = request.args.get("channel", "facebook")
    mode = request.args.get("mode", "preview")
    variant = request.args.get("variant", "full")

    renderer = ChannelPreviewRenderer()
    result = renderer.render(post_id, channel, mode=mode, variant=variant)

    # Use canonical channel template for Facebook (source provenance + validator warnings)
    if result.get("success") and result.get("channel") == "facebook":
        result["html"] = render_template(
            "channel_previews/facebook_feed.html",
            display_text=result.get("display_text", ""),
            meta=result.get("meta", {}),
        )

    status_code = 200
    if not result.get("success"):
        error_code = result.get("error_code")
        if error_code == "POST_NOT_FOUND":
            status_code = 404
        elif error_code == "INVALID_CHANNEL":
            status_code = 400
        else:
            status_code = 500

    return jsonify(result), status_code

