from flask import Blueprint, render_template

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
def index():
    return render_template('settings/index.html')

@settings_bp.route('/workflow_field_mapping')
def workflow_field_mapping():
    return render_template('settings/workflow_field_mapping.html')

@settings_bp.route('/workflow_prompts', methods=['GET', 'POST'])
def workflow_prompts():
    return render_template('settings/workflow_prompts.html')

@settings_bp.route('/workflow_prompts_json', methods=['GET', 'POST'])
def workflow_prompts_json():
    return render_template('settings/workflow_prompts_json.html')

@settings_bp.route('/planning_steps')
def planning_steps():
    return render_template('settings/planning_steps.html')

@settings_bp.route('/planning_steps_json', methods=['GET', 'POST'])
def planning_steps_json():
    return render_template('settings/planning_steps_json.html') 