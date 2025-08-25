# Current System Analysis - Database Schema Documentation

**Date:** 2025-07-17  
**Purpose:** Comprehensive documentation of current database schema for project reorganization  
**Status:** Phase 1, Step 1 - Database Schema Documentation  

---

## Database Overview

The blog system uses PostgreSQL with direct SQL (no SQLAlchemy ORM). The schema is designed around content management, LLM integration, workflow tracking, and media handling.

**Database Connection:** Direct PostgreSQL connection via `app/db.py`  
**Schema Management:** Via `create_tables.sql` and direct SQL migrations  
**Backup Strategy:** `pg_dump` backups stored in `/backups/` directory  

---

## Core Tables by Functional Area

### 1. Content Management Tables

#### `post` - Main Post Table
**Purpose:** Stores blog post metadata and basic information  
**Used by:** All stages (planning, writing, structuring, images, publishing)  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| title | VARCHAR(200) | Post title | All |
| slug | VARCHAR(200) | URL slug (unique) | All |
| summary | TEXT | Post summary | All |
| created_at | TIMESTAMP | Creation timestamp | All |
| updated_at | TIMESTAMP | Last update timestamp | All |
| header_image_id | INTEGER | Reference to image(id) | Images, Publishing |
| status | post_status ENUM | Draft/in_process/published/archived | All |
| substage_id | INTEGER | Current substage | Workflow |

**Foreign Keys:**
- `header_image_id` → `image(id)`

**New Project Assignment:**
- **blog-core:** Database connection and basic CRUD operations
- **blog-planning:** Post creation and basic metadata
- **blog-writing:** Post content and section management
- **blog-structuring:** Post finalization and metadata
- **blog-images:** Header image management
- **blog-publishing:** Post status and publishing workflow

---

#### `post_development` - Planning Stage Data
**Purpose:** Stores all planning stage data and article-wide fields  
**Used by:** Planning stage (purple module)  
**Primary Key:** `id` (SERIAL)  
**Unique Constraint:** `post_id` (one-to-one with post)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | Planning |
| post_id | INTEGER | Reference to post(id) | Planning |
| basic_idea | TEXT | Initial idea description | Planning |
| idea_seed | TEXT | Core concept seed | Planning |
| summary | TEXT | Article summary | Planning, Structuring |
| provisional_title | TEXT | Working title | Planning |
| idea_scope | TEXT | Scope definition | Planning |
| topics_to_cover | TEXT | Topics to include | Planning |
| interesting_facts | TEXT | Key facts to include | Planning |
| tartans_products | TEXT | Product references | Planning |
| section_planning | TEXT | Section planning notes | Planning |
| section_headings | TEXT | Master section headings (JSON) | Planning, Writing |
| section_order | TEXT | Section ordering | Planning, Writing |
| main_title | TEXT | Final title | Structuring |
| subtitle | TEXT | Article subtitle | Structuring |
| intro_blurb | TEXT | Introduction text | Structuring |
| conclusion | TEXT | Conclusion text | Structuring |
| basic_metadata | TEXT | Basic metadata | Structuring |
| tags | TEXT | Article tags | Structuring |
| categories | TEXT | Article categories | Structuring |
| image_captions | TEXT | Image captions | Images |
| seo_optimization | TEXT | SEO optimization | Publishing |
| self_review | TEXT | Self-review notes | Publishing |
| peer_review | TEXT | Peer review notes | Publishing |
| final_check | TEXT | Final check notes | Publishing |
| scheduling | TEXT | Publishing schedule | Publishing |
| deployment | TEXT | Deployment notes | Publishing |
| verification | TEXT | Verification notes | Publishing |
| feedback_collection | TEXT | Feedback collection | Publishing |
| content_updates | TEXT | Content update notes | Publishing |
| version_control | TEXT | Version control notes | Publishing |
| platform_selection | TEXT | Platform selection | Publishing |
| content_adaptation | TEXT | Content adaptation | Publishing |
| distribution | TEXT | Distribution notes | Publishing |
| engagement_tracking | TEXT | Engagement tracking | Publishing |

**Foreign Keys:**
- `post_id` → `post(id)` (UNIQUE)

**New Project Assignment:**
- **blog-planning:** All planning-related fields (basic_idea through section_order)
- **blog-structuring:** Structuring fields (main_title through basic_metadata)
- **blog-images:** Image-related fields (image_captions)
- **blog-publishing:** Publishing fields (seo_optimization through engagement_tracking)

---

