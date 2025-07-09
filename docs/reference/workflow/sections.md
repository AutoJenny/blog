# Section-Based Workflow Documentation

## Overview

The section-based workflow system enables modular content creation by breaking blog posts into discrete, manageable sections. Each section can be independently edited, reordered, and processed through LLM actions. This approach supports content repurposing across different platforms and formats while maintaining a structured workflow.

### Key Concepts

- **Sections**: Discrete content blocks within a blog post, each with a title, content, and metadata
- **Section Elements**: Individual facts, ideas, or themes associated with specific sections
- **Per-Section Editing**: Independent editing and LLM processing of individual sections
- **Section Workflow**: Integration with the main workflow system for stage/substage/step management
- **Section Synchronization**: Automatic data consistency between planning and individual section management

## Section Data Architecture

### Dual-Field System

The system uses two complementary fields to manage section data:

#### 1. post_development.section_headings (Master Field)
- **Purpose**: Master list of all section headings for a post
- **Usage**: LLM actions, workflow planning, and overall post structure
- **Format**: JSON array containing structured section data
- **Authority**: Primary source of truth for section structure

#### 2. post_section.section_heading (Individual Field)
- **Purpose**: Individual section heading for UI display and management
- **Usage**: Green sections module, accordion display, drag-and-drop reordering
- **Format**: Simple text string for each section
- **Authority**: Derived from master field, used for UI interactions

### Data Synchronization Strategy

#### Primary Direction: post_development → post_section
- **Trigger**: Any update to `post_development.section_headings`
- **Action**: Automatically sync to individual `post_section` records
- **Purpose**: Ensure UI sections reflect the master planning data

#### Secondary Direction: post_section → post_development (Optional)
- **Trigger**: When individual sections are created/updated/deleted
- **Action**: Update the master list to reflect actual section data
- **Purpose**: Keep planning data in sync with actual implementation

### Data Format Standards

#### Recommended JSON Format for section_headings
```json
[
  {
    "order": 1,
    "heading": "Introduction",
    "description": "Overview of the topic",
    "status": "draft"
  },
  {
    "order": 2,
    "heading": "Main Content",
    "description": "Core discussion points",
    "status": "in_progress"
  },
  {
    "order": 3,
    "heading": "Conclusion",
    "description": "Summary and takeaways",
    "status": "complete"
  }
]
```

#### Legacy Format Support
The system supports multiple formats during transition:
- **Simple Array**: `["Section 1", "Section 2", "Section 3"]`
- **Delimited String**: `"Section 1\nSection 2\nSection 3"`
- **Numbered Format**: `"1. Section 1\n2. Section 2"`

## Database Schema

### Table: post_section

The `post_section` table stores section metadata and content for each blog post.

| Column              | Type         | Description                                      |
|---------------------|--------------|--------------------------------------------------|
| id                  | SERIAL (PK)  | Unique section identifier                        |
| post_id             | INTEGER      | Foreign key to post(id)                          |
| section_order       | INTEGER      | Order within the post (1-based)                  |
| section_heading     | TEXT         | Section heading/title (synced from master)       |
| section_description | TEXT         | Section description or summary                   |
| ideas_to_include    | TEXT         | Ideas to include in this section                 |
| facts_to_include    | TEXT         | Facts to include in this section                 |
| draft               | TEXT         | Initial raw content before processing            |
| polished            | TEXT         | Final publication-ready content after unified LLM processing |
| highlighting        | TEXT         | Key points to highlight                          |
| image_concepts      | TEXT         | Image concepts for this section                  |
| image_prompts       | TEXT         | Image generation prompts                         |
| watermarking        | TEXT         | Image watermarking settings                      |
| image_meta_descriptions | TEXT     | Image metadata descriptions                      |
| image_captions      | TEXT         | Image captions                                   |
| image_prompt_example_id | INTEGER  | Reference to image prompt example                |
| generated_image_url | VARCHAR(512) | URL of generated image                           |
| image_generation_metadata | JSONB   | Metadata from image generation                   |
| image_id            | INTEGER      | Reference to image(id)                           |
| status              | TEXT         | Section status (draft, in_progress, complete)    |

**Indexes:**
- `idx_post_section_post_order`: (post_id, section_order) - Unique ordering
- `idx_post_section_status`: status - Status filtering
- `idx_post_section_created`: created_at - Chronological queries

