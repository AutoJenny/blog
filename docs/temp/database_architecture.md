# Database Architecture Reference

## Overview

The BlogForge CMS uses PostgreSQL as its primary database with 82+ tables organized into logical groups. This document provides a comprehensive reference for the database structure, relationships, and usage patterns.

## Database Groups

### 1. Core Content (12 tables)
**Purpose:** Core content management including posts, sections, and content relationships

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `post` | Main post content | `id`, `title`, `content`, `status`, `created_at` |
| `post_categories` | Post categorization | `post_id`, `category_id` |
| `post_images` | Post-image relationships | `post_id`, `image_id`, `image_type` |
| `post_performance` | Post analytics and metrics | `post_id`, `views`, `engagement_score` |
| `post_section` | Post content sections | `id`, `post_id`, `title`, `content`, `order` |
| `post_section_elements` | Section sub-elements | `section_id`, `element_type`, `content` |
| `post_tags` | Post tagging system | `post_id`, `tag_id` |
| `post_workflow_stage` | Workflow stage tracking | `post_id`, `stage_id`, `status` |
| `post_workflow_step_action` | Workflow step actions | `post_id`, `step_id`, `action_type` |
| `post_workflow_sub_stage` | Workflow sub-stages | `post_id`, `sub_stage_id`, `status` |
| `post_development` | Post development tracking | `post_id`, `development_status`, `notes` |
| `daily_posts` | Daily post scheduling | `date`, `post_id`, `status` |

### 2. Image Management (9 tables)
**Purpose:** Image processing, storage, and optimization

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `image` | Image metadata | `id`, `filename`, `path`, `size`, `format` |
| `image_format` | Supported image formats | `id`, `name`, `extension`, `mime_type` |
| `image_processing_jobs` | Processing job queue | `id`, `image_id`, `status`, `created_at` |
| `image_processing_status` | Job status tracking | `job_id`, `status`, `progress` |
| `image_processing_steps` | Processing pipeline steps | `job_id`, `step_name`, `status` |
| `image_prompt_example` | AI image generation prompts | `id`, `prompt_text`, `category` |
| `image_setting` | Image processing settings | `id`, `setting_name`, `value` |
| `image_style` | Image style definitions | `id`, `name`, `description`, `css_class` |
| `images` | Legacy image table | `id`, `filename`, `path` |
| `section_image_mappings` | Section-image relationships | `section_id`, `image_id`, `position` |

### 3. Workflow System (12 tables)
**Purpose:** Content creation workflow management

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `workflow` | Workflow definitions | `id`, `name`, `description`, `status` |
| `workflow_stage_entity` | Workflow stages | `id`, `workflow_id`, `name`, `order` |
| `workflow_sub_stage_entity` | Workflow sub-stages | `id`, `stage_id`, `name`, `order` |
| `workflow_step_entity` | Workflow steps | `id`, `sub_stage_id`, `name`, `type` |
| `workflow_step_context_config` | Step configuration | `step_id`, `config_key`, `config_value` |
| `workflow_step_input` | Step input definitions | `step_id`, `input_name`, `input_type` |
| `workflow_step_prompt` | AI prompts for steps | `step_id`, `prompt_text`, `prompt_type` |
| `workflow_steps` | Legacy workflow steps | `id`, `name`, `description` |
| `workflow_field_mapping` | Field mapping definitions | `id`, `source_field`, `target_field` |
| `workflow_field_mappings` | Field mapping instances | `mapping_id`, `post_id`, `value` |
| `workflow_format_template` | Output format templates | `id`, `name`, `template_content` |
| `workflow_post_format` | Post-specific formats | `post_id`, `format_id`, `content` |
| `workflow_stage_format` | Stage-specific formats | `stage_id`, `format_id`, `template` |
| `workflow_step_format` | Step-specific formats | `step_id`, `format_id`, `template` |
| `workflow_table_preferences` | User workflow preferences | `user_id`, `preference_key`, `value` |

