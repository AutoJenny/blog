"""
Image Generation Handler

Handles execution of image generation for workflow steps.
"""

from typing import Dict, Any, List
import requests
import json
import logging
from datetime import datetime

def get_section_content(section_id: int) -> Dict[str, Any]:
    """
    Get section content from database.
    
    Args:
        section_id: Section ID
    
    Returns:
        Section content dictionary
    """
    from db import get_db_conn
    import psycopg2.extras
    
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT title, content, summary
                    FROM post_section
                    WHERE id = %s
                """, (section_id,))
                result = cur.fetchone()
                
                if result:
                    return {
                        "title": result['title'],
                        "content": result['content'],
                        "summary": result['summary']
                    }
                else:
                    logging.warning(f"Section {section_id} not found in database")
                    return {"title": f"Section {section_id}", "content": "", "summary": ""}
    except Exception as e:
        logging.error(f"Database error getting section {section_id} content: {e}")
        return {"title": f"Section {section_id}", "content": "", "summary": ""}

def generate_image_prompt(section_content: Dict[str, Any], parameters: Dict[str, Any], task_prompt: str = "") -> str:
    """
    Generate image prompt from section content.
    
    Args:
        section_content: Section title, content, summary
        parameters: Generation parameters
        task_prompt: Optional task prompt from user
    
    Returns:
        Generated image prompt
    """
    # Use section title as primary prompt, fallback to summary, then content
    title = section_content.get('title', '')
    summary = section_content.get('summary', '')
    content = section_content.get('content', '')
    
    # Log the inputs
    logging.info(f"=== PROMPT GENERATION DEBUG ===")
    logging.info(f"Section content: {section_content}")
    logging.info(f"Parameters: {parameters}")
    logging.info(f"Task prompt: {task_prompt}")
    
    # If task_prompt is provided, use it exactly as provided
    if task_prompt and task_prompt.strip():
        base_prompt = task_prompt.strip()
        logging.info(f"Using task prompt exactly as provided: {base_prompt}")
        return base_prompt
    else:
        # Use section title as primary prompt, fallback to summary, then content
        base_prompt = title if title else (summary if summary else content[:100])
        logging.info(f"Using section content as base: {base_prompt}")
        return base_prompt

def call_blog_images_service(post_id: int, section_id: int, prompt: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call blog-images service to generate image.
    
    Args:
        post_id: Post ID
        section_id: Section ID
        prompt: Image generation prompt
        parameters: Generation parameters
    
    Returns:
        Service response
    """
    try:
        url = "http://localhost:5005/api/images/generate"
        payload = {
            "prompt": prompt,
            "post_id": post_id,
            "section_id": section_id,
            "size": parameters.get('size', '1024x1024'),
            "model": parameters.get('model', 'dall-e-3')
        }
        
        logging.info(f"Calling blog-images service for section {section_id} with prompt: {prompt[:50]}...")
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        logging.info(f"Blog-images service response for section {section_id}: {result.get('status', 'unknown')}")
        return result
        
    except requests.exceptions.Timeout:
        logging.error(f"Timeout calling blog-images service for section {section_id}")
        raise Exception(f"Blog-images service timeout for section {section_id}")
    except requests.exceptions.ConnectionError:
        logging.error(f"Connection error calling blog-images service for section {section_id}")
        raise Exception(f"Blog-images service connection error for section {section_id}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Blog-images service error for section {section_id}: {str(e)}")
        raise Exception(f"Blog-images service error for section {section_id}: {str(e)}")

