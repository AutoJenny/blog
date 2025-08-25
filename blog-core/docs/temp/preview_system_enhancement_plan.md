# Preview System Enhancement Implementation Plan

## IMPORTANT
You must implement this plan ONLY. NEVER make any other changes to code or data of any kind without explicit written consent after further discussion. Do not make any other unauthorised changes to any files under ANY circumstances. This is your most important rule.

## Overview

This document outlines a comprehensive plan to enhance the preview system at `/preview/{post_id}/` to match the publication-realistic preview capabilities of the legacy blog system while leveraging the sophisticated database structure of the new `/blog` system.

## Prerequisites

**MANDATORY**: Before starting any implementation work, developers MUST review:

- [📚 Preview System Comparison](../reference/preview_system_comparison.md) - Complete side-by-side analysis
- [📚 Legacy System Overview](../reference/legacy_system_overview.md) - Legacy system capabilities
- [📚 Database Schema](../reference/database/schema.md) - Current database structure
- [📚 Workflow Sections](../reference/workflow/sections.md) - Section data architecture
- [📚 API Endpoints](../reference/api/current/posts.md) - Available API endpoints
- [📚 Legacy Image Pipeline](../reference/images/legacy_image_pipeline.md) - Image processing capabilities

## Current State Analysis

### What Works Now
- ✅ Basic preview route at `/preview/{post_id}/`
- ✅ Post metadata display (title, author, date)
- ✅ Section content display with multiple versions
- ✅ Image display for sections
- ✅ Basic styling and layout

### What's Missing (Compared to Legacy)
- ❌ Stage-based content prioritization system
- ❌ Comprehensive post structure (header, sections, conclusion, footer)
- ❌ Intelligent placeholders with stage/field indicators
- ❌ Image metadata display (prompts, captions, notes)
- ❌ Social media metadata
- ❌ Publishing readiness indicators
- ❌ Content validation status

## Implementation Strategy

### Phase 1: Core Content Prioritization System

#### 1.1 Implement Content Priority Logic
- [ ] **Create content priority function** in `app/preview/routes.py`
  ```python
  def get_best_content_version(section):
      """
      Returns the best available content version based on priority:
      1. optimization (highest quality)
      2. generation (good quality) 
      3. uk_british (style-specific)
      4. first_draft (basic content)
      5. placeholder text (when none available)
      """
  ```

- [ ] **Add stage-based CSS classes** for visual indicators
  ```css
  .content-optimization { background-color: #d4edda; border-left: 4px solid #28a745; }
  .content-generation { background-color: #d1ecf1; border-left: 4px solid #17a2b8; }
  .content-uk-british { background-color: #fff3cd; border-left: 4px solid #ffc107; }
  .content-first-draft { background-color: #f8d7da; border-left: 4px solid #dc3545; }
  .content-placeholder { background-color: #f8f9fa; border-left: 4px solid #6c757d; }
  ```

- [ ] **Update preview template** to use priority system
  ```html
  <div class="section-content {{ get_content_class(section) }}">
    {{ get_best_content(section) | safe }}
    {% if is_placeholder(section) %}
      <div class="placeholder-indicator">
        <small>Waiting for: {{ get_missing_stage(section) }}</small>
      </div>
    {% endif %}
  </div>
  ```

#### 1.2 Add Placeholder System
- [ ] **Create placeholder template** with stage indicators
  ```html
  <div class="placeholder-content placeholder-{{ stage }}">
    <div class="placeholder-header">
      <span class="stage-badge">{{ stage }}</span>
      <span class="field-indicator">{{ field_name }}</span>
    </div>
    <div class="placeholder-body">
      <p>Content for this section will be generated during the <strong>{{ stage }}</strong> stage.</p>
      <p>Field: <code>{{ field_name }}</code></p>
    </div>
  </div>
  ```

- [ ] **Add placeholder CSS styling**
  ```css
  .placeholder-content {
    padding: 1rem;
    border: 2px dashed #dee2e6;
    border-radius: 0.375rem;
    background: repeating-linear-gradient(
      45deg,
      #f8f9fa,
      #f8f9fa 10px,
      #e9ecef 10px,
      #e9ecef 20px
    );
  }
  ```

