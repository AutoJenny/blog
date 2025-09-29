# Phase 1: Research & Understanding - COMPLETED

## Current State Analysis - COMPLETED

### Base Template Structure
- Uses `{% block scripts %}` for JavaScript (not `{% block extra_js %}`)
- Standard Flask/Jinja2 template inheritance

### Current LLM Functionality - Both Pages

#### Ideas Page (`/planning/posts/60/calendar/ideas`)
**LLM Components:**
1. **Prompt Display Section**
   - HTML: `<div class="prompt-display">` with `h4`, `llm-provider-info`, `llm-prompt-display`
   - CSS: `.prompt-display`, `.llm-provider-info`, `.prompt-content`
   - JS: `displayLLMPrompt()`, `displayLLMConfig()`, `displayLLMPromptError()`

2. **Results Display Section**
   - HTML: `<div class="expanded-idea-display">` with header and content
   - CSS: `.expanded-idea-display`, `.expanded-idea-header`
   - JS: `displayExpandedIdea()`, `generateExpandedIdea()`

#### Brainstorm Page (`/planning/posts/60/concept/brainstorm`)
**LLM Components:**
1. **Prompt Display Section**
   - HTML: `<div class="prompt-display">` with header, actions, `llm-provider-info`, `llm-prompt-display`
   - CSS: `.prompt-display`, `.prompt-header`, `.prompt-actions`, `.llm-provider-info`, `.prompt-content`
   - JS: `displayLLMPrompt()`, `displayLLMConfig()`, `displayLLMPromptError()`
   - **Additional**: Edit functionality with `togglePromptEdit()`, `savePrompt()`, `cancelPromptEdit()`

2. **Results Display Section**
   - HTML: `<div class="topics-display">` with header and content
   - CSS: `.topics-display`, `.topics-header`
   - JS: `displayTopics()`, `startBrainstorming()`, `regenerateTopics()`

### API Endpoints - VERIFIED WORKING
- `GET /planning/api/llm/prompts/idea-expansion` ✅
- `GET /planning/api/llm/prompts/topic-brainstorming` ✅
- `POST /planning/api/posts/{id}/expanded-idea` ✅
- `POST /planning/api/brainstorm/topics` ✅

### Key Differences Between Pages
1. **Edit Functionality**: Brainstorm page has prompt editing, Ideas page doesn't
2. **Results Display**: Different CSS classes and structure
3. **Generation Functions**: Different API endpoints and data handling

## Phase 2: Design & Planning

### Shared Component Architecture

#### 1. HTML Template (`templates/includes/llm_module.html`)
```html
<div class="llm-module">
    <div class="llm-prompt-panel">
        <div class="prompt-header">
            <h4>LLM Prompt in Use</h4>
            <div class="prompt-actions" id="prompt-actions">
                <!-- Edit buttons will be conditionally shown -->
            </div>
        </div>
        <div id="llm-provider-info" class="llm-provider-info">
            <!-- Provider info -->
        </div>
        <div id="llm-prompt-display" class="llm-prompt-display">
            <!-- Prompt content -->
        </div>
        <div id="llm-prompt-edit" class="llm-prompt-edit" style="display: none;">
            <!-- Edit form -->
        </div>
    </div>
    
    <div class="llm-results-panel">
        <div class="results-header">
            <h4 id="results-title">Generated Results</h4>
            <button class="btn btn-primary" id="generate-btn">
                <i class="fas fa-magic"></i> Generate
            </button>
        </div>
        <div id="llm-results-display" class="llm-results-display">
            <!-- Results content -->
        </div>
    </div>
</div>
```

#### 2. CSS File (`static/css/llm-module.css`)
- All LLM-related styles consolidated
- Responsive design
- Consistent styling across pages

#### 3. JavaScript Module (`static/js/llm-module.js`)
```javascript
class LLMModule {
    constructor(config) {
        this.config = config;
        this.currentPrompt = null;
        this.isEditing = false;
    }
    
    // Core methods
    loadPrompt()
    displayPrompt()
    displayConfig()
    toggleEdit()
    savePrompt()
    generateContent()
    displayResults()
    handleError()
}
```

### Configuration System
```javascript
const LLM_CONFIGS = {
    'ideas': {
        promptEndpoint: '/planning/api/llm/prompts/idea-expansion',
        generateEndpoint: '/planning/api/posts/{id}/expanded-idea',
        resultsField: 'expanded_idea',
        resultsTitle: 'Expanded Idea',
        allowEdit: false
    },
    'brainstorm': {
        promptEndpoint: '/planning/api/llm/prompts/topic-brainstorming',
        generateEndpoint: '/planning/api/brainstorm/topics',
        resultsField: 'idea_scope',
        resultsTitle: 'Generated Topics',
        allowEdit: true
    }
};
```

### Integration Points
1. **Page Templates**: Include `{% include 'includes/llm_module.html' %}`
2. **Page JavaScript**: Initialize with `new LLMModule(LLM_CONFIGS['page_type'])`
3. **Page CSS**: Include `llm-module.css`

## Next Steps
1. Create shared components
2. Test with Ideas page first
3. Test with Brainstorm page
4. Verify all functionality works
