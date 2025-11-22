"""
Settings API Endpoints
Provides data for the Post Type Settings modal
"""

from flask import Blueprint, jsonify, request
from config.database import db_manager
from config.post_type_pipeline_configs import (
    POST_TYPE_PIPELINE_CONFIGS,
    STEP_LABELS,
    STEP_FUNCTION_MAPPINGS,
    get_pipeline_steps,
    get_step_label,
    get_step_function
)
from config.authoring_panel_configs import (
    POST_TYPE_PANEL_CONFIGS,
    get_panel_config_by_post_type
)
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('settings_api', __name__, url_prefix='/api/settings')


@bp.route('/post-types/<post_type>/pipeline-steps', methods=['GET'])
def get_pipeline_steps_api(post_type):
    """Get pipeline steps for a post type with detailed information."""
    try:
        config = POST_TYPE_PIPELINE_CONFIGS.get(post_type)
        if not config:
            return jsonify({
                'success': False,
                'error': f'Post type "{post_type}" not found'
            }), 404

        steps = config.get('steps', [])
        function_mappings = STEP_FUNCTION_MAPPINGS.get(post_type, {})

        # Build detailed step information
        detailed_steps = []
        for i, step_id in enumerate(steps):
            step_info = {
                'stepId': step_id,
                'order': i + 1,
                'label': get_step_label(step_id),
                'function': get_step_function(step_id, post_type)
            }

            # Add previous/next step info
            if i > 0:
                prev_step_id = steps[i - 1]
                step_info['previous'] = {
                    'stepId': prev_step_id,
                    'label': get_step_label(prev_step_id)
                }

            if i < len(steps) - 1:
                next_step_id = steps[i + 1]
                step_info['next'] = {
                    'stepId': next_step_id,
                    'label': get_step_label(next_step_id)
                }

            detailed_steps.append(step_info)

        return jsonify({
            'success': True,
            'post_type': post_type,
            'steps': detailed_steps
        })

    except Exception as e:
        logger.error(f"Error fetching pipeline steps: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/post-types/<post_type>/panels', methods=['GET'])
def get_panel_config_api(post_type):
    """Get panel configuration for a post type."""
    try:
        config = get_panel_config_by_post_type(post_type)
        
        return jsonify({
            'success': True,
            'post_type': post_type,
            'panels': config.get('panels', []),
            'output_panel': config.get('output_panel'),
            'output_script': config.get('output_script')
        })

    except Exception as e:
        logger.error(f"Error fetching panel config: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/post-types/<post_type>/context/<stage>/<substage>', methods=['GET'])
def get_context_settings_api(post_type, stage, substage):
    """Get settings for a specific stage/substage context."""
    try:
        from config.template_mappings import get_template_path, get_templates_for_substage
        
        # Get template path for this post_type
        template_path = get_template_path(stage, substage, post_type)
        
        # Get all available templates for this substage (to show post_type-specific variants)
        all_templates = get_templates_for_substage(stage, substage)
        
        # Determine if template is post_type-specific
        is_post_type_specific = False
        if all_templates:
            # Check if there's a post_type-specific entry (not just 'default')
            is_post_type_specific = post_type in all_templates and 'default' in all_templates
        
        return jsonify({
            'success': True,
            'post_type': post_type,
            'stage': stage,
            'substage': substage,
            'template': {
                'path': template_path,
                'is_post_type_specific': is_post_type_specific,
                'all_variants': all_templates
            }
        })

    except Exception as e:
        logger.error(f"Error fetching context settings: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/post-types/<post_type>/navigation', methods=['GET'])
def get_navigation_structure_api(post_type):
    """Get navigation structure for a post type."""
    try:
        # Return the navigation structure
        # This could be customized per post type in the future
        navigation = {
            'calendar': {
                'label': 'Calendar',
                'icon': 'fa-calendar-alt',
                'substages': ['view', 'week-view', 'ideas-week']
            },
            'concept': {
                'label': 'Planning',
                'icon': 'fa-lightbulb',
                'substages': ['taxonomy', 'section-structure', 'topic-allocation', 'titling']
            },
            'research': {
                'label': 'Research',
                'icon': 'fa-search',
                'substages': ['research', 'sources', 'visuals', 'prompts', 'verification']
            },
            'authoring': {
                'label': 'Authoring',
                'icon': 'fa-pen-nib',
                'substages': ['drafting', 'image-concepts', 'image-prompts', 'image-captions']
            },
            'imaging': {
                'label': 'Imaging',
                'icon': 'fa-magic',
                'substages': ['image-generation', 'optimise']
            },
            'header': {
                'label': 'Header',
                'icon': 'fa-heading',
                'substages': ['title-summary', 'image-prompt', 'image-details', 'image-generate', 'seo-meta']
            }
        }

        # Filter based on post type
        if post_type == 'profile':
            # Profile posts don't have Calendar or Research
            navigation.pop('calendar', None)
            navigation.pop('research', None)
        elif post_type == 'recipe':
            # Recipe posts don't have Research
            navigation.pop('research', None)

        return jsonify({
            'success': True,
            'post_type': post_type,
            'navigation': navigation
        })

    except Exception as e:
        logger.error(f"Error fetching navigation structure: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/llm-config/<page_type>', methods=['GET'])
def get_llm_config_api(page_type):
    """Get LLM configuration for a page type."""
    try:
        # This would need to read from the JavaScript LLM_CONFIGS
        # For now, return a placeholder
        return jsonify({
            'success': True,
            'page_type': page_type,
            'message': 'LLM config should be read from JavaScript LLM_CONFIGS object'
        })

    except Exception as e:
        logger.error(f"Error fetching LLM config: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

