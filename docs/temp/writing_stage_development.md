# Writing Stage Development Specification

## CRITICAL WARNING
⚠️ The Planning stage code is now stable and must be preserved. DO NOT modify any files in the Planning stage, including:
- `app/templates/workflow/planning/_planning_content.html`
- Any Planning stage routes or controllers
- Any Planning stage database operations

The Writing stage will be developed as a completely separate module, reusing UI components where appropriate but maintaining independence from the Planning stage.

## Development Base
The Writing stage will be developed starting from:
```
http://localhost:5000/workflow/22/planning/structure/outline/
```

This provides our development base with:
- Existing navigation module
- Working workflow structure
- Test data from post_id=22

## Overview
This document outlines the development plan for the Writing stage of the blog post workflow. The Writing stage focuses on developing individual sections of the post, with support for batch processing and fact allocation.

## Development Phases

### Phase 1: UI Wireframe Implementation
- [x] Create base template for Writing stage
  - [x] Create new `_writing_content.html` template
  - [x] Reuse navigation module from Planning stage
  - [x] Implement section accordion framework
  - [x] Add section-specific navigation

- [ ] Implement section display components
  - [ ] Primary section accordions
  - [ ] Secondary accordion groups (Text, Resources, Meta)
  - [ ] Section selection interface
  - [ ] Progress indicators

- [ ] Add section content display
  - [ ] Title display
  - [ ] Description display
  - [ ] Ideas display
  - [ ] Content preview areas

### Phase 2: Database Structure
- [ ] Extend workflow_step_entity table
  - [ ] Add section-specific fields
  - [ ] Add batch processing fields
  - [ ] Add fact allocation fields

- [ ] Create section-specific tables
  - [ ] Section content table
  - [ ] Section resources table
  - [ ] Section metadata table

### Phase 3: Batch Processing Framework
- [ ] Implement section selection system
  - [ ] "All Sections" default option
  - [ ] Individual section checkboxes
  - [ ] Selection persistence

- [ ] Add batch processing logic
  - [ ] Section iteration system
  - [ ] Progress tracking
  - [ ] Error handling
  - [ ] Results storage

### Phase 4: Fact Allocation System
- [ ] Implement fact allocation UI
  - [ ] Fact list display
  - [ ] Section assignment interface
  - [ ] Progress tracking

- [ ] Add fact processing logic
  - [ ] Batch processing system
  - [ ] Section matching algorithm
  - [ ] Results storage
  - [ ] Verification system

### Phase 5: LLM Integration
- [ ] Implement section-specific prompts
  - [ ] Prompt templates
  - [ ] Context management
  - [ ] Response handling

- [ ] Add batch processing prompts
  - [ ] Section iteration prompts
  - [ ] Fact allocation prompts
  - [ ] Verification prompts

### Phase 6: Testing and Refinement
- [ ] Unit testing
  - [ ] Component tests
  - [ ] Integration tests
  - [ ] End-to-end tests

- [ ] Performance optimization
  - [ ] Batch processing efficiency
  - [ ] UI responsiveness
  - [ ] Memory usage

## Technical Details

### UI Components
```html
<!-- Section Accordion Structure -->
<div class="section-accordion">
  <div class="section-header">
    <h3>Section Title</h3>
    <div class="section-meta">
      <span class="status">Status</span>
      <span class="word-count">Word Count</span>
    </div>
  </div>
  
  <div class="section-content">
    <!-- Secondary Accordions -->
    <div class="content-group">
      <div class="text-accordion">
        <!-- Text content -->
      </div>
      <div class="resources-accordion">
        <!-- Resources content -->
      </div>
      <div class="meta-accordion">
        <!-- Meta content -->
      </div>
    </div>
  </div>
</div>
```

### Database Schema Extensions
```sql
-- Section-specific fields for workflow_step_entity
ALTER TABLE workflow_step_entity
ADD COLUMN section_id INTEGER,
ADD COLUMN batch_status VARCHAR(50),
ADD COLUMN processing_order INTEGER;

-- New section content table
CREATE TABLE section_content (
  id SERIAL PRIMARY KEY,
  post_id INTEGER,
  section_id INTEGER,
  content_type VARCHAR(50),
  content TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### API Endpoints
```
POST /api/v1/workflow/sections/batch
GET /api/v1/workflow/sections/{section_id}/content
POST /api/v1/workflow/sections/{section_id}/facts
GET /api/v1/workflow/sections/{section_id}/status
```

## Implementation Notes

1. Each phase should be completed and tested before moving to the next
2. All changes should be committed to Git after testing
3. Documentation should be updated as features are implemented
4. Performance metrics should be monitored throughout development
5. Regular testing with post_id=22 should be performed
6. NEVER modify Planning stage code - it is now stable and preserved
7. Reuse UI components from Planning stage where appropriate, but maintain independence

## Success Criteria

- [ ] UI wireframe successfully displays all section content
- [ ] Batch processing works reliably for all sections
- [ ] Fact allocation system accurately assigns facts to sections
- [ ] All components are responsive and performant
- [ ] Documentation is complete and up-to-date
- [ ] Planning stage functionality remains completely unchanged 