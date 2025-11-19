"""Prompt management API endpoints for header blueprint"""
from flask import Blueprint, jsonify, request
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Register prompt management API routes"""
    
    @bp.route('/api/prompts/<int:step_id>')
    def api_get_prompts(step_id):
        """Get system and task prompts for a workflow step"""
        try:
            logger.info(f"Getting prompts for step_id: {step_id}")
            with db_manager.get_cursor() as cursor:
                # Get prompts from workflow_step_prompt table
                cursor.execute("""
                    SELECT 
                        sp.system_prompt,
                        tp.prompt_text as task_prompt
                    FROM workflow_step_prompt wsp
                    LEFT JOIN llm_prompt sp ON sp.id = wsp.system_prompt_id
                    LEFT JOIN llm_prompt tp ON tp.id = wsp.task_prompt_id
                    WHERE wsp.step_id = %s
                """, (step_id,))
                
                result = cursor.fetchone()
                
                if result:
                    return jsonify({
                        'success': True,
                        'system_prompt': result.get('system_prompt', '') or '',
                        'task_prompt': result.get('task_prompt', '') or ''
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'No prompts found for this step'
                    }), 404
                    
        except Exception as e:
            logger.error(f"Error getting prompts for step {step_id}: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/prompts/<int:step_id>', methods=['POST'])
    def api_save_prompts(step_id):
        """Save system and task prompts for a workflow step"""
        try:
            data = request.get_json()
            system_prompt = data.get('system_prompt', '')
            task_prompt = data.get('task_prompt', '')
            
            with db_manager.get_cursor() as cursor:
                # Get current prompt IDs
                cursor.execute("""
                    SELECT system_prompt_id, task_prompt_id
                    FROM workflow_step_prompt
                    WHERE step_id = %s
                """, (step_id,))
                
                result = cursor.fetchone()
                
                if result:
                    system_prompt_id, task_prompt_id = result
                    
                    # Update system prompt
                    if system_prompt_id:
                        cursor.execute("""
                            UPDATE llm_prompt 
                            SET system_prompt = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (system_prompt, system_prompt_id))
                    else:
                        # Create new system prompt
                        cursor.execute("""
                            INSERT INTO llm_prompt (name, description, system_prompt)
                            VALUES (%s, %s, %s)
                            RETURNING id
                        """, (f'System Prompt Step {step_id}', f'System prompt for step {step_id}', system_prompt))
                        system_prompt_id = cursor.fetchone()[0]
                    
                    # Update task prompt
                    if task_prompt_id:
                        cursor.execute("""
                            UPDATE llm_prompt 
                            SET prompt_text = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (task_prompt, task_prompt_id))
                    else:
                        # Create new task prompt
                        cursor.execute("""
                            INSERT INTO llm_prompt (name, description, prompt_text, step_id)
                            VALUES (%s, %s, %s, %s)
                            RETURNING id
                        """, (f'Task Prompt Step {step_id}', f'Task prompt for step {step_id}', task_prompt, step_id))
                        task_prompt_id = cursor.fetchone()[0]
                    
                    # Update workflow_step_prompt link
                    cursor.execute("""
                        UPDATE workflow_step_prompt
                        SET system_prompt_id = %s, task_prompt_id = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE step_id = %s
                    """, (system_prompt_id, task_prompt_id, step_id))
                    
                    return jsonify({'success': True})
                else:
                    return jsonify({
                        'success': False,
                        'error': 'No workflow step found'
                    }), 404
                    
        except Exception as e:
            logger.error(f"Error saving prompts for step {step_id}: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/posts/<int:post_id>/title-summary-prompt', methods=['GET', 'PUT'])
    def api_title_summary_prompt(post_id):
        """Get or update the Title Generation prompt for title-summary page"""
        try:
            with db_manager.get_cursor() as cursor:
                if request.method == 'GET':
                    # Get prompt from workflow_step_prompt for step 60 (Title Generation)
                    cursor.execute("""
                        SELECT 
                            sp.id as system_prompt_id,
                            sp.name as system_prompt_name,
                            sp.system_prompt,
                            tp.id as task_prompt_id,
                            tp.name as task_prompt_name,
                            tp.prompt_text as task_prompt
                        FROM workflow_step_prompt wsp
                        JOIN llm_prompt sp ON wsp.system_prompt_id = sp.id
                        JOIN llm_prompt tp ON wsp.task_prompt_id = tp.id
                        WHERE wsp.step_id = 60
                    """)
                    
                    result = cursor.fetchone()
                    
                    if not result:
                        return jsonify({'error': 'Title Generation prompt not found'}), 404
                    
                    # Return system_prompt and prompt_text separately for LLM Prompts Panel
                    return jsonify({
                        'success': True,
                        'prompt': {
                            'id': result['task_prompt_id'],  # Use task prompt ID for editing
                            'name': result['task_prompt_name'],
                            'system_prompt': result['system_prompt'] or '',
                            'prompt_text': result['task_prompt'] or '',
                            'system_prompt_id': result['system_prompt_id'],
                            'task_prompt_id': result['task_prompt_id']
                        }
                    })
                
                elif request.method == 'PUT':
                    # Update the prompt
                    # LLM Prompts Panel sends: { system_prompt, prompt_text }
                    # But we display combined, so we need to handle both formats
                    data = request.get_json()
                    
                    # Get current prompts first
                    cursor.execute("""
                        SELECT 
                            sp.id as system_prompt_id,
                            sp.system_prompt,
                            tp.id as task_prompt_id,
                            tp.prompt_text as task_prompt
                        FROM workflow_step_prompt wsp
                        JOIN llm_prompt sp ON wsp.system_prompt_id = sp.id
                        JOIN llm_prompt tp ON wsp.task_prompt_id = tp.id
                        WHERE wsp.step_id = 60
                    """)
                    
                    result = cursor.fetchone()
                    
                    if not result:
                        return jsonify({'error': 'Title Generation prompt not found'}), 404
                    
                    # Handle two formats:
                    # 1. LLM Prompts Panel format: { system_prompt, prompt_text }
                    # 2. Direct content format: { content }
                    if 'prompt_text' in data:
                        # Format from LLM Prompts Panel - update task prompt
                        task_prompt = data.get('prompt_text', '').strip()
                        # Only update if substantial content (more than 100 chars to avoid test data)
                        # Check against original to avoid overwriting with stale/test data
                        original_task = result.get('task_prompt', '').strip()
                        if task_prompt and len(task_prompt) > 100 and task_prompt != original_task:
                            # Ensure we're using integer IDs
                            task_prompt_id = int(result['task_prompt_id'])
                            cursor.execute("""
                                UPDATE llm_prompt
                                SET prompt_text = %s,
                                    updated_at = NOW()
                                WHERE id = %s
                            """, (task_prompt, task_prompt_id))
                            cursor.connection.commit()
                            logger.info(f"Updated Title Generation task prompt (task_prompt_id={task_prompt_id}) for post {post_id}")
                        elif task_prompt and len(task_prompt) <= 100:
                            logger.warning(f"Ignored task prompt update - too short (likely test data): {len(task_prompt)} chars")
                        elif task_prompt == original_task:
                            logger.info(f"Ignored task prompt update - no changes detected")
                        
                        # Optionally update system prompt if provided AND substantial
                        # Only update if it's actually meaningful content (not empty or test data)
                        if 'system_prompt' in data:
                            system_prompt = data.get('system_prompt', '').strip()
                            # Only update if it's substantial (more than just "Test system" or empty)
                            # Check against the original to avoid overwriting with test/stale data
                            original_system = result.get('system_prompt', '').strip()
                            if system_prompt and len(system_prompt) > 50 and system_prompt != original_system:
                                # Ensure we're using integer IDs
                                system_prompt_id = int(result['system_prompt_id'])
                                cursor.execute("""
                                    UPDATE llm_prompt
                                    SET system_prompt = %s,
                                        updated_at = NOW()
                                    WHERE id = %s
                                """, (system_prompt, system_prompt_id))
                                cursor.connection.commit()
                                logger.info(f"Updated Title Generation system prompt (system_prompt_id={system_prompt_id}) for post {post_id}")
                            elif system_prompt and len(system_prompt) <= 50:
                                logger.warning(f"Ignored system prompt update - too short (likely test data): {len(system_prompt)} chars")
                    
                    elif 'content' in data:
                        # Direct content format - user is editing combined prompt
                        prompt_content = data.get('content', '').strip()
                        
                        if not prompt_content:
                            return jsonify({'error': 'Prompt content is required'}), 400
                        
                        # Try to extract task part from combined prompt
                        system_prompt = result['system_prompt']
                        combined_pattern = f"{system_prompt}\n\n"
                        
                        if prompt_content.startswith(combined_pattern):
                            task_prompt = prompt_content[len(combined_pattern):]
                        elif prompt_content.startswith(system_prompt):
                            task_prompt = prompt_content[len(system_prompt):].lstrip()
                        else:
                            # If it doesn't match, assume user is editing just the task prompt
                            task_prompt = prompt_content
                        
                        # Ensure we're using integer ID
                        task_prompt_id = int(result['task_prompt_id'])
                        cursor.execute("""
                            UPDATE llm_prompt
                            SET prompt_text = %s,
                                updated_at = NOW()
                            WHERE id = %s
                        """, (task_prompt, task_prompt_id))
                        cursor.connection.commit()
                        logger.info(f"Updated Title Generation prompt from content (task_prompt_id={task_prompt_id}) for post {post_id}")
                    else:
                        return jsonify({'error': 'Either prompt_text or content is required'}), 400
                    
                    return jsonify({
                        'success': True,
                        'message': 'Prompt updated successfully'
                    })
                    
        except Exception as e:
            logger.error(f"Error with title-summary prompt: {e}")
            return jsonify({'error': str(e)}), 500

