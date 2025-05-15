from flask import Blueprint, render_template

bp = Blueprint('preview', __name__, template_folder='../templates/preview')

@bp.route('/')
def landing():
    return render_template('preview/landing.html') 