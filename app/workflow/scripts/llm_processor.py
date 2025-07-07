import json
import os
import sys
import requests
import re
import threading
import time
from typing import Dict, Any, Optional, List
from psycopg2.extras import RealDictCursor
from app.database.routes import get_db_conn
from app.api.workflow.format_validator import FormatValidator
from app.llm.services import LLMService, parse_tagged_prompt_to_messages, modular_prompt_to_canonical
from app.utils.json_extractor import extract_and_parse_json, extract_json_with_fallback
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

class TimeoutError(Exception):
    """Custom timeout exception for section processing."""
    pass

class timeout_context:
    """Context manager for implementing per-section timeouts using threading."""
    
    def __init__(self, seconds):
        self.seconds = seconds
        self.result = None
        self.exception = None
        self.thread = None
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.thread and self.thread.is_alive():
            # Thread is still running, timeout occurred
            raise TimeoutError(f"Operation timed out after {self.seconds} seconds")
        elif self.exception:
            # Thread completed but raised an exception
            raise self.exception
        return False
    
    def run_with_timeout(self, func, *args, **kwargs):
        """Run a function with timeout using threading."""
        def target():
            try:
                self.result = func(*args, **kwargs)
            except Exception as e:
                self.exception = e
        
        self.thread = threading.Thread(target=target)
        self.thread.daemon = True
        self.thread.start()
        self.thread.join(timeout=self.seconds)
        
        if self.thread.is_alive():
            # Thread is still running, timeout occurred
            raise TimeoutError(f"Operation timed out after {self.seconds} seconds")
        elif self.exception:
            # Thread completed but raised an exception
            raise self.exception
        
        return self.result

def create_diagnostic_logs(post_id: int, stage: str, substage: str, step: str, 
                          db_fields: Dict[str, Any], llm_message: str, llm_response: str,
                          input_format_template: dict = None, output_format_template: dict = None,
                          frontend_inputs: Dict[str, Any] = None,
                          input_field_values: Dict[str, Any] = None):
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
        "database_fields": db_fields,
        "input_field_values": input_field_values or {}
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
                    step_config: Dict[str, Any] = None, stage: str = None) -> str:
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
        stage: Workflow stage (e.g., 'writing', 'planning', etc.)
    
    Returns:
        Structured prompt string with CONTEXT, INPUTS, TASK, and RESPONSE sections
    """
    try:
        # Check if this is Writing stage - use hard-coded structure
        if stage == 'writing':
            return construct_writing_stage_prompt(system_prompt, inputs, output_format_template)
        
        # Use existing logic for other stages
        return construct_standard_prompt(system_prompt, task_prompt, inputs, all_db_fields, 
                                       input_format_template, output_format_template, step_config)
        
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

def construct_writing_stage_prompt(system_prompt: str, inputs: Dict[str, str], 
                                 output_format_template: Dict[str, Any]) -> str:
    """
    Hard-coded prompt structure for Writing stage only.
    This function creates a consistent, reliable prompt structure for all Writing stage steps.
    """
    try:
        # CONTEXT section (expert knowledge + broad article context)
        context_section = f"""CONTEXT to orientate you

{system_prompt.strip() if system_prompt else 'You are an expert in Scottish history, culture, and traditions. You have deep knowledge of clan history, tartans, kilts, quaichs, and other aspects of Scottish heritage. You write in a clear, engaging style that balances historical accuracy with accessibility for a general audience.'}

BROAD SUBJECT OF WIDER ARTICLE:
Basic Idea: {inputs.get('basic_idea', '')}"""

        # INPUTS section (section-specific details only)
        avoid_topics_text = ""
        if inputs.get('avoid_topics'):
            avoid_topics_text = "\n".join([f"- {topic}" for topic in inputs.get('avoid_topics', [])])
        
        inputs_section = f"""INPUTS for your TASK below
(Mixed plain text & JSON)
The inputs are a combination of plain text and structured JSON. Interpret each type appropriately.

