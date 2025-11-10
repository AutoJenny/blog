"""
Content Generation API

API endpoints for generating blog posts from products/categories.
"""

from flask import Blueprint, jsonify, request
import logging
import json
from utils.content_generation.generation_orchestrator import GenerationOrchestrator
from utils.content_generation.post_creator import PostCreator

logger = logging.getLogger(__name__)

bp = Blueprint('content_generation', __name__)


@bp.route('/api/content/generate', methods=['POST'])
def api_generate_content():
    """
    Generate blog post from product or category.
    
    Request body:
    {
        "source_type": "product",  // or "category"
        "source_id": 123,
        "generation_type": "deep_dive",  // or "comparison", "feature"
        "tone": "warm",  // optional
        "length": "medium"  // optional: short, medium, long
    }
    
    Response:
    {
        "success": true,
        "post_id": 456,
        "title": "Generated headline",
        "sections": [...]
    }
    """
    try:
        data = request.get_json() or {}
        source_type = data.get('source_type', '').lower()
        source_id = data.get('source_id')
        generation_type = data.get('generation_type', 'deep_dive')
        tone = data.get('tone', 'warm')
        length = data.get('length', 'medium')
        
        # Validate input
        if source_type not in ['product', 'category']:
            return jsonify({
                'success': False,
                'error': 'source_type must be "product" or "category"'
            }), 400
        
        if not source_id:
            return jsonify({
                'success': False,
                'error': 'source_id is required'
            }), 400
        
        # Generate content
        orchestrator = GenerationOrchestrator()
        generation_result = orchestrator.generate_content(
            source_type=source_type,
            source_id=source_id,
            generation_type=generation_type,
            tone=tone,
            length=length
        )
        
        if not generation_result.get('success'):
            return jsonify(generation_result), 500
        
        content_data = generation_result['content']
        
        # Extract content
        headline = content_data.get('headline', 'Untitled Post')
        standfirst = content_data.get('standfirst', '')
        sections = content_data.get('sections', [])
        
        # Create idea seed
        source_name = generation_result['context']['primary'].get('metadata', {}).get(
            f'{source_type}_name',
            f'{source_type} {source_id}'
        )
        idea_seed = f"Generated from {source_type}: {source_name}"
        expanded_idea = json.dumps([s.get('heading', '') for s in sections])
        
        # Create post
        post_creator = PostCreator()
        post_id = post_creator.create_post(
            title=headline,
            standfirst=standfirst,
            idea_seed=idea_seed,
            expanded_idea=expanded_idea
        )
        
        # Create sections
        section_ids = post_creator.create_sections_from_generated(
            post_id=post_id,
            sections=sections
        )
        
        # Add product image if product
        if source_type == 'product':
            post_creator.add_product_image(post_id, source_id)
        
        # Format response
        response_sections = [
            {
                'section_id': sid,
                'heading': sections[i].get('heading', ''),
                'content': sections[i].get('content', '')
            }
            for i, sid in enumerate(section_ids)
        ]
        
        return jsonify({
            'success': True,
            'post_id': post_id,
            'title': headline,
            'standfirst': standfirst,
            'sections': response_sections
        })
        
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/content/preview', methods=['POST'])
def api_preview_content():
    """
    Preview generation without saving to database.
    
    Same request body as /api/content/generate
    Returns preview data without creating post.
    """
    try:
        data = request.get_json() or {}
        source_type = data.get('source_type', '').lower()
        source_id = data.get('source_id')
        generation_type = data.get('generation_type', 'deep_dive')
        
        if source_type not in ['product', 'category']:
            return jsonify({
                'success': False,
                'error': 'source_type must be "product" or "category"'
            }), 400
        
        if not source_id:
            return jsonify({
                'success': False,
                'error': 'source_id is required'
            }), 400
        
        # Generate content (without creating post)
        orchestrator = GenerationOrchestrator()
        generation_result = orchestrator.generate_content(
            source_type=source_type,
            source_id=source_id,
            generation_type=generation_type
        )
        
        if not generation_result.get('success'):
            return jsonify(generation_result), 500
        
        content_data = generation_result['content']
        
        return jsonify({
            'success': True,
            'preview': {
                'headline': content_data.get('headline', ''),
                'standfirst': content_data.get('standfirst', ''),
                'sections': content_data.get('sections', [])
            }
        })
        
    except Exception as e:
        logger.error(f"Error previewing content: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
