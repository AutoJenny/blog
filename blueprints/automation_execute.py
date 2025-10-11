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
        from blueprints.planning_sections import api_sections_title
        
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
                        
                        # Save the image concepts to database
                        with db_manager.get_cursor() as cursor:
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
