# Workflow Database Reference

This document serves as a comprehensive reference for all workflow-related database tables and their fields. Use this document to verify table and column names before writing SQL queries.

## Core Tables

### post
Primary table for blog posts.
- `id`: SERIAL PRIMARY KEY
- Other fields not directly related to workflow

### workflow
Tracks the current stage and status for each post's development.
- `id`: SERIAL PRIMARY KEY
- `post_id`: INTEGER REFERENCES post(id)
- `stage`: ENUM (idea, research, structure, content, meta_information, images, preflight, publishing, syndication)
- `status`: ENUM (draft, published, review, deleted)
- `created`: TIMESTAMP DEFAULT now()
- `updated`: TIMESTAMP DEFAULT now()

## Section Management

### post_section
Manages sections within a post.
- `id`: SERIAL PRIMARY KEY
- `post_id`: INTEGER REFERENCES post(id) NOT NULL
- `section_order`: INTEGER
- `section_heading`: TEXT
- `section_description`: TEXT
- `ideas_to_include`: TEXT
- `facts_to_include`: TEXT
- `first_draft`: TEXT
- `uk_british`: TEXT
- `highlighting`: TEXT
- `image_concepts`: TEXT
- `image_prompts`: TEXT
- `generation`: TEXT
- `optimization`: TEXT
- `watermarking`: TEXT
- `image_meta_descriptions`: TEXT
- `image_captions`: TEXT
- `image_prompt_example_id`: INTEGER
- `generated_image_url`: VARCHAR(512)
- `image_generation_metadata`: JSONB
- `image_id`: INTEGER REFERENCES image(id)

### post_section_elements
Stores individual elements (facts, ideas, themes) within a section.
- `id`: SERIAL PRIMARY KEY
- `post_id`: INTEGER REFERENCES post(id) NOT NULL
- `section_id`: INTEGER REFERENCES post_section(id) NOT NULL
- `element_type`: VARCHAR(50) CHECK (element_type IN ('fact', 'idea', 'theme'))
- `element_text`: TEXT NOT NULL
- `element_order`: INTEGER
- `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- `updated_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

## Workflow Stage Structure

### workflow_stage_entity
Canonical list of main workflow stages.
- `id`: SERIAL PRIMARY KEY
- `name`: VARCHAR(100) NOT NULL
- `description`: TEXT
- `stage_order`: INTEGER NOT NULL

### workflow_sub_stage_entity
Ordered sub-stages for each main stage.
- `id`: SERIAL PRIMARY KEY
- `stage_id`: INTEGER REFERENCES workflow_stage_entity(id)
- `name`: VARCHAR(100) NOT NULL
- `description`: TEXT
- `sub_stage_order`: INTEGER NOT NULL

### workflow_step_entity
Individual steps within each sub-stage.
- `id`: SERIAL PRIMARY KEY
- `sub_stage_id`: INTEGER REFERENCES workflow_sub_stage_entity(id)
- `name`: VARCHAR(100) NOT NULL
- `description`: TEXT
- `step_order`: INTEGER NOT NULL
- `config`: JSONB -- Contains input/output field mappings

## Workflow Progress Tracking

### post_workflow_stage
Tracks the status and timing of each workflow stage for a post.
- `id`: SERIAL PRIMARY KEY
- `post_id`: INTEGER REFERENCES post(id)
- `stage_id`: INTEGER REFERENCES workflow_stage_entity(id)
- `started_at`: TIMESTAMP
- `completed_at`: TIMESTAMP
- `status`: VARCHAR(32)
- `input_field`: VARCHAR(128)
- `output_field`: VARCHAR(128)

### post_workflow_step_action
Tracks LLM action button settings for each post and workflow step.
- `id`: SERIAL PRIMARY KEY
- `post_id`: INTEGER REFERENCES post(id)
- `step_id`: INTEGER REFERENCES workflow_step_entity(id)
- `action_id`: INTEGER REFERENCES llm_action(id)
- `input_field`: VARCHAR(128)
- `output_field`: VARCHAR(128)
- `button_label`: TEXT
- `button_order`: INTEGER DEFAULT 0

### workflow_field_mapping
Maps post development fields to workflow stages and substages.
- `id`: SERIAL PRIMARY KEY
- `field_name`: TEXT
- `stage_id`: INTEGER REFERENCES workflow_stage_entity(id)
- `substage_id`: INTEGER REFERENCES workflow_sub_stage_entity(id)
- `order_index`: INTEGER DEFAULT 0

## Development Data

### post_development
Stores development state for each post.
- `post_id`: INTEGER PRIMARY KEY REFERENCES post(id)
- `outline`: TEXT
- `draft`: TEXT
- `status`: VARCHAR(32)
- `updated_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

## Important Notes

1. Always verify table and column names against this reference before writing SQL queries.
2. All table names are singular (e.g., `post` not `posts`).
3. All foreign keys use the singular form (e.g., `post_id` not `posts_id`).
4. When joining tables, use meaningful aliases (e.g., `p` for post, `ws` for workflow_stage).
5. The workflow system uses a hierarchical structure:
   - Stage (workflow_stage_entity)
   - Sub-stage (workflow_sub_stage_entity)
   - Step (workflow_step_entity)

## Example Queries

### Get Post with Workflow State
```sql
SELECT p.*, 
       w.stage as current_stage,
       w.status as workflow_status
FROM post p
LEFT JOIN workflow w ON w.post_id = p.id
WHERE p.id = :post_id
```

### Get Workflow Progress
```sql
SELECT 
    pws.id,
    ws.name as stage_name,
    pws.status,
    pws.completed_at
FROM post_workflow_stage pws
JOIN workflow_stage_entity ws ON ws.id = pws.stage_id
WHERE pws.post_id = :post_id
ORDER BY pws.completed_at
```

### Get Development State
```sql
SELECT pd.*
FROM post_development pd
WHERE pd.post_id = :post_id
```

### Get Post Sections with Elements
```sql
SELECT 
    s.id,
    s.section_heading,
    s.section_description,
    array_agg(DISTINCT e.element_text) FILTER (WHERE e.element_type = 'fact') as facts,
    array_agg(DISTINCT e.element_text) FILTER (WHERE e.element_type = 'idea') as ideas,
    array_agg(DISTINCT e.element_text) FILTER (WHERE e.element_type = 'theme') as themes
FROM post_section s
LEFT JOIN post_section_elements e ON e.section_id = s.id
WHERE s.post_id = :post_id
GROUP BY s.id, s.section_heading, s.section_description
ORDER BY s.section_order
``` 