**Constraints:**
- `UNIQUE(post_id, section_order)` - Ensures no duplicate positions within a post
- `FOREIGN KEY(post_id) REFERENCES post(id)` - Referential integrity

### Table: post_development

The `post_development` table includes the master section headings field:

| Column           | Type         | Description                                      |
|------------------|--------------|--------------------------------------------------|
| id               | SERIAL (PK)  | Unique identifier                                |
| post_id          | INTEGER      | Foreign key to post(id)                          |
| section_headings | TEXT         | **MASTER FIELD**: JSON array of section data     |
| ...              | ...          | Other development fields                         |

**Note**: The `section_headings` field is the authoritative source for section structure and is used by LLM actions and workflow planning.

### Table: post_section_elements

The `post_section_elements` table stores individual elements (facts, ideas, themes) associated with specific sections.

| Column        | Type         | Description                                      |
|---------------|--------------|--------------------------------------------------|
| id            | SERIAL (PK)  | Unique element identifier                        |
| post_id       | INTEGER      | Foreign key to post(id)                          |
| section_id    | INTEGER      | Foreign key to post_section(id)                  |
| element_type  | VARCHAR(50)  | Type of element ('fact', 'idea', 'theme')       |
| element_text  | TEXT         | The actual element content                       |
| element_order | INTEGER      | Order within the section (1-based)               |
| created_at    | TIMESTAMP    | Creation timestamp                               |
| updated_at    | TIMESTAMP    | Last update timestamp                            |

**Indexes:**
- `idx_post_section_elements_post_id`: post_id - Post filtering
- `idx_post_section_elements_section_id`: section_id - Section filtering
- `idx_post_section_elements_type`: element_type - Type filtering
- `idx_post_section_elements_order`: (section_id, element_order) - Ordering

**Constraints:**
- `FOREIGN KEY(section_id) REFERENCES post_section(id)` - Referential integrity
- `UNIQUE(section_id, element_order)` - Ensures no duplicate positions within a section

### Relationships

```
post (1) ←→ (1) post_development (1) ←→ (many) post_section (1) ←→ (many) post_section_elements
```

- Each post has one development record with the master section list
- Each post can have multiple sections (synced from master list)
- Each section can have multiple elements (facts, ideas, themes)
- Sections are ordered by section_order within the post
- Elements are ordered by element_order within the section

## Synchronization Implementation

### Database Triggers

#### Primary Sync Trigger (post_development → post_section)
```sql
-- Trigger function for post_development.section_headings changes
CREATE OR REPLACE FUNCTION sync_section_headings_to_sections()
RETURNS TRIGGER AS $$
DECLARE
    section_data JSONB;
    section_item JSONB;
    section_id INTEGER;
    i INTEGER := 0;
BEGIN
    -- Only proceed if section_headings was updated
    IF OLD.section_headings IS NOT DISTINCT FROM NEW.section_headings THEN
        RETURN NEW;
    END IF;
    
    -- Parse the section_headings JSON
    IF NEW.section_headings IS NULL OR NEW.section_headings = '' THEN
        -- Clear all sections for this post
        DELETE FROM post_section WHERE post_id = NEW.post_id;
        RETURN NEW;
    END IF;
    
    BEGIN
        section_data := NEW.section_headings::JSONB;
    EXCEPTION WHEN OTHERS THEN
        -- Handle invalid JSON - log error but don't fail
        RAISE WARNING 'Invalid JSON in section_headings for post %: %', NEW.post_id, NEW.section_headings;
        RETURN NEW;
    END;
    
    -- Process each section in the array
    FOR section_item IN SELECT * FROM jsonb_array_elements(section_data)
    LOOP
        i := i + 1;
        
        -- Extract section data
        DECLARE
            heading TEXT;
            description TEXT;
            status TEXT;
        BEGIN
            -- Handle different JSON formats
            IF jsonb_typeof(section_item) = 'string' THEN
                heading := section_item::TEXT;
                description := '';
                status := 'draft';
            ELSE
                heading := COALESCE(section_item->>'heading', section_item->>'title', 'Section ' || i);
                description := COALESCE(section_item->>'description', '');
                status := COALESCE(section_item->>'status', 'draft');
            END IF;
            
            -- Find existing section or create new one
            SELECT id INTO section_id 
            FROM post_section 
            WHERE post_id = NEW.post_id AND section_order = i;
            
            IF section_id IS NULL THEN
                -- Create new section
                INSERT INTO post_section (
                    post_id, section_order, section_heading, 
                    section_description, status
                ) VALUES (
                    NEW.post_id, i, heading, description, status
                );
            ELSE
                -- Update existing section
                UPDATE post_section 
                SET section_heading = heading,
                    section_description = description,
                    status = status,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = section_id;
            END IF;
        END;
    END LOOP;
    
    -- Remove sections that are no longer in the list
    DELETE FROM post_section 
    WHERE post_id = NEW.post_id AND section_order > i;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger on post_development updates
CREATE TRIGGER trigger_sync_section_headings
    AFTER UPDATE OF section_headings ON post_development
    FOR EACH ROW
    EXECUTE FUNCTION sync_section_headings_to_sections();
```