#### `post_section` - Writing Stage Data
**Purpose:** Stores individual section content and metadata  
**Used by:** Writing stage (green sections)  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | Writing |
| post_id | INTEGER | Reference to post(id) | Writing |
| section_order | INTEGER | Section position | Writing |
| section_heading | TEXT | Section heading | Writing |
| section_description | TEXT | Section description | Writing |
| ideas_to_include | TEXT | Ideas for this section | Writing |
| facts_to_include | TEXT | Facts for this section | Writing |
| first_draft | TEXT | Initial draft content | Writing |
| uk_british | TEXT | UK British version | Writing |
| highlighting | TEXT | Key points to highlight | Writing |
| image_concepts | TEXT | Image concepts | Writing, Images |
| image_prompts | TEXT | Image generation prompts | Writing, Images |
| generation | TEXT | Content generation notes | Writing |
| optimization | TEXT | Content optimization | Writing |
| watermarking | TEXT | Image watermarking | Images |
| image_meta_descriptions | TEXT | Image metadata | Images |
| image_captions | TEXT | Image captions | Images |
| image_prompt_example_id | INTEGER | Reference to image_prompt_example(id) | Images |
| generated_image_url | VARCHAR(512) | Generated image URL | Images |
| image_generation_metadata | JSONB | Image generation metadata | Images |
| image_id | INTEGER | Reference to image(id) | Images |

**Foreign Keys:**
- `post_id` → `post(id)`
- `image_prompt_example_id` → `image_prompt_example(id)`
- `image_id` → `image(id)`

**Constraints:**
- `UNIQUE(post_id, section_order)` - Ensures no duplicate positions

**New Project Assignment:**
- **blog-writing:** All content fields (section_heading through optimization)
- **blog-images:** All image-related fields (image_concepts through image_id)

---

### 2. Workflow Management Tables

#### `workflow` - Main Workflow Tracking
**Purpose:** Tracks current stage and status for each post  
**Used by:** All stages  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| post_id | INTEGER | Reference to post(id) | All |
| stage_id | INTEGER | Reference to workflow_stage_entity(id) | All |
| status | workflow_status_enum | Draft/published/review/deleted | All |
| created | TIMESTAMP | Creation timestamp | All |
| updated | TIMESTAMP | Last update timestamp | All |

**Foreign Keys:**
- `post_id` → `post(id)` (UNIQUE)
- `stage_id` → `workflow_stage_entity(id)`

**New Project Assignment:**
- **blog-core:** Database operations and status tracking
- **All projects:** Read access for workflow state

---

#### `workflow_stage_entity` - Stage Definitions
**Purpose:** Canonical list of workflow stages  
**Used by:** All stages  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| name | VARCHAR(100) | Stage name (unique) | All |
| description | TEXT | Stage description | All |
| stage_order | INTEGER | Stage ordering | All |

**New Project Assignment:**
- **blog-core:** Stage definitions and ordering

---

#### `workflow_sub_stage_entity` - Sub-Stage Definitions
**Purpose:** Sub-stages within each main stage  
**Used by:** All stages  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| stage_id | INTEGER | Reference to workflow_stage_entity(id) | All |
| name | VARCHAR(100) | Sub-stage name | All |
| description | TEXT | Sub-stage description | All |
| sub_stage_order | INTEGER | Sub-stage ordering | All |

**Foreign Keys:**
- `stage_id` → `workflow_stage_entity(id)`

**New Project Assignment:**
- **blog-core:** Sub-stage definitions and ordering

---

#### `workflow_step_entity` - Step Definitions
**Purpose:** Individual steps within sub-stages  
**Used by:** All stages  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| sub_stage_id | INTEGER | Reference to workflow_sub_stage_entity(id) | All |
| name | VARCHAR(100) | Step name | All |
| description | TEXT | Step description | All |
| step_order | INTEGER | Step ordering | All |
| config | JSONB | Input/output field mappings | All |

**Foreign Keys:**
- `sub_stage_id` → `workflow_sub_stage_entity(id)`

**New Project Assignment:**
- **blog-core:** Step definitions and configuration

---

#### `post_workflow_stage` - Stage Progress Tracking
**Purpose:** Tracks progress through each stage for a post  
**Used by:** All stages  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| post_id | INTEGER | Reference to post(id) | All |
| stage_id | INTEGER | Reference to workflow_stage_entity(id) | All |
| started_at | TIMESTAMP | When stage started | All |
| completed_at | TIMESTAMP | When stage completed | All |
| status | VARCHAR(32) | Stage status | All |
| input_field | VARCHAR(128) | Selected input field | All |
| output_field | VARCHAR(128) | Selected output field | All |

