"""
Planning Post-Specific API Module

Micro-file for post-specific API endpoints that aren't basic CRUD
"""

from flask import request, jsonify
from config.database import db_manager
from blueprints.planning_llm import LLMService
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def api_posts_expanded_idea(post_id):
    """Get or create expanded idea for a post"""
    if request.method == 'GET':
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT expanded_idea
                    FROM post_development 
                    WHERE post_id = %s
                """, (post_id,))
                
                result = cursor.fetchone()
                
                if result and result['expanded_idea']:
                    return jsonify({
                        'success': True,
                        'expanded_idea': result['expanded_idea']
                    })
                else:
                    return jsonify({
                        'success': True,
                        'expanded_idea': None
                    })
                    
        except Exception as e:
            logger.error(f"Error fetching expanded idea: {e}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            idea_seed = data.get('idea_seed', '')
            
            if not idea_seed:
                return jsonify({'error': 'Idea seed is required'}), 400
            
            # Generate expanded idea using LLM
            llm_service = LLMService()
            
            # Load prompt from database
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT system_prompt, prompt_text
                    FROM llm_prompt 
                    WHERE name = 'Expanded Idea Generation'
                    ORDER BY id DESC
                    LIMIT 1
                """)
                prompt_data = cursor.fetchone()
                
                if prompt_data:
                    system_prompt = prompt_data['system_prompt']
                    prompt_text = prompt_data['prompt_text']
                else:
                    # Fallback prompts
                    system_prompt = "You are an expert content creator. Expand the given idea seed into a comprehensive, engaging expanded idea that can be developed into a full blog post."
                    prompt_text = "Expand this idea seed into a comprehensive expanded idea:\n\n{idea_seed}"
            
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt_text.replace('{idea_seed}', idea_seed)}
            ]
            
            response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, max_tokens=2000)
            
            if response and 'content' in response:
                expanded_idea = response['content']
                
                # Save to database
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        UPDATE post_development 
                        SET expanded_idea = %s, updated_at = %s
                        WHERE post_id = %s
                    """, (expanded_idea, datetime.now(), post_id))
                
                return jsonify({
                    'success': True,
                    'expanded_idea': expanded_idea
                })
            else:
                return jsonify({'error': 'Failed to generate expanded idea'}), 500
                
        except Exception as e:
            logger.error(f"Error generating expanded idea: {e}")
            return jsonify({'error': str(e)}), 500

def api_posts_idea_seed(post_id):
    """Get or set idea seed for a post"""
    if request.method == 'GET':
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT idea_seed
                    FROM post_development 
                    WHERE post_id = %s
                """, (post_id,))
                
                result = cursor.fetchone()
                
                if result:
                    return jsonify({
                        'success': True,
                        'idea_seed': result['idea_seed']
                    })
                else:
                    return jsonify({
                        'success': True,
                        'idea_seed': None
                    })
                    
        except Exception as e:
            logger.error(f"Error fetching idea seed: {e}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            idea_seed = data.get('idea_seed', '')
            
            if not idea_seed:
                return jsonify({'error': 'Idea seed is required'}), 400
            
            # Save to database
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE post_development 
                    SET idea_seed = %s, updated_at = %s
                    WHERE post_id = %s
                """, (idea_seed, datetime.now(), post_id))
            
            return jsonify({
                'success': True,
                'idea_seed': idea_seed
            })
                
        except Exception as e:
            logger.error(f"Error saving idea seed: {e}")
            return jsonify({'error': str(e)}), 500

def api_check_topic():
    """Check if a topic has already been used this year"""
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        year = data.get('year', datetime.now().year)
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Check if this topic exists in post_development for this year
            cursor.execute("""
                SELECT pd.post_id, pd.idea_seed, p.created_at
                FROM post_development pd
                JOIN post p ON pd.post_id = p.id
                WHERE pd.idea_seed ILIKE %s 
                AND EXTRACT(YEAR FROM p.created_at) = %s
                ORDER BY p.created_at DESC
                LIMIT 1
            """, (f'%{topic}%', year))
            
            result = cursor.fetchone()
            
            if result:
                return jsonify({
                    'success': True,
                    'topic_exists': True,
                    'existing_post_id': result['post_id'],
                    'idea_seed': result['idea_seed']
                })
            else:
                return jsonify({
                    'success': True,
                    'topic_exists': False
                })
                
    except Exception as e:
        logger.error(f"Error checking topic: {e}")
        return jsonify({'error': str(e)}), 500

def api_create_new_post():
    """Create a new post"""
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Generate unique slug from topic
            base_slug = topic.lower().replace(' ', '-').replace('_', '-')
            base_slug = ''.join(c for c in base_slug if c.isalnum() or c == '-')
            
            # Make slug unique by adding timestamp
            import time
            unique_slug = f"{base_slug}-{int(time.time())}"
            
            # Insert new post
            cursor.execute("""
                INSERT INTO post (title, slug, created_at, updated_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (topic, unique_slug, datetime.now(), datetime.now()))
            
            post_id = cursor.fetchone()['id']
            
            # Insert post_development record
            cursor.execute("""
                INSERT INTO post_development (post_id, idea_seed)
                VALUES (%s, %s)
            """, (post_id, topic))
            
            return jsonify({
                'success': True,
                'post_id': post_id,
                'topic': topic
            })
            
    except Exception as e:
        logger.error(f"Error creating new post: {e}")
        return jsonify({'error': str(e)}), 500

def api_posts_idea_scope(post_id):
    """Get or set idea scope for a post"""
    if request.method == 'GET':
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT idea_scope
                    FROM post_development 
                    WHERE post_id = %s
                """, (post_id,))
                
                result = cursor.fetchone()
                
                if result:
                    # Parse JSON string if it exists
                    idea_scope = result['idea_scope']
                    if idea_scope and isinstance(idea_scope, str):
                        try:
                            idea_scope = json.loads(idea_scope)
                        except json.JSONDecodeError:
                            # If parsing fails, return as string
                            pass
                    
                    return jsonify({
                        'success': True,
                        'idea_scope': idea_scope
                    })
                else:
                    return jsonify({
                        'success': True,
                        'idea_scope': None
                    })
                    
        except Exception as e:
            logger.error(f"Error fetching idea scope: {e}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Handle both 'topics' and 'idea_scope' formats for backward compatibility
            if 'topics' in data:
                # Format topics as JSON for storage (brainstorm page format)
                topics = data.get('topics', [])
                if not topics:
                    return jsonify({'error': 'No topics provided'}), 400
                
                idea_scope_data = {
                    'generated_topics': topics,
                    'generated_at': datetime.now().isoformat(),
                    'total_count': len(topics)
                }
                idea_scope_json = json.dumps(idea_scope_data)
                
            elif 'idea_scope' in data:
                # Direct idea_scope format
                idea_scope_json = data.get('idea_scope', '')
                if not idea_scope_json:
                    return jsonify({'error': 'Idea scope is required'}), 400
            else:
                return jsonify({'error': 'Either topics or idea_scope is required'}), 400
            
            # Save to database
            with db_manager.get_cursor() as cursor:
                # Check if post_development record exists
                cursor.execute("SELECT id FROM post_development WHERE post_id = %s", (post_id,))
                if not cursor.fetchone():
                    # Create post_development record if it doesn't exist
                    cursor.execute("""
                        INSERT INTO post_development (post_id, idea_scope, created_at, updated_at)
                        VALUES (%s, %s, NOW(), NOW())
                    """, (post_id, idea_scope_json))
                else:
                    # Update existing record
                    cursor.execute("""
                        UPDATE post_development 
                        SET idea_scope = %s, updated_at = NOW()
                        WHERE post_id = %s
                    """, (idea_scope_json, post_id))
            
            return jsonify({
                'success': True,
                'message': 'Topics saved successfully' if 'topics' in data else 'Idea scope updated successfully'
            })
                
        except Exception as e:
            logger.error(f"Error saving idea scope: {e}")
            return jsonify({'error': str(e)}), 500
