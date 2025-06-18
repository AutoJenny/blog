# Structure Stage

## Overview
The Structure stage is responsible for organizing the post's content into a logical sequence of sections. It takes the basic idea and interesting facts from the Research stage and creates a coherent structure for the article.

## Data Flow
1. Inputs from Research stage:
   - Title (from post table)
   - Basic idea (from post_development table)
   - Interesting facts (from post_development table)

2. Output to post_section table:
   - section_heading: The title of the section
   - section_description: A brief description of what the section will cover
   - section_order: The sequence number of the section

3. Output to post_section_elements table:
   - post_id: Reference to the post
   - section_id: Reference to the section
   - element_type: Type of element ('fact', 'idea', 'theme')
   - element_text: The actual content
   - element_order: Order within the section

## UI Components

### Inputs Panel
- Title field (read-only from post table)
- Basic idea textarea (from post_development)
- Interesting facts textarea (from post_development)

### LLM Action Panel
- "Generate Structure" button that triggers section generation

### Output Panel
- List of generated sections, each showing:
  - Section heading
  - Section description
  - Assigned elements (facts, ideas, themes)
- Sections are draggable for reordering
- Elements can be dragged between sections

### Save Panel
- "Save Structure" button to persist the sections and their elements to the database

## API Endpoints

### POST /api/v1/structure/generate
Generates a section structure using Ollama.

**Request Body:**
```json
{
  "title": "Post Title",
  "idea": "Basic idea text",
  "facts": ["Fact 1", "Fact 2", "Fact 3"]
}
```

**Response:**
```json
{
  "sections": [
    {
      "heading": "Section Title",
      "description": "Section description",
      "elements": [
        {
          "type": "fact",
          "text": "Fact 1"
        },
        {
          "type": "idea",
          "text": "Idea 1"
        }
      ]
    }
  ]
}
```

### POST /api/v1/structure/save/<post_id>
Saves the generated structure to the database.

**Request Body:**
```json
{
  "sections": [
    {
      "heading": "Section Title",
      "description": "Section description",
      "elements": [
        {
          "type": "fact",
          "text": "Fact 1"
        }
      ]
    }
  ]
}
```

**Response:**
```json
{
  "message": "Structure saved successfully",
  "sections": [...]
}
```

## JavaScript Functions

### planSectionsLLM(inputs)
- Takes title, idea, and facts as input
- Calls Ollama to generate section structure
- Returns array of sections with headings, descriptions, and elements

### renderSections(list, sections)
- Renders sections in the UI
- Each section shows heading, description, and assigned elements
- Supports drag-and-drop reordering of sections and elements

### saveStructure(sections)
- Saves the current section structure to the database
- Updates post_section table with new sections
- Updates post_section_elements table with assigned elements

## Error Handling
- 400: Bad Request - Invalid input data
- 404: Not Found - Post not found
- 500: Internal Server Error

## Database Schema

### post_section
- id: SERIAL PRIMARY KEY
- post_id: INTEGER REFERENCES post(id)
- section_order: INTEGER
- section_heading: TEXT
- section_description: TEXT
- first_draft: TEXT
- created_at: TIMESTAMP
- updated_at: TIMESTAMP

### post_section_elements
- id: SERIAL PRIMARY KEY
- post_id: INTEGER REFERENCES post(id)
- section_id: INTEGER REFERENCES post_section(id)
- element_type: VARCHAR(50) CHECK (element_type IN ('fact', 'idea', 'theme'))
- element_text: TEXT
- element_order: INTEGER
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
- CONSTRAINT unique_element_per_section UNIQUE (post_id, section_id, element_text)

## Page URL
```
http://localhost:5000/workflow/structure/?post_id=<id>
```

## How It Works

### Data Flow Overview
1. **Input Collection**
   - The stage takes three key inputs from previous stages:
     - `provisional_title`: The working title of the post
     - `basic_idea`: The core concept from the Idea stage
     - `interesting_facts`: Verified facts from the Research stage

2. **Structure Generation**
   - When you click "Generate Structure", the LLM analyzes these inputs to:
     - Identify logical groupings of facts and ideas
     - Create section titles that reflect these groupings
     - Write brief descriptions for each section
     - Assign relevant facts and ideas to each section

3. **Structure Refinement**
   - You can then:
     - Reorder sections via drag-and-drop
     - Edit section titles and descriptions
     - Move elements (facts, ideas, themes) between sections
     - Add or remove sections as needed