WRITE ABOUT THIS SPECIFIC SECTION:
Section Heading: {inputs.get('write_about_section_heading', '')}
Section Description: {inputs.get('write_about_section_description', '')}

AVOID THESE TOPICS (DO NOT WRITE ABOUT):
{avoid_topics_text}"""

        # TASK section (hard-coded for Writing stage)
        task_section = """TASK to process the INPUTS above

We are authoring a blog article about the IDEA SCOPE and BASIC IDEA in the context above. These have been organised into Sections with titles and descriptions provided in the SECTION_HEADINGS above (note the plural in the field name).

Your task is to write 2-3 HTML paragraphs (100-150 words) on the topic of the SECTION_HEADING (note singular) and SECTION_DESCRIPTION in the inputs above. Stick to this narrow topic, avoiding overlapping with related topics outlined in the full SECTION_HEADINGS input (note plural). 

You must not use headings, numbering, and NO introduction, conclusions or commentary. Write only the topic content in a way that will flow naturally from and into other topic sections. Use only UK British idioms and spellings. Avoid long words or florid expressions."""

        # RESPONSE section
        output_instructions = output_format_template.get('llm_instructions', '') if output_format_template else 'Return your response as plain text using British English spellings and conventions (e.g., colour, centre, organisation). Do not include any JSON, metadata, or commentary—just the text.'
        response_section = f"""RESPONSE to return

{output_instructions}"""

        return f"{context_section}\n\n{inputs_section}\n\n{task_section}\n\n{response_section}"
        
    except Exception as e:
        print(f"Error in Writing stage prompt construction: {e}", file=sys.stderr)
        return f"""SYSTEM ERROR: Writing stage prompt construction failed

Error: {str(e)}

This is a system configuration issue that needs to be resolved before LLM processing can continue."""

def construct_standard_prompt(system_prompt: str, task_prompt: str, inputs: Dict[str, str], all_db_fields: Dict[str, Any], 
                            input_format_template: Dict[str, Any] = None, output_format_template: Dict[str, Any] = None,
                            step_config: Dict[str, Any] = None) -> str:
    """
    Standard prompt construction for non-Writing stages (Planning, etc.).
    This maintains the existing flexible prompt system for other stages.
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
        print(f"Error in standard prompt construction: {e}", file=sys.stderr)
        return f"""SYSTEM ERROR: Standard prompt construction failed

Error: {str(e)}

This is a system configuration issue that needs to be resolved before LLM processing can continue."""

