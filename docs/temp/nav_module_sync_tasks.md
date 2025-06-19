# Navigation Module Synchronization Tasks

## Overview
This document outlines the specific tasks needed to ensure perfect synchronization between the workflow-navigation branch and the MAIN_HUB nav module integration.

## Critical Rules
- All module changes MUST be made in workflow-navigation branch
- MAIN_HUB modules directory remains READ-ONLY
- Use merge_nav_module.sh script for integration only

## Tasks

### 1. Template Synchronization
- [ ] Update URL Generation in nav.html
  ```python
  # Replace all href="#" with proper Flask routes
  href="{{ url_for('workflow_nav.stage', stage=stage_name, substage=substage_name) }}"
  ```
- [ ] Standardize Error Messages
  ```html
  <div class="text-red-500 bg-dark-bg p-4 rounded-lg border border-red-700 mt-4">
      {{ error_message }}
  </div>
  ```
- [ ] Add Status Indicators
  ```html
  <div class="text-green-500 bg-dark-bg p-4 rounded-lg border border-green-700 mt-4">
      {{ status_message }}
  </div>
  ```

### 2. Service Layer Implementation
- [ ] Update services.py in workflow-navigation:
  ```python
  def get_workflow_context():
      try:
          from app.services.shared import get_shared_workflow_context
          return get_shared_workflow_context()
      except ImportError:
          return get_demo_workflow_context()
  ```
- [ ] Implement Demo Data Fallback
  ```python
  def get_demo_workflow_context():
      return {
          'stages': DEMO_STAGES,
          'current_stage': 'planning',
          'current_substage': 'idea'
      }
  ```
- [ ] Remove Any Direct DB Access
  - Replace with shared service calls
  - Document required shared services

### 3. Static Asset Management
- [ ] Update CSS Loading
  ```html
  <link rel="stylesheet" href="{{ url_for('workflow_nav.static', filename='css/nav.dist.css') }}">
  ```
- [ ] Verify JS Loading
  ```html
  <script src="{{ url_for('workflow_nav.static', filename='js/nav.js') }}"></script>
  ```
- [ ] Check Font Awesome Integration
  ```html
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
  ```

### 4. Blueprint Configuration
- [ ] Update __init__.py in workflow-navigation:
  ```python
  from flask import Blueprint

  workflow_nav = Blueprint('workflow_nav', __name__,
                         template_folder='templates',
                         static_folder='static',
                         static_url_path='/static/workflow_nav')
  ```
- [ ] Verify Route Registration
  ```python
  from . import routes
  workflow_nav.register_blueprint(routes.bp)
  ```

### 5. Context Variables
- [ ] Document Required Variables
  ```python
  REQUIRED_CONTEXT = [
      'current_stage',
      'current_substage',
      'current_step',
      'all_posts',
      'post_id'
  ]
  ```
- [ ] Implement Context Validation
  ```python
  def validate_context(context):
      missing = [var for var in REQUIRED_CONTEXT if var not in context]
      if missing:
          raise ValueError(f"Missing required context variables: {missing}")
  ```

### 6. Testing Protocol
- [ ] Standalone Tests
  ```bash
  # In workflow-navigation branch
  python -m pytest tests/nav/
  ```
- [ ] Integration Tests
  ```bash
  # After merge to MAIN_HUB
  python -m pytest tests/integration/nav/
  ```
- [ ] Visual Verification
  - Compare screenshots
  - Check all links work
  - Verify error states

### 7. Documentation
- [ ] Update CHANGES_LOG.md
  ```markdown
  ## [2024-03-XX]
  ### Changed
  - Synchronized nav module templates
  - Updated service layer implementation
  - Standardized error handling
  ```
- [ ] Update README.md with Integration Requirements
  ```markdown
  ## Required Context
  - List all required variables
  - Document service dependencies
  - Show integration example
  ```

### 8. Merge Process
- [ ] Pre-merge Checklist
  - [ ] All tests pass in workflow-navigation
  - [ ] Documentation updated
  - [ ] No direct DB access
  - [ ] All assets properly namespaced
- [ ] Run Merge Script
  ```bash
  ./merge_nav_module.sh
  ```
- [ ] Post-merge Verification
  - [ ] Check all features work
  - [ ] Verify no broken links
  - [ ] Test error states

## Verification

### Visual Elements
- [ ] Dark theme consistent
- [ ] Icons displaying correctly
- [ ] Hover states working
- [ ] Error messages styled properly

### Functionality
- [ ] Stage navigation works
- [ ] Post selector working
- [ ] Error states handled
- [ ] Context properly passed

### Integration
- [ ] No console errors
- [ ] All assets loading
- [ ] No 404s for static files
- [ ] Blueprint routes resolving

## Notes
- Keep CHANGES_LOG.md updated as tasks are completed
- Document any deviations from plan
- Note any integration issues for future reference 