### 4. LLM & AI (8 tables)
**Purpose:** AI model integration and prompt management

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `llm_action` | AI action definitions | `id`, `name`, `description`, `action_type` |
| `llm_action_history` | Action execution history | `id`, `action_id`, `post_id`, `result` |
| `llm_config` | LLM configuration | `id`, `provider`, `model_name`, `api_key` |
| `llm_format_template` | AI output templates | `id`, `name`, `template_content` |
| `llm_interaction` | AI interaction logs | `id`, `post_id`, `prompt`, `response` |
| `llm_model` | Available AI models | `id`, `provider`, `name`, `capabilities` |
| `llm_prompt` | Prompt templates | `id`, `name`, `prompt_text`, `category` |
| `llm_prompt_part` | Prompt components | `prompt_id`, `part_name`, `content` |
| `llm_provider` | AI service providers | `id`, `name`, `api_endpoint`, `status` |

### 5. Platforms & Syndication (11 tables)
**Purpose:** Social media and content distribution

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `platforms` | Social media platforms | `id`, `name`, `display_name`, `logo_url` |
| `platform_capabilities` | Platform features | `platform_id`, `capability`, `supported` |
| `platform_channel_support` | Channel type support | `platform_id`, `channel_type_id` |
| `platform_credentials` | Platform API credentials | `platform_id`, `credential_type`, `value` |
| `channel_types` | Content channel types | `id`, `name`, `description` |
| `channel_requirements` | Channel-specific requirements | `channel_type_id`, `requirement`, `mandatory` |
| `content_processes` | Content processing workflows | `id`, `platform_id`, `channel_type_id`, `name` |
| `content_priorities` | Content prioritization | `id`, `content_type`, `priority_score` |
| `syndication_progress` | Syndication tracking | `post_id`, `platform_id`, `status`, `progress` |
| `posting_queue` | Content posting queue | `id`, `post_id`, `platform_id`, `scheduled_at` |
| `product_content_templates` | Product content templates | `id`, `platform_id`, `template_content` |
| `process_configurations` | Process configuration | `process_id`, `config_key`, `config_value` |

### 6. Credentials & Security (6 tables)
**Purpose:** API credentials and user management

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `credentials` | API credentials storage | `id`, `service_name`, `credential_type`, `encrypted_value` |
| `active_credentials` | Currently active credentials | `credential_id`, `is_active`, `activated_at` |
| `credential_channels` | Credential-channel associations | `credential_id`, `channel_id` |
| `credential_services` | Credential-service mappings | `credential_id`, `service_id` |
| `credential_usage_history` | Credential usage tracking | `id`, `credential_id`, `used_at`, `action` |
| `user` | User accounts | `id`, `username`, `email`, `password_hash` |

### 7. Clan API Integration (3 tables)
**Purpose:** External product data integration

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `clan_cache_metadata` | Cache management | `id`, `cache_key`, `last_updated`, `expires_at` |
| `clan_categories` | Product categories | `id`, `name`, `description`, `parent_id` |
| `clan_products` | Product information | `id`, `name`, `description`, `price`, `category_id` |

### 8. UI & Configuration (6 tables)
**Purpose:** User interface and system configuration

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `ui_display_rules` | UI display logic | `id`, `rule_name`, `condition`, `action` |
| `ui_menu_items` | Navigation menu items | `id`, `name`, `url`, `parent_id`, `order` |
| `ui_sections` | UI section definitions | `id`, `name`, `template`, `visible` |
| `ui_session_state` | User session state | `session_id`, `state_key`, `state_value` |
| `ui_user_preferences` | User preferences | `user_id`, `preference_key`, `preference_value` |
| `config_categories` | Configuration categories | `id`, `name`, `description` |
| `priority_factors` | Content prioritization factors | `id`, `factor_name`, `weight`, `description` |
| `substage_action_default` | Default sub-stage actions | `sub_stage_id`, `action_type`, `default_value` |