def call_llm(prompt: str, parameters: Dict[str, Any], conn, timeout: int = 60) -> Dict[str, Any]:
    """Call LLM with prompt and parameters using the LLM service."""
    # Get LLM configuration from database instead of Flask config
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT provider_type, model_name, api_base
            FROM llm_config
            WHERE is_active = true
            ORDER BY id DESC
            LIMIT 1
        """)
        config = cur.fetchone()
        if not config:
            # Fallback to default configuration
            config = {
                'provider_type': 'ollama',
                'model_name': 'llama3.1:70b',
                'api_base': 'http://localhost:11434'
            }
    
    # Initialize LLM service with configuration
    llm_service = LLMService()
    llm_service.ollama_url = config['api_base'] if config['provider_type'] == 'ollama' else None
    llm_service.openai_api_key = None  # No API key in current schema
    llm_service.default_model = config['model_name']
    
    # Extract parameters (use database config as defaults)
    model = parameters.get('model', config['model_name'])
    temperature = parameters.get('temperature', 0.7)  # Default temperature
    max_tokens = parameters.get('max_tokens', 1000)   # Default max_tokens
    
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

def save_section_output(conn, section_ids: List[int], output: str, field: str):
    """
    WRITING STAGE ONLY: Save LLM output to specific sections.
    
    This function is specifically for Writing stage section processing.
    DO NOT USE for Planning stage - use save_output() instead.
    
    Args:
        conn: Database connection
        section_ids: List of section IDs to update
        output: LLM output content to save
        field: Field name in post_section table to update
    """
    if not section_ids:
        raise ValueError("section_ids cannot be empty for Writing stage processing")
    
    placeholders = ','.join(['%s'] * len(section_ids))
    query = f"UPDATE post_section SET {field} = %s WHERE id IN ({placeholders})"
    params = [output] + section_ids
    
    logger.info(f"Saving section output: field={field}, section_ids={section_ids}, output_length={len(output)}")
    logger.debug(f"SQL Query: {query}")
    logger.debug(f"SQL Params: {params}")
    
    with conn.cursor() as cur:
        cur.execute(query, params)
        conn.commit()
        logger.info(f"Successfully saved output to {field} for sections {section_ids}")

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
    logger.info(f"Getting output mapping for step_id: {step_id}, post_id: {post_id}")
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT config FROM workflow_step_entity WHERE id = %s", (step_id,))
        result = cur.fetchone()
        if not result or not result['config']:
            logger.warning(f"No config found for step_id: {step_id}")
            return None
        
        config = result['config']
        logger.debug(f"Retrieved config for step_id {step_id}: {config}")
        
        # Check for user output mapping first
        user_mapping = config.get('settings', {}).get('llm', {}).get('user_output_mapping')
        if user_mapping:
            logger.info(f"Found user output mapping: {user_mapping}")
            return user_mapping
        
        # Fallback to default mapping
        default_mapping = config.get('settings', {}).get('llm', {}).get('output_mapping')
        logger.info(f"Using default output mapping: {default_mapping}")
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

def get_selected_sections_data(conn, post_id: int, selected_section_ids: List[int], current_section_id: int) -> Dict[str, Any]:
    """
    Get data for selected sections and current section context.
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get current section context (fetch all columns)
            cur.execute("""
                SELECT *
                FROM post_section 
                WHERE id = %s AND post_id = %s
            """, (current_section_id, post_id))
            current_section = cur.fetchone()
            
            if not current_section:
                raise ValueError(f"Current section {current_section_id} not found for post {post_id}")
            
            # Get selected sections data (filtered)
            if selected_section_ids:
                placeholders = ','.join(['%s'] * len(selected_section_ids))
                cur.execute(f"""
                    SELECT id, section_heading, section_description, section_order
                    FROM post_section 
                    WHERE id IN ({placeholders}) AND post_id = %s
                    ORDER BY section_order
                """, selected_section_ids + [post_id])
                selected_sections = cur.fetchall()
            else:
                selected_sections = []
            
            # Get post-level context
            cur.execute("""
                SELECT idea_scope, basic_idea, section_headings
                FROM post_development 
                WHERE post_id = %s
            """, (post_id,))
            post_context = cur.fetchone() or {}
            
            # Build context_data with all fields from current_section
            context_data = dict(current_section)
            # Add post-level context fields
            context_data["idea_scope"] = post_context.get("idea_scope")
            context_data["basic_idea"] = post_context.get("basic_idea")
            context_data["section_headings"] = post_context.get("section_headings")
            # Add legacy/compatibility fields
            context_data["write_about_section_heading"] = current_section.get("section_heading", "")
            context_data["write_about_section_description"] = current_section.get("section_description", "")
            # All section headings for avoid_topics
            all_section_headings = []
            if post_context.get("section_headings"):
                try:
                    all_section_headings = json.loads(post_context["section_headings"])
                    if not isinstance(all_section_headings, list):
                        all_section_headings = []
                except (json.JSONDecodeError, TypeError):
                    all_section_headings = [
                        {
                            "title": section["section_heading"],
                            "description": section["section_description"]
                        } for section in selected_sections
                    ]
            current_section_heading = current_section.get("section_heading", "")
            avoid_topics = []
            for heading in all_section_headings:
                if isinstance(heading, dict):
                    title = heading.get('title', heading.get('heading', ''))
                    if title != current_section_heading:
                        avoid_topics.append(title)
            context_data["avoid_topics"] = avoid_topics
            return {
                "current_section": {
                    "id": current_section_id,
                    "heading": current_section.get('section_heading', ''),
                    "description": current_section.get('section_description', ''),
                    "first_draft": current_section.get('first_draft', '')
                },
                "selected_sections": [
                    {
                        "id": section['id'],
                        "heading": section['section_heading'],
                        "description": section['section_description'],
                        "order": section['section_order']
                    } for section in selected_sections
                ],
                "post_context": post_context,
                "context_data": context_data
            }
    except Exception as e:
        print(f"Error getting selected sections data: {str(e)}", file=sys.stderr)
        raise

