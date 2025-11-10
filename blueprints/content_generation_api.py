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
        
        # Create post first (with placeholder title) so we have a post_id for LLM intercept_context
        post_creator = PostCreator()
        
        # Get source name for idea_seed
        from utils.vector_search.retrieval import ContentRetriever
        retriever = ContentRetriever()
        context_result = retriever.search(
            query=f"{source_type} {source_id}",
            chunk_types=[source_type],
            limit=1
        )
        
        source_name = f'{source_type} {source_id}'
        if context_result.get('results'):
            for result in context_result['results']:
                if result['source_id'] == source_id:
                    metadata = result.get('metadata', {})
                    source_name = metadata.get(f'{source_type}_name') or metadata.get('name', source_name)
                    break
        
        # Create placeholder post with generated_source_type and preset taxonomy
        placeholder_title = f"Generating content for {source_name}..."
        idea_seed = f"Generated from {source_type}: {source_name}"
        post_id = post_creator.create_post(
            title=placeholder_title,
            standfirst='',
            idea_seed=idea_seed,
            expanded_idea='',
            generated_source_type=source_type  # Set source type: 'product' or 'category'
        )
        
        # Generate content (now we have a valid post_id)
        orchestrator = GenerationOrchestrator()
        generation_result = orchestrator.generate_content(
            source_type=source_type,
            source_id=source_id,
            generation_type=generation_type,
            tone=tone,
            length=length,
            post_id=post_id  # Pass post_id for intercept_context
        )
        
        if not generation_result.get('success'):
            # Delete placeholder post if generation failed
            try:
                from config.database import db_manager
                with db_manager.get_cursor() as cursor:
                    cursor.execute("DELETE FROM post WHERE id = %s", (post_id,))
            except Exception as e:
                logger.warning(f"Failed to delete placeholder post {post_id}: {e}")
            return jsonify(generation_result), 500
        
        content_data = generation_result['content']
        
        # Extract content
        headline = content_data.get('headline', 'Untitled Post')
        standfirst = content_data.get('standfirst', '')
        sections = content_data.get('sections', [])
        
        # Update post with generated content
        expanded_idea = json.dumps([s.get('heading', '') for s in sections])
        from config.database import db_manager
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE post 
                SET title = %s, summary = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (headline, standfirst, post_id))
            
            cursor.execute("""
                UPDATE post_development
                SET expanded_idea = %s, updated_at = CURRENT_TIMESTAMP
                WHERE post_id = %s
            """, (expanded_idea, post_id))
        
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
        
        # For preview, we need a temporary post_id for intercept_context
        # Create a temporary post that we'll delete after preview
        post_creator = PostCreator()
        temp_post_id = post_creator.create_post(
            title='[PREVIEW] Temporary Post',
            standfirst='',
            idea_seed=f'Preview: {source_type} {source_id}',
            expanded_idea=''
        )
        
        try:
            # Generate content (without updating post)
            orchestrator = GenerationOrchestrator()
            generation_result = orchestrator.generate_content(
                source_type=source_type,
                source_id=source_id,
                generation_type=generation_type,
                post_id=temp_post_id
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
        finally:
            # Clean up temporary post
            try:
                from config.database import db_manager
                with db_manager.get_cursor() as cursor:
                    cursor.execute("DELETE FROM post WHERE id = %s", (temp_post_id,))
            except Exception as e:
                logger.warning(f"Failed to delete temporary preview post {temp_post_id}: {e}")
    except Exception as e:
        logger.error(f"Error previewing content: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/content/suggest-ideas', methods=['POST'])
def api_suggest_ideas():
        """
        Get content suggestions from vector search.
        
        Request body:
        {
            "query": "interesting Scottish products",  // optional
            "limit": 10  // optional, default 10
        }
        
        Response:
        {
            "success": true,
            "suggestions": [
                {
                    "type": "product",
                    "id": 123,
                    "name": "Lambswool Scarf",
                    "reason": "Rich heritage and craftsmanship details",
                    "score": 0.89
                }
            ]
        }
        """
        try:
            data = request.get_json() or {}
            query = data.get('query', 'interesting Scottish products')
            limit = data.get('limit', 10)
            
            from utils.vector_search.retrieval import ContentRetriever
            
            retriever = ContentRetriever()
            results = retriever.search(
                query=query,
                chunk_types=['product', 'category'],
                limit=limit
            )
            
            suggestions = []
            for result in results.get('results', []):
                metadata = result.get('metadata', {})
                chunk_type = result.get('chunk_type', 'product')
                
                suggestion = {
                    'type': chunk_type,
                    'id': result.get('source_id'),
                    'name': metadata.get(f'{chunk_type}_name') or metadata.get('name', 'Unknown'),
                    'reason': f"Relevant content with {chunk_type} details",
                    'score': result.get('score', 0)
                }
                
                # Add more specific reason based on metadata
                if chunk_type == 'product' and metadata.get('supplier_name'):
                    suggestion['reason'] = f"Product from {metadata['supplier_name']}"
                elif chunk_type == 'category' and metadata.get('category_name'):
                    suggestion['reason'] = f"Category: {metadata['category_name']}"
                
                suggestions.append(suggestion)
            
            return jsonify({
                'success': True,
                'suggestions': suggestions
            })
            
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
