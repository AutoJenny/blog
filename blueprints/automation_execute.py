"""
Automation Execution Functions
Helper functions for executing automation substages
"""

import json
import logging
from config.database import db_manager

logger = logging.getLogger(__name__)

def execute_topic_allocation(post_id, data):
    """Execute topic allocation for a post using the same logic as template page"""
    try:
        # Get post data - need section structure for generating section-specific topics
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.title, pd.section_structure, pd.expanded_idea
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
            if not post:
                return {"success": False, "error": "Post not found"}, 404
            
        if not post['section_structure']:
            return {"success": False, "error": "No section structure found. Please run Section Structure first."}, 400
            
        # Call the unified section-specific topic generation API
        from blueprints.planning_api_topic_allocation import api_generate_section_specific_topics
        
        # Create a mock request object with the required data
        class MockRequest:
            def get_json(self):
                return {'post_id': post_id}
        
        # Temporarily replace the global request object
        import flask
        original_request = flask.request
        flask.request = MockRequest()
        
        try:
            # Call the unified section-specific topic generation API
            result = api_generate_section_specific_topics()
            
            # Handle Flask response
            if isinstance(result, tuple):
                status_code, result_data = result
                if status_code != 200:
                    return {
                        'success': False,
                        'error': result_data.get('error', 'Failed to generate section-specific topics')
                    }, status_code
                # If status is 200, result_data is the Flask response object
                result_data = result_data.get_json() if hasattr(result_data, 'get_json') else result_data
            else:
                # Direct response object
                result_data = result.get_json() if hasattr(result, 'get_json') else result
            
            return result_data
            
        finally:
            # Restore original request object
            flask.request = original_request
            
    except Exception as e:
        logger.error(f"Error executing topic allocation: {e}")
        return {"success": False, "error": str(e)}, 500

def execute_section_titling(post_id, data):
    """Execute section titling for a post"""
    try:
        logger.info(f"Starting section titling for post {post_id}")
        
        # Get post data
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.title, pd.topic_allocation, pd.expanded_idea, pd.sections
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
            if not post:
                return {"success": False, "error": "Post not found"}, 404
        
        if not post['topic_allocation']:
            return {"success": False, "error": "No topic allocation found. Please run Topic Allocation first."}, 400
        
        # Parse topic allocation
        topic_allocation = post['topic_allocation']
        if isinstance(topic_allocation, str):
            topic_allocation = json.loads(topic_allocation)
        
        # Call the section titling API directly
        from blueprints.planning_titling import api_sections_title
        
        # Create mock request data
        class MockRequest:
            def get_json(self):
                return {
                    'topic_allocation': topic_allocation.get('allocations', []),
                    'expanded_idea': post['expanded_idea'],
                    'post_id': post_id
                }
        
        # Temporarily replace request object
        import flask
        original_request = flask.request
        flask.request = MockRequest()
        
        try:
            result = api_sections_title()
            
            # Handle Flask response
            if isinstance(result, tuple):
                response_obj, status_code = result
                if status_code != 200:
                    error_msg = "Unknown error"
                    if hasattr(response_obj, 'get_json'):
                        error_data = response_obj.get_json()
                        error_msg = error_data.get('error', 'Unknown error')
                    return {"success": False, "error": error_msg}, status_code
                
                # Success case
                result_data = response_obj.get_json()
                return result_data
            else:
                # Direct response object
                result_data = result.get_json()
                return result_data
                
        finally:
            # Restore original request object
            flask.request = original_request
            
    except Exception as e:
        logger.error(f"Error executing section titling: {e}")
        return {"success": False, "error": str(e)}, 500

def execute_topic_brainstorming(post_id, data):
    """Execute topic brainstorming for a post"""
    try:
        logger.info(f"Starting topic brainstorming for post {post_id}")
        
        # Get post data
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.title, pd.expanded_idea, pd.idea_scope
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
            if not post:
                return {"success": False, "error": "Post not found"}, 404
        
        if not post['expanded_idea']:
            return {"success": False, "error": "No expanded idea found. Please run idea expansion first."}, 400
        
        # Call the topic brainstorming API directly
        from blueprints.planning import api_posts_idea_scope
        
        # Create mock request data
        class MockRequest:
            def get_json(self):
                return {
                    'expanded_idea': post['expanded_idea'],
                    'post_id': post_id
                }
        
        # Temporarily replace request object
        import flask
        original_request = flask.request
        flask.request = MockRequest()
        
        try:
            result = api_posts_idea_scope()
            
            # Handle Flask response
            if isinstance(result, tuple):
                response_obj, status_code = result
                if status_code != 200:
                    error_msg = "Unknown error"
                    if hasattr(response_obj, 'get_json'):
                        error_data = response_obj.get_json()
                        error_msg = error_data.get('error', 'Unknown error')
                    return {"success": False, "error": error_msg}, status_code
                
                # Success case
                result_data = response_obj.get_json()
                return result_data
            else:
                # Direct response object
                result_data = result.get_json()
                return result_data
                
        finally:
            # Restore original request object
            flask.request = original_request
            
    except Exception as e:
        logger.error(f"Error executing topic brainstorming: {e}")
        return {"success": False, "error": str(e)}, 500

