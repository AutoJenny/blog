# Phase 3: Static Assets Consolidation - Detailed Implementation

## 3.1 CSS Consolidation

### Step 3.1.1: Analyze Current CSS Files
- [ ] List all CSS files from each service
- [ ] Identify conflicts and overlaps
- [ ] Document CSS dependencies
- [ ] Plan consolidation strategy

**Current CSS Files Analysis**:
```
blog-core/static/css/:
- dist/main.css (Tailwind CSS)
- workflow_nav/css/nav.dist.css

blog-launchpad/static/css/:
- (No specific CSS files found)

blog-llm-actions/static/css/:
- llm-actions.css

blog-post-sections/static/css/:
- (No specific CSS files found)

blog-post-info/static/css/:
- (No specific CSS files found)

blog-images/static/css/:
- (No specific CSS files found)

blog-clan-api/static/css/:
- (No specific CSS files found)
```

**Benchmark**: CSS files catalogued and conflicts identified
**Test**: `find . -name "*.css" -type f` lists all CSS files

### Step 3.1.2: Create Unified CSS Structure
- [ ] Create `static/css/` directory structure
- [ ] Organize CSS files by service
- [ ] Create main CSS file
- [ ] Set up CSS imports

**Directory Structure**:
```
static/css/
├── main.css                 # Main unified CSS file
├── core/                    # Core service CSS
│   ├── workflow.css
│   └── navigation.css
├── launchpad/               # Launchpad service CSS
│   └── syndication.css
├── llm_actions/             # LLM Actions service CSS
│   └── llm-actions.css
├── post_sections/           # Post Sections service CSS
├── post_info/               # Post Info service CSS
├── images/                  # Images service CSS
├── clan_api/                # Clan API service CSS
└── shared/                  # Shared CSS
    ├── base.css
    ├── components.css
    └── utilities.css
```

**Benchmark**: Unified CSS structure created
**Test**: `ls -la static/css/` shows organized structure

### Step 3.1.3: Consolidate CSS Files
- [ ] Move CSS files to unified structure
- [ ] Resolve CSS conflicts
- [ ] Update CSS imports
- [ ] Test visual consistency

**Consolidation Steps**:
- [ ] Move `blog-core/static/css/dist/main.css` → `static/css/shared/base.css`
- [ ] Move `blog-core/static/css/workflow_nav/css/nav.dist.css` → `static/css/core/navigation.css`
- [ ] Move `blog-llm-actions/static/css/llm-actions.css` → `static/css/llm_actions/llm-actions.css`
- [ ] Create `static/css/main.css` with imports
- [ ] Resolve any CSS conflicts

**Main CSS File**:
```css
/* static/css/main.css */
@import 'shared/base.css';
@import 'shared/components.css';
@import 'shared/utilities.css';
@import 'core/workflow.css';
@import 'core/navigation.css';
@import 'launchpad/syndication.css';
@import 'llm_actions/llm-actions.css';
```

**Benchmark**: All CSS files consolidated and conflicts resolved
**Test**: All pages load with proper styling

### Step 3.1.4: Update Template References
- [ ] Update all templates to use unified CSS paths
- [ ] Update CSS imports in templates
- [ ] Test template rendering
- [ ] Verify visual consistency

**Template Updates**:
- [ ] Update `templates/core/index.html` to use `/static/css/main.css`
- [ ] Update `templates/launchpad/syndication.html` to use `/static/css/main.css`
- [ ] Update `templates/llm_actions/index.html` to use `/static/css/main.css`
- [ ] Update all other templates

**Benchmark**: All templates use unified CSS paths
**Test**: All pages render with correct styling

## 3.2 JavaScript Consolidation

### Step 3.2.1: Analyze Current JavaScript Files
- [ ] List all JavaScript files from each service
- [ ] Identify API call patterns
- [ ] Document JavaScript dependencies
- [ ] Plan consolidation strategy

