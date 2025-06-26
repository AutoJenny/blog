# Workflow Testing Guide

## Overview
This guide provides instructions for testing workflow endpoints, including field mappings, prompts, and LLM processing.
 
## Prerequisites
- Running Flask server on port 5000
- PostgreSQL database with required tables
- Valid post ID for testing (e.g., 38)

## Testing Workflow Endpoints

### 1. Field Mappings

Get available fields for a stage/substage:

```bash
# Get field mappings for planning/idea stage
curl -s "http://localhost:5000/workflow/api/field_mappings/?stage=planning&substage=idea" | python3 -m json.tool

# Get field mappings for planning/research stage
curl -s "http://localhost:5000/workflow/api/field_mappings/?stage=planning&substage=research" | python3 -m json.tool
```

Expected response format:
```json
{
  "planning": {
    "idea": {
      "inputs": [
        {
          "field_name": "idea_seed",
          "display_name": "Idea Seed"
        }
      ],
      "outputs": [
        {
          "field_name": "basic_idea",
          "display_name": "Basic Idea"
        }
      ]
    }
  }
}
```

### 2. Update Field Mapping

Map a field to a workflow step:

```bash
curl -s -X POST "http://localhost:5000/workflow/api/update_field_mapping/" \
  -H "Content-Type: application/json" \
  -d '{
    "target_id": "input1",
    "field_name": "idea_seed",
    "section": "inputs",
    "stage": "planning",
    "substage": "idea",
    "step": "Initial Concept"
  }' | python3 -m json.tool
```

Expected response format:
```json
{
  "field_name": "idea_seed",
  "section": "inputs",
  "table_name": "post_development"
}
```

### 3. Post Development Fields

Get and update development fields:

```bash
# Get all development fields
curl -s "http://localhost:5000/api/v1/post/38/development" | python3 -m json.tool

# Update a development field
curl -s -X POST "http://localhost:5000/api/v1/post/38/development" \
  -H "Content-Type: application/json" \
  -d '{"idea_seed": "Test idea seed"}' | python3 -m json.tool
```

Expected response format:
```json
{
  "idea_seed": "Test idea seed",
  "basic_idea": "...",
  "provisional_title": "..."
}
```

### 4. Workflow LLM Processing

Run LLM processing for a workflow step:

```bash
curl -s -X POST "http://localhost:5000/api/v1/workflow/run_llm/" \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": 38,
    "stage": "planning",
    "substage": "idea",
    "step": "Initial Concept"
  }' | python3 -m json.tool
```

Expected response format:
```json
{
  "success": true,
  "result": "Generated content..."
}
```

## Workflow Steps and Post IDs

### Post IDs
- Post IDs are numeric and start from 1
- Use the test_insert endpoint to create a test post:
  ```bash
  curl -s "http://localhost:5000/test_insert" | python3 -m json.tool
  ```

### Workflow Steps
Steps are organized hierarchically:

1. Planning Stage
   - Idea Substage
     - Initial Concept
     - Basic Idea
     - Provisional Title
   - Research Substage
     - Facts
     - Concepts
   - Structure Substage
     - Outline
     - Allocate Facts

2. Authoring Stage
   - Content Substage
     - Draft
     - Review
   - Meta Info Substage
     - SEO
     - Social
   - Images Substage
     - Planning
     - Generation

3. Publishing Stage
   - Preflight Substage
     - Review
     - Validation
   - Launch Substage
     - Publish
     - Verify
   - Syndication Substage
     - Plan
     - Execute

### Step Names
- In URLs: lowercase with underscores (e.g., `initial_concept`)
- In API calls: Title Case with spaces (e.g., `Initial Concept`)
- Always check the database for exact step names:
  ```bash
  psql blog -c "SELECT wst.name as stage, wsse.name as substage, wse.name as step FROM workflow_stage_entity wst JOIN workflow_sub_stage_entity wsse ON wsse.stage_id = wst.id JOIN workflow_step_entity wse ON wse.sub_stage_id = wsse.id ORDER BY wst.id, wsse.id, wse.id;"
  ```

## Common Issues

1. Step Not Found
   - Ensure step names match exactly what's in the database
   - Check case sensitivity and spacing
   - Use the SQL query above to verify step names

2. Post Not Found
   - Verify post ID exists
   - Use test_insert to create a test post
   - Check post_development table for valid IDs

3. Field Mapping Errors
   - Verify field names exist in post_development table
   - Check stage/substage/step hierarchy
   - Ensure target_id matches frontend field selector

4. LLM Processing Errors
   - Check Ollama is running (default: http://localhost:11434)
   - Verify input fields have values
   - Check step configuration exists in database 

## Testing Workflow Step Prompt Configuration

### Prerequisites
- Ensure all required tables (`workflow_step_prompt`, `workflow_step_entity`, `llm_prompt`) exist and have correct ownership
- Have a valid post ID and step ID ready for testing
- Have valid system and task prompt IDs from the `llm_prompt` table

### Test Cases

1. Save Step Prompts
```bash
# Save prompts for step
curl -X POST "http://localhost:5000/workflow/api/step_prompts/22/41" \
  -H "Content-Type: application/json" \
  -d '{
    "system_prompt_id": 71,
    "task_prompt_id": 86
  }'

# Expected response: {"success": true}
```

2. Verify Database State
```sql
-- Check prompt configuration was saved
SELECT * FROM workflow_step_prompt 
WHERE step_id = 41 
  AND post_id = 22;

-- Expected: Row with system_prompt_id = 71 and task_prompt_id = 86
```

3. Common Issues
- Permission errors: Check table ownership (all tables must be owned by same user)
- Invalid prompt IDs: Verify IDs exist in `llm_prompt` table
- Missing step ID: Confirm step exists in `workflow_step_entity`
- Missing post ID: Verify post exists in database

### Test Data Reference
- Post ID: 22 (Scottish Culture article)
- Step ID: 41 (Initial Concept)
- System Prompt ID: 71 (Scottish Culture Expert)
- Task Prompt ID: 86 (Basic Idea Expander) 