def execute_section_structure(post_id, data):
    """Execute section structure design for a post"""
    try:
        logger.info(f"Starting section structure design for post {post_id}")
        
        # Get post data
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.title, pd.expanded_idea, pd.section_structure
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
            if not post:
                return {"success": False, "error": "Post not found"}, 404
        
        if not post['expanded_idea']:
            return {"success": False, "error": "No expanded idea found. Please run idea expansion first."}, 400
        
        # Call the section structure API directly
        from blueprints.planning_sections import api_design_section_structure
        
        # Create mock request data
        class MockRequest:
            def get_json(self):
                return {
                    'expanded_idea': post['expanded_idea'],
                    'post_id': post_id
                }
        
        # Temporarily replace request object
        import flask
        original_request = flask.request
        flask.request = MockRequest()
        
        try:
            result = api_design_section_structure()
            
            # Handle Flask response
            if isinstance(result, tuple):
                response_obj, status_code = result
                if status_code != 200:
                    error_msg = "Unknown error"
                    if hasattr(response_obj, 'get_json'):
                        error_data = response_obj.get_json()
                        error_msg = error_data.get('error', 'Unknown error')
                    return {"success": False, "error": error_msg}, status_code
                
                # Success case
                result_data = response_obj.get_json()
                return result_data
            else:
                # Direct response object
                result_data = result.get_json()
                return result_data
                
        finally:
            # Restore original request object
            flask.request = original_request
            
    except Exception as e:
        logger.error(f"Error executing section structure: {e}")
        return {"success": False, "error": str(e)}, 500

def execute_author_first_drafts(post_id, data):
    """Execute author first drafts generation for all sections of a post"""
    try:
        logger.info(f"Starting author first drafts generation for post {post_id}")
        
        # Get all sections for this post
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description, status, draft
                FROM post_section
                WHERE post_id = %s 
                AND section_order <= 7
                ORDER BY section_order
            """, (post_id,))
            
            sections = cursor.fetchall()
            
            if not sections:
                return {"success": False, "error": "No sections found for this post"}, 404
        
        logger.info(f"Found {len(sections)} sections to generate drafts for")
        
        # Generate drafts for each section
        results = []
        success_count = 0
        
        for section in sections:
            section_id = section['id']
            section_title = section['section_heading']
            
            try:
                logger.info(f"Generating draft for section {section_id}: {section_title}")
                
                # Call the core LLM logic directly (same as authoring API)
                from blueprints.authoring import LLMService
                import json
                
                try:
                    # Get the LLM prompt for section drafting
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT system_prompt, prompt_text
                            FROM llm_prompt
                            WHERE name = 'Section Drafting'
                            ORDER BY id DESC
                            LIMIT 1
                        """)
                        prompt_data = cursor.fetchone()
                        
                        if not prompt_data:
                            raise Exception("Section Drafting prompt not found")
                    
                    # Get post development data for context
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT expanded_idea, topic_allocation, sections
                            FROM post_development
                            WHERE post_id = %s
                        """, (post_id,))
                        dev_data = cursor.fetchone()
                        
                        if not dev_data:
                            raise Exception("Post development data not found")
                    
                    # Prepare prompt variables
                    topic_allocation = dev_data['topic_allocation']
                    if isinstance(topic_allocation, str):
                        topic_allocation = json.loads(topic_allocation)
                    
                    # Find the section data
                    current_section_data = None
                    if topic_allocation and 'allocations' in topic_allocation:
                        for allocation in topic_allocation['allocations']:
                            if allocation.get('section_id') == f'section_{section["section_order"]}':
                                current_section_data = allocation
                                break
                    
                    if not current_section_data:
                        raise Exception(f"Section data not found for section {section['section_order']}")
                    
                    # Build prompt variables
                    prompt_vars = {
                        'SELECTED_IDEA': dev_data.get('expanded_idea', ''),
                        'EXPANDED_IDEA': dev_data.get('expanded_idea', ''),
                        'SECTION_TITLE': section['section_heading'],
                        'SECTION_SUBTITLE': section['section_description'] or '',
                        'SECTION_GROUP': current_section_data.get('section_theme', f'Section {section["section_order"]}'),
                        'GROUP_SUMMARY': current_section_data.get('section_description', ''),
                        'SECTION_TOPICS': ', '.join(current_section_data.get('topics', [])),
                        'AVOID_SECTIONS_DETAILED': ''  # Simplified for now
                    }
                    
                    # Replace placeholders in prompt
                    prompt_text = prompt_data['prompt_text']
                    for key, value in prompt_vars.items():
                        prompt_text = prompt_text.replace(f'[{key}]', str(value))
                    
                    # Call LLM service
                    messages = [
                        {'role': 'system', 'content': prompt_data['system_prompt']},
                        {'role': 'user', 'content': prompt_text}
                    ]
                    
                    llm_service = LLMService()
                    llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
                    
                    if llm_response and 'content' in llm_response:
                        draft_content = llm_response['content'].strip()
                        
                        # Save the draft content to database
                        with db_manager.get_cursor() as cursor:
                            cursor.execute("""
                                UPDATE post_section
                                SET draft = %s, status = 'complete'
                                WHERE id = %s
                            """, (draft_content, section_id))
                        
                        success_count += 1
                        results.append({
                            'section_id': section_id,
                            'section_title': section_title,
                            'success': True,
                            'draft_content': draft_content
                        })
                        logger.info(f"Successfully generated draft for section {section_id}")
                    else:
                        raise Exception("No content in LLM response")
                        
                except Exception as e:
                    results.append({
                        'section_id': section_id,
                        'section_title': section_title,
                        'success': False,
                        'error': str(e)
                    })
                    logger.error(f"Error generating draft for section {section_id}: {e}")
                    
            except Exception as e:
                logger.error(f"Error generating draft for section {section_id}: {e}")
                results.append({
                    'section_id': section_id,
                    'section_title': section_title,
                    'success': False,
                    'error': str(e)
                })
        
        # Update the authoring progress timestamp
        if success_count > 0:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE post_development 
                    SET updated_at = NOW()
                    WHERE post_id = %s
                """, (post_id,))
        
        logger.info(f"Author first drafts generation completed: {success_count}/{len(sections)} sections successful")
        
        return {
            'success': True,
            'total_sections': len(sections),
            'successful_sections': success_count,
            'failed_sections': len(sections) - success_count,
            'results': results,
            'message': f'Generated drafts for {success_count} out of {len(sections)} sections'
        }
        
    except Exception as e:
        logger.error(f"Error executing author first drafts: {e}")
        return {"success": False, "error": str(e)}, 500

