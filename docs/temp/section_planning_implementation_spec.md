# Section Planning Implementation Specification

## Overview
This document outlines the complete implementation plan for fixing the section planning functionality, addressing LLM validation failures, and improving the overall user experience.

## Current Issues Analysis

### 1. Topic Brainstorming Problems
- **Format Inconsistency**: LLM sometimes returns JSON, sometimes plain text
- **Quality Control**: No validation of topic length, uniqueness, or quality
- **Context Loss**: Topics generated as isolated strings without thematic hints

### 2. Section Planning Problems
- **Validation Failures**: 100% failure rate requiring fallback allocation
- **Complex Prompt**: Trying to do too much (ordering, titling, allocation, validation)
- **Conflicting Instructions**: "6-8 sections" vs "exactly [SECTION_COUNT]"
- **Poor Topic Matching**: No semantic guidance for topic-to-section allocation

### 3. Display Issues
- **Generic Titles**: "Section 1", "Section 2" instead of meaningful names
- **Poor Formatting**: Messy display with repetitive text
- **No Visual Hierarchy**: Topics displayed as simple tags

## Implementation Plan

### Phase 1: Topic Brainstorming Enhancement

#### 1.1 Prompt Redesign
**File**: `scripts/update_topic_brainstorming_prompt.py`

**New System Prompt**:
```
You are a content strategist specializing in Scottish topics. Generate diverse, specific topic ideas that can be logically grouped into blog sections.

Your expertise includes:
- Scottish history, culture, and traditions
- Content variety (historical, cultural, practical, contemporary, quirky)
- Topic clustering and thematic organization
```

**New User Prompt**:
```
Generate exactly 50 distinct topic ideas about [EXPANDED_IDEA].

REQUIREMENTS:
- Each topic: 5-8 words maximum
- Include variety: historical, cultural, practical, contemporary, quirky
- Ensure topics can be grouped into 6-8 thematic sections
- Return ONLY: ["Topic 1", "Topic 2", ...] (no numbering, no explanations)

VALIDATION: Count topics, check length, ensure uniqueness
```

#### 1.2 Enhanced Topic Parsing
**File**: `blueprints/planning.py` - `parse_brainstorm_topics()` function

**Improvements**:
- Strict JSON parsing with fallback
- Topic length validation (5-8 words)
- Uniqueness checking
- Category tagging (historical, cultural, practical, etc.)
- Semantic similarity detection

**Implementation**:
```python
def parse_brainstorm_topics(content):
    """Enhanced topic parsing with validation"""
    topics = []
    
    # Step 1: Try JSON parsing
    try:
        json_topics = json.loads(content.strip())
        if isinstance(json_topics, list) and len(json_topics) == 50:
            for topic in json_topics:
                if validate_topic(topic):
                    topics.append({
                        'title': topic.strip(),
                        'description': topic.strip(),
                        'category': categorize_topic(topic),
                        'word_count': len(topic.split())
                    })
            return topics
    except:
        pass
    
    # Step 2: Fallback to text parsing
    # ... existing fallback logic
    
    return topics[:50]

def validate_topic(topic):
    """Validate individual topic"""
    words = topic.split()
    return 5 <= len(words) <= 8 and len(topic.strip()) > 0

def categorize_topic(topic):
    """Categorize topic by content type"""
    topic_lower = topic.lower()
    if any(word in topic_lower for word in ['history', 'ancient', 'traditional', 'heritage']):
        return 'historical'
    elif any(word in topic_lower for word in ['culture', 'festival', 'celebration', 'custom']):
        return 'cultural'
    elif any(word in topic_lower for word in ['how', 'guide', 'tips', 'practical']):
        return 'practical'
    elif any(word in topic_lower for word in ['modern', 'contemporary', 'today', 'current']):
        return 'contemporary'
    else:
        return 'general'
```

### Phase 2: Section Planning Redesign

#### 2.1 Two-Stage Approach
**File**: `blueprints/planning.py` - `api_sections_plan()` function

**Stage 1: Thematic Grouping**
- Group topics into 6-8 thematic clusters
- Identify natural topic relationships
- Create cluster names

**Stage 2: Section Creation**
- Convert clusters to blog sections
- Determine optimal section order
- Create compelling section titles
- Validate complete allocation