**Current JavaScript Files Analysis**:
```
blog-core/static/js/:
- (No specific JS files found)

blog-launchpad/static/js/:
- (No specific JS files found)

blog-llm-actions/static/js/:
- logger.js
- llm-actions.js
- config-manager.js
- prompt-manager.js
- ui-config.js
- field-selector.js
- message-manager-core.js
- message-manager-ui.js
- message-manager-elements.js
- message-manager-preview.js
- message-manager-storage.js
- llm-config-manager.js
- accordion-manager.js
- debug-modules.js

blog-post-sections/static/js/:
- (No specific JS files found)

blog-post-info/static/js/:
- (No specific JS files found)

blog-images/static/js/:
- (No specific JS files found)

blog-clan-api/static/js/:
- (No specific JS files found)
```

**Benchmark**: JavaScript files catalogued and dependencies identified
**Test**: `find . -name "*.js" -type f` lists all JavaScript files

### Step 3.2.2: Create Unified JavaScript Structure
- [ ] Create `static/js/` directory structure
- [ ] Organize JavaScript files by service
- [ ] Create main JavaScript file
- [ ] Set up JavaScript imports

**Directory Structure**:
```
static/js/
├── main.js                  # Main unified JavaScript file
├── core/                    # Core service JavaScript
│   ├── workflow.js
│   └── navigation.js
├── launchpad/               # Launchpad service JavaScript
│   └── syndication.js
├── llm_actions/             # LLM Actions service JavaScript
│   ├── llm-actions.js
│   ├── config-manager.js
│   ├── prompt-manager.js
│   ├── ui-config.js
│   ├── field-selector.js
│   ├── message-manager-core.js
│   ├── message-manager-ui.js
│   ├── message-manager-elements.js
│   ├── message-manager-preview.js
│   ├── message-manager-storage.js
│   ├── llm-config-manager.js
│   ├── accordion-manager.js
│   └── debug-modules.js
├── post_sections/           # Post Sections service JavaScript
├── post_info/               # Post Info service JavaScript
├── images/                  # Images service JavaScript
├── clan_api/                # Clan API service JavaScript
└── shared/                  # Shared JavaScript
    ├── logger.js
    ├── api.js
    └── utils.js
```

**Benchmark**: Unified JavaScript structure created
**Test**: `ls -la static/js/` shows organized structure

### Step 3.2.3: Update API Calls
- [ ] Update all hardcoded port references
- [ ] Update API endpoints to use unified paths
- [ ] Remove CORS-specific code
- [ ] Test API functionality

**API Call Updates**:
- [ ] Update `http://localhost:5000` → `window.location.origin`
- [ ] Update `http://localhost:5001` → `window.location.origin`
- [ ] Update `http://localhost:5002` → `window.location.origin`
- [ ] Update all fetch calls to use relative URLs
- [ ] Remove CORS headers

**Example Updates**:
```javascript
// Before
const response = await fetch('http://localhost:5002/api/run-llm', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
});

// After
const response = await fetch('/llm_actions/api/run-llm', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
});
```

**Benchmark**: All API calls updated to use unified endpoints
**Test**: All JavaScript API calls work without cross-origin errors

### Step 3.2.4: Consolidate JavaScript Files
- [ ] Move JavaScript files to unified structure
- [ ] Resolve JavaScript conflicts
- [ ] Update JavaScript imports
- [ ] Test functionality

**Consolidation Steps**:
- [ ] Move `blog-llm-actions/static/js/logger.js` → `static/js/shared/logger.js`
- [ ] Move all LLM Actions JS files → `static/js/llm_actions/`
- [ ] Create `static/js/main.js` with imports
- [ ] Resolve any JavaScript conflicts

**Main JavaScript File**:
```javascript
// static/js/main.js
import './shared/logger.js';
import './shared/api.js';
import './shared/utils.js';
import './core/workflow.js';
import './core/navigation.js';
import './launchpad/syndication.js';
import './llm_actions/llm-actions.js';
```

