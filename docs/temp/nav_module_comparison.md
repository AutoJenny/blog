# Navigation Module Branch Comparison

## Static File Paths

| Asset Type | workflow-navigation | MAIN_HUB |
|------------|-------------------|-----------|
| CSS | `/workflow_nav/static/css/nav.dist.css` | `/static/modules/nav/nav.dist.css` |
| JavaScript | `/workflow_nav/static/js/nav.js` | `/static/modules/nav/nav.js` |
| Template | `/workflow_nav/templates/nav.html` | `/templates/workflow_nav/nav.html` |

## Route Structure

| Route Purpose | workflow-navigation | MAIN_HUB |
|--------------|-------------------|-----------|
| Base Path | `/workflow_nav/dev` | `/dev` |
| Post Selection | `/workflow_nav/dev/posts/<post_id>` | `/dev/posts/<post_id>` |
| Stage View | `/workflow_nav/dev/posts/<post_id>/<stage>` | `/dev/posts/<post_id>/<stage>` |
| Substage View | `/workflow_nav/dev/posts/<post_id>/<stage>/<substage>` | `/dev/posts/<post_id>/<stage>/<substage>` |

## Blueprint Registration

| Aspect | workflow-navigation | MAIN_HUB |
|--------|-------------------|-----------|
| Blueprint Name | `workflow_nav` | `nav` |
| URL Prefix | `/workflow_nav` | `/` |
| Template Folder | `templates` | `templates/workflow_nav` |
| Static Folder | `static` | `static/modules/nav` |

## Template Variables

| Variable | workflow-navigation | MAIN_HUB |
|----------|-------------------|-----------|
| current_stage | ✓ | ✓ |
| current_substage | ✓ | ✓ |
| current_step | ✓ | ✓ |
| post_id | ✓ | ✓ |
| all_posts | ✓ | ✓ |

## CSS Classes and Styling

| Element | workflow-navigation | MAIN_HUB |
|---------|-------------------|-----------|
| Active Icon Border | `border-blue-500` | `border-blue-500` |
| Icon Background | `bg-dark-bg` | `bg-dark-bg` |
| Icon Hover | `hover:bg-dark-hover` | `hover:bg-dark-hover` |
| Text Color | `text-dark-text` | `text-dark-text` |
| Stage Labels | `text-gray-400` | `text-gray-400` |

## JavaScript Event Handlers

| Event | workflow-navigation | MAIN_HUB |
|-------|-------------------|-----------|
| Post Selector Change | `post-selector` ID | `post-selector` ID |
| URL Path Construction | Uses split('/') | Uses split('/') |

## Required Actions for Synchronization:

1. File Structure Alignment:
   - [ ] Ensure CSS files are in identical locations
   - [ ] Ensure JS files are in identical locations
   - [ ] Ensure templates are in identical locations

2. Blueprint Configuration:
   - [ ] Align blueprint names
   - [ ] Align URL prefixes
   - [ ] Align static folder paths
   - [ ] Align template folder paths

3. Route Handling:
   - [ ] Synchronize base paths
   - [ ] Synchronize post selection paths
   - [ ] Synchronize stage/substage paths

4. Template Context:
   - [ ] Verify all variables are passed identically
   - [ ] Verify variable processing is identical

5. Static Asset Loading:
   - [ ] Verify CSS loading paths
   - [ ] Verify JS loading paths
   - [ ] Verify asset compilation process

6. Visual Verification:
   - [ ] Icon highlighting
   - [ ] Stage labels
   - [ ] Post selector functionality
   - [ ] Navigation state preservation 