#### Secondary Sync Trigger (post_section → post_development) - Optional
```sql
-- Trigger function for post_section changes
CREATE OR REPLACE FUNCTION sync_sections_to_section_headings()
RETURNS TRIGGER AS $$
DECLARE
    section_headings JSONB;
    section_record RECORD;
BEGIN
    -- Build JSON array from current sections
    section_headings := '[]'::JSONB;
    
    FOR section_record IN 
        SELECT section_order, section_heading, section_description, status
        FROM post_section 
        WHERE post_id = COALESCE(NEW.post_id, OLD.post_id)
        ORDER BY section_order
    LOOP
        section_headings := section_headings || jsonb_build_object(
            'order', section_record.section_order,
            'heading', section_record.section_heading,
            'description', COALESCE(section_record.section_description, ''),
            'status', COALESCE(section_record.status, 'draft')
        );
    END LOOP;
    
    -- Update post_development
    UPDATE post_development 
    SET section_headings = section_headings::TEXT,
        updated_at = CURRENT_TIMESTAMP
    WHERE post_id = COALESCE(NEW.post_id, OLD.post_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Triggers for post_section changes
CREATE TRIGGER trigger_sync_sections_to_headings_insert
    AFTER INSERT ON post_section
    FOR EACH ROW
    EXECUTE FUNCTION sync_sections_to_section_headings();

CREATE TRIGGER trigger_sync_sections_to_headings_update
    AFTER UPDATE ON post_section
    FOR EACH ROW
    EXECUTE FUNCTION sync_sections_to_section_headings();

CREATE TRIGGER trigger_sync_sections_to_headings_delete
    AFTER DELETE ON post_section
    FOR EACH ROW
    EXECUTE FUNCTION sync_sections_to_section_headings();
```

### Application-Level Synchronization

#### Manual Sync API Endpoint
```python
@bp.route('/posts/<int:post_id>/sync-sections', methods=['POST'])
def sync_sections(post_id):
    """Manually sync section data between post_development and post_section"""
    direction = request.json.get('direction', 'both')  # 'to_sections', 'to_development', 'both'
    
    try:
        if direction in ['to_sections', 'both']:
            # Sync post_development.section_headings → post_section
            post_dev = get_post_development(post_id)
            if post_dev and post_dev.section_headings:
                sync_section_headings_to_sections(post_id, post_dev.section_headings)
        
        if direction in ['to_development', 'both']:
            # Sync post_section → post_development.section_headings
            sync_sections_to_section_headings(post_id)
        
        return jsonify({
            'status': 'success', 
            'direction': direction,
            'message': f'Sections synchronized successfully'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Sync failed: {str(e)}'
        }), 500
```

