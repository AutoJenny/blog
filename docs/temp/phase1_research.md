# Phase 1: Research & Understanding

## Step 1: Base Template Analysis

### Base Template Blocks Available
From `templates/base.html`:
- `{% block title %}` - Page title
- `{% block css_assets %}` - CSS includes
- `{% block head %}` - Additional head content
- `{% block navigation %}` - Navigation content
- `{% block content %}` - Main page content
- `{% block footer %}` - Footer content
- `{% block js_assets %}` - JavaScript includes
- `{% block scripts %}` - Page-specific JavaScript

### Key Finding
- Pages should use `{% block scripts %}` for JavaScript, not `{% block extra_js %}`
- This was a critical error in the previous attempt

## Step 2: Current LLM Functionality Analysis

### Ideas Page (`/planning/posts/60/calendar/ideas`)
Current LLM components:
1. **LLM Prompt Display**
   - Shows provider info (Ollama, llama3.2:latest, temperature, max_tokens)
   - Displays prompt text with syntax highlighting
   - Edit functionality for prompt modification

2. **LLM Results Display**
   - Shows generated expanded idea
   - Loading states during generation
   - Error handling

3. **API Integration**
   - Loads prompt from `/planning/api/llm/prompts/idea-expansion`
   - Generates content via `/planning/api/posts/{id}/expanded-idea`
   - Saves results to `post_development.expanded_idea`

### Brainstorm Page (`/planning/posts/60/concept/brainstorm`)
Current LLM components:
1. **LLM Prompt Display**
   - Shows provider info (Ollama, llama3.2:latest, temperature, max_tokens)
   - Displays prompt text with syntax highlighting
   - Edit functionality for prompt modification

2. **LLM Results Display**
   - Shows generated topics
   - Loading states during generation
   - Error handling

3. **API Integration**
   - Loads prompt from `/planning/api/llm/prompts/topic-brainstorming`
   - Generates content via `/planning/api/brainstorm/topics`
   - Saves results to `post_development.idea_scope`

## Step 3: API Endpoint Analysis

### Prompt Loading Endpoints
- `GET /planning/api/llm/prompts/idea-expansion` - Returns prompt + LLM config
- `GET /planning/api/llm/prompts/topic-brainstorming` - Returns prompt + LLM config

### Content Generation Endpoints
- `POST /planning/api/posts/{id}/expanded-idea` - Generates expanded idea
- `POST /planning/api/brainstorm/topics` - Generates brainstorm topics

### Response Format
Both prompt endpoints return:
```json
{
  "success": true,
  "prompt": {
    "id": 57,
    "name": "Scottish Idea Expansion",
    "prompt_text": "...",
    "system_prompt": null
  },
  "llm_config": {
    "provider": "Ollama",
    "model": "llama3.2:latest",
    "temperature": 0.7,
    "max_tokens": 2000,
    "timeout": 60
  }
}
```

## Step 4: Current Functionality Test

### Test Ideas Page
- [ ] Page loads correctly
- [ ] LLM prompt displays correctly
- [ ] Provider info shows correctly
- [ ] Edit functionality works
- [ ] Generate functionality works
- [ ] Results display correctly

### Test Brainstorm Page
- [ ] Page loads correctly
- [ ] LLM prompt displays correctly
- [ ] Provider info shows correctly
- [ ] Edit functionality works
- [ ] Generate functionality works
- [ ] Results display correctly

## Next Steps
1. Test current functionality thoroughly
2. Document exact HTML/CSS/JS structure
3. Design shared component architecture
4. Plan implementation steps
