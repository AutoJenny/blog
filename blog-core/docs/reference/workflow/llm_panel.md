# LLM Panel System Reference

> **Note**: For comprehensive documentation of the LLM message preview and assembly system, see [LLM Message System Reference](llm_message_system.md).

## Overview

The LLM Panel system provides a modular, reusable interface for LLM action execution across different workflow stages. It handles input/output field mapping, action selection, and result processing with a consistent UI pattern.

## Architecture

### Core Components

1. **Modular Panel Template**: `app/templates/modules/llm_panel/templates/components/`
2. **JavaScript Field Selector**: `app/static/modules/llm_panel/js/field_selector.js`
3. **Backend API Endpoints**: `/api/workflow/` routes
4. **Field Mapping System**: Dynamic field selection based on stage/substage

### Panel Structure

```
LLM Panel
├── Inputs Section
│   ├── Field Selector Dropdown
│   └── Input Text Area
├── Action Selection
│   ├── Action Dropdown
│   └── Action Details Panel
└── Outputs Section
    ├── Field Selector Dropdown
    └── Output Text Area
```

## Field Selector System

### Dynamic Field Loading

The field selector system dynamically loads available fields based on the current workflow stage and context:

#### For Writing Stage Outputs
- **Endpoint**: `/api/workflow/post_section_fields`
- **Usage**: Used specifically for Writing stage LLM action Outputs dropdown
- **Response**: All text fields from post_section table
- **Key Fields**: `draft`, `polished`, `section_heading`, `ideas_to_include`, etc.

#### For Other Stages
- **Endpoint**: `/api/workflow/fields/available`
- **Usage**: Used for Planning and Publishing stages
- **Response**: All available fields with stage/substage mappings

### JavaScript Implementation

The field selector is implemented in `app/static/modules/llm_panel/js/field_selector.js`:

```javascript
// For Writing stage outputs, use the new post_section_text_fields endpoint
if (this.stage === 'writing' && section === 'outputs') {
    const response = await fetch('/api/workflow/post_section_fields');
    const data = await response.json();
    // Populate dropdown with data.fields
}
```

### Field Selector Behavior

| Stage | Section | Endpoint Used | Purpose |
|-------|---------|---------------|---------|
| Writing | outputs | `/api/workflow/post_section_fields` | Show all post_section text fields |
| Writing | inputs | `/api/workflow/fields/available` | Show mapped input fields |
| Planning | outputs | `/api/workflow/fields/available` | Show mapped output fields |
| Publishing | outputs | `/api/workflow/fields/available` | Show mapped output fields |

## API Endpoints

### Post Section Text Fields
- **URL**: `/api/workflow/post_section_fields`
- **Method**: `GET`
- **Description**: Returns all text fields from post_section table
- **Used By**: Writing stage Outputs dropdown
- **Response**: Array of field names including `draft` and `polished`

### Available Fields
- **URL**: `/api/workflow/fields/available`
- **Method**: `GET`
- **Description**: Returns all available fields with stage mappings
- **Used By**: Input fields and non-Writing stage outputs
- **Response**: Structured field data with mappings

## Content Quality Fields

### Simplified Two-Field System

The system now uses a simplified content quality model:

- **`draft`**: Initial raw content before LLM processing
- **`polished`**: Final publication-ready content after unified LLM processing

### Migration from Four-Field System

Previously used four fields:
- `first_draft` → `draft`
- `generation` → (removed)
- `optimization` → (removed)  
- `uk_british` → `polished`

### Database Schema

```sql
-- post_section table text fields
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'post_section' 
AND data_type IN ('text', 'character varying', 'varchar')
AND column_name NOT IN ('id', 'post_id', 'section_order', 'image_id', 'image_prompt_example_id');
```

## Usage Examples

### Testing the Endpoint

```bash
# Test post_section_fields endpoint
curl -s "http://localhost:5000/api/workflow/post_section_fields" -H "Accept: application/json"

# Expected response:
{
  "fields": [
    "section_heading",
    "ideas_to_include", 
    "facts_to_include",
    "highlighting",
    "image_concepts",
    "image_prompts",
    "watermarking",
    "image_meta_descriptions",
    "image_captions",
    "generated_image_url",
    "section_description",
    "status",
    "polished",
    "draft"
  ]
}
```

### Frontend Integration

The field selector automatically detects the stage and section to use the appropriate endpoint:

1. **Writing Stage + Outputs**: Uses `/api/workflow/post_section_fields`
2. **All Other Cases**: Uses `/api/workflow/fields/available`

## Error Handling

### Common Issues

1. **Wrong Endpoint URL**: 
   - ❌ `/api/workflow/post_section_text_fields/<post_id>`
   - ✅ `/api/workflow/post_section_fields`

2. **Missing Post ID Parameter**:
   - The endpoint does NOT take a post_id parameter
   - It returns global field list for post_section table

3. **Frontend Not Updating**:
   - Check browser console for JavaScript errors
   - Verify the stage is 'writing' and section is 'outputs'
   - Ensure the field selector has correct data attributes

## Testing Checklist

- [ ] Backend endpoint returns JSON (not HTML)
- [ ] Frontend page loads without JavaScript errors
- [ ] Writing stage Outputs dropdown shows all post_section fields
- [ ] `draft` and `polished` fields are included in dropdown
- [ ] Field selection saves correctly
- [ ] LLM actions work with selected fields

## Related Documentation

- [API Reference - Posts](../api/current/posts.md#post-section-text-fields-endpoint)
- [Workflow Endpoints](endpoints.md)
- [Content Quality Migration](../workflow/sections.md#content-quality-fields) 