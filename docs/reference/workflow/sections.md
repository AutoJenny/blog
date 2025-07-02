# Section-Based Workflow Documentation

## Overview

The section-based workflow system enables modular content creation by breaking blog posts into discrete, manageable sections. Each section can be independently edited, reordered, and processed through LLM actions. This approach supports content repurposing across different platforms and formats while maintaining a structured workflow.

### Key Concepts

- **Sections**: Discrete content blocks within a blog post, each with a title, content, and metadata
- **Section Elements**: Individual facts, ideas, or themes associated with specific sections
- **Per-Section Editing**: Independent editing and LLM processing of individual sections
- **Section Workflow**: Integration with the main workflow system for stage/substage/step management

## Database Schema

### Table: post_section

The `post_section` table stores section metadata and content for each blog post.

| Column              | Type         | Description                                      |
|---------------------|--------------|--------------------------------------------------|
| id                  | SERIAL (PK)  | Unique section identifier                        |
| post_id             | INTEGER      | Foreign key to post(id)                          |
| title               | VARCHAR(200) | Section heading/title                            |
| description         | TEXT         | Section description or summary                   |
| content             | TEXT         | Main section content                             |
| position            | INTEGER      | Order within the post (1-based)                  |
| content_type        | VARCHAR(50)  | Type of content (e.g., 'text', 'image', 'video') |
| created_at          | TIMESTAMP    | Creation timestamp                               |
| updated_at          | TIMESTAMP    | Last update timestamp                            |
| section_metadata    | JSONB        | Additional metadata (SEO, social, etc.)         |

**Indexes:**
- `idx_post_section_position`: (post_id, position) - Unique ordering
- `idx_post_section_content_type`: content_type - Content filtering
- `idx_post_section_created`: created_at - Chronological queries

**Constraints:**
- `UNIQUE(post_id, position)` - Ensures no duplicate positions within a post
- `FOREIGN KEY(post_id) REFERENCES post(id)` - Referential integrity

### Table: post_section_elements

The `post_section_elements` table stores individual elements (facts, ideas, themes) associated with specific sections.

| Column        | Type         | Description                                      |
|---------------|--------------|--------------------------------------------------|
| id            | SERIAL (PK)  | Unique element identifier                        |
| section_id    | INTEGER      | Foreign key to post_section(id)                  |
| element_type  | VARCHAR(50)  | Type of element ('fact', 'idea', 'theme')       |
| element_text  | TEXT         | The actual element content                       |
| position      | INTEGER      | Order within the section (1-based)               |
| created_at    | TIMESTAMP    | Creation timestamp                               |

**Indexes:**
- `idx_post_section_elements_section`: section_id - Section filtering
- `idx_post_section_elements_type`: element_type - Type filtering
- `idx_post_section_elements_position`: (section_id, position) - Ordering

**Constraints:**
- `FOREIGN KEY(section_id) REFERENCES post_section(id)` - Referential integrity
- `UNIQUE(section_id, position)` - Ensures no duplicate positions within a section

### Relationships

```
post (1) ←→ (many) post_section (1) ←→ (many) post_section_elements
```

- Each post can have multiple sections
- Each section can have multiple elements (facts, ideas, themes)
- Sections are ordered by position within the post
- Elements are ordered by position within the section

## API Endpoints

### Section Management

#### Get All Sections for a Post
```http
GET /api/workflow/posts/{post_id}/sections
```

**Example:**
```bash
curl -s "http://localhost:5000/api/workflow/posts/22/sections" | python3 -m json.tool
```

**Response:**
```json
{
  "sections": [
    {
      "id": 1,
      "post_id": 22,
      "title": "Introduction",
      "description": "Overview of the topic",
      "content": "This section introduces...",
      "position": 1,
      "content_type": "text",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "section_metadata": {
        "seo_keywords": ["introduction", "overview"],
        "social_summary": "Brief introduction to the topic"
      }
    }
  ]
}
```

#### Create a New Section
```http
POST /api/workflow/posts/{post_id}/sections
```

**Example:**
```bash
curl -s -X POST "http://localhost:5000/api/workflow/posts/22/sections" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Section",
    "description": "Section description",
    "content": "Section content...",
    "position": 2,
    "content_type": "text",
    "section_metadata": {
      "seo_keywords": ["keyword1", "keyword2"]
    }
  }' | python3 -m json.tool
```

