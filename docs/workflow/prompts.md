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