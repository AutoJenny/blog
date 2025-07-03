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
from app.utils.json_extractor import extract_and_parse_json, extract_json_with_fallback
from datetime import datetime

# Import external prompt constructor
try:
    from .prompt_constructor import (
        build_structured_prompt,
        handle_prompt_construction_errors,
        log_prompt_construction_metadata,
        PromptConstructionError
    )
except ImportError:
    # Fallback for direct script execution
    sys.path.append(os.path.dirname(__file__))
    from prompt_constructor import (
        build_structured_prompt,
        handle_prompt_construction_errors,
        log_prompt_construction_metadata,
        PromptConstructionError
    )

def create_diagnostic_logs(post_id: int, stage: str, substage: str, step: str, 
                          db_fields: Dict[str, Any], llm_message: str, llm_response: str,
                          input_format_template: dict = None, output_format_template: dict = None,
                          frontend_inputs: Dict[str, Any] = None):
    """Create three diagnostic log files for troubleshooting - overwrites existing files."""
    logs_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # 1. Database fields log - always overwrites
    db_log_path = os.path.join(logs_dir, "workflow_diagnostic_db_fields.json")
    log_obj = {
        "metadata": {
            "post_id": post_id,
            "stage": stage,
            "substage": substage,
            "step": step,
            "timestamp": datetime.now().isoformat(),
            "log_type": "database_fields"
        },
        "input_format_template": input_format_template or {},
        "output_format_template": output_format_template or {},
        "frontend_inputs": frontend_inputs or {},
        "database_fields": db_fields
    }
    with open(db_log_path, 'w') as f:
        json.dump(log_obj, f, indent=2, default=str)
    
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
        f.write(f"# Log Type: llm_response\n")
        f.write(f"# Frontend Inputs: {json.dumps(frontend_inputs or {}, indent=2)}\n\n")
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
        "format_config": {}
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
            
            # Get workflow step configuration (only once)
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
            
            # Get format configuration from workflow_step_entity (step-level only)
            step_id = fields["workflow_config"].get('id') if fields["workflow_config"] else None
            if step_id:
                cur.execute("""
                    SELECT 
                        wse.default_input_format_id,
                        wse.default_output_format_id
                    FROM workflow_step_entity wse
                    WHERE wse.id = %s
                """, (step_id,))
                step_format_result = cur.fetchone()
                if step_format_result:
                    fields["format_config"] = {
                        "step_id": step_id,
                        "default_input_format_id": step_format_result['default_input_format_id'],
                        "default_output_format_id": step_format_result['default_output_format_id']
                    }
                
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

def get_input_values(conn, post_id: int, input_mapping: Dict[str, Any], frontend_inputs: Dict[str, Any] = None) -> Dict[str, str]:
    """Fetch input values from database based on input mapping, with support for frontend-provided inputs."""
    inputs = {}
    
    # If frontend inputs are provided, use them as the primary source
    if frontend_inputs:
        for input_name, input_data in frontend_inputs.items():
            if isinstance(input_data, dict):
                # Frontend provided structured input data - preserve the full structure
                inputs[input_name] = input_data
            elif isinstance(input_data, str):
                # Frontend provided direct string value
                inputs[input_name] = input_data
            else:
                # Fallback to empty string
                inputs[input_name] = ''
    
    # Fallback to database lookup for any missing inputs
    for input_name, mapping in input_mapping.items():
        if input_name not in inputs or not inputs[input_name]:
            # Handle both old format (field/table) and new format (db_field/db_table)
            field_name = mapping.get('db_field') or mapping.get('field')
            table_name = mapping.get('db_table') or mapping.get('table')
            
            if field_name and table_name:
                query = f"SELECT {field_name} FROM {table_name} WHERE post_id = %s"
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, (post_id,))
                    result = cur.fetchone()
                    if result:
                        inputs[input_name] = result[field_name] or ''
                    else:
                        inputs[input_name] = ''
            else:
                inputs[input_name] = ''
    
    # Convert generic input names to database field names for consistency
    db_field_inputs = {}
    for input_name, value in inputs.items():
        # Check if this input has its own db_field information (from frontend)
        if isinstance(value, dict) and 'db_field' in value:
            # Frontend provided db_field information
            db_field_inputs[value['db_field']] = value.get('value', '')
        elif input_name in input_mapping:
            # Use mapping from step configuration
            field_name = input_mapping[input_name].get('db_field') or input_mapping[input_name].get('field')
            if field_name:
                db_field_inputs[field_name] = value
            else:
                db_field_inputs[input_name] = value
        else:
            # If not in mapping, assume it's already a database field name
            db_field_inputs[input_name] = value
    
    return db_field_inputs

