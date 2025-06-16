from flask import Blueprint, render_template
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/test-core')
def test_core():
    return render_template('test_core.html', year=datetime.now().year) 