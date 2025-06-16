from flask import render_template
from datetime import datetime
from . import bp

@bp.route('/db/')
def db_index():
    return render_template('db/index.html', year=datetime.now().year)

@bp.route('/db/raw')
def db_raw():
    return render_template('db/raw.html', year=datetime.now().year) 