def execute_image_concepts(post_id, data):
    """Execute image concepts generation for all sections of a post"""
    try:
        logger.info(f"Starting image concepts generation for post {post_id}")
        
        # Get all sections for this post
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description, status, image_concepts
                FROM post_section
                WHERE post_id = %s 
                AND section_order <= 7
                ORDER BY section_order
            """, (post_id,))
            
            sections = cursor.fetchall()
            
            if not sections:
                return {"success": False, "error": "No sections found for this post"}, 404
        
        logger.info(f"Found {len(sections)} sections to generate image concepts for")
        
        # Generate image concepts for each section
        results = []
        success_count = 0
        
        for section in sections:
            section_id = section['id']
            section_title = section['section_heading']
            
            try:
                logger.info(f"Generating image concepts for section {section_id}: {section_title}")
                
                # Call the core LLM logic directly (same as authoring API)
                from blueprints.authoring import LLMService
                import json
                
                try:
                    # Get the image concepts prompt
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT system_prompt, prompt_text
                            FROM llm_prompt
                            WHERE name = 'Image Concepts Generation'
                            ORDER BY id DESC
                            LIMIT 1
                        """)
                        prompt_data = cursor.fetchone()
                        
                        if not prompt_data:
                            raise Exception("Image Concepts prompt not found")
                    
                    # Get post development data for context
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT expanded_idea, topic_allocation, sections
                            FROM post_development
                            WHERE post_id = %s
                        """, (post_id,))
                        dev_data = cursor.fetchone()
                        
                        if not dev_data:
                            raise Exception("Post development data not found")
                    
                    # Get section draft content
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT draft
                            FROM post_section
                            WHERE id = %s
                        """, (section_id,))
                        section_data = cursor.fetchone()
                        
                        if not section_data:
                            raise Exception("Section data not found")
                    
                    # Prepare prompt variables
                    prompt_vars = {
                        'SECTION_TITLE': section['section_heading'],
                        'SECTION_DESCRIPTION': section['section_description'] or '',
                        'SECTION_CONTENT': section_data['draft'] or '',
                        'POST_TITLE': dev_data.get('expanded_idea', ''),
                        'POST_CONTEXT': dev_data.get('expanded_idea', '')
                    }
                    
                    # Replace placeholders in prompt
                    prompt_text = prompt_data['prompt_text']
                    for key, value in prompt_vars.items():
                        prompt_text = prompt_text.replace(f'[{key}]', str(value))
                    
                    # Call LLM service
                    messages = [
                        {'role': 'system', 'content': prompt_data['system_prompt']},
                        {'role': 'user', 'content': prompt_text}
                    ]
                    
                    llm_service = LLMService()
                    llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
                    
                    if llm_response and 'content' in llm_response:
                        image_concepts = llm_response['content'].strip()
                        
                        # Save the image concepts to database with auto-selection
                        with db_manager.get_cursor() as cursor:
                            # Auto-select first concept if no selection exists
                            try:
                                concepts_data = json.loads(image_concepts)
                                if concepts_data.get('concepts') and len(concepts_data['concepts']) > 0:
                                    first_concept_id = concepts_data['concepts'][0]['concept_id']
                                    
                                    cursor.execute("""
                                        UPDATE post_section
                                        SET image_concepts = %s, selected_image_concept = %s
                                        WHERE id = %s
                                    """, (image_concepts, first_concept_id, section_id))
                                    logger.info(f"Auto-selected concept {first_concept_id} for section {section_id}")
                                else:
                                    cursor.execute("""
                                        UPDATE post_section
                                        SET image_concepts = %s
                                        WHERE id = %s
                                    """, (image_concepts, section_id))
                            except Exception as e:
                                logger.error(f"Error auto-selecting concept for section {section_id}: {e}")
                                cursor.execute("""
                                    UPDATE post_section
                                    SET image_concepts = %s
                                    WHERE id = %s
                                """, (image_concepts, section_id))
                        
                        success_count += 1
                        results.append({
                            'section_id': section_id,
                            'section_title': section_title,
                            'success': True,
                            'image_concepts': image_concepts
                        })
                        logger.info(f"Successfully generated image concepts for section {section_id}")
                    else:
                        raise Exception("No content in LLM response")
                        
                except Exception as e:
                    results.append({
                        'section_id': section_id,
                        'section_title': section_title,
                        'success': False,
                        'error': str(e)
                    })
                    logger.error(f"Error generating image concepts for section {section_id}: {e}")
                    
            except Exception as e:
                logger.error(f"Error generating image concepts for section {section_id}: {e}")
                results.append({
                    'section_id': section_id,
                    'section_title': section_title,
                    'success': False,
                    'error': str(e)
                })
        
        # Update the authoring progress timestamp
        if success_count > 0:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE post_development 
                    SET updated_at = NOW()
                    WHERE post_id = %s
                """, (post_id,))
        
        logger.info(f"Image concepts generation completed: {success_count}/{len(sections)} sections successful")
        
        return {
            'success': True,
            'total_sections': len(sections),
            'successful_sections': success_count,
            'failed_sections': len(sections) - success_count,
            'results': results,
            'message': f'Generated image concepts for {success_count} out of {len(sections)} sections'
        }
        
    except Exception as e:
        logger.error(f"Error executing image concepts: {e}")
        return {"success": False, "error": str(e)}, 500

def execute_image_prompts(post_id, data):
    """Execute image prompts generation for all sections of a post"""
    try:
        logger.info(f"Starting image prompts generation for post {post_id}")
        
        # Get all sections for this post
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description, status, image_prompts
                FROM post_section
                WHERE post_id = %s 
                AND section_order <= 7
                ORDER BY section_order
            """, (post_id,))
            
            sections = cursor.fetchall()
            
            if not sections:
                return {"success": False, "error": "No sections found for this post"}, 404
        
        logger.info(f"Found {len(sections)} sections to generate image prompts for")
        
        # Generate image prompts for each section
        results = []
        success_count = 0
        
        for section in sections:
            section_id = section['id']
            section_title = section['section_heading']
            
            try:
                logger.info(f"Generating image prompts for section {section_id}: {section_title}")
                
                # Call the core LLM logic directly (same as authoring API)
                from blueprints.authoring import LLMService
                import json
                
                try:
                    # Get the image prompts prompt
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT system_prompt, prompt_text
                            FROM llm_prompt
                            WHERE name = 'Image Prompts Generation'
                            ORDER BY id DESC
                            LIMIT 1
                        """)
                        prompt_data = cursor.fetchone()
                        
                        if not prompt_data:
                            raise Exception("Image Prompts prompt not found")
                    
                    # Get post development data for context
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT expanded_idea, topic_allocation, sections
                            FROM post_development
                            WHERE post_id = %s
                        """, (post_id,))
                        dev_data = cursor.fetchone()
                        
                        if not dev_data:
                            raise Exception("Post development data not found")
                    
                    # Get section draft content
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT draft
                            FROM post_section
                            WHERE id = %s
                        """, (section_id,))
                        section_data = cursor.fetchone()
                        
                        if not section_data:
                            raise Exception("Section data not found")
                    
                    # Prepare prompt variables
                    prompt_vars = {
                        'SECTION_TITLE': section['section_heading'],
                        'SECTION_DESCRIPTION': section['section_description'] or '',
                        'SECTION_CONTENT': section_data['draft'] or '',
                        'POST_TITLE': dev_data.get('expanded_idea', ''),
                        'POST_CONTEXT': dev_data.get('expanded_idea', '')
                    }
                    
                    # Replace placeholders in prompt
                    prompt_text = prompt_data['prompt_text']
                    for key, value in prompt_vars.items():
                        prompt_text = prompt_text.replace(f'[{key}]', str(value))
                    
                    # Call LLM service
                    messages = [
                        {'role': 'system', 'content': prompt_data['system_prompt']},
                        {'role': 'user', 'content': prompt_text}
                    ]
                    
                    llm_service = LLMService()
                    llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
                    
                    if llm_response and 'content' in llm_response:
                        image_prompts = llm_response['content'].strip()
                        
                        # Save the image prompts to database
                        with db_manager.get_cursor() as cursor:
                            cursor.execute("""
                                UPDATE post_section
                                SET image_prompts = %s
                                WHERE id = %s
                            """, (image_prompts, section_id))
                        
                        success_count += 1
                        results.append({
                            'section_id': section_id,
                            'section_title': section_title,
                            'success': True,
                            'image_prompts': image_prompts
                        })
                        logger.info(f"Successfully generated image prompts for section {section_id}")
                    else:
                        raise Exception("No content in LLM response")
                        
                except Exception as e:
                    results.append({
                        'section_id': section_id,
                        'section_title': section_title,
                        'success': False,
                        'error': str(e)
                    })
                    logger.error(f"Error generating image prompts for section {section_id}: {e}")
                    
            except Exception as e:
                logger.error(f"Error generating image prompts for section {section_id}: {e}")
                results.append({
                    'section_id': section_id,
                    'section_title': section_title,
                    'success': False,
                    'error': str(e)
                })
        
        # Update the authoring progress timestamp
        if success_count > 0:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE post_development 
                    SET updated_at = NOW()
                    WHERE post_id = %s
                """, (post_id,))
        
        return {
            'success': True,
            'total_sections': len(sections),
            'successful_sections': success_count,
            'failed_sections': len(sections) - success_count,
            'results': results,
            'message': f'Generated image prompts for {success_count} out of {len(sections)} sections'
        }
        
    except Exception as e:
        logger.error(f"Error executing image prompts: {e}")
        return {"success": False, "error": str(e)}, 500

