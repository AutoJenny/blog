# Workflow Prompts Guide
 
## Overview
This guide documents the workflow prompt system, including system prompts and task prompts for each workflow stage.
 
## Prompt Types

### 1. System Prompts
System prompts provide the base context and instructions for the LLM. They are not tied to specific workflow stages.

Example system prompt:
```
You are a helpful assistant focused on blog post development. You help authors:
1. Develop and refine ideas
2. Structure content effectively
3. Write engaging copy
4. Optimize for SEO
```

### 2. Task Prompts
Task prompts are specific to workflow stages and steps. They guide the LLM in performing specific tasks.

Example task prompt for "Initial Concept" step:
```
Given the idea seed: [data:idea_seed]

Generate a clear, concise basic idea for a blog post that:
1. Captures the core concept
2. Identifies the target audience
3. Outlines the value proposition
4. Suggests potential angles

Keep the response focused and actionable.
```

## Prompt Management

### Creating Prompts
1. System Prompts:
   ```bash
   curl -s -X POST "http://localhost:5000/settings/workflow_prompts" \
     -F "prompt_type=system" \
     -F "name=Base Context" \
     -F "prompt_text=You are a helpful assistant..."
   ```

2. Task Prompts:
   ```bash
   curl -s -X POST "http://localhost:5000/settings/workflow_prompts" \
     -F "prompt_type=task" \
     -F "stage=planning" \
     -F "substage=idea" \
     -F "step=Initial Concept" \
     -F "name=Generate Basic Idea" \
     -F "prompt_text=Given the idea seed..."
   ```

### Updating Prompts
```bash
curl -s -X POST "http://localhost:5000/settings/workflow_prompts" \
  -F "prompt_id=1" \
  -F "name=Updated Name" \
  -F "prompt_text=Updated text..."
```

### Deleting Prompts
```bash
curl -s -X POST "http://localhost:5000/settings/workflow_prompts" \
  -F "prompt_id=1" \
  -F "delete=true"
```

## Prompt Structure

### System Prompts
- Focus on general capabilities and context
- Define the assistant's role and expertise
- Set overall tone and style
- Establish constraints and guidelines

### Task Prompts
- Use [data:field_name] syntax for dynamic data
- Include clear instructions and expectations
- Specify desired output format
- Provide evaluation criteria

## Stage-Specific Prompts

### 1. Planning Stage

#### Idea Substage
1. Initial Concept
   ```
   Given the idea seed: [data:idea_seed]
   Generate a basic idea that...
   ```

2. Basic Idea
   ```
   Based on the initial concept: [data:basic_idea]
   Refine and expand the idea by...
   ```

3. Provisional Title
   ```
   Using the basic idea: [data:basic_idea]
   Generate an engaging title that...
   ```

#### Research Substage
1. Facts
   ```
   For the topic: [data:basic_idea]
   Research and list key facts that...
   ```

2. Concepts
   ```
   Based on the facts: [data:research_facts]
   Identify core concepts that...
   ```

#### Structure Substage
1. Outline
   ```
   Using the facts: [data:research_facts]
   And concepts: [data:research_concepts]
   Create a detailed outline that...
   ```

2. Allocate Facts
   ```
   Given the outline: [data:structure_outline]
   And facts: [data:research_facts]
   Distribute facts across sections...
   ```

### 2. Authoring Stage

#### Content Substage
1. Draft
   ```
   Using the outline: [data:structure_outline]
   And allocated facts: [data:structure_facts]
   Write a draft that...
   ```

2. Review
   ```
   Review the draft: [data:content_draft]
   For clarity, engagement, and...
   ```

#### Meta Info Substage
1. SEO
   ```
   Based on the content: [data:content_draft]
   Generate SEO metadata including...
   ```

2. Social
   ```
   Using the content: [data:content_draft]
   Create social media previews that...
   ```

### 3. Publishing Stage

#### Preflight Substage
1. Review
   ```
   Review all content: [data:content_draft]
   And metadata: [data:meta_info]
   Ensure compliance with...
   ```