def update_section_image_metadata(section_id: int, image_filename: str) -> bool:
    """
    Update section with image metadata.
    
    Args:
        section_id: Section ID
        image_filename: Generated image filename
        prompt: Used prompt
    
    Returns:
        Success status
    """
    from db import get_db_conn
    from datetime import datetime
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Check if image_filename column exists, if not add it
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'post_section' 
                    AND column_name = 'image_filename'
                """)
                
                if not cur.fetchone():
                    logging.info("Adding image metadata columns to post_section table")
                    # Add the column if it doesn't exist
                    cur.execute("""
                        ALTER TABLE post_section 
                        ADD COLUMN image_filename VARCHAR(255),
                        ADD COLUMN image_generated_at TIMESTAMP
                    """)
                    conn.commit()
                
                # Update the section with image metadata
                cur.execute("""
                    UPDATE post_section 
                    SET image_filename = %s, 
                        image_generated_at = %s
                    WHERE id = %s
                """, (image_filename, datetime.now(), section_id))
                
                conn.commit()
                logging.info(f"Updated image metadata for section {section_id}: {image_filename}")
                return True
                
    except Exception as e:
        logging.error(f"Database error updating section {section_id} metadata: {e}")
        return False

def execute_image_generation(step_config: Dict[str, Any], post_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute image generation for workflow step.
    
    Args:
        step_config: Step configuration from database
        post_id: Post ID
        context: Execution context (section_ids, inputs, etc.)
    
    Returns:
        Execution results
    """
    start_time = datetime.now()
    
    # Enhanced logging for debugging
    logging.info(f"=== IMAGE GENERATION DEBUG START ===")
    logging.info(f"Post ID: {post_id}")
    logging.info(f"Step config: {step_config}")
    logging.info(f"Context: {context}")
    logging.info(f"Section IDs received: {context.get('section_ids', [])}")
    logging.info(f"Task prompt: {context.get('task_prompt', 'N/A')}")
    
    # Initialize comprehensive execution log
    execution_log = {
        'timestamp': datetime.now().isoformat(),
        'function': 'execute_image_generation',
        'post_id': post_id,
        'step_config': step_config,
        'context': context,
        'execution_steps': []
    }
    
    # Log to file for detailed debugging
    log_dir = '/Users/nickfiddes/Code/projects/blog/blog-images/logs'
    import os
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'llm_message.log')
    
    with open(log_file, 'w') as f:
        f.write("=== COMPREHENSIVE IMAGE GENERATION EXECUTION LOG ===\n")
        f.write(f"Timestamp: {execution_log['timestamp']}\n")
        f.write(f"Function: {execution_log['function']}\n")
        f.write(f"Post ID: {post_id}\n")
        f.write(f"Step Config: {json.dumps(step_config, indent=2)}\n\n")
        f.write(f"Context: {json.dumps(context, indent=2)}\n\n")
        f.write(f"Section IDs: {context.get('section_ids', [])}\n")
        f.write(f"Task prompt: {context.get('task_prompt', 'N/A')}\n\n")
    
    logging.info(f"Starting image generation for post {post_id} with {len(context.get('section_ids', []))} sections")
    logging.info(f"Comprehensive log written to: {log_file}")
    
    try:
        execution_log['execution_steps'].append({
            'step': 'initialization',
            'status': 'started'
        })
        
        script_config = step_config.get('script_config', {})
        parameters = script_config.get('parameters', {})
        section_ids = context.get('section_ids', [])
        
        execution_log['execution_steps'][-1].update({
            'status': 'success',
            'script_config': script_config,
            'parameters': parameters,
            'section_ids_count': len(section_ids),
            'section_ids': section_ids
        })
        
        if not section_ids:
            execution_log['execution_steps'].append({
                'step': 'validation',
                'status': 'error',
                'error': 'No section_ids provided in context'
            })
            
            # Update log file with error
            with open(log_file, 'a') as f:
                f.write(f"ERROR: No section_ids provided in context\n")
                f.write(f"Execution Steps: {json.dumps(execution_log['execution_steps'], indent=2)}\n\n")
            
            logging.error("No section_ids provided in context")
            raise ValueError("No section_ids provided in context")
        
        execution_log['execution_steps'].append({
            'step': 'section_processing',
            'status': 'started',
            'sections_to_process': len(section_ids)
        })
        
        logging.info(f"Processing {len(section_ids)} sections: {section_ids}")
        
        results = []
        successful_generations = 0
        failed_generations = 0
        
        for section_id in section_ids:
            try:
                logging.info(f"Processing section {section_id}")
                
                # Get section content
                section_content = get_section_content(section_id)
                
                # Generate image prompt
                task_prompt = context.get('task_prompt', '')
                prompt = generate_image_prompt(section_content, parameters, task_prompt)
                logging.info(f"Generated prompt for section {section_id}: {prompt[:100]}...")
                
                # Call blog-images service
                logging.info(f"Calling blog-images service for section {section_id} with prompt: {prompt}")
                service_response = call_blog_images_service(post_id, section_id, prompt, parameters)
                logging.info(f"Blog-images service response for section {section_id}: {service_response}")
                
                if service_response.get('status') == 'success':
                    # Extract image filename from response
                    image_data = service_response.get('data', {})
                    image_filename = image_data.get('filename', '')
                    
                    # Update section metadata
                    metadata_updated = update_section_image_metadata(section_id, image_filename)
                    
                    results.append({
                        "section_id": section_id,
                        "status": "success",
                        "prompt": prompt,
                        "image_filename": image_filename,
                        "metadata_updated": metadata_updated,
                        "service_response": service_response
                    })
                    successful_generations += 1
                    logging.info(f"Successfully generated image for section {section_id}: {image_filename}")
                else:
                    error_msg = service_response.get('message', 'Unknown error')
                    logging.error(f"Blog-images service failed for section {section_id}: {error_msg}")
                    results.append({
                        "section_id": section_id,
                        "status": "failed",
                        "error": error_msg,
                        "service_response": service_response
                    })
                    failed_generations += 1
                    
            except Exception as e:
                logging.error(f"Error processing section {section_id}: {str(e)}")
                results.append({
                    "section_id": section_id,
                    "status": "failed",
                    "error": str(e)
                })
                failed_generations += 1
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        execution_log['execution_steps'][-1].update({
            'status': 'success',
            'successful_generations': successful_generations,
            'failed_generations': failed_generations,
            'execution_time_seconds': execution_time
        })
        
        execution_log['final_results'] = {
            'sections_processed': section_ids,
            'successful_generations': successful_generations,
            'failed_generations': failed_generations,
            'results': results,
            'execution_time_seconds': execution_time
        }
        
        # Update log file with final results
        with open(log_file, 'a') as f:
            f.write(f"=== FINAL RESULTS ===\n")
            f.write(f"Execution Time: {execution_time:.2f} seconds\n")
            f.write(f"Successful Generations: {successful_generations}\n")
            f.write(f"Failed Generations: {failed_generations}\n")
            f.write(f"Execution Steps: {json.dumps(execution_log['execution_steps'], indent=2)}\n\n")
            f.write(f"Final Results: {json.dumps(results, indent=2)}\n\n")
        
        logging.info(f"Image generation completed for post {post_id}: {successful_generations} successful, {failed_generations} failed in {execution_time:.2f}s")
        
        return {
            "status": "success",
            "post_id": post_id,
            "section_ids": section_ids,
            "parameters": parameters,
            "message": f"Image generation completed: {successful_generations} successful, {failed_generations} failed",
            "result": {
                "sections_processed": section_ids,
                "successful_generations": successful_generations,
                "failed_generations": failed_generations,
                "results": results,
                "action_type": "image_generation",
                "service": "blog-images",
                "execution_time_seconds": execution_time
            },
            "execution_log": execution_log
        }
        
    except Exception as e:
        execution_log['execution_steps'].append({
            'step': 'error_handling',
            'status': 'error',
            'error': str(e),
            'error_type': 'Exception'
        })
        
        # Update log file with error
        with open(log_file, 'a') as f:
            f.write(f"=== ERROR LOG ===\n")
            f.write(f"Error: {str(e)}\n")
            f.write(f"Execution Steps: {json.dumps(execution_log['execution_steps'], indent=2)}\n\n")
        
        logging.error(f"Image generation execution failed for post {post_id}: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Image generation execution failed",
            "execution_log": execution_log
        } 