#### Synchronization Functions
```python
def sync_section_headings_to_sections(post_id: int, section_headings_json: str):
    """
    Parse section_headings from post_development and sync to post_section records
    """
    try:
        # Parse the JSON array
        sections_data = json.loads(section_headings_json)
        
        # Clear existing sections for this post
        with get_db_conn() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM post_section WHERE post_id = %s", (post_id,))
            
            # Create new sections from the JSON data
            for i, section_info in enumerate(sections_data):
                if isinstance(section_info, str):
                    # Simple string format
                    heading = section_info
                    description = ""
                    status = "draft"
                else:
                    # Structured format
                    heading = section_info.get('heading', section_info.get('title', f'Section {i+1}'))
                    description = section_info.get('description', '')
                    status = section_info.get('status', 'draft')
                
                # Insert new section
                cur.execute("""
                    INSERT INTO post_section (
                        post_id, section_order, section_heading, 
                        section_description, status
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (post_id, i+1, heading, description, status))
            
            conn.commit()
            
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in section_headings: {e}")
    except Exception as e:
        raise Exception(f"Failed to sync sections: {e}")

def sync_sections_to_section_headings(post_id: int):
    """
    Update post_development.section_headings based on current post_section records
    """
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get all sections for this post
        cur.execute("""
            SELECT section_order, section_heading, section_description, status
            FROM post_section 
            WHERE post_id = %s 
            ORDER BY section_order
        """, (post_id,))
        
        sections = cur.fetchall()
        
        # Build JSON array
        section_headings = []
        for section in sections:
            section_headings.append({
                "order": section['section_order'],
                "heading": section['section_heading'],
                "description": section['section_description'] or "",
                "status": section['status'] or "draft"
            })
        
        # Update post_development
        cur.execute("""
            UPDATE post_development 
            SET section_headings = %s
            WHERE post_id = %s
        """, (json.dumps(section_headings), post_id))
        
        conn.commit()
```

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
      "section_order": 1,
      "section_heading": "Introduction",
      "section_description": "Overview of the topic",
      "status": "draft",
      "ideas_to_include": "Key concepts to cover",
      "facts_to_include": "Important facts to mention",
      "draft": "Initial content...",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
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
    "section_heading": "New Section",
    "section_description": "Section description",
    "section_order": 2,
    "status": "draft"
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
    "section_heading": "Updated Section Title",
    "section_description": "Updated description",
    "status": "in_progress"
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

### Section Synchronization

#### Manual Sync
```http
POST /api/workflow/posts/{post_id}/sync-sections
```

**Example:**
```bash
# Sync both directions
curl -s -X POST "http://localhost:5000/api/workflow/posts/22/sync-sections" \
  -H "Content-Type: application/json" \
  -d '{"direction": "both"}' | python3 -m json.tool

# Sync only to sections
curl -s -X POST "http://localhost:5000/api/workflow/posts/22/sync-sections" \
  -H "Content-Type: application/json" \
  -d '{"direction": "to_sections"}' | python3 -m json.tool

# Sync only to development
curl -s -X POST "http://localhost:5000/api/workflow/posts/22/sync-sections" \
  -H "Content-Type: application/json" \
  -d '{"direction": "to_development"}' | python3 -m json.tool
```

**Response:**
```json
{
  "status": "success",
  "direction": "both",
  "message": "Sections synchronized successfully"
}
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
      "element_order": 1,
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "section_id": 1,
      "element_type": "idea",
      "element_text": "Main idea to explore",
      "element_order": 2,
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
    "element_order": 3
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
    "section_heading": "Introduction",
    "section_description": "Overview of the topic",
    "section_content": "This section introduces...",
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
      <h3 class="text-lg font-semibold text-white mb-2">${section.section_heading}</h3>
      <p class="text-gray-300 mb-2">${section.section_description || ''}</p>
      <div class="text-sm text-gray-400">
        <strong>Position:</strong> ${section.section_order} | 
        <strong>Status:</strong> ${section.status || 'draft'}
      </div>
      <div class="mt-2 text-gray-300">
        ${section.draft ? section.draft.substring(0, 200) + '...' : 'No content yet'}
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
    { "name": "section_heading", "type": "string", "required": true, "description": "Section title" },
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
  "description": "Format for section data output from LLM actions",
  "fields": [
    { "name": "section_heading", "type": "string", "required": true, "description": "Updated section title" },
    { "name": "section_content", "type": "string", "required": true, "description": "Generated section content" },
    { "name": "section_elements", "type": "array", "required": false, "description": "Generated facts/ideas for the section" }
  ],
  "format_type": "output",
  "llm_instructions": "Provide updated section information including title, content, and associated elements."
}
```

## Migration and Deployment

### Implementation Phases

#### Phase 1: Basic Synchronization (Immediate)
1. **Database Triggers**: Implement primary sync trigger (post_development → post_section)
2. **Manual Sync API**: Add `/api/workflow/posts/{post_id}/sync-sections` endpoint
3. **Documentation**: Update all relevant documentation
4. **Testing**: Test with existing data

#### Phase 2: Enhanced Synchronization (Next)
1. **Secondary Triggers**: Add post_section → post_development sync triggers
2. **Format Standardization**: Migrate to standardized JSON format
3. **Error Handling**: Add comprehensive error handling and logging
4. **Validation**: Add data validation for sync operations

