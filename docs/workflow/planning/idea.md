# Idea Planning Stage

## Purpose

The Idea Planning stage is responsible for developing the initial concept and basic idea for a blog post. This stage focuses on defining the core concept, target audience, and value proposition that will guide the entire content creation process.

## Page URL
```
http://localhost:5000/workflow/idea/?post_id=<id>
```

## How It Works

### Data Flow Overview
1. **Input Collection**
   - The stage takes three key inputs:
     - `basic_idea`: The core concept and main idea for the post
     - `provisional_title`: A working title that reflects the main idea
     - `idea_scope`: The boundaries and focus of the content

2. **Idea Development**
   - When you save the idea, the system:
     - Validates that all required fields are filled
     - Ensures the idea is clear and focused
     - Checks that the title aligns with the idea
     - Verifies the scope is well-defined

3. **Output Generation**
   - The final idea is saved as:
     - `post_development.basic_idea`: The core concept
     - `post_development.provisional_title`: The working title
     - `post_development.idea_scope`: The content boundaries
     - `post_development.current_stage`: Set to 'idea'
     - `post_development.current_substage`: Set to 'plan'

## Page Components

### Inputs Panel
```html
<!-- templates/workflow/planning/idea/index.html -->
<div class="panel bg-gray-800 dark:bg-[#23293a] rounded-lg p-6">
    <h2 class="text-lg font-bold mb-2 text-gray-800 dark:text-gray-200">Inputs</h2>
    <div class="mb-2">
        <label class="block font-semibold text-gray-700 dark:text-gray-200">Basic Idea</label>
        <textarea class="input w-full bg-gray-900 dark:bg-[#181c23] text-gray-200 placeholder-gray-400 border border-gray-700" rows="3"></textarea>
    </div>
    <div class="mb-2">
        <label class="block font-semibold text-gray-700 dark:text-gray-200">Provisional Title</label>
        <input type="text" class="input w-full bg-gray-900 dark:bg-[#181c23] text-gray-200 placeholder-gray-400 border border-gray-700" />
    </div>
    <div class="mb-2">
        <label class="block font-semibold text-gray-700 dark:text-gray-200">Idea Scope</label>
        <textarea class="input w-full bg-gray-900 dark:bg-[#181c23] text-gray-200 placeholder-gray-400 border border-gray-700" rows="2"></textarea>
    </div>
</div>
```

### Component References
- **Basic Idea Textarea**
  - Field: `post_development.basic_idea`
  - Used in: `app/static/js/workflow/idea_stage.js:saveIdea()`
  - Event handler: `app/static/js/workflow/idea_stage.js:handleIdeaChange()`
  - Source: `workflow_field_mapping` table (id: 1, stage_id: 1, substage_id: 1, order_index: 1)

- **Provisional Title Input**
  - Field: `post_development.provisional_title`
  - Used in: `app/static/js/workflow/idea_stage.js:saveIdea()`
  - Event handler: `app/static/js/workflow/idea_stage.js:handleTitleChange()`
  - Source: `workflow_field_mapping` table (id: 2, stage_id: 1, substage_id: 1, order_index: 2)

- **Idea Scope Textarea**
  - Field: `post_development.idea_scope`
  - Used in: `app/static/js/workflow/idea_stage.js:saveIdea()`
  - Event handler: `app/static/js/workflow/idea_stage.js:handleScopeChange()`
  - Source: `workflow_field_mapping` table (id: 3, stage_id: 1, substage_id: 1, order_index: 3)

## User Flows

### 1. Initial Load
1. Page loads with existing post data
2. Input fields are pre-populated from:
   - `post_development.basic_idea`
   - `post_development.provisional_title`
   - `post_development.idea_scope`
3. Validation state is checked
4. Save button is enabled/disabled based on validation

### 2. Idea Development
1. Enter/edit the basic idea
2. Create/edit the provisional title
3. Define the idea scope
4. System validates:
   - Basic idea is not empty
   - Title is not empty
   - Scope is well-defined

### 3. Saving Idea
1. Click "Save Idea"
2. System:
   - Validates all required fields
   - Updates `post_development` table
   - Sets current stage/substage
   - Shows success/error message

## API Endpoints

### Main Idea Planning Endpoint
```python
# app/api/routes.py
POST /api/v1/idea/save
Content-Type: application/json

Request Body:
{
    "basic_idea": string,      # From post_development.basic_idea
    "provisional_title": string, # From post_development.provisional_title
    "idea_scope": string       # From post_development.idea_scope
}

Response:
{
    "status": "success",
    "message": "Idea saved successfully"
}
```

## Database Fields

### post_development Table
```sql
-- Used in: app/static/js/workflow/idea_stage.js:saveIdea()
id: integer (PRIMARY KEY)  -- From URL parameter post_id
basic_idea: text          -- From textarea (first)
provisional_title: text    -- From input[type="text"]
idea_scope: text          -- From textarea (second)
current_stage: text       -- Set to 'idea' when entering this stage
current_substage: text    -- Set to 'plan' when entering this stage
```

## JavaScript Functions

### Idea Panel
```javascript
// app/static/js/workflow/idea_stage.js
async function saveIdea(idea, title, scope) {
  const resp = await fetch('/api/v1/idea/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      basic_idea: idea, 
      provisional_title: title, 
      idea_scope: scope 
    })
  });
  return await resp.json();
}

// Event handlers for input changes
document.addEventListener('DOMContentLoaded', async () => {
  const ideaTextarea = document.querySelectorAll('textarea')[0];
  const titleInput = document.querySelector('input[type="text"]');
  const scopeTextarea = document.querySelectorAll('textarea')[1];
  
  // Load existing data
  const dev = await fetchPostDevelopment(postId);
  if (dev) {
    if (ideaTextarea && dev.basic_idea) ideaTextarea.value = dev.basic_idea;
    if (titleInput && dev.provisional_title) titleInput.value = dev.provisional_title;
    if (scopeTextarea && dev.idea_scope) scopeTextarea.value = dev.idea_scope;
  }
});
```

## Error Handling

### HTTP Status Codes
```python
# app/api/routes.py:save_idea()
400: Bad Request - Invalid input data  # Used in app/static/js/workflow/idea_stage.js:handleError()
404: Not Found - Post not found        # Used in app/static/js/workflow/idea_stage.js:handleError()
500: Internal Server Error             # Used in app/static/js/workflow/idea_stage.js:handleError()
```

### Error Response Format
```json
{
    "error": "string",
    "details": "string"
}
``` 