def resolve_format_references(text: str, data: Dict[str, Any]) -> str:
    """Resolve [data:field_name] references in text."""
    def replace_data_ref(match):
        field_name = match.group(1)
        return str(data.get(field_name, f"[{field_name}]"))
    
    return re.sub(r'\[data:([a-zA-Z0-9_]+)\]', replace_data_ref, text)

def construct_prompt(system_prompt: str, task_prompt: str, inputs: Dict[str, str], all_db_fields: Dict[str, Any], 
                    input_format_template: Dict[str, Any] = None, output_format_template: Dict[str, Any] = None,
                    step_config: Dict[str, Any] = None) -> str:
    """
    Construct the full prompt for the LLM with proper CONTEXT, INPUTS, TASK, and RESPONSE sections.
    
    Args:
        system_prompt: System prompt for the LLM
        task_prompt: Task-specific prompt
        inputs: Input data dictionary
        all_db_fields: All database fields for reference resolution
        input_format_template: Input format template data
        output_format_template: Output format template data
        step_config: Step configuration data
    
    Returns:
        Structured prompt string with CONTEXT, INPUTS, TASK, and RESPONSE sections
    """
    try:
        # Validate required components
        if not system_prompt or not system_prompt.strip():
            raise ValueError("System prompt is required and cannot be empty")
        
        if not task_prompt or not task_prompt.strip():
            raise ValueError("Task prompt is required and cannot be empty")
        
        if not input_format_template:
            raise ValueError("Input format template is required")
        
        if not output_format_template:
            raise ValueError("Output format template is required")
        
        # Resolve any [data:field_name] references in prompts
        system_prompt = resolve_format_references(system_prompt, all_db_fields)
        task_prompt = resolve_format_references(task_prompt, all_db_fields)
        
        # Extract format instructions
        input_instructions = input_format_template.get('llm_instructions', '')
        input_description = input_format_template.get('description', '')
        output_instructions = output_format_template.get('llm_instructions', '')
        output_description = output_format_template.get('description', '')
        
        # Build CONTEXT section
        context_parts = ["CONTEXT to orientate you", ""]
        if system_prompt.strip():
            context_parts.append(system_prompt.strip())
        context_section = "\n".join(context_parts)
        
        # Build INPUTS section
        inputs_parts = ["INPUTS for your TASK below"]
        if input_description:
            inputs_parts.append(f"({input_description})")
        if input_instructions:
            inputs_parts.append(input_instructions)
        inputs_parts.append("")
        
        # Add input data with proper titles
        for k, v in inputs.items():
            if v is not None and v.strip():
                # Convert key to display name (e.g., "basic_idea" -> "Basic Idea")
                display_name = k.replace('_', ' ').title()
                inputs_parts.append(f"{display_name}:")
                inputs_parts.append(v.strip())
                inputs_parts.append("")
        
        inputs_section = "\n".join(inputs_parts)
        
        # Build TASK section
        task_parts = ["TASK to process the INPUTS above", ""]
        if task_prompt.strip():
            task_parts.append(task_prompt.strip())
        task_section = "\n".join(task_parts)
        
        # Build RESPONSE section
        response_parts = ["RESPONSE to return", ""]
        if output_description:
            response_parts.append(output_description)
        if output_instructions:
            response_parts.append(output_instructions)
        response_section = "\n".join(response_parts)
        
        # Combine all sections
        full_prompt = f"{context_section}\n\n{inputs_section}\n\n{task_section}\n\n{response_section}"
        
        return full_prompt
        
    except Exception as e:
        print(f"Error in prompt construction: {e}", file=sys.stderr)
        # Return a clear error message instead of malformed prompt
        error_prompt = f"""SYSTEM ERROR: Prompt construction failed

The LLM prompt could not be properly constructed due to the following error:
{str(e)}

Please report this error to the system administrator. The required prompt components are:
- System prompt (for CONTEXT section)
- Task prompt (for TASK section) 
- Input format template (for INPUTS section)
- Output format template (for RESPONSE section)

This is a system configuration issue that needs to be resolved before LLM processing can continue."""
        
        return error_prompt

def call_llm(prompt: str, parameters: Dict[str, Any], conn, timeout: int = 60) -> Dict[str, Any]:
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
    
    # Generate response with timeout
    response = llm_service.generate(
        prompt=prompt,
        model_name=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout
    )
    
    return {"result": response}

def transform_output_to_format(output: str, format_spec: Dict[str, Any]) -> Dict[str, Any]:
    """Transform LLM output to match the required format specification."""
    try:
        # Use robust JSON extraction from markdown
        parsed_json = extract_and_parse_json(output)
        
        if parsed_json is not None:
            # Successfully extracted and parsed JSON
            parsed_output = parsed_json
        else:
            # If no JSON found, create a simple text response
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

