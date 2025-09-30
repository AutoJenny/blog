# LLM Module Refactoring - Comprehensive Audit & Implementation Plan

## 🚨 CRITICAL CONDITIONS
- **NO CODING WITHOUT EXPLICIT CONSENT**
- **ASK BEFORE ANY CHANGES**
- **VERIFY EVERY DEPENDENCY**
- **MAINTAIN 100% BACKWARD COMPATIBILITY**

## 📊 CURRENT STATE ANALYSIS

### Files Involved
**Core LLM Files:**
- `static/js/llm-module.js` (538 lines, 25 methods)
- `static/js/llm-config.js` (83 lines)
- `static/js/llm-utils.js` (112 lines)

**Templates Using LLM Module (6 files):**
- `templates/authoring/sections/drafting.html`
- `templates/planning/calendar/ideas.html`
- `templates/planning/concept/brainstorm.html`
- `templates/planning/concept/grouping.html`
- `templates/planning/concept/sections.html`
- `templates/planning/concept/titling.html`

**Shared Template:**
- `templates/includes/llm_module.html`

### 🔍 DEPENDENCY ANALYSIS

#### 1. Function Dependencies
**Global Functions Called:**
- `initializeLLMModule()` - Called in 6 templates
- `toggleLLMAccordion()` - Called in 3 templates + shared template
- `escapeHtml()` - Called internally in LLMModule class

**Class Methods Used Externally:**
- `llmModule.generateContent()` - Overridden in 5 templates
- `llmModule.config.generateEndpoint` - Accessed in 1 template

#### 2. API Endpoints Used
**Planning Endpoints:**
- `/planning/api/llm/prompts/idea-expansion`
- `/planning/api/llm/prompts/topic-brainstorming`
- `/planning/api/llm/prompts/section-planning`
- `/planning/api/llm/prompts/section-titling`
- `/planning/api/posts/{id}/expanded-idea`
- `/planning/api/brainstorm/topics`
- `/planning/api/sections/group`
- `/planning/api/sections/title`
- `/planning/api/sections/plan`

**Authoring Endpoints:**
- `/authoring/api/llm/prompts/section-drafting`
- `/authoring/api/posts/{id}/sections/{section_id}/generate`
- `/authoring/api/posts/{id}/sections/{section_id}` (PUT for auto-save)

#### 3. DOM Element Dependencies
**Required DOM Elements:**
- `generate-btn`
- `llm-results-display`
- `llm-prompt-display`
- `llm-provider-info`
- `llm-accordion-content`
- `accordion-icon`
- `prompt-actions`
- `edit-prompt-btn`
- `save-prompt-btn`
- `cancel-prompt-btn`
- `system-prompt-edit`
- `user-prompt-edit`
- `content-editor`
- `word-count`
- `save-btn`
- `last-saved`
- `results-title`

### 🎯 PROPOSED REFACTORING STRUCTURE

#### Current Method Classification:
**Core/Orchestration (Keep in main class):**
- `constructor()`
- `init()`
- `setPostId()`
- `generateContent()`

**UI Management (Extract to llm-ui-manager.js):**
- `displayPrompt()`
- `displayConfig()`
- `displayError()`
- `displayResults()`
- `displayArrayResults()`
- `displayObjectResults()`
- `displayTopics()`
- `displayGroups()`
- `displaySections()`
- `displayAuthoringResults()` (both instances)
- `toggleAccordion()`

**API Management (Extract to llm-api-client.js):**
- `loadPrompt()`
- `savePrompt()`
- `autoSaveContent()`

**Edit Management (Extract to llm-edit-manager.js):**
- `setupEditButtons()`
- `toggleEdit()`
- `cancelEdit()`

**Utilities (Already extracted):**
- `escapeHtml()`
- `isCurrentSection()`

### ⚠️ CRITICAL RISKS IDENTIFIED

#### 1. Template Method Overrides
**HIGH RISK:** 5 templates override `generateContent()` method:
```javascript
const originalGenerateContent = llmModule.generateContent.bind(llmModule);
llmModule.generateContent = async function() { ... }
```
**Impact:** Any change to method structure breaks these overrides.

#### 2. Direct Property Access
**MEDIUM RISK:** Templates access `llmModule.config.generateEndpoint`:
```javascript
llmModule.config.generateEndpoint = `/authoring/api/posts/${window.postId}/sections/${sectionId}/generate`;
```
**Impact:** Config structure changes break this access.

#### 3. Global Function Dependencies
**MEDIUM RISK:** Templates call global functions:
- `initializeLLMModule()`
- `toggleLLMAccordion()`
**Impact:** Function signature changes break templates.

#### 4. DOM Element Dependencies
**HIGH RISK:** 17+ DOM elements must exist for module to work.
**Impact:** Missing elements cause runtime errors.

#### 5. API Endpoint Dependencies
**HIGH RISK:** 11 API endpoints must exist and return expected data.
**Impact:** Endpoint changes break functionality.

### 🛡️ SAFETY REQUIREMENTS

#### 1. Backward Compatibility
- **MUST maintain all existing method signatures**
- **MUST maintain all existing property access patterns**
- **MUST maintain all existing global function signatures**
- **MUST maintain all existing DOM element requirements**

#### 2. Testing Requirements
- **MUST test all 6 templates after each change**
- **MUST verify all API endpoints still work**
- **MUST verify all DOM interactions still work**
- **MUST verify method overrides still work**

#### 3. Rollback Strategy
- **MUST commit after each successful step**
- **MUST be able to rollback to commit `852ec117`**
- **MUST document each change for easy reversal**

### 📋 IMPLEMENTATION PLAN

#### Phase 1: Extract UI Manager (LOWEST RISK)
1. Create `llm-ui-manager.js` with display methods
2. Update main class to use UI manager
3. Test all templates
4. Commit if successful

#### Phase 2: Extract API Client (MEDIUM RISK)
1. Create `llm-api-client.js` with API methods
2. Update main class to use API client
3. Test all templates
4. Commit if successful

#### Phase 3: Extract Edit Manager (MEDIUM RISK)
1. Create `llm-edit-manager.js` with edit methods
2. Update main class to use edit manager
3. Test all templates
4. Commit if successful

#### Phase 4: Cleanup (LOW RISK)
1. Remove duplicate methods
2. Optimize imports
3. Final testing
4. Commit if successful

### ❓ QUESTIONS FOR USER APPROVAL

1. **Should I proceed with Phase 1 (UI Manager extraction)?**
2. **Should I create separate files or keep everything in one file?**
3. **Should I maintain the current method override pattern or change it?**
4. **Should I test each template individually or all at once?**
5. **Should I create a rollback script for easy reversal?**

### 🚫 WHAT I WILL NOT DO WITHOUT CONSENT

- Change any method signatures
- Change any property access patterns
- Change any global function signatures
- Remove any existing functionality
- Modify any templates
- Change any API endpoints
- Make any assumptions about user preferences

## 📝 NEXT STEPS

**WAITING FOR USER APPROVAL BEFORE PROCEEDING**

I will not make any changes until you explicitly approve:
1. The overall approach
2. The specific phase to start with
3. The testing strategy
4. Any modifications to the plan
