"""
Workflow Navigation API
Provides endpoints for workflow navigation (Next button, progress tracking)

W2-FIX-8: Uses DB-backed substage config (post_type_substages, substage_metadata).
Falls back to config/post_type_substages with deprecation warning only when DB is empty.
"""

from flask import Blueprint, jsonify, request
from utils.taxonomy_helpers import get_post_type
from utils.substage_config import (
    get_substages_for_post_type,
    get_substage_metadata,
)
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('workflow_navigation', __name__, url_prefix='/api/workflow')

# Stage order for "next substage" navigation (DB does not store stage order)
_STAGE_ORDER = ['planning', 'research', 'authoring', 'imaging', 'header']


def _get_substages_with_fallback(post_type):
    """Get substages from DB; fall back to config if DB returns empty. Logs warning on fallback."""
    substages = get_substages_for_post_type(post_type)
    if substages:
        return substages
    # Fallback when DB has no data (e.g. tables not populated)
    try:
        from config.post_type_substages import POST_TYPE_SUBSTAGES
        fallback = POST_TYPE_SUBSTAGES.get(post_type, POST_TYPE_SUBSTAGES.get('themed', {}))
        if fallback:
            logger.warning(
                "workflow_navigation: DB substage config empty for post_type=%s, using config fallback. "
                "Populate post_type_substages and substage_metadata for DB-backed config.",
                post_type
            )
            return fallback
    except ImportError:
        pass
    return {}


def _get_substage_metadata_with_fallback(substage_key):
    """Get substage metadata from DB; fall back to config if not found."""
    meta = get_substage_metadata(substage_key)
    if meta:
        return meta
    try:
        from config.post_type_substages import SUBSTAGE_METADATA
        return SUBSTAGE_METADATA.get(substage_key, {})
    except ImportError:
        return {}


@bp.route('/substages', methods=['GET'])
def get_substages():
    """
    Get substages configuration for a post type
    Returns substages organized by stage in order.
    W2-FIX-8: Uses DB-backed config; fallback to config with warning.
    """
    try:
        post_type = request.args.get('post_type', 'themed')
        substages_by_stage = _get_substages_with_fallback(post_type)
        if not substages_by_stage:
            post_type = 'themed'
            substages_by_stage = _get_substages_with_fallback('themed')
        
        result = {stage: keys for stage, keys in substages_by_stage.items()}
        
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
    Returns next substage URL and metadata.
    W2-FIX-8: Uses DB-backed substage config.
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
        
        post_type = get_post_type(post_id)
        if not post_type:
            post_type = 'themed'
        
        substages_by_stage = _get_substages_with_fallback(post_type)
        if not substages_by_stage:
            substages_by_stage = _get_substages_with_fallback('themed')
        
        if not current_stage or not current_substage:
            return jsonify({
                'success': False,
                'error': 'stage and substage are required'
            }), 400
        
        if current_stage == 'concept':
            current_stage = 'planning'
        
        stage_substages = substages_by_stage.get(current_stage, [])
        if not stage_substages:
            return jsonify({
                'success': False,
                'error': f'No substages found for stage: {current_stage}'
            }), 404
        
        current_index = stage_substages.index(current_substage) if current_substage in stage_substages else -1
        
        if current_index == -1:
            return jsonify({
                'success': False,
                'error': f'Substage {current_substage} not found in stage {current_stage}'
            }), 404
        
        if current_index < len(stage_substages) - 1:
            next_substage_key = stage_substages[current_index + 1]
            next_stage = current_stage
        else:
            current_stage_index = _STAGE_ORDER.index(current_stage) if current_stage in _STAGE_ORDER else -1
            
            if current_stage_index == -1 or current_stage_index == len(_STAGE_ORDER) - 1:
                return jsonify({
                    'success': False,
                    'error': 'No next substage available'
                }), 404
            
            next_stage = _STAGE_ORDER[current_stage_index + 1]
            next_stage_substages = substages_by_stage.get(next_stage, [])
            
            if not next_stage_substages:
                return jsonify({
                    'success': False,
                    'error': f'No substages found for next stage: {next_stage}'
                }), 404
            
            next_substage_key = next_stage_substages[0]
        
        metadata = _get_substage_metadata_with_fallback(next_substage_key)
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
        'drafting': f'/posts/{post_id}/sections/drafting',  # W2-FIX-1: authoring bp has no prefix
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
