"""
Preview Views

Full-page channel preview routes (non-API) for human-readable previews.
Reuses ChannelPreviewRenderer and channel preview templates.
"""

from flask import Blueprint, request, render_template
import logging
from utils.channel_preview.preview_renderer import ChannelPreviewRenderer

bp = Blueprint('preview_views', __name__, url_prefix='/preview')
logger = logging.getLogger(__name__)


@bp.route('/post/<int:post_id>', methods=['GET'])
def preview_post_page(post_id: int):
    """
    Full-page preview for a posting_queue post.

    Query params:
        channel: facebook|instagram|x|tiktok|generic (default: facebook)

    Renders the same HTML used by the API preview inside a simple, high-contrast frame.
    """
    channel = request.args.get('channel', 'facebook')
    valid_channels = ['facebook', 'instagram', 'x', 'twitter', 'tiktok', 'generic']
    channel_lower = channel.lower()
    if channel_lower not in valid_channels:
        channel_lower = 'facebook'

    renderer = ChannelPreviewRenderer()
    result = renderer.render(post_id, channel_lower, mode='preview', variant='full')

    if not result.get('success'):
        # Render a simple error page rather than JSON
        error_message = result.get('error', 'Preview failed')
        error_code = result.get('error_code', 'PREVIEW_ERROR')
        return render_template(
            'preview/full_page_preview.html',
            html=f'<div class="preview-error">{error_message}</div>',
            post_id=post_id,
            channel=channel_lower,
            error=error_message,
            error_code=error_code
        ), 404 if error_code == 'POST_NOT_FOUND' else 500

    # Use the rendered HTML from the renderer
    html = result.get('html', '')

    # Compute a simple back URL (best-effort)
    back_url = request.referrer or '/planning/calendar'

    return render_template(
        'preview/full_page_preview.html',
        html=html,
        post_id=post_id,
        channel=channel_lower,
        back_url=back_url,
        error=None,
        error_code=None
    )