#### 2.2 New Section Planning Prompt
**File**: `scripts/update_section_planning_prompt.py`

**New System Prompt**:
```
You are a blog structure expert specializing in organizing topics into coherent, engaging sections. Your role is to analyze topic lists and create logical, flowing blog structures.

EXPERTISE:
- Content organization and flow
- Section titling and description
- Topic clustering and allocation
- Reader engagement optimization
```

**New User Prompt**:
```
Given these 50 topics about [EXPANDED_IDEA], group them into exactly [SECTION_COUNT] thematic sections.

PROCESS:
1. Identify natural topic clusters (6-8 groups)
2. Name each cluster thematically
3. Order clusters for logical flow
4. Ensure every topic is allocated exactly once

OUTPUT FORMAT:
{
  "sections": [
    {
      "id": "intro",
      "title": "Introduction to Scottish Autumn Traditions",
      "description": "Overview of Scotland's autumn heritage and cultural significance",
      "topics": ["Topic 1", "Topic 2", ...],
      "order": 1
    }
  ],
  "metadata": {
    "total_sections": [SECTION_COUNT],
    "total_topics": 50,
    "allocated_topics": 50,
    "flow_type": "chronological"
  }
}
```

#### 2.3 Enhanced Validation System
**File**: `blueprints/planning.py` - `validate_sections_response()` function

**Progressive Validation Levels**:
```python
def validate_sections_response(sections_data, original_topics, expected_section_count):
    """Enhanced validation with progressive levels"""
    errors = []
    
    # Level 1: Structure validation
    structure_errors = validate_structure(sections_data)
    if structure_errors:
        return structure_errors
    
    # Level 2: Count validation
    count_errors = validate_counts(sections_data, expected_section_count, len(original_topics))
    if count_errors:
        errors.extend(count_errors)
    
    # Level 3: Allocation validation
    allocation_errors = validate_allocation(sections_data, original_topics)
    if allocation_errors:
        errors.extend(allocation_errors)
    
    # Level 4: Quality validation
    quality_errors = validate_quality(sections_data)
    if quality_errors:
        errors.extend(quality_errors)
    
    return errors

def validate_structure(sections_data):
    """Level 1: Basic structure validation"""
    errors = []
    if not isinstance(sections_data, dict):
        errors.append("Response must be a JSON object")
    if 'sections' not in sections_data:
        errors.append("Response must contain 'sections' array")
    return errors

def validate_counts(sections_data, expected_count, total_topics):
    """Level 2: Count validation with flexibility"""
    errors = []
    sections = sections_data.get('sections', [])
    
    # Flexible section count (6-8 range)
    if not (6 <= len(sections) <= 8):
        errors.append(f"Must have 6-8 sections, got {len(sections)}")
    
    # Check topic allocation
    allocated_count = sum(len(section.get('topics', [])) for section in sections)
    if allocated_count != total_topics:
        errors.append(f"Topic count mismatch: {allocated_count} allocated vs {total_topics} original")
    
    return errors

def validate_allocation(sections_data, original_topics):
    """Level 3: Topic allocation validation with fuzzy matching"""
    errors = []
    sections = sections_data.get('sections', [])
    original_titles = [topic['title'] for topic in original_topics]
    allocated_topics = []
    
    for section in sections:
        for topic in section.get('topics', []):
            allocated_topics.append(topic)
    
    # Check for unallocated topics (with fuzzy matching)
    unallocated = []
    for original in original_titles:
        if not any(fuzzy_match(original, allocated) for allocated in allocated_topics):
            unallocated.append(original)
    
    if unallocated:
        errors.append(f"Unallocated topics: {', '.join(unallocated[:5])}{'...' if len(unallocated) > 5 else ''}")
    
    # Check for duplicates
    if len(set(allocated_topics)) != len(allocated_topics):
        duplicates = [topic for topic in allocated_topics if allocated_topics.count(topic) > 1]
        errors.append(f"Duplicate topics found: {', '.join(set(duplicates))}")
    
    return errors

def validate_quality(sections_data):
    """Level 4: Quality validation"""
    errors = []
    sections = sections_data.get('sections', [])
    
    for i, section in enumerate(sections):
        if not section.get('title') or len(section.get('title', '')) < 10:
            errors.append(f"Section {i+1} has inadequate title")
        if not section.get('description') or len(section.get('description', '')) < 20:
            errors.append(f"Section {i+1} has inadequate description")
        if len(section.get('topics', [])) < 3:
            errors.append(f"Section {i+1} has too few topics")
    
    return errors

def fuzzy_match(str1, str2, threshold=0.8):
    """Fuzzy string matching for topic validation"""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio() >= threshold
```