def build_section_specific_prompt(conn, post_id: int, step_id: int, selected_section_ids: List[int], current_section_id: int) -> Dict[str, Any]:
    """
    Build section-specific prompt for Writing stage with clear "WRITE ABOUT" and "AVOID THESE TOPICS" structure.
    
    Args:
        conn: Database connection
        post_id: Post ID
        step_id: Workflow step ID
        selected_section_ids: List of selected section IDs
        current_section_id: ID of section being processed
    
    Returns:
        Dict with system_prompt, task_prompt, and context_data
    """
    try:
        # Get base prompts from workflow_step_prompt table
        prompt_templates = get_step_prompt_templates(conn, step_id)
        system_prompt = prompt_templates.get('system_prompt', '')
        task_prompt = prompt_templates.get('task_prompt', '')
        
        # Get section-specific data
        section_data = get_selected_sections_data(conn, post_id, selected_section_ids, current_section_id)
        
        # Get all section headings from post_development
        all_section_headings = []
        if section_data["post_context"].get("section_headings"):
            try:
                all_section_headings = json.loads(section_data["post_context"]["section_headings"])
                if not isinstance(all_section_headings, list):
                    all_section_headings = []
            except (json.JSONDecodeError, TypeError):
                # If parsing fails, create headings from section data
                all_section_headings = [
                    {
                        "title": section["heading"],
                        "description": section["description"]
                    } for section in section_data["selected_sections"]
                ]
        
        # Extract current section and create "avoid topics" list
        current_section_heading = section_data["current_section"]["heading"]
        current_section_description = section_data["current_section"]["description"]
        
        # Create list of topics to avoid (all sections except current)
        avoid_topics = []
        for heading in all_section_headings:
            if isinstance(heading, dict):
                title = heading.get('title', heading.get('heading', ''))
                if title != current_section_heading:
                    avoid_topics.append(title)
        
        # Create context data for prompt construction with restructured format
        context_data = {
            "idea_scope": section_data["post_context"].get("idea_scope"),
            "basic_idea": section_data["post_context"].get("basic_idea"),
            "write_about_section_heading": current_section_heading,
            "write_about_section_description": current_section_description,
            "avoid_topics": avoid_topics,
            # Keep legacy fields for backward compatibility
            "section_heading": current_section_heading,
            "section_description": current_section_description,
            "section_headings": json.dumps(all_section_headings) if all_section_headings else "[]"
        }
        
        return {
            "system_prompt": system_prompt,
            "task_prompt": task_prompt,
            "context_data": context_data,
            "section_data": section_data
        }
        
    except Exception as e:
        print(f"Error building section-specific prompt: {str(e)}", file=sys.stderr)
        raise