#### Get a Specific Section
```http
GET /api/workflow/posts/{post_id}/sections/{section_id}
```

**Example:**
```bash
curl -s "http://localhost:5000/api/workflow/posts/22/sections/1" | python3 -m json.tool
```

#### Update a Section
```http
PUT /api/workflow/posts/{post_id}/sections/{section_id}
```

**Example:**
```bash
curl -s -X PUT "http://localhost:5000/api/workflow/posts/22/sections/1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Section Title",
    "content": "Updated content...",
    "section_metadata": {
      "seo_keywords": ["updated", "keywords"]
    }
  }' | python3 -m json.tool
```

#### Delete a Section
```http
DELETE /api/workflow/posts/{post_id}/sections/{section_id}
```

**Example:**
```bash
curl -s -X DELETE "http://localhost:5000/api/workflow/posts/22/sections/1" | python3 -m json.tool
```

#### Reorder Sections
```http
PUT /api/workflow/posts/{post_id}/sections/reorder
```

**Example:**
```bash
curl -s -X PUT "http://localhost:5000/api/workflow/posts/22/sections/reorder" \
  -H "Content-Type: application/json" \
  -d '{
    "section_ids": [3, 1, 4, 2]
  }' | python3 -m json.tool
```

### Section Elements Management

#### Get Elements for a Section
```http
GET /api/workflow/posts/{post_id}/sections/{section_id}/elements
```

**Example:**
```bash
curl -s "http://localhost:5000/api/workflow/posts/22/sections/1/elements" | python3 -m json.tool
```

**Response:**
```json
{
  "elements": [
    {
      "id": 1,
      "section_id": 1,
      "element_type": "fact",
      "element_text": "Key fact about the topic",
      "position": 1,
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "section_id": 1,
      "element_type": "idea",
      "element_text": "Main idea to explore",
      "position": 2,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Add Element to Section
```http
POST /api/workflow/posts/{post_id}/sections/{section_id}/elements
```

**Example:**
```bash
curl -s -X POST "http://localhost:5000/api/workflow/posts/22/sections/1/elements" \
  -H "Content-Type: application/json" \
  -d '{
    "element_type": "fact",
    "element_text": "New fact to add",
    "position": 3
  }' | python3 -m json.tool
```

#### Update Section Element
```http
PUT /api/workflow/posts/{post_id}/sections/{section_id}/elements/{element_id}
```

**Example:**
```bash
curl -s -X PUT "http://localhost:5000/api/workflow/posts/22/sections/1/elements/1" \
  -H "Content-Type: application/json" \
  -d '{
    "element_text": "Updated fact content"
  }' | python3 -m json.tool
```

#### Delete Section Element
```http
DELETE /api/workflow/posts/{post_id}/sections/{section_id}/elements/{element_id}
```

**Example:**
```bash
curl -s -X DELETE "http://localhost:5000/api/workflow/posts/22/sections/1/elements/1" | python3 -m json.tool
```

### Section Fields (for Workflow Integration)

#### Get Section Fields
```http
GET /api/workflow/posts/{post_id}/sections/{section_id}/fields
```

**Example:**
```bash
curl -s "http://localhost:5000/api/workflow/posts/22/sections/1/fields" | python3 -m json.tool
```

**Response:**
```json
{
  "fields": {
    "section_title": "Introduction",
    "section_content": "This section introduces...",
    "section_description": "Overview of the topic",
    "section_elements": [
      {
        "type": "fact",
        "text": "Key fact about the topic"
      },
      {
        "type": "idea", 
        "text": "Main idea to explore"
      }
    ]
  }
}
```

## UI Integration

### Writing Stage Layout

The writing stage uses a two-column layout with the LLM panel on the left and sections panel on the right:

```html
<!-- In app/templates/workflow/index.html -->
{% elif current_stage == 'writing' %}
<div class="px-6 -mt-20">
  <div class="flex gap-6" style="min-height: 400px;">
    <!-- LLM Actions Panel -->
    <div id="workflow-llm-actions" style="background-color: #2D0A50; width: 50%;">
      {% include 'workflow/_modular_llm_panels.html' %}
    </div>
    <!-- Sections Panel -->
    <div id="workflow-sections" style="background-color: #013828; width: 50%;">
      <!-- Sections content loaded via JavaScript -->
    </div>
  </div>