**Foreign Keys:**
- `post_id` → `post(id)`
- `stage_id` → `workflow_stage_entity(id)`

**Constraints:**
- `UNIQUE(post_id, stage_id)` - One record per stage per post

**New Project Assignment:**
- **blog-core:** Progress tracking and field persistence
- **All projects:** Read/write access for stage progress

---

#### `post_workflow_sub_stage` - Sub-Stage Progress Tracking
**Purpose:** Tracks progress through sub-stages  
**Used by:** All stages  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| post_workflow_stage_id | INTEGER | Reference to post_workflow_stage(id) | All |
| sub_stage_id | INTEGER | Reference to workflow_sub_stage_entity(id) | All |
| content | TEXT | Sub-stage content | All |
| status | VARCHAR(32) | Sub-stage status | All |
| started_at | TIMESTAMP | When sub-stage started | All |
| completed_at | TIMESTAMP | When sub-stage completed | All |
| notes | TEXT | Sub-stage notes | All |

**Foreign Keys:**
- `post_workflow_stage_id` → `post_workflow_stage(id)`
- `sub_stage_id` → `workflow_sub_stage_entity(id)`

**Constraints:**
- `UNIQUE(post_workflow_stage_id, sub_stage_id)` - One record per sub-stage per stage

**New Project Assignment:**
- **blog-core:** Sub-stage progress tracking
- **All projects:** Read/write access for sub-stage progress

---

### 3. LLM Integration Tables

#### `llm_action` - LLM Action Templates
**Purpose:** Stores LLM prompt templates and configuration  
**Used by:** All stages  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| field_name | VARCHAR(128) | Target field name | All |
| prompt_template | TEXT | Prompt template text | All |
| prompt_template_id | INTEGER | Reference to llm_prompt(id) | All |
| llm_model | VARCHAR(128) | LLM model name | All |
| provider_id | INTEGER | Reference to llm_provider(id) | All |
| temperature | FLOAT | Temperature setting | All |
| max_tokens | INTEGER | Max tokens setting | All |
| timeout | INTEGER | Request timeout | All |
| order | INTEGER | Action ordering | All |
| input_field | VARCHAR(128) | Input field name | All |
| output_field | VARCHAR(128) | Output field name | All |
| created_at | TIMESTAMP | Creation timestamp | All |
| updated_at | TIMESTAMP | Last update timestamp | All |

**Foreign Keys:**
- `prompt_template_id` → `llm_prompt(id)`
- `provider_id` → `llm_provider(id)`

**New Project Assignment:**
- **blog-core:** LLM action definitions and configuration
- **All projects:** Read access for LLM actions

---

#### `llm_prompt` - Prompt Templates
**Purpose:** Stores prompt templates and configuration  
**Used by:** All stages  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| name | VARCHAR(100) | Prompt name | All |
| description | TEXT | Prompt description | All |
| prompt_text | TEXT | Prompt template text | All |
| prompt_json | JSONB | Structured prompt parts | All |
| system_prompt | TEXT | System prompt | All |
| parameters | JSONB | Prompt parameters | All |
| order | INTEGER | Prompt ordering | All |
| created_at | TIMESTAMP | Creation timestamp | All |
| updated_at | TIMESTAMP | Last update timestamp | All |

**New Project Assignment:**
- **blog-core:** Prompt template definitions
- **All projects:** Read access for prompts

---

#### `llm_interaction` - LLM Interaction History
**Purpose:** Tracks LLM interactions and responses  
**Used by:** All stages  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| prompt_id | INTEGER | Reference to llm_prompt(id) | All |
| input_text | TEXT | Input text | All |
| output_text | TEXT | Output text | All |
| parameters_used | JSONB | Parameters used | All |
| interaction_metadata | JSONB | Interaction metadata | All |
| created_at | TIMESTAMP | Creation timestamp | All |

**Foreign Keys:**
- `prompt_id` → `llm_prompt(id)`

**New Project Assignment:**
- **blog-core:** Interaction history and logging
- **All projects:** Write access for logging interactions

---

#### `llm_action_history` - Action History
**Purpose:** Tracks LLM action execution history  
**Used by:** All stages  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| action_id | INTEGER | Reference to llm_action(id) | All |
| post_id | INTEGER | Reference to post(id) | All |
| input_text | TEXT | Input text | All |
| output_text | TEXT | Output text | All |
| status | VARCHAR(50) | Execution status | All |
| error_message | TEXT | Error message if failed | All |
| created_at | TIMESTAMP | Creation timestamp | All |

