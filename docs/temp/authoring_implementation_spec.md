# Authoring Area Implementation Specification

## Overview
The Authoring area mirrors the Planning area's structure and styling but operates at the blog post section level rather than the post level. Each operation needs to be iterated per-section (typically 6-8 sections) while allowing individual section editing.

## Core Principles
- **Consistency**: Use identical header/navigation patterns as Planning
- **Section-centric**: All operations work on individual sections within a post
- **Dual modes**: Batch operations across all sections + individual section editing
- **Reusability**: Leverage existing LLM module, CSS, and JavaScript patterns
- **No schema changes**: Work with existing data structures initially

## Data Architecture

### Current Data Sources
- **Sections**: Available via `api_get_sections(post_id)` from Planning titling work
- **Structure**: Each section contains `id`, `title`, `subtitle`, `topics`, `order`, `description`
- **Storage**: Sections stored in `post.sections` JSONB field (canonical source)

### Required Data Extensions (Future)
- **Section Content**: `sections[i].draft_html`, `sections[i].draft_md`
- **Section Metadata**: `sections[i].word_count`, `sections[i].last_modified`, `sections[i].status`
- **Section Notes**: `sections[i].notes`, `sections[i].citations`, `sections[i].seo_meta`

## Backend Architecture

### New Blueprint: `authoring.py`
```python
# Main routes
@bp.route('/posts/<int:post_id>')
def authoring_post_overview(post_id)

@bp.route('/posts/<int:post_id>/sections')
def authoring_sections_overview(post_id)

@bp.route('/posts/<int:post_id>/sections/<int:section_id>')
def authoring_section_detail(post_id, section_id)

# API endpoints
@bp.route('/api/posts/<int:post_id>/sections')
def api_get_sections(post_id)

@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>')
def api_get_section_detail(post_id, section_id)

@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>', methods=['PUT'])
def api_save_section_content(post_id, section_id)

@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>/generate', methods=['POST'])
def api_generate_section_content(post_id, section_id)

@bp.route('/api/posts/<int:post_id>/sections/generate', methods=['POST'])
def api_generate_all_sections(post_id)
```

### LLM Integration
- **Reuse**: Existing `llm_module.html` include and `llm-module.js`
- **New Configs**: Add authoring-specific configurations:
  ```javascript
  const LLM_CONFIGS = {
    // ... existing configs ...
    'author_draft': {
      promptEndpoint: '/authoring/api/llm/prompts/section-drafting',
      generateEndpoint: '/authoring/api/posts/{id}/sections/{section_id}/generate',
      resultsField: 'draft_content',
      resultsTitle: 'Generated Draft',
      allowEdit: true
    },
    'author_refine': {
      promptEndpoint: '/authoring/api/llm/prompts/section-refinement',
      generateEndpoint: '/authoring/api/posts/{id}/sections/{section_id}/refine',
      resultsField: 'refined_content',
      resultsTitle: 'Refined Content',
      allowEdit: true
    }
  };
  ```

## Template Architecture

### Main Templates
- `templates/authoring/sections/overview.html` - Section list with batch operations
- `templates/authoring/sections/detail.html` - Individual section editor
- `templates/authoring/sections/drafting.html` - Section drafting workspace
- `templates/authoring/sections/refinement.html` - Section refinement workspace
- `templates/authoring/sections/seo.html` - SEO and metadata workspace

### Layout Pattern
Each template extends `base.html` and includes:
```html
{% extends 'base.html' %}
{% block content %}
  {% include 'planning/includes/condensed_header.html' %}
  
  <div class="authoring-workspace">
    <div class="sections-panel">
      <!-- Section list/navigation -->
    </div>
    <div class="editor-panel">
      <!-- LLM module + editing workspace -->
    </div>
  </div>
{% endblock %}
```

## User Interface Design

### Two-Pane Layout
```
┌─────────────────────────────────────────────────────────────┐
│                    Condensed Header                         │
│  [Authoring] [Drafting] [Refinement] [SEO] [Images]         │
├─────────────────────┬───────────────────────────────────────┤
│   Sections Panel    │           Editor Panel               │
│                     │                                       │
│  📝 Section 1       │  ┌─ LLM Module ─────────────────┐   │
│  📝 Section 2       │  │ Prompt: Section Drafting     │   │
│  📝 Section 3       │  │ [Accordion - collapsed]      │   │
│  📝 Section 4       │  └──────────────────────────────┘   │
│  📝 Section 5       │                                       │
│  📝 Section 6       │  Input Data:                         │
│  📝 Section 7       │  • Section Title: "Harvesting..."   │
│                     │  • Topics: [Celtic festivals...]    │
│  [Batch Generate]   │  • Context: [expanded_idea]          │
│  [Select All]       │                                       │
│                     │  Generated Content:                  │
│                     │  [Rich text editor]                  │
│                     │                                       │
│                     │  [Save] [Regenerate] [Preview]       │
└─────────────────────┴───────────────────────────────────────┘
```

