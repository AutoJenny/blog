# Script Registry System Reference

## Overview

The Script Registry System provides a centralized, extensible framework for executing different types of workflow actions. This system replaces ad-hoc script handling with a unified approach that supports LLM actions, custom scripts, and image generation while maintaining isolation between workflow steps.

## Architecture

### Core Components

```
Script Registry System
├── Registry (script_registry.py)
│   ├── SCRIPT_REGISTRY - Type-to-handler mapping
│   ├── execute_step_script() - Main execution function
│   └── register_script_type() - Extensibility mechanism
├── Handlers
│   ├── llm_actions.py - LLM action execution
│   ├── custom_scripts.py - Custom script execution
│   └── image_generation.py - Image generation execution
└── Configuration
    ├── workflow_step_entity.config - Step-specific settings
    └── post_workflow_step_action - Post-specific overrides
```

### Script Types

1. **`llm_action`**: Standard LLM processing using configured actions
2. **`custom_script`**: Custom endpoint execution for specialized processing
3. **`image_generation`**: Image generation using external services (e.g., DALL-E)

## Database Schema

### Extended Step Configuration

The `workflow_step_entity.config` JSONB field now supports script configuration:

```json
{
  "inputs": {
    "input1": {
      "label": "Input Field Label",
      "db_field": "database_field_name",
      "type": "text|textarea"
    }
  },
  "outputs": {
    "output1": {
      "label": "Output Field Label",
      "db_field": "database_field_name",
      "type": "text|textarea"
    }
  },
  "script_config": {
    "type": "llm_action|custom_script|image_generation",
    "action_id": 123,
    "custom_endpoint": "/api/images/generate-batch",
    "parameters": {
      "model": "dall-e-3",
      "size": "1024x1024",
      "timeout": 30
    }
  }
}
```

### Script Configuration Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `type` | string | Script type identifier | Yes |
| `action_id` | integer | LLM action ID (for llm_action type) | Conditional |
| `custom_endpoint` | string | Custom API endpoint (for custom_script type) | Conditional |
| `parameters` | object | Script-specific parameters | No |

## Implementation

### 1. Script Registry Core

```python
# app/workflow/scripts/registry.py

from typing import Dict, Any, Callable
from . import llm_actions, custom_scripts, image_generation

SCRIPT_REGISTRY: Dict[str, Callable] = {
    'llm_action': llm_actions.execute_llm_action,
    'custom_script': custom_scripts.execute_custom_script,
    'image_generation': image_generation.execute_image_generation
}

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
    step_config = get_step_config(step_id)
    script_config = step_config.get('script_config', {})
    script_type = script_config.get('type', 'llm_action')
    
    if script_type not in SCRIPT_REGISTRY:
        raise ValueError(f"Unknown script type: {script_type}")
    
    handler = SCRIPT_REGISTRY[script_type]
    return handler(step_config, post_id, context)

def register_script_type(script_type: str, handler: Callable) -> None:
    """Register a new script type handler."""
    SCRIPT_REGISTRY[script_type] = handler
```

### 2. LLM Action Handler

```python
# app/workflow/scripts/llm_actions.py

def execute_llm_action(step_config: Dict[str, Any], post_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute LLM action for workflow step."""
    action_id = step_config['script_config']['action_id']
    section_ids = context.get('section_ids', [])
    
    if section_ids:
        return process_sections_with_llm(action_id, post_id, section_ids, context)
    else:
        return process_individual_llm_action(action_id, post_id, context)
```

### 3. Image Generation Handler

```python
# app/workflow/scripts/image_generation.py

def execute_image_generation(step_config: Dict[str, Any], post_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute image generation for workflow step."""
    parameters = step_config['script_config']['parameters']
    section_ids = context.get('section_ids', [])
    
    # Call blog-images service for batch processing
    return call_image_generation_service(post_id, section_ids, parameters)
```

## API Integration

### New Endpoint: Execute Step

```http
POST /api/workflow/execute-step
```

**Request Body:**
```json
{
  "step_id": 123,
  "post_id": 53,
  "context": {
    "section_ids": [711, 712, 713],
    "inputs": {
      "image_prompts": "Scottish highland landscape"
    },
    "llm_settings": {
      "model": "dall-e-3",
      "temperature": 0.7
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "section_id": 711,
      "status": "success",
      "image_url": "/static/content/posts/53/sections/711/raw/image.png",
      "metadata": {
        "model": "dall-e-3",
        "generation_time": "2025-07-26T07:06:40Z"
      }
    }
  ],
  "step": "section_illustrations",
  "sections_processed": [711, 712, 713]
}
```

## Frontend Integration

### Updated Run LLM Button Handler

```javascript
async function handleRunActionClick(context) {
    const stepId = context.step_id;
    const postId = context.post_id;
    
    // Gather context from UI
    const sectionIds = await getSelectedSectionIds();
    const inputs = gatherInputsFromUI();
    const llmSettings = gatherLLMSettingsFromUI();
    
    const executionContext = {
        section_ids: sectionIds,
        inputs: inputs,
        llm_settings: llmSettings
    };
    
    // Call centralized script execution
    const response = await fetch('/api/workflow/execute-step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            step_id: stepId, 
            post_id: postId, 
            context: executionContext 
        })
    });
    
    const result = await response.json();
    handleExecutionResult(result);
}
```