**Foreign Keys:**
- `action_id` → `llm_action(id)`
- `post_id` → `post(id)`

**New Project Assignment:**
- **blog-core:** Action history and logging
- **All projects:** Write access for logging actions

---

#### `llm_provider` - LLM Provider Registry
**Purpose:** Stores LLM provider configurations  
**Used by:** All stages  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| name | VARCHAR(128) | Provider name | All |
| type | provider_type_enum | Provider type (openai/ollama/other) | All |
| api_url | TEXT | API endpoint URL | All |
| auth_token | TEXT | Authentication token | All |
| description | TEXT | Provider description | All |
| created_at | TIMESTAMP | Creation timestamp | All |
| updated_at | TIMESTAMP | Last update timestamp | All |

**New Project Assignment:**
- **blog-core:** Provider configurations
- **All projects:** Read access for provider settings

---

#### `llm_model` - LLM Model Registry
**Purpose:** Stores LLM model configurations  
**Used by:** All stages  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| name | VARCHAR(128) | Model name | All |
| provider_id | INTEGER | Reference to llm_provider(id) | All |
| description | TEXT | Model description | All |
| strengths | TEXT | Model strengths | All |
| weaknesses | TEXT | Model weaknesses | All |
| api_params | JSONB | API parameters | All |
| created_at | TIMESTAMP | Creation timestamp | All |
| updated_at | TIMESTAMP | Last update timestamp | All |

**Foreign Keys:**
- `provider_id` → `llm_provider(id)`

**Constraints:**
- `UNIQUE(provider_id, name)` - Unique model per provider

**New Project Assignment:**
- **blog-core:** Model configurations
- **All projects:** Read access for model settings

---

### 4. Image Management Tables

#### `image` - Main Image Table
**Purpose:** Stores image metadata and file information  
**Used by:** Images stage  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | Images |
| filename | VARCHAR(255) | System filename | Images |
| original_filename | VARCHAR(255) | Original filename | Images |
| path | VARCHAR(255) | File path (unique) | Images |
| alt_text | VARCHAR(255) | Alt text | Images |
| caption | TEXT | Image caption | Images |
| image_prompt | TEXT | Generation prompt | Images |
| notes | TEXT | Image notes | Images |
| image_metadata | JSONB | Image metadata | Images |
| watermarked | BOOLEAN | Watermark status | Images |
| watermarked_path | VARCHAR(255) | Watermarked file path | Images |
| created_at | TIMESTAMP | Creation timestamp | Images |
| updated_at | TIMESTAMP | Last update timestamp | Images |

**New Project Assignment:**
- **blog-images:** All image management operations

---

#### `image_style` - Image Styles
**Purpose:** Predefined image styles for generation  
**Used by:** Images stage  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | Images |
| title | VARCHAR(100) | Style title (unique) | Images |
| description | TEXT | Style description | Images |
| created_at | TIMESTAMP | Creation timestamp | Images |
| updated_at | TIMESTAMP | Last update timestamp | Images |

**New Project Assignment:**
- **blog-images:** Style definitions and management

---

#### `image_format` - Image Formats
**Purpose:** Supported image output formats  
**Used by:** Images stage  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | Images |
| title | VARCHAR(100) | Format title (unique) | Images |
| description | VARCHAR(255) | Format description | Images |
| width | INTEGER | Image width | Images |
| height | INTEGER | Image height | Images |
| steps | INTEGER | Generation steps | Images |
| guidance_scale | FLOAT | Guidance scale | Images |
| extra_settings | TEXT | Additional settings | Images |
| created_at | TIMESTAMP | Creation timestamp | Images |
| updated_at | TIMESTAMP | Last update timestamp | Images |

**New Project Assignment:**
- **blog-images:** Format definitions and management

---

#### `image_setting` - Image Settings
**Purpose:** Global image processing settings  
**Used by:** Images stage  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | Images |
| name | VARCHAR(100) | Setting name (unique) | Images |
| style_id | INTEGER | Reference to image_style(id) | Images |
| format_id | INTEGER | Reference to image_format(id) | Images |
| width | INTEGER | Image width | Images |
| height | INTEGER | Image height | Images |
| steps | INTEGER | Generation steps | Images |
| guidance_scale | FLOAT | Guidance scale | Images |
| extra_settings | TEXT | Additional settings | Images |
| created_at | TIMESTAMP | Creation timestamp | Images |
| updated_at | TIMESTAMP | Last update timestamp | Images |