#### 2.4 Auto-Correction System
**File**: `blueprints/planning.py` - `auto_correct_sections()` function

```python
def auto_correct_sections(sections_data, original_topics):
    """Auto-correct minor issues in section data"""
    corrections = []
    
    # Fix empty sections
    for section in sections_data.get('sections', []):
        if not section.get('topics'):
            # Find nearby topics to allocate
            nearby_topics = find_nearby_topics(section, original_topics)
            section['topics'] = nearby_topics
            corrections.append(f"Added {len(nearby_topics)} topics to empty section")
    
    # Fix duplicate topics
    all_topics = []
    for section in sections_data.get('sections', []):
        unique_topics = []
        for topic in section.get('topics', []):
            if topic not in all_topics:
                unique_topics.append(topic)
                all_topics.append(topic)
        section['topics'] = unique_topics
    
    # Fix inadequate titles
    for section in sections_data.get('sections', []):
        if not section.get('title') or len(section.get('title', '')) < 10:
            section['title'] = generate_section_title(section.get('topics', []))
            corrections.append("Generated section title")
    
    return corrections
```

### Phase 3: Display System Enhancement

#### 3.1 Enhanced Visual Design
**File**: `templates/planning/concept/sections.html` - `displaySections()` function

**New Display Format**:
```javascript
function displaySections(sectionsData) {
    const resultsDisplay = document.getElementById('llm-results-display');
    
    let sections = sectionsData.sections || [];
    let metadata = sectionsData.metadata || {};
    
    if (sections.length === 0) {
        resultsDisplay.innerHTML = '<div class="no-results">No sections generated. Try again with different settings.</div>';
        return;
    }
    
    let sectionsHTML = '<div class="sections-list">';
    
    // Add metadata info
    if (metadata.fallback) {
        sectionsHTML += '<div class="fallback-notice">⚠️ Using fallback allocation due to LLM validation issues</div>';
    }
    
    // Display sections with enhanced formatting
    sections.forEach((section, index) => {
        const topicCount = section.topics ? section.topics.length : 0;
        const categoryCounts = getCategoryCounts(section.topics || []);
        
        sectionsHTML += `
            <div class="section-item enhanced" data-section-id="${section.id || index}">
                <div class="section-header">
                    <h4 class="section-title">${section.title || `Section ${index + 1}`}</h4>
                    <div class="section-meta">
                        <span class="topic-count">${topicCount} topics</span>
                        <span class="section-order">${section.order || index + 1}</span>
                    </div>
                </div>
                <div class="section-description">${section.description || 'No description provided'}</div>
                <div class="section-topics">
                    <div class="topics-header">
                        <h5>Topics in this section:</h5>
                        <div class="category-indicators">
                            ${Object.entries(categoryCounts).map(([cat, count]) => 
                                `<span class="category-tag ${cat}">${cat} (${count})</span>`
                            ).join('')}
                        </div>
                    </div>
                    <div class="topics-grid">
                        ${(section.topics || []).map(topic => 
                            `<div class="topic-item enhanced" data-topic="${topic}">
                                <span class="topic-text">${topic}</span>
                            </div>`
                        ).join('')}
                    </div>
                </div>
            </div>
        `;
    });
    
    sectionsHTML += '</div>';
    resultsDisplay.innerHTML = sectionsHTML;
}

function getCategoryCounts(topics) {
    const categories = {};
    topics.forEach(topic => {
        const category = categorizeTopic(topic);
        categories[category] = (categories[category] || 0) + 1;
    });
    return categories;
}

function categorizeTopic(topic) {
    const topicLower = topic.toLowerCase();
    if (topicLower.includes('history') || topicLower.includes('ancient') || topicLower.includes('traditional')) {
        return 'historical';
    } else if (topicLower.includes('culture') || topicLower.includes('festival') || topicLower.includes('celebration')) {
        return 'cultural';
    } else if (topicLower.includes('how') || topicLower.includes('guide') || topicLower.includes('tips')) {
        return 'practical';
    } else if (topicLower.includes('modern') || topicLower.includes('contemporary') || topicLower.includes('today')) {
        return 'contemporary';
    }
    return 'general';
}
```

