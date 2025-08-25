"""
LLM Action Handler - Fresh Start

Simple script that logs when the Run LLM button is clicked.
"""

import logging
import os
import psycopg2
import requests
from datetime import datetime
from typing import Dict, Any

def call_llm(system_prompt: str, user_message: str, llm_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call the LLM with the given prompts and configuration.
    
    Args:
        system_prompt: System prompt to send to LLM
        user_message: User message to send to LLM
        llm_config: LLM configuration from database
    
    Returns:
        LLM response
    """
    try:
        # Prepare the request payload
        payload = {
            "model": llm_config.get('model_name', 'mistral'),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": llm_config.get('temperature', 0.7),
            "max_tokens": llm_config.get('max_tokens', 1000),
            "stream": False
        }
        
        # Get API base URL
        api_base = llm_config.get('api_base', 'http://localhost:11434')
        
        # Make the request
        response = requests.post(
            f"{api_base}/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=llm_config.get('timeout', 60)
        )
        
        if response.status_code == 200:
            result = response.json()
            raw_content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # Clean HTML from LLM response to prevent DOCTYPE corruption
            import re
            if raw_content and ('<!DOCTYPE' in raw_content or '<html' in raw_content or '<head>' in raw_content or '<body>' in raw_content):
                # Strip full HTML document structure
                cleaned_content = re.sub(r'<!DOCTYPE[^>]*>', '', raw_content)
                cleaned_content = re.sub(r'<html[^>]*>', '', cleaned_content)
                cleaned_content = re.sub(r'</html>', '', cleaned_content)
                cleaned_content = re.sub(r'<head[^>]*>.*?</head>', '', cleaned_content, flags=re.DOTALL)
                cleaned_content = re.sub(r'<body[^>]*>', '', cleaned_content)
                cleaned_content = re.sub(r'</body>', '', cleaned_content)
                
                # Remove any remaining HTML tags but keep text content
                cleaned_content = re.sub(r'<[^>]+>', '', cleaned_content)
                
                # Clean up whitespace
                cleaned_content = re.sub(r'\s+', ' ', cleaned_content).strip()
                
                print(f"⚠️ LLM returned HTML document, cleaned to: {cleaned_content[:100]}...")
            else:
                cleaned_content = raw_content
            
            return {
                "success": True,
                "content": cleaned_content,
                "usage": result.get('usage', {}),
                "model": result.get('model', '')
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "content": ""
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "content": ""
        }

def save_section_output(section_id: int, output_field: str, content: str, cursor, conn) -> bool:
    """
    Save LLM response to the output field for a specific section.
    
    Args:
        section_id: Section ID
        output_field: Output field name
        content: Content to save
        cursor: Database cursor
        conn: Database connection
    
    Returns:
        Success status
    """
    try:
        # Update the section with the LLM response
        cursor.execute(
            f"UPDATE post_section SET {output_field} = %s WHERE id = %s",
            (content, section_id)
        )
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"Error saving output for section {section_id}: {e}")
        return False

def execute_llm_action(step_config: Dict[str, Any], post_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute LLM action for workflow step.
    
    Args:
        step_config: Step configuration from database
        post_id: Post ID
        context: Execution context (section_ids, inputs, etc.)
    
    Returns:
        Execution results
    """
    log_file = "logs/llm_actions_script.log"
    
    # Set up logging
    logger = logging.getLogger('llm_actions_script')
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    # Log the button click
    logger.info("=== RUN LLM BUTTON CLICKED ===")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("Run LLM button clicked on purple LLM-actions panel")
    
    # Get step_id from context or step_config (like image_generation.py)
    step_id = context.get('step_id') or step_config.get('step_id')
    
    # Get checked sections from context - handle both formats
    checked_sections = []
    if 'checked_sections' in context:
        checked_sections = context.get('checked_sections', [])
    elif 'section_ids' in context:
        checked_sections = context.get('section_ids', [])
    
    # === BASIC IDENTIFICATION ===
    logger.info("=== BASIC IDENTIFICATION ===")
    logger.info(f"Post ID: {post_id}")
    logger.info(f"Step ID: {step_id}")
    logger.info(f"Checked Sections: {checked_sections}")
    logger.info(f"Section Count: {len(checked_sections)}")
    
    # === GLOBAL PROMPTS (Applied to every Section iteration) ===
    logger.info("=== GLOBAL PROMPTS (Applied to every Section iteration) ===")
    
    # Get prompt settings from context
    system_prompt = context.get('system_prompt', '')
    action_prompt = context.get('message_content', '')  # Changed from 'action_prompt' to 'message_content'
    
    # Log prompt selections with full content
    logger.info(f"System Prompt ID: {system_prompt}")
    logger.info(f"Action Prompt ID: {action_prompt}")
    
    # Fetch and log full prompt content from database
    try:
        # Database connection
        conn = psycopg2.connect(
            dbname="blog",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()
        
        # Fetch system prompt content
        if system_prompt:
            cursor.execute("SELECT name, prompt_text, system_prompt FROM llm_prompt WHERE id = %s", (system_prompt,))
            system_result = cursor.fetchone()
            if system_result:
                name, prompt_text, system_prompt_content = system_result
                logger.info(f"System Prompt Name: {name}")
                logger.info(f"System Prompt Content: {system_prompt_content or prompt_text}")
            else:
                logger.info(f"System Prompt Content: Not found in database")
        
        # Fetch action prompt content - since message_content is the actual content, not an ID
        if action_prompt:
            logger.info(f"Action Prompt Content: {action_prompt}")
        else:
            logger.info(f"Action Prompt Content: Not provided")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.info(f"Error fetching prompt content from database: {e}")
        logger.info("Note: Could not fetch full prompt content from database")
    
    logger.info("=== END GLOBAL PROMPTS ===")
    
    # === PER-SECTION FIELD MAPPINGS ===
    logger.info("=== PER-SECTION FIELD MAPPINGS ===")
    
    # Get field mappings from context
    input_field = context.get('input_field', 'draft')  # Default to draft if not specified
    output_field = context.get('output_field', '')
    
    # Get Live Preview text from context
    live_preview_text = context.get('message_content', '')  # Changed from 'live_preview_text' to 'message_content'
    
    # Get section-specific input contents from context
    section_input_contents = context.get('section_input_contents', {})
    
    # Log field mappings
    logger.info(f"Input Field: {input_field}")
    logger.info(f"Output Field: {output_field}")
    logger.info(f"Live Preview Text: {live_preview_text}")
    logger.info(f"Section Input Contents: {section_input_contents}")
    
    logger.info("=== END PER-SECTION FIELD MAPPINGS ===")
    
    # === LLM CONFIGURATION & ACTIONS ===
    logger.info("=== LLM CONFIGURATION & ACTIONS ===")
    
    # Fetch LLM configuration from database
    try:
        conn = psycopg2.connect(
            dbname="blog",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()
        
        # Get active LLM configuration
        cursor.execute("""
            SELECT provider_type, model_name, api_base, is_active
            FROM llm_config
            WHERE is_active = true
            ORDER BY id DESC
            LIMIT 1
        """)
        config_result = cursor.fetchone()
        
        if config_result:
            provider_type, model_name, api_base, is_active = config_result
            logger.info(f"LLM Provider (DB): {provider_type}")
            logger.info(f"LLM Model (DB): {model_name}")
            logger.info(f"LLM API Base (DB): {api_base}")
            logger.info(f"LLM Status (DB): {'Active' if is_active else 'Inactive'}")
        else:
            logger.info("LLM Configuration: No active configuration found in database")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.info(f"Error fetching LLM config from database: {e}")
    
    # Log hard-coded LLM parameters
    logger.info(f"LLM Temperature (Hard-coded): 0.7")
    logger.info(f"LLM Max Tokens (Hard-coded): 1000")
    logger.info(f"LLM Timeout (Hard-coded): 60s")
    
    logger.info("=== END LLM CONFIGURATION & ACTIONS ===")
    
    # === SECTION ITERATION PROCESSING ===
    logger.info("=== SECTION ITERATION PROCESSING ===")
    
    if not checked_sections:
        logger.info("No sections to process. Skipping iteration.")
        logger.info("=== END SECTION ITERATION PROCESSING ===")
        logger.info("=== END LOG ===")
        
        return {
            "success": True,
            "message": "No sections to process",
            "post_id": post_id,
            "checked_sections": checked_sections,
            "section_count": len(checked_sections)
        }
    
    # Initialize processing results
    processing_results = {
        "total_sections": len(checked_sections),
        "processed_sections": 0,
        "successful_sections": 0,
        "failed_sections": 0,
        "section_details": []
    }
    
    logger.info(f"Starting to process {len(checked_sections)} sections...")
    logger.info(f"Global System Prompt: {system_prompt}")
    logger.info(f"Global Action Prompt: {action_prompt}")
    logger.info(f"Per-Section Input Field: {input_field}")
    logger.info(f"Per-Section Output Field: {output_field}")
    
    # Iterate through each section one at a time (modeled on image_generation.py)
    for index, section_id in enumerate(checked_sections, 1):
        section_start_time = datetime.now()
        
        logger.info(f"Processing section {index}/{len(checked_sections)}: Section ID {section_id}")
        
        try:
            # Get the actual input content for this specific section
            section_input_content = section_input_contents.get(str(section_id), '[No input content available]')
            
            # If we don't have input content from context, fetch it from database
            if section_input_content == '[No input content available]':
                # We'll fetch this from the database later when we have the connection
                section_input_content = None
            
            # Extract plain text from HTML content if it's HTML
            import re
            if section_input_content and (section_input_content.startswith('<!DOCTYPE html>') or section_input_content.startswith('<html')):
                # Strip HTML tags to get plain text
                plain_text = re.sub(r'<[^>]+>', '', section_input_content)
                # Clean up extra whitespace and newlines
                plain_text = re.sub(r'\s+', ' ', plain_text).strip()
                section_input_content = plain_text
            
            # Create the actual message that will be sent to the LLM for this section
            # Replace the placeholder with the actual input content
            actual_message = live_preview_text.replace(
                "Input fields will be detected from the Inputs panel...",
                f"Input Content: {section_input_content}"
            )
            
            # Log the actual message that will be sent to the LLM for this section
            logger.info(f"=== PER SECTION {index}/{len(checked_sections)} ===")
            logger.info(f"Section ID: {section_id}")
            logger.info(f"Input Field: {input_field}")
            logger.info(f"Input Content for this section:")
            logger.info(f"{section_input_content}")
            logger.info(f"Message to be sent to LLM:")
            logger.info(f"{actual_message}")
            logger.info(f"=== END PER SECTION {index}/{len(checked_sections)} ===")
            
            # === ACTUAL LLM PROCESSING ===
            logger.info(f"Calling LLM for section {section_id}...")
            
            # Get LLM configuration
            conn = psycopg2.connect(
                dbname="blog",
                user="postgres",
                password="postgres",
                host="localhost",
                port="5432"
            )
            cursor = conn.cursor()
            
            # Fetch section input content from database if not provided in context
            if section_input_content is None:
                try:
                    cursor.execute(f"SELECT {input_field} FROM post_section WHERE id = %s", (section_id,))
                    result = cursor.fetchone()
                    if result and result[0]:
                        section_input_content = result[0]
                        # Extract plain text from HTML content if it's HTML
                        if section_input_content.startswith('<!DOCTYPE html>') or section_input_content.startswith('<html'):
                            plain_text = re.sub(r'<[^>]+>', '', section_input_content)
                            plain_text = re.sub(r'\s+', ' ', plain_text).strip()
                            section_input_content = plain_text
                    else:
                        section_input_content = '[No content found in database]'
                except Exception as e:
                    logger.error(f"Error fetching section input content: {e}")
                    section_input_content = '[Error fetching content]'
            
            # Fetch LLM configuration
            cursor.execute("SELECT provider_type, model_name, api_base, is_active FROM llm_config WHERE is_active = true LIMIT 1")
            llm_result = cursor.fetchone()
            
            if llm_result:
                provider_type, model_name, api_base, is_active = llm_result
                llm_config = {
                    "provider_type": provider_type,
                    "model_name": model_name,
                    "api_base": api_base,
                    "is_active": is_active,
                    "temperature": 0.7,  # Hard-coded as per log
                    "max_tokens": 1000,  # Hard-coded as per log
                    "timeout": 60        # Hard-coded as per log
                }
                
                # Get system prompt content
                system_prompt_content = ""
                if system_prompt:
                    cursor.execute("SELECT prompt_text, system_prompt FROM llm_prompt WHERE id = %s", (system_prompt,))
                    prompt_result = cursor.fetchone()
                    if prompt_result:
                        prompt_text, system_prompt_content = prompt_result
                        system_prompt_content = system_prompt_content or prompt_text
                
                # Call LLM
                llm_response = call_llm(system_prompt_content, actual_message, llm_config)
                
                if llm_response["success"]:
                    # Save response to output field
                    save_success = save_section_output(int(section_id), output_field, llm_response["content"], cursor, conn)
                    
                    if save_success:
                        logger.info(f"✓ LLM response saved to {output_field} for section {section_id}")
                        logger.info(f"LLM Response: {llm_response['content'][:200]}...")  # Log first 200 chars
                        
                        section_result = {
                            "section_id": section_id,
                            "status": "success",
                            "processing_time_seconds": (datetime.now() - section_start_time).total_seconds(),
                            "message": f"Section {section_id} processed successfully",
                            "llm_response": {
                                "content": llm_response["content"],
                                "usage": llm_response.get("usage", {}),
                                "model": llm_response.get("model", "")
                            },
                            "llm_input_data": {
                                "system_prompt": system_prompt,
                                "action_prompt": action_prompt,
                                "input_field": input_field,
                                "output_field": output_field,
                                "live_preview_text": live_preview_text
                            }
                        }
                    else:
                        logger.error(f"✗ Failed to save LLM response for section {section_id}")
                        section_result = {
                            "section_id": section_id,
                            "status": "error",
                            "processing_time_seconds": (datetime.now() - section_start_time).total_seconds(),
                            "message": f"Failed to save LLM response for section {section_id}",
                            "llm_response": llm_response
                        }
                else:
                    logger.error(f"✗ LLM call failed for section {section_id}: {llm_response.get('error', 'Unknown error')}")
                    section_result = {
                        "section_id": section_id,
                        "status": "error",
                        "processing_time_seconds": (datetime.now() - section_start_time).total_seconds(),
                        "message": f"LLM call failed: {llm_response.get('error', 'Unknown error')}",
                        "llm_response": llm_response
                    }
            else:
                logger.error(f"✗ No active LLM configuration found")
                section_result = {
                    "section_id": section_id,
                    "status": "error",
                    "processing_time_seconds": (datetime.now() - section_start_time).total_seconds(),
                    "message": "No active LLM configuration found",
                    "llm_response": {"success": False, "error": "No LLM config"}
                }
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"✗ Error processing section {section_id}: {e}")
            section_result = {
                "section_id": section_id,
                "status": "error",
                "processing_time_seconds": (datetime.now() - section_start_time).total_seconds(),
                "message": f"Error processing section {section_id}: {e}",
                "llm_input_data": {
                    "system_prompt": system_prompt,
                    "action_prompt": action_prompt,
                    "input_field": input_field,
                    "output_field": output_field,
                    "live_preview_text": live_preview_text
                }
            }
        
        # Update processing results based on section result status
        if section_result["status"] == "success":
            processing_results["successful_sections"] += 1
        else:
            processing_results["failed_sections"] += 1
        
        processing_results["section_details"].append(section_result)
        processing_results["processed_sections"] += 1
        
        section_duration = (datetime.now() - section_start_time).total_seconds()
        if section_result["status"] == "success":
            logger.info(f"✓ Section {section_id} processed successfully in {section_duration:.2f}s")
        else:
            logger.error(f"✗ Section {section_id} failed in {section_duration:.2f}s")
    
    logger.info(f"=== ITERATION COMPLETE ===")
    logger.info(f"Total Sections: {processing_results['total_sections']}")
    logger.info(f"Processed: {processing_results['processed_sections']}")
    logger.info(f"Successful: {processing_results['successful_sections']}")
    logger.info(f"Failed: {processing_results['failed_sections']}")
    logger.info("=== END SECTION ITERATION PROCESSING ===")
    
    # === DEBUG INFORMATION ===
    logger.info("=== DEBUG INFORMATION ===")
    
    # Context Keys: These are the data fields passed from the frontend to the backend
    # They represent what the user has configured in the purple LLM module interface
    logger.info(f"Context Keys (Frontend Settings): {list(context.keys())}")
    logger.info("Context Keys Explanation: These are the settings/values passed from the frontend interface")
    
    # Step Config Keys: These are configuration settings from the database for this workflow step
    # They define what options are available and how the step should behave
    logger.info(f"Step Config Keys (Database Config): {list(step_config.keys()) if step_config else 'None'}")
    logger.info("Step Config Keys Explanation: These are database configuration settings for this workflow step")
    
    # Log any other settings that might be in context
    for key, value in context.items():
        if key not in ['checked_sections', 'system_prompt', 'action_prompt', 'input_field', 'output_field', 'step_id']:
            logger.info(f"Additional Context Setting - {key}: {value}")
    
    logger.info("=== END DEBUG INFORMATION ===")
    logger.info("=== END LOG ===")
    
    return {
        "success": True,
        "message": "Section iteration processing completed",
        "post_id": post_id,
        "checked_sections": checked_sections,
        "section_count": len(checked_sections),
        "processing_results": processing_results
    } 