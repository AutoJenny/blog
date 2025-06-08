# Idea Planning Stage

## Purpose

The Idea Planning stage is responsible for developing the initial concept and basic idea for the blog post. This stage focuses on defining the core concept, target audience, and value proposition that will guide the content creation process.

## Page URL
```
http://localhost:5000/workflow/idea/?post_id=<id>
```

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
  - Event handler: `app/static/js/workflow/idea_stage.js:handleBasicIdeaChange()`
  - Source: `workflow_field_mapping` table (id: 1, stage_id: 10, substage_id: 1, order_index: 1)

- **Provisional Title Input**
  - Field: `post_development.provisional_title`
  - Used in: `app/static/js/workflow/idea_stage.js:saveIdea()`
  - Event handler: `app/static/js/workflow/idea_stage.js:handleTitleChange()`
  - Source: `workflow_field_mapping` table (id: 2, stage_id: 10, substage_id: 1, order_index: 2)

- **Idea Scope Textarea**
  - Field: `post_development.idea_scope`
  - Used in: `app/static/js/workflow/idea_stage.js:saveIdea()`
  - Event handler: `app/static/js/workflow/idea_stage.js:handleScopeChange()`
  - Source: `workflow_field_mapping` table (id: 3, stage_id: 10, substage_id: 1, order_index: 3)

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
```

## JavaScript Functions

### Idea Panel
```javascript
// app/static/js/workflow/idea_stage.js
async function saveIdea(basicIdea, title, scope) {
  const resp = await fetch('/api/v1/idea/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ basic_idea: basicIdea, provisional_title: title, idea_scope: scope })
  });
  return await resp.json();
}

// Event handlers for input changes
document.addEventListener('DOMContentLoaded', async () => {
  const basicIdeaTextarea = document.querySelectorAll('textarea')[0];
  const titleInput = document.querySelector('input[type="text"]');
  const scopeTextarea = document.querySelectorAll('textarea')[1];
  
  // Load existing data
  const dev = await fetchPostDevelopment(postId);
  if (dev) {
    if (basicIdeaTextarea && dev.basic_idea) basicIdeaTextarea.value = dev.basic_idea;
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