4. **Final Output**
   - The final structure is saved as:
     - Section records in the `post_section` table
     - Element records in the `post_section_elements` table
     - Each section includes:
       - Title (`section_heading`)
       - Description (`section_description`)
       - Order in the post (`section_order`)
     - Each element includes:
       - Type (`element_type`)
       - Content (`element_text`)
       - Order within section (`element_order`)

## Page Components

### Inputs Panel
```html
<!-- templates/workflow/planning/structure/index.html -->
<div class="panel bg-gray-800 dark:bg-[#23293a] rounded-lg p-6">
    <h2 class="text-lg font-bold mb-2 text-gray-800 dark:text-gray-200">Inputs</h2>
    <div class="mb-2">
        <label class="block font-semibold text-gray-700 dark:text-gray-200">Title</label>
        <input type="text" class="input w-full bg-gray-900 dark:bg-[#181c23] text-gray-200 placeholder-gray-400 border border-gray-700" />
    </div>
    <div class="mb-2">
        <label class="block font-semibold text-gray-700 dark:text-gray-200">Basic Idea</label>
        <textarea class="input w-full bg-gray-900 dark:bg-[#181c23] text-gray-200 placeholder-gray-400 border border-gray-700" rows="2"></textarea>
    </div>
    <div class="mb-2">
        <label class="block font-semibold text-gray-700 dark:text-gray-200">Interesting Facts</label>
        <textarea class="input w-full bg-gray-900 dark:bg-[#181c23] text-gray-200 placeholder-gray-400 border border-gray-700" rows="3"></textarea>
    </div>
</div>
```

### Component References
- **Title Input** 
  - Field: `post_development.provisional_title`
  - Used in: `app/static/js/workflow/structure_stage.js:planStructure()`
  - Event handler: `app/static/js/workflow/structure_stage.js:handleTitleChange()`
  - Source: `workflow_field_mapping` table (id: 1, stage_id: 10, substage_id: 1, order_index: 1)

- **Basic Idea Textarea**
  - Field: `post_development.basic_idea`
  - Used in: `app/static/js/workflow/structure_stage.js:planStructure()`
  - Event handler: `app/static/js/workflow/structure_stage.js:handleIdeaChange()`
  - Source: `workflow_field_mapping` table (id: 1, stage_id: 10, substage_id: 1, order_index: 2)

- **Interesting Facts Textarea**
  - Field: `post_development.interesting_facts`
  - Used in: `app/static/js/workflow/structure_stage.js:planStructure()`
  - Event handler: `app/static/js/workflow/structure_stage.js:handleFactsChange()`
  - Source: `workflow_field_mapping` table (id: 5, stage_id: 10, substage_id: 2, order_index: 2)

### Structure Panel
```html
<!-- templates/workflow/planning/structure/index.html -->
<div class="panel bg-gray-800 dark:bg-[#23293a] rounded-lg p-6">
    <h2 class="text-lg font-bold mb-2 text-gray-800 dark:text-gray-200">Structure</h2>
    <button class="btn-primary bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
        Generate Structure
    </button>
    <div id="sections-list" class="mt-4 space-y-4"></div>
</div>
```

- **Generate Structure Button**
  - Action: `section_structure_creator`
  - Used in: `app/static/js/workflow/structure_stage.js:planStructure()`
  - Endpoint: `POST /api/v1/structure/plan`

- **Structure Display**
  - Field: `post_development.section_planning`
  - Used in: `app/static/js/workflow/structure_stage.js:renderSections()`
  - Source: `workflow_field_mapping` table (id: 7, stage_id: 10, substage_id: 3, order_index: 1)

## User Flows

### 1. Initial Load
1. Page loads with existing post data
2. Input fields are pre-populated from:
   - `post_development.provisional_title`
   - `post_development.basic_idea`
   - `post_development.interesting_facts`
3. Existing sections are displayed if any
4. Existing elements are displayed within their sections
5. Unassigned elements are shown in their panel

### 2. Planning Sections
1. Review/edit input fields
2. Click "Generate Structure"
3. LLM analyzes inputs and generates:
   - Section titles
   - Section descriptions
   - Element assignments (facts, ideas, themes)
4. Sections are displayed in a draggable list
5. Elements are displayed within their sections

### 3. Editing Sections
1. Edit section titles inline
2. Edit section descriptions
3. Drag sections to reorder
4. Drag elements between sections
5. Remove elements from sections

