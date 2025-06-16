from flask import render_template
from datetime import datetime
from . import bp

@bp.route('/settings')
def settings():
    return render_template('settings/settings.html', year=datetime.now().year) 