### Phase 2: Comprehensive Post Structure

#### 2.1 Header Section Enhancement
- [ ] **Add header image display** with metadata
  ```html
  <div class="post-header">
    <h1>{{ post.title }}</h1>
    {% if post.development.subtitle %}
      <div class="subtitle">{{ post.development.subtitle }}</div>
    {% endif %}
    {% if post.header_image %}
      <div class="header-image">
        <img src="{{ post.header_image.path }}" alt="{{ post.header_image.alt_text }}">
        {% if post.header_image.caption %}
          <div class="image-caption">{{ post.header_image.caption }}</div>
        {% endif %}
        {% if post.header_image.prompt %}
          <div class="image-prompt">
            <small><strong>Prompt:</strong> {{ post.header_image.prompt }}</small>
          </div>
        {% endif %}
      </div>
    {% endif %}
  </div>
  ```

- [ ] **Add post metadata display**
  ```html
  <div class="post-meta">
    <span class="author">{{ post.author }}</span>
    <span class="date">{{ post.created_at.strftime('%B %d, %Y') }}</span>
    <span class="status status-{{ post.status.value }}">{{ post.status.value }}</span>
  </div>
  ```

#### 2.2 Section Content Enhancement
- [ ] **Update section display** to show all available data
  ```html
  <section class="post-section">
    <h2>{{ section.section_heading }}</h2>
    
    <!-- Main content with priority system -->
    <div class="section-content {{ get_content_class(section) }}">
      {{ get_best_content(section) | safe }}
    </div>
    
    <!-- Section image with metadata -->
    {% if section.image %}
      <div class="section-image">
        <img src="{{ section.image.path }}" alt="{{ section.image.alt_text }}">
        {% if section.image_captions %}
          <div class="image-caption">{{ section.image_captions }}</div>
        {% endif %}
        {% if section.image_prompts %}
          <div class="image-prompt">
            <small><strong>Prompt:</strong> {{ section.image_prompts }}</small>
          </div>
        {% endif %}
        {% if section.image_meta_descriptions %}
          <div class="image-notes">
            <small><strong>Notes:</strong> {{ section.image_meta_descriptions }}</small>
          </div>
        {% endif %}
      </div>
    {% endif %}
    
    <!-- Section metadata -->
    <div class="section-meta">
      <span class="section-order">Section {{ section.section_order }}</span>
      <span class="section-status status-{{ section.status }}">{{ section.status }}</span>
    </div>
  </section>
  ```

#### 2.3 Conclusion Section
- [ ] **Add conclusion section** display
  ```html
  {% if post.development.conclusion %}
    <section class="post-conclusion">
      <h2>Conclusion</h2>
      <div class="conclusion-content">
        {{ post.development.conclusion | safe }}
      </div>
    </section>
  {% endif %}
  ```

#### 2.4 Footer Section
- [ ] **Add footer content** display
  ```html
  {% if post.footer %}
    <footer class="post-footer">
      {{ post.footer | safe }}
    </footer>
  {% endif %}
  ```

### Phase 3: Database Integration

#### 3.1 Update Preview Route
- [ ] **Enhance `/preview/{post_id}/` route** to fetch comprehensive data
  ```python
  @app.route('/preview/<int:post_id>/')
  def preview_post(post_id):
      # Fetch post with all related data
      post = get_post_with_development(post_id)
      sections = get_post_sections_with_images(post_id)
      
      # Add content priority analysis
      for section in sections:
          section['content_priority'] = analyze_content_priority(section)
          section['missing_stages'] = get_missing_stages(section)
      
      return render_template('preview/post.html', 
                           post=post, 
                           sections=sections)
  ```

