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
            # CRITICAL: Read year/week from query parameters to get expanded idea for the CORRECT week
            url_year = request.args.get('year', type=int)
            url_week = request.args.get('week', type=int)
            
            # If week context is provided, fetch expanded idea for that week's selected theme/post
            if url_year and url_week:
                with db_manager.get_cursor() as cursor:
                    # STEP 1: Try to find a post directly scheduled for this week with a theme
                    cursor.execute("""
                        SELECT cs.post_id, pd.expanded_idea, ci.idea_title, ci.id as theme_id
                        FROM calendar_schedule cs
                        LEFT JOIN post_development pd ON cs.post_id = pd.post_id
                        LEFT JOIN calendar_ideas ci ON cs.idea_id = ci.id
                        WHERE cs.year = %s 
                          AND cs.week_number = %s
                          AND cs.post_id IS NOT NULL
                          AND ci.item_classification = 'theme'
                          AND pd.expanded_idea IS NOT NULL
                          AND pd.expanded_idea != ''
                        ORDER BY cs.created_at DESC
                        LIMIT 1
                    """, (url_year, url_week))
                    
                    week_result = cursor.fetchone()
                    
                    if week_result and week_result['expanded_idea']:
                        logger.info(f"Found expanded idea for week {url_year}/{url_week}: post {week_result['post_id']}, theme: {week_result['idea_title']}")
                        return jsonify({
                            'success': True,
                            'expanded_idea': week_result['expanded_idea']
                        })
                    
                    # STEP 2: If no post scheduled for this week, find the theme for this week and look for ANY post with that theme
                    cursor.execute("""
                        SELECT ci.id as theme_id, ci.idea_title as theme_title
                        FROM calendar_schedule cs
                        JOIN calendar_ideas ci ON cs.idea_id = ci.id
                        WHERE cs.year = %s 
                          AND cs.week_number = %s
                          AND ci.item_classification = 'theme'
                        ORDER BY cs.created_at DESC
                        LIMIT 1
                    """, (url_year, url_week))
                    
                    week_theme = cursor.fetchone()
                    
                    if week_theme:
                        logger.info(f"Week {url_year}/{url_week} has theme: {week_theme['theme_title']} (ID: {week_theme['theme_id']})")
                        
                        # Now find any post that has this theme scheduled (regardless of which week) and has an expanded_idea
                        cursor.execute("""
                            SELECT cs2.post_id, pd.expanded_idea, ci2.idea_title
                            FROM calendar_schedule cs2
                            LEFT JOIN post_development pd ON cs2.post_id = pd.post_id
                            LEFT JOIN calendar_ideas ci2 ON cs2.idea_id = ci2.id
                            WHERE cs2.idea_id = %s
                              AND cs2.post_id IS NOT NULL
                              AND pd.expanded_idea IS NOT NULL
                              AND pd.expanded_idea != ''
                            ORDER BY cs2.created_at DESC
                            LIMIT 1
                        """, (week_theme['theme_id'],))
                        
                        theme_post_result = cursor.fetchone()
                        
                        if theme_post_result and theme_post_result['expanded_idea']:
                            logger.info(f"Found expanded idea for theme '{week_theme['theme_title']}': post {theme_post_result['post_id']}")
                            return jsonify({
                                'success': True,
                                'expanded_idea': theme_post_result['expanded_idea']
                            })
                    
                    logger.warn(f"No expanded idea found for week {url_year}/{url_week}")
            
            # Fallback: fetch expanded idea for the requested post_id (original behavior)
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
            # Get selected theme with full details (Title, Description, Important Notes)
            selected_theme = None
            with db_manager.get_cursor() as cursor:
                # Try to get schedule by post_id first
                cursor.execute("""
                    SELECT cs.idea_id, cs.year, cs.week_number
                    FROM calendar_schedule cs
                    WHERE cs.post_id = %s
                    ORDER BY cs.created_at DESC
                    LIMIT 1
                """, (post_id,))
                schedule = cursor.fetchone()
                
                # If no schedule found by post_id with idea_id, try to get post's year/week
                # and look up schedule by year/week instead (theme might be selected before post is created)
                if not schedule or not schedule.get('idea_id'):
                    # Get post's scheduled week/year from calendar_schedule
                    cursor.execute("""
                        SELECT year, week_number
                        FROM calendar_schedule
                        WHERE post_id = %s
                        LIMIT 1
                    """, (post_id,))
                    post_schedule = cursor.fetchone()
                    
                    if post_schedule and post_schedule.get('year') and post_schedule.get('week_number'):
                        # Look up schedule by year/week (any schedule entry for that week with an idea_id)
                        cursor.execute("""
                            SELECT cs.idea_id, cs.year, cs.week_number
                            FROM calendar_schedule cs
                            WHERE cs.year = %s AND cs.week_number = %s AND cs.idea_id IS NOT NULL
                            ORDER BY cs.created_at DESC
                            LIMIT 1
                        """, (post_schedule['year'], post_schedule['week_number']))
                        week_schedule = cursor.fetchone()
                        
                        if week_schedule and week_schedule.get('idea_id'):
                            # Found theme for this week - update the post's schedule entry to link them
                            cursor.execute("""
                                UPDATE calendar_schedule
                                SET idea_id = %s, updated_at = NOW()
                                WHERE post_id = %s AND year = %s AND week_number = %s
                            """, (week_schedule['idea_id'], post_id, post_schedule['year'], post_schedule['week_number']))
                            schedule = week_schedule
                
                if not schedule or not schedule.get('idea_id'):
                    return jsonify({'error': 'No selected theme found for this post. Please select a theme in the calendar week view.'}), 400
                
                idea_id = schedule['idea_id']
                
                # Check if important_notes column exists
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'calendar_ideas' AND column_name = 'important_notes'
                """)
                has_important_notes = cursor.fetchone() is not None
                
                # Fetch full theme data
                important_notes_field = 'ci.important_notes' if has_important_notes else "'[]'::jsonb as important_notes"
                cursor.execute(f"""
                    SELECT ci.idea_title, ci.idea_description, {important_notes_field}
                    FROM calendar_ideas ci
                    WHERE ci.id = %s
                """, (idea_id,))
                theme_data = cursor.fetchone()
                
                if not theme_data:
                    return jsonify({'error': 'Selected theme not found in database'}), 404
                
                selected_theme = {
                    'title': theme_data.get('idea_title') or '',
                    'description': theme_data.get('idea_description') or '',
                    'important_notes': []
                }
                
                if has_important_notes and theme_data.get('important_notes'):
                    import json
                    notes_data = theme_data['important_notes']
                    if isinstance(notes_data, (list, dict)):
                        selected_theme['important_notes'] = notes_data if isinstance(notes_data, list) else [notes_data]
                    elif isinstance(notes_data, str):
                        selected_theme['important_notes'] = json.loads(notes_data)
            
            # Generate expanded idea using LLM
            llm_service = LLMService()
            
            # Load prompt from database
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT system_prompt, prompt_text
                    FROM llm_prompt 
                    WHERE name ILIKE '%idea%expansion%' OR name ILIKE '%scottish%idea%'
                    ORDER BY id DESC
                    LIMIT 1
                """)
                prompt_data = cursor.fetchone()
                
                if prompt_data:
                    system_prompt = prompt_data['system_prompt']
                    prompt_text = prompt_data['prompt_text']
                else:
                    # Fallback prompts
                    system_prompt = "You are an expert content creator specializing in Scottish and Celtic history and culture. Expand the given theme into a comprehensive, engaging expanded idea that can be developed into a full blog post."
                    prompt_text = "Expand this theme into a comprehensive expanded idea:\n\n[theme_data]"
            
            # Build theme content string to replace [data:idea_seed] or [theme_data]
            theme_content = f"Title: {selected_theme['title']}\n\n"
            if selected_theme['description']:
                theme_content += f"Description: {selected_theme['description']}\n\n"
            
            # Add Important Notes if they exist - HIGHLIGHTED as CRITICAL AND MANDATORY
            if selected_theme['important_notes'] and len(selected_theme['important_notes']) > 0:
                theme_content += "\n\n"
                theme_content += "=" * 70 + "\n"
                theme_content += "⚠️  CRITICAL: IMPORTANT NOTES - MANDATORY REQUIREMENTS ⚠️\n"
                theme_content += "=" * 70 + "\n"
                theme_content += "\n"
                theme_content += "EACH OF THE FOLLOWING NOTES REPRESENTS A MANDATORY TOPIC THAT MUST BE EXPLICITLY INCLUDED.\n"
                theme_content += "YOU CANNOT SKIP, OMIT, OR GLOSS OVER ANY OF THESE - EACH MUST BE EXPLICITLY MENTIONED.\n"
                theme_content += "IF A NOTE SAYS 'Mention X', YOU MUST EXPLICITLY MENTION X IN YOUR RESPONSE.\n"
                theme_content += "\n"
                for i, note in enumerate(selected_theme['important_notes'], 1):
                    note_text = note.get('text', '') if isinstance(note, dict) else str(note)
                    if note_text:
                        theme_content += f"⚠️  MANDATORY NOTE #{i}: {note_text}\n"
                        theme_content += f"   → THIS TOPIC/POINT MUST BE EXPLICITLY AND CLEARLY MENTIONED IN YOUR EXPANDED IDEA\n"
                        theme_content += f"   → DO NOT ALLUDE TO IT - YOU MUST EXPLICITLY INCLUDE IT\n\n"
                theme_content += "=" * 70 + "\n"
                theme_content += "⚠️  FINAL REMINDER: Every single Important Note above is MANDATORY.\n"
                theme_content += "⚠️  You must explicitly address each one - no exceptions.\n"
                theme_content += "⚠️  If you fail to explicitly mention all Important Notes, your response is incomplete.\n"
                theme_content += "=" * 70 + "\n\n"
            
            # Replace placeholder in prompt (handle both old and new formats)
            user_prompt = prompt_text.replace('[data:idea_seed]', theme_content).replace('{idea_seed}', theme_content).replace('[theme_data]', theme_content)
            
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
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
