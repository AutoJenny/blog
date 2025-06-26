import json
import os
import sys
import requests
from typing import Dict, Any, Optional, List
from psycopg2.extras import RealDictCursor
from app.database.routes import get_db_conn
from app.api.workflow.format_validator import FormatValidator

def get_llm_model(conn, model_id: int = 14) -> str:
    """Get LLM model name from database."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT name FROM llm_model WHERE id = %s
        """, (model_id,))
        result = cur.fetchone()
        return result['name'] if result else 'llama3'

def load_step_config(post_id: int, stage: str, substage: str, step: str) -> Dict[str, Any]:
    """Load step configuration from workflow_step_entity table."""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # First get the substage_id
            cur.execute("""
                SELECT id FROM workflow_sub_stage_entity 
                WHERE name = %s
            """, (substage,))
            result = cur.fetchone()
            if not result:
                raise Exception(f"Substage {substage} not found")
            substage_id = result['id']

            # Then get the step configuration
            cur.execute("""
                SELECT config FROM workflow_step_entity 
                WHERE sub_stage_id = %s AND name = %s
            """, (substage_id, step))
            result = cur.fetchone()
            if not result or not result['config']:
                raise Exception(f"Step {step} not found in substage {substage} or has no configuration")
            return result['config']
    finally:
        conn.close()

def get_input_values(conn, post_id: int, input_mapping: Dict[str, Any]) -> Dict[str, str]:
    """Fetch input values from database based on input mapping."""
    inputs = {}
    for input_name, mapping in input_mapping.items():
        query = f"SELECT {mapping['field']} FROM {mapping['table']} WHERE post_id = %s"
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (post_id,))
            result = cur.fetchone()
            if result:
                inputs[input_name] = result[mapping['field']]
    return inputs

def construct_prompt(system_prompt: str, task_prompt: str, inputs: Dict[str, str]) -> str:
    """Construct the full prompt for the LLM."""
    input_text = "\n".join([f"{k}: {v}" for k, v in inputs.items()])
    return f"{system_prompt}\n\n{task_prompt}\n\n{input_text}"

def call_llm(prompt: str, parameters: Dict[str, Any], conn) -> Dict[str, Any]:
    """Call LLM with prompt and parameters."""
    # For testing, return a fixed response
    return {"result": "This is a test response for format validation"}

def save_output(conn, post_id: int, output: str, mapping: dict):
    """Save LLM output to the database using the output mapping."""
    query = f"UPDATE {mapping['table']} SET {mapping['field']} = %s WHERE post_id = %s"
    with conn.cursor() as cur:
        cur.execute(query, (output, post_id))
        conn.commit()

def get_step_id(conn, stage: str, substage: str, step: str) -> int:
    """Get step ID from stage, substage, and step names."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT wse.id
            FROM workflow_step_entity wse
            JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
            JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
            WHERE wst.name ILIKE %s
            AND wsse.name ILIKE %s
            AND wse.name ILIKE %s
        """, (stage, substage, step))
        result = cur.fetchone()
        if not result:
            raise Exception(f"Step not found: {stage}/{substage}/{step}")
        return result['id']

def process_step(post_id: int, stage: str, substage: str, step: str):
    """Main function to process a workflow step."""
    try:
        # Load configuration from database
        config = load_step_config(post_id, stage, substage, step)
        if 'settings' not in config or 'llm' not in config['settings']:
            raise Exception(f"Step {step} does not have LLM configuration")
        llm_config = config['settings']['llm']
        
        # Get database connection
        conn = get_db_conn()
        
        # Get step ID
        step_id = get_step_id(conn, stage, substage, step)
        
        # Get input values
        inputs = get_input_values(conn, post_id, llm_config['input_mapping'])
        
        # Validate input format
        validator = FormatValidator()
        is_valid, error = validator.validate_step_input(step_id, post_id, inputs)
        if not is_valid:
            raise Exception(f"Input validation failed: {error}")
        
        # Construct and send prompt
        prompt = construct_prompt(
            llm_config['system_prompt'],
            llm_config['task_prompt'],
            inputs
        )
        
        # Call LLM
        output = call_llm(prompt, llm_config['parameters'], conn)
        
        # Validate output format
        is_valid, error = validator.validate_step_output(step_id, post_id, output)
        if not is_valid:
            raise Exception(f"Output validation failed: {error}")
        
        # Save output
        save_output(conn, post_id, output, llm_config['output_mapping'])
        
        print(f"Successfully processed step for post {post_id}")
        return output
        
    except Exception as e:
        print(f"Error processing step: {str(e)}", file=sys.stderr)
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python llm_processor.py <post_id> <stage> <substage> <step>")
        sys.exit(1)
    
    post_id = int(sys.argv[1])
    stage = sys.argv[2]
    substage = sys.argv[3]
    step = sys.argv[4]
    
    process_step(post_id, stage, substage, step) 