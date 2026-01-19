"""
Workflow Navigation API
Provides endpoints for workflow navigation (Next button, progress tracking)
"""

from flask import Blueprint, jsonify, request
from config.database import db_manager
from config.post_type_substages import POST_TYPE_SUBSTAGES, SUBSTAGE_METADATA
from utils.taxonomy_helpers import get_post_type
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('workflow_navigation', __name__, url_prefix='/api/workflow')

@bp.route('/substages', methods=['GET'])
def get_substages():
    """
    Get substages configuration for a post type
    Returns substages organized by stage in order
    """
    try:
        post_type = request.args.get('post_type', 'themed')
        
        # Normalize post_type
        if post_type not in POST_TYPE_SUBSTAGES:
            post_type = 'themed'
        
        # Get substages for this post type
        substages_by_stage = POST_TYPE_SUBSTAGES[post_type]
        
        # Build response - return list of substage keys for each stage
        result = {}
        for stage, substage_keys in substages_by_stage.items():
            result[stage] = substage_keys  # Return list of substage keys
        
        return jsonify({
            'success': True,
            'post_type': post_type,
            'substages': result
        })
    except Exception as e:
        logger.error(f"Error getting substages: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/next-substage', methods=['GET'])
def get_next_substage():
    """
    Get next substage for a post
    Returns next substage URL and metadata
    """
    try:
        post_id = request.args.get('post_id', type=int)
        current_stage = request.args.get('stage')
        current_substage = request.args.get('substage')
        
        if not post_id:
            return jsonify({
                'success': False,
                'error': 'post_id is required'
            }), 400
        
        # Get post type
        post_type = get_post_type(post_id)
        if not post_type:
            post_type = 'themed'
        
        # Get substages
        substages_by_stage = POST_TYPE_SUBSTAGES.get(post_type, POST_TYPE_SUBSTAGES['themed'])
        
        # Find current position
        if not current_stage or not current_substage:
            return jsonify({
                'success': False,
                'error': 'stage and substage are required'
            }), 400
        
        # Normalize stage name
        if current_stage == 'concept':
            current_stage = 'planning'
        
        # Get substages for current stage
        stage_substages = substages_by_stage.get(current_stage, [])
        if not stage_substages:
            return jsonify({
                'success': False,
                'error': f'No substages found for stage: {current_stage}'
            }), 404
        
        # Find current substage index
        current_index = stage_substages.index(current_substage) if current_substage in stage_substages else -1
        
        if current_index == -1:
            return jsonify({
                'success': False,
                'error': f'Substage {current_substage} not found in stage {current_stage}'
            }), 404
        
        # Check if there's a next substage in current stage
        if current_index < len(stage_substages) - 1:
            next_substage_key = stage_substages[current_index + 1]
            next_stage = current_stage
        else:
            # Move to next stage
            stage_order = ['planning', 'research', 'authoring', 'imaging', 'header']
            current_stage_index = stage_order.index(current_stage) if current_stage in stage_order else -1
            
            if current_stage_index == -1 or current_stage_index == len(stage_order) - 1:
                # No next stage
                return jsonify({
                    'success': False,
                    'error': 'No next substage available'
                }), 404
            
            next_stage = stage_order[current_stage_index + 1]
            next_stage_substages = substages_by_stage.get(next_stage, [])
            
            if not next_stage_substages:
                return jsonify({
                    'success': False,
                    'error': f'No substages found for next stage: {next_stage}'
                }), 404
            
            next_substage_key = next_stage_substages[0]
        
        # Get metadata for next substage
        metadata = SUBSTAGE_METADATA.get(next_substage_key, {})
        route_function = metadata.get('route_function')
        
        # Build URL
        url = None
        if route_function:
            from flask import url_for
            try:
                url = url_for(route_function, post_id=post_id)
            except Exception as e:
                logger.warning(f"Could not generate URL for route_function {route_function}: {e}")
        
        # Fallback: Build URL from pattern
        if not url:
            url = build_substage_url(post_id, next_stage, next_substage_key)
        
        return jsonify({
            'success': True,
            'next': {
                'stage': next_stage,
                'substage': next_substage_key,
                'label': metadata.get('label', next_substage_key.replace('_', ' ').title()),
                'url': url
            }
        })
    except Exception as e:
        logger.error(f"Error getting next substage: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def build_substage_url(post_id, stage, substage_key):
    """Build URL for a substage based on pattern"""
    # Try to use url_for if available
    try:
        from flask import url_for
        route_map = {
            'ideas': 'planning.planning_calendar_ideas',
            'taxonomy': 'planning.planning_calendar_taxonomy',
            'topic_brainstorming': 'planning.planning_concept_brainstorm',
            'section_structure': 'planning.planning_concept_section_structure',
            'topic_allocation': 'planning.planning_concept_topic_allocation',
            'section_titling': 'planning.planning_concept_titling',
            'drafting': 'authoring.authoring_sections_drafting',
            'image_concepts': 'authoring_imaging.authoring_sections_image_concepts',
            'image_prompts': 'authoring_imaging.authoring_sections_image_prompts',
            'image_captions': 'authoring_imaging.authoring_sections_image_captions',
            'image_generation': 'imaging.imaging_sections_image_generation',
            'optimise': 'imaging.imaging_sections_optimise',
            'title_summary': 'header.header_title_summary',
            'header_image': 'header.header_header_image',
            'seo_meta': 'header.header_seo_meta',
            'final_review': 'header.header_preview'
        }
        
        route_function = route_map.get(substage_key)
        if route_function:
            return url_for(route_function, post_id=post_id)
    except Exception as e:
        logger.warning(f"Could not use url_for for {substage_key}: {e}")
    
    # Fallback: Build URL from pattern
    route_patterns = {
        'ideas': f'/planning/posts/{post_id}/calendar/ideas',
        'taxonomy': f'/planning/posts/{post_id}/calendar/taxonomy',
        'topic_brainstorming': f'/planning/posts/{post_id}/concept/brainstorm',
        'section_structure': f'/planning/posts/{post_id}/concept/section-structure',
        'topic_allocation': f'/planning/posts/{post_id}/concept/topic-allocation',
        'section_titling': f'/planning/posts/{post_id}/concept/titling',
        'drafting': f'/authoring/posts/{post_id}/sections/drafting',
        'image_concepts': f'/authoring/posts/{post_id}/sections/image-concepts',
        'image_prompts': f'/authoring/posts/{post_id}/sections/image-prompts',
        'image_captions': f'/authoring/posts/{post_id}/sections/image-captions',
        'image_generation': f'/imaging/posts/{post_id}/sections/image-generation',
        'optimise': f'/imaging/posts/{post_id}/sections/optimise',
        'title_summary': f'/header/posts/{post_id}/title-summary',
        'header_image': f'/header/posts/{post_id}/header-image',
        'seo_meta': f'/header/posts/{post_id}/seo-meta',
        'final_review': f'/header/posts/{post_id}/preview'
    }
    
    return route_patterns.get(substage_key, None)
