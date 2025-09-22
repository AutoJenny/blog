"""
Image Generation Handler - Two Phase Process

Phase 1: Simple Detection - collects post ID and checked section IDs from context.
Phase 2: Section Processing - iterates through each selected section and processes them one at a time.
"""

from typing import Dict, Any, List
import json
import logging
import requests
from datetime import datetime
import os
import time
import psycopg
from psycopg.rows import dict_row

def get_db_conn():
    """Get database connection."""
    return psycopg.connect(
        host="localhost",
        database="blog",
        user="nickfiddes",
        password=""
    )

def get_step_prompts(step_id: int) -> Dict[str, Any]:
    """
    Get both task prompt and system prompt for the current workflow step.
    
    Args:
        step_id: The workflow step ID
        
    Returns:
        Dictionary containing task prompt and system prompt information
    """
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Get both task prompt and system prompt for the step
            cur.execute("""
                SELECT 
                    wsp.task_prompt_id,
                    wsp.system_prompt_id,
                    task_lp.name as task_prompt_name,
                    task_lp.prompt_text as task_prompt_text,
                    task_lp.description as task_prompt_description,
                    sys_lp.name as system_prompt_name,
                    sys_lp.prompt_text as system_prompt_text,
                    sys_lp.description as system_prompt_description
                FROM workflow_step_prompt wsp
                LEFT JOIN llm_prompt task_lp ON task_lp.id = wsp.task_prompt_id
                LEFT JOIN llm_prompt sys_lp ON sys_lp.id = wsp.system_prompt_id
                WHERE wsp.step_id = %s
            """, (step_id,))
            
            result = cur.fetchone()
            
            if result:
                return {
                    "task_prompt_id": result['task_prompt_id'],
                    "task_prompt_name": result['task_prompt_name'],
                    "task_prompt_text": result['task_prompt_text'],
                    "task_prompt_description": result['task_prompt_description'],
                    "system_prompt_id": result['system_prompt_id'],
                    "system_prompt_name": result['system_prompt_name'],
                    "system_prompt_text": result['system_prompt_text'],
                    "system_prompt_description": result['system_prompt_description']
                }
            else:
                return {
                    "task_prompt_id": None,
                    "task_prompt_name": "No task prompt configured",
                    "task_prompt_text": "No task prompt found for this step",
                    "task_prompt_description": None,
                    "system_prompt_id": None,
                    "system_prompt_name": "No system prompt configured",
                    "system_prompt_text": "No system prompt found for this step",
                    "system_prompt_description": None
                }
                
    except Exception as e:
        logging.error(f"Error getting step prompts: {str(e)}")
        return {
            "task_prompt_id": None,
            "task_prompt_name": "Error retrieving task prompt",
            "task_prompt_text": f"Error: {str(e)}",
            "task_prompt_description": None,
            "system_prompt_id": None,
            "system_prompt_name": "Error retrieving system prompt",
            "system_prompt_text": f"Error: {str(e)}",
            "system_prompt_description": None
        }

def get_section_image_prompts(post_id: int, section_id: int) -> Dict[str, Any]:
    """
    Get the image_prompts for a specific section.
    
    Args:
        post_id: The post ID
        section_id: The section ID
        
    Returns:
        Dictionary containing only the image_prompts content
    """
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Get ONLY image_prompts for the section
            cur.execute("""
                SELECT image_prompts
                FROM post_section 
                WHERE id = %s AND post_id = %s
            """, (section_id, post_id))
            
            result = cur.fetchone()
            
            if result:
                return {
                    "section_id": section_id,
                    "image_prompts": result['image_prompts']
                }
            else:
                return {
                    "section_id": section_id,
                    "image_prompts": None
                }
                
    except Exception as e:
        logging.error(f"Error getting section image_prompts: {str(e)}")
        return {
            "section_id": section_id,
            "image_prompts": None
        }