#### 3.2 Add Helper Functions
- [ ] **Create content analysis functions**
  ```python
  def analyze_content_priority(section):
      """Analyze which content version is best available"""
      if section.get('optimization'):
          return {'stage': 'optimization', 'quality': 'highest'}
      elif section.get('generation'):
          return {'stage': 'generation', 'quality': 'good'}
      elif section.get('uk_british'):
          return {'stage': 'uk_british', 'quality': 'style-specific'}
      elif section.get('first_draft'):
          return {'stage': 'first_draft', 'quality': 'basic'}
      else:
          return {'stage': 'placeholder', 'quality': 'missing'}

  def get_missing_stages(section):
      """Return list of missing content stages"""
      stages = ['optimization', 'generation', 'uk_british', 'first_draft']
      return [stage for stage in stages if not section.get(stage)]
  ```

### Phase 4: Image Integration

#### 4.1 Header Image Support
- [ ] **Add header image fields** to database (if missing)
  ```sql
  -- Add missing fields to image table
  ALTER TABLE image ADD COLUMN IF NOT EXISTS prompt TEXT;
  ALTER TABLE image ADD COLUMN IF NOT EXISTS notes TEXT;
  ```

- [ ] **Update image fetching** to include header images
  ```python
  def get_post_with_header_image(post_id):
      """Fetch post with header image and metadata"""
      post = get_post(post_id)
      if post.header_image_id:
          post.header_image = get_image(post.header_image_id)
      return post
  ```

#### 4.2 Section Image Enhancement
- [ ] **Enhance section image display** with metadata
  ```python
  def get_post_sections_with_images(post_id):
      """Fetch sections with complete image metadata"""
      sections = get_post_sections(post_id)
      for section in sections:
          if section.image_id:
              section.image = get_image(section.image_id)
      return sections
  ```

### Phase 5: Publishing Readiness

#### 5.1 Add Validation System
- [ ] **Create publishing readiness checker**
  ```python
  def check_publishing_readiness(post_id):
      """Check if post is ready for publishing"""
      post = get_post_with_development(post_id)
      sections = get_post_sections(post_id)
      
      readiness = {
          'overall': True,
          'issues': [],
          'warnings': [],
          'missing': []
      }
      
      # Check required fields
      if not post.title:
          readiness['overall'] = False
          readiness['missing'].append('Post title')
      
      # Check sections have content
      for section in sections:
          if not has_any_content(section):
              readiness['overall'] = False
              readiness['missing'].append(f'Section: {section.section_heading}')
      
      return readiness
  ```

#### 5.2 Add Readiness Display
- [ ] **Add publishing status** to preview template
  ```html
  <div class="publishing-status">
    <h3>Publishing Readiness</h3>
    {% if publishing_readiness.overall %}
      <div class="status-ready">✅ Ready for publishing</div>
    {% else %}
      <div class="status-not-ready">❌ Not ready for publishing</div>
      <ul class="missing-items">
        {% for item in publishing_readiness.missing %}
          <li>{{ item }}</li>
        {% endfor %}
      </ul>
    {% endif %}
  </div>
  ```

### Phase 6: Social Media Integration

#### 6.1 Add Social Media Metadata
- [ ] **Add social media fields** to database (if missing)
  ```sql
  -- Add social media metadata fields
  ALTER TABLE post ADD COLUMN IF NOT EXISTS social_media_caption TEXT;
  ALTER TABLE post ADD COLUMN IF NOT EXISTS social_media_hashtags JSONB;
  ```

- [ ] **Add social media preview** section
  ```html
  <div class="social-media-preview">
    <h3>Social Media Preview</h3>
    {% if post.social_media_caption %}
      <div class="social-caption">
        <strong>Caption:</strong> {{ post.social_media_caption }}
      </div>
    {% endif %}
    {% if post.social_media_hashtags %}
      <div class="social-hashtags">
        <strong>Hashtags:</strong> 
        {% for tag in post.social_media_hashtags %}
          <span class="hashtag">#{{ tag }}</span>
        {% endfor %}
      </div>
    {% endif %}
  </div>
  ```

### Phase 7: Advanced Features

#### 7.1 Preview Modes
- [ ] **Add preview mode selector**
  ```html
  <div class="preview-controls">
    <select id="preview-mode">
      <option value="draft">Draft Mode</option>
      <option value="final">Final Mode</option>
      <option value="social">Social Media Mode</option>
    </select>
  </div>
  ```