### 9. Categories & Tags (3 tables)
**Purpose:** Content classification and tagging

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `category` | Content categories | `id`, `name`, `description`, `parent_id` |
| `tag` | Content tags | `id`, `name`, `color`, `description` |
| `requirement_categories` | Requirement categories | `id`, `name`, `description` |

### 10. Backup Tables (3 tables)
**Purpose:** Historical data and backups

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `post_development_backup_20250804_080448` | Post development backup | Historical post development data |
| `post_section_backup_20250109` | Post section backup | Historical post section data |
| `workflow_step_entity_backup` | Workflow step backup | Historical workflow step data |

## Key Relationships

### Content Flow
```
post → post_section → post_section_elements
  ↓
post_workflow_stage → post_workflow_sub_stage → post_workflow_step_action
  ↓
syndication_progress → posting_queue
```

### Image Processing
```
image → image_processing_jobs → image_processing_steps
  ↓
section_image_mappings ← post_section
```

### AI Integration
```
llm_interaction → post
  ↓
llm_action_history ← llm_action
```

## Database Management

### Accessing the Database Interface
- **URL:** `http://localhost:5000/db/`
- **Features:**
  - Browse all 82 tables organized by category
  - View table schemas and sample data
  - Execute custom SQL queries
  - Perform database backups and restores
  - Search and filter across tables

### Common Queries

#### Get Post with All Related Data
```sql
SELECT p.*, 
       array_agg(DISTINCT c.name) as categories,
       array_agg(DISTINCT t.name) as tags,
       ws.name as workflow_stage
FROM post p
LEFT JOIN post_categories pc ON p.id = pc.post_id
LEFT JOIN category c ON pc.category_id = c.id
LEFT JOIN post_tags pt ON p.id = pt.post_id
LEFT JOIN tag t ON pt.tag_id = t.id
LEFT JOIN post_workflow_stage pws ON p.id = pws.post_id
LEFT JOIN workflow_stage_entity ws ON pws.stage_id = ws.id
WHERE p.id = ?;
```

#### Get Image Processing Status
```sql
SELECT i.filename, 
       ipj.status, 
       ips.progress,
       array_agg(ips.step_name) as completed_steps
FROM image i
JOIN image_processing_jobs ipj ON i.id = ipj.image_id
JOIN image_processing_status ips ON ipj.id = ips.job_id
WHERE ipj.status = 'processing';
```

#### Get Syndication Progress
```sql
SELECT p.title,
       pl.name as platform,
       sp.status,
       sp.progress,
       pq.scheduled_at
FROM post p
JOIN syndication_progress sp ON p.id = sp.post_id
JOIN platforms pl ON sp.platform_id = pl.id
LEFT JOIN posting_queue pq ON p.id = pq.post_id
WHERE sp.status != 'completed';
```

## Performance Considerations

### Indexes
Key indexes are automatically created on:
- Primary keys (`id` columns)
- Foreign keys (relationship columns)
- Frequently queried columns (`post_id`, `status`, `created_at`)

### Query Optimization
- Use specific column selection instead of `SELECT *`
- Leverage the grouped table structure for efficient browsing
- Use the database interface's built-in filtering for large datasets

## Backup and Recovery

### Automated Backups
- Database backups are stored in the `backups/` directory
- Use the database interface to create manual backups
- Backup files are named with timestamps: `blog_backup_YYYYMMDD_HHMMSS.sql`

### Recovery Process
1. Access the database interface at `/db/`
2. Navigate to the "Backup & Restore" section
3. Select a backup file from the list
4. Click "Restore" to restore the database

## Security

### Credential Management
- API credentials are encrypted in the `credentials` table
- Use the credential management system for secure storage
- Regular rotation of API keys is recommended

### Access Control
- Database access is controlled through the unified application
- No direct database access should be required for normal operations
- Use the database interface for all database interactions
