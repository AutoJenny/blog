"""
KB Topic Rota Editor Blueprint

UI for editing the weekly topic rota schedule.
"""

from flask import Blueprint, render_template
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('kb_topic_rota_editor', __name__, url_prefix='/kb-topics')


@bp.route('/editor')
def editor():
    """Rota editor UI page."""
    return render_template('kb_topics/rota_editor.html', page_title='KB Topic Rota Editor')