def execute_image_captions(post_id, data):
    """Execute image captions generation for all sections of a post"""
    try:
        logger.info(f"Starting image captions generation for post {post_id}")
        
        # Get all sections for this post
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description, status, image_captions
                FROM post_section
                WHERE post_id = %s 
                AND section_order <= 7
                ORDER BY section_order
            """, (post_id,))
            
            sections = cursor.fetchall()
            
            if not sections:
                return {"success": False, "error": "No sections found for this post"}, 404
        
        logger.info(f"Found {len(sections)} sections to generate image captions for")
        
        # Generate image captions for each section
        results = []
        success_count = 0
        
        for section in sections:
            section_id = section['id']
            section_title = section['section_heading']
            
            try:
                logger.info(f"Generating image captions for section {section_id}: {section_title}")
                
                # Call the core LLM logic directly (same as authoring API)
                from blueprints.authoring import LLMService
                import json
                
                try:
                    # Get the image captions prompt
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT system_prompt, prompt_text
                            FROM llm_prompt
                            WHERE name = 'Image Captions Generation'
                            ORDER BY id DESC
                            LIMIT 1
                        """)
                        prompt_data = cursor.fetchone()
                        
                        if not prompt_data:
                            raise Exception("Image Captions prompt not found")
                    
                    # Get post development data for context
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT expanded_idea, topic_allocation, sections
                            FROM post_development
                            WHERE post_id = %s
                        """, (post_id,))
                        dev_data = cursor.fetchone()
                        
                        if not dev_data:
                            raise Exception("Post development data not found")
                    
                    # Get section draft content
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT draft
                            FROM post_section
                            WHERE id = %s
                        """, (section_id,))
                        section_data = cursor.fetchone()
                        
                        if not section_data:
                            raise Exception("Section data not found")
                    
                    # Prepare prompt variables
                    prompt_vars = {
                        'SECTION_TITLE': section['section_heading'],
                        'SECTION_DESCRIPTION': section['section_description'] or '',
                        'SECTION_CONTENT': section_data['draft'] or '',
                        'POST_TITLE': dev_data.get('expanded_idea', ''),
                        'POST_CONTEXT': dev_data.get('expanded_idea', '')
                    }
                    
                    # Replace placeholders in prompt
                    prompt_text = prompt_data['prompt_text']
                    for key, value in prompt_vars.items():
                        prompt_text = prompt_text.replace(f'[{key}]', str(value))
                    
                    # Call LLM service
                    messages = [
                        {'role': 'system', 'content': prompt_data['system_prompt']},
                        {'role': 'user', 'content': prompt_text}
                    ]
                    
                    llm_service = LLMService()
                    llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
                    
                    if llm_response and 'content' in llm_response:
                        image_captions = llm_response['content'].strip()
                        
                        # Save the image captions to database
                        with db_manager.get_cursor() as cursor:
                            cursor.execute("""
                                UPDATE post_section
                                SET image_captions = %s
                                WHERE id = %s
                            """, (image_captions, section_id))
                        
                        success_count += 1
                        results.append({
                            'section_id': section_id,
                            'section_title': section_title,
                            'success': True,
                            'image_captions': image_captions
                        })
                        logger.info(f"Successfully generated image captions for section {section_id}")
                    else:
                        raise Exception("No content in LLM response")
                        
                except Exception as e:
                    results.append({
                        'section_id': section_id,
                        'section_title': section_title,
                        'success': False,
                        'error': str(e)
                    })
                    logger.error(f"Error generating image captions for section {section_id}: {e}")
                    
            except Exception as e:
                logger.error(f"Error generating image captions for section {section_id}: {e}")
                results.append({
                    'section_id': section_id,
                    'section_title': section_title,
                    'success': False,
                    'error': str(e)
                })
        
        # Update the authoring progress timestamp
        if success_count > 0:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE post_development 
                    SET updated_at = NOW()
                    WHERE post_id = %s
                """, (post_id,))
        
        return {
            'success': True,
            'total_sections': len(sections),
            'successful_sections': success_count,
            'failed_sections': len(sections) - success_count,
            'results': results,
            'message': f'Generated image captions for {success_count} out of {len(sections)} sections'
        }
        
    except Exception as e:
        logger.error(f"Error executing image captions: {e}")
        return {"success": False, "error": str(e)}, 500


# Weekly Content Substage Functions

def execute_format_for_facebook(post_id, data):
    """
    Format content for Facebook.
    
    For posting_queue rows:
    - Weekly content: Extract data from calendar_ideas via idea_id
    - Product posts: Extract data from clan_products via product_id
    - Prepare data structure for caption/image generation
    - Store formatted data in posting_queue.generated_content
    """
    try:
        from utils.posting_queue_helpers import get_posting_queue_row
        from utils.weekly_content_data_extractor import extract_weekly_content_data
        import json
        
        # Get posting_queue row (post_id is actually queue_id here)
        queue_row = get_posting_queue_row(post_id)
        
        if not queue_row:
            return {"success": False, "error": "Posting queue row not found"}, 404
        
        content_type = queue_row.get('content_type')
        
        # Handle weekly content
        if content_type in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
            idea_id = queue_row.get('idea_id')
            if not idea_id:
                return {"success": False, "error": "No idea_id for weekly content post"}, 400
            
            # Extract formatted data
            formatted_data = extract_weekly_content_data(idea_id, content_type)
        
        # Handle product posts
        elif content_type == 'product':
            product_id = queue_row.get('product_id')
            if not product_id:
                return {"success": False, "error": "No product_id for product post"}, 400
            
            # Get product data
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, sku, price, description, image_url, url
                    FROM clan_products
                    WHERE id = %s
                """, (product_id,))
                product = cursor.fetchone()
                
                if not product:
                    return {"success": False, "error": f"Product {product_id} not found"}, 404
            
            # Format product data for Facebook
            formatted_data = {
                'category': 'product',
                'product_id': product['id'],
                'product_name': product['name'],
                'product_sku': product['sku'],
                'product_description': product['description'] or '',
                'product_image_url': product['image_url'] or '',
                'product_url': product['url'] or '',
                'product_price': str(product['price']) if product['price'] else None,
                'content_type': 'product'
            }
        
        else:
            return {"success": False, "error": f"Unsupported content type: {content_type}"}, 400
        
        # Store in generated_content (JSON)
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE posting_queue
                SET generated_content = %s, updated_at = NOW()
                WHERE id = %s
            """, (json.dumps(formatted_data), post_id))
        
        return {
            "success": True,
            "formatted_data": formatted_data,
            "message": "Content formatted for Facebook"
        }
        
    except Exception as e:
        logger.error(f"Error formatting for Facebook: {e}")
        return {"success": False, "error": str(e)}, 500


def execute_add_translation(post_id, data):
    """
    Add translation to formatted content.
    
    For weekly_phrase and weekly_insult, ensures translation is included.
    Translation is already in formatted_data from extract_weekly_content_data,
    so this substage may just verify it exists or format it differently.
    """
    try:
        from utils.posting_queue_helpers import get_posting_queue_row
        import json
        
        # Get posting_queue row
        queue_row = get_posting_queue_row(post_id)
        if not queue_row:
            return {"success": False, "error": "Posting queue row not found"}, 404
        
        # Translation is already in formatted_data from format_for_facebook
        # This substage is a no-op for now, but could add formatting logic
        formatted_data_json = queue_row.get('generated_content')
        if formatted_data_json:
            formatted_data = json.loads(formatted_data_json)
            translation = formatted_data.get('translation', '')
            
            if not translation:
                logger.warning(f"Translation missing for queue_id={post_id}")
        
        return {
            "success": True,
            "message": "Translation verified"
        }
        
    except Exception as e:
        logger.error(f"Error adding translation: {e}")
        return {"success": False, "error": str(e)}, 500


def execute_add_hashtags(post_id, data):
    """
    Add hashtags to caption (max 1 per briefing requirements).
    
    Hashtags are added to the caption text, not the image.
    """
    try:
        from utils.posting_queue_helpers import get_posting_queue_row
        
        # Get posting_queue row
        queue_row = get_posting_queue_row(post_id)
        if not queue_row:
            return {"success": False, "error": "Posting queue row not found"}, 404
        
        # Get current caption
        caption = queue_row.get('generated_caption', '')
        
        # Add hashtag if not present (max 1 per briefing)
        hashtag = "#ScotsLanguage"  # Default hashtag
        if hashtag not in caption:
            caption_with_hashtag = f"{caption} {hashtag}"
        else:
            caption_with_hashtag = caption
        
        # Update generated_caption
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE posting_queue
                SET generated_caption = %s, updated_at = NOW()
                WHERE id = %s
            """, (caption_with_hashtag, post_id))
        
        return {
            "success": True,
            "caption": caption_with_hashtag,
            "message": "Hashtag added to caption"
        }
        
    except Exception as e:
        logger.error(f"Error adding hashtags: {e}")
        return {"success": False, "error": str(e)}, 500


