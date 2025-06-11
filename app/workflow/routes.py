from flask import render_template, redirect, url_for, abort
from app.workflow import workflow
from .navigation import navigator

@workflow.route('/')
def index():
    navigator.load_navigation()
    stages = navigator.stages
    return render_template('workflow/index.html', stages=stages)

@workflow.route('/<stage_name>/')
def stage(stage_name: str):
    navigator.load_navigation()
    stage = next((s for s in navigator.stages if s['name'] == stage_name), None)
    if not stage:
        abort(404, f"Stage '{stage_name}' not found.")
    substages = navigator.get_substages_for_stage(stage['id'])
    return render_template('workflow/stage.html', stage=stage, substages=substages)

@workflow.route('/<stage_name>/<substage_name>/')
def substage(stage_name: str, substage_name: str):
    navigator.load_navigation()
    stage = next((s for s in navigator.stages if s['name'] == stage_name), None)
    if not stage:
        abort(404, f"Stage '{stage_name}' not found.")
    substages = navigator.get_substages_for_stage(stage['id'])
    substage = next((s for s in substages if s['name'] == substage_name), None)
    if not substage:
        abort(404, f"Substage '{substage_name}' not found in stage '{stage_name}'.")
    steps = navigator.get_steps_for_substage(substage['id'])
    if not steps:
        abort(404, f"No steps found for substage '{substage_name}'.")
    # Redirect to first step
    return redirect(url_for('workflow.step', stage_name=stage_name, substage_name=substage_name, step_name=steps[0]['name']))

@workflow.route('/<stage_name>/<substage_name>/<step_name>/')
def step(stage_name: str, substage_name: str, step_name: str):
    navigator.load_navigation()
    stage = next((s for s in navigator.stages if s['name'] == stage_name), None)
    if not stage:
        abort(404, f"Stage '{stage_name}' not found.")
    substages = navigator.get_substages_for_stage(stage['id'])
    substage = next((s for s in substages if s['name'] == substage_name), None)
    if not substage:
        abort(404, f"Substage '{substage_name}' not found in stage '{stage_name}'.")
    steps = navigator.get_steps_for_substage(substage['id'])
    step = next((s for s in steps if s['name'] == step_name), None)
    if not step:
        abort(404, f"Step '{step_name}' not found in substage '{substage_name}'.")
    return render_template(f'workflow/steps/{step_name}.html', stage=stage, substage=substage, step=step) 