## Step Configuration Examples

### 1. LLM Action Step

```json
{
  "inputs": {
    "input1": {
      "label": "Section Content",
      "db_field": "draft",
      "type": "textarea"
    }
  },
  "outputs": {
    "output1": {
      "label": "Polished Content",
      "db_field": "polished",
      "type": "textarea"
    }
  },
  "script_config": {
    "type": "llm_action",
    "action_id": 5
  }
}
```

### 2. Image Generation Step

```json
{
  "inputs": {
    "input1": {
      "label": "Image Prompts",
      "db_field": "image_prompts",
      "type": "textarea"
    }
  },
  "outputs": {
    "output1": {
      "label": "Generated Image URL",
      "db_field": "generated_image_url",
      "type": "text"
    }
  },
  "script_config": {
    "type": "image_generation",
    "parameters": {
      "model": "dall-e-3",
      "size": "1024x1024",
      "timeout": 30
    }
  }
}
```

### 3. Custom Script Step

```json
{
  "inputs": {
    "input1": {
      "label": "Input Data",
      "db_field": "raw_data",
      "type": "textarea"
    }
  },
  "outputs": {
    "output1": {
      "label": "Processed Data",
      "db_field": "processed_data",
      "type": "textarea"
    }
  },
  "script_config": {
    "type": "custom_script",
    "custom_endpoint": "/api/custom/process-data",
    "parameters": {
      "format": "json",
      "validation": true
    }
  }
}
```

## Migration Guide

### From Legacy System

1. **Identify Current Scripts**: Map existing hardcoded scripts to script types
2. **Create Step Configurations**: Add script_config to existing workflow_step_entity records
3. **Update Frontend**: Replace direct script calls with centralized execution
4. **Test Thoroughly**: Verify all existing functionality works with new system

### Database Migration

```sql
-- Add script_config to existing steps (example)
UPDATE workflow_step_entity 
SET config = config || '{"script_config": {"type": "llm_action", "action_id": 1}}'::jsonb
WHERE name = 'existing_step_name';
```

## Best Practices

### 1. Script Type Design

- **Keep Types Generic**: Design script types to be reusable across different steps
- **Parameter Validation**: Validate all parameters before execution
- **Error Handling**: Provide meaningful error messages for debugging
- **Logging**: Log all script executions for audit trails

### 2. Configuration Management

- **Default Values**: Provide sensible defaults for all parameters
- **Validation**: Validate configuration at step creation/update
- **Documentation**: Document all available parameters for each script type

### 3. Performance Considerations

- **Async Execution**: Use async/await for I/O operations
- **Timeout Handling**: Implement appropriate timeouts for all script types
- **Resource Management**: Clean up resources after script execution
- **Caching**: Cache frequently used configurations and results

## Testing

### Unit Tests

```python
def test_execute_step_script_llm_action():
    """Test LLM action execution."""
    step_config = {
        'script_config': {'type': 'llm_action', 'action_id': 1}
    }
    context = {'section_ids': [1, 2, 3]}
    
    result = execute_step_script(1, 53, context)
    assert result['success'] == True
    assert len(result['results']) == 3

def test_execute_step_script_image_generation():
    """Test image generation execution."""
    step_config = {
        'script_config': {
            'type': 'image_generation',
            'parameters': {'model': 'dall-e-3'}
        }
    }
    context = {'section_ids': [711]}
    
    result = execute_step_script(1, 53, context)
    assert result['success'] == True
    assert 'image_url' in result['results'][0]
```

### Integration Tests

```python
def test_section_illustrations_workflow():
    """Test complete section illustrations workflow."""
    # Test step configuration
    # Test script execution
    # Test database updates
    # Test file storage
    pass
```

## Future Extensibility

### Adding New Script Types

1. **Create Handler**: Implement handler function in appropriate module
2. **Register Type**: Add to SCRIPT_REGISTRY
3. **Update Documentation**: Document new script type and parameters
4. **Add Tests**: Create comprehensive test coverage

### Example: Video Generation

```python
# Register new script type
register_script_type('video_generation', video_generation.execute_video_generation)

# Step configuration
{
  "script_config": {
    "type": "video_generation",
    "parameters": {
      "model": "stable-video-diffusion",
      "duration": 5,
      "fps": 24
    }
  }
}
```

## Related Documentation

- [Workflow System Overview](README.md)
- [LLM Panel Integration](llm_panel.md)
- [Section Management](sections.md)
- [API Endpoints](endpoints.md)
- [Database Schema](../database/schema.md) 

## Step-Specific Template System (Frontend Integration)

To support multiple script types and specialized UIs, the workflow frontend now uses a step-specific template system:

- **Template Selection**: The backend inspects the step's `script_config.type` and selects the appropriate template for rendering the workflow panel.
- **Template Map Example**:

```python
TEMPLATE_MAP = {
    'image_generation': 'workflow/steps/section_illustrations.html',
    'llm_action': 'workflow/steps/llm_action.html',
    'custom_script': 'workflow/steps/custom_script.html',
}
```

- **Integration**: When rendering a workflow step, the backend includes the template from the map based on the script type. This allows for custom UIs for steps like image generation, while keeping legacy LLM actions unchanged.
- **Migration Note**: Legacy steps continue to use the default LLM actions template unless explicitly migrated to a new script type and template.

See the main README for more details and the implementation plan. 