def get_section_specific_prompts(conn, step_id: int, post_id: int, selected_section_ids: List[int], current_section_id: int) -> Dict[str, Any]:
    """
    Get section-specific prompts while maintaining existing prompt system.
    
    Args:
        conn: Database connection
        step_id: Workflow step ID
        post_id: Post ID
        selected_section_ids: List of selected section IDs
        current_section_id: ID of section being processed
    
    Returns:
        Dict with system_prompt, task_prompt, and section_context
    """
    try:
        # Get existing prompts from workflow_step_prompt table
        prompt_templates = get_step_prompt_templates(conn, step_id)
        system_prompt = prompt_templates.get('system_prompt', '')
        task_prompt = prompt_templates.get('task_prompt', '')
        
        # Get section data for context
        section_data = get_selected_sections_data(conn, post_id, selected_section_ids, current_section_id)
        
        # Add section-specific context to task_prompt
        section_context = f"""
Section Heading: {section_data["current_section"]["heading"]}
Section Description: {section_data["current_section"]["description"]}
"""
        
        # Only add section context if not already present
        if "Section Heading:" not in task_prompt:
            task_prompt = section_context + "\n" + task_prompt
        
        return {
            "system_prompt": system_prompt,
            "task_prompt": task_prompt,
            "section_context": section_context,
            "section_data": section_data
        }
        
    except Exception as e:
        print(f"Error getting section-specific prompts: {str(e)}", file=sys.stderr)
        raise

