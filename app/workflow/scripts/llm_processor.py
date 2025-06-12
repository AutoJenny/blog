import json
import os
import sys
import requests
from typing import Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from jinja2 import Template

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'prompts')
def get_prompt_file_path(step_name, substage_name, stage_name):
    return os.path.join(PROMPTS_DIR, f"{stage_name}_{substage_name}_{step_name}.json")

def get_db_conn():
    """Get database connection using environment variables."""
    return psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB', 'blog'),
        user=os.getenv('POSTGRES_USER', 'nickfiddes'),
        password=os.getenv('POSTGRES_PASSWORD', ''),
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432')
    )

def get_llm_model(conn, model_id: int = 14) -> str:
    """Get LLM model name from database."""
    query = "SELECT name FROM llm_model WHERE id = %s"
    with conn.cursor() as cur:
        cur.execute(query, (model_id,))
        result = cur.fetchone()
        if not result:
            raise Exception(f"LLM model with id {model_id} not found")
        return result[0]

def load_step_config(post_id: int, stage: str, substage: str, step: str) -> Dict[str, Any]:
    """Load step configuration from planning_steps.json and patch with latest prompt from JSON file if present."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'planning_steps.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    step_config = config[stage][substage][step]
    # Patch with latest prompt from JSON file if present
    prompt_file = get_prompt_file_path(step, substage, stage)
    if os.path.exists(prompt_file):
        with open(prompt_file, 'r') as pf:
            prompt_data = json.load(pf)
            if 'system_prompt' in prompt_data and 'task_prompt' in prompt_data:
                if 'settings' in step_config and 'llm' in step_config['settings']:
                    step_config['settings']['llm']['system_prompt'] = prompt_data['system_prompt']
                    step_config['settings']['llm']['task_prompt'] = prompt_data['task_prompt']
    return step_config

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
    """
    Assemble the LLM prompt in three labeled sections:
    1. Context: (system prompt)
    2. Data to process: (all input fields, labeled)
    3. Instructions: (task/user prompt)
    
    Args:
        system_prompt: The system/context prompt (no placeholders)
        task_prompt: The user/task instructions (no placeholders)
        inputs: Dictionary of input field names and their values
    
    Returns:
        str: The fully constructed prompt
    """
    # 1. Context section
    prompt_parts = ["Context:", system_prompt.strip()]
    
    # 2. Data to process section (all input fields, labeled)
    if inputs:
        data_lines = ["Data to process:"]
        for field_name, value in inputs.items():
            if value:
                data_lines.append(f"{field_name}:")
                data_lines.append(value.strip())
        prompt_parts.append("\n".join(data_lines))
    
    # 3. Instructions section
    prompt_parts.append("Instructions:")
    prompt_parts.append(task_prompt.strip())
    
    # Join all parts with double newlines for clear separation
    final_prompt = "\n\n".join(prompt_parts)
    print(f"DEBUG: Final constructed prompt: {final_prompt}", file=sys.stderr)
    return final_prompt

def call_llm(prompt: str, parameters: Dict[str, Any], conn) -> str:
    """Call Ollama API with the constructed prompt."""
    model_name = get_llm_model(conn)
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        **parameters
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()['response']
    else:
        raise Exception(f"LLM API call failed: {response.text}")

def save_output(conn, post_id: int, output: str, mapping: dict):
    """Save LLM output to the database using the output mapping."""
    query = f"UPDATE {mapping['table']} SET {mapping['field']} = %s WHERE post_id = %s"
    with conn.cursor() as cur:
        cur.execute(query, (output, post_id))
        conn.commit()

def process_step(post_id: int, stage: str, substage: str, step: str):
    """Main function to process a workflow step."""
    try:
        # Load configuration (patched with latest prompt from JSON file)
        config = load_step_config(post_id, stage, substage, step)
        llm_config = config['settings']['llm']
        
        # Get database connection
        conn = get_db_conn()
        
        # Get input values
        inputs = get_input_values(conn, post_id, llm_config['input_mapping'])
        
        # Construct and send prompt
        prompt = construct_prompt(
            llm_config['system_prompt'],
            llm_config['task_prompt'],
            inputs
        )
        print(f"DEBUG: Constructed prompt for step {step}:\n{prompt}", file=sys.stderr)
        
        # Call LLM
        output = call_llm(prompt, llm_config['parameters'], conn)
        
        # Save output
        save_output(conn, post_id, output, llm_config['output_mapping'])
        
        print(f"DEBUG: Successfully processed step for post {post_id}", file=sys.stderr)
        # Print clean JSON output to stdout
        print(json.dumps({"status": "success", "output": output}))
        return output
        
    except Exception as e:
        error_msg = f"Error processing step: {str(e)}"
        print(error_msg, file=sys.stderr)
        print(json.dumps({"status": "error", "message": error_msg}))
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