### Section States
- **Not Started**: Gray, no content
- **Draft**: Yellow, partial content
- **Complete**: Green, full content
- **Needs Review**: Orange, flagged for attention

### Batch Operations
- **Generate All**: Process all sections sequentially with progress
- **Select All**: Select multiple sections for batch operations
- **Filter**: Show only sections by status (All, Draft, Complete, etc.)

## Workflow Stages

### Stage 1: Drafting
- **Purpose**: Generate initial content for each section
- **Input**: Section title, subtitle, topics, expanded idea
- **Output**: Draft HTML/Markdown content
- **LLM Prompt**: "Section Drafting" - generate engaging content based on section scope

### Stage 2: Refinement
- **Purpose**: Improve and polish generated content
- **Input**: Current draft content, refinement instructions
- **Output**: Refined content with better flow and engagement
- **LLM Prompt**: "Section Refinement" - enhance readability and engagement

### Stage 3: SEO & Metadata
- **Purpose**: Optimize for search engines and social sharing
- **Input**: Refined content, target keywords
- **Output**: SEO-optimized content with meta descriptions
- **LLM Prompt**: "SEO Optimization" - optimize for search visibility

### Stage 4: Images
- **Purpose**: Generate and integrate visual content
- **Input**: Section content, image requirements
- **Output**: Image prompts and integration points
- **LLM Prompt**: "Image Generation" - create visual content prompts

## Technical Implementation Phases

### Phase 1: Foundation (Read-Only)
- [ ] Create `authoring.py` blueprint with basic routes
- [ ] Create section overview template with condensed header
- [ ] Implement section list display (read-only)
- [ ] Add Authoring to main navigation
- [ ] Test data flow from Planning sections

### Phase 2: Individual Section Editing
- [ ] Create section detail template
- [ ] Implement section selection and loading
- [ ] Add basic content editing (text areas)
- [ ] Implement save/load functionality
- [ ] Add section status tracking

### Phase 3: LLM Integration
- [ ] Add authoring configs to LLM module
- [ ] Create section-specific prompts
- [ ] Implement content generation per section
- [ ] Add regeneration functionality
- [ ] Implement content validation

### Phase 4: Batch Operations
- [ ] Implement batch generation across sections
- [ ] Add progress tracking and error handling
- [ ] Implement section filtering and selection
- [ ] Add batch status updates

### Phase 5: Advanced Features
- [ ] Rich text editor integration
- [ ] Content preview functionality
- [ ] Section reordering
- [ ] Export/import capabilities
- [ ] Collaboration features (future)

## Error Handling & Validation

### Content Validation
- **Length**: Enforce minimum/maximum word counts per section
- **Quality**: Check for placeholder text, incomplete sentences
- **Consistency**: Ensure tone and style match across sections
- **SEO**: Validate meta descriptions, keyword density

### Error Recovery
- **Auto-save**: Periodic saves to prevent data loss
- **Conflict Resolution**: Handle concurrent edits gracefully
- **Rollback**: Ability to revert to previous versions
- **Progress Persistence**: Resume interrupted batch operations

## Performance Considerations

### Batch Operations
- **Rate Limiting**: Limit concurrent LLM requests
- **Progress Streaming**: Real-time updates for long operations
- **Error Isolation**: Failures in one section don't stop others
- **Caching**: Cache generated content to avoid regeneration

### Individual Operations
- **Lazy Loading**: Load section content only when needed
- **Optimistic Updates**: Immediate UI feedback for better UX
- **Debounced Saves**: Prevent excessive save operations

## Migration Strategy

### From Old Workflow
- **Preserve**: Existing section data and structure
- **Enhance**: Add new authoring-specific fields
- **Replace**: Old iframe-based UI with native templates
- **Maintain**: Backward compatibility for existing workflows

### Data Migration
- **Sections**: Read from existing `post.sections` JSONB
- **Content**: Add new fields for draft content
- **Metadata**: Add section-level tracking fields
- **History**: Preserve existing workflow history

## Success Metrics

### User Experience
- **Efficiency**: Time to complete all sections
- **Quality**: Content quality and consistency
- **Usability**: Ease of navigation and editing
- **Reliability**: Error rates and recovery success

### Technical Performance
- **Speed**: Page load times and operation response times
- **Scalability**: Performance with large numbers of sections
- **Stability**: Error rates and system uptime
- **Maintainability**: Code quality and documentation

## Future Enhancements

### Advanced Features
- **AI-Powered Suggestions**: Context-aware content recommendations
- **Collaborative Editing**: Multi-user section editing
- **Version Control**: Detailed content history and branching
- **Template System**: Reusable content templates
- **Integration**: Connect with external tools and services

### Analytics & Insights
- **Content Analytics**: Track section performance and engagement
- **Writing Patterns**: Analyze writing style and preferences
- **Efficiency Metrics**: Measure authoring productivity
- **Quality Scores**: Automated content quality assessment

---

This specification provides a comprehensive roadmap for implementing the Authoring area while maintaining consistency with the existing Planning area architecture and patterns.