**Foreign Keys:**
- `style_id` → `image_style(id)`
- `format_id` → `image_format(id)`

**New Project Assignment:**
- **blog-images:** Setting definitions and management

---

#### `image_prompt_example` - Prompt Examples
**Purpose:** Example prompts for different content types  
**Used by:** Images stage  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | Images |
| description | TEXT | Example description | Images |
| style_id | INTEGER | Reference to image_style(id) | Images |
| format_id | INTEGER | Reference to image_format(id) | Images |
| provider | VARCHAR(50) | Image provider | Images |
| image_setting_id | INTEGER | Reference to image_setting(id) | Images |
| created_at | TIMESTAMP | Creation timestamp | Images |
| updated_at | TIMESTAMP | Last update timestamp | Images |

**Foreign Keys:**
- `style_id` → `image_style(id)`
- `format_id` → `image_format(id)`
- `image_setting_id` → `image_setting(id)`

**New Project Assignment:**
- **blog-images:** Prompt example definitions

---

### 5. Organization Tables

#### `category` - Categories
**Purpose:** Post categories for organization  
**Used by:** All stages  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| name | VARCHAR(50) | Category name (unique) | All |
| slug | VARCHAR(50) | Category slug (unique) | All |
| description | TEXT | Category description | All |

**New Project Assignment:**
- **blog-core:** Category definitions
- **All projects:** Read access for categories

---

#### `tag` - Tags
**Purpose:** Post tags for organization  
**Used by:** All stages  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| name | VARCHAR(50) | Tag name (unique) | All |
| slug | VARCHAR(50) | Tag slug (unique) | All |
| description | TEXT | Tag description | All |

**New Project Assignment:**
- **blog-core:** Tag definitions
- **All projects:** Read access for tags

---

#### `post_categories` - Post-Category Relationships
**Purpose:** Many-to-many relationship between posts and categories  
**Used by:** All stages  
**Primary Key:** `(post_id, category_id)`  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| post_id | INTEGER | Reference to post(id) | All |
| category_id | INTEGER | Reference to category(id) | All |

**Foreign Keys:**
- `post_id` → `post(id)` ON DELETE CASCADE
- `category_id` → `category(id)` ON DELETE CASCADE

**New Project Assignment:**
- **blog-core:** Relationship management
- **All projects:** Read/write access for post categorization

---

#### `post_tags` - Post-Tag Relationships
**Purpose:** Many-to-many relationship between posts and tags  
**Used by:** All stages  
**Primary Key:** `(post_id, tag_id)`  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| post_id | INTEGER | Reference to post(id) | All |
| tag_id | INTEGER | Reference to tag(id) | All |

**Foreign Keys:**
- `post_id` → `post(id)` ON DELETE CASCADE
- `tag_id` → `tag(id)` ON DELETE CASCADE

**New Project Assignment:**
- **blog-core:** Relationship management
- **All projects:** Read/write access for post tagging

---

### 6. Workflow Action Tables

#### `post_workflow_step_action` - Step Action Settings
**Purpose:** Tracks LLM action button settings for each post and workflow step  
**Used by:** All stages  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| post_id | INTEGER | Reference to post(id) | All |
| step_id | INTEGER | Reference to workflow_step_entity(id) | All |
| action_id | INTEGER | Reference to llm_action(id) | All |
| input_field | VARCHAR(128) | Selected input field | All |
| output_field | VARCHAR(128) | Selected output field | All |
| button_label | TEXT | Button label | All |
| button_order | INTEGER | Button ordering | All |

**Foreign Keys:**
- `post_id` → `post(id)` ON DELETE CASCADE
- `step_id` → `workflow_step_entity(id)`
- `action_id` → `llm_action(id)`

**New Project Assignment:**
- **blog-core:** Action button configuration
- **All projects:** Read/write access for action settings

---

#### `post_substage_action` - Sub-Stage Action Settings
**Purpose:** Defines available LLM actions per post and substage  
**Used by:** All stages  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| post_id | INTEGER | Reference to post(id) | All |
| substage | VARCHAR(64) | Sub-stage name | All |
| action_id | INTEGER | Reference to llm_action(id) | All |
| input_field | VARCHAR(128) | Input field name | All |
| output_field | VARCHAR(128) | Output field name | All |
| button_label | TEXT | Button label | All |
| button_order | INTEGER | Button ordering | All |