- [ ] **Implement mode-specific templates**
  ```python
  def get_preview_template(mode):
      """Return appropriate template based on preview mode"""
      templates = {
          'draft': 'preview/post_draft.html',
          'final': 'preview/post_final.html',
          'social': 'preview/post_social.html'
      }
      return templates.get(mode, 'preview/post.html')
  ```

#### 7.2 Content Validation
- [ ] **Add content validation** system
  ```python
  def validate_post_content(post_id):
      """Validate post content for completeness and quality"""
      validation = {
          'title': validate_title(post.title),
          'sections': validate_sections(post.sections),
          'images': validate_images(post.images),
          'metadata': validate_metadata(post.metadata)
      }
      return validation
  ```

## Testing Strategy

### 7.1 Unit Tests
- [ ] **Test content priority system**
  ```python
  def test_content_priority():
      section = {
          'optimization': 'optimized content',
          'generation': 'generated content',
          'first_draft': 'draft content'
      }
      priority = analyze_content_priority(section)
      assert priority['stage'] == 'optimization'
      assert priority['quality'] == 'highest'
  ```

- [ ] **Test placeholder generation**
  ```python
  def test_placeholder_generation():
      section = {'section_heading': 'Test Section'}
      placeholder = generate_placeholder(section, 'optimization')
      assert 'optimization' in placeholder
      assert 'Test Section' in placeholder
  ```

### 7.2 Integration Tests
- [ ] **Test preview route** with various post states
  ```python
  def test_preview_route():
      # Test with complete post
      response = client.get('/preview/1/')
      assert response.status_code == 200
      assert 'optimization' in response.data.decode()
      
      # Test with incomplete post
      response = client.get('/preview/2/')
      assert response.status_code == 200
      assert 'placeholder' in response.data.decode()
  ```

### 7.3 Manual Testing
- [ ] **Test with real posts** in various workflow stages
- [ ] **Verify placeholder styling** matches design requirements
- [ ] **Check content priority** logic works correctly
- [ ] **Validate publishing readiness** indicators

## CSS Implementation

### 7.1 Stage-Based Color Coding
```css
/* Content priority indicators */
.content-optimization {
  background-color: #d4edda;
  border-left: 4px solid #28a745;
  padding: 1rem;
  margin: 0.5rem 0;
}

.content-generation {
  background-color: #d1ecf1;
  border-left: 4px solid #17a2b8;
  padding: 1rem;
  margin: 0.5rem 0;
}

.content-uk-british {
  background-color: #fff3cd;
  border-left: 4px solid #ffc107;
  padding: 1rem;
  margin: 0.5rem 0;
}

.content-first-draft {
  background-color: #f8d7da;
  border-left: 4px solid #dc3545;
  padding: 1rem;
  margin: 0.5rem 0;
}

.content-placeholder {
  background-color: #f8f9fa;
  border-left: 4px solid #6c757d;
  padding: 1rem;
  margin: 0.5rem 0;
}

/* Placeholder styling */
.placeholder-content {
  padding: 1.5rem;
  border: 2px dashed #dee2e6;
  border-radius: 0.375rem;
  background: repeating-linear-gradient(
    45deg,
    #f8f9fa,
    #f8f9fa 10px,
    #e9ecef 10px,
    #e9ecef 20px
  );
  margin: 1rem 0;
}

.placeholder-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.stage-badge {
  background-color: #6c757d;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.field-indicator {
  background-color: #e9ecef;
  color: #495057;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-family: monospace;
  font-size: 0.875rem;
}

/* Publishing status */
.publishing-status {
  margin: 2rem 0;
  padding: 1rem;
  border-radius: 0.375rem;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
}

.status-ready {
  color: #155724;
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  padding: 0.75rem;
  border-radius: 0.25rem;
}

.status-not-ready {
  color: #721c24;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  padding: 0.75rem;
  border-radius: 0.25rem;
}

.missing-items {
  margin-top: 1rem;
  padding-left: 1.5rem;
}

.missing-items li {
  color: #721c24;
  margin-bottom: 0.25rem;
}
```