def execute_optimize_for_facebook(post_id, data):
    """
    Optimize image for Facebook posting.
    
    For weekly content: Generates square 1080×1080 image using ImageMagick
    For product posts: Uses product image URL directly (no generation needed)
    """
    try:
        from utils.posting_queue_helpers import get_posting_queue_row
        from utils.weekly_content_data_extractor import extract_weekly_content_data
        from utils.weekly_content_image_renderer import render_weekly_content_image
        import json
        
        # Get posting_queue row
        queue_row = get_posting_queue_row(post_id)
        if not queue_row:
            return {"success": False, "error": "Posting queue row not found"}, 404
        
        content_type = queue_row.get('content_type')
        
        # Handle weekly content - generate image
        if content_type in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
            # Get formatted data (from previous substage)
            formatted_data_json = queue_row.get('generated_content')
            if not formatted_data_json:
                # Extract fresh if not formatted yet
                idea_id = queue_row.get('idea_id')
                if not idea_id:
                    return {"success": False, "error": "No idea_id for weekly content post"}, 400
                formatted_data = extract_weekly_content_data(idea_id, content_type)
            else:
                formatted_data = json.loads(formatted_data_json)
            
            # Render image
            result = render_weekly_content_image(
                category=formatted_data['category'],
                title=formatted_data['title'],
                scots_text=formatted_data['scots_text'],
                translation=formatted_data['translation'],
                series_footer=formatted_data['series_footer'],
                logo_path=formatted_data['logo_path'],
                output_path=formatted_data['output_path'],
                usage_examples=formatted_data.get('usage_examples', []),
                notes=formatted_data.get('notes', '')
            )
            
            if not result['success']:
                return {"success": False, "error": result['error']}, 500
            
            image_path = result['output_path']
        
        # Handle product posts - use product image URL
        elif content_type == 'product':
            # Get formatted data (from format_for_facebook substage)
            formatted_data_json = queue_row.get('generated_content')
            if not formatted_data_json:
                return {"success": False, "error": "Product data not formatted. Run format_for_facebook first."}, 400
            
            formatted_data = json.loads(formatted_data_json)
            product_image_url = formatted_data.get('product_image_url', '')
            
            if not product_image_url:
                return {"success": False, "error": "Product has no image URL"}, 400
            
            # For product posts, we use the product image URL directly
            # Store it as image_path (will be converted to public URL in publish step)
            # If it's already a full URL, use it; otherwise it might be a relative path
            image_path = product_image_url
        
        else:
            return {"success": False, "error": f"Unsupported content type: {content_type}"}, 400
        
        # Store image path in posting_queue
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE posting_queue
                SET image_path = %s, updated_at = NOW()
                WHERE id = %s
            """, (image_path, post_id))
        
        return {
            "success": True,
            "image_path": image_path,
            "message": "Image optimized for Facebook" if content_type == 'product' else "Square image generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error optimizing for Facebook: {e}")
        return {"success": False, "error": str(e)}, 500


def execute_publish_to_facebook(queue_id, data):
    """
    Publish post to Facebook (both pages).
    
    Supports:
    - Weekly content: Uses generated image and caption, posts via /photos endpoint
    - Product posts: Uses product image URL and caption, posts via /photos endpoint
    """
    try:
        import requests
        import os
        from utils.posting_queue_helpers import get_posting_queue_row
        import json
        
        # Get posting_queue row
        queue_row = get_posting_queue_row(queue_id)
        if not queue_row:
            return {"success": False, "error": "Posting queue row not found"}, 404
        
        content_type = queue_row.get('content_type')
        
        # Get generated image and caption
        image_path = queue_row.get('image_path')
        caption = queue_row.get('generated_caption')
        
        if not image_path or not caption:
            return {"success": False, "error": "Image or caption not generated"}, 400
        
        # Handle image URL conversion based on content type
        if content_type == 'product':
            # Product posts: image_path is already a URL (product_image_url)
            # Check if it's a full URL or needs conversion
            if image_path.startswith('http://') or image_path.startswith('https://'):
                image_url = image_path
            else:
                # Might be a relative path, try to construct full URL
                # Product images are typically on clan.com CDN already
                if 'clan.com' in image_path or 'clan-products' in image_path:
                    image_url = image_path if image_path.startswith('http') else f"https://{image_path}"
                else:
                    # Fallback: assume it's a clan.com product image
                    image_url = f"https://clan.com{image_path}" if image_path.startswith('/') else f"https://clan.com/{image_path}"
            
            logger.info(f"Using product image URL: {image_url}")
        
        else:
            # Weekly content: Upload image to clan.com CDN
            try:
                import sys
                # Add blog-launchpad to path if needed
                blog_launchpad_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-launchpad')
                if blog_launchpad_path not in sys.path:
                    sys.path.insert(0, blog_launchpad_path)
                from clan_publisher import ClanPublisher
                publisher = ClanPublisher()
                
                # Generate a unique filename for the weekly content image
                import time
                filename = f"weekly_content_{queue_row.get('idea_id', 'unknown')}_{int(time.time())}.png"
                
                logger.info(f"Uploading weekly content image to clan.com: {image_path}")
                uploaded_url = publisher.upload_image(image_path, filename)
                
                if not uploaded_url:
                    return {"success": False, "error": "Failed to upload image to clan.com CDN"}, 500
                
                logger.info(f"Image uploaded successfully to: {uploaded_url}")
                image_url = uploaded_url
                
            except ImportError:
                # Fallback: try to use static URL if ClanPublisher not available
                logger.warning("ClanPublisher not available, falling back to static URL")
                if os.path.exists(image_path):
                    # Extract relative path from static/
                    if 'static/' in image_path:
                        relative_path = image_path.split('static/', 1)[1]
                        # Use production domain
                        base_url = 'https://clan.com'
                        image_url = f"{base_url}/static/{relative_path}"
                    else:
                        return {"success": False, "error": f"Cannot convert image path to URL: {image_path}"}, 400
                else:
                    return {"success": False, "error": f"Image file not found: {image_path}"}, 400
            except Exception as e:
                logger.error(f"Error uploading image to clan.com: {e}")
                return {"success": False, "error": f"Failed to upload image: {str(e)}"}, 500
        
        # Get Facebook credentials for both pages
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT credential_key, credential_value
                FROM platform_credentials 
                WHERE platform_id = (SELECT id FROM platforms WHERE name = 'facebook')
                AND is_active = true
            """)
            credentials = cursor.fetchall()
        
        # Convert to dictionary
        creds = {}
        for cred in credentials:
            creds[cred['credential_key']] = cred['credential_value']
        
        # Define both pages to post to
        pages_to_post = []
        
        # Page 1 (Scotweb CLAN)
        if creds.get('page_access_token') and creds.get('page_id'):
            pages_to_post.append({
                'page_id': creds['page_id'],
                'access_token': creds['page_access_token'],
                'name': 'Scotweb CLAN'
            })
        
        # Page 2 (CLAN by Scotweb) - only add if different from Page 1
        if (creds.get('page_access_token_2') and creds.get('page_id_2') and 
            creds.get('page_id_2') != creds.get('page_id')):
            pages_to_post.append({
                'page_id': creds['page_id_2'],
                'access_token': creds['page_access_token_2'],
                'name': 'CLAN by Scotweb'
            })
        elif creds.get('page_id_2') == creds.get('page_id'):
            logger.warning("Both Facebook pages have the same page_id - skipping duplicate posting to prevent double posts")
        
        if not pages_to_post:
            return {"success": False, "error": "No Facebook pages configured"}, 400
        
        # Post to both pages using /photos endpoint for image posts
        results = []
        successful_posts = []
        failed_posts = []
        
        for page in pages_to_post:
            photos_url = f"https://graph.facebook.com/v18.0/{page['page_id']}/photos"
            photos_payload = {
                'url': image_url,
                'caption': caption,
                'published': True,
                'access_token': page['access_token']
            }
            
            logger.info(f"Posting to {page['name']} (Page ID: {page['page_id']})")
            logger.info(f"Image URL: {image_url}")
            logger.info(f"Caption: {caption[:50]}...")
            
            try:
                response = requests.post(photos_url, data=photos_payload, timeout=30)
                logger.info(f"Facebook API response - Status: {response.status_code}")
                logger.info(f"Facebook API response - Content: {response.text}")
                
                if response.status_code == 200:
                    result = response.json()
                    fb_post_id = result.get('id')
                    successful_posts.append(fb_post_id)
                    results.append({
                        'page_name': page['name'],
                        'page_id': page['page_id'],
                        'post_id': fb_post_id,
                        'success': True
                    })
                else:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get('error', {}).get('message', 'Unknown Facebook API error')
                    failed_posts.append(f"{page['name']}: {error_msg}")
                    results.append({
                        'page_name': page['name'],
                        'page_id': page['page_id'],
                        'success': False,
                        'error': error_msg
                    })
            except Exception as e:
                error_msg = str(e)
                failed_posts.append(f"{page['name']}: {error_msg}")
                logger.error(f"Error posting to {page['name']}: {e}")
                results.append({
                    'page_name': page['name'],
                    'page_id': page['page_id'],
                    'success': False,
                    'error': error_msg
                })
        
        # Update queue item status
        with db_manager.get_cursor() as cursor:
            if successful_posts:
                # platform_post_id is VARCHAR(100), so convert to string
                platform_post_id_str = str(successful_posts[0])
                cursor.execute("""
                    UPDATE posting_queue 
                    SET status = 'published', 
                        platform_post_id = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (platform_post_id_str, queue_id))  # Store first post ID as primary
                
                if len(failed_posts) == 0:
                    return {
                        "success": True,
                        "message": f"Successfully posted to {len(successful_posts)} page(s)",
                        "platform_post_ids": successful_posts,
                        "results": results
                    }
                else:
                    return {
                        "success": True,
                        "message": f"Posted to {len(successful_posts)} page(s), failed on {len(failed_posts)}: {', '.join(failed_posts)}",
                        "platform_post_ids": successful_posts,
                        "results": results,
                        "warnings": failed_posts
                    }
            else:
                # All posts failed
                cursor.execute("""
                    UPDATE posting_queue 
                    SET status = 'failed', 
                        error_message = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (", ".join(failed_posts), queue_id))
                
                return {
                    "success": False,
                    "error": f"Failed to post to all pages: {', '.join(failed_posts)}",
                    "results": results
                }, 500
        
    except Exception as e:
        logger.error(f"Error publishing to Facebook: {e}", exc_info=True)
        return {"success": False, "error": str(e)}, 500


