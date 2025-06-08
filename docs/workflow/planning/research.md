# Research Planning Stage

## Purpose

The Research Planning stage is responsible for gathering and organizing information, facts, and resources that will support the blog post's content. This stage focuses on collecting relevant data, verifying facts, and identifying key topics to cover.

## Page URL
```
http://localhost:5000/workflow/research/?post_id=<id>
```

## How It Works

### Data Flow Overview
1. **Input Collection**
   - The stage takes three key inputs:
     - `topics_to_cover`: Main topics and areas to research
     - `interesting_facts`: Verified facts and information
     - `tartans_products`: Relevant products to reference

2. **Research Organization**
   - When you save the research, the system:
     - Validates that all required fields are filled
     - Ensures topics are well-defined
     - Verifies facts are properly formatted
     - Checks product references are valid

3. **Output Generation**
   - The final research is saved as:
     - `post_development.topics_to_cover`: Research topics
     - `post_development.interesting_facts`: Verified facts
     - `post_development.tartans_products`: Product references
     - `post_development.current_stage`: Set to 'research'
     - `post_development.current_substage`: Set to 'plan'

## Page Components

### Inputs Panel
```html
<!-- templates/workflow/planning/research/index.html -->
<div class="panel bg-gray-800 dark:bg-[#23293a] rounded-lg p-6">
    <h2 class="text-lg font-bold mb-2 text-gray-800 dark:text-gray-200">Inputs</h2>
    <div class="mb-2">
        <label class="block font-semibold text-gray-700 dark:text-gray-200">Topics to Cover</label>
        <textarea class="input w-full bg-gray-900 dark:bg-[#181c23] text-gray-200 placeholder-gray-400 border border-gray-700" rows="3"></textarea>
    </div>
    <div class="mb-2">
        <label class="block font-semibold text-gray-700 dark:text-gray-200">Interesting Facts</label>
        <textarea class="input w-full bg-gray-900 dark:bg-[#181c23] text-gray-200 placeholder-gray-400 border border-gray-700" rows="3"></textarea>
    </div>
    <div class="mb-2">
        <label class="block font-semibold text-gray-700 dark:text-gray-200">Tartans Products</label>
        <textarea class="input w-full bg-gray-900 dark:bg-[#181c23] text-gray-200 placeholder-gray-400 border border-gray-700" rows="2"></textarea>
    </div>
</div>
```

### Component References
- **Topics to Cover Textarea**
  - Field: `post_development.topics_to_cover`
  - Used in: `app/static/js/workflow/research_stage.js:saveResearch()`
  - Event handler: `app/static/js/workflow/research_stage.js:handleTopicsChange()`
  - Source: `workflow_field_mapping` table (id: 4, stage_id: 2, substage_id: 1, order_index: 1)

- **Interesting Facts Textarea**
  - Field: `post_development.interesting_facts`
  - Used in: `app/static/js/workflow/research_stage.js:saveResearch()`
  - Event handler: `app/static/js/workflow/research_stage.js:handleFactsChange()`
  - Source: `workflow_field_mapping` table (id: 5, stage_id: 2, substage_id: 1, order_index: 2)

- **Tartans Products Textarea**
  - Field: `post_development.tartans_products`
  - Used in: `app/static/js/workflow/research_stage.js:saveResearch()`
  - Event handler: `app/static/js/workflow/research_stage.js:handleProductsChange()`
  - Source: `workflow_field_mapping` table (id: 6, stage_id: 2, substage_id: 1, order_index: 3)

## User Flows

### 1. Initial Load
1. Page loads with existing post data
2. Input fields are pre-populated from:
   - `post_development.topics_to_cover`
   - `post_development.interesting_facts`
   - `post_development.tartans_products`
3. Validation state is checked
4. Save button is enabled/disabled based on validation

### 2. Research Development
1. Enter/edit topics to cover
2. Add/edit interesting facts
3. List relevant products
4. System validates:
   - Topics are not empty
   - Facts are properly formatted
   - Products are valid references

### 3. Saving Research
1. Click "Save Research"
2. System:
   - Validates all required fields
   - Updates `post_development` table
   - Sets current stage/substage
   - Shows success/error message

## API Endpoints

### Main Research Planning Endpoint
```python
# app/api/routes.py
POST /api/v1/research/save
Content-Type: application/json

Request Body:
{
    "topics_to_cover": string,    # From post_development.topics_to_cover
    "interesting_facts": string,   # From post_development.interesting_facts
    "tartans_products": string    # From post_development.tartans_products
}

Response:
{
    "status": "success",
    "message": "Research saved successfully"
}
```

## Database Fields

### post_development Table
```sql
-- Used in: app/static/js/workflow/research_stage.js:saveResearch()
id: integer (PRIMARY KEY)  -- From URL parameter post_id
topics_to_cover: text     -- From textarea (first)
interesting_facts: text    -- From textarea (second)
tartans_products: text     -- From textarea (third)
current_stage: text       -- Set to 'research' when entering this stage
current_substage: text    -- Set to 'plan' when entering this stage
```

## JavaScript Functions

### Research Panel
```javascript
// app/static/js/workflow/research_stage.js
async function saveResearch(topics, facts, products) {
  const resp = await fetch('/api/v1/research/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      topics_to_cover: topics, 
      interesting_facts: facts, 
      tartans_products: products 
    })
  });
  return await resp.json();
}

// Event handlers for input changes
document.addEventListener('DOMContentLoaded', async () => {
  const topicsTextarea = document.querySelectorAll('textarea')[0];
  const factsTextarea = document.querySelectorAll('textarea')[1];
  const productsTextarea = document.querySelectorAll('textarea')[2];
  
  // Load existing data
  const dev = await fetchPostDevelopment(postId);
  if (dev) {
    if (topicsTextarea && dev.topics_to_cover) topicsTextarea.value = dev.topics_to_cover;
    if (factsTextarea && dev.interesting_facts) factsTextarea.value = dev.interesting_facts;
    if (productsTextarea && dev.tartans_products) productsTextarea.value = dev.tartans_products;
  }
});
```

## Error Handling

### HTTP Status Codes
```python
# app/api/routes.py:save_research()
400: Bad Request - Invalid input data  # Used in app/static/js/workflow/research_stage.js:handleError()
404: Not Found - Post not found        # Used in app/static/js/workflow/research_stage.js:handleError()
500: Internal Server Error             # Used in app/static/js/workflow/research_stage.js:handleError()
```

### Error Response Format
```json
{
    "error": "string",
    "details": "string"
}
``` 