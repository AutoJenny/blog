from flask import render_template
from datetime import datetime
from . import bp

@bp.route('/')
def index():
    return render_template('main/modern_index.html', year=datetime.now().year)

@bp.route('/test-core')
def test_core():
    return render_template('test_core.html', year=datetime.now().year) 