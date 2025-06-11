from flask import render_template, request, jsonify, current_app, redirect, url_for
from app.database import get_db_conn
from app.workflow.navigation import navigator
from app.workflow import bp

@bp.route('/')
def index():
    """Show the workflow navigation."""
    # Ensure navigation data is loaded
    navigator.load_navigation()
    nav_context = navigator.get_navigation_context()
    current_app.logger.debug(f"Navigation context: {nav_context}")
    return render_template('workflow/index.html', **nav_context)

@bp.route('/<string:stage_name>/')
def stage_by_name(stage_name):
    """Show a specific workflow stage by name."""
    navigator.load_navigation()
    stage = next((s for s in navigator.stages if s['name'] == stage_name), None)
    if not stage:
        return "Stage not found", 404
    
    substages = navigator.get_substages_for_stage(stage['id'])
    nav_context = navigator.get_navigation_context(current_stage_id=stage['id'])
    current_app.logger.debug(f"Stage context: {stage}, Substages: {substages}")
    
    # Remove substages from nav_context to avoid duplicate
    nav_context.pop('substages', None)
    
    return render_template('workflow/stage.html', **nav_context)

@bp.route('/<string:stage_name>/<string:substage_name>/')
def substage_by_name(stage_name, substage_name):
    """Show a specific workflow substage by name."""
    navigator.load_navigation()
    stage = next((s for s in navigator.stages if s['name'] == stage_name), None)
    if not stage:
        return "Stage not found", 404
        
    substage = next((s for s in navigator.substages 
                    if s['stage_id'] == stage['id'] and s['name'] == substage_name), None)
    if not substage:
        return "Substage not found", 404
        
    steps = navigator.get_steps_for_substage(substage['id'])
    nav_context = navigator.get_navigation_context(
        current_stage_id=stage['id'],
        current_substage_id=substage['id']
    )
    current_app.logger.debug(f"Substage context: {substage}, Steps: {steps}")
    
    # Remove steps from nav_context to avoid duplicate
    nav_context.pop('steps', None)
    
    return render_template('workflow/substage.html',
                         stage=stage,
                         substage=substage,
                         steps=steps,
                         **nav_context)

@bp.route('/<string:stage_name>/<string:substage_name>/<string:step_name>/')
def step_by_name(stage_name, substage_name, step_name):
    """Show a specific workflow step by name."""
    navigator.load_navigation()
    stage = next((s for s in navigator.stages if s['name'] == stage_name), None)
    if not stage:
        return "Stage not found", 404
        
    substage = next((s for s in navigator.substages 
                    if s['stage_id'] == stage['id'] and s['name'] == substage_name), None)
    if not substage:
        return "Substage not found", 404
        
    step = next((s for s in navigator.steps 
                if s['sub_stage_id'] == substage['id'] and s['name'] == step_name), None)
    if not step:
        return "Step not found", 404
        
    nav_context = navigator.get_navigation_context(
        current_stage_id=stage['id'],
        current_substage_id=substage['id'],
        current_step_id=step['id']
    )
    current_app.logger.debug(f"Step context: {step}")
    
    return render_template('workflow/step.html',
                         stage=stage,
                         substage=substage,
                         step=step,
                         **nav_context)
