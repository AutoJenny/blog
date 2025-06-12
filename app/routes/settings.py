import json
from flask import Blueprint, render_template, jsonify

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
def index():
    return render_template('settings/index.html')

@settings_bp.route('/settings/workflow_field_mapping')
def workflow_field_mapping():
    return render_template('settings/workflow_field_mapping.html')

@settings_bp.route('/settings/workflow_prompts')
def workflow_prompts():
    return render_template('settings/workflow_prompts.html')

@settings_bp.route('/settings/workflow_prompts_json')
def workflow_prompts_json():
    try:
        with open('path/to/your/prompts.json', 'r') as file:
            prompts = json.load(file)
        return jsonify(prompts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500 