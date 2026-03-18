# Substage Completion Tracking Implementation Plan

**Date:** 2025-01-15  
**Status:** Planning  
**Estimated Total Time:** 14-18 hours

---

## Executive Summary

This plan implements comprehensive completion tracking for all 18 substages across 5 stages (Calendar, Planning, Authoring, Imaging, Header) in the one-click blog workflow. The system will automatically detect completion status and display green dot indicators for completed substages.

**Key Challenge:** Multi-section substages (Authoring, Imaging) require checking completion across ALL sections, not just a single field.

---

## Detailed Substage Analysis

### Stage 1: Calendar (2 substages)

#### 1.1 Calendar View
- **Type:** Single-item
- **Completion Field:** None (view-only, no data persistence)
- **Completion Logic:** Always considered complete (viewing is not a generation step)
- **Status:** ✅ **No tracking needed** (informational only)

#### 1.2 Idea Generation (Week View)
- **Type:** Single-item
- **Completion Field:** `calendar_schedule.post_id`
- **Completion Logic:** Check if post has been assigned to a week in calendar
- **Database Query:**
  ```sql
  SELECT EXISTS(
    SELECT 1 FROM calendar_schedule 
    WHERE post_id = %s
  )
  ```
- **Note:** `calendar_week_selection` table does not exist; only `calendar_schedule` is used
- **Status:** ⚠️ **Needs implementation**

---

### Stage 2: Planning (6 substages)

#### 2.1 Ideas (`expanded_idea`)
- **Type:** Single-item
- **Completion Field:** `post_development.expanded_idea`
- **Completion Logic:** `expanded_idea IS NOT NULL AND expanded_idea != ''`
- **Timestamp:** Use `post_development.updated_at` when `expanded_idea` was last set
- **Status:** ⚠️ **Needs implementation**

#### 2.2 Taxonomy (`taxonomy`)
- **Type:** Single-item (3 fields)
- **Completion Fields:** 
  - `post.theme_id`
  - `post.content_type_id`
  - `post.format_id`
- **Completion Logic:** All three fields must be NOT NULL
  ```sql
  theme_id IS NOT NULL 
  AND content_type_id IS NOT NULL 
  AND format_id IS NOT NULL
  ```
- **Timestamp:** Use `post.updated_at` when taxonomy was last set
- **Status:** ⚠️ **Needs implementation**

#### 2.3 Topic Brainstorming (`topic_brainstorming`)
- **Type:** Single-item
- **Completion Field:** `post_development.idea_scope`
- **Completion Logic:** `idea_scope IS NOT NULL AND idea_scope != ''`
- **Timestamp:** Extract from `idea_scope` JSON `generated_at` field (already implemented)
- **Status:** ✅ **Already tracked** (line 129 in `automation_pipeline.py`)

#### 2.4 Section Structure (`section_structure`)
- **Type:** Single-item
- **Completion Field:** `post_development.section_structure`
- **Completion Logic:** `section_structure IS NOT NULL`
- **Timestamp:** `post_development.structure_design_at`
- **Status:** ✅ **Already tracked** (line 133)

#### 2.5 Topic Allocation (`topic_allocation`)
- **Type:** Single-item
- **Completion Field:** `post_development.topic_allocation`
- **Completion Logic:** `topic_allocation IS NOT NULL`
- **Timestamp:** `post_development.allocation_completed_at`
- **Status:** ✅ **Already tracked** (line 137)

#### 2.6 Section Titling (`section_titling`)
- **Type:** Single-item
- **Completion Field:** `post_development.sections`
- **Completion Logic:** `sections IS NOT NULL AND sections != ''`
- **Timestamp:** `post_development.updated_at` (sections_updated_at)
- **Status:** ✅ **Already tracked** (line 141)

---

### Stage 3: Authoring (4 substages - ALL multi-section)

#### 3.1 Author First Drafts (`author_first_drafts`)
- **Type:** Multi-section
- **Completion Fields:** `post_section.draft` (for each section)
- **Completion Logic:** ALL sections (where `section_order <= 7`) must have non-empty `draft`
  ```sql
  SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN draft IS NOT NULL AND draft != '' THEN 1 ELSE 0 END) as drafted
  FROM post_section
  WHERE post_id = %s AND section_order <= 7
  
  -- Complete if: drafted = total AND total > 0
  ```
