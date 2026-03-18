# Post Type Settings Phase 1 - Design & Organization

**Date:** 2025-01-XX  
**Purpose:** Design the contextual settings view that shows current stage/substage settings with exploration capability.

---

## UI Placement

### Settings Icon in Post Type Header

**Location:** Right-aligned in the post_type header bar

**Visual Design:**
```
┌─────────────────────────────────────────┐
│ Post type: PROFILE          [⚙️]        │  ← Settings icon here
└─────────────────────────────────────────┘
```

**HTML Structure:**
```html
<div class="post-type-header">
    <span class="post-type-label">Post type:</span>
    <span class="post-type-value">PROFILE</span>
    <button class="post-type-settings-btn" 
            id="post-type-settings-btn"
            title="View Post Type Settings">
        <i class="fas fa-cog"></i>
    </button>
</div>
```

**CSS:**
- Icon: Small (0.7rem), subtle color (#94a3b8), hover effect
- Right-aligned with flexbox
- Spacing: 0.5rem margin-left

---

## Modal/Sidebar Structure

### Option A: Modal (Recommended for First Implementation)
- Full-screen overlay
- Centered modal (max-width: 900px)
- Easy to dismiss (click outside or X button)
- Good for detailed exploration

### Option B: Right Sidebar
- Slides in from right
- Stays open while navigating
- Better for quick reference
- More complex state management

**Recommendation:** Start with **Modal** (easier to implement, can migrate to sidebar later)

---

## Modal Layout

```
┌─────────────────────────────────────────────────────────┐
│ Post Type Settings: PROFILE                    [×]      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│ Current Context: Planning > Section Structure Design    │
│                                                           │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Navigation                                          │ │
│ │                                                     │ │
│ │ [Current: Planning > Section Structure]             │ │
│ │                                                     │ │
│ │ Explore Other Stages:                              │ │
│ │ • Calendar                                          │ │
│ │ • Planning                                           │ │
│ │   - Taxonomy                                        │ │
│ │   - Section Structure Design  ← Current            │ │
│ │   - Section Ideas                                   │ │
│ │   - Section Titling                                 │ │
│ │ • Research                                          │ │
│ │ • Authoring                                         │ │
│ │ • Imaging                                           │ │
│ │ • Header                                            │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                           │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Settings for: Planning > Section Structure Design   │ │
│ │                                                     │ │
│ │ Template:                                           │ │
│ │   planning/concept/section_structure_profile.html  │ │
│ │                                                     │ │
│ │ Action Buttons:                                      │ │
│ │   • Generate Section Structure                      │ │
│ │     Endpoint: /planning/api/profile/section-structure││
│ │     Prompt: Product Profile Section Structure       │ │
│ │                                                     │ │
│ │ Pipeline Step:                                      │ │
│ │   Step 5: Section Structure Design                 │ │
│ │   Order: 5                                          │ │
│ │   Label: Planning — Section Structure              │ │
│ │                                                     │ │
│ │ Related Steps:                                      │ │
│ │   ← Step 4: Taxonomy                               │ │
│ │   → Step 6: Section Ideas                          │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                           │
│ [Close]                                                  │
└─────────────────────────────────────────────────────────┘
```

---

## Data Organization

### Context-Aware Settings Structure

**Primary Organization:** By Stage > Substage

**For each Stage/Substage combination, show:**

1. **Template Information**
   - Template path used
   - Whether it's post_type-specific (e.g., `*_profile.html`)
   - Route function that renders it

2. **Action Button Configuration**
   - Which "Generate" buttons appear
   - Their endpoints (prompt, generate, results field)
   - Which LLM config entry they use

3. **Pipeline Step Information**
   - Step order in pipeline
   - Step label
   - JavaScript function mapping
   - Previous/next steps

4. **Panel Configuration** (if applicable)
   - Which panels appear in sidebar
   - Panel order
   - Output panel/script

5. **Navbar Configuration**
   - Whether this substage appears in navbar
   - Which post types see it
   - URL route

---

## Navigation/Exploration Mechanism

### Default View: Current Context

**On Open:**
1. Read `window.currentStage` and `window.currentSubstage`
2. Read `window.postType` (or from post_type header)
3. Display settings for that specific stage/substage combination

### Exploration: Stage/Substage Tree

**Left Panel (Navigation):**
- Hierarchical tree of all stages
- Expandable substages under each stage
- Current context highlighted
- Click to navigate to different stage/substage

**Structure:**
```
📁 Calendar
  ├─ Calendar View
  ├─ Week View
  └─ Week Themes

📁 Planning
  ├─ Taxonomy
  ├─ Section Structure Design  ← Current
  ├─ Section Ideas
  └─ Section Titling

📁 Research
  ├─ Research Overview
  ├─ Sources
  ├─ Visuals
  ├─ Prompts
  └─ Verification

📁 Authoring
  ├─ Drafting
  ├─ Image Concepts
  ├─ Image Prompts
  └─ Image Captions

📁 Imaging
  ├─ Image Generation
  └─ Optimise

📁 Header
  ├─ Title & Summary
  ├─ Image Prompt
  ├─ Image Details
  ├─ Image Generate
  └─ SEO Meta
```

**Interaction:**
- Click stage to expand/collapse
- Click substage to view its settings
- Current substage highlighted in blue
- Breadcrumb shows current path

---

## Data Sources & Mapping

### 1. Determine Current Context

**JavaScript:**
```javascript
const currentContext = {
    postType: window.postType || document.querySelector('.post-type-value').textContent.trim().toLowerCase(),
    stage: window.currentStage,
    substage: window.currentSubstage
};
```

### 2. Map Substage to Configuration

**Mapping Table:**
```javascript
const SUBSTAGE_CONFIG_MAP = {
    // Planning substages
    'taxonomy': {
        template: 'planning/calendar/taxonomy.html',
        llmConfig: null,  // No LLM action buttons
        pipelineStep: 'taxonomy',
        panels: null
    },
    'section-structure': {
        template: {
            'profile': 'planning/concept/section_structure_profile.html',
            'default': 'planning/concept/section_structure.html'
        },
        llmConfig: 'section_structure',
        pipelineStep: 'section-structure-design',
        panels: null
    },
    'topic-allocation': {
        template: {
            'profile': 'planning/concept/topic_allocation_profile.html',
            'default': 'planning/concept/topic_allocation.html'
        },
        llmConfig: 'topic_allocation',
        pipelineStep: 'section-ideas',  // Note: different name
        panels: null
    },
    'titling': {
        template: {
            'profile': 'planning/concept/titling_profile.html',
            'default': 'planning/concept/titling.html'
        },
        llmConfig: 'titling',
        pipelineStep: 'section-titling',
        panels: null
    },
    
    // Authoring substages
    'drafting': {
        template: 'authoring/sections/drafting.html',
        llmConfig: 'author_draft',
        pipelineStep: 'drafting',
        panels: 'authoring'  // Uses authoring panel config
    },
    'image-concepts': {
        template: 'authoring/sections/image_concepts.html',
        llmConfig: 'image_concepts',
        pipelineStep: 'image-concepts',
        panels: 'authoring'
    },
    // ... etc
};
```

### 3. Load Configuration Data

**For Current Context:**
```javascript
async function loadSettingsForContext(postType, stage, substage) {
    const config = SUBSTAGE_CONFIG_MAP[substage];
    
    // Determine template
    const template = typeof config.template === 'object' 
        ? config.template[postType] || config.template['default']
        : config.template;
    
    // Load LLM config if applicable
    let llmConfig = null;
    if (config.llmConfig) {
        llmConfig = LLM_CONFIGS[config.llmConfig];
        // Replace {id} and {section_id} placeholders
        llmConfig = processLLMConfig(llmConfig, postId, sectionId);
    }
    
    // Load pipeline step info
    const pipelineStep = getPipelineStepInfo(postType, config.pipelineStep);
    
    // Load panel config if applicable
    let panelConfig = null;
    if (config.panels) {
        panelConfig = getPanelConfigByPostType(postType);
    }
    
    return {
        template,
        llmConfig,
        pipelineStep,
        panelConfig,
        navbar: getNavbarConfig(postType, stage, substage)
    };
}
```

---

## Implementation Structure

### Files to Create

```
templates/shared/
└── includes/
    └── post_type_settings_modal.html      # Modal template

static/js/shared/
└── post-type-settings.js                 # Settings modal logic

static/css/shared/
└── post-type-settings.css                # Modal styles

blueprints/
└── settings_api.py                        # API endpoints for settings data
```

### API Endpoints

```python
# Get settings for specific context
GET /api/settings/post-types/<post_type>/context/<stage>/<substage>

# Get all stages/substages for a post type
GET /api/settings/post-types/<post_type>/navigation

# Get LLM config for a page type
GET /api/settings/llm-config/<page_type>
```

---

## Example: Current Context Display

**When on Planning > Section Structure Design for Profile post:**

```json
{
    "context": {
        "postType": "profile",
        "stage": "concept",
        "substage": "section-structure"
    },
    "template": {
        "path": "planning/concept/section_structure_profile.html",
        "isPostTypeSpecific": true,
        "route": "planning.planning_concept_section_structure"
    },
    "actionButtons": {
        "generate": {
            "label": "Generate Section Structure",
            "endpoint": "/planning/api/profile/section-structure",
            "method": "POST",
            "llmConfig": {
                "promptName": "Product Profile Section Structure",
                "systemPrompt": "...",
                "userPrompt": "..."
            }
        }
    },
    "pipelineStep": {
        "stepId": "section-structure-design",
        "order": 5,
        "label": "Planning — Section Structure",
        "function": "runSectionStructure",
        "previous": {
            "stepId": "taxonomy",
            "label": "Planning — Taxonomy"
        },
        "next": {
            "stepId": "section-ideas",
            "label": "Planning — Section Ideas"
        }
    },
    "navbar": {
        "visible": true,
        "url": "/planning/posts/{post_id}/concept/section-structure",
        "postTypes": ["themed", "profile", "generated"]
    }
}
```

---

## User Flow

1. **User clicks settings icon** in post_type header
2. **Modal opens** showing current context (Planning > Section Structure)
3. **Settings displayed** for that specific context
4. **User can explore:**
   - Click "Planning" in navigation tree to see all Planning substages
   - Click "Section Ideas" to see settings for that substage
   - Click "Authoring" to see Authoring stage settings
5. **Context updates** as user navigates
6. **Breadcrumb shows** current path
7. **User closes modal** (X button or click outside)

---

## Benefits of This Approach

1. **Contextual:** Shows relevant settings for current page
2. **Explorable:** Easy to see other stages/substages
3. **Non-intrusive:** Small icon, modal doesn't block workflow
4. **Informative:** Shows all relevant config in one place
5. **Extensible:** Easy to add editing in Phase 2

---

## Next Steps

1. Add settings icon to post_type header
2. Create modal template
3. Create JavaScript for modal logic
4. Create API endpoints for settings data
5. Implement navigation tree
6. Implement context display
7. Test with all post types and stages