#### 3.2 Enhanced CSS Styling
**File**: `templates/planning/concept/sections.html` - CSS section

```css
/* Enhanced Section Display */
.section-item.enhanced {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    transition: all 0.2s ease;
}

.section-item.enhanced:hover {
    border-color: #3b82f6;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
}

.section-title {
    color: #f1f5f9;
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0;
    flex: 1;
}

.section-meta {
    display: flex;
    gap: 1rem;
    align-items: center;
}

.topic-count {
    background: #3b82f6;
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
}

.section-order {
    background: #64748b;
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
}

.section-description {
    color: #94a3b8;
    font-size: 1rem;
    line-height: 1.5;
    margin-bottom: 1.5rem;
}

.topics-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.topics-header h5 {
    color: #f1f5f9;
    font-size: 1rem;
    font-weight: 500;
    margin: 0;
}

.category-indicators {
    display: flex;
    gap: 0.5rem;
}

.category-tag {
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
}

.category-tag.historical {
    background: #fef3c7;
    color: #92400e;
}

.category-tag.cultural {
    background: #dbeafe;
    color: #1e40af;
}

.category-tag.practical {
    background: #dcfce7;
    color: #166534;
}

.category-tag.contemporary {
    background: #fce7f3;
    color: #be185d;
}

.category-tag.general {
    background: #f1f5f9;
    color: #475569;
}

.topics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 0.75rem;
}

.topic-item.enhanced {
    background: #334155;
    border: 1px solid #475569;
    border-radius: 8px;
    padding: 0.75rem;
    transition: all 0.2s ease;
}

.topic-item.enhanced:hover {
    background: #475569;
    border-color: #64748b;
}

.topic-text {
    color: #e2e8f0;
    font-size: 0.875rem;
    line-height: 1.4;
}
```

### Phase 4: Implementation Steps

#### Step 1: Create Update Scripts
1. Create `scripts/update_topic_brainstorming_prompt.py`
2. Create `scripts/update_section_planning_prompt.py`
3. Run both scripts to update database prompts

#### Step 2: Enhance Backend Functions
1. Update `parse_brainstorm_topics()` in `blueprints/planning.py`
2. Update `validate_sections_response()` in `blueprints/planning.py`
3. Add `auto_correct_sections()` function
4. Add `fuzzy_match()` helper function

#### Step 3: Update Frontend Display
1. Update `displaySections()` function in `templates/planning/concept/sections.html`
2. Add enhanced CSS styling
3. Add category detection JavaScript

#### Step 4: Testing & Validation
1. Test topic generation with new prompt
2. Test section planning with various topic sets
3. Validate display formatting
4. Test error handling and fallback mechanisms

#### Step 5: Documentation & Cleanup
1. Update API documentation
2. Add error handling documentation
3. Clean up old code and comments

## Rollback Plan

If implementation fails:
1. Revert database prompts to previous versions
2. Restore original functions in `blueprints/planning.py`
3. Revert frontend changes in `templates/planning/concept/sections.html`
4. Test original functionality

## Success Criteria

1. **Topic Generation**: 95%+ success rate for 50-topic JSON output
2. **Section Planning**: 90%+ validation success rate (vs current 0%)
3. **Display Quality**: Professional, organized section presentation
4. **Error Handling**: Graceful degradation with auto-correction
5. **User Experience**: Clear, intuitive interface with meaningful section titles

## Risk Mitigation

1. **Incremental Implementation**: Implement one phase at a time
2. **Comprehensive Testing**: Test each component thoroughly
3. **Rollback Capability**: Maintain ability to revert changes
4. **Documentation**: Document all changes for future reference
5. **User Feedback**: Gather feedback during implementation

## Timeline Estimate

- **Phase 1**: 2-3 hours (Topic Brainstorming Enhancement)
- **Phase 2**: 4-5 hours (Section Planning Redesign)
- **Phase 3**: 2-3 hours (Display System Enhancement)
- **Phase 4**: 2-3 hours (Implementation & Testing)
- **Total**: 10-14 hours

This implementation plan provides a comprehensive, robust solution to the section planning issues while maintaining system stability and providing clear rollback capabilities.