# 3-Step Topic Allocation Process - Implementation Plan
## Comprehensive Blog Structure Design and Topic Allocation

**Date:** 2025-01-29  
**Status:** PLANNING - Ready for implementation  
**Replaces:** Current 2-step grouping/titling workflow  
**Goal:** Systematic topic allocation with proper data persistence

---

## 🎯 **OVERVIEW OF 3-STEP PROCESS**

### **Step 1: Section Structure Design**
**Purpose:** Design 7-section blog structure that encompasses all ideas  
**Input:** 50+ brainstormed topics + expanded idea  
**Output:** 7 thematic section concepts with clear boundaries  
**Benefit:** Ensures comprehensive coverage and logical flow

### **Step 2: Topic Allocation** 
**Purpose:** Assign each topic to its most relevant section  
**Input:** 50+ topics + 7 section structures  
**Output:** One-to-one topic-to-section mapping  
**Benefit:** Ensures no topics are lost or duplicated

### **Step 3: Topic Refinement** (Optional)
**Purpose:** Reduce topics per section to optimal 5-7 topics  
**Input:** Sections with too many topics  
**Output:** Refined topic lists maintaining content value  
**Benefit:** Prevents overwhelming sections while preserving quality

---

## 🏗️ **IMPLEMENTATION ARCHITECTURE**

### **New API Endpoints Required:**

#### **Step 1: Section Structure Design**
- `POST /api/sections/design-structure` - Design 7-section blog structure
- `GET /api/sections/design-structure/<post_id>` - Retrieve structure design

#### **Step 2: Topic Allocation**
- `POST /api/sections/allocate-topics` - Allocate topics to sections
- `GET /api/sections/allocate-topics/<post_id>` - Retrieve topic allocation

#### **Step 3: Topic Refinement**
- `POST /api/sections/refine-topics` - Refine topics per section
- `GET /api/sections/refine-topics/<post_id>` - Retrieve refined topics

### **Database Schema Updates:**

#### **New Fields in `post_development` Table:**
```sql
-- Step 1: Section Structure Design
section_structure JSON,           -- 7 section concepts with boundaries
structure_design_at TIMESTAMP,    -- When structure was designed

-- Step 2: Topic Allocation  
topic_allocation JSON,            -- One-to-one topic-to-section mapping
allocation_completed_at TIMESTAMP, -- When allocation was completed

-- Step 3: Topic Refinement
refined_topics JSON,              -- Final refined topic lists per section
refinement_completed_at TIMESTAMP -- When refinement was completed
```

#### **Data Structure Examples:**

**Section Structure (Step 1):**
```json
{
  "sections": [
    {
      "id": "section_1",
      "theme": "Historical Foundations",
      "boundaries": "Celtic roots, ancient traditions, historical development",
      "exclusions": "Modern practices, contemporary celebrations",
      "order": 1,
      "description": "Explores the Celtic origins and historical evolution of Scottish autumnal traditions"
    }
  ],
  "metadata": {
    "total_sections": 7,
    "design_principles": "Chronological flow from ancient to modern",
    "audience_focus": "Scottish heritage enthusiasts"
  }
}
```

**Topic Allocation (Step 2):**
```json
{
  "allocations": [
    {
      "section_id": "section_1",
      "topics": [
        "Celtic Roots of Samhain Traditions",
        "The History of Ceres Festival in Modern Scotland",
        "Samhain Traditions in Scottish Christianity"
      ],
      "allocation_reason": "Historical and Celtic-focused topics"
    }
  ],
  "metadata": {
    "total_topics_allocated": 32,
    "unallocated_topics": [],
    "allocation_method": "semantic_matching_with_validation"
  }
}
```

**Refined Topics (Step 3):**
```json
{
  "refined_sections": [
    {
      "section_id": "section_1",
      "final_topics": [
        "Celtic Roots of Samhain Traditions",
        "The History of Ceres Festival in Modern Scotland",
        "Samhain Traditions in Scottish Christianity"
      ],
      "refinement_notes": "Selected 3 most representative topics",
      "excluded_topics": ["Ancient Scottish Practices for Autumn Crop Succession"]
    }
  ],
  "metadata": {
    "refinement_criteria": "Representativeness, uniqueness, engagement",
    "average_topics_per_section": 4.6
  }
}
```