def get_step_prompt_templates(conn, step_id: int) -> Dict[str, str]:
    """Get prompt templates from workflow_step_prompt table."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT 
                sys_prompt.system_prompt as system_prompt,
                task_prompt.prompt_text as task_prompt
            FROM workflow_step_prompt wsp
            LEFT JOIN llm_prompt sys_prompt ON wsp.system_prompt_id = sys_prompt.id
            LEFT JOIN llm_prompt task_prompt ON wsp.task_prompt_id = task_prompt.id
            WHERE wsp.step_id = %s
        """, (step_id,))
        result = cur.fetchone()
        if result:
            return {
                'system_prompt': result['system_prompt'] or '',
                'task_prompt': result['task_prompt'] or ''
            }
        return {'system_prompt': '', 'task_prompt': ''}

def process_step(post_id: int, stage: str, substage: str, step: str, frontend_inputs: Dict[str, Any] = None):
    """Main function to process a workflow step with format validation and multiple inputs."""
    diagnostic_data = {
        "db_fields": {},
        "llm_message": "",
        "llm_response": "",
        "frontend_inputs": frontend_inputs or {}
    }
    try:
        config = load_step_config(post_id, stage, substage, step)
        if 'settings' not in config or 'llm' not in config['settings']:
            raise Exception(f"Step {step} does not have LLM configuration")
        llm_config = config['settings']['llm']
        conn = get_db_conn()
        step_id = get_step_id(conn, stage, substage, step)
        prompt_templates = get_step_prompt_templates(conn, step_id)
        system_prompt = prompt_templates['system_prompt'] or llm_config.get('system_prompt', '')
        task_prompt = prompt_templates['task_prompt'] or llm_config.get('task_prompt', '')

        # Get input values and collect ALL database fields for diagnostic purposes
        # Use inputs from config, fallback to llm_config.input_mapping if available
        input_mapping = config.get('inputs', {})
        if not input_mapping and 'input_mapping' in llm_config:
            input_mapping = llm_config['input_mapping']
        
        inputs = get_input_values(conn, post_id, input_mapping, frontend_inputs)
        diagnostic_data["db_fields"] = collect_all_database_fields(conn, post_id, stage, substage, step, config)

        # Collect format templates separately to avoid duplication
        input_format_template = None
        output_format_template = None
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get step-level format configuration from workflow_step_entity
            cur.execute("""
                SELECT 
                    wse.default_input_format_id,
                    wse.default_output_format_id
                FROM workflow_step_entity wse
                WHERE wse.id = %s
            """, (step_id,))
            step_format_result = cur.fetchone()
            
            if step_format_result:
                # Input format template
                if step_format_result['default_input_format_id']:
                    cur.execute("""
                        SELECT 
                            id,
                            name,
                            description,
                            fields,
                            llm_instructions,
                            created_at,
                            updated_at
                        FROM workflow_format_template 
                        WHERE id = %s
                    """, (step_format_result['default_input_format_id'],))
                    input_template = cur.fetchone()
                    if input_template:
                        input_format_template = dict(input_template)
                
                # Output format template
                if step_format_result['default_output_format_id']:
                    cur.execute("""
                        SELECT 
                            id,
                            name,
                            description,
                            fields,
                            llm_instructions,
                            created_at,
                            updated_at
                        FROM workflow_format_template 
                        WHERE id = %s
                    """, (step_format_result['default_output_format_id'],))
                    output_template = cur.fetchone()
                    if output_template:
                        output_format_template = dict(output_template)

        # Construct and send prompt
        all_db_fields = diagnostic_data["db_fields"].get("post_development", {})
        prompt = construct_prompt(system_prompt, task_prompt, inputs, all_db_fields, input_format_template, output_format_template, config)
        diagnostic_data["llm_message"] = prompt

        # Call LLM
        llm_response = call_llm(prompt, llm_config['parameters'], conn, llm_config.get('timeout', 60))
        output = llm_response['result']
        diagnostic_data["llm_response"] = output

        # Save output
        output_mapping = get_user_output_mapping(conn, step_id, post_id)
        if not output_mapping:
            output_mapping = llm_config['output_mapping']
        save_output(conn, post_id, output, output_mapping)

        # Create diagnostic logs with unified, non-duplicated structure
        create_diagnostic_logs(
            post_id, stage, substage, step,
            diagnostic_data["db_fields"],
            diagnostic_data["llm_message"],
            diagnostic_data["llm_response"],
            input_format_template,
            output_format_template,
            diagnostic_data["frontend_inputs"]
        )
        print(f"Successfully processed step {step} for post {post_id}")
        return output
    except Exception as e:
        if diagnostic_data["llm_message"] or diagnostic_data["db_fields"]:
            create_diagnostic_logs(
                post_id, stage, substage, step,
                diagnostic_data["db_fields"],
                diagnostic_data["llm_message"],
                f"ERROR: {str(e)}",
                input_format_template,
                output_format_template,
                diagnostic_data["frontend_inputs"]
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