def get_step_name_by_id(conn, step_id: int) -> str:
    """Get the step name from workflow_step_entity by step_id."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT name FROM workflow_step_entity WHERE id = %s", (step_id,))
        result = cur.fetchone()
        if not result:
            raise Exception(f"Step name not found for step_id {step_id}")
        return result['name']

def process_single_section(conn, post_id: int, step_id: int, section_id: int, selected_section_ids: List[int], 
                          timeout_per_section: int = 300) -> Dict[str, Any]:
    """
    Process a single section with section-specific prompt and timeout.
    """
    prompt_data = None
    section_heading = "Unknown"
    prompt = None
    output = None
    all_db_fields = {}
    input_format_template = None
    output_format_template = None
    input_field_values = {}
    try:
        # Build section-specific prompt
        prompt_data = build_section_specific_prompt(conn, post_id, step_id, selected_section_ids, section_id)
        section_heading = prompt_data["section_data"]["current_section"]["heading"]
        
        # Get step name for this step_id
        step_name = get_step_name_by_id(conn, step_id)
        # Get step configuration for LLM parameters
        step_config = load_step_config(post_id, "writing", "content", step_name)
        llm_config = step_config.get('settings', {}).get('llm', {})
        
        # Collect ALL input field values for logging
        input_field_values = collect_all_input_field_values(conn, post_id, step_config)
        
        # Get format templates from database
        format_config = get_step_format_config(conn, step_id, post_id)
        input_format_template = format_config.get('input') if format_config else None
        output_format_template = format_config.get('output') if format_config else None
        
        # If no format templates found, create simple defaults
        if not input_format_template:
            input_format_template = {
                'description': 'Mixed plain text & JSON',
                'llm_instructions': 'The inputs are a combination of plain text and structured JSON. Interpret each type appropriately.'
            }
        if not output_format_template:
            output_format_template = {
                'description': 'Format for plain text responses using British English spellings and conventions',
                'llm_instructions': 'Return your response as plain text using British English spellings and conventions (e.g., colour, centre, organisation). Do not include any JSON, metadata, or commentary—just the text.'
            }
        
        # DEBUG: Log step_config['inputs'] and prompt_data['context_data']
        debug_log_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'logs', 'llm_section_inputs_debug.json')
        with open(debug_log_path, 'w') as dbg:
            import json
            dbg.write(json.dumps({
                'step_config_inputs': step_config.get('inputs', {}) if step_config else {},
                'context_data': prompt_data.get('context_data', {})
            }, indent=2, default=str))

        # Dynamically extract all input fields from step_config['inputs']
        section_inputs = {}
        if step_config and 'inputs' in step_config:
            for input_id, input_cfg in step_config['inputs'].items():
                db_field = input_cfg.get('db_field', input_id)
                # Use the db_field as the key for the prompt input, fallback to input_id
                section_inputs[db_field] = prompt_data["context_data"].get(db_field, "")
        # Fallback: if no config, use previous hardcoded fields
        if not section_inputs:
            section_inputs = {
                "write_about_section_heading": prompt_data["context_data"].get("write_about_section_heading", ""),
                "write_about_section_description": prompt_data["context_data"].get("write_about_section_description", ""),
                "avoid_topics": prompt_data["context_data"].get("avoid_topics", []),
                "idea_scope": prompt_data["context_data"].get("idea_scope", ""),
                "basic_idea": prompt_data["context_data"].get("basic_idea", "")
            }

        prompt = construct_prompt(
            prompt_data["system_prompt"],
            prompt_data["task_prompt"],
            section_inputs,  # Pass section-specific inputs
            all_db_fields,
            input_format_template,
            output_format_template,
            step_config,
            "writing"  # Specify the stage for the prompt construction
        )
        
        # Call LLM with timeout
        llm_response = call_llm(prompt, llm_config.get('parameters', {}), conn, timeout_per_section)
        output = llm_response['result']
        
        # Save to specific section
        output_mapping = get_user_output_mapping(conn, step_id, post_id)
        logger.info(f"Step ID: {step_id}, Step Name: {step_name}")
        logger.info(f"Output mapping: {output_mapping}")
        logger.info(f"Output content length: {len(output) if output else 0}")
        
        if output_mapping and output_mapping.get('table') == 'post_section':
            field = output_mapping.get('field', 'first_draft')
            logger.info(f"Saving to field: {field} for section {section_id}")
            save_section_output(conn, [section_id], output, field)
            logger.info(f"Save completed")
        else:
            logger.warning(f"No valid output mapping found or wrong table")
            logger.warning(f"output_mapping: {output_mapping}")
        
        return {
            "success": True,
            "result": output,
            "section_id": section_id,
            "section_heading": section_heading,
            "processing_time": 0  # TODO: Add actual timing
        }
        
    except Exception as e:
        output = f"ERROR: {str(e)}"
        return {
            "success": False,
            "error": str(e),
            "section_id": section_id,
            "section_heading": section_heading,
            "processing_time": 0
        }
    finally:
        # Always log the prompt and response/error for diagnostics
        try:
            create_diagnostic_logs(
                post_id=post_id,
                stage="writing",
                substage="content", 
                step=step_name if 'step_name' in locals() else "unknown",
                db_fields=all_db_fields,
                llm_message=prompt if prompt else "[Prompt not constructed]",
                llm_response=output if output else "[No response or error]",
                input_format_template=input_format_template,
                output_format_template=output_format_template,
                frontend_inputs={},  # No frontend inputs for section processing
                input_field_values=input_field_values  # Pass all input field values
            )
        except Exception as log_exc:
            print(f"[LOGGING ERROR] Failed to write diagnostic logs: {log_exc}", file=sys.stderr)

def process_sections_sequentially(conn, post_id: int, step_id: int, selected_section_ids: List[int], 
                                 timeout_per_section: int = 300) -> Dict[str, Any]:
    """
    Process sections sequentially with per-section timeout.
    
    Args:
        conn: Database connection
        post_id: Post ID
        step_id: Workflow step ID
        selected_section_ids: List of selected section IDs
        timeout_per_section: Timeout in seconds per section (default: 300)
    
    Returns:
        Dict with results for each section
    """
    results = {}
    total_time = 0
    
    for section_id in selected_section_ids:
        start_time = datetime.now()
        
        try:
            # Create timeout context
            timeout_ctx = timeout_context(timeout_per_section)
            
            # Process section with section-specific prompt using timeout
            result = timeout_ctx.run_with_timeout(
                process_single_section, 
                conn, post_id, step_id, section_id, selected_section_ids, timeout_per_section
            )
            results[section_id] = result
                
        except TimeoutError:
            processing_time = (datetime.now() - start_time).total_seconds()
            results[section_id] = {
                "success": False,
                "error": f"Timeout after {timeout_per_section}s",
                "section_id": section_id,
                "section_heading": "Unknown",
                "processing_time": processing_time
            }
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            results[section_id] = {
                "success": False,
                "error": str(e),
                "section_id": section_id,
                "section_heading": "Unknown",
                "processing_time": processing_time
            }
            # Continue with next section
        
        total_time += (datetime.now() - start_time).total_seconds()
    
    # Add summary information
    successful = sum(1 for r in results.values() if r.get("success", False))
    failed = len(results) - successful
    
    return {
        "results": results,
        "summary": {
            "total_sections": len(selected_section_ids),
            "successful": successful,
            "failed": failed,
            "total_time": total_time
        }
    }

def collect_all_input_field_values(conn, post_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
    """Collect ALL input fields from step config and their values from database tables."""
    all_input_fields = {}
    
    # Get all input fields from step configuration (these are what appear in the Inputs dropdown)
    input_mapping = config.get('inputs', {})
    
    # First, collect all fields from post_development table
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get all columns from post_development table
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'post_development' 
                AND column_name NOT IN ('id', 'post_id')
                ORDER BY ordinal_position
            """)
            dev_columns = [row['column_name'] for row in cur.fetchall()]
            
            # Fetch all post_development fields for this post
            if dev_columns:
                column_list = ', '.join(dev_columns)
                cur.execute(f"SELECT {column_list} FROM post_development WHERE post_id = %s", (post_id,))
                dev_result = cur.fetchone()
                
                if dev_result:
                    for column in dev_columns:
                        field_id = f"post_development_{column}"
                        all_input_fields[field_id] = {
                            'input_id': field_id,
                            'db_field': column,
                            'db_table': 'post_development',
                            'value': dev_result[column],
                            'display_name': column.replace('_', ' ').title(),
                            'type': 'text',
                            'source': 'post_development_table'
                        }
                else:
                    # Post development record doesn't exist, log all fields as null
                    for column in dev_columns:
                        field_id = f"post_development_{column}"
                        all_input_fields[field_id] = {
                            'input_id': field_id,
                            'db_field': column,
                            'db_table': 'post_development',
                            'value': None,
                            'display_name': column.replace('_', ' ').title(),
                            'type': 'text',
                            'source': 'post_development_table',
                            'note': 'No post_development record found for this post'
                        }
    except Exception as e:
        all_input_fields['post_development_error'] = {
            'input_id': 'post_development_error',
            'db_field': 'error',
            'db_table': 'post_development',
            'value': None,
            'display_name': 'Post Development Error',
            'type': 'error',
            'error': str(e)
        }
    
    # Then, collect all fields from post_section table
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get all columns from post_section table
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'post_section' 
                AND column_name NOT IN ('id', 'post_id')
                ORDER BY ordinal_position
            """)
            section_columns = [row['column_name'] for row in cur.fetchall()]
            
            # Fetch all post_section fields for this post
            if section_columns:
                column_list = ', '.join(section_columns)
                cur.execute(f"SELECT id, {column_list} FROM post_section WHERE post_id = %s", (post_id,))
                section_results = cur.fetchall()
                
                if section_results:
                    # Create a mapping of section_id to all field values
                    for column in section_columns:
                        field_id = f"post_section_{column}"
                        section_values = {row['id']: row[column] for row in section_results}
                        all_input_fields[field_id] = {
                            'input_id': field_id,
                            'db_field': column,
                            'db_table': 'post_section',
                            'value': section_values,
                            'display_name': column.replace('_', ' ').title(),
                            'type': 'text',
                            'source': 'post_section_table',
                            'section_count': len(section_results)
                        }
                else:
                    # No sections found, log all fields as empty
                    for column in section_columns:
                        field_id = f"post_section_{column}"
                        all_input_fields[field_id] = {
                            'input_id': field_id,
                            'db_field': column,
                            'db_table': 'post_section',
                            'value': {},
                            'display_name': column.replace('_', ' ').title(),
                            'type': 'text',
                            'source': 'post_section_table',
                            'note': 'No sections found for this post'
                        }
    except Exception as e:
        all_input_fields['post_section_error'] = {
            'input_id': 'post_section_error',
            'db_field': 'error',
            'db_table': 'post_section',
            'value': None,
            'display_name': 'Post Section Error',
            'type': 'error',
            'error': str(e)
        }
    
    # Finally, add the configured input fields with their specific config info
    for input_id, input_config in input_mapping.items():
        db_field = input_config.get('db_field', input_id)
        db_table = input_config.get('db_table', 'post_development')
        
        # Check if we already have this field in our collection
        existing_field_id = f"{db_table}_{db_field}"
        if existing_field_id in all_input_fields:
            # Update the existing field with config info
            all_input_fields[existing_field_id].update({
                'configured_input_id': input_id,
                'configured_label': input_config.get('label', input_id),
                'configured_type': input_config.get('type', 'unknown'),
                'is_configured': True
            })
        else:
            # This is a configured field that we didn't find in our table scan
            all_input_fields[input_id] = {
                'input_id': input_id,
                'db_field': db_field,
                'db_table': db_table,
                'value': None,
                'display_name': input_config.get('label', input_id),
                'type': input_config.get('type', 'unknown'),
                'configured_input_id': input_id,
                'configured_label': input_config.get('label', input_id),
                'configured_type': input_config.get('type', 'unknown'),
                'is_configured': True,
                'note': f'Configured field not found in {db_table} table'
            }
    
    return all_input_fields

def process_step(post_id: int, stage: str, substage: str, step: str, frontend_inputs: Dict[str, Any] = None):
    """Main function to process a workflow step with format validation and multiple inputs."""
    diagnostic_data = {
        "db_fields": {},
        "llm_message": "",
        "llm_response": "",
        "frontend_inputs": frontend_inputs or {},
        "input_field_values": {}
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
        diagnostic_data["input_field_values"] = collect_all_input_field_values(conn, post_id, config)  # Log ALL input fields and their values

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
        prompt = construct_prompt(system_prompt, task_prompt, inputs, all_db_fields, input_format_template, output_format_template, config, stage)
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
            diagnostic_data["frontend_inputs"],
            diagnostic_data["input_field_values"]
        )
        print(f"Successfully processed step {step} for post {post_id}")
        return output
    except Exception as e:
        if diagnostic_data["llm_message"] or diagnostic_data["db_fields"]:
            create_diagnostic_logs(
                post_id, stage, substage, step,
                diagnostic_data["db_fields"],
                diagnostic_data["llm_message"],
                diagnostic_data["llm_response"],
                diagnostic_data.get("input_format_template"),
                diagnostic_data.get("output_format_template"),
                diagnostic_data["frontend_inputs"],
                diagnostic_data["input_field_values"]
            )
        print(f"Error processing step: {str(e)}", file=sys.stderr)
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def standardize_llm_response(success, results, step, sections_processed, parameters=None):
    """Standardize LLM response format for consistent frontend handling"""
    return {
        'success': success,
        'results': results,
        'step': step,
        'sections_processed': sections_processed,
        'parameters': parameters or {}
    }

def resolve_field_value(table_name, column_name, context):
    """
    Resolve field value from specified table based on context
    
    Args:
        table_name: Name of the table (post_development, post_section, etc.)
        column_name: Name of the column
        context: Dict with post_id, section_id, etc.
    
    Returns:
        Field value or None if not found
    """
    conn = get_db_conn()
    try:
        if table_name == 'post_development':
            # Fetch from post_development table
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT %s FROM post_development WHERE post_id = %s",
                (column_name, context['post_id'])
            )
            result = cursor.fetchone()
            return result[column_name] if result else None
            
        elif table_name == 'post_section':
            # Fetch from post_section table for specific section
            if 'section_id' not in context:
                raise ValueError("section_id required for post_section table")
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT %s FROM post_section WHERE id = %s AND post_id = %s",
                (column_name, context['section_id'], context['post_id'])
            )
            result = cursor.fetchone()
            return result[column_name] if result else None
            
        else:
            # Future tables can be added here
            raise ValueError(f"Unsupported table: {table_name}")
            
    finally:
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