def execute_generate_caption(post_id, data):
    """
    Generate caption using Ollama.
    
    Supports:
    - Weekly content: Uses weekly_content_caption_generator
    - Product posts: Uses LLMService with product data
    """
    try:
        from utils.posting_queue_helpers import get_posting_queue_row
        from utils.weekly_content_data_extractor import extract_weekly_content_data
        from utils.weekly_content_caption_generator import generate_weekly_content_caption
        from blueprints.llm_actions import LLMService
        import json
        
        # Get posting_queue row
        queue_row = get_posting_queue_row(post_id)
        if not queue_row:
            return {"success": False, "error": "Posting queue row not found"}, 404
        
        content_type = queue_row.get('content_type')
        
        # Handle weekly content
        if content_type in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
            idea_id = queue_row.get('idea_id')
            if not idea_id:
                return {"success": False, "error": "No idea_id for weekly content post"}, 400
            
            # Get formatted data (or extract fresh)
            formatted_data_json = queue_row.get('generated_content')
            if formatted_data_json:
                formatted_data = json.loads(formatted_data_json)
            else:
                formatted_data = extract_weekly_content_data(idea_id, content_type)
            
            # Generate caption
            caption_result = generate_weekly_content_caption(
                category=formatted_data['category'],
                scots_text=formatted_data['scots_text'],
                translation=formatted_data['translation'],
                notes=formatted_data.get('notes')
            )
            
            caption = caption_result.get('caption', '')
        
        # Handle product posts
        elif content_type == 'product':
            # Get formatted data (from format_for_facebook substage)
            formatted_data_json = queue_row.get('generated_content')
            if not formatted_data_json:
                return {"success": False, "error": "Product data not formatted. Run format_for_facebook first."}, 400
            
            formatted_data = json.loads(formatted_data_json)
            
            # Generate caption using standardized product caption generator
            from utils.product_post_caption_generator import generate_product_post_caption
            
            caption_result = generate_product_post_caption(
                product_name=formatted_data['product_name'],
                product_description=formatted_data.get('product_description', ''),
                product_url=formatted_data.get('product_url', ''),
                model='mistral'
            )
            
            caption = caption_result.get('caption', '')
            
            # Log the request for tracking (similar to weekly content)
            logger.info(f"Generated caption for product post queue_id={post_id}, product_id={formatted_data['product_id']}, style_id={caption_result.get('chosen_prompt_style_id')}")
        
        else:
            return {"success": False, "error": f"Unsupported content type: {content_type}"}, 400
        
        # Store in posting_queue
        with db_manager.get_cursor() as cursor:
            if content_type in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
                # Weekly content has structured caption result
                cursor.execute("""
                    UPDATE posting_queue
                    SET 
                        generated_caption = %s,
                        pinned_comment = %s,
                        chosen_prompt_style_id = %s,
                        ollama_model = %s,
                        generation_timestamp = NOW(),
                        updated_at = NOW()
                    WHERE id = %s
                """, (
                    caption_result['caption'],
                    caption_result.get('pinned_comment'),
                    caption_result['chosen_prompt_style_id'],
                    caption_result['ollama_model'],
                    post_id
                ))
            elif content_type == 'product':
                # Product posts - store caption with metadata
                cursor.execute("""
                    UPDATE posting_queue
                    SET 
                        generated_caption = %s,
                        chosen_prompt_style_id = %s,
                        ollama_model = %s,
                        generation_timestamp = NOW(),
                        updated_at = NOW()
                    WHERE id = %s
                """, (
                    caption_result['caption'],
                    caption_result.get('chosen_prompt_style_id'),
                    caption_result.get('model', 'mistral'),
                    post_id
                ))
        
        # Return appropriate response based on content type
        if content_type in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
            return {
                "success": True,
                "caption": caption_result['caption'],
                "caption_result": caption_result,
                "message": "Caption generated successfully"
            }
        elif content_type == 'product':
            return {
                "success": True,
                "caption": caption_result['caption'],
                "caption_result": caption_result,
                "message": "Caption generated successfully"
            }
        else:
            return {
                "success": True,
                "caption": caption,
                "message": "Caption generated successfully"
            }
        
    except Exception as e:
        logger.error(f"Error generating caption: {e}")
        return {"success": False, "error": str(e)}, 500
