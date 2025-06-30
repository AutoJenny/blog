import json
import os
import sys
import requests
import re
from typing import Dict, Any, Optional, List
from psycopg2.extras import RealDictCursor
from app.database.routes import get_db_conn
from app.api.workflow.format_validator import FormatValidator
from app.llm.services import LLMService, parse_tagged_prompt_to_messages, modular_prompt_to_canonical
from datetime import datetime

def create_diagnostic_logs(post_id: int, stage: str, substage: str, step: str, 
                          db_fields: Dict[str, Any], llm_message: str, llm_response: str):
    """Create three diagnostic log files for troubleshooting - overwrites existing files."""
    logs_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # 1. Database fields log - always overwrites
    db_log_path = os.path.join(logs_dir, "workflow_diagnostic_db_fields.json")
    with open(db_log_path, 'w') as f:
        json.dump({
            "metadata": {
                "post_id": post_id,
                "stage": stage,
                "substage": substage,
                "step": step,
                "timestamp": datetime.now().isoformat(),
                "log_type": "database_fields"
            },
            "database_fields": db_fields
        }, f, indent=2, default=str)
    
    # 2. LLM message log - always overwrites
    message_log_path = os.path.join(logs_dir, "workflow_diagnostic_llm_message.txt")
    with open(message_log_path, 'w') as f:
        f.write(f"# LLM Message Diagnostic Log\n")
        f.write(f"# Post ID: {post_id}\n")
        f.write(f"# Stage: {stage}\n")
        f.write(f"# Substage: {substage}\n")
        f.write(f"# Step: {step}\n")
        f.write(f"# Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"# Log Type: llm_message\n\n")
        f.write(llm_message)
    
    # 3. LLM response log - always overwrites
    response_log_path = os.path.join(logs_dir, "workflow_diagnostic_llm_response.txt")
    with open(response_log_path, 'w') as f:
        f.write(f"# LLM Response Diagnostic Log\n")
        f.write(f"# Post ID: {post_id}\n")
        f.write(f"# Stage: {stage}\n")
        f.write(f"# Substage: {substage}\n")
        f.write(f"# Step: {step}\n")
        f.write(f"# Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"# Log Type: llm_response\n\n")
        f.write(llm_response)
    
    print(f"Diagnostic logs created (overwriting previous files):")
    print(f"  - Database fields: {db_log_path}")
    print(f"  - LLM message: {message_log_path}")
    print(f"  - LLM response: {response_log_path}")

def collect_all_database_fields(conn, post_id: int, stage: str, substage: str, step: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Collect all relevant database fields for diagnostic purposes."""
    fields = {
        "post_info": {},
        "post_development": {},
        "workflow_config": {},
        "step_config": config,
        "input_mappings": {},
        "output_mappings": {}
    }
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get post information
            cur.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post WHERE id = %s
            """, (post_id,))
            post_result = cur.fetchone()
            if post_result:
                fields["post_info"] = dict(post_result)
            
            # Get all post_development fields
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'post_development' 
                AND column_name NOT IN ('id', 'post_id')
                ORDER BY ordinal_position
            """)
            dev_columns = [row['column_name'] for row in cur.fetchall()]
            
            if dev_columns:
                column_list = ', '.join(dev_columns)
                cur.execute(f"""
                    SELECT {column_list}
                    FROM post_development
                    WHERE post_id = %s
                """, (post_id,))
                dev_result = cur.fetchone()
                if dev_result:
                    fields["post_development"] = dict(dev_result)
            
            # Get workflow step configuration
            cur.execute("""
                SELECT wse.id, wse.name, wse.config, wse.description,
                       wsse.name as substage_name, wst.name as stage_name
                FROM workflow_step_entity wse
                JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                WHERE wst.name ILIKE %s AND wsse.name ILIKE %s AND wse.name ILIKE %s
            """, (stage, substage, step))
            step_result = cur.fetchone()
            if step_result:
                fields["workflow_config"] = dict(step_result)
            
            # Get input and output mappings if they exist in config
            if 'settings' in config and 'llm' in config['settings']:
                llm_config = config['settings']['llm']
                fields["input_mappings"] = llm_config.get('input_mapping', {})
                fields["output_mappings"] = llm_config.get('output_mapping', {})
                
    except Exception as e:
        fields["error"] = f"Error collecting database fields: {str(e)}"
    
    return fields

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
            # Convert step name from URL format to database format
            # URL format: "initial_concept" -> DB format: "Initial Concept"
            db_step_name = step.replace('_', ' ').title()
            
            # First get the substage_id
            cur.execute("""
                SELECT id FROM workflow_sub_stage_entity 
                WHERE name ILIKE %s
            """, (substage,))
            result = cur.fetchone()
            if not result:
                raise Exception(f"Substage {substage} not found")
            substage_id = result['id']

            # Then get the step configuration
            cur.execute("""
                SELECT config FROM workflow_step_entity 
                WHERE sub_stage_id = %s AND name ILIKE %s
            """, (substage_id, db_step_name))
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

def resolve_format_references(text: str, data: Dict[str, Any]) -> str:
    """Resolve [data:field_name] references in text."""
    def replace_data_ref(match):
        field_name = match.group(1)
        return str(data.get(field_name, f"[{field_name}]"))
    
    return re.sub(r'\[data:([a-zA-Z0-9_]+)\]', replace_data_ref, text)

def construct_prompt(system_prompt: str, task_prompt: str, inputs: Dict[str, str]) -> str:
    """Construct the full prompt for the LLM with format reference resolution."""
    # Resolve any [data:field_name] references in prompts
    system_prompt = resolve_format_references(system_prompt, inputs)
    task_prompt = resolve_format_references(task_prompt, inputs)
    
    input_text = "\n".join([f"{k}: {v}" for k, v in inputs.items()])
    return f"{system_prompt}\n\n{task_prompt}\n\n{input_text}"

def call_llm(prompt: str, parameters: Dict[str, Any], conn) -> Dict[str, Any]:
    """Call LLM with prompt and parameters using the LLM service."""
    # Initialize LLM service
    llm_service = LLMService()
    
    # Extract parameters
    model = parameters.get('model', 'llama3.1:70b')
    temperature = parameters.get('temperature', 0.7)
    max_tokens = parameters.get('max_tokens', 1000)
    
    # Check if prompt is modular (JSON) or plain text
    if prompt.strip().startswith('[') or prompt.strip().startswith('{'):
        try:
            prompt_data = json.loads(prompt)
            result = modular_prompt_to_canonical(prompt_data, {})
            prompt = result['prompt']
        except json.JSONDecodeError:
            # If not valid JSON, treat as plain text
            pass
    
    # Generate response
    response = llm_service.generate(
        prompt=prompt,
        model_name=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    return {"result": response}

def transform_output_to_format(output: str, format_spec: Dict[str, Any]) -> Dict[str, Any]:
    """Transform LLM output to match the required format specification."""
    try:
        # Try to parse as JSON first
        if output.strip().startswith('{') or output.strip().startswith('['):
            parsed_output = json.loads(output)
        else:
            # If not JSON, create a simple text response
            parsed_output = {"content": output.strip()}
        
        # Apply format transformation if specified
        if 'transform' in format_spec:
            transform_rules = format_spec['transform']
            if 'extract_fields' in transform_rules:
                # Extract specific fields from the output
                extracted = {}
                for field_name, field_path in transform_rules['extract_fields'].items():
                    if isinstance(parsed_output, dict):
                        # Simple dot notation for nested fields
                        keys = field_path.split('.')
                        value = parsed_output
                        for key in keys:
                            if isinstance(value, dict) and key in value:
                                value = value[key]
                            else:
                                value = None
                                break
                        extracted[field_name] = value
                return extracted
        
        return parsed_output
        
    except Exception as e:
        print(f"Output transformation failed: {str(e)}", file=sys.stderr)
        return {"content": output.strip()}

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

def get_step_format_config(conn, step_id: int, post_id: int) -> Optional[Dict[str, Any]]:
    """Get format configuration for a workflow step."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT 
                input_fmt.fields as input_spec,
                output_fmt.fields as output_spec,
                input_fmt.id as input_format_id,
                output_fmt.id as output_format_id
            FROM workflow_step_format wsf
            JOIN workflow_format_template input_fmt ON wsf.input_format_id = input_fmt.id
            JOIN workflow_format_template output_fmt ON wsf.output_format_id = output_fmt.id
            WHERE wsf.step_id = %s AND wsf.post_id = %s
        """, (step_id, post_id))
        result = cur.fetchone()
        if not result:
            return None
        def ensure_dict(val):
            if isinstance(val, str):
                return json.loads(val)
            return val
        return {
            'input': ensure_dict(result['input_spec']),
            'output': ensure_dict(result['output_spec']),
            'input_format_id': result['input_format_id'],
            'output_format_id': result['output_format_id']
        }

def get_user_output_mapping(conn, step_id: int, post_id: int) -> Optional[Dict[str, str]]:
    """Get the user's output field mapping for a workflow step, falling back to default if not set."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT config FROM workflow_step_entity WHERE id = %s", (step_id,))
        result = cur.fetchone()
        if not result or not result['config']:
            return None
        
        config = result['config']
        
        # Check for user output mapping first
        user_mapping = config.get('settings', {}).get('llm', {}).get('user_output_mapping')
        if user_mapping:
            return user_mapping
        
        # Fallback to default mapping
        default_mapping = config.get('settings', {}).get('llm', {}).get('output_mapping')
        return default_mapping

def process_step(post_id: int, stage: str, substage: str, step: str):
    """Main function to process a workflow step with format validation."""
    # Initialize diagnostic data collection
    diagnostic_data = {
        "db_fields": {},
        "llm_message": "",
        "llm_response": ""
    }
    
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
        
        # Get format configuration
        format_config = get_step_format_config(conn, step_id, post_id)
        if not format_config:
            print(f"Warning: No format configuration found for step {step_id}, post {post_id}")
        
        # Get input values and collect ALL database fields for diagnostic purposes
        inputs = get_input_values(conn, post_id, llm_config['input_mapping'])
        
        # Collect comprehensive database fields for diagnostics
        diagnostic_data["db_fields"] = collect_all_database_fields(conn, post_id, stage, substage, step, config)
        
        # Validate input format if configuration exists
        if format_config:
            validator = FormatValidator()
            is_valid, error = validator.validate_step_input(step_id, post_id, inputs)
            if not is_valid:
                raise Exception(f"Input validation failed: {error}")
            print(f"Input validation passed for step {step}")
        
        # Validate prompt references if configuration exists
        if format_config:
            validator = FormatValidator()
            is_valid, errors = validator.validate_step_prompts(
                step_id, post_id, 
                llm_config['system_prompt'], 
                llm_config['task_prompt'], 
                inputs
            )
            if not is_valid:
                error_msg = "Reference validation failed:\n" + "\n".join(errors)
                raise Exception(error_msg)
            print(f"Reference validation passed for step {step}")
        
        # Construct and send prompt
        prompt = construct_prompt(
            llm_config['system_prompt'],
            llm_config['task_prompt'],
            inputs
        )
        
        # Store the exact message sent to LLM
        diagnostic_data["llm_message"] = prompt
        
        # Call LLM
        llm_response = call_llm(prompt, llm_config['parameters'], conn)
        output = llm_response['result']
        
        # Store the exact response from LLM
        diagnostic_data["llm_response"] = output
        
        # Transform output to match format if configuration exists
        if format_config:
            transformed_output = transform_output_to_format(output, format_config['output'])
            
            # Validate transformed output
            validator = FormatValidator()
            is_valid, error = validator.validate_step_output(step_id, post_id, transformed_output)
            if not is_valid:
                raise Exception(f"Output validation failed: {error}")
            print(f"Output validation passed for step {step}")
            
            # Convert back to string for storage
            if isinstance(transformed_output, dict):
                output = json.dumps(transformed_output, indent=2)
            else:
                output = str(transformed_output)
        
        # Save output
        output_mapping = get_user_output_mapping(conn, step_id, post_id)
        if not output_mapping:
            output_mapping = llm_config['output_mapping']  # Fallback to default
        save_output(conn, post_id, output, output_mapping)
        
        # Create diagnostic logs
        create_diagnostic_logs(
            post_id, stage, substage, step,
            diagnostic_data["db_fields"],
            diagnostic_data["llm_message"],
            diagnostic_data["llm_response"]
        )
        
        print(f"Successfully processed step {step} for post {post_id}")
        return output
        
    except Exception as e:
        # Create diagnostic logs even on error
        if diagnostic_data["llm_message"] or diagnostic_data["db_fields"]:
            create_diagnostic_logs(
                post_id, stage, substage, step,
                diagnostic_data["db_fields"],
                diagnostic_data["llm_message"],
                f"ERROR: {str(e)}"
            )
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