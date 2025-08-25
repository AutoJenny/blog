"""
Script Registry System

Centralized script execution system for workflow actions.
"""

from typing import Dict, Any, Callable
from . import llm_actions, custom_scripts, image_generation

# Registry mapping script types to their handlers
SCRIPT_REGISTRY: Dict[str, Callable] = {
    'llm_action': llm_actions.execute_llm_action,
    'custom_script': custom_scripts.execute_custom_script,
    'image_generation': image_generation.execute_image_generation
}

def get_step_config(step_id: int) -> Dict[str, Any]:
    """
    Get step configuration from database.
    
    Args:
        step_id: Workflow step ID
    
    Returns:
        Step configuration dictionary
    """
    from db import get_db_conn
    import psycopg2.extras
    import logging
    
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT config, name
                    FROM workflow_step_entity
                    WHERE id = %s
                """, (step_id,))
                
                result = cur.fetchone()
                if result:
                    config = result['config'] or {}
                    step_name = result['name']
                    logging.info(f"Retrieved config for step {step_id} ({step_name})")
                    return config
                else:
                    logging.error(f"Step {step_id} not found in database")
                    raise ValueError(f"Step {step_id} not found")
                    
    except Exception as e:
        logging.error(f"Database error getting step {step_id} config: {e}")
        raise ValueError(f"Step {step_id} not found")

def execute_step_script(step_id: int, post_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Central script execution based on step configuration.
    
    Args:
        step_id: Workflow step ID
        post_id: Post ID
        context: Execution context (section_ids, inputs, etc.)
    
    Returns:
        Execution results
    """
    import logging
    from datetime import datetime
    
    start_time = datetime.now()
    logging.info(f"Starting script execution for step {step_id}, post {post_id}")
    
    try:
        # Get step configuration
        step_config = get_step_config(step_id)
        script_config = step_config.get('script_config', {})
        script_type = script_config.get('type', 'llm_action')
        
        logging.info(f"Step {step_id} configured for script type: {script_type}")
        
        # Validate script type
        if script_type not in SCRIPT_REGISTRY:
            logging.error(f"Unknown script type '{script_type}' for step {step_id}")
            raise ValueError(f"Unknown script type: {script_type}")
        
        # Execute script
        handler = SCRIPT_REGISTRY[script_type]
        logging.info(f"Executing {script_type} handler for step {step_id}")
        result = handler(step_config, post_id, context)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logging.info(f"Script execution completed for step {step_id} in {execution_time:.2f}s")
        
        return {
            "success": True,
            "step_id": step_id,
            "post_id": post_id,
            "script_type": script_type,
            "result": result,
            "execution_time_seconds": execution_time
        }
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logging.error(f"Script execution failed for step {step_id}, post {post_id} in {execution_time:.2f}s: {str(e)}")
        return {
            "success": False,
            "step_id": step_id,
            "post_id": post_id,
            "error": str(e),
            "message": "Script execution failed",
            "execution_time_seconds": execution_time
        }

def register_script_type(script_type: str, handler: Callable) -> None:
    """
    Register a new script type handler.
    
    Args:
        script_type: Script type identifier
        handler: Handler function
    """
    SCRIPT_REGISTRY[script_type] = handler 