### 4. Managing Unassigned Elements
1. Unassigned elements appear in their panel
2. Drag elements to sections
3. Drag elements between sections

### 5. Saving Structure
1. Click "Accept Structure"
2. System:
   - Creates/updates `post_section` records
   - Updates `post_development.section_planning`
   - Validates all required fields
   - Shows success/error message

## API Endpoints

### Main Structure Planning Endpoint
```python
# app/api/routes.py
POST /api/v1/structure/plan
Content-Type: application/json

Request Body:
{
    "title": string,  # From post_development.provisional_title
    "idea": string,   # From post_development.basic_idea
    "facts": string[] # From post_development.interesting_facts
}

Response:
{
    "sections": [
        {
            "name": string,  # Stored in post_development.section_planning
            "description": string  # Stored in post_development.section_planning
        }
    ]
}
```

## Database Fields

### post_development Table
```sql
-- Used in: app/static/js/workflow/structure_stage.js:saveResearch()
id: integer (PRIMARY KEY)  -- From URL parameter post_id
provisional_title: text    -- From input[type="text"]
basic_idea: text          -- From textarea (first)
interesting_facts: text    -- From textarea (second)
section_planning: text     -- Generated by section_structure_creator
current_stage: text       -- Set to 'structure' when entering this stage
current_substage: text    -- Set to 'plan' when entering this stage
```

### post_section Table
```sql
id: integer (PRIMARY KEY)
post_id: integer (FOREIGN KEY)
section_heading: text      -- Section title
section_description: text  -- Section description
ideas_to_include: jsonb    -- Array of assigned ideas
facts_to_include: jsonb    -- Array of assigned facts
section_order: integer     -- Order in the post
```

## JavaScript Functions

### Research Panel
```javascript
// app/static/js/workflow/structure_stage.js
async function planStructure(title, idea, facts) {
  const resp = await fetch('/api/v1/structure/plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      title: title, 
      idea: idea, 
      facts: facts 
    })
  });
  return await resp.json();
}

// Event handlers for input changes
document.addEventListener('DOMContentLoaded', async () => {
  const titleInput = document.querySelector('input[type="text"]');
  const ideaTextarea = document.querySelectorAll('textarea')[0];
  const factsTextarea = document.querySelectorAll('textarea')[1];
  
  // Load existing data
  const dev = await fetchPostDevelopment(postId);
  if (dev) {
    if (titleInput && dev.provisional_title) titleInput.value = dev.provisional_title;
    if (ideaTextarea && dev.basic_idea) ideaTextarea.value = dev.basic_idea;
    if (factsTextarea && dev.interesting_facts) factsTextarea.value = dev.interesting_facts;
  }
});
```

## Error Handling

### HTTP Status Codes
```python
# app/api/routes.py:plan_structure()
400: Bad Request - Invalid input data  # Used in app/static/js/workflow/structure_stage.js:handleError()
404: Not Found - Post not found        # Used in app/static/js/workflow/structure_stage.js:handleError()
500: Internal Server Error             # Used in app/static/js/workflow/structure_stage.js:handleError()
```

### Error Response Format
```json
{
    "error": "string",
    "details": "string"
}
```

## Recent Changes

### 2024-06-14
- Updated to use universal modular LLM panel  # Changed: static/js/workflow/panels/structure_panel.js
- Added error handling for Ollama service  # Changed: app/api/llm_service.py
- Implemented retry logic for LLM calls  # Changed: app/api/llm_service.py 

## Complete Data Reference

### Database Fields

#### Input Fields (post_development table)
```sql
-- All fields used in this stage
id: integer (PRIMARY KEY)  -- From URL parameter post_id
provisional_title: text    -- From input[type="text"]
basic_idea: text          -- From textarea (first)
interesting_facts: text    -- From textarea (second)
section_planning: text     -- Generated by section_structure_creator
current_stage: text       -- Set to 'structure' when entering this stage
current_substage: text    -- Set to 'plan' when entering this stage
```

### API Endpoints

#### GET /workflow/structure/
```python
# app/api/routes.py:structure_stage()
# Used by: templates/workflow/structure.html

Query Parameters:
- post_id: integer (required)  # Used to fetch post_development record

Response:
- HTML page with structure planning interface
- Includes post data from post_development table
```

