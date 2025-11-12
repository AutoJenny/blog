# Product Pipeline Simplification - Implementation Checklist

**Date:** 2025-11-11  
**Status:** Ready for Implementation  
**Goal:** Simplify planning stages for `generated` product posts from 6 stages to 4 stages

---

## Overview

Simplify the planning pipeline for `generated` product posts by:
1. Removing redundant stages (`topic-brainstorming`, `section-structure-design`)
2. Replacing `section-ideas` with `section-content-mapping` (visual data mapping)
3. Streamlining workflow to focus on data-driven content generation

**Current:** 6 planning stages  
**Target:** 4 planning stages  
**Savings:** 2 stages eliminated (33% reduction)

---

## Current State

### Current Pipeline (from `config/post_type_pipeline_configs.py`)
```
1. taxonomy                    # Assign taxonomy
2. product-data-review        # Review CLAN product data
3. topic-brainstorming        # Generate topics (REDUNDANT)
4. section-structure-design   # Design structure (REDUNDANT - structure is fixed)
5. section-ideas              # Section-specific ideas (REPLACE with mapping)
6. section-titling            # Finalize section titles
7. drafting                   # Author drafts
```

### Target Pipeline
```
1. taxonomy                    # Assign taxonomy (auto-populate from product)
2. product-data-review        # Review CLAN product data
3. section-content-mapping    # NEW: Visual data-to-section mapping
4. section-titling            # Finalize section titles (optional)
5. drafting                   # Author drafts
```

---

## Implementation Tasks

### Phase 1: Update Pipeline Configuration

#### Task 1.1: Update `post_type_pipeline_configs.py`
**File:** `config/post_type_pipeline_configs.py`  
**Action:**
- Remove `topic-brainstorming` from `generated` steps
- Remove `section-structure-design` from `generated` steps
- Remove `section-ideas` from `generated` steps
- Add `section-content-mapping` to `generated` steps
- Update step order

**Expected Result:**
```python
'generated': {
    'active': True,
    'steps': [
        'taxonomy',
        'product-data-review',
        'section-content-mapping',  # NEW
        'section-titling',
        'drafting',
        # ... rest of steps unchanged
    ]
}
```

**Checklist:**
- [ ] Remove `topic-brainstorming` from steps list
- [ ] Remove `section-structure-design` from steps list
- [ ] Remove `section-ideas` from steps list
- [ ] Add `section-content-mapping` to steps list
- [ ] Update `STEP_FUNCTION_MAPPINGS` for `generated` type
- [ ] Update `STEP_LABELS` with new label
- [ ] Test pipeline navigation still works

---

### Phase 2: Create Section Content Mapping Stage

#### Task 2.1: Create Route Handler
**File:** `blueprints/planning_concept.py` (or new file)  
**Action:**
- Create `planning_concept_section_content_mapping(post_id)` function
- Similar structure to other planning concept functions
- Fetch product data using `ClanDataExtractor`
- Pass data to template

**Expected Code:**
```python
def planning_concept_section_content_mapping(post_id):
    """Section content mapping page - shows which data maps to which section"""
    from utils.content_generation.clan_data_extractor import ClanDataExtractor
    from utils.taxonomy_helpers import get_post_type
    
    # Verify this is a generated post with product
    post_type = get_post_type(post_id)
    if post_type != 'generated':
        # Redirect or error
    
    # Get product ID from post
    product_id = get_product_id_from_post(post_id)
    
    # Extract product data
    extractor = ClanDataExtractor()
    product_data = extractor.extract_product_data(product_id)
    validation = extractor.validate_data_completeness(product_data)
    
    # Map data to sections (7-section structure)
    section_mapping = create_section_data_mapping(product_data)
    
    return render_template('planning/concept/section_content_mapping.html',
                          post_id=post_id,
                          product_data=product_data,
                          section_mapping=section_mapping,
                          validation=validation)
```

**Checklist:**
- [ ] Create route function
- [ ] Add route registration in `blueprints/planning.py`
- [ ] Import `ClanDataExtractor`
- [ ] Fetch product ID from post (check `post_development` or post metadata)
- [ ] Extract product data
- [ ] Create section mapping logic
- [ ] Handle errors (no product, missing data)

#### Task 2.2: Create Template
**File:** `templates/planning/concept/section_content_mapping.html`  
**Action:**
- Create visual mapping interface
- Show 7 sections with data sources for each
- Display data completeness indicators
- Allow author to review/override mappings
- Save mappings to `post_development` table

**Template Structure:**
```
Section Content Mapping
├── Product Info Panel (product name, SKU, supplier)
├── Section Mapping Panel
│   ├── Section 1: Introduction & Historical Context
│   │   ├── Data Sources: heritage_data.historical_origins ✓
│   │   ├── Data Sources: heritage_data.cultural_significance ✓
│   │   └── Completeness: 85% (narrative present)
│   ├── Section 2: Craftsmanship & Materials
│   │   ├── Data Sources: supplier_description ✓
│   │   ├── Data Sources: specifications ✓
│   │   └── Completeness: 90%
│   └── ... (all 7 sections)
└── Actions
    ├── Save Mapping
    └── Continue to Section Titling
```