#### Phase 3: Advanced Features (Future)
1. **Conflict Resolution**: Handle sync conflicts between fields
2. **Performance Optimization**: Optimize sync performance for large datasets
3. **Monitoring**: Add sync monitoring and alerting
4. **Rollback Capability**: Add ability to rollback sync operations

### Migration Scripts

#### Data Format Migration
```sql
-- Migrate existing section_headings to standardized JSON format
UPDATE post_development 
SET section_headings = (
    SELECT json_agg(
        json_build_object(
            'order', s.section_order,
            'heading', s.section_heading,
            'description', COALESCE(s.section_description, ''),
            'status', COALESCE(s.status, 'draft')
        )
    )
    FROM post_section s 
    WHERE s.post_id = post_development.post_id
    ORDER BY s.section_order
)
WHERE section_headings IS NULL OR section_headings = '';
```

#### Validation Script
```sql
-- Validate sync consistency
SELECT 
    pd.post_id,
    pd.section_headings,
    COUNT(ps.id) as section_count,
    CASE 
        WHEN pd.section_headings IS NULL THEN 'No master data'
        WHEN COUNT(ps.id) = 0 THEN 'No sections'
        WHEN json_array_length(pd.section_headings::json) != COUNT(ps.id) THEN 'Count mismatch'
        ELSE 'OK'
    END as sync_status
FROM post_development pd
LEFT JOIN post_section ps ON pd.post_id = ps.post_id
GROUP BY pd.post_id, pd.section_headings
HAVING COUNT(ps.id) > 0 OR pd.section_headings IS NOT NULL;
```

### Testing Strategy

#### Unit Tests
```python
def test_sync_section_headings_to_sections():
    """Test synchronization from post_development to post_section"""
    # Test data
    post_id = 1
    section_headings = json.dumps([
        {"order": 1, "heading": "Intro", "description": "Overview"},
        {"order": 2, "heading": "Main", "description": "Content"}
    ])
    
    # Execute sync
    sync_section_headings_to_sections(post_id, section_headings)
    
    # Verify results
    sections = get_post_sections(post_id)
    assert len(sections) == 2
    assert sections[0].section_heading == "Intro"
    assert sections[1].section_heading == "Main"

def test_sync_sections_to_section_headings():
    """Test synchronization from post_section to post_development"""
    # Test data
    post_id = 1
    create_test_sections(post_id)
    
    # Execute sync
    sync_sections_to_section_headings(post_id)
    
    # Verify results
    post_dev = get_post_development(post_id)
    section_headings = json.loads(post_dev.section_headings)
    assert len(section_headings) == 2
    assert section_headings[0]["heading"] == "Test Section 1"
```

#### Integration Tests
```python
def test_sync_api_endpoint():
    """Test the manual sync API endpoint"""
    response = client.post(f'/api/workflow/posts/1/sync-sections', 
                          json={'direction': 'both'})
    assert response.status_code == 200
    assert response.json['status'] == 'success'

def test_database_triggers():
    """Test database trigger synchronization"""
    # Update post_development.section_headings
    update_post_development(1, {'section_headings': '["New Section"]'})
    
    # Verify post_section was automatically updated
    sections = get_post_sections(1)
    assert len(sections) == 1
    assert sections[0].section_heading == "New Section"
```

## Troubleshooting

### Common Issues

#### 1. Sync Not Working
**Symptoms**: Changes to post_development.section_headings don't appear in post_section
**Causes**: 
- Database triggers not installed
- Invalid JSON format in section_headings
- Database connection issues

**Solutions**:
```bash
# Check if triggers exist
psql -d blog -c "\d+ post_development"

# Test manual sync
curl -X POST "http://localhost:5000/api/workflow/posts/1/sync-sections" \
  -H "Content-Type: application/json" \
  -d '{"direction": "to_sections"}'

# Check JSON format
psql -d blog -c "SELECT post_id, section_headings FROM post_development WHERE post_id = 1;"
```

#### 2. Data Inconsistency
**Symptoms**: post_development and post_section have different section data
**Causes**:
- Manual updates bypassing sync
- Sync errors not handled properly
- Concurrent updates

**Solutions**:
```bash
# Force sync both directions
curl -X POST "http://localhost:5000/api/workflow/posts/1/sync-sections" \
  -H "Content-Type: application/json" \
  -d '{"direction": "both"}'

# Check data consistency
psql -d blog -c "
SELECT 
    pd.post_id,
    pd.section_headings,
    COUNT(ps.id) as section_count
FROM post_development pd
LEFT JOIN post_section ps ON pd.post_id = ps.post_id
WHERE pd.post_id = 1
GROUP BY pd.post_id, pd.section_headings;
"
```

