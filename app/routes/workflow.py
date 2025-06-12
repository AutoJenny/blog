from flask import Blueprint
from flask import jsonify
from flask import current_app
from flask import flash
from flask import redirect
from flask import url_for
from flask import render_template
from flask import request
import json
import os
from app.workflow.navigation import navigator
from app.database import get_db_conn

bp = Blueprint('workflow', __name__)

@bp.route('/<int:post_id>/writing/<substage>/<step>', methods=['GET'])
def writing_stage(post_id, substage, step):
    """Handle the writing stage of the workflow."""
    try:
        # Get the post
        post = get_post(post_id)
        if not post:
            flash('Post not found', 'error')
            return redirect(url_for('blog.index'))

        # Get the stage configuration
        stage_config = get_stage_config('writing')
        if not stage_config:
            flash('Writing stage configuration not found', 'error')
            return redirect(url_for('blog.index'))

        # Get the substage configuration
        substage_config = stage_config.get('substages', {}).get(substage)
        if not substage_config:
            flash(f'Substage {substage} not found in writing stage', 'error')
            return redirect(url_for('blog.index'))

        # Get the step configuration
        step_config = substage_config.get('steps', {}).get(step)
        if not step_config:
            flash(f'Step {step} not found in {substage} substage', 'error')
            return redirect(url_for('blog.index'))

        # Get the step ID
        step_id = get_workflow_step_id(post_id, 'writing', substage, step)

        # Get input values
        input_values = get_step_input_values(post_id, step_id) if step_id else {}

        # Get output values
        output_values = get_step_output_values(post_id, step_id) if step_id else {}

        # Get available fields for output mapping
        fields = get_available_fields()

        return render_template(
            'workflow/steps/writing_step.html',
            post=post,
            post_id=post_id,
            current_stage='writing',
            current_substage=substage,
            current_step=step,
            step_id=step_id,
            stage_config=stage_config,
            substage_config=substage_config,
            step_config=step_config,
            input_values=input_values,
            output_values=output_values,
            fields=fields
        )

    except Exception as e:
        current_app.logger.error(f"Error in writing stage: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('blog.index'))

@bp.route('/api/run_llm/', methods=['POST'])
def run_llm():
    """Run the LLM for the current step."""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        stage_name = data.get('stage_name')
        substage_name = data.get('substage_name')
        step_name = data.get('step_name')
        sections = data.get('sections', [])  # List of section IDs to process

        if not all([post_id, stage_name, substage_name, step_name]):
            return jsonify({'error': 'Missing required parameters'}), 400

        # Use navigator to get step_id (same as main step route)
        navigator.load_navigation()
        stage = next((s for s in navigator.stages if s['name'] == stage_name), None)
        if not stage:
            return jsonify({'error': f"Stage '{stage_name}' not found."}), 404
        substages = navigator.get_substages_for_stage(stage['id'])
        substage = next((s for s in substages if s['name'] == substage_name), None)
        if not substage:
            return jsonify({'error': f"Substage '{substage_name}' not found in stage '{stage_name}'."}), 404
        steps = navigator.get_steps_for_substage(substage['id'])
        step = next((s for s in steps if s['name'] == step_name), None)
        if not step:
            return jsonify({'error': f"Step '{step_name}' not found in substage '{substage_name}'."}), 404
        step_id = step['id']

        # Get the step configuration
        step_config = get_step_config(stage_name, substage_name, step_name)
        if not step_config:
            return jsonify({'error': 'Step configuration not found'}), 404

        # Get input values
        input_values = get_step_input_values(post_id, step_id)
        if not input_values:
            return jsonify({'error': 'No input values found'}), 404

        # Get the LLM configuration
        llm_config = step_config.get('settings', {}).get('llm')
        if not llm_config:
            return jsonify({'error': 'LLM configuration not found'}), 404

        # Process each selected section
        results = []
        for section_id in sections:
            # Get section data
            section_data = get_section_data(post_id, section_id)
            if not section_data:
                continue

            # Prepare the prompt with section-specific data
            prompt = prepare_section_prompt(step_config, input_values, section_data)

            # Run the LLM
            response = run_llm_request(llm_config, prompt)
            if response:
                # Save the response
                save_section_response(post_id, section_id, response)
                results.append({
                    'section_id': section_id,
                    'status': 'success',
                    'response': response
                })

        return jsonify({
            'success': True,
            'results': results
        })

    except Exception as e:
        current_app.logger.error(f"Error running LLM: {str(e)}")
        return jsonify({'error': str(e)}), 500

def prepare_section_prompt(step_config, input_values, section_data):
    """Prepare the prompt for section-specific processing."""
    # Get the base prompt template
    prompt_template = step_config.get('settings', {}).get('llm', {}).get('task_prompt')
    if not prompt_template:
        return None

    # Replace placeholders with actual values
    prompt = prompt_template
    for key, value in input_values.items():
        prompt = prompt.replace(f'{{{key}}}', str(value))

    # Add section-specific data
    prompt = prompt.replace('{section_title}', section_data.get('title', ''))
    prompt = prompt.replace('{section_description}', section_data.get('description', ''))
    prompt = prompt.replace('{section_content}', section_data.get('content', ''))

    return prompt

def get_section_data(post_id, section_id):
    """Get section data from the database."""
    try:
        # Get the outline
        outline = get_post_outline(post_id)
        if not outline:
            return None

        # Find the section
        for section in outline.get('sections', []):
            if section.get('id') == section_id:
                return section

        return None

    except Exception as e:
        current_app.logger.error(f"Error getting section data: {str(e)}")
        return None

def save_section_response(post_id, section_id, response):
    """Save the LLM response for a section."""
    try:
        # Get the outline
        outline = get_post_outline(post_id)
        if not outline:
            return False

        # Find and update the section
        for section in outline.get('sections', []):
            if section.get('id') == section_id:
                section['content'] = response
                section['status'] = 'completed'
                break

        # Save the updated outline
        save_post_outline(post_id, outline)
        return True

    except Exception as e:
        current_app.logger.error(f"Error saving section response: {str(e)}")
        return False

def get_post_outline(post_id):
    """Get the post's outline from either post_development or post_section tables."""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # First try to get from post_development
                cur.execute("SELECT outline FROM post_development WHERE post_id = %s", (post_id,))
                result = cur.fetchone()
                if result and result['outline']:
                    return result['outline']
                
                # If not found in post_development, get from post_section
                cur.execute("""
                    SELECT section_heading as title, 
                           section_description as description, 
                           ideas_to_include as contents
                    FROM post_section 
                    WHERE post_id = %s 
                    ORDER BY section_order
                """, (post_id,))
                sections = cur.fetchall()
                if sections:
                    return {
                        'sections': [
                            {
                                'id': i + 1,
                                'title': section['title'],
                                'description': section['description'],
                                'contents': json.loads(section['contents']) if section['contents'] else []
                            }
                            for i, section in enumerate(sections)
                        ]
                    }
                return None
    except Exception as e:
        current_app.logger.error(f"Error getting post outline: {str(e)}")
        return None

def get_step_config(stage_name, substage_name, step_name):
    """Load step configuration from JSON file."""
    try:
        config_path = os.path.join(current_app.root_path, 'workflow', 'config', f'{stage_name}_steps.json')
        if not os.path.exists(config_path):
            return None
            
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        return config.get(stage_name, {}).get(substage_name, {}).get(step_name)
    except Exception as e:
        current_app.logger.error(f"Error loading step config: {str(e)}")
        return None

def get_step_input_values(post_id, step_id):
    """Fetch input values for a step from the database."""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Get the step configuration
                cur.execute("SELECT name, sub_stage_id FROM workflow_step_entity WHERE id = %s", (step_id,))
                step_result = cur.fetchone()
                if not step_result:
                    return {}
                step_name = step_result['name']
                sub_stage_id = step_result['sub_stage_id']

                # Get the substage and stage names
                cur.execute("SELECT name, stage_id FROM workflow_sub_stage_entity WHERE id = %s", (sub_stage_id,))
                substage_result = cur.fetchone()
                if not substage_result:
                    return {}
                substage_name = substage_result['name']
                stage_id = substage_result['stage_id']

                cur.execute("SELECT name FROM workflow_stage_entity WHERE id = %s", (stage_id,))
                stage_result = cur.fetchone()
                if not stage_result:
                    return {}
                stage_name = stage_result['name']

                # Load step configuration
                step_config = get_step_config(stage_name, substage_name, step_name)
                if not step_config or 'inputs' not in step_config:
                    return {}

                input_values = {}
                for input_id, input_config in step_config['inputs'].items():
                    db_field = input_config.get('db_field')
                    db_table = input_config.get('db_table')
                    if db_field and db_table:
                        cur.execute(f"SELECT {db_field} FROM {db_table} WHERE post_id = %s", (post_id,))
                        result = cur.fetchone()
                        if result and db_field in result and result[db_field] is not None:
                            input_values[input_id] = result[db_field]
                return input_values
    except Exception as e:
        current_app.logger.error(f"Error getting step input values: {str(e)}")
        return {}

def get_step_output_values(post_id, step_id):
    """Fetch output values for a step from the database."""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Get the step configuration
                cur.execute("SELECT name, sub_stage_id FROM workflow_step_entity WHERE id = %s", (step_id,))
                step_result = cur.fetchone()
                if not step_result:
                    return {}
                step_name = step_result['name']
                sub_stage_id = step_result['sub_stage_id']

                # Get the substage and stage names
                cur.execute("SELECT name, stage_id FROM workflow_sub_stage_entity WHERE id = %s", (sub_stage_id,))
                substage_result = cur.fetchone()
                if not substage_result:
                    return {}
                substage_name = substage_result['name']
                stage_id = substage_result['stage_id']

                cur.execute("SELECT name FROM workflow_stage_entity WHERE id = %s", (stage_id,))
                stage_result = cur.fetchone()
                if not stage_result:
                    return {}
                stage_name = stage_result['name']

                # Load step configuration
                step_config = get_step_config(stage_name, substage_name, step_name)
                if not step_config or 'outputs' not in step_config:
                    return {}

                output_values = {}
                for output_id, output_config in step_config['outputs'].items():
                    db_field = output_config.get('db_field')
                    db_table = output_config.get('db_table')
                    if db_field and db_table:
                        cur.execute(f"SELECT {db_field} FROM {db_table} WHERE post_id = %s", (post_id,))
                        result = cur.fetchone()
                        if result and db_field in result and result[db_field] is not None:
                            output_values[output_id] = result[db_field]
                return output_values
    except Exception as e:
        current_app.logger.error(f"Error getting step output values: {str(e)}")
        return {}

def get_available_fields():
    """Fetch available fields for output mapping."""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'post_development'
                    AND column_name NOT IN ('id', 'outline')
                """)
                fields = [row[0] for row in cur.fetchall()]
                return fields
    except Exception as e:
        current_app.logger.error(f"Error getting available fields: {str(e)}")
        return []

@bp.route('/api/sections/', methods=['POST'])
def get_sections():
    """Get or save sections for a post, stage, substage, and step."""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        stage_name = data.get('stage_name')
        substage_name = data.get('substage_name')
        step_name = data.get('step_name')

        if not all([post_id, stage_name, substage_name, step_name]):
            return jsonify({'error': 'Missing required parameters'}), 400

        # Use navigator to get step_id (same as main step route)
        navigator.load_navigation()
        stage = next((s for s in navigator.stages if s['name'] == stage_name), None)
        if not stage:
            return jsonify({'error': f"Stage '{stage_name}' not found."}), 404
        substages = navigator.get_substages_for_stage(stage['id'])
        substage = next((s for s in substages if s['name'] == substage_name), None)
        if not substage:
            return jsonify({'error': f"Substage '{substage_name}' not found in stage '{stage_name}'."}), 404
        steps = navigator.get_steps_for_substage(substage['id'])
        step = next((s for s in steps if s['name'] == step_name), None)
        if not step:
            return jsonify({'error': f"Step '{step_name}' not found in substage '{substage_name}'."}), 404
        step_id = step['id']

        # Get the step configuration
        step_config = get_step_config(stage_name, substage_name, step_name)
        if not step_config:
            return jsonify({'error': 'Step configuration not found'}), 404

        # If sections are provided in the request, save them
        if 'sections' in data:
            sections = data['sections']
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    # Delete existing sections
                    cur.execute("DELETE FROM post_section WHERE post_id = %s", (post_id,))
                    
                    # Insert new sections
                    for i, section in enumerate(sections):
                        cur.execute("""
                            INSERT INTO post_section (post_id, section_heading, section_description, ideas_to_include, section_order)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (
                            post_id,
                            section.get('title', ''),
                            section.get('description', ''),
                            json.dumps(section.get('content', '')),
                            i
                        ))
                    conn.commit()
            return jsonify({'success': True})

        # Otherwise, get sections from the database
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, section_heading as title, section_description as description, ideas_to_include as content
                    FROM post_section
                    WHERE post_id = %s
                    ORDER BY section_order
                """, (post_id,))
                sections = [dict(row) for row in cur.fetchall()]

        return jsonify({
            'success': True,
            'sections': sections
        })

    except Exception as e:
        current_app.logger.error(f"Error handling sections: {str(e)}")
        return jsonify({'error': str(e)}), 500 