**Checklist:**
- [ ] Create template file
- [ ] Add section mapping display (7 sections)
- [ ] Show data sources per section
- [ ] Show data completeness indicators
- [ ] Add visual indicators (✓ for available, ⚠️ for missing)
- [ ] Add save functionality
- [ ] Add continue button
- [ ] Style consistently with other planning pages

#### Task 2.3: Create Section Mapping Logic
**File:** `utils/content_generation/section_mapper.py` (new)  
**Action:**
- Create `SectionMapper` class
- Method: `map_data_to_sections(product_data) -> Dict`
- Returns mapping of section → data sources
- Includes completeness scores

**Expected Structure:**
```python
class SectionMapper:
    def map_data_to_sections(self, product_data: Dict) -> Dict:
        """
        Map product data to 7-section structure.
        
        Returns:
        {
            "section_1": {
                "name": "Introduction & Historical Context",
                "data_sources": [
                    {"field": "heritage_data.historical_origins.narrative", "available": True, "word_count": 450},
                    {"field": "heritage_data.cultural_significance.narrative", "available": True, "word_count": 380}
                ],
                "completeness": 0.85,
                "llm_needed": "synthesis"
            },
            # ... all 7 sections
        }
        """
```

**Checklist:**
- [ ] Create `utils/content_generation/section_mapper.py`
- [ ] Implement `SectionMapper` class
- [ ] Create `map_data_to_sections()` method
- [ ] Map all 7 sections to data sources
- [ ] Calculate completeness scores
- [ ] Identify LLM needs per section
- [ ] Test with sample product data

#### Task 2.4: Store Mapping in Database
**Action:**
- Store section mapping in `post_development` table
- Add JSONB field or use existing `data_sources` field
- Store mapping for use in drafting stage

**Database Update:**
```sql
-- Check if data_sources field exists in post_development
-- If not, add it:
ALTER TABLE post_development 
ADD COLUMN IF NOT EXISTS data_sources JSONB DEFAULT '{}';
```

**Checklist:**
- [ ] Check if `data_sources` field exists
- [ ] Add migration if needed
- [ ] Update route to save mapping
- [ ] Store mapping structure in database
- [ ] Test save/load functionality

---

### Phase 3: Update Navigation & Routing

#### Task 3.1: Update Pipeline Navigation
**Files:** 
- `templates/shared/blog_pipeline_header.html` (or navigation component)
- JavaScript navigation logic

**Action:**
- Remove `topic-brainstorming` from navigation
- Remove `section-structure-design` from navigation
- Remove `section-ideas` from navigation
- Add `section-content-mapping` to navigation
- Update step labels

**Checklist:**
- [ ] Update navigation component
- [ ] Remove old stage links
- [ ] Add new stage link
- [ ] Update step labels
- [ ] Test navigation flow

#### Task 3.2: Update Route Registration
**File:** `blueprints/planning.py`  
**Action:**
- Register new route for `section-content-mapping`
- Remove or deprecate old routes (if not used elsewhere)
- Update route patterns

**Checklist:**
- [ ] Add route: `/posts/<id>/concept/section-content-mapping`
- [ ] Register route handler
- [ ] Test route accessibility
- [ ] Verify navigation links work

---

### Phase 4: Update Drafting Stage to Use Mapping

#### Task 4.1: Update Drafting Prompts
**Files:**
- `blueprints/authoring_api_content.py` (or drafting logic)
- LLM prompt templates

**Action:**
- Update drafting prompts to use section mapping
- Include data sources from mapping
- Use CLAN-first policy with mapped data

**Checklist:**
- [ ] Load section mapping from `post_development.data_sources`
- [ ] Update prompt templates to include mapped data
- [ ] Ensure CLAN-first policy is enforced
- [ ] Test drafting with mapped data

#### Task 4.2: Update Section Generation
**Action:**
- Modify section generation to use data mapping
- Generate sections based on mapped data sources
- Include data source indicators in generated content

**Checklist:**
- [ ] Update section generation logic
- [ ] Use mapped data sources per section
- [ ] Generate content with data source awareness
- [ ] Test section generation

---

### Phase 5: Clean Up Old Stages (Optional)

#### Task 5.1: Deprecate Old Templates
**Files:**
- `templates/planning/concept/brainstorm.html` (keep for themed posts)
- `templates/planning/concept/section_structure.html` (keep for themed posts)
- `templates/planning/concept/sections.html` (if exists, check usage)

**Action:**
- Keep templates (they're used for `themed` posts)
- Add comments indicating they're not used for `generated` posts
- Or create separate templates if needed

**Checklist:**
- [ ] Verify templates are still used for `themed` posts
- [ ] Add comments if keeping
- [ ] Document which templates are for which post type

#### Task 5.2: Update Documentation
**Files:**
- `docs/data_intelligence/content_generation/PRODUCT_ARTICLE_PLANNING_DISCUSSION.md`
- Any other relevant docs

**Action:**
- Update documentation to reflect simplified pipeline
- Remove references to removed stages
- Add documentation for new `section-content-mapping` stage

**Checklist:**
- [ ] Update `PRODUCT_ARTICLE_PLANNING_DISCUSSION.md`
- [ ] Update any pipeline documentation
- [ ] Add section-content-mapping documentation
- [ ] Update changelog

---

## Data Structure

### Section Mapping Structure
```json
{
  "section_1": {
    "section_name": "Introduction & Historical Context",
    "section_type": "introduction_historical_context",
    "data_sources": [
      {
        "field": "heritage_data.historical_origins.narrative",
        "available": true,
        "word_count": 450,
        "source": "clan_categories.heritage_data"
      },
      {
        "field": "heritage_data.cultural_significance.narrative",
        "available": true,
        "word_count": 380,
        "source": "clan_categories.heritage_data"
      }
    ],
    "completeness": 0.85,
    "llm_role": "synthesize",
    "llm_needed": true
  },
  "section_2": {
    "section_name": "Craftsmanship & Materials",
    "section_type": "craftsmanship_materials",
    "data_sources": [
      {
        "field": "supplier_description",
        "available": true,
        "word_count": 320,
        "source": "clan_products.supplier_description"
      },
      {
        "field": "specifications",
        "available": true,
        "word_count": 150,
        "source": "clan_products.specifications"
      }
    ],
    "completeness": 0.90,
    "llm_role": "clean_html_format",
    "llm_needed": true
  }
  // ... all 7 sections
}
```

### Storage Location
- **Table:** `post_development`
- **Field:** `data_sources` (JSONB) or new `section_mapping` field
- **Structure:** Section mapping JSON as above

---

## Testing Checklist

### Functional Testing
- [ ] Pipeline navigation works correctly
- [ ] `section-content-mapping` page loads
- [ ] Product data displays correctly
- [ ] Section mapping shows all 7 sections
- [ ] Data sources are correctly identified
- [ ] Completeness scores are accurate
- [ ] Mapping saves to database
- [ ] Drafting stage uses mapping
- [ ] Generated content uses mapped data sources

### Edge Cases
- [ ] Product with missing heritage data
- [ ] Product with missing supplier description
- [ ] Product with minimal data
- [ ] Product with complete data
- [ ] Multiple categories (heritage data merging)

### Integration Testing
- [ ] Full pipeline flow (taxonomy → mapping → titling → drafting)
- [ ] Data flows correctly between stages
- [ ] No broken links in navigation
- [ ] Post can be created and published

---

## Rollback Plan

If issues arise:
1. Revert `post_type_pipeline_configs.py` to original
2. Keep new code but disable via feature flag
3. Old stages still exist (just not in pipeline)

---

## Files to Create

1. `utils/content_generation/section_mapper.py` - Section mapping logic
2. `templates/planning/concept/section_content_mapping.html` - Mapping UI
3. `static/css/planning/section-content-mapping.css` - Styling (if needed)
4. `static/js/planning/section-content-mapping.js` - Client logic (if needed)

## Files to Modify

1. `config/post_type_pipeline_configs.py` - Update pipeline steps
2. `blueprints/planning_concept.py` - Add new route function
3. `blueprints/planning.py` - Register new route
4. `blueprints/authoring_api_content.py` - Use mapping in drafting (if needed)
5. `docs/data_intelligence/content_generation/PRODUCT_ARTICLE_PLANNING_DISCUSSION.md` - Update docs

## Files to Review (Not Modify)

1. `templates/planning/concept/brainstorm.html` - Keep for themed posts
2. `templates/planning/concept/section_structure.html` - Keep for themed posts
3. `templates/planning/concept/sections.html` - Check if used

---

## Implementation Order

1. **Phase 1:** Update pipeline config (quick, test navigation)
2. **Phase 2:** Create section mapping stage (core functionality)
3. **Phase 3:** Update navigation (connect everything)
4. **Phase 4:** Update drafting (use mapping)
5. **Phase 5:** Clean up docs (documentation)

**Estimated Time:** 4-6 hours

---

## Success Criteria

- ✅ Pipeline reduced from 6 to 4 planning stages
- ✅ `section-content-mapping` stage works
- ✅ Visual data mapping displays correctly
- ✅ Mapping saves to database
- ✅ Drafting uses mapped data
- ✅ Navigation flows correctly
- ✅ No broken functionality
- ✅ Documentation updated

---

## Notes

- Keep old templates (used for `themed` posts)
- Section mapping is read-only display (author reviews, doesn't edit)
- Mapping can be overridden in drafting if needed
- All 7 sections are fixed (no structure design needed)

---

**End of Checklist**