</div>
```

### JavaScript Module: template_view.js

The sections panel is rendered using the `template_view.js` module:

```javascript
// app/static/js/workflow/template_view.js
export function renderStructure(data) {
  const { post, sections } = data;
  
  if (!sections || sections.length === 0) {
    return '<div class="p-4 text-gray-400">No sections found. Create your first section to get started.</div>';
  }
  
  return sections.map(section => `
    <div class="section-item mb-4 p-4 bg-gray-800 rounded-lg">
      <h3 class="text-lg font-semibold text-white mb-2">${section.title}</h3>
      <p class="text-gray-300 mb-2">${section.description || ''}</p>
      <div class="text-sm text-gray-400">
        <strong>Position:</strong> ${section.position} | 
        <strong>Type:</strong> ${section.content_type}
      </div>
      <div class="mt-2 text-gray-300">
        ${section.content.substring(0, 200)}${section.content.length > 200 ? '...' : ''}
      </div>
    </div>
  `).join('');
}
```

### Section Panel Initialization

```javascript
// In workflow template
<script type="module">
  import sectionPanel from '/static/js/workflow/template_view.js';
  
  document.addEventListener('DOMContentLoaded', async () => {
    const postId = {{ post.id }};
    const panel = document.getElementById('workflow-sections');
    
    try {
      // Fetch sections data
      const response = await fetch(`/api/workflow/posts/${postId}/sections`);
      const data = await response.json();
      
      // Render sections
      const structure = { 
        post: { id: postId }, 
        sections: data.sections || [] 
      };
      panel.innerHTML = sectionPanel.renderStructure(structure);
    } catch (error) {
      console.error('Error loading sections:', error);
      panel.innerHTML = '<div class="p-4 text-red-400">Error loading sections</div>';
    }
  });
</script>
```

## Workflow Integration

### Stage/Substage/Step Mapping

Sections are primarily used in the **Writing** stage, specifically:

- **Stage**: Writing
- **Substage**: Content  
- **Steps**: 
  - Create Sections
  - Edit Section Content
  - Review Sections
  - Allocate Facts to Sections

### LLM Integration

Sections can be processed through LLM actions in several ways:

#### 1. Section-Specific LLM Actions

```json
{
  "action_name": "Expand Section",
  "input_field": "section_content",
  "output_field": "section_content",
  "prompt_template": "Expand the following section content with more detail and examples: [data:section_content]"
}
```

#### 2. Section Allocation Actions

```json
{
  "action_name": "Allocate Facts to Sections",
  "input_field": "research_facts",
  "output_field": "section_elements",
  "prompt_template": "Given these facts: [data:research_facts] and these sections: [data:sections], allocate each fact to the most appropriate section."
}
```

#### 3. Section Generation Actions

```json
{
  "action_name": "Generate Section Content",
  "input_field": "section_outline",
  "output_field": "section_content", 
  "prompt_template": "Based on this outline: [data:section_outline], write detailed content for the section."
}
```

### Format Templates for Sections

#### Input Format Template
```json
{
  "name": "Section Input Format",
  "description": "Format for section data input to LLM actions",
  "fields": [
    { "name": "section_title", "type": "string", "required": true, "description": "Section title" },
    { "name": "section_content", "type": "string", "required": true, "description": "Current section content" },
    { "name": "section_elements", "type": "array", "required": false, "description": "Associated facts/ideas" }
  ],
  "format_type": "input",
  "llm_instructions": "The input data contains section information including title, content, and associated elements."
}
```

#### Output Format Template
```json
{
  "name": "Section Output Format", 
  "description": "Format for LLM-generated section content",
  "fields": [
    { "name": "section_title", "type": "string", "required": true, "description": "Updated section title" },
    { "name": "section_content", "type": "string", "required": true, "description": "Generated section content" },
    { "name": "key_points", "type": "array", "required": false, "description": "Key points extracted from content" }
  ],
  "format_type": "output",
  "llm_instructions": "Return the updated section with title, content, and optional key points in the specified format."
}
```

## Testing

### Section CRUD Testing

#### 1. Create a Test Post
```bash
# Create a test post first
curl -s "http://localhost:5000/test_insert" | python3 -m json.tool
```

#### 2. Create Sections
```bash
# Create first section
curl -s -X POST "http://localhost:5000/api/workflow/posts/22/sections" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Introduction",
    "description": "Overview of the topic",
    "content": "This is the introduction section content.",
    "position": 1,
    "content_type": "text"
  }' | python3 -m json.tool