---

## 🔧 **DETAILED IMPLEMENTATION STEPS**

### **Phase 1: Backend API Development**

#### **Step 1.1: Section Structure Design API**
```python
@bp.route('/api/sections/design-structure', methods=['POST'])
def api_design_section_structure():
    """Step 1: Design 7-section blog structure"""
    try:
        data = request.get_json()
        topics = data.get('topics', [])
        expanded_idea = data.get('expanded_idea', '')
        post_id = data.get('post_id')
        
        # Create structure design prompt
        structure_prompt = f"""Design a 7-section blog structure for: {expanded_idea}
        
TOPICS TO ENCOMPASS ({len(topics)} topics):
{format_topics_for_prompt(topics)}

REQUIREMENTS:
- Create exactly 7 sections that together cover all topics
- Each section should have clear thematic boundaries
- Sections should flow logically from ancient to modern
- Each section should be engaging for Scottish heritage audience
- Specify what each section includes and excludes

OUTPUT FORMAT: Return ONLY valid JSON:
{{
  "sections": [
    {{
      "id": "section_1",
      "theme": "Clear thematic focus",
      "boundaries": "What this section covers",
      "exclusions": "What this section does NOT cover",
      "order": 1,
      "description": "Engaging description for readers"
    }}
  ],
  "metadata": {{
    "total_sections": 7,
    "design_principles": "How sections relate to each other",
    "audience_focus": "Target audience description"
  }}
}}"""
        
        # Execute LLM and save results
        result = execute_llm_and_save_structure(post_id, structure_prompt)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

#### **Step 1.2: Topic Allocation API**
```python
@bp.route('/api/sections/allocate-topics', methods=['POST'])
def api_allocate_topics():
    """Step 2: Allocate topics to sections"""
    try:
        data = request.get_json()
        topics = data.get('topics', [])
        section_structure = data.get('section_structure', {})
        post_id = data.get('post_id')
        
        # Create allocation prompt
        allocation_prompt = f"""Allocate each topic to its most appropriate section.

SECTION STRUCTURE:
{format_section_structure(section_structure)}

TOPICS TO ALLOCATE ({len(topics)} topics):
{format_topics_for_prompt(topics)}

REQUIREMENTS:
- Each topic must be allocated to exactly ONE section
- All topics must be allocated (no unallocated topics)
- Choose the section where each topic fits BEST
- Consider thematic boundaries and exclusions
- Ensure balanced distribution across sections

OUTPUT FORMAT: Return ONLY valid JSON:
{{
  "allocations": [
    {{
      "section_id": "section_1",
      "topics": ["Topic 1", "Topic 2", "Topic 3"],
      "allocation_reason": "Why these topics belong here"
    }}
  ],
  "metadata": {{
    "total_topics_allocated": {len(topics)},
    "unallocated_topics": [],
    "allocation_method": "semantic_matching_with_validation"
  }}
}}"""
        
        # Execute LLM and save results
        result = execute_llm_and_save_allocation(post_id, allocation_prompt)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

