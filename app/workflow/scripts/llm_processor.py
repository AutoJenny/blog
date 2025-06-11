import json
import os
import sys
import requests
from typing import Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

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
    """Load step configuration from planning_steps.json."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'planning_steps.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config[stage][substage][step]

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
        # Load configuration
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
        
        # Call LLM
        output = call_llm(prompt, llm_config['parameters'], conn)
        
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