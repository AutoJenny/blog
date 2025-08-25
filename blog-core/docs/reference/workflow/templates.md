# Workflow Templates Reference

## Overview
This document explains the template hierarchy and structure for the workflow system, including which templates are used for different stages and how to modify them correctly.

## Template Hierarchy

### Main Workflow Template
**File**: `app/templates/workflow/index.html`
**Purpose**: Primary template that handles all workflow stages and routing

#### Structure
```html
{% extends 'base.html' %}
{% block content %}
<div class="flex flex-col min-h-screen">
  <!-- Navigation -->
  <div id="workflow-nav">
    {% include 'nav/workflow_nav.html' %}
  </div>
  
  <!-- Stage-specific content -->
  <div class="flex-grow">
    {% if current_stage == 'planning' %}
      <!-- Planning stage layout -->
    {% elif current_stage == 'writing' %}
      <!-- Writing stage layout -->
    {% else %}
      <!-- Other stages -->
    {% endif %}
  </div>
</div>
{% endblock %}
```

### Stage-Specific Templates

#### Planning Stage
- **Template**: `app/templates/workflow/index.html` (planning section)
- **Layout**: Full-width LLM actions panel
- **Features**: Modular LLM panels for idea generation and research

#### Writing Stage
- **Template**: `app/templates/workflow/index.html` (writing section)
- **Layout**: Two-column layout
  - Left: LLM Actions Panel (`#workflow-llm-actions`)
  - Right: Sections Panel (`#workflow-sections`)
- **JS Integration**: Inline script block with ES6 modules
- **Data Source**: `/api/workflow/posts/{post_id}/sections`

#### Publishing Stage
- **Template**: `app/templates/workflow/index.html` (publishing section)
- **Layout**: Full-width layout for final stages
- **Features**: Preflight checks, launch management

## Key Template Files

### 1. Main Workflow Template
**File**: `app/templates/workflow/index.html`
**Purpose**: Stage routing and layout management
**Key Sections**:
- Navigation area
- Stage-specific content areas
- Conditional rendering based on `current_stage`

### 2. Modular LLM Panels
**File**: `app/templates/workflow/_modular_llm_panels.html`
**Purpose**: Reusable LLM action panels
**Usage**: Included in all workflow stages

### 3. Navigation Template
**File**: `app/templates/nav/workflow_nav.html`
**Purpose**: Workflow navigation and stage indicators
**Usage**: Included in main workflow template

### 4. Section Rendering JS
**File**: `app/static/js/workflow/template_view.js`
**Purpose**: JavaScript module for rendering section data
**Features**: 
- ES6 module with `renderStructure()` function
- Dark theme styling
- JSON pretty-printing for complex data

## Template Modification Guidelines

### Writing Stage Modifications
**Important**: For the writing stage, always modify `app/templates/workflow/index.html`, not separate template files.

#### Correct Approach
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
      <!-- Your sections panel content here -->
    </div>
  </div>
</div>
<script type="module">
  // Your JavaScript here
</script>
```

#### Incorrect Approach
- Don't create separate `writing/content.html` files
- Don't modify files in `app/templates/workflow/writing/` directory
- Don't expect separate templates to be used for writing stage

### JavaScript Integration
**Pattern**: Use ES6 modules with inline script blocks

```html
<script type="module">
  import sectionPanel from '/static/js/workflow/template_view.js';
  
  document.addEventListener('DOMContentLoaded', async () => {
    // Your initialization code
  });
</script>
```

### API Integration
**Pattern**: Fetch data and render using JS modules

```javascript
// Fetch sections data
const response = await fetch(`/api/workflow/posts/${postId}/sections`);
const data = await response.json();

// Render using module function
const structure = { post: { id: postId }, sections: data.sections || [] };
panel.innerHTML = sectionPanel.renderStructure(structure);
```

## Common Issues and Solutions

### Issue: Placeholder Text Appears
**Symptom**: "Sections module interface placeholder for Writing stage."
**Cause**: Wrong template is being used or template not updated
**Solution**: Ensure `app/templates/workflow/index.html` is modified for writing stage

### Issue: JavaScript Not Running
**Symptom**: "Loading sections..." never changes
**Causes**:
1. Module import errors
2. API endpoint issues
3. Static file not accessible
**Solutions**:
1. Check browser console for JS errors
2. Test API endpoint with curl
3. Verify static file paths

### Issue: Wrong Layout
**Symptom**: Single column instead of two-column layout
**Cause**: Template conditional logic not working
**Solution**: Check `current_stage` variable and template conditions

## Development Workflow

### Making Changes
1. **Identify Stage**: Determine which workflow stage you're modifying
2. **Find Template**: Locate the correct template file (usually `workflow/index.html`)
3. **Modify Section**: Update the appropriate stage-specific section
4. **Test**: Reload the page and verify changes
5. **Debug**: Use browser console and curl for troubleshooting

### Testing Changes
1. **Template Changes**: Reload the workflow page
2. **JavaScript Changes**: Hard refresh (Shift+Reload)
3. **API Changes**: Test with curl first
4. **Static Files**: Verify file accessibility

### Debugging Checklist
- [ ] Correct template file is being modified
- [ ] Template conditional logic is correct
- [ ] JavaScript modules are accessible
- [ ] API endpoints are working
- [ ] Browser console shows no errors
- [ ] Static files are being served correctly

## Future Considerations

### Template Organization
- Consider separating stage-specific templates for better maintainability
- Implement template inheritance for common elements
- Create reusable components for repeated UI patterns

### JavaScript Architecture
- Maintain ES6 module structure
- Keep business logic separate from UI rendering
- Implement proper error handling and loading states

### API Integration
- Use consistent endpoint patterns
- Implement proper error handling
- Consider caching for frequently accessed data 