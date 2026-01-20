"""
Research API Blueprint
Handles research-related API endpoints for background research system.
"""

from flask import Blueprint, jsonify, request
import logging
import json
from datetime import datetime
from config.database import db_manager
from utils.taxonomy_helpers import get_post_type
from config.research_topics import get_research_topics_for_post_type, get_research_topic_by_key
from utils.research_agents import WebResearcher, SourceEvaluator, FactExtractor, ContentSynthesizer

bp = Blueprint('research_api', __name__)
logger = logging.getLogger(__name__)

# Import LLM service (prefer planning_llm which has the right signature)
try:
    from blueprints.planning_llm import LLMService
except ImportError:
    try:
        from blueprints.header import LLMService
    except ImportError:
        from modules.llm_service import LLMService


@bp.route('/api/posts/<int:post_id>/research/topics', methods=['GET'])
def get_research_topics(post_id):
    """Get available research topics for this post type."""
    try:
        post_type = get_post_type(post_id)
        topics = get_research_topics_for_post_type(post_type)
        
        return jsonify({
            'success': True,
            'post_type': post_type,
            'topics': topics
        })
    except Exception as e:
        logger.error(f"Error getting research topics for post {post_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/posts/<int:post_id>/research/status', methods=['GET'])
def get_research_status(post_id):
    """Get research status for all topics."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT recipe_research FROM post_development WHERE post_id = %s
            """, (post_id,))
            dev_data = cursor.fetchone()
            
            post_type = get_post_type(post_id)
            topics_config = get_research_topics_for_post_type(post_type)
            
            if not dev_data or not dev_data.get('recipe_research'):
                # Initialize research structure with all topics
                research_data = {
                    'background_research': {
                        'topics': [
                            {
                                'key': topic['key'],
                                'label': topic['label'],
                                'status': 'pending',
                                'research_query': None,
                                'sources': [],
                                'extracted_facts': {},
                                'synthesized_content': None,
                                'error_message': None,
                                'created_at': None,
                                'updated_at': None,
                                'completed_at': None
                            }
                            for topic in topics_config
                        ],
                        'synthesized_background': None,
                        'last_updated': None
                    }
                }
                
                return jsonify({
                    'success': True,
                    'research_data': research_data,
                    'initialized': True
                })
            
            research_data = dev_data['recipe_research']
            if isinstance(research_data, str):
                research_data = json.loads(research_data)
            
            # Ensure all topics from config are present (add missing ones)
            if 'background_research' not in research_data:
                research_data['background_research'] = {'topics': []}
            
            existing_topic_keys = {t.get('key') for t in research_data['background_research'].get('topics', [])}
            for topic_config in topics_config:
                if topic_config['key'] not in existing_topic_keys:
                    # Add missing topic
                    research_data['background_research']['topics'].append({
                        'key': topic_config['key'],
                        'label': topic_config['label'],
                        'status': 'pending',
                        'research_query': None,
                        'sources': [],
                        'extracted_facts': {},
                        'synthesized_content': None,
                        'error_message': None,
                        'created_at': None,
                        'updated_at': None,
                        'completed_at': None
                    })
            
            # Check for stuck "researching" states and reset them
            stuck_topics_reset = False
            if 'background_research' in research_data and 'topics' in research_data['background_research']:
                now = datetime.now()
                for topic in research_data['background_research']['topics']:
                    if topic.get('status') == 'researching':
                        updated_at_str = topic.get('updated_at')
                        if updated_at_str:
                            try:
                                # Parse ISO format datetime (handle both with and without timezone)
                                if 'Z' in updated_at_str:
                                    updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00')).replace(tzinfo=None)
                                elif '+' in updated_at_str or (updated_at_str.count('-') > 2 and 'T' in updated_at_str):
                                    # Has timezone info
                                    updated_at = datetime.fromisoformat(updated_at_str).replace(tzinfo=None)
                                else:
                                    # No timezone, parse directly
                                    updated_at = datetime.fromisoformat(updated_at_str)
                                
                                # If it's been researching for more than 10 minutes, reset to pending
                                elapsed = (now - updated_at).total_seconds()
                                if elapsed > 600:  # 10 minutes
                                    logger.warning(f"Resetting stuck research topic {topic.get('key')} to pending (elapsed: {elapsed:.0f}s)")
                                    topic['status'] = 'pending'
                                    topic['error_message'] = 'Previous research attempt appears to have failed. Please try again.'
                                    topic['updated_at'] = datetime.now().isoformat()
                                    stuck_topics_reset = True
                            except Exception as e:
                                logger.warning(f"Error parsing updated_at for topic {topic.get('key')}: {e}")
                                # If we can't parse the date, reset to pending
                                topic['status'] = 'pending'
                                topic['updated_at'] = datetime.now().isoformat()
                                stuck_topics_reset = True
                        else:
                            # No updated_at, assume stuck and reset
                            topic['status'] = 'pending'
                            topic['updated_at'] = datetime.now().isoformat()
                            stuck_topics_reset = True
            
            # Save reset state back to database if we reset any topics
            if stuck_topics_reset:
                try:
                    cursor.execute("""
                        SELECT id FROM post_development WHERE post_id = %s
                    """, (post_id,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        cursor.execute("""
                            UPDATE post_development
                            SET recipe_research = %s
                            WHERE post_id = %s
                        """, (json.dumps(research_data), post_id))
                    else:
                        cursor.execute("""
                            INSERT INTO post_development (post_id, recipe_research)
                            VALUES (%s, %s)
                        """, (post_id, json.dumps(research_data)))
                    cursor.connection.commit()
                    logger.info(f"Reset stuck research topics for post {post_id}")
                except Exception as e:
                    logger.error(f"Error saving reset research state: {e}")
            
            return jsonify({
                'success': True,
                'research_data': research_data,
                'initialized': False
            })
            
    except Exception as e:
        logger.error(f"Error getting research status for post {post_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/posts/<int:post_id>/research/<topic_key>/start', methods=['POST'])
def start_research(post_id, topic_key):
    """Start research for a specific topic."""
    try:
        post_type = get_post_type(post_id)
        topic_config = get_research_topic_by_key(post_type, topic_key)
        
        if not topic_config:
            return jsonify({'error': f'Research topic "{topic_key}" not found for post type "{post_type}"'}), 404
        
        # Get post/item name for query generation
        with db_manager.get_cursor() as cursor:
            if post_type == 'recipe':
                cursor.execute("""
                    SELECT cr.recipe_title, p.title
                    FROM post p
                    LEFT JOIN calendar_recipes cr ON cr.id = p.recipe_id
                    WHERE p.id = %s
                """, (post_id,))
                post_data = cursor.fetchone()
                item_name = post_data.get('recipe_title') or post_data.get('title', '')
            else:
                cursor.execute("""
                    SELECT title FROM post WHERE id = %s
                """, (post_id,))
                post_data = cursor.fetchone()
                item_name = post_data.get('title', '') if post_data else ''
        
        # Generate research query
        research_query = topic_config['search_template'].format(item_name=item_name)
        
        # Initialize research structure if needed
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT recipe_research FROM post_development WHERE post_id = %s
            """, (post_id,))
            dev_data = cursor.fetchone()
            
            research_data = {}
            if dev_data and dev_data.get('recipe_research'):
                research_data = dev_data['recipe_research']
                if isinstance(research_data, str):
                    research_data = json.loads(research_data)
            else:
                # Initialize structure
                topics = get_research_topics_for_post_type(post_type)
                research_data = {
                    'background_research': {
                        'topics': [
                            {
                                'key': t['key'],
                                'label': t['label'],
                                'status': 'pending',
                                'research_query': None,
                                'sources': [],
                                'extracted_facts': {},
                                'synthesized_content': None,
                                'error_message': None,
                                'created_at': None,
                                'updated_at': None,
                                'completed_at': None
                            }
                            for t in topics
                        ]
                    }
                }
            
            # Update topic status
            if 'background_research' not in research_data:
                research_data['background_research'] = {'topics': []}
            
            topic_found = False
            for topic in research_data['background_research']['topics']:
                if topic['key'] == topic_key:
                    # Reset topic for re-run (clear previous results)
                    topic['status'] = 'researching'
                    topic['research_query'] = research_query
                    topic['created_at'] = datetime.now().isoformat()
                    topic['updated_at'] = datetime.now().isoformat()
                    topic['completed_at'] = None
                    topic['error_message'] = None
                    # Keep sources and facts for now (will be overwritten on completion)
                    topic_found = True
                    break
            
            if not topic_found:
                research_data['background_research']['topics'].append({
                    'key': topic_key,
                    'label': topic_config['label'],
                    'status': 'researching',
                    'research_query': research_query,
                    'sources': [],
                    'extracted_facts': {},
                    'synthesized_content': None,
                    'error_message': None,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'completed_at': None
                })
            
            # Save to database
            cursor.execute("""
                SELECT id FROM post_development WHERE post_id = %s
            """, (post_id,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE post_development
                    SET recipe_research = %s
                    WHERE post_id = %s
                """, (json.dumps(research_data), post_id))
            else:
                cursor.execute("""
                    INSERT INTO post_development (post_id, recipe_research)
                    VALUES (%s, %s)
                """, (post_id, json.dumps(research_data)))
            
            cursor.connection.commit()
        
        # Start research process (async - return immediately)
        # Research will be performed in background
        # For now, return status update
        
        return jsonify({
            'success': True,
            'topic_key': topic_key,
            'research_query': research_query,
            'status': 'researching',
            'message': 'Research started. This may take a few minutes.'
        })
        
    except Exception as e:
        logger.error(f"Error starting research for post {post_id}, topic {topic_key}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/posts/<int:post_id>/research/<topic_key>/execute', methods=['POST'])
def execute_research(post_id, topic_key):
    """Execute the full research process for a topic (web search, fact extraction, synthesis)."""
    import time
    
    logger.info(f"[Research] Starting research execution for post {post_id}, topic {topic_key}")
    
    # Track execution start time for timeout
    start_time = time.time()
    timeout_seconds = 300  # 5 minutes (increased for multiple sources + LLM calls)
    
    def check_timeout():
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            logger.error(f"[Research] Timeout after {elapsed:.1f} seconds")
            raise TimeoutError(f"Research execution timed out after {timeout_seconds} seconds")
        logger.debug(f"[Research] Elapsed time: {elapsed:.1f}s / {timeout_seconds}s")
    
    try:
        post_type = get_post_type(post_id)
        topic_config = get_research_topic_by_key(post_type, topic_key)
        
        if not topic_config:
            return jsonify({'error': f'Research topic "{topic_key}" not found'}), 404
        
        # Get item name
        with db_manager.get_cursor() as cursor:
            if post_type == 'recipe':
                cursor.execute("""
                    SELECT cr.recipe_title, p.title
                    FROM post p
                    LEFT JOIN calendar_recipes cr ON cr.id = p.recipe_id
                    WHERE p.id = %s
                """, (post_id,))
                post_data = cursor.fetchone()
                item_name = post_data.get('recipe_title') or post_data.get('title', '')
            else:
                cursor.execute("""
                    SELECT title FROM post WHERE id = %s
                """, (post_id,))
                post_data = cursor.fetchone()
                item_name = post_data.get('title', '') if post_data else ''
        
        # Generate research query
        research_query = topic_config['search_template'].format(item_name=item_name)
        
        # Initialize research agents
        web_researcher = WebResearcher()
        source_evaluator = SourceEvaluator()
        llm_service = LLMService()
        # Pass post_id to agents for intercept_context if needed
        fact_extractor = FactExtractor(llm_service, post_id=post_id)
        content_synthesizer = ContentSynthesizer(llm_service, post_id=post_id)
        
        # Step 1: Web search
        logger.info(f"[Research] Step 1/6: Searching for: {research_query}")
        check_timeout()
        search_results = web_researcher.search(research_query, max_results=10)
        
        if not search_results:
            raise Exception("No search results found for query: " + research_query)
        
        logger.info(f"[Research] Step 2/6: Found {len(search_results)} search results")
        
        # Step 2: Prioritize sources
        check_timeout()
        prioritized_results = source_evaluator.prioritize_sources(search_results)
        
        # Step 3: Filter to top 3-5 most reliable sources (reduced to speed up)
        top_sources = prioritized_results[:5]
        logger.info(f"[Research] Step 3/6: Processing top {len(top_sources)} sources")
        
        # Step 4: Fetch content from top sources
        sources_with_content = []
        all_extracted_facts = {
            'dates': [],
            'locations': [],
            'events': [],
            'people': [],
            'cultural_notes': [],
            'uncertainties': [],
            'conflicts': [],
            'quotations': []
        }
        
        for i, source in enumerate(top_sources, 1):
            try:
                check_timeout()
                url = source['url']
                logger.info(f"[Research] Step 4/6: Fetching source {i}/{len(top_sources)}: {url}")
                content = web_researcher.fetch_content(url)
                
                if content and len(content) > 100:
                    # Evaluate source
                    evaluation = source_evaluator.evaluate_reliability(url)
                    
                    # Extract facts from content (limit content size to avoid long LLM processing)
                    logger.info(f"[Research] Extracting facts from source {i} (content length: {len(content)})...")
                    # Limit content to first 3000 chars to speed up processing
                    content_to_analyze = content[:3000] if len(content) > 3000 else content
                    check_timeout()
                    facts = fact_extractor.extract_facts(
                        content_to_analyze,
                        topic_config['label'],
                        item_name,
                        topic_key=topic_key
                    )
                    logger.info(f"[Research] Extracted facts from source {i}: {sum(len(facts.get(k, [])) for k in facts)} total facts")
                    
                    # Merge facts
                    for key in all_extracted_facts:
                        if key in facts:
                            all_extracted_facts[key].extend(facts[key])
                    
                    sources_with_content.append({
                        'title': source.get('title', ''),
                        'url': url,
                        'domain': evaluation['domain'],
                        'domain_tier': evaluation['tier'],
                        'reliability': evaluation['reliability'],
                        'reliability_score': evaluation['reliability_score'],
                        'is_academic': evaluation['is_academic'],
                        'content_length': len(content),
                        'facts_count': sum(len(facts.get(k, [])) for k in facts)
                    })
                    
                    logger.info(f"[Research] Source {i} processed: {len(sources_with_content)} sources with content so far")
                    
                    # Limit to 3 sources with content (reduced to speed up)
                    if len(sources_with_content) >= 3:
                        logger.info(f"[Research] Reached limit of 3 sources, stopping")
                        break
                        
            except TimeoutError:
                raise
            except Exception as e:
                logger.warning(f"Error processing source {source.get('url', '')}: {e}")
                continue
        
        if not sources_with_content:
            raise Exception("No sources with usable content found")
        
        logger.info(f"[Research] Step 5/6: Deduplicating facts from {len(sources_with_content)} sources")
        check_timeout()
        
        # Step 5: Deduplicate facts
        all_extracted_facts = fact_extractor._deduplicate_facts(all_extracted_facts)
        
        logger.info(f"[Research] Step 6/6: Synthesizing content...")
        check_timeout()
        
        # Step 6: Synthesize content
        synthesized_content = content_synthesizer.synthesize_paragraph(
            all_extracted_facts,
            topic_config['label'],
            item_name,
            sources_with_content,
            word_target=topic_config.get('word_target', 150),
            topic_key=topic_key,
            focus_areas=topic_config.get('focus_areas', [])
        )
        
        logger.info(f"[Research] Research complete for topic {topic_key}")
        
        # Step 7: Update database
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT recipe_research FROM post_development WHERE post_id = %s
            """, (post_id,))
            dev_data = cursor.fetchone()
            
            research_data = {}
            if dev_data and dev_data.get('recipe_research'):
                research_data = dev_data['recipe_research']
                if isinstance(research_data, str):
                    research_data = json.loads(research_data)
            
            if 'background_research' not in research_data:
                research_data['background_research'] = {'topics': []}
            
            # Update topic
            topic_found = False
            for topic in research_data['background_research']['topics']:
                if topic['key'] == topic_key:
                    topic['status'] = 'completed'
                    topic['sources'] = sources_with_content
                    topic['extracted_facts'] = all_extracted_facts
                    topic['synthesized_content'] = synthesized_content
                    topic['updated_at'] = datetime.now().isoformat()
                    topic['completed_at'] = datetime.now().isoformat()
                    topic['error_message'] = None
                    topic_found = True
                    break
            
            if not topic_found:
                research_data['background_research']['topics'].append({
                    'key': topic_key,
                    'label': topic_config['label'],
                    'status': 'completed',
                    'research_query': research_query,
                    'sources': sources_with_content,
                    'extracted_facts': all_extracted_facts,
                    'synthesized_content': synthesized_content,
                    'error_message': None,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'completed_at': datetime.now().isoformat()
                })
            
            research_data['background_research']['last_updated'] = datetime.now().isoformat()
            
            # Save
            cursor.execute("""
                SELECT id FROM post_development WHERE post_id = %s
            """, (post_id,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE post_development
                    SET recipe_research = %s
                    WHERE post_id = %s
                """, (json.dumps(research_data), post_id))
            else:
                cursor.execute("""
                    INSERT INTO post_development (post_id, recipe_research)
                    VALUES (%s, %s)
                """, (post_id, json.dumps(research_data)))
            
            cursor.connection.commit()
        
        return jsonify({
            'success': True,
            'topic_key': topic_key,
            'status': 'completed',
            'sources_count': len(sources_with_content),
            'facts_count': sum(len(all_extracted_facts.get(k, [])) for k in all_extracted_facts),
            'synthesized_content': synthesized_content
        })
        
    except TimeoutError as e:
        logger.error(f"Research timeout for post {post_id}, topic {topic_key}: {e}")
        # Update status to failed
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT recipe_research FROM post_development WHERE post_id = %s
                """, (post_id,))
                dev_data = cursor.fetchone()
                
                if dev_data and dev_data.get('recipe_research'):
                    research_data = dev_data['recipe_research']
                    if isinstance(research_data, str):
                        research_data = json.loads(research_data)
                    
                    if 'background_research' in research_data:
                        for topic in research_data['background_research']['topics']:
                            if topic['key'] == topic_key:
                                topic['status'] = 'failed'
                                topic['error_message'] = f'Research timed out after {timeout_seconds} seconds. Please try again.'
                                topic['updated_at'] = datetime.now().isoformat()
                                break
                        
                        cursor.execute("""
                            UPDATE post_development
                            SET recipe_research = %s
                            WHERE post_id = %s
                        """, (json.dumps(research_data), post_id))
                        cursor.connection.commit()
        except:
            pass
        
        return jsonify({'error': f'Research timed out after {timeout_seconds} seconds. Please try again.'}), 504
        
    except Exception as e:
        logger.error(f"Error executing research for post {post_id}, topic {topic_key}: {e}")
        import traceback
        traceback.print_exc()
        
        # Update status to failed
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT recipe_research FROM post_development WHERE post_id = %s
                """, (post_id,))
                dev_data = cursor.fetchone()
                
                if dev_data and dev_data.get('recipe_research'):
                    research_data = dev_data['recipe_research']
                    if isinstance(research_data, str):
                        research_data = json.loads(research_data)
                    
                    if 'background_research' in research_data:
                        for topic in research_data['background_research']['topics']:
                            if topic['key'] == topic_key:
                                topic['status'] = 'failed'
                                topic['error_message'] = str(e)
                                topic['updated_at'] = datetime.now().isoformat()
                                break
                        
                        cursor.execute("""
                            UPDATE post_development
                            SET recipe_research = %s
                            WHERE post_id = %s
                        """, (json.dumps(research_data), post_id))
                        cursor.connection.commit()
        except:
            pass
        
        return jsonify({'error': str(e)}), 500


@bp.route('/api/posts/<int:post_id>/research/<topic_key>/results', methods=['GET'])
def get_research_results(post_id, topic_key):
    """Get research results for a specific topic."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT recipe_research FROM post_development WHERE post_id = %s
            """, (post_id,))
            dev_data = cursor.fetchone()
            
            if not dev_data or not dev_data.get('recipe_research'):
                return jsonify({'error': 'No research data found'}), 404
            
            research_data = dev_data['recipe_research']
            if isinstance(research_data, str):
                research_data = json.loads(research_data)
            
            if 'background_research' not in research_data:
                return jsonify({'error': 'No background research data found'}), 404
            
            # Find topic
            for topic in research_data['background_research']['topics']:
                if topic['key'] == topic_key:
                    return jsonify({
                        'success': True,
                        'topic': topic
                    })
            
            return jsonify({'error': f'Topic "{topic_key}" not found'}), 404
            
    except Exception as e:
        logger.error(f"Error getting research results for post {post_id}, topic {topic_key}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