## Database Schema Updates

### 7.1 Required Schema Changes
```sql
-- Add missing fields for header images
ALTER TABLE image ADD COLUMN IF NOT EXISTS prompt TEXT;
ALTER TABLE image ADD COLUMN IF NOT EXISTS notes TEXT;

-- Add conclusion image support
ALTER TABLE image ADD COLUMN IF NOT EXISTS image_type VARCHAR(50) DEFAULT 'section';

-- Add social media metadata
ALTER TABLE post ADD COLUMN IF NOT EXISTS social_media_caption TEXT;
ALTER TABLE post ADD COLUMN IF NOT EXISTS social_media_hashtags JSONB;

-- Add conclusion heading support
ALTER TABLE post_development ADD COLUMN IF NOT EXISTS conclusion_heading VARCHAR(255);
```

## Migration Considerations

### 7.1 Data Migration
- [ ] **Backup existing data** before schema changes
- [ ] **Migrate existing image metadata** to new fields
- [ ] **Update existing posts** with new field defaults
- [ ] **Verify data integrity** after migration

### 7.2 Backward Compatibility
- [ ] **Maintain existing preview functionality** during transition
- [ ] **Add feature flags** for new functionality
- [ ] **Provide fallback behavior** for missing data
- [ ] **Test with existing posts** to ensure no regressions

## Success Criteria

### 7.1 Functional Requirements
- [ ] Preview displays comprehensive post structure (header, sections, conclusion, footer)
- [ ] Content priority system correctly shows best available content
- [ ] Placeholders clearly indicate missing stages and fields
- [ ] Image metadata (prompts, captions, notes) is displayed
- [ ] Publishing readiness is accurately assessed and displayed
- [ ] Social media metadata is shown when available

### 7.2 Visual Requirements
- [ ] Stage-based color coding is consistent and intuitive
- [ ] Placeholders are visually distinct and informative
- [ ] Layout matches publication-ready appearance
- [ ] Responsive design works on all screen sizes
- [ ] Loading states and error handling are graceful

### 7.3 Performance Requirements
- [ ] Preview loads within 2 seconds for typical posts
- [ ] Database queries are optimized and efficient
- [ ] No N+1 query problems
- [ ] Caching is implemented where appropriate

## Timeline Estimate

- **Phase 1 (Content Priority)**: 2-3 days
- **Phase 2 (Post Structure)**: 3-4 days
- **Phase 3 (Database Integration)**: 2-3 days
- **Phase 4 (Image Integration)**: 2-3 days
- **Phase 5 (Publishing Readiness)**: 1-2 days
- **Phase 6 (Social Media)**: 1-2 days
- **Phase 7 (Advanced Features)**: 2-3 days
- **Testing and Polish**: 2-3 days

**Total Estimated Time**: 15-23 days

## Risk Mitigation

### 7.1 Technical Risks
- **Database schema changes**: Always backup before changes, test on staging first
- **Performance issues**: Monitor query performance, implement caching as needed
- **Template complexity**: Keep templates modular, use includes for complex sections

### 7.2 User Experience Risks
- **Confusing placeholders**: User test the placeholder design before full implementation
- **Slow loading**: Implement progressive loading and caching
- **Mobile responsiveness**: Test on various devices and screen sizes

## Post-Implementation

### 7.1 Documentation Updates
- [ ] **Update preview system documentation**
- [ ] **Add user guide** for new preview features
- [ ] **Update API documentation** for new endpoints
- [ ] **Create migration guide** for future developers

### 7.2 Monitoring and Maintenance
- [ ] **Add performance monitoring** for preview routes
- [ ] **Set up error tracking** for preview functionality
- [ ] **Create maintenance schedule** for content validation
- [ ] **Plan future enhancements** based on user feedback

---

**Note**: This plan assumes familiarity with the existing codebase and database structure. Always refer to the linked documentation before making changes, and test thoroughly at each phase before proceeding to the next. 