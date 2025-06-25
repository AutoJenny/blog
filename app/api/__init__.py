from flask import Blueprint
from . import workflow

bp = Blueprint('api', __name__, url_prefix='/api')

def init_app(app):
    from . import workflow
    from .workflow import steps
    
    bp.register_blueprint(workflow.bp)
    bp.register_blueprint(steps.bp, url_prefix='/workflow')
    
    app.register_blueprint(bp) 