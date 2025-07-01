# Field Selection Mapping Analysis

## Executive Summary

**Problem**: 25 out of 29 workflow steps are missing field selection mappings, causing 404 errors in the workflow UI.

**Solution**: Seed default field selection mappings for all steps based on logical field relationships.

## Current Status

### Steps WITH Field Selection Mappings (4/29)
- ✅ **Step 13**: "Interesting Facts" → `interesting_facts` (200 OK)
- ✅ **Step 21**: "Provisional Title" → `provisional_title` (200 OK)  
- ✅ **Step 22**: "Idea Scope" → `idea_scope` (200 OK)
- ✅ **Step 41**: "Initial Concept" → `basic_idea` (200 OK)

### Steps WITHOUT Field Selection Mappings (25/29)
- ❌ **Step 3**: "Main" (404)
- ❌ **Step 7**: "Final Check" (404)
- ❌ **Step 8**: "Verification" (404)
- ❌ **Step 9**: "Content Adaptation" (404)
- ❌ **Step 12**: "Research Notes" (404)
- ❌ **Step 14**: "Structure" (404)
- ❌ **Step 15**: "Allocate Facts" (404) ← **This is the one causing the console error**
- ❌ **Step 16**: "Sections" (404)
- ❌ **Step 18**: "Main" (404)
- ❌ **Step 19**: "Main" (404)
- ❌ **Step 23**: "Section Order" (404)
- ❌ **Step 24**: "Section Headings" (404)
- ❌ **Step 25**: "Self Review" (404)
- ❌ **Step 26**: "SEO Optimization" (404)
- ❌ **Step 27**: "Scheduling" (404)
- ❌ **Step 28**: "Deployment" (404)
- ❌ **Step 29**: "Content Distribution" (404)
- ❌ **Step 30**: "Engagement Tracking" (404)
- ❌ **Step 32**: "Topics To Cover" (404)
- ❌ **Step 33**: "Peer Review" (404)
- ❌ **Step 34**: "Tartans Products" (404)
- ❌ **Step 35**: "Content Updates" (404)
- ❌ **Step 36**: "Platform Selection" (404)
- ❌ **Step 37**: "Version Control" (404)
- ❌ **Step 38**: "Feedback Collection" (404)

## Available Post Development Fields

Based on the API response, these fields are available for mapping:

### Planning Stage Fields
- `idea_seed` - Basic idea seed
- `basic_idea` - Expanded basic idea
- `expanded_idea` - Further expanded idea
- `idea_scope` - Scope definition
- `concepts` - Related concepts
- `research_notes` - Research notes
- `interesting_facts` - Interesting facts
- `topics_to_cover` - Topics to cover
- `facts` - General facts
- `allocated_facts` - Allocated facts

### Structure Stage Fields
- `outline` - Content outline
- `section_planning` - Section planning
- `section_order` - Section ordering
- `section_headings` - Section headings
- `sections` - Section content

### Content Stage Fields
- `main_title` - Main title
- `provisional_title` - Provisional titles
- `provisional_title_primary` - Primary provisional title
- `subtitle` - Subtitle
- `intro_blurb` - Introduction blurb
- `content_draft` - Content draft
- `conclusion` - Conclusion
- `summary` - Summary

### Meta Information Fields
- `basic_metadata` - Basic metadata
- `categories` - Categories
- `tags` - Tags
- `seo_optimization` - SEO optimization
- `meta_description` - Meta description
- `meta_keywords` - Meta keywords

### Review Fields
- `self_review` - Self review
- `peer_review` - Peer review
- `final_check` - Final check

### Publishing Fields
- `scheduling` - Scheduling
- `deployment` - Deployment
- `distribution` - Distribution
- `content_adaptation` - Content adaptation
- `content_updates` - Content updates
- `engagement_tracking` - Engagement tracking
- `feedback_collection` - Feedback collection
- `platform_selection` - Platform selection
- `version_control` - Version control
- `verification` - Verification
- `tartans_products` - Tartans products

## Recommended Field Selection Mappings

### Planning Stage
| Step ID | Step Name | Recommended Field | Rationale |
|---------|-----------|-------------------|-----------|
| 41 | Initial Concept | `basic_idea` | ✅ Already mapped correctly |
| 12 | Research Notes | `research_notes` | Direct match |
| 13 | Interesting Facts | `interesting_facts` | ✅ Already mapped correctly |
| 32 | Topics To Cover | `topics_to_cover` | Direct match |
| 15 | Allocate Facts | `allocated_facts` | Direct match |

### Structure Stage
| Step ID | Step Name | Recommended Field | Rationale |
|---------|-----------|-------------------|-----------|
| 14 | Structure | `outline` | Structure creates outline |
| 23 | Section Order | `section_order` | Direct match |
| 24 | Section Headings | `section_headings` | Direct match |
| 16 | Sections | `sections` | Direct match |
| 21 | Provisional Title | `provisional_title` | ✅ Already mapped correctly |
| 22 | Idea Scope | `idea_scope` | ✅ Already mapped correctly |

### Content Stage
| Step ID | Step Name | Recommended Field | Rationale |
|---------|-----------|-------------------|-----------|
| 3 | Main | `content_draft` | Main content creation |
| 18 | Main | `content_draft` | Main content creation |
| 19 | Main | `content_draft` | Main content creation |

### Meta Information Stage
| Step ID | Step Name | Recommended Field | Rationale |
|---------|-----------|-------------------|-----------|
| 25 | Self Review | `self_review` | Direct match |
| 26 | SEO Optimization | `seo_optimization` | Direct match |
| 33 | Peer Review | `peer_review` | Direct match |
| 7 | Final Check | `final_check` | Direct match |

### Publishing Stage
| Step ID | Step Name | Recommended Field | Rationale |
|---------|-----------|-------------------|-----------|
| 27 | Scheduling | `scheduling` | Direct match |
| 28 | Deployment | `deployment` | Direct match |
| 29 | Content Distribution | `distribution` | Direct match |
| 9 | Content Adaptation | `content_adaptation` | Direct match |
| 35 | Content Updates | `content_updates` | Direct match |
| 30 | Engagement Tracking | `engagement_tracking` | Direct match |
| 38 | Feedback Collection | `feedback_collection` | Direct match |
| 36 | Platform Selection | `platform_selection` | Direct match |
| 37 | Version Control | `version_control` | Direct match |
| 8 | Verification | `verification` | Direct match |
| 34 | Tartans Products | `tartans_products` | Direct match |

## Implementation Strategy

### Phase 1: Data Seeding (Immediate Fix)
Create SQL script to update `workflow_step_entity.config` for all 25 missing steps:

```sql
-- Example for Step 15 (Allocate Facts)
UPDATE workflow_step_entity 
SET config = jsonb_set(
    COALESCE(config, '{}'::jsonb),
    '{settings,llm,user_output_mapping}',
    '{"field": "allocated_facts", "table": "post_development"}'::jsonb
)
WHERE id = 15;
```

### Phase 2: API Endpoint Fix (When Ready)
- Remove post ID from field selection endpoints
- Update to use step ID only

### Phase 3: Frontend Update (When Ready)
- Update frontend to use step ID only for field selection

## Benefits of This Approach

1. **Immediate Fix**: Eliminates all 404 errors instantly
2. **Logical Mappings**: Each step maps to the most appropriate field
3. **Consistency**: All steps have field selection mappings
4. **Maintainability**: Clear, documented field relationships
5. **User Experience**: Workflow UI works without errors
6. **Policy Compliance**: Follows per-step field selection policy

## Risk Assessment

**Low Risk**: 
- Field selection mappings can be updated later through the UI
- No existing data is modified, only step configurations
- All mappings are logical and appropriate for each step's purpose

**Testing Required**:
- Verify all 404 errors are eliminated
- Confirm field selection dropdowns work correctly
- Test workflow navigation across all stages

## Next Steps

1. **Approve the mapping recommendations**
2. **Create and execute the SQL seeding script**
3. **Test the workflow UI to confirm 404 errors are resolved**
4. **Proceed with API and frontend updates when ready** 