#### 3. Performance Issues
**Symptoms**: Slow sync operations with large datasets
**Causes**:
- Inefficient database queries
- Large JSON parsing overhead
- Missing indexes

**Solutions**:
```sql
-- Add performance indexes
CREATE INDEX CONCURRENTLY idx_post_section_post_order 
ON post_section(post_id, section_order);

CREATE INDEX CONCURRENTLY idx_post_development_section_headings 
ON post_development USING GIN ((section_headings::jsonb));

-- Optimize sync function
-- (Add batch processing for large datasets)
```

### Monitoring and Logging

#### Database Logging
```sql
-- Enable trigger logging
CREATE OR REPLACE FUNCTION log_sync_operations()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO sync_log (
        operation_type, 
        post_id, 
        old_data, 
        new_data, 
        timestamp
    ) VALUES (
        TG_OP,
        COALESCE(NEW.post_id, OLD.post_id),
        OLD.section_headings,
        NEW.section_headings,
        CURRENT_TIMESTAMP
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
```

#### Application Logging
```python
import logging

logger = logging.getLogger(__name__)

def sync_section_headings_to_sections(post_id: int, section_headings_json: str):
    """Parse section_headings from post_development and sync to post_section records"""
    logger.info(f"Starting sync for post {post_id}")
    
    try:
        # ... sync logic ...
        logger.info(f"Sync completed successfully for post {post_id}")
    except Exception as e:
        logger.error(f"Sync failed for post {post_id}: {e}")
        raise
```

## Best Practices

### Data Management
1. **Always use post_development.section_headings as the master source**
2. **Let automatic sync handle post_section updates**
3. **Use manual sync only for troubleshooting or bulk operations**
4. **Validate JSON format before updates**

### Performance
1. **Batch large sync operations**
2. **Use database indexes for sync queries**
3. **Monitor sync performance with large datasets**
4. **Consider async processing for non-critical syncs**

### Error Handling
1. **Always wrap sync operations in try-catch blocks**
2. **Log sync errors for debugging**
3. **Provide fallback mechanisms for sync failures**
4. **Validate data before and after sync operations**

### Testing
1. **Test sync with various data formats**
2. **Test concurrent updates**
3. **Test sync with large datasets**
4. **Test sync error conditions**

This comprehensive documentation provides a complete guide to the section synchronization system, including implementation details, API endpoints, troubleshooting, and best practices. 

## LLM Processing in Writing Stage

### Section Selection Requirements
- **Single Section**: Process only the selected section
- **Multiple Sections**: Process each selected section sequentially
- **No Selection**: Process first section by default
- **All Selected**: Process all sections in order

### Processing Logic
- **Input**: Section-specific data + post context
- **Output**: Save to specific section record(s)
- **Scope**: Never update all sections unless explicitly requested
- **Isolation**: Section-level changes do not affect post-level planning data

### Current Implementation Issues
- **Problem**: LLM output is saved to ALL sections for a post
- **Root Cause**: `save_output()` function uses `WHERE post_id = %s` for all tables
- **Impact**: Violates section-specific processing principle
- **Fix Required**: Modify output saving to target specific section IDs

### Required Changes
1. **Modify `save_output()` function** to accept section selection
2. **Update LLM processor** to handle section-specific processing
3. **Add section selection logic** to Writing stage LLM actions
4. **Maintain backward compatibility** for Planning stage (post-focused)

### Implementation Status
✅ **COMPLETED**: Separate functions created for Writing stage processing

#### **New Writing Stage Functions**
- `save_section_output()`: Saves LLM output to specific sections only
- `process_writing_step()`: Processes Writing stage steps with section selection

#### **Planning Stage Functions (Unchanged)**
- `save_output()`: Remains unchanged for Planning stage
- `process_step()`: Remains unchanged for Planning stage

#### **Function Usage**
- **Planning stage**: Uses `process_step()` → `save_output()`
- **Writing stage**: Uses `process_writing_step()` → `save_section_output()`

#### **Next Steps**
1. **Update LLM endpoint** to accept section selection parameter
2. **Add section selection UI** to Writing stage
3. **Test section-specific processing** with new functions 