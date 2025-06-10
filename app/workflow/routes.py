from flask import render_template, request, jsonify, current_app
from app.database import get_db_conn
from app.workflow.navigation import navigator
from app.workflow import bp

@bp.route('/')
def index():
    """Show the workflow navigation."""
    # Ensure navigation data is loaded
    navigator.load_navigation()
    nav_context = navigator.get_navigation_context()
    return render_template('workflow/index.html', **nav_context)

@bp.route('/stage/<int:stage_id>')
def stage(stage_id):
    """Show a specific workflow stage."""
    navigator.load_navigation()
    nav_context = navigator.get_navigation_context()
    stage = next((s for s in navigator.stages if s['id'] == stage_id), None)
    if not stage:
        return "Stage not found", 404
    return render_template('workflow/stage.html', stage=stage, **nav_context)

@bp.route('/substage/<int:substage_id>')
def substage(substage_id):
    """Show a specific workflow substage."""
    navigator.load_navigation()
    nav_context = navigator.get_navigation_context()
    substage = next((s for s in navigator.substages if s['id'] == substage_id), None)
    if not substage:
        return "Substage not found", 404
    return render_template('workflow/substage.html', substage=substage, **nav_context)

@bp.route('/step/<int:step_id>')
def step(step_id):
    """Show a specific workflow step."""
    navigator.load_navigation()
    nav_context = navigator.get_navigation_context()
    step = next((s for s in navigator.steps if s['id'] == step_id), None)
    if not step:
        return "Step not found", 404
    return render_template('workflow/step.html', step=step, **nav_context)
