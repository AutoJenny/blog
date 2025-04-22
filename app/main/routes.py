from flask import render_template, current_app
from app.main import bp

@bp.route('/')
def index():
    current_app.logger.info('Home page accessed')
    return render_template('main/index.html', title='Home') 