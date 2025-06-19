from flask import Blueprint

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
def index():
    return "Settings index - stub"

@settings_bp.route('/workflow_field_mapping')
def workflow_field_mapping():
    return "Workflow field mapping - stub"

@settings_bp.route('/workflow_prompts', methods=['GET', 'POST'])
def workflow_prompts():
    return "Workflow prompts - stub"

@settings_bp.route('/workflow_prompts_json', methods=['GET', 'POST'])
def workflow_prompts_json():
    return "Workflow prompts JSON - stub"

@settings_bp.route('/planning_steps')
def planning_steps():
    return "Planning steps - stub"

@settings_bp.route('/planning_steps_json', methods=['GET', 'POST'])
def planning_steps_json():
    return "Planning steps JSON - stub" 