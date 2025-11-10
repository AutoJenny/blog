"""
Image Model Configuration API Endpoints
API routes for model selection and configuration
"""

from flask import Blueprint, jsonify, request
from config.database import db_manager
import logging
import json

logger = logging.getLogger(__name__)


# Standalone functions that can be imported directly
def imaging_model_selection_handler():
    """Get or save model selection configuration (per-post persistent)"""
    try:
        if request.method == 'GET':
            # Prefer per-post selection from post_development; fallback to ui_user_preferences
            post_id = request.args.get('post_id', type=int)
            with db_manager.get_cursor() as cursor:
                if post_id:
                    cursor.execute(
                        """
                        SELECT imaging_model_selection, imaging_model_parameters 
                        FROM post_development 
                        WHERE post_id = %s
                        """,
                        (post_id,)
                    )
                    row = cursor.fetchone()
                    if row and row.get('imaging_model_selection'):
                        parameters = {}
                        if row.get('imaging_model_parameters'):
                            try:
                                parameters = json.loads(row['imaging_model_parameters'])
                            except (json.JSONDecodeError, TypeError):
                                parameters = {}
                        return jsonify({'success': True, 'model': row['imaging_model_selection'], 'parameters': parameters})

                # Fallback to global preference
                cursor.execute(
                    """
                    SELECT preference_value FROM ui_user_preferences 
                    WHERE preference_key = 'imaging_model_selection'
                    """
                )
                pref = cursor.fetchone()
                if pref:
                    config = json.loads(pref['preference_value'])
                    return jsonify({'success': True, 'model': config.get('model', 'sdxl-lora'), 'parameters': config.get('parameters', {})})

                # Default
                return jsonify({'success': True, 'model': 'sdxl-lora', 'parameters': {}})
        
        elif request.method == 'POST':
            # Save per-post selection to post_development; also update ui_user_preferences for global default
            data = request.get_json()
            model = data.get('model', 'sdxl-lora')
            parameters = data.get('parameters', {})
            post_id = data.get('post_id')

            with db_manager.get_cursor() as cursor:
                if post_id:
                    # Update per-post selection
                    parameters_json = json.dumps(parameters) if parameters else None
                    cursor.execute(
                        """
                        UPDATE post_development
                        SET imaging_model_selection = %s, imaging_model_parameters = %s, updated_at = NOW()
                        WHERE post_id = %s
                        """,
                        (model, parameters_json, post_id)
                    )
                    # If no row updated, attempt insert minimal row (best-effort)
                    if cursor.rowcount == 0:
                        try:
                            cursor.execute(
                                """
                                INSERT INTO post_development (post_id, imaging_model_selection, imaging_model_parameters, created_at, updated_at)
                                VALUES (%s, %s, %s, NOW(), NOW())
                                """,
                                (post_id, model, parameters_json)
                            )
                        except Exception as _ignore:
                            logger.warning(f"Could not insert post_development for post_id={post_id}: {_ignore}")

                # Also update global preference for convenience
                config_data = {'model': model, 'parameters': parameters}
                cursor.execute(
                    """
                    INSERT INTO ui_user_preferences (user_id, preference_key, preference_value, preference_type, category, is_global)
                    VALUES (1, 'imaging_model_selection', %s, 'json', 'imaging', false)
                    ON CONFLICT (user_id, preference_key)
                    DO UPDATE SET preference_value = EXCLUDED.preference_value, updated_at = NOW()
                    """,
                    (json.dumps(config_data),)
                )
                cursor.connection.commit()

                return jsonify({'success': True, 'message': 'Model selection saved for post'})
                
    except Exception as e:
        logger.error(f"Error with model selection: {e}")
        return jsonify({'error': str(e)}), 500


def imaging_get_model_specs_handler():
    """Get model specifications and parameter defaults for UI"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get all image generation models from llm_model table
            cursor.execute("""
                SELECT lm.id, lm.name, lm.description, lm.api_params, lp.name as provider_name
                FROM llm_model lm
                JOIN llm_provider lp ON lm.provider_id = lp.id
                WHERE lm.api_params->>'type' = 'image'
                ORDER BY lm.name
            """)
            models = cursor.fetchall()
            
            # Get parameter defaults for each model
            cursor.execute("""
                SELECT model_key, param_key, default_value, param_type, min_value, max_value, options
                FROM model_param_default
                ORDER BY model_key, param_key
            """)
            param_defaults = cursor.fetchall()
            
            # Organize parameter defaults by model
            params_by_model = {}
            for param in param_defaults:
                model_key = param['model_key']
                if model_key not in params_by_model:
                    params_by_model[model_key] = []
                params_by_model[model_key].append({
                    'key': param['param_key'],
                    'default_value': param['default_value'],
                    'type': param['param_type'],
                    'min_value': param['min_value'],
                    'max_value': param['max_value'],
                    'options': param['options']
                })
            
            # Build response with model specs
            model_specs = []
            for model in models:
                model_key = model['name']
                api_params = model['api_params'] or {}
                
                spec = {
                    'model_key': model_key,
                    'name': model['name'],
                    'description': model['description'],
                    'provider': model['provider_name'],
                    'supports_lora': model_key == 'sdxl-lora',
                    'constraints': {
                        'max_prompt_chars': api_params.get('max_prompt_chars', 1000),
                        'supported_sizes': api_params.get('sizes', []),
                        'supported_qualities': api_params.get('quality', []),
                        'supported_styles': api_params.get('style', [])
                    },
                    'parameters': params_by_model.get(model_key, [])
                }
                model_specs.append(spec)
            
            return jsonify({
                'success': True,
                'models': model_specs
            })
            
    except Exception as e:
        logger.error(f"Error getting model specs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def register_routes(bp):
    """Register model configuration API routes with the blueprint"""
    
    @bp.route('/api/llm/save-config', methods=['POST'])
    def imaging_save_llm_config():
        """Save LLM configuration for imaging workflow"""
        try:
            data = request.get_json()
            
            # Extract configuration data
            image_model = data.get('image_model')
            system_prompt = data.get('system_prompt')
            user_prompt = data.get('user_prompt')
            llm_provider = data.get('llm_provider')
            llm_model = data.get('llm_model')
            temperature = data.get('temperature')
            max_tokens = data.get('max_tokens')
            parameters = data.get('parameters', {})
            
            # For now, just log the configuration (could be saved to database later)
            logger.info(f"Imaging LLM Config saved: image_model={image_model}, llm_provider={llm_provider}, llm_model={llm_model}")
            
            return jsonify({
                'success': True,
                'message': 'Configuration saved successfully'
            })
            
        except Exception as e:
            logger.error(f"Error saving imaging LLM configuration: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/model-selection', methods=['GET', 'POST'])
    def imaging_model_selection():
        """Get or save model selection configuration (per-post persistent)"""
        return imaging_model_selection_handler()

    @bp.route('/api/model-specs', methods=['GET'])
    def imaging_get_model_specs():
        """Get model specifications and parameter defaults for UI"""
        return imaging_get_model_specs_handler()