**Benchmark**: All JavaScript files consolidated and conflicts resolved
**Test**: All JavaScript functionality works

### Step 3.2.5: Update Template References
- [ ] Update all templates to use unified JavaScript paths
- [ ] Update JavaScript imports in templates
- [ ] Test template rendering
- [ ] Verify functionality

**Template Updates**:
- [ ] Update `templates/core/index.html` to use `/static/js/main.js`
- [ ] Update `templates/launchpad/syndication.html` to use `/static/js/main.js`
- [ ] Update `templates/llm_actions/index.html` to use `/static/js/main.js`
- [ ] Update all other templates

**Benchmark**: All templates use unified JavaScript paths
**Test**: All pages load with correct JavaScript functionality

## 3.3 Template Consolidation

### Step 3.3.1: Analyze Current Template Structure
- [ ] List all template files from each service
- [ ] Identify template conflicts
- [ ] Document template dependencies
- [ ] Plan consolidation strategy

**Current Template Structure Analysis**:
```
blog-core/templates/:
- index.html
- workflow.html
- docs_browser.html
- docs_content.html
- error.html

blog-launchpad/templates/:
- index.html
- syndication.html
- syndication_dashboard.html
- syndication/facebook/product_post.html
- syndication/facebook/blog_post.html

blog-llm-actions/templates/:
- index.html
- test_api.html

blog-post-sections/templates/:
- (No specific template files found)

blog-post-info/templates/:
- (No specific template files found)

blog-images/templates/:
- (No specific template files found)

blog-clan-api/templates/:
- (No specific template files found)
```

**Benchmark**: Template files catalogued and conflicts identified
**Test**: `find . -name "*.html" -type f` lists all template files

### Step 3.3.2: Create Unified Template Structure
- [ ] Create `templates/` directory structure
- [ ] Organize templates by service
- [ ] Create base template
- [ ] Set up template inheritance

**Directory Structure**:
```
templates/
├── base.html                # Base template
├── core/                    # Core service templates
│   ├── index.html
│   ├── workflow.html
│   ├── docs_browser.html
│   ├── docs_content.html
│   └── error.html
├── launchpad/               # Launchpad service templates
│   ├── index.html
│   ├── syndication.html
│   ├── syndication_dashboard.html
│   └── syndication/
│       └── facebook/
│           ├── product_post.html
│           └── blog_post.html
├── llm_actions/             # LLM Actions service templates
│   ├── index.html
│   └── test_api.html
├── post_sections/           # Post Sections service templates
├── post_info/               # Post Info service templates
├── images/                  # Images service templates
├── clan_api/                # Clan API service templates
└── shared/                  # Shared templates
    ├── components/
    └── partials/
```

**Benchmark**: Unified template structure created
**Test**: `ls -la templates/` shows organized structure

### Step 3.3.3: Create Base Template
- [ ] Create `templates/base.html` with common structure
- [ ] Include CSS and JavaScript imports
- [ ] Set up template blocks
- [ ] Test base template

**Base Template**:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Blog CMS{% endblock %}</title>
    <link rel="stylesheet" href="/static/css/main.css">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <header>
        {% block header %}{% endblock %}
    </header>
    <main>
        {% block content %}{% endblock %}
    </main>
    <footer>
        {% block footer %}{% endblock %}
    </footer>
    <script src="/static/js/main.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

**Benchmark**: Base template created and working
**Test**: Base template renders correctly

### Step 3.3.4: Consolidate Template Files
- [ ] Move template files to unified structure
- [ ] Update template inheritance
- [ ] Resolve template conflicts
- [ ] Test template rendering

**Consolidation Steps**:
- [ ] Move `blog-core/templates/*` → `templates/core/`
- [ ] Move `blog-launchpad/templates/*` → `templates/launchpad/`
- [ ] Move `blog-llm-actions/templates/*` → `templates/llm_actions/`
- [ ] Update all templates to extend `base.html`
- [ ] Resolve any template conflicts