#### **Step 1.3: Topic Refinement API**
```python
@bp.route('/api/sections/refine-topics', methods=['POST'])
def api_refine_topics():
    """Step 3: Refine topics per section (optional)"""
    try:
        data = request.get_json()
        allocations = data.get('allocations', [])
        section_structure = data.get('section_structure', {})
        post_id = data.get('post_id')
        
        # Identify sections with too many topics (>7)
        sections_to_refine = []
        for allocation in allocations:
            if len(allocation['topics']) > 7:
                sections_to_refine.append(allocation)
        
        if not sections_to_refine:
            return jsonify({
                'success': True,
                'message': 'No sections need refinement',
                'refined_sections': allocations
            })
        
        # Create refinement prompt for each overloaded section
        refined_sections = []
        for section in sections_to_refine:
            refinement_prompt = f"""Refine topics for section: {section['section_id']}
            
SECTION CONTEXT:
{get_section_context(section['section_id'], section_structure)}

CURRENT TOPICS ({len(section['topics'])} topics):
{format_topics_for_prompt(section['topics'])}

REQUIREMENTS:
- Select the 5-7 BEST topics for this section
- Maintain thematic coherence
- Ensure comprehensive coverage
- Prioritize most engaging and representative topics
- Explain why excluded topics were removed

OUTPUT FORMAT: Return ONLY valid JSON:
{{
  "section_id": "{section['section_id']}",
  "final_topics": ["Selected Topic 1", "Selected Topic 2"],
  "refinement_notes": "Why these topics were selected",
  "excluded_topics": ["Removed Topic 1", "Removed Topic 2"]
}}"""
            
            # Execute LLM for this section
            refined_section = execute_llm_refinement(refinement_prompt)
            refined_sections.append(refined_section)
        
        # Save refined results
        save_refined_topics(post_id, refined_sections)
        
        return jsonify({
            'success': True,
            'refined_sections': refined_sections
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### **Phase 2: Frontend Implementation**

#### **Step 2.1: Update Grouping Page Structure**
```html
<!-- Replace current grouping.html with 3-step process -->
<div class="three-step-process">
    <!-- Step 1: Section Structure Design -->
    <div class="step-container" id="step-1">
        <h3>Step 1: Design Section Structure</h3>
        <div class="step-content">
            <div class="input-panel">
                <h4>Input: Generated Topics</h4>
                <div id="topics-display"></div>
            </div>
            <div class="action-panel">
                <button onclick="designSectionStructure()" class="btn btn-primary">
                    Design 7-Section Structure
                </button>
            </div>
            <div class="output-panel">
                <h4>Section Structure</h4>
                <div id="section-structure-display"></div>
            </div>
        </div>
    </div>
    
    <!-- Step 2: Topic Allocation -->
    <div class="step-container" id="step-2" style="display: none;">
        <h3>Step 2: Allocate Topics to Sections</h3>
        <div class="step-content">
            <div class="input-panel">
                <h4>Section Structure</h4>
                <div id="structure-display"></div>
            </div>
            <div class="action-panel">
                <button onclick="allocateTopics()" class="btn btn-primary">
                    Allocate All Topics
                </button>
            </div>
            <div class="output-panel">
                <h4>Topic Allocation</h4>
                <div id="allocation-display"></div>
            </div>
        </div>
    </div>
    
    <!-- Step 3: Topic Refinement -->
    <div class="step-container" id="step-3" style="display: none;">
        <h3>Step 3: Refine Topics (Optional)</h3>
        <div class="step-content">
            <div class="input-panel">
                <h4>Current Allocation</h4>
                <div id="allocation-review"></div>
            </div>
            <div class="action-panel">
                <button onclick="refineTopics()" class="btn btn-primary">
                    Refine Overloaded Sections
                </button>
            </div>
            <div class="output-panel">
                <h4>Refined Topics</h4>
                <div id="refined-display"></div>
            </div>
        </div>
    </div>
</div>
```

#### **Step 2.2: JavaScript Implementation**
```javascript
// Step 1: Design Section Structure
async function designSectionStructure() {
    try {
        const topics = await loadBrainstormTopics();
        const expandedIdea = await loadExpandedIdea();
        
        const response = await fetch('/api/sections/design-structure', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topics: topics,
                expanded_idea: expandedIdea,
                post_id: window.postId
            })
        });
        
        const result = await response.json();
        if (result.success) {
            displaySectionStructure(result.section_structure);
            showStep(2); // Move to next step
        }
    } catch (error) {
        console.error('Error designing section structure:', error);
    }
}

// Step 2: Allocate Topics
async function allocateTopics() {
    try {
        const topics = await loadBrainstormTopics();
        const sectionStructure = await loadSectionStructure();
        
        const response = await fetch('/api/sections/allocate-topics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topics: topics,
                section_structure: sectionStructure,
                post_id: window.postId
            })
        });
        
        const result = await response.json();
        if (result.success) {
            displayTopicAllocation(result.allocations);
            showStep(3); // Move to next step
        }
    } catch (error) {
        console.error('Error allocating topics:', error);
    }
}