# Create second section
curl -s -X POST "http://localhost:5000/api/workflow/posts/22/sections" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Main Content",
    "description": "Core content of the post",
    "content": "This is the main content section.",
    "position": 2,
    "content_type": "text"
  }' | python3 -m json.tool
```

#### 3. List Sections
```bash
# Get all sections for the post
curl -s "http://localhost:5000/api/workflow/posts/22/sections" | python3 -m json.tool
```

#### 4. Update a Section
```bash
# Update the first section
curl -s -X PUT "http://localhost:5000/api/workflow/posts/22/sections/1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Introduction",
    "content": "This is the updated introduction content."
  }' | python3 -m json.tool
```

#### 5. Reorder Sections
```bash
# Reorder sections (swap positions)
curl -s -X PUT "http://localhost:5000/api/workflow/posts/22/sections/reorder" \
  -H "Content-Type: application/json" \
  -d '{
    "section_ids": [2, 1]
  }' | python3 -m json.tool
```

#### 6. Add Section Elements
```bash
# Add a fact to the first section
curl -s -X POST "http://localhost:5000/api/workflow/posts/22/sections/1/elements" \
  -H "Content-Type: application/json" \
  -d '{
    "element_type": "fact",
    "element_text": "This is an important fact about the topic.",
    "position": 1
  }' | python3 -m json.tool
```

#### 7. Get Section Fields (for Workflow)
```bash
# Get section fields for LLM processing
curl -s "http://localhost:5000/api/workflow/posts/22/sections/1/fields" | python3 -m json.tool
```

### Workflow Integration Testing

#### 1. Test Section-Based LLM Action
```bash
# Run LLM action on a section
curl -s -X POST "http://localhost:5000/api/workflow/posts/22/writing/content/llm" \
  -H "Content-Type: application/json" \
  -d '{
    "step": "create_sections",
    "input_field": "section_content",
    "output_field": "section_content"
  }' | python3 -m json.tool
```

#### 2. Test Section Allocation
```bash
# Allocate facts to sections
curl -s -X POST "http://localhost:5000/api/workflow/posts/22/writing/content/llm" \
  -H "Content-Type: application/json" \
  -d '{
    "step": "allocate_facts_to_sections",
    "input_field": "research_facts",
    "output_field": "section_elements"
  }' | python3 -m json.tool
```

### Common Issues and Solutions

#### Issue: Section Not Found
- **Cause**: Invalid section_id or post_id
- **Solution**: Verify section exists with `GET /api/workflow/posts/{post_id}/sections`

#### Issue: Position Conflict
- **Cause**: Duplicate position values within a post
- **Solution**: Use reorder endpoint to fix positions or ensure unique positions

#### Issue: Sections Not Loading in UI
- **Cause**: JavaScript error or API endpoint issue
- **Solution**: Check browser console and test API endpoint with curl

#### Issue: LLM Action Not Working with Sections
- **Cause**: Incorrect field mapping or format template
- **Solution**: Verify input/output fields and format templates are configured correctly

## Best Practices

### 1. Section Organization
- Keep sections focused on single topics
- Use consistent section lengths (aim for 200-500 words)
- Maintain logical flow between sections
- Use descriptive section titles

### 2. Content Management
- Store section metadata in the `section_metadata` JSONB field
- Use section elements for facts, ideas, and themes
- Maintain proper ordering with position fields
- Version control section content through timestamps

### 3. Workflow Integration
- Map sections to appropriate workflow stages/steps
- Use format templates for consistent LLM processing
- Test section-based LLM actions thoroughly
- Maintain clear field mappings between sections and workflow

### 4. Performance
- Use database indexes for efficient queries
- Limit section content length for UI performance
- Cache frequently accessed section data
- Use pagination for posts with many sections

## References

- [Workflow System Overview](README.md)
- [API Endpoints Reference](endpoints.md)
- [Format System Guide](formats.md)
- [LLM Panel Integration](llm_panel.md)
- [Database Schema](../database/schema.md)
- [Template System](templates.md)

---

**Note**: This documentation covers the section-based workflow functionality. For general workflow concepts, see the main [Workflow System Overview](README.md). 