- **Progress Calculation:** `(drafted / total) * 100`
- **Timestamp:** Use `post_development.updated_at` when last section draft was completed
- **Status:** ✅ **Already tracked** (lines 150-152, but needs verification for multi-section logic)

#### 3.2 Image Concepts (`image_concepts`)
- **Type:** Multi-section
- **Completion Fields:** `post_section.image_concepts` (for each section)
- **Completion Logic:** ALL sections must have non-empty `image_concepts`
  ```sql
  SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN image_concepts IS NOT NULL AND image_concepts != '' THEN 1 ELSE 0 END) as with_concepts
  FROM post_section
  WHERE post_id = %s AND section_order <= 7
  
  -- Complete if: with_concepts = total AND total > 0
  ```
- **Progress Calculation:** `(with_concepts / total) * 100`
- **Timestamp:** Use `post_development.updated_at`
- **Status:** ✅ **Already tracked** (lines 154-156, but needs verification)

#### 3.3 Image Prompts (`image_prompts`)
- **Type:** Multi-section
- **Completion Fields:** `post_section.image_prompts` (for each section)
- **Completion Logic:** ALL sections must have non-empty `image_prompts`
  ```sql
  SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN image_prompts IS NOT NULL AND image_prompts != '' THEN 1 ELSE 0 END) as with_prompts
  FROM post_section
  WHERE post_id = %s AND section_order <= 7
  
  -- Complete if: with_prompts = total AND total > 0
  ```
- **Progress Calculation:** `(with_prompts / total) * 100`
- **Timestamp:** Use `post_development.updated_at`
- **Status:** ✅ **Already tracked** (lines 158-160, but needs verification)

#### 3.4 Image Captions (`image_captions`)
- **Type:** Multi-section
- **Completion Fields:** `post_section.image_captions` (for each section)
- **Completion Logic:** ALL sections must have non-empty `image_captions`
  ```sql
  SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN image_captions IS NOT NULL AND image_captions != '' THEN 1 ELSE 0 END) as with_captions
  FROM post_section
  WHERE post_id = %s AND section_order <= 7
  
  -- Complete if: with_captions = total AND total > 0
  ```
- **Progress Calculation:** `(with_captions / total) * 100`
- **Timestamp:** Use `post_development.updated_at`
- **Status:** ✅ **Already tracked** (lines 162-164, but needs verification)

---

### Stage 4: Imaging (2 substages - ALL multi-section)

#### 4.1 Image Generation (`image-generation`)
- **Type:** Multi-section
- **Completion Fields:** 
  - Primary: `post_section.image_filename` (indicates image was generated)
  - Secondary: `post_section.image_generated_at` (timestamp)
  - Alternative: Check for raw image file existence
- **Completion Logic:** ALL sections must have generated images
  ```sql
  SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN image_filename IS NOT NULL AND image_filename != '' THEN 1 ELSE 0 END) as generated
  FROM post_section
  WHERE post_id = %s AND section_order <= 7
  
  -- Complete if: generated = total AND total > 0
  ```
- **Alternative Check:** Verify raw image files exist on filesystem
  ```python
  # For each section, check if raw image exists:
  # static/content/posts/{post_id}/sections/{section_id}/landscape/raw/{section_id}.png
  ```
- **Progress Calculation:** `(generated / total) * 100`
- **Timestamp:** Use `MAX(post_section.image_generated_at)` across all sections
- **Status:** ⚠️ **Needs implementation**

#### 4.2 Optimise (`optimise`)
- **Type:** Multi-section
- **Completion Fields:** `post_images` table with `image_type = 'section_optimized'`
- **Completion Logic:** ALL sections must have optimized images linked
  ```sql
  SELECT 
    COUNT(DISTINCT ps.id) as total_sections,
    COUNT(DISTINCT pi.section_id) as optimized_sections
  FROM post_section ps
  LEFT JOIN post_images pi ON ps.id = pi.section_id AND pi.image_type = 'section_optimized'
  WHERE ps.post_id = %s AND ps.section_order <= 7
  
  -- Complete if: optimized_sections = total_sections AND total_sections > 0
  ```
- **Alternative Check:** Verify optimized image files exist on filesystem
  ```python
  # For each section, check if optimized image exists:
  # static/content/posts/{post_id}/sections/{section_id}/landscape/optimized/{section_id}_optimized.jpg
  ```
- **Progress Calculation:** `(optimized_sections / total_sections) * 100`
- **Timestamp:** Use `MAX(post_images.created_at)` for optimized images
- **Status:** ⚠️ **Needs implementation**