// Step 3: Refine Topics
async function refineTopics() {
    try {
        const allocations = await loadTopicAllocation();
        const sectionStructure = await loadSectionStructure();
        
        const response = await fetch('/api/sections/refine-topics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                allocations: allocations,
                section_structure: sectionStructure,
                post_id: window.postId
            })
        });
        
        const result = await response.json();
        if (result.success) {
            displayRefinedTopics(result.refined_sections);
            completeProcess(); // Mark process as complete
        }
    } catch (error) {
        console.error('Error refining topics:', error);
    }
}
```

### **Phase 3: Database Integration**

#### **Step 3.1: Database Migration**
```sql
-- Add new fields to post_development table
ALTER TABLE post_development ADD COLUMN section_structure JSON;
ALTER TABLE post_development ADD COLUMN structure_design_at TIMESTAMP;
ALTER TABLE post_development ADD COLUMN topic_allocation JSON;
ALTER TABLE post_development ADD COLUMN allocation_completed_at TIMESTAMP;
ALTER TABLE post_development ADD COLUMN refined_topics JSON;
ALTER TABLE post_development ADD COLUMN refinement_completed_at TIMESTAMP;
```

#### **Step 3.2: Data Persistence Functions**
```python
def save_section_structure(post_id, structure_data):
    """Save section structure design to database"""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            UPDATE post_development 
            SET section_structure = %s, structure_design_at = NOW()
            WHERE post_id = %s
        """, (json.dumps(structure_data), post_id))

def save_topic_allocation(post_id, allocation_data):
    """Save topic allocation to database"""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            UPDATE post_development 
            SET topic_allocation = %s, allocation_completed_at = NOW()
            WHERE post_id = %s
        """, (json.dumps(allocation_data), post_id))

def save_refined_topics(post_id, refined_data):
    """Save refined topics to database"""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            UPDATE post_development 
            SET refined_topics = %s, refinement_completed_at = NOW()
            WHERE post_id = %s
        """, (json.dumps(refined_data), post_id))
```

---

## 🎯 **IMPLEMENTATION TIMELINE**

### **Week 1: Backend Development**
- Day 1-2: Implement Step 1 API (Section Structure Design)
- Day 3-4: Implement Step 2 API (Topic Allocation)
- Day 5: Implement Step 3 API (Topic Refinement)

### **Week 2: Frontend Development**
- Day 1-2: Update grouping page with 3-step interface
- Day 3-4: Implement JavaScript for each step
- Day 5: Testing and integration

### **Week 3: Database & Integration**
- Day 1: Database migration and schema updates
- Day 2-3: Data persistence functions
- Day 4-5: End-to-end testing and bug fixes

---

## ✅ **SUCCESS CRITERIA**

### **Functional Requirements:**
- ✅ All 50+ topics are allocated to exactly one section
- ✅ No topics are lost or duplicated
- ✅ Sections have clear thematic boundaries
- ✅ Process is completed in 3 distinct steps
- ✅ All data is properly persisted to database

### **Quality Requirements:**
- ✅ Section structure is engaging and logical
- ✅ Topic allocation is semantically accurate
- ✅ Refinement maintains content quality
- ✅ Process is user-friendly and intuitive
- ✅ Results are immediately usable by authoring system

### **Technical Requirements:**
- ✅ APIs return proper JSON responses
- ✅ Database schema supports all data types
- ✅ Frontend provides clear progress indication
- ✅ Error handling is comprehensive
- ✅ Process can be resumed if interrupted

---

## 🚀 **NEXT STEPS**

1. **Review and approve** this implementation plan
2. **Begin Phase 1** with Step 1 API development
3. **Test each step** individually before proceeding
4. **Integrate with existing** brainstorming workflow
5. **Update authoring system** to use new data structure

**This 3-step process will provide a robust, systematic approach to topic allocation that ensures comprehensive coverage and proper data integrity.**