def send_to_dalle(system_prompt: str, task_prompt: str, image_prompts: str) -> Dict[str, Any]:
    """
    Send content to DALL-E for image generation.
    
    Args:
        system_prompt: System prompt text
        task_prompt: Task prompt text  
        image_prompts: Image prompts content
        
    Returns:
        Dictionary containing DALL-E response
    """
    try:
        # Load OpenAI API key from environment
        api_key = os.getenv("OPENAI_AUTH_TOKEN")
        if not api_key:
            raise Exception("OPENAI_AUTH_TOKEN not found in environment")
        
        # Construct the full prompt for DALL-E
        full_prompt = f"{task_prompt}\n\n{image_prompts}"
        
        # Log the complete message being sent to DALL-E
        dalle_message = {
            "model": "dall-e-3",
            "prompt": full_prompt,
            "size": "1792x1024",
            "quality": "standard",
            "n": 1
        }
        
        logging.info("=== DALL-E MESSAGE BEING SENT ===")
        logging.info(f"API Key: {api_key[:10]}...")
        logging.info(f"Model: {dalle_message['model']}")
        logging.info(f"Size: {dalle_message['size']}")
        logging.info(f"Quality: {dalle_message['quality']}")
        logging.info(f"Full Prompt: {full_prompt}")
        logging.info("=== END DALL-E MESSAGE ===")
        
        # Prepare the request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Make the API call
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json=dalle_message,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            logging.info(f"DALL-E API call successful: {result}")
            return {
                "success": True,
                "response": result,
                "image_url": result.get("data", [{}])[0].get("url") if result.get("data") else None
            }
        else:
            error_msg = f"DALL-E API request failed with status {response.status_code}: {response.text}"
            logging.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "response": response.text
            }
            
    except Exception as e:
        error_msg = f"DALL-E integration failed: {str(e)}"
        logging.error(error_msg)
        return {
            "success": False,
            "error": error_msg
        }

def store_llm_response(post_id: int, section_id: int, llm_input_data: Dict[str, Any], llm_output: Dict[str, Any]) -> str:
    """
    Store LLM response and download generated image in the specified directory structure.
    
    Args:
        post_id: The post ID
        section_id: The section ID
        llm_input_data: The input data sent to LLM
        llm_output: The output received from LLM
        
    Returns:
        Path to the stored image file
    """
    try:
        # Create directory structure in blog-images service
        base_dir = f"../blog-images/static/content/posts/{post_id}/sections/{section_id}/raw"
        os.makedirs(base_dir, exist_ok=True)
        
        # Create timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Store JSON response
        json_filename = f"dalle_response_{timestamp}.json"
        json_filepath = os.path.join(base_dir, json_filename)
        
        # Prepare data to store
        stored_data = {
            "timestamp": datetime.now().isoformat(),
            "post_id": post_id,
            "section_id": section_id,
            "llm_input_data": llm_input_data,
            "llm_output": llm_output
        }
        
        # Write JSON to file
        with open(json_filepath, 'w') as f:
            json.dump(stored_data, f, indent=2)
        
        logging.info(f"LLM response JSON stored at: {json_filepath}")
        
        # Download and store the generated image
        if llm_output.get('success') and llm_output.get('image_url'):
            image_url = llm_output['image_url']
            
            # Download the image
            logging.info(f"Downloading image from: {image_url}")
            image_response = requests.get(image_url, timeout=60)
            
            if image_response.status_code == 200:
                # Determine image format from URL or content-type
                if 'png' in image_url.lower():
                    image_ext = 'png'
                elif 'jpg' in image_url.lower() or 'jpeg' in image_url.lower():
                    image_ext = 'jpg'
                else:
                    # Default to PNG
                    image_ext = 'png'
                
                # Create image filename
                image_filename = f"generated_image_{timestamp}.{image_ext}"
                image_filepath = os.path.join(base_dir, image_filename)
                
                # Save the image
                with open(image_filepath, 'wb') as f:
                    f.write(image_response.content)
                
                logging.info(f"Generated image stored at: {image_filepath}")
                
                # Update the stored data to include local image path
                stored_data['local_image_path'] = image_filepath
                stored_data['local_image_filename'] = image_filename
                
                # Update the JSON file with the local image path
                with open(json_filepath, 'w') as f:
                    json.dump(stored_data, f, indent=2)
                
                return image_filepath
            else:
                logging.error(f"Failed to download image: HTTP {image_response.status_code}")
                return json_filepath
        else:
            logging.warning("No image URL found in LLM output")
            return json_filepath
        
    except Exception as e:
        logging.error(f"Error storing LLM response: {str(e)}")
        return None

