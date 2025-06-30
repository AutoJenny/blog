"""
External Prompt Constructor for Workflow LLM Integration

This module provides structured prompt construction with format template integration.
It builds prompts with CONTEXT, TASK, and RESPONSE sections using step-level format configuration.

Author: Blog CMS Team
Date: June 30, 2025
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of prompt data validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]

@dataclass
class ProcessedTemplates:
    """Processed format template data."""
    input_instructions: str
    input_description: str
    input_schema: Dict[str, Any]
    output_instructions: str
    output_description: str
    output_schema: Dict[str, Any]

@dataclass
class MappedInput:
    """Mapped input data with field transformations."""
    field_mappings: Dict[str, str]
    transformed_data: Dict[str, Any]
    validation_status: bool

@dataclass
class ContextData:
    """Data for CONTEXT section."""
    system_prompt: str
    input_instructions: str
    input_description: str

@dataclass
class TaskData:
    """Data for TASK section."""
    task_prompt: str
    input_data: Dict[str, Any]

@dataclass
class ResponseData:
    """Data for RESPONSE section."""
    output_instructions: str
    output_description: str


def validate_prompt_data(
    system_prompt: str,
    task_prompt: str,
    input_format_template: Dict[str, Any],
    output_format_template: Dict[str, Any],
    input_data: Dict[str, Any],
    step_config: Dict[str, Any]
) -> ValidationResult:
    """
    Validate all required data is present and properly formatted.
    
    Args:
        system_prompt: System prompt for the LLM
        task_prompt: Task-specific prompt
        input_format_template: Input format template data
        output_format_template: Output format template data
        input_data: Input data for the prompt
        step_config: Step configuration data
    
    Returns:
        ValidationResult with validation status and any errors/warnings
    """
    errors = []
    warnings = []
    
    # Validate required fields
    if not system_prompt or not system_prompt.strip():
        errors.append("System prompt is required and cannot be empty")
    
    if not task_prompt or not task_prompt.strip():
        errors.append("Task prompt is required and cannot be empty")
    
    if not input_format_template:
        errors.append("Input format template is required")
    elif not isinstance(input_format_template, dict):
        errors.append("Input format template must be a dictionary")
    
    if not output_format_template:
        errors.append("Output format template is required")
    elif not isinstance(output_format_template, dict):
        errors.append("Output format template must be a dictionary")
    
    if not input_data:
        warnings.append("Input data is empty - this may cause issues")
    
    if not step_config:
        warnings.append("Step configuration is empty - using defaults")
    
    # Validate format template structure
    if input_format_template:
        required_fields = ['id', 'name', 'description', 'fields', 'llm_instructions']
        for field in required_fields:
            if field not in input_format_template:
                errors.append(f"Input format template missing required field: {field}")
    
    if output_format_template:
        required_fields = ['id', 'name', 'description', 'fields', 'llm_instructions']
        for field in required_fields:
            if field not in output_format_template:
                errors.append(f"Output format template missing required field: {field}")
    
    # Validate input data structure
    if input_data and not isinstance(input_data, dict):
        errors.append("Input data must be a dictionary")
    
    # Validate step configuration
    if step_config and not isinstance(step_config, dict):
        errors.append("Step configuration must be a dictionary")
    
    valid = len(errors) == 0
    
    return ValidationResult(
        valid=valid,
        errors=errors,
        warnings=warnings
    )


def extract_format_instructions(
    format_template: Dict[str, Any],
    format_type: str
) -> Dict[str, str]:
    """
    Extract LLM instructions and description from format template.
    
    Args:
        format_template: Format template data
        format_type: "input" or "output"
    
    Returns:
        Dictionary with llm_instructions, description, and schema_summary
    """
    if not format_template:
        return {
            "llm_instructions": "",
            "description": "",
            "schema_summary": ""
        }
    
    # Extract basic fields
    llm_instructions = format_template.get('llm_instructions', '')
    description = format_template.get('description', '')
    
    # Extract schema information
    fields = format_template.get('fields', {})
    schema = fields.get('schema', {}) if isinstance(fields, dict) else {}
    
    # Create schema summary
    schema_summary = ""
    if schema:
        schema_type = schema.get('type', 'unknown')
        if schema_type == 'object':
            properties = schema.get('properties', {})
            required = schema.get('required', [])
            schema_summary = f"JSON object with properties: {list(properties.keys())}"
            if required:
                schema_summary += f" (required: {required})"
        elif schema_type == 'string':
            schema_summary = "Plain text string"
        elif schema_type == 'array':
            schema_summary = "Array of values"
        else:
            schema_summary = f"{schema_type} data type"
    
    return {
        "llm_instructions": llm_instructions,
        "description": description,
        "schema_summary": schema_summary
    }


def map_input_fields(
    input_data: Dict[str, Any],
    step_config: Dict[str, Any],
    input_format_template: Dict[str, Any]
) -> MappedInput:
    """
    Map input data according to step configuration and format template.
    
    Args:
        input_data: Raw input data
        step_config: Step configuration with input mapping
        input_format_template: Input format template for validation
    
    Returns:
        MappedInput with field mappings and transformed data
    """
    field_mappings = {}
    transformed_data = {}
    validation_status = True
    
    if not input_data:
        return MappedInput(
            field_mappings={},
            transformed_data={},
            validation_status=False
        )
    
    # Get input mapping from step configuration
    input_mapping = step_config.get('input_mapping', {})
    
    # Transform field names and values
    field_index = 1
    for field_name, field_value in input_data.items():
        # Skip empty or None values
        if field_value is None or (isinstance(field_value, str) and not field_value.strip()):
            continue
        
        # Create transformed field name (Input1, Input2, etc.)
        transformed_name = f"Input{field_index}"
        field_mappings[field_name] = transformed_name
        
        # Transform field value based on format template
        transformed_value = transform_field_value(field_value, input_format_template)
        transformed_data[transformed_name] = transformed_value
        
        field_index += 1
    
    # Validate against input format template if available
    if input_format_template:
        validation_status = validate_input_against_template(
            transformed_data, input_format_template
        )
    
    return MappedInput(
        field_mappings=field_mappings,
        transformed_data=transformed_data,
        validation_status=validation_status
    )


def transform_field_value(
    field_value: Any,
    input_format_template: Dict[str, Any]
) -> Any:
    """
    Transform field value based on input format template.
    
    Args:
        field_value: Original field value
        input_format_template: Input format template for guidance
    
    Returns:
        Transformed field value
    """
    if not input_format_template:
        return field_value
    
    # Get schema information
    fields = input_format_template.get('fields', {})
    schema = fields.get('schema', {}) if isinstance(fields, dict) else {}
    
    # Handle different data types
    if isinstance(field_value, str):
        # String processing
        if schema.get('type') == 'string':
            # Ensure proper string formatting
            return field_value.strip()
        elif schema.get('type') == 'object':
            # Try to parse as JSON if expected
            try:
                import json
                return json.loads(field_value)
            except (json.JSONDecodeError, TypeError):
                return field_value
    elif isinstance(field_value, (list, tuple)):
        # Array processing
        if schema.get('type') == 'array':
            return list(field_value)
        else:
            # Convert to string if not expected as array
            return str(field_value)
    elif isinstance(field_value, dict):
        # Object processing
        if schema.get('type') == 'object':
            return field_value
        else:
            # Convert to string if not expected as object
            return str(field_value)
    
    return field_value


def validate_input_against_template(
    input_data: Dict[str, Any],
    input_format_template: Dict[str, Any]
) -> bool:
    """
    Validate input data against input format template.
    
    Args:
        input_data: Transformed input data
        input_format_template: Input format template
    
    Returns:
        True if validation passes, False otherwise
    """
    if not input_format_template:
        return True
    
    try:
        fields = input_format_template.get('fields', {})
        schema = fields.get('schema', {}) if isinstance(fields, dict) else {}
        
        # Basic validation - check if we have the expected data structure
        if schema.get('type') == 'object':
            # For object types, check if we have any data
            return len(input_data) > 0
        elif schema.get('type') == 'string':
            # For string types, check if we have string data
            return any(isinstance(v, str) for v in input_data.values())
        elif schema.get('type') == 'array':
            # For array types, check if we have array data
            return any(isinstance(v, (list, tuple)) for v in input_data.values())
        
        return True
    except Exception as e:
        logger.warning(f"Input validation error: {e}")
        return False


def build_context_section(
    system_prompt: str,
    input_format_instructions: Dict[str, str]
) -> str:
    """
    Build CONTEXT section with system prompt and input format instructions.
    
    Args:
        system_prompt: System prompt for the LLM
        input_format_instructions: Input format instructions and description
    
    Returns:
        Formatted CONTEXT section
    """
    context_parts = ["CONTEXT:"]
    
    # Add system prompt
    if system_prompt:
        context_parts.append(system_prompt.strip())
    
    # Add input format instructions
    llm_instructions = input_format_instructions.get('llm_instructions', '')
    description = input_format_instructions.get('description', '')
    
    if llm_instructions:
        context_parts.append(llm_instructions.strip())
    
    if description:
        context_parts.append(description.strip())
    
    return "\n\n".join(context_parts)


def build_task_section(
    task_prompt: str,
    input_data: Dict[str, Any]
) -> str:
    """
    Build TASK section with task prompt and mapped input data.
    
    Args:
        task_prompt: Task-specific prompt
        input_data: Mapped input data
    
    Returns:
        Formatted TASK section
    """
    task_parts = ["TASK:"]
    
    # Add task prompt
    if task_prompt:
        task_parts.append(task_prompt.strip())
    
    # Add input data
    if input_data:
        for field_name, field_value in input_data.items():
            if field_value is not None:
                if isinstance(field_value, str):
                    task_parts.append(f"{field_name}:\n{field_value}")
                else:
                    task_parts.append(f"{field_name}:\n{str(field_value)}")
    
    return "\n\n".join(task_parts)


def build_response_section(
    output_format_instructions: Dict[str, str]
) -> str:
    """
    Build RESPONSE section with output format instructions.
    
    Args:
        output_format_instructions: Output format instructions and description
    
    Returns:
        Formatted RESPONSE section
    """
    response_parts = ["RESPONSE:"]
    
    # Add output format instructions
    llm_instructions = output_format_instructions.get('llm_instructions', '')
    description = output_format_instructions.get('description', '')
    
    if llm_instructions:
        response_parts.append(llm_instructions.strip())
    
    if description:
        response_parts.append(description.strip())
    
    return "\n\n".join(response_parts)


def build_prompt_sections(
    context_data: ContextData,
    task_data: TaskData,
    response_data: ResponseData
) -> str:
    """
    Build individual prompt sections with proper formatting.
    
    Args:
        context_data: Data for CONTEXT section
        task_data: Data for TASK section
        response_data: Data for RESPONSE section
    
    Returns:
        Complete formatted prompt with all sections
    """
    sections = []
    
    # Build CONTEXT section
    context_section = build_context_section(
        context_data.system_prompt,
        {
            "llm_instructions": context_data.input_instructions,
            "description": context_data.input_description
        }
    )
    sections.append(context_section)
    
    # Build TASK section
    task_section = build_task_section(
        task_data.task_prompt,
        task_data.input_data
    )
    sections.append(task_section)
    
    # Build RESPONSE section
    response_section = build_response_section(
        {
            "llm_instructions": response_data.output_instructions,
            "description": response_data.output_description
        }
    )
    sections.append(response_section)
    
    # Join sections with double newlines for clear separation
    return "\n\n".join(sections)


def build_structured_prompt(
    system_prompt: str,
    task_prompt: str,
    input_format_template: Dict[str, Any],
    output_format_template: Dict[str, Any],
    input_data: Dict[str, Any],
    step_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build a structured prompt with CONTEXT, TASK, and RESPONSE sections.
    
    Args:
        system_prompt: System prompt for the LLM
        task_prompt: Task-specific prompt
        input_format_template: Input format template data
        output_format_template: Output format template data
        input_data: Input data for the prompt
        step_config: Step configuration data
    
    Returns:
        Dictionary with prompt, validation status, and metadata
    """
    try:
        # Step 1: Validate input data
        validation_result = validate_prompt_data(
            system_prompt, task_prompt, input_format_template,
            output_format_template, input_data, step_config
        )
        
        if not validation_result.valid:
            return {
                "prompt": "",
                "validation": {
                    "valid": False,
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings
                },
                "metadata": {
                    "error": "Prompt validation failed",
                    "validation_result": validation_result
                }
            }
        
        # Log warnings if any
        if validation_result.warnings:
            logger.warning(f"Prompt construction warnings: {validation_result.warnings}")
        
        # Step 2: Extract format template instructions
        input_instructions = extract_format_instructions(input_format_template, "input")
        output_instructions = extract_format_instructions(output_format_template, "output")
        
        # Step 3: Map input fields
        mapped_input = map_input_fields(input_data, step_config, input_format_template)
        
        if not mapped_input.validation_status:
            logger.warning("Input field mapping validation failed")
        
        # Step 4: Build prompt sections
        context_data = ContextData(
            system_prompt=system_prompt,
            input_instructions=input_instructions["llm_instructions"],
            input_description=input_instructions["description"]
        )
        
        task_data = TaskData(
            task_prompt=task_prompt,
            input_data=mapped_input.transformed_data
        )
        
        response_data = ResponseData(
            output_instructions=output_instructions["llm_instructions"],
            output_description=output_instructions["description"]
        )
        
        # Step 5: Assemble final prompt
        prompt = build_prompt_sections(context_data, task_data, response_data)
        
        # Step 6: Create metadata
        metadata = {
            "input_format_id": input_format_template.get('id') if input_format_template else None,
            "output_format_id": output_format_template.get('id') if output_format_template else None,
            "field_mappings": mapped_input.field_mappings,
            "input_fields_count": len(mapped_input.transformed_data),
            "prompt_length": len(prompt),
            "sections": ["CONTEXT", "TASK", "RESPONSE"]
        }
        
        return {
            "prompt": prompt,
            "validation": {
                "valid": True,
                "errors": [],
                "warnings": validation_result.warnings
            },
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Error building structured prompt: {e}")
        return {
            "prompt": "",
            "validation": {
                "valid": False,
                "errors": [f"Prompt construction error: {str(e)}"],
                "warnings": []
            },
            "metadata": {
                "error": str(e),
                "error_type": type(e).__name__
            }
        }


def handle_prompt_construction_errors(prompt_result: Dict[str, Any]) -> None:
    """
    Handle prompt construction errors with detailed logging.
    
    Args:
        prompt_result: Result from build_structured_prompt
    """
    if not prompt_result['validation']['valid']:
        error_msg = f"Prompt construction failed: {prompt_result['validation']['errors']}"
        logger.error(error_msg)
        
        # Log detailed validation information
        if 'validation_result' in prompt_result.get('metadata', {}):
            validation_result = prompt_result['metadata']['validation_result']
            logger.error(f"Validation details: {validation_result}")
        
        # Raise custom exception for error handling
        raise PromptConstructionError(error_msg)


def log_prompt_construction_metadata(prompt_result: Dict[str, Any]) -> None:
    """
    Log prompt construction metadata for debugging.
    
    Args:
        prompt_result: Result from build_structured_prompt
    """
    metadata = prompt_result.get('metadata', {})
    logger.info(f"Prompt constructed successfully: {metadata}")
    
    # Log prompt structure statistics
    prompt = prompt_result.get('prompt', '')
    if prompt:
        logger.info(f"Prompt length: {len(prompt)} characters")
        logger.info(f"Prompt sections: {metadata.get('sections', [])}")


class PromptConstructionError(Exception):
    """Custom exception for prompt construction errors."""
    pass


# Example usage and testing
if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(level=logging.INFO)
    
    # Example format templates
    example_input_template = {
        "id": 27,
        "name": "Title-description JSON (Input)",
        "description": "Structured JSON with two elements: title (string) and description (string).",
        "fields": {
            "type": "input",
            "schema": {
                "type": "object",
                "required": ["title", "description"],
                "properties": {
                    "title": {"type": "string", "description": "The main title"},
                    "description": {"type": "string", "description": "A description of the title"}
                }
            }
        },
        "llm_instructions": "The input will be provided as a JSON object with title and description fields. Process this input according to the specified schema requirements.",
        "created_at": "2025-06-29 10:23:51.020087",
        "updated_at": "2025-06-30 11:31:07.802536"
    }
    
    example_output_template = {
        "id": 38,
        "name": "Plain text (GB) - Output",
        "description": "Plain text output using UK English spellings and idioms.",
        "fields": {
            "type": "output",
            "schema": {
                "type": "string",
                "description": "Plain text response"
            }
        },
        "llm_instructions": "Return your response as plain text using UK English spellings and idioms. Do not include any JSON formatting or special characters.",
        "created_at": "2025-06-29 10:23:51.020087",
        "updated_at": "2025-06-30 11:31:07.802536"
    }
    
    # Example usage
    result = build_structured_prompt(
        system_prompt="You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do.",
        task_prompt="Generate five alternative, arresting, and informative blog post titles for a post based on the following Input.",
        input_format_template=example_input_template,
        output_format_template=example_output_template,
        input_data={"idea_seed": "Story-telling"},
        step_config={"input_mapping": {"idea_seed": "Input1"}}
    )
    
    print("Prompt Construction Result:")
    print(f"Valid: {result['validation']['valid']}")
    print(f"Errors: {result['validation']['errors']}")
    print(f"Warnings: {result['validation']['warnings']}")
    print("\nGenerated Prompt:")
    print(result['prompt'])
    print(f"\nMetadata: {result['metadata']}") 