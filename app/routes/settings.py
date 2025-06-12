import json
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
import os
from app.database import get_db_conn

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
def index():
    print('DEBUG: settings_bp index route called')
    return render_template('settings/index.html')

@settings_bp.route('/workflow_field_mapping')
def workflow_field_mapping():
    field_mappings = []
    stages = []
    substages = []
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT wfm.id, wfm.field_name, wfm.stage_id, wfm.substage_id, wfm.order_index
                FROM workflow_field_mapping wfm
                ORDER BY wfm.order_index ASC, wfm.field_name ASC
            ''')
            field_mappings = cur.fetchall()
            cur.execute('SELECT id, name FROM workflow_stage_entity ORDER BY stage_order')
            stages = cur.fetchall()
            cur.execute('SELECT id, stage_id, name FROM workflow_sub_stage_entity ORDER BY sub_stage_order')
            substages = cur.fetchall()
    return render_template('settings/workflow_field_mapping.html', field_mappings=field_mappings, stages=stages, substages=substages)

@settings_bp.route('/workflow_prompts', methods=['GET', 'POST'])
def workflow_prompts():
    prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'prompts')
    prompts = {}
    # Load all prompt files
    for filename in os.listdir(prompts_dir):
        if filename.endswith('.json'):
            with open(os.path.join(prompts_dir, filename), 'r') as file:
                prompt_data = json.load(file)
                key = os.path.splitext(filename)[0]
                prompts[key] = prompt_data

    if request.method == 'POST':
        # Reconstruct the prompts dict from the form
        new_prompts = {}
        for prompt_name, fields in prompts.items():
            new_prompts[prompt_name] = {}
            for field in fields:
                form_key = f'{prompt_name}__{field}'
                new_prompts[prompt_name][field] = request.form.get(form_key, '')
        # Save each prompt to its respective file
        for key, content in new_prompts.items():
            filename = f"{key}.json"
            filepath = os.path.join(prompts_dir, filename)
            with open(filepath, 'w') as file:
                json.dump(content, file, indent=2)
        flash('Prompts updated successfully!', 'success')
        return redirect(url_for('settings.workflow_prompts'))

    return render_template('settings/workflow_prompts.html', prompts=prompts)

@settings_bp.route('/workflow_prompts_json', methods=['GET', 'POST'])
def workflow_prompts_json():
    if request.method == 'POST':
        try:
            data = request.get_json()
            prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'prompts')
            
            # Save each prompt to its respective file
            for key, content in data.items():
                filename = f"{key}.json"
                filepath = os.path.join(prompts_dir, filename)
                with open(filepath, 'w') as file:
                    json.dump(content, file, indent=2)
            
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    try:
        prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'prompts')
        prompts = {}
        
        # Walk through the prompts directory
        for filename in os.listdir(prompts_dir):
            if filename.endswith('.json'):
                with open(os.path.join(prompts_dir, filename), 'r') as file:
                    prompt_data = json.load(file)
                    # Use the filename without extension as the key
                    key = os.path.splitext(filename)[0]
                    prompts[key] = prompt_data
                    
        return jsonify(prompts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500 