**Template Updates**:
```html
<!-- Before -->
<!DOCTYPE html>
<html>
<head>
    <title>Workflow</title>
    <link rel="stylesheet" href="/static/css/dist/main.css">
</head>
<body>
    <!-- content -->
</body>
</html>

<!-- After -->
{% extends "base.html" %}
{% block title %}Workflow{% endblock %}
{% block content %}
    <!-- content -->
{% endblock %}
```

**Benchmark**: All template files consolidated and conflicts resolved
**Test**: All templates render correctly

### Step 3.3.5: Update Template References
- [ ] Update all route handlers to use unified template paths
- [ ] Update template includes
- [ ] Test template rendering
- [ ] Verify functionality

**Route Handler Updates**:
```python
# Before
return render_template('index.html', first_post_id=first_post_id)

# After
return render_template('core/index.html', first_post_id=first_post_id)
```

**Benchmark**: All route handlers use unified template paths
**Test**: All pages render with correct templates

## 3.4 Image Assets Consolidation

### Step 3.4.1: Analyze Current Image Assets
- [ ] List all image files from each service
- [ ] Identify image conflicts
- [ ] Document image usage
- [ ] Plan consolidation strategy

**Current Image Assets Analysis**:
```
blog-core/static/images/:
- site/brand-logo.png
- (other site images)

blog-launchpad/static/images/:
- (No specific image files found)

blog-llm-actions/static/images/:
- (No specific image files found)

blog-post-sections/static/images/:
- (No specific image files found)

blog-post-info/static/images/:
- (No specific image files found)

blog-images/static/images/:
- (Image processing output)

blog-clan-api/static/images/:
- (No specific image files found)
```

**Benchmark**: Image assets catalogued and conflicts identified
**Test**: `find . -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.gif" -o -name "*.svg"` lists all image files

### Step 3.4.2: Create Unified Image Structure
- [ ] Create `static/images/` directory structure
- [ ] Organize images by service
- [ ] Set up image serving
- [ ] Test image access

**Directory Structure**:
```
static/images/
├── site/                    # Site-wide images
│   └── brand-logo.png
├── core/                    # Core service images
├── launchpad/               # Launchpad service images
├── llm_actions/             # LLM Actions service images
├── post_sections/           # Post Sections service images
├── post_info/               # Post Info service images
├── images/                  # Images service output
└── clan_api/                # Clan API service images
```

**Benchmark**: Unified image structure created
**Test**: `ls -la static/images/` shows organized structure

### Step 3.4.3: Consolidate Image Files
- [ ] Move image files to unified structure
- [ ] Update image references in templates
- [ ] Resolve image conflicts
- [ ] Test image serving

**Consolidation Steps**:
- [ ] Move `blog-core/static/images/*` → `static/images/site/`
- [ ] Move `blog-images/static/images/*` → `static/images/images/`
- [ ] Update all template image references
- [ ] Resolve any image conflicts

**Template Updates**:
```html
<!-- Before -->
<img src="/static/images/site/brand-logo.png" alt="Logo">

<!-- After -->
<img src="/static/images/site/brand-logo.png" alt="Logo">
```

**Benchmark**: All image files consolidated and conflicts resolved
**Test**: All images load correctly

## Phase 3 Completion Checklist

- [ ] All CSS files consolidated
- [ ] All JavaScript files consolidated
- [ ] All template files consolidated
- [ ] All image assets consolidated
- [ ] All conflicts resolved
- [ ] All references updated
- [ ] All tests passing

**Overall Benchmark**: All static assets consolidated and working
**Test**: All pages load with correct styling, JavaScript, and images

---

**Next Phase**: Phase 4 - Configuration Unification
**Estimated Time**: 1 day
**Dependencies**: Phase 3 complete