#### POST /api/v1/structure/plan
```python
# app/api/routes.py:plan_structure()
# Used by: static/js/workflow/panels/structure_panel.js:generateStructure()

Request Body:
{
    "title": string,  # From post_development.provisional_title
    "idea": string,   # From post_development.basic_idea
    "facts": string[] # From post_development.interesting_facts
}

Response:
{
    "sections": [
        {
            "name": string,  # Stored in post_development.section_planning
            "description": string  # Stored in post_development.section_planning
        }
    ]
}
```

#### POST /api/v1/workflow/update_stage
```python
# app/api/routes.py:update_workflow_stage()
# Used by: static/js/workflow/panels/structure_panel.js:handleStageChange()

Request Body:
{
    "post_id": integer,  # From URL parameter
    "stage": "structure"  # Fixed value for this page
}

Response:
{
    "success": boolean,
    "current_stage": string  # Updated post_development.current_stage
}
```

#### POST /api/v1/workflow/update_substage
```python
# app/api/routes.py:update_workflow_substage()
# Used by: static/js/workflow/panels/structure_panel.js:handleSubstageChange()

Request Body:
{
    "post_id": integer,  # From URL parameter
    "substage": "plan"  # Fixed value for this page
}

Response:
{
    "success": boolean,
    "current_substage": string  # Updated post_development.current_substage
}
```

### UI Components and Their Data Bindings

#### Input Fields
```html
<!-- templates/workflow/structure.html -->
<input type="text" id="title" name="title" 
       value="{{ post.title }}"  <!-- From post_development.provisional_title -->
       data-field="title"        <!-- Used in updateField() -->
       data-table="post_development">

<textarea id="idea" name="idea"
          data-field="idea"      <!-- Used in updateField() -->
          data-table="post_development">{{ post.basic_idea }}</textarea>  <!-- From post_development.basic_idea -->

<textarea id="facts" name="facts"
          data-field="facts"     <!-- Used in updateField() -->
          data-table="post_development">{{ post.interesting_facts }}</textarea>  <!-- From post_development.interesting_facts -->
```

#### Structure Display
```html
<!-- templates/workflow/components/structure_display.html -->
<div id="structure-display">
    {% for section in post.section_planning.sections %}  <!-- From post_development.section_planning -->
    <div class="section">
        <h3>{{ section.name }}</h3>  <!-- From post_development.section_planning.sections[].name -->
        <p>{{ section.description }}</p>  <!-- From post_development.section_planning.sections[].description -->
    </div>
    {% endfor %}
</div>
```

### JavaScript Event Handlers and Their Data Flow

```javascript
// static/js/workflow/panels/structure_panel.js

// Input change handlers
document.getElementById('title').addEventListener('change', (e) => {
    // Updates post_development.provisional_title
    updateField('title', e.target.value);
});

document.getElementById('idea').addEventListener('change', (e) => {
    // Updates post_development.basic_idea
    updateField('idea', e.target.value);
});

document.getElementById('facts').addEventListener('change', (e) => {
    // Updates post_development.interesting_facts
    updateField('facts', JSON.parse(e.target.value));
});

// Generate structure handler
document.getElementById('generate-structure').addEventListener('click', async () => {
    // Calls POST /api/v1/structure/plan
    // Updates post_development.section_planning
    const result = await generateStructure();
    updateStructureDisplay(result.sections);
});
```

### Database Queries Used

```sql
-- app/api/db.py:get_post_development()
-- Used in: app/api/routes.py:structure_stage()
SELECT id, provisional_title, basic_idea, interesting_facts, section_planning, current_stage, current_substage
FROM post_development
WHERE id = %s

-- app/api/db.py:update_post_development()
-- Used in: static/js/workflow/panels/structure_panel.js:updateField()
UPDATE post_development
SET {field} = %s,
    updated_at = CURRENT_TIMESTAMP
WHERE id = %s

-- app/api/db.py:update_post_structure()
-- Used in: app/api/routes.py:plan_structure()
UPDATE post_development
SET section_planning = %s,
    updated_at = CURRENT_TIMESTAMP
WHERE id = %s

-- app/api/db.py:update_workflow_stage()
-- Used in: static/js/workflow/panels/structure_panel.js:handleStageChange()
UPDATE post_development
SET current_stage = %s,
    updated_at = CURRENT_TIMESTAMP
WHERE id = %s

-- app/api/db.py:update_workflow_substage()
-- Used in: static/js/workflow/panels/structure_panel.js:handleSubstageChange()
UPDATE post_development
SET current_substage = %s,
    updated_at = CURRENT_TIMESTAMP
WHERE id = %s
``` 