def execute_image_generation(step_config: Dict[str, Any], post_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Two-phase process:
    Phase 1: Simple detection - collect post ID and checked section IDs
    Phase 2: Section processing - iterate through each section and process them one at a time
    
    Args:
        step_config: Step configuration from database
        post_id: Post ID
        context: Execution context (section_ids, inputs, etc.)
    
    Returns:
        Processing results with post ID, checked sections, and processing details
    """
    start_time = datetime.now()
    
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    # Log file path
    log_file_path = os.path.join(logs_dir, "section_illustrations_script.log")
    
    # ========================================
    # PHASE 1: SIMPLE DETECTION
    # ========================================
    
    # Get checked sections from context
    checked_sections = context.get('section_ids', [])
    
    # Log detection information
    detection_info = {
        "timestamp": datetime.now().isoformat(),
        "function": "execute_image_generation",
        "post_id": post_id,
        "checked_sections": checked_sections,
        "section_count": len(checked_sections)
    }
    
    # Write Phase 1 to log file (overwrites each time)
    with open(log_file_path, 'w') as f:
        f.write("=== SECTION ILLUSTRATIONS SCRIPT - PHASE 1: SIMPLE DETECTION ===\n")
        f.write(f"Timestamp: {detection_info['timestamp']}\n")
        f.write(f"Post ID: {detection_info['post_id']}\n")
        f.write(f"Checked Sections: {detection_info['checked_sections']}\n")
        f.write(f"Section Count: {detection_info['section_count']}\n")
        f.write("=== END PHASE 1 ===\n\n")
    
    # Also log to console
    logging.info(f"=== PHASE 1: SIMPLE DETECTION ===")
    logging.info(f"Post ID: {post_id}")
    logging.info(f"Checked Sections: {checked_sections}")
    logging.info(f"Section Count: {len(checked_sections)}")
    
    # ========================================
    # PHASE 2: SECTION PROCESSING
    # ========================================
    
    if not checked_sections:
        logging.info("No sections to process. Skipping Phase 2.")
        with open(log_file_path, 'a') as f:
            f.write("=== PHASE 2: SECTION PROCESSING ===\n")
            f.write("No sections to process. Skipping Phase 2.\n")
            f.write("=== END PHASE 2 ===\n")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        return {
            "success": True,
            "post_id": post_id,
            "checked_sections": checked_sections,
            "section_count": len(checked_sections),
            "detection_info": detection_info,
            "processing_results": {"message": "No sections to process"},
            "execution_time_seconds": execution_time,
            "log_file": log_file_path
        }
    
    # Get step_id from context or step_config
    step_id = context.get('step_id') or step_config.get('step_id', 55)  # Default to section_illustrations step
    
    # Get both task prompt and system prompt for this step
    step_prompts_info = get_step_prompts(step_id)
    
    # Initialize processing results
    processing_results = {
        "total_sections": len(checked_sections),
        "processed_sections": 0,
        "successful_sections": 0,
        "failed_sections": 0,
        "section_details": [],
        "step_prompts_info": step_prompts_info
    }
    
    # Log Phase 2 start
    phase2_start = datetime.now()
    logging.info(f"=== PHASE 2: SECTION PROCESSING ===")
    logging.info(f"Starting to process {len(checked_sections)} sections...")
    logging.info(f"Task Prompt: {step_prompts_info['task_prompt_name']}")
    logging.info(f"System Prompt: {step_prompts_info['system_prompt_name']}")
    
    with open(log_file_path, 'a') as f:
        f.write("=== PHASE 2: SECTION PROCESSING ===\n")
        f.write(f"Phase 2 Start Time: {phase2_start.isoformat()}\n")
        f.write(f"Total Sections to Process: {len(checked_sections)}\n")
        f.write(f"Sections: {checked_sections}\n")
        f.write(f"Step ID: {step_id}\n")
        f.write(f"Task Prompt ID: {step_prompts_info['task_prompt_id']}\n")
        f.write(f"Task Prompt Name: {step_prompts_info['task_prompt_name']}\n")
        f.write(f"Task Prompt Text: {step_prompts_info['task_prompt_text']}\n")
        f.write(f"System Prompt ID: {step_prompts_info['system_prompt_id']}\n")
        f.write(f"System Prompt Name: {step_prompts_info['system_prompt_name']}\n")
        f.write(f"System Prompt Text: {step_prompts_info['system_prompt_text']}\n")
        f.write("-" * 50 + "\n")
    
    # Iterate through each section one at a time
    for index, section_id in enumerate(checked_sections, 1):
        section_start_time = datetime.now()
        
        logging.info(f"Processing section {index}/{len(checked_sections)}: Section ID {section_id}")
        
        with open(log_file_path, 'a') as f:
            f.write(f"\n--- Processing Section {index}/{len(checked_sections)} ---\n")
            f.write(f"Section ID: {section_id}\n")
            f.write(f"Start Time: {section_start_time.isoformat()}\n")
        
        try:
            # Get section image_prompts
            section_data = get_section_image_prompts(post_id, section_id)
            
            # Log the data that will be sent to the LLM
            llm_input_data = {
                "system_prompt": step_prompts_info['system_prompt_text'],
                "task_prompt": step_prompts_info['task_prompt_text'],
                "image_prompts": section_data['image_prompts']
            }
            
            logging.info(f"Section {section_id} data collected:")
            logging.info(f"  - Image Prompts: {section_data['image_prompts']}")
            
            with open(log_file_path, 'a') as f:
                f.write(f"LLM Input Data (as will be sent to LLM):\n")
                f.write(f"  System Prompt: {llm_input_data['system_prompt']}\n")
                f.write(f"  Task Prompt: {llm_input_data['task_prompt']}\n")
                f.write(f"  Image Prompts: {llm_input_data['image_prompts']}\n")
            
            # Send to DALL-E and get response
            logging.info(f"Sending section {section_id} to DALL-E...")
            dalle_response = send_to_dalle(
                system_prompt=llm_input_data['system_prompt'],
                task_prompt=llm_input_data['task_prompt'],
                image_prompts=llm_input_data['image_prompts']
            )
            
            # Store the response
            stored_file_path = store_llm_response(
                post_id=post_id,
                section_id=section_id,
                llm_input_data=llm_input_data,
                llm_output=dalle_response
            )
            
            # Determine processing result
            if dalle_response.get('success'):
                section_result = {
                    "section_id": section_id,
                    "status": "success",
                    "processing_time_seconds": (datetime.now() - section_start_time).total_seconds(),
                    "message": f"Section {section_id} processed successfully with DALL-E",
                    "llm_input_data": llm_input_data,
                    "llm_output": dalle_response,
                    "stored_file_path": stored_file_path,
                    "image_url": dalle_response.get('image_url')
                }
                processing_results["successful_sections"] += 1
            else:
                section_result = {
                    "section_id": section_id,
                    "status": "failed",
                    "processing_time_seconds": (datetime.now() - section_start_time).total_seconds(),
                    "message": f"Section {section_id} failed: {dalle_response.get('error', 'Unknown error')}",
                    "llm_input_data": llm_input_data,
                    "llm_output": dalle_response,
                    "stored_file_path": stored_file_path
                }
                processing_results["failed_sections"] += 1
            
            processing_results["section_details"].append(section_result)
            
            section_end_time = datetime.now()
            section_duration = (section_end_time - section_start_time).total_seconds()
            
            if dalle_response.get('success'):
                logging.info(f"✓ Section {section_id} processed successfully with DALL-E in {section_duration:.2f}s")
                logging.info(f"  Image URL: {dalle_response.get('image_url', 'No URL returned')}")
            else:
                logging.error(f"✗ Section {section_id} failed: {dalle_response.get('error', 'Unknown error')}")
            
            with open(log_file_path, 'a') as f:
                f.write(f"Status: {section_result['status'].upper()}\n")
                f.write(f"Processing Time: {section_duration:.2f} seconds\n")
                f.write(f"Message: {section_result['message']}\n")
                f.write(f"DALL-E Success: {dalle_response.get('success', False)}\n")
                if dalle_response.get('success'):
                    f.write(f"Image URL: {dalle_response.get('image_url', 'No URL returned')}\n")
                else:
                    f.write(f"DALL-E Error: {dalle_response.get('error', 'Unknown error')}\n")
                f.write(f"Stored File: {stored_file_path}\n")
                f.write(f"End Time: {section_end_time.isoformat()}\n")
            
        except Exception as e:
            # Handle processing errors
            section_result = {
                "section_id": section_id,
                "status": "failed",
                "error": str(e),
                "message": f"Section {section_id} processing failed: {str(e)}"
            }
            
            processing_results["failed_sections"] += 1
            processing_results["section_details"].append(section_result)
            
            section_end_time = datetime.now()
            section_duration = (section_end_time - section_start_time).total_seconds()
            
            logging.error(f"✗ Section {section_id} failed after {section_duration:.2f}s: {str(e)}")
            
            with open(log_file_path, 'a') as f:
                f.write(f"Status: FAILED\n")
                f.write(f"Processing Time: {section_duration:.2f} seconds\n")
                f.write(f"Error: {str(e)}\n")
                f.write(f"End Time: {section_end_time.isoformat()}\n")
        
        processing_results["processed_sections"] += 1
        
        # Add a small delay between sections to avoid overwhelming the system
        if index < len(checked_sections):
            time.sleep(0.5)  # 0.5 second delay between sections
    
    # Log Phase 2 completion
    phase2_end = datetime.now()
    phase2_duration = (phase2_end - phase2_start).total_seconds()
    
    logging.info(f"=== PHASE 2 COMPLETED ===")
    logging.info(f"Total Processing Time: {phase2_duration:.2f} seconds")
    logging.info(f"Successful: {processing_results['successful_sections']}/{processing_results['total_sections']}")
    logging.info(f"Failed: {processing_results['failed_sections']}/{processing_results['total_sections']}")
    
    with open(log_file_path, 'a') as f:
        f.write("\n" + "=" * 50 + "\n")
        f.write("=== PHASE 2 SUMMARY ===\n")
        f.write(f"Phase 2 End Time: {phase2_end.isoformat()}\n")
        f.write(f"Total Processing Time: {phase2_duration:.2f} seconds\n")
        f.write(f"Total Sections: {processing_results['total_sections']}\n")
        f.write(f"Successfully Processed: {processing_results['successful_sections']}\n")
        f.write(f"Failed: {processing_results['failed_sections']}\n")
        f.write("=== END PHASE 2 ===\n")
    
    # Calculate total execution time
    execution_time = (datetime.now() - start_time).total_seconds()
    
    return {
        "success": True,
        "post_id": post_id,
        "checked_sections": checked_sections,
        "section_count": len(checked_sections),
        "detection_info": detection_info,
        "processing_results": processing_results,
        "execution_time_seconds": execution_time,
        "log_file": log_file_path
    } 