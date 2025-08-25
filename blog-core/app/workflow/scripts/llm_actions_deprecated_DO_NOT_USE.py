"""
LLM Action Handler

Handles execution of LLM actions for workflow steps.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any
import psycopg2
import psycopg2.extras

def get_db_conn():
    """Get database connection."""
    return psycopg2.connect(
        host='localhost',
        database='blog',
        user='nickfiddes',
        password=''
    )

def get_step_prompts(step_id: int) -> Dict[str, Any]:
    """Get task and system prompts for the step."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT wsp.task_prompt_id, wsp.system_prompt_id,
                       tp.name as task_prompt_name, tp.text as task_prompt_text,
                       sp.name as system_prompt_name, sp.text as system_prompt_text
                FROM workflow_step_prompt wsp
                LEFT JOIN llm_prompt tp ON wsp.task_prompt_id = tp.id
                LEFT JOIN llm_prompt sp ON wsp.system_prompt_id = sp.id
                WHERE wsp.step_id = %s
            """, (step_id,))
            
            result = cur.fetchone()
            if result:
                return {
                    'task_prompt_id': result['task_prompt_id'],
                    'task_prompt_name': result['task_prompt_name'],
                    'task_prompt_text': result['task_prompt_text'],
                    'system_prompt_id': result['system_prompt_id'],
                    'system_prompt_name': result['system_prompt_name'],
                    'system_prompt_text': result['system_prompt_text']
                }
            else:
                print(f"WARNING: No prompts found for step {step_id}")
                return {}
                
    except Exception as e:
        print(f"ERROR: Database error getting step {step_id} prompts: {e}")
        return {}

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
    # Get step_id from context or step_config
    step_id = context.get('step_id') or step_config.get('step_id')
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
    
    # Use logger instead of logging
    def log_info(message):
        logger.info(message)
        print(message)
    
    def log_error(message):
        logger.error(message)
        print(f"ERROR: {message}")
    
    # Phase 1: Simple Detection
    log_info("=== LLM ACTIONS SCRIPT - PHASE 1: SIMPLE DETECTION ===")
    log_info(f"Timestamp: {datetime.now().isoformat()}")
    log_info(f"Post ID: {post_id}")
    log_info(f"Step ID: {step_id}")
    
    checked_sections = context.get('section_ids', [])
    log_info(f"Checked Sections: {checked_sections}")
    log_info(f"Section Count: {len(checked_sections)}")
    log_info("=== END PHASE 1 ===\n")
    
    # Phase 2: Section Processing
    log_info("=== PHASE 2: SECTION PROCESSING ===")
    phase2_start = datetime.now()
    log_info(f"Phase 2 Start Time: {phase2_start.isoformat()}")
    log_info(f"Total Sections to Process: {len(checked_sections)}")
    log_info(f"Sections: {checked_sections}")
    
    # Get step prompts
    prompts = get_step_prompts(step_id) if step_id else {}
    log_info(f"Step ID: {step_id}")
    log_info(f"Task Prompt ID: {prompts.get('task_prompt_id')}")
    log_info(f"Task Prompt Name: {prompts.get('task_prompt_name')}")
    log_info(f"Task Prompt Text: {prompts.get('task_prompt_text')}")
    log_info(f"System Prompt ID: {prompts.get('system_prompt_id')}")
    log_info(f"System Prompt Name: {prompts.get('system_prompt_name')}")
    log_info(f"System Prompt Text: {prompts.get('system_prompt_text')}")
    log_info("-" * 50)
    
    processing_results = {
        'total_sections': len(checked_sections),
        'processed_sections': 0,
        'successful_sections': 0,
        'failed_sections': 0,
        'section_details': [],
        'step_prompts_info': prompts
    }
    
    # Process each section
    for i, section_id in enumerate(checked_sections, 1):
        section_start = datetime.now()
        log_info(f"\n--- Processing Section {i}/{len(checked_sections)} ---")
        log_info(f"Section ID: {section_id}")
        log_info(f"Start Time: {section_start.isoformat()}")
        
        try:
            # Prepare LLM input data
            llm_input_data = {
                'system_prompt': prompts.get('system_prompt_text', ''),
                'task_prompt': prompts.get('task_prompt_text', ''),
                'section_id': section_id,
                'post_id': post_id,
                'step_id': step_id
            }
            
            log_info("LLM Input Data (as will be sent to LLM):")
            log_info(f"  System Prompt: {llm_input_data['system_prompt']}")
            log_info(f"  Task Prompt: {llm_input_data['task_prompt']}")
            log_info(f"  Section ID: {llm_input_data['section_id']}")
            log_info(f"  Post ID: {llm_input_data['post_id']}")
            log_info(f"  Step ID: {llm_input_data['step_id']}")
            
            # TODO: Add actual LLM processing here
            # For now, simulate processing
            processing_time = (datetime.now() - section_start).total_seconds()
            
            section_result = {
                'section_id': section_id,
                'status': 'SUCCESS',
                'processing_time_seconds': processing_time,
                'message': f"Section {section_id} processed successfully (placeholder)",
                'llm_input_data': llm_input_data,
                'llm_output': {
                    'success': True,
                    'response': 'Placeholder LLM response',
                    'error': None
                },
                'stored_file_path': f"../blog-core/logs/llm_actions_section_{section_id}_response.json"
            }
            
            processing_results['successful_sections'] += 1
            
        except Exception as e:
            processing_time = (datetime.now() - section_start).total_seconds()
            error_msg = f"Section {section_id} failed: {str(e)}"
            
            section_result = {
                'section_id': section_id,
                'status': 'FAILED',
                'processing_time_seconds': processing_time,
                'message': error_msg,
                'llm_input_data': llm_input_data if 'llm_input_data' in locals() else {},
                'llm_output': {
                    'success': False,
                    'response': None,
                    'error': str(e)
                },
                'stored_file_path': None
            }
            
            processing_results['failed_sections'] += 1
            log_error(error_msg)
        
        processing_results['processed_sections'] += 1
        processing_results['section_details'].append(section_result)
        
        log_info(f"Status: {section_result['status']}")
        log_info(f"Processing Time: {processing_time:.2f} seconds")
        log_info(f"Message: {section_result['message']}")
        log_info(f"End Time: {datetime.now().isoformat()}\n")
    
    # Phase 2 Summary
    phase2_end = datetime.now()
    total_processing_time = (phase2_end - phase2_start).total_seconds()
    
    log_info("=" * 50)
    log_info("=== PHASE 2 SUMMARY ===")
    log_info(f"Phase 2 End Time: {phase2_end.isoformat()}")
    log_info(f"Total Processing Time: {total_processing_time:.2f} seconds")
    log_info(f"Total Sections: {processing_results['total_sections']}")
    log_info(f"Successfully Processed: {processing_results['successful_sections']}")
    log_info(f"Failed: {processing_results['failed_sections']}")
    log_info("=== END PHASE 2 ===\n")
    
    return {
        'success': True,
        'post_id': post_id,
        'checked_sections': checked_sections,
        'section_count': len(checked_sections),
        'execution_time_seconds': total_processing_time,
        'log_file': log_file,
        'processing_results': processing_results,
        'detection_info': {
            'post_id': post_id,
            'checked_sections': checked_sections,
            'section_count': len(checked_sections),
            'function': 'execute_llm_action',
            'timestamp': datetime.now().isoformat()
        }
    } 