**Foreign Keys:**
- `post_id` → `post(id)` ON DELETE CASCADE
- `action_id` → `llm_action(id)`

**New Project Assignment:**
- **blog-core:** Sub-stage action configuration
- **All projects:** Read/write access for action settings

---

#### `substage_action_default` - Default Actions
**Purpose:** Default action per substage (location-specific, post-agnostic)  
**Used by:** All stages  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| substage | VARCHAR(64) | Sub-stage name (unique) | All |
| action_id | INTEGER | Reference to llm_action(id) | All |

**Foreign Keys:**
- `action_id` → `llm_action(id)`

**New Project Assignment:**
- **blog-core:** Default action definitions
- **All projects:** Read access for default actions

---

#### `workflow_field_mapping` - Field Mappings
**Purpose:** Maps post development fields to workflow stages and substages  
**Used by:** All stages  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | All |
| field_name | TEXT | Field name | All |
| stage_id | INTEGER | Reference to workflow_stage_entity(id) | All |
| substage_id | INTEGER | Reference to workflow_sub_stage_entity(id) | All |
| order_index | INTEGER | Field ordering | All |

**Foreign Keys:**
- `stage_id` → `workflow_stage_entity(id)`
- `substage_id` → `workflow_sub_stage_entity(id)`

**New Project Assignment:**
- **blog-core:** Field mapping definitions
- **All projects:** Read access for field mappings

---

### 7. User Management Tables

#### `user` - User Accounts
**Purpose:** User account information (currently not used)  
**Used by:** None (reserved for future)  
**Primary Key:** `id` (SERIAL)  

| Column | Type | Description | Used by Stage |
|--------|------|-------------|---------------|
| id | SERIAL | Primary key | None |
| username | VARCHAR(64) | Username (unique) | None |
| email | VARCHAR(120) | Email (unique) | None |
| password_hash | VARCHAR(128) | Password hash | None |
| is_active | BOOLEAN | Account status | None |
| created_at | TIMESTAMP | Creation timestamp | None |
| updated_at | TIMESTAMP | Last update timestamp | None |

**New Project Assignment:**
- **blog-core:** User management (future use)

---

## Database Relationships Summary

### Primary Relationships
1. **post** → **post_development** (1:1 via post_id)
2. **post** → **post_section** (1:many via post_id)
3. **post** → **workflow** (1:1 via post_id)
4. **workflow** → **workflow_stage_entity** (many:1 via stage_id)
5. **workflow_stage_entity** → **workflow_sub_stage_entity** (1:many via stage_id)
6. **workflow_sub_stage_entity** → **workflow_step_entity** (1:many via sub_stage_id)

### LLM Relationships
1. **llm_action** → **llm_prompt** (many:1 via prompt_template_id)
2. **llm_action** → **llm_provider** (many:1 via provider_id)
3. **llm_interaction** → **llm_prompt** (many:1 via prompt_id)
4. **llm_action_history** → **llm_action** (many:1 via action_id)
5. **llm_action_history** → **post** (many:1 via post_id)

### Image Relationships
1. **post** → **image** (many:1 via header_image_id)
2. **post_section** → **image** (many:1 via image_id)
3. **post_section** → **image_prompt_example** (many:1 via image_prompt_example_id)
4. **image_setting** → **image_style** (many:1 via style_id)
5. **image_setting** → **image_format** (many:1 via format_id)
6. **image_prompt_example** → **image_style** (many:1 via style_id)
7. **image_prompt_example** → **image_format** (many:1 via format_id)
8. **image_prompt_example** → **image_setting** (many:1 via image_setting_id)

### Organization Relationships
1. **post** → **category** (many:many via post_categories)
2. **post** → **tag** (many:many via post_tags)

---

## New Project Table Assignments

### blog-core
**Primary Responsibility:** Shared infrastructure and database access
**Tables:**
- All workflow definition tables (workflow_stage_entity, workflow_sub_stage_entity, workflow_step_entity)
- All LLM configuration tables (llm_action, llm_prompt, llm_provider, llm_model)
- All organization tables (category, tag, post_categories, post_tags)
- User management (user)
- Workflow action configuration (post_workflow_step_action, post_substage_action, substage_action_default, workflow_field_mapping)

### blog-planning
**Primary Responsibility:** Planning stage functionality
**Tables:**
- post (read/write for planning operations)
- post_development (primary data store)
- workflow (read/write for stage tracking)
- post_workflow_stage (read/write for stage progress)
- post_workflow_sub_stage (read/write for sub-stage progress)
- llm_interaction (write for logging)
- llm_action_history (write for logging)

