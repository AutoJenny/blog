"""SEO meta API endpoints for header blueprint"""
from flask import Blueprint, jsonify, request
from config.database import db_manager
from .helpers import resolve_target_post_id, resolve_target_post_id_with_auto_week_check
import logging
import json
import re

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Register SEO meta API routes"""
    
    @bp.route('/api/posts/<int:post_id>/generate-seo-meta', methods=['POST'])
    def api_generate_seo_meta(post_id):
        """Generate meta title, description, tags"""
        try:
            from modules.llm_service import llm_service
            
            year = request.args.get('year', type=int)
            week = request.args.get('week', type=int)
            
            target_post_id, error = resolve_target_post_id_with_auto_week_check(post_id, year, week)
            if error:
                return jsonify({'error': error}), 400 if 'required' in error else 404
            
            # Get post title and summary from post table (use target_post_id)
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT title, summary
                    FROM post 
                    WHERE id = %s
                """, (target_post_id,))
                
                post_data = cursor.fetchone()
                if not post_data:
                    return jsonify({'error': 'Post not found'}), 404
                
                # Get section titles from planning/concept/titling (use resolved post_id)
                cursor.execute("""
                    SELECT section_heading
                    FROM post_section 
                    WHERE post_id = %s 
                    ORDER BY section_order
                """, (target_post_id,))
                
                sections = cursor.fetchall()
                
                # Build context for LLM
                post_title = post_data['title'] or ''
                post_summary = post_data['summary'] or ''
                
                section_titles = []
                for section in sections:
                    title = section['section_heading'] or ''
                    if title:
                        section_titles.append(title)
                
                sections_text = "\n".join(section_titles)
                
                # Call LLM to generate SEO metadata
                task_prompt = f"""Generate SEO metadata for this blog post:

Post Title: {post_title}

Summary: {post_summary}

Section Structure:
{sections_text}

Generate:
1. A compelling HTML meta title (max 60 characters)
2. A concise HTML meta description (max 160 characters)
3. Relevant meta tags (comma-separated, 5-8 tags)

Return in JSON format:
{{
  "meta_title": "Short compelling title",
  "meta_description": "Brief engaging description",
  "meta_tags": "tag1, tag2, tag3, tag4, tag5"
}}"""
                
                # Call LLM with intercept_context (use resolved post_id)
                intercept_context = {
                    'post_id': target_post_id,
                    'step_id': 66,  # SEO meta generation step
                    'context_type': 'seo_meta_generation'
                }
                
                llm_response = llm_service.execute_llm_request(
                    provider='ollama',
                    model='llama3.2:latest',
                    messages=[{'role': 'user', 'content': task_prompt}],
                    intercept_context=intercept_context
                )
                
                if 'error' in llm_response:
                    logger.error(f"LLM call failed: {llm_response}")
                    return jsonify({'error': 'Failed to generate SEO metadata'}), 500
                
                content = llm_response.get('content', '')
                
                logger.info(f"LLM response content: {content}")
                
                # Parse JSON response
                
                # Try to extract JSON from code blocks first
                json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', content)
                if not json_match:
                    # Fallback: try to find JSON without code blocks
                    json_match = re.search(r'\{[\s\S]*\}', content)
                
                if json_match:
                    json_text = json_match.group(1) if json_match.lastindex else json_match.group(0)
                    # Clean up the JSON text
                    json_text = json_text.strip()
                    try:
                        seo_data = json.loads(json_text)
                        
                        meta_title = seo_data.get('meta_title', '')
                        meta_description = seo_data.get('meta_description', '')
                        meta_tags = seo_data.get('meta_tags', '')
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error: {e}, text: {repr(json_text)}")
                        meta_title = ""
                        meta_description = ""
                        meta_tags = ""
                else:
                    logger.error(f"Failed to find JSON in LLM response: {content}")
                    # Fallback if JSON parsing fails
                    meta_title = ""
                    meta_description = ""
                    meta_tags = ""
                
                # Get header image path for OG image
                cursor.execute("""
                    SELECT i.file_path as path 
                    FROM post p
                    JOIN images i ON p.header_image_id = i.id
                    WHERE p.id = %s
                """, (post_id,))
                
                image_result = cursor.fetchone()
                raw_path = image_result['path'] if image_result and image_result['path'] else None
                
                if raw_path:
                    # Convert to optimized path: replace /raw/ with /optimized/ and .png with .jpg
                    optimized_path = raw_path.replace('/raw/', '/optimized/').replace('.png', '.jpg')
                    meta_image = f"https://clan.com{optimized_path}"
                else:
                    meta_image = "https://clan.com/images/default-scottish-heritage.jpg"
                
                # Save to database (use resolved post_id)
                cursor.execute("""
                    UPDATE post 
                    SET meta_title = %s,
                        meta_description = %s,
                        meta_tags = %s,
                        meta_image = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (meta_title, meta_description, meta_tags, meta_image, target_post_id))
                
                return jsonify({
                    'success': True,
                    'meta_title': meta_title,
                    'meta_description': meta_description,
                    'meta_tags': meta_tags,
                    'meta_image': meta_image,
                    'meta_type': 'article',
                    'meta_site_name': 'Clan.com Blog'
                })
                
        except Exception as e:
            logger.error(f"Error generating SEO meta: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/posts/<int:post_id>/get-meta-data', methods=['GET'])
    def api_get_meta_data(post_id):
        """Get current meta data for post"""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT meta_title, meta_description, meta_tags, 
                           meta_image, meta_type, meta_site_name
                    FROM post 
                    WHERE id = %s
                """, (post_id,))
                
                result = cursor.fetchone()
                if not result:
                    return jsonify({'error': 'Post not found'}), 404
                
                return jsonify({
                    'success': True,
                    'meta_title': result['meta_title'] or '',
                    'meta_description': result['meta_description'] or '',
                    'meta_tags': result['meta_tags'] or '',
                    'meta_image': result['meta_image'] or '',
                    'meta_type': result['meta_type'] or 'article',
                    'meta_site_name': result['meta_site_name'] or 'Clan.com Blog'
                })
                
        except Exception as e:
            logger.error(f"Error getting meta data: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/posts/<int:post_id>/save-author', methods=['POST'])
    def api_save_author(post_id):
        """Save author name to post"""
        try:
            data = request.get_json()
            author_name = data.get('author_name', '')
            
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE post 
                    SET author_name = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (author_name, post_id))
                
                return jsonify({'success': True})
                
        except Exception as e:
            logger.error(f"Error saving author for post {post_id}: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/posts/<int:post_id>/generate-embeddings', methods=['POST'])
    def api_generate_post_embeddings(post_id):
        """Generate vector embeddings for post content and find similar entities"""
        try:
            year = request.args.get('year', type=int)
            week = request.args.get('week', type=int)
            
            target_post_id, error = resolve_target_post_id_with_auto_week_check(post_id, year, week)
            if error:
                return jsonify({'error': error}), 400 if 'required' in error else 404
            
            # Import required modules
            from utils.vector_search.post_extractor import extract_post_content
            from utils.vector_search.embeddings import EmbeddingGenerator
            from utils.vector_search.faiss_index import FAISSIndexManager
            from utils.vector_search.chunking import ContentChunker
            from utils.profile_matching.post_matcher import find_similar_entities
            from utils.profile_matching.normalization import normalize_and_select_best
            import json
            import numpy as np
            
            # Step 1: Extract post content
            logger.info(f"Extracting content for post {target_post_id}")
            post_content = extract_post_content(target_post_id)
            
            if not post_content:
                return jsonify({
                    'success': False,
                    'error': 'No content found in post_development. Please ensure the post has expanded_idea, idea_seed, summary, or intro_blurb.'
                }), 400
            
            # Step 2: Check if embedding already exists
            chunker = ContentChunker()
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, faiss_index_id, embedding_model, embedding_dim, last_embedded_at
                    FROM content_chunks
                    WHERE chunk_type = 'post' AND source_id = %s
                """, (target_post_id,))
                
                existing_chunk = cursor.fetchone()
            
            # Step 3: Generate embedding
            logger.info(f"Generating embedding for post {target_post_id}")
            embedding_gen = EmbeddingGenerator()
            embedding = embedding_gen.generate_embedding(post_content)
            
            # Step 4: Store in content_chunks and FAISS index
            faiss_manager = FAISSIndexManager()
            if not faiss_manager.load_index():
                logger.warning("FAISS index not loaded, creating new one")
                faiss_manager.create_index()
            
            if existing_chunk:
                # Update existing chunk
                chunk_id = existing_chunk['id']
                chunk_data = {
                    'chunk_text': post_content,
                    'metadata': {
                        'post_id': target_post_id,
                        'post_title': None  # Could fetch from post table if needed
                    }
                }
                
                # Update chunk text and metadata
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        UPDATE content_chunks
                        SET chunk_text = %s, 
                            metadata = %s::jsonb,
                            embedding_model = %s,
                            embedding_dim = %s,
                            last_embedded_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (
                        chunk_data['chunk_text'],
                        json.dumps(chunk_data['metadata']),
                        embedding_gen.model_name,
                        len(embedding),
                        chunk_id
                    ))
                
                # Update FAISS index if needed
                if existing_chunk['faiss_index_id'] is None:
                    # Add to index
                    embeddings_array = np.array([embedding])
                    faiss_ids = faiss_manager.add_vectors(embeddings_array, [chunk_id])
                    faiss_index_id = faiss_ids[0] if faiss_ids else None
                    
                    if faiss_index_id is not None:
                        with db_manager.get_cursor() as cursor:
                            cursor.execute("""
                                UPDATE content_chunks
                                SET faiss_index_id = %s
                                WHERE id = %s
                            """, (faiss_index_id, chunk_id))
                else:
                    faiss_index_id = existing_chunk['faiss_index_id']
            else:
                # Create new chunk
                chunk_data = {
                    'chunk_text': post_content,
                    'metadata': {
                        'post_id': target_post_id
                    }
                }
                
                chunk_id = chunker.save_chunk('post', target_post_id, chunk_data)
                
                # Add to FAISS index
                embeddings_array = np.array([embedding])
                faiss_ids = faiss_manager.add_vectors(embeddings_array, [chunk_id])
                faiss_index_id = faiss_ids[0] if faiss_ids else None
                
                # Update chunk with embedding metadata and FAISS index ID
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        UPDATE content_chunks
                        SET embedding_model = %s,
                            embedding_dim = %s,
                            faiss_index_id = %s,
                            last_embedded_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (
                        embedding_gen.model_name,
                        len(embedding),
                        faiss_index_id,
                        chunk_id
                    ))
            
            # Save FAISS index
            faiss_manager.save_index()
            
            # Step 5: Find similar entities (pass post_content to avoid re-extraction)
            logger.info(f"Finding similar entities for post {target_post_id}")
            matches = find_similar_entities(target_post_id, limit=3, post_content=post_content)
            
            # Step 6: Normalize and select best match
            best_match = normalize_and_select_best(
                matches['products'],
                matches['suppliers'],
                matches['categories']
            )
            
            # Step 7: Return results
            return jsonify({
                'success': True,
                'embedding': {
                    'chunk_id': chunk_id,
                    'faiss_index_id': faiss_index_id,
                    'filepath': 'data/vector_index/products_categories.faiss',
                    'table': 'content_chunks',
                    'model': embedding_gen.model_name,
                    'dimension': len(embedding),
                    'generated_at': existing_chunk['last_embedded_at'].isoformat() if existing_chunk and existing_chunk.get('last_embedded_at') else None
                },
                'matches': {
                    'products': matches['products'],
                    'suppliers': matches['suppliers'],
                    'categories': matches['categories']
                },
                'best_match': best_match
            })
            
        except Exception as e:
            logger.error(f"Error generating embeddings for post {post_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/posts/<int:post_id>/save-embedding-overrides', methods=['POST'])
    def api_save_embedding_overrides(post_id):
        """Save manual overrides for embedding similarity matches"""
        try:
            year = request.args.get('year', type=int)
            week = request.args.get('week', type=int)
            
            target_post_id, error = resolve_target_post_id_with_auto_week_check(post_id, year, week)
            if error:
                return jsonify({'error': error}), 400 if 'required' in error else 404
            
            data = request.get_json()
            
            # Get existing overrides
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT embedding_overrides
                    FROM post_development
                    WHERE post_id = %s
                """, (target_post_id,))
                
                result = cursor.fetchone()
                existing_overrides = result['embedding_overrides'] if result and result.get('embedding_overrides') else {}
            
            # Update overrides
            overrides = existing_overrides.copy() if isinstance(existing_overrides, dict) else {}
            
            # Update from request data
            if 'selected_type' in data:
                overrides['selected_type'] = data['selected_type']
            if 'selected_id' in data:
                overrides['selected_id'] = data['selected_id']
            # Legacy support for individual type fields
            if 'selected_product_id' in data:
                overrides['selected_product_id'] = data['selected_product_id']
            if 'selected_supplier_id' in data:
                overrides['selected_supplier_id'] = data['selected_supplier_id']
            if 'selected_category_id' in data:
                overrides['selected_category_id'] = data['selected_category_id']
            
            overrides['override_reason'] = 'manual'
            overrides['updated_at'] = 'now'
            
            # Save to database
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE post_development
                    SET embedding_overrides = %s::jsonb,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE post_id = %s
                """, (json.dumps(overrides), target_post_id))
            
            return jsonify({
                'success': True,
                'overrides': overrides
            })
            
        except Exception as e:
            logger.error(f"Error saving embedding overrides for post {post_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/posts/<int:post_id>/get-embedding-overrides', methods=['GET'])
    def api_get_embedding_overrides(post_id):
        """Get manual overrides for embedding similarity matches"""
        try:
            year = request.args.get('year', type=int)
            week = request.args.get('week', type=int)
            
            target_post_id, error = resolve_target_post_id_with_auto_week_check(post_id, year, week)
            if error:
                return jsonify({'error': error}), 400 if 'required' in error else 404
            
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT embedding_overrides
                    FROM post_development
                    WHERE post_id = %s
                """, (target_post_id,))
                
                result = cursor.fetchone()
                overrides = result['embedding_overrides'] if result and result.get('embedding_overrides') else {}
            
            return jsonify({
                'success': True,
                'overrides': overrides
            })
            
        except Exception as e:
            logger.error(f"Error getting embedding overrides for post {post_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'error': str(e)}), 500