2. Validation
   ```
   Validate the post against...
   ```

## Best Practices

1. Data References
   - Always use [data:field_name] syntax
   - Reference only fields available in the current context
   - Verify field names in post_development table

2. Prompt Design
   - Keep instructions clear and specific
   - Include examples where helpful
   - Define expected output format
   - Consider edge cases

3. Context Management
   - Maintain consistent context across stages
   - Pass relevant information forward
   - Avoid redundant instructions

4. Error Handling
   - Provide fallback instructions
   - Handle missing or invalid data
   - Include validation criteria

## Database Schema

### llm_prompt Table
```sql
CREATE TABLE llm_prompt (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    prompt_text TEXT NOT NULL,
    prompt_type VARCHAR(32) NOT NULL,
    stage VARCHAR(32),
    substage VARCHAR(32),
    step VARCHAR(32),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Prompt Types
- system: Base context and instructions
- task: Stage/step specific prompts

### Field References
All [data:field_name] references must correspond to columns in:
```sql
CREATE TABLE post_development (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id),
    idea_seed TEXT,
    basic_idea TEXT,
    provisional_title TEXT,
    research_facts TEXT,
    research_concepts TEXT,
    structure_outline TEXT,
    structure_facts TEXT,
    content_draft TEXT,
    meta_info JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Format Integration

### Overview
The prompt system works in conjunction with the format system (see formats.md) to ensure consistent data structures throughout the workflow. Each prompt can reference both input and output formats.

### Using Formats in Prompts

1. Input Format References
   ```
   Given the input in the following format:
   [format:input]

   Process the data: [data:field_name]
   ```

2. Output Format Requirements
   ```
   Generate output that strictly follows this format:
   [format:output]

   Ensure all required fields are included and properly formatted.
   ```

### Format Validation
- Input data is validated against the input format before processing
- LLM output is validated against the output format
- Failed validations trigger reprocessing with format correction

### Example Prompt with Formats
```
You are a blog post section creator.

Input Format:
[format:input]

Output Format:
[format:output]

Given the section topic: [data:section_topic]
Generate a well-structured section that:
1. Follows the output format exactly
2. Maintains consistent style
3. Integrates smoothly with surrounding content

Ensure all required fields in the output format are included.
```

## Workflow Step Prompt Configuration

### Overview
Each workflow step can have associated system and task prompts that are persisted in the `workflow_step_prompt` table. This configuration determines which prompts are used when the step is processed by the LLM.

### Database Structure
The workflow step prompts are stored in the following tables:
- `workflow_step_prompt`: Links workflow steps to their system and task prompts
- `workflow_step_entity`: Contains the step definitions
- `llm_prompt`: Stores the actual prompt content

### Saving Step Prompts
To save prompt configuration for a workflow step:

```bash
curl -X POST "http://localhost:5000/workflow/api/step_prompts/{post_id}/{step_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "system_prompt_id": 71,  # Example: Scottish Culture Expert
    "task_prompt_id": 86     # Example: Basic Idea Expander
  }'
```

### Table Ownership Requirements
- The `workflow_step_prompt` table must be owned by the same user as the `workflow_step_entity` and `llm_prompt` tables (typically `nickfiddes`)
- If you encounter permission errors, verify table ownership with:
  ```sql
  SELECT tablename, tableowner 
  FROM pg_tables 
  WHERE tablename IN ('workflow_step_prompt', 'workflow_step_entity', 'llm_prompt');
  ```
- To fix ownership issues:
  ```sql
  ALTER TABLE workflow_step_entity OWNER TO nickfiddes;
  ```

### Best Practices
1. Always verify table ownership before making schema changes
2. Test prompt saving with curl before implementing UI changes
3. Include both system and task prompts in configuration
4. Verify prompt IDs exist in `llm_prompt` table before saving 

### Format Configuration
Each workflow step's prompt configuration should include:
1. System prompt
2. Task prompt
3. Input format (optional)
4. Output format (optional)

See formats.md for detailed format configuration instructions. 