### blog-writing
**Primary Responsibility:** Writing stage functionality
**Tables:**
- post (read/write for writing operations)
- post_section (primary data store)
- workflow (read/write for stage tracking)
- post_workflow_stage (read/write for stage progress)
- post_workflow_sub_stage (read/write for sub-stage progress)
- llm_interaction (write for logging)
- llm_action_history (write for logging)

### blog-structuring
**Primary Responsibility:** Structuring stage functionality
**Tables:**
- post (read/write for structuring operations)
- post_development (read/write for structuring fields)
- workflow (read/write for stage tracking)
- post_workflow_stage (read/write for stage progress)
- post_workflow_sub_stage (read/write for sub-stage progress)
- llm_interaction (write for logging)
- llm_action_history (write for logging)

### blog-images
**Primary Responsibility:** Image generation and management
**Tables:**
- post (read for post context)
- post_section (read/write for image-related fields)
- post_development (read/write for image-related fields)
- image (primary data store)
- image_style (read/write)
- image_format (read/write)
- image_setting (read/write)
- image_prompt_example (read/write)
- workflow (read/write for stage tracking)
- post_workflow_stage (read/write for stage progress)
- post_workflow_sub_stage (read/write for sub-stage progress)
- llm_interaction (write for logging)
- llm_action_history (write for logging)

### blog-publishing
**Primary Responsibility:** Publishing and syndication
**Tables:**
- post (read/write for publishing operations)
- post_development (read/write for publishing fields)
- workflow (read/write for stage tracking)
- post_workflow_stage (read/write for stage progress)
- post_workflow_sub_stage (read/write for sub-stage progress)
- llm_interaction (write for logging)
- llm_action_history (write for logging)

---

## Migration Considerations

### Shared Database Access
- All projects will connect to the same PostgreSQL database
- Each project will have read access to all tables
- Write access will be restricted to project-specific tables
- Database connection utilities will be shared via blog-core

### Data Integrity
- Foreign key constraints must be maintained across projects
- Transaction management will be handled at the application level
- Backup and restore procedures must account for all tables

### Performance Considerations
- Database connection pooling will be shared
- Indexes must be maintained for cross-project queries
- Query optimization may be needed for complex joins

---

**Status:** Step 1 Complete - Database schema documentation created  
**Next Step:** Step 2 - Code Inventory and Dependencies

---

## Configuration Analysis

### Environment Variables

#### Database Configuration
- **DATABASE_URL:** `postgresql://nickfiddes@localhost:5432/blog` (from assistant_config.env)
- **DB_NAME:** Database name (parsed from DATABASE_URL)
- **DB_USER:** Database user (parsed from DATABASE_URL)
- **DB_PASSWORD:** Database password (parsed from DATABASE_URL)
- **DB_HOST:** Database host (parsed from DATABASE_URL)
- **DB_PORT:** Database port (parsed from DATABASE_URL)

#### Flask Configuration
- **SECRET_KEY:** Flask secret key (default: "hard-to-guess-string")
- **FLASK_ENV:** Flask environment (default: "default")
- **DEBUG:** Debug mode (True for development)

#### LLM Configuration
- **OLLAMA_API_URL:** Ollama API URL (default: "http://localhost:11434")
- **DEFAULT_LLM_MODEL:** Default LLM model (default: "llama3.1:70b")
- **COMPLETION_SERVICE_TOKEN:** Completion service token
- **OPENAI_AUTH_TOKEN:** OpenAI authentication token
- **OPENAI_ORG_ID:** OpenAI organization ID
- **OPENAI_API_BASE:** OpenAI API base URL (default: "https://api.openai.com/v1")
- **OPENAI_DEFAULT_MODEL:** OpenAI default model (default: "gpt-3.5-turbo")
- **OPENAI_EMBEDDING_MODEL:** OpenAI embedding model (default: "text-embedding-3-small")

#### Email Configuration
- **MAIL_SERVER:** Mail server
- **MAIL_PORT:** Mail port (default: 25)
- **MAIL_USE_TLS:** Use TLS for email
- **MAIL_USERNAME:** Mail username
- **MAIL_PASSWORD:** Mail password
- **MAIL_DEFAULT_SENDER:** Default email sender
- **ADMIN_EMAIL:** Admin email address

#### Cache Configuration
- **CACHE_TYPE:** Cache type (default: "simple", "redis" for production)
- **CACHE_DEFAULT_TIMEOUT:** Cache timeout (default: 300)

#### Celery Configuration
- **CELERY_BROKER_URL:** Celery broker URL (default: "redis://localhost:6379/0")
- **CELERY_RESULT_BACKEND:** Celery result backend (default: "redis://localhost:6379/0")

#### Upload Configuration
- **MAX_CONTENT_LENGTH:** Maximum upload size (16MB)
- **UPLOAD_FOLDER:** Upload folder path
- **ALLOWED_EXTENSIONS:** Allowed file extensions

#### TinyMCE Configuration
- **TINYMCE_API_KEY:** TinyMCE API key

### Configuration Files

#### `config.py` - Main Configuration
**Purpose:** Central configuration management
**Used by:** All stages
**Dependencies:**
- os
- dotenv
- re (for DATABASE_URL parsing)

**Configuration Classes:**
- **Config:** Base configuration class
- **DevelopmentConfig:** Development-specific configuration
- **ProductionConfig:** Production-specific configuration

**New Project Assignment:**
- **blog-core:** Central configuration management

#### `assistant_config.env` - Database Configuration
**Purpose:** Database connection configuration
**Used by:** All stages
**Content:** DATABASE_URL for PostgreSQL connection

**New Project Assignment:**
- **blog-core:** Database configuration

#### `.env` - General Environment Variables
**Purpose:** General environment variables (if present)
**Used by:** All stages
**Content:** Various environment variables

**New Project Assignment:**
- **blog-core:** Environment variable management

### Configuration Loading Patterns

#### Current Pattern
**Issue:** Multiple files load environment variables independently
**Files with this pattern:**
- `app/main/routes.py`
- `app/blog/routes.py`
- `app/database/routes.py`
- `app/llm/routes.py`

**Problem:** Inconsistent environment variable loading
**Solution:** Centralize in `config.py` and use Flask config

#### Database Connection Pattern
**Issue:** Multiple files implement their own `get_db_conn()` function
**Files with this pattern:**
- `app/main/routes.py`
- `app/blog/routes.py`
- `app/database/routes.py`
- `app/llm/routes.py`

**Problem:** Code duplication and potential inconsistency
**Solution:** Centralize in `app/db.py` and import from there

### Configuration by Project

#### blog-core
**Required Configuration:**
- Database connection (DATABASE_URL)
- Flask configuration (SECRET_KEY, DEBUG, etc.)
- LLM configuration (OLLAMA_API_URL, DEFAULT_LLM_MODEL)
- Cache configuration (CACHE_TYPE, CACHE_DEFAULT_TIMEOUT)
- Celery configuration (CELERY_BROKER_URL, CELERY_RESULT_BACKEND)
- Upload configuration (MAX_CONTENT_LENGTH, UPLOAD_FOLDER)

#### blog-planning
**Required Configuration:**
- All blog-core configuration
- Planning-specific settings (if any)

#### blog-writing
**Required Configuration:**
- All blog-core configuration
- Writing-specific settings (if any)

#### blog-structuring
**Required Configuration:**
- All blog-core configuration
- Structuring-specific settings (if any)

#### blog-images
**Required Configuration:**
- All blog-core configuration
- Image processing settings
- Image generation API keys (if external services)

#### blog-publishing
**Required Configuration:**
- All blog-core configuration
- Publishing API keys (clan.com, social media)
- Publishing-specific settings

### Configuration Migration Strategy

#### Phase 1: Centralization
1. **Extract all configuration** to `blog-core`
2. **Standardize configuration loading** in `config.py`
3. **Remove duplicate configuration** from other files
4. **Test configuration loading** across all projects

#### Phase 2: Project-Specific Configuration
1. **Create project-specific config files** for each project
2. **Inherit from blog-core configuration**
3. **Add project-specific settings**
4. **Test configuration isolation**

#### Phase 3: Environment-Specific Configuration
1. **Create environment-specific config files**
2. **Implement configuration validation**
3. **Add configuration documentation**
4. **Test configuration in all environments**

### Configuration Security

#### Sensitive Information
**Current:** Some sensitive information in environment variables
**Future:** Use secure configuration management
**Implementation:** Environment variables for sensitive data

#### Configuration Validation
**Current:** Basic validation
**Future:** Comprehensive validation
**Implementation:** Marshmallow schemas for configuration validation

---

**Status:** Step 3 Complete - Configuration analysis documented  
**Next Step:** Step 4 - Testing Infrastructure 