---

### Stage 5: Header (5 substages)

#### 5.1 Title & Summary (`title-summary`)
- **Type:** Single-item (3 fields)
- **Completion Fields:**
  - `post.title`
  - `post.summary`
  - `post.subtitle` (optional but recommended)
- **Completion Logic:** Title and summary must be present
  ```sql
  title IS NOT NULL AND title != ''
  AND summary IS NOT NULL AND summary != ''
  ```
- **Timestamp:** Use `post.updated_at` when title/summary were last set
- **Status:** ⚠️ **Needs implementation**

#### 5.2 Header Image (`header-image`)
- **Type:** Single-item (multiple related fields)
- **Completion Fields:**
  - `post.header_image_id` (primary indicator)
  - `post.header_image_caption` (recommended)
  - `post.header_image_alt_text` (recommended)
- **Completion Logic:** Header image ID must be present
  ```sql
  header_image_id IS NOT NULL
  ```
- **Optional Enhancement:** Check that image file actually exists
- **Timestamp:** Use `post.updated_at` when header_image_id was last set
- **Status:** ⚠️ **Needs implementation**

#### 5.3 SEO & Meta (`seo-meta`)
- **Type:** Single-item (multiple fields)
- **Completion Fields:**
  - `post.meta_title` (required)
  - `post.meta_description` (required)
  - `post.meta_tags` (recommended)
  - `post.slug` (required)
- **Completion Logic:** Core meta fields must be present
  ```sql
  meta_title IS NOT NULL AND meta_title != ''
  AND meta_description IS NOT NULL AND meta_description != ''
  AND slug IS NOT NULL AND slug != ''
  ```
- **Timestamp:** Use `post.updated_at` when SEO meta was last set
- **Status:** ⚠️ **Needs implementation**

#### 5.4 Product Match (`product-match`)
- **Type:** Single-item
- **Completion Fields:**
  - `post.profile_product_id` (for profile posts)
  - `post.cross_promotion_product_id` (for themed posts)
- **Completion Logic:** At least one product ID must be present
  ```sql
  (profile_product_id IS NOT NULL) 
  OR (cross_promotion_product_id IS NOT NULL)
  ```
- **Note:** This may be optional depending on post type
- **Timestamp:** Use `post.updated_at` when product match was last set
- **Status:** ⚠️ **Needs implementation**

#### 5.5 Final Review (`final-review`)
- **Type:** Single-item
- **Completion Field:** `post.status` = 'ready_for_publish' or similar
- **Alternative:** Check if all previous header substages are complete
- **Completion Logic:** 
  ```sql
  -- Option 1: Check status field
  status = 'ready_for_publish'
  
  -- Option 2: Check all header substages are complete
  -- (title_summary, header_image, seo_meta all complete)
  ```
- **Timestamp:** Use `post.updated_at` when status changed
- **Status:** ⚠️ **Needs implementation** (requires definition of completion criteria)

---

## Implementation Phases

### Phase 1: Database Schema Verification & Documentation (2-3 hours)

**Objective:** Verify all required fields exist and document completion criteria

**Tasks:**
1. ✅ Verify `post_section` table has all required fields
   - `image_filename`, `image_generated_at` ✓
   - `draft`, `image_concepts`, `image_prompts`, `image_captions` ✓
2. ✅ Verify `post_images` table structure
   - `image_type = 'section_optimized'` exists ✓
3. ✅ Verify `post` table has all header fields
   - `title`, `summary`, `subtitle` ✓
   - `header_image_id`, `header_image_caption`, `header_image_alt_text` ✓
   - `meta_title`, `meta_description`, `meta_tags`, `slug` ✓
   - `profile_product_id`, `cross_promotion_product_id` ✓
4. ✅ Verify `post_development` table fields
   - `expanded_idea`, `idea_scope`, `section_structure`, `topic_allocation`, `sections` ✓
5. ✅ Verify `calendar_schedule` table
   - Confirmed: Table exists with `post_id` field
   - Note: `calendar_week_selection` table does not exist
6. Create completion criteria documentation
   - Document exact SQL queries for each substage
   - Document edge cases (empty strings, NULL values)

**Deliverable:** Completion criteria specification document

---

### Phase 2: Backend API Enhancement (6-8 hours)

**Objective:** Extend `/pipeline-status/<post_id>` API to return completion status for all substages

**File:** `blueprints/automation_pipeline.py`

#### Task 2.1: Add Ideas Substage Tracking (30 min)
- Add `expanded_idea` to SQL query (line 22-32)
- Add completion check: `post['expanded_idea'] IS NOT NULL AND post['expanded_idea'] != ''`
- Add to response substages (line 127-144)
- Extract timestamp from `post_development.updated_at`

#### Task 2.2: Add Taxonomy Substage Tracking (30 min)
- Add `theme_id`, `content_type_id`, `format_id` to SQL query
- Add completion check: All three fields NOT NULL
- Add to response substages
- Use `post.updated_at` as timestamp

#### Task 2.3: Verify Multi-Section Authoring Substages (1 hour)
- Review existing implementation (lines 39-91)
- Verify SQL queries correctly check ALL sections
- Ensure `section_order <= 7` filter is applied consistently
- Test edge cases (0 sections, partial completion)
- Fix any bugs in existing logic

#### Task 2.4: Add Image Generation Substage Tracking (1.5 hours)
- Add SQL query to check `post_section.image_filename` for all sections
- Implement completion check: All sections have `image_filename`
- Add filesystem fallback check (verify raw images exist)
- Add to response substages
- Calculate progress percentage
- Extract timestamp from `MAX(image_generated_at)`

#### Task 2.5: Add Image Optimization Substage Tracking (1.5 hours)
- Add SQL query to check `post_images` with `image_type = 'section_optimized'`
- Join with `post_section` to count total vs optimized
- Implement completion check: All sections have optimized images
- Add filesystem fallback check (verify optimized images exist)
- Add to response substages
- Calculate progress percentage
- Extract timestamp from `MAX(post_images.created_at)`

#### Task 2.6: Add Header Substages Tracking (2.5 hours)
- **Title & Summary:** Check `post.title` and `post.summary`
- **Header Image:** Check `post.header_image_id IS NOT NULL`
- **SEO & Meta:** Check `post.meta_title`, `post.meta_description`, `post.slug`
- **Product Match:** Check `post.profile_product_id OR post.cross_promotion_product_id`
- **Final Review:** Define criteria (all header substages complete OR status = 'ready_for_publish')
- Add all to response substages
- Extract timestamps from `post.updated_at`

#### Task 2.7: Add Calendar Substage Tracking (30 min)
- Add query to check `calendar_schedule` for `post_id`
- Add to response (if calendar stage is included in API response)
- Note: Only `calendar_schedule` table exists (not `calendar_week_selection`)

#### Task 2.8: Update Response Structure (30 min)
- Ensure all substages follow consistent structure:
  ```json
  {
    "status": "complete" | "in_progress" | "pending",
    "completed_at": "ISO8601 timestamp" | null,
    "progress": 0-100 (for multi-section substages)
  }
  ```
- Update stage-level completion logic to include new substages

**Deliverable:** Enhanced API endpoint with all substages tracked

---

### Phase 3: Frontend UI Updates (4-5 hours)

**Objective:** Display completion status with green dot indicators

**Files:**
- `static/js/launchpad/pipeline-manager.js`
- `templates/launchpad/one_click_blog.html`
- `static/css/launchpad/one-click-blog.css` (if needed)

#### Task 3.1: Update Pipeline Manager JavaScript (2 hours)
- Modify `updatePipelineStatus()` to handle all substages
- Add logic to display green dot for `status === "complete"`
- Add progress bars for multi-section substages (show percentage)
- Handle new substages in status updates
- Update substage rendering to show completion indicators

#### Task 3.2: Update Template (1 hour)
- Ensure all substages are listed in template
- Add CSS classes for completion indicators
- Update substage macro to accept and display completion status

#### Task 3.3: Add Visual Indicators (1 hour)
- Create green dot CSS (circle with checkmark for complete)
- Add progress bar styling for in-progress multi-section substages
- Add hover tooltips showing completion details
- Ensure accessibility (screen reader support)

#### Task 3.4: Handle Edge Cases (1 hour)
- Display "0%" for substages with no sections yet
- Handle NULL timestamps gracefully
- Show appropriate messages for pending substages
- Test with posts at various completion stages

**Deliverable:** UI with green dot indicators for all completed substages

---

### Phase 4: Testing & Validation (2-3 hours)

**Objective:** Verify completion tracking works correctly for all substages

#### Task 4.1: Unit Testing (1 hour)
- Test each completion check with sample data
- Test edge cases:
  - Empty strings vs NULL
  - Partial completion (multi-section)
  - Posts with no sections
  - Posts with all sections complete
- Verify SQL queries return correct results

#### Task 4.2: Integration Testing (1 hour)
- Test API endpoint with real post data
- Verify response structure matches specification
- Test with posts at different completion stages
- Verify timestamps are correctly formatted

#### Task 4.3: UI Testing (1 hour)
- Test green dot indicators display correctly
- Test progress bars for multi-section substages
- Test with different browser sizes
- Verify accessibility features work

#### Task 4.4: End-to-End Testing (30 min)
- Create test post and complete each substage
- Verify completion status updates correctly
- Test reload persistence
- Verify all substages show correct status

**Deliverable:** Tested and validated completion tracking system

---

### Phase 5: Documentation & Cleanup (1 hour)

**Objective:** Document implementation and clean up code

#### Task 5.1: Code Documentation
- Add docstrings to new functions
- Add comments explaining completion logic
- Document SQL queries

#### Task 5.2: User Documentation
- Update user guide with completion tracking explanation
- Document what each substage completion means
- Add troubleshooting guide

#### Task 5.3: Code Cleanup
- Remove any debug logging
- Ensure consistent code style
- Remove unused code

**Deliverable:** Clean, documented codebase

---

## Risk Assessment & Mitigation

### Risk 1: Multi-Section Completion Logic Complexity
- **Risk:** Incorrectly calculating completion for multi-section substages
- **Mitigation:** 
  - Use explicit SQL queries with COUNT and SUM
  - Test with posts having 0, 1, partial, and all sections
  - Add logging to verify calculation logic

### Risk 2: Filesystem Checks for Images
- **Risk:** Database says complete but files don't exist (or vice versa)
- **Mitigation:**
  - Primary check: Database fields
  - Fallback check: Filesystem (optional, for validation)
  - Log warnings if mismatch detected

### Risk 3: Performance with Many Sections
- **Risk:** SQL queries slow with posts having many sections
- **Mitigation:**
  - Use efficient queries with proper indexes
  - Cache results if needed
  - Limit section checks to `section_order <= 7`

### Risk 4: Timestamp Accuracy
- **Risk:** Timestamps may not reflect actual completion time
- **Mitigation:**
  - Use existing timestamp fields where available
  - For multi-section, use MAX timestamp
  - Document timestamp source for each substage

---

## Success Criteria

1. ✅ All 18 substages have completion tracking
2. ✅ Multi-section substages correctly check ALL sections
3. ✅ Green dot indicators display for completed substages
4. ✅ Progress bars show percentage for in-progress multi-section substages
5. ✅ API response includes all substages with consistent structure
6. ✅ Completion status persists across page reloads
7. ✅ Edge cases handled gracefully (no sections, partial completion, etc.)

---

## Timeline Estimate

| Phase | Hours | Dependencies |
|-------|-------|---------------|
| Phase 1: Schema Verification | 2-3 | None |
| Phase 2: Backend API | 6-8 | Phase 1 |
| Phase 3: Frontend UI | 4-5 | Phase 2 |
| Phase 4: Testing | 2-3 | Phase 2, 3 |
| Phase 5: Documentation | 1 | Phase 2, 3, 4 |
| **Total** | **15-20 hours** | |

---

## Next Steps

1. **Immediate:** Review and approve this plan
2. **Phase 1:** Begin database schema verification
3. **Phase 2:** Start with high-priority substages (Ideas, Taxonomy)
4. **Phase 3:** Implement frontend after backend is stable
5. **Phase 4:** Test incrementally as each phase completes

---

## Appendix: SQL Query Templates

### Multi-Section Completion Check Template
```sql
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN {field} IS NOT NULL AND {field} != '' THEN 1 ELSE 0 END) as completed
FROM post_section
WHERE post_id = %s AND section_order <= 7

-- Complete if: completed = total AND total > 0
-- Progress: (completed / total) * 100
```

### Image Optimization Check Template
```sql
SELECT 
    COUNT(DISTINCT ps.id) as total_sections,
    COUNT(DISTINCT pi.section_id) as optimized_sections
FROM post_section ps
LEFT JOIN post_images pi ON ps.id = pi.section_id AND pi.image_type = 'section_optimized'
WHERE ps.post_id = %s AND ps.section_order <= 7

-- Complete if: optimized_sections = total_sections AND total_sections > 0
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-15  
**Author:** AI Assistant  
**Status:** Ready for Review

