# Blog Post Automation Goals

**Date:** 2026-01-19  
**Status:** Planning & Implementation  
**Goal:** Self-generating blog posts to 'ready' status one week in advance

---

## Executive Summary

**Target**: Blog posts (themed, recipe, product profiles, surname profiles, family profiles) should be automatically:
1. **Created** 1 week before scheduled publication
2. **Processed** through all automated stages
3. **Reach 'ready' status** (ready for final review/publishing)
4. **Require minimal manual intervention** (review gates where needed)

**Current State**: 
- ✅ Weekly content (weekly_word, weekly_phrase, weekly_insult) - FULLY AUTOMATED
- ✅ Product posts - FULLY AUTOMATED  
- ⚠️ Blog posts (themed, recipe, profiles) - PARTIALLY AUTOMATED (manual creation)

**Goal**: Achieve same automation level for blog posts as weekly content.

---

## Automation Flow (Target State)

### 1. Automatic Post Creation (1 Week in Advance)

**Script**: `scripts/automated_blog_post_creator.py` (TO BE CREATED)

**What it should do:**
- Runs daily (via `background_posting_monitor.sh`)
- Checks upcoming weeks (next 7 days)
- Resolves blog post items from calendar schedule using `resolve_item_for_week()`
- Creates `post` records with:
  - `status='draft'`
  - Proper post type (themed, recipe, profile_product, profile_surname, family_profile)
  - Calendar scheduling in `calendar_week_posts_v2`
  - Publication date/time from `post_type_config`

**Post Types to Handle:**
- `theme` → Creates themed post
- `recipe` → Creates recipe post
- `profile_product` → Creates product profile post
- `profile_surname` → Creates surname profile post
- `family_profile` → Creates family profile post (when implemented)

**When it runs:** Every 5 minutes (via background monitor)

**Output:** Draft posts in `post` table, scheduled in `calendar_week_posts_v2`

---

### 2. Automatic Workflow Execution

**Script**: `scripts/automated_blog_post_workflow.py` (TO BE CREATED)

**What it should do:**
- Finds draft blog posts (`status='draft'`)
- Executes all automated substages based on post type:
  - **Themed posts**: ideas → taxonomy → topic_brainstorming → section_structure → topic_allocation → section_titling → (research stages) → drafting → image_concepts → image_prompts → image_captions → image_generation → optimise → title_summary → header_image → seo_meta
  - **Recipe posts**: taxonomy → topic_brainstorming → section_structure → topic_allocation → section_titling → drafting → image_concepts → image_prompts → image_captions → image_generation → optimise → title_summary → header_image → seo_meta
  - **Profile posts**: Similar to recipe but with profile-specific data
- Updates status to `'ready'` when all automated stages complete
- Stops at review gates (if configured)

**When it runs:** Every 5 minutes (via background monitor)

**Output:** 
- Posts with content generated through automated stages
- Status updated to `'ready'` when complete
- Status remains `'draft'` if review gates require approval

---

### 3. Review Gates (Optional)

**Purpose**: Allow manual review at key stages before proceeding

**Potential Review Points:**
- After `topic_brainstorming` - Review topic selection
- After `section_structure` - Review content structure
- After `drafting` - Review draft content
- After `title_summary` - Review title and summary
- Before publication - Final review

**Implementation:**
- Use `post_approval` table (if exists) or add approval flags
- Automation pauses at review gates
- Manual approval triggers continuation
- Can be configured per post type

---

### 4. Publication (Manual or Automated)

**Current**: Manual publication via UI

**Future**: Could be automated if review gates are passed

**Status**: Posts with `status='ready'` are ready for final review and publication

---

## Comparison with Weekly Content Automation

### Weekly Content (Current - Fully Automated)

```
Calendar Schedule
  ↓ (1 week ahead)
automated_weekly_content_creator.py
  ↓ Creates posting_queue entries
automated_weekly_content_workflow.py
  ↓ Executes workflow stages
Status: 'ready'
  ↓ (at scheduled time)
posting_executor.py
  ↓ Publishes to Facebook
Status: 'published'
```

### Blog Posts (Target - To Be Automated)

```
Calendar Schedule
  ↓ (1 week ahead)
automated_blog_post_creator.py
  ↓ Creates post records
automated_blog_post_workflow.py
  ↓ Executes workflow stages
Status: 'ready'
  ↓ (manual review/publication)
Publication
```

**Key Difference**: Blog posts go to `post` table (full blog posts), not `posting_queue` (social media posts)

---

## Post Type Specifics

### Themed Posts

**Automation Stages:**
1. ✅ Ideas selection (can be automated)
2. ✅ Taxonomy assignment (can be automated)
3. ✅ Topic brainstorming (can be automated)
4. ✅ Section structure design (can be automated)
5. ✅ Topic allocation (can be automated)
6. ✅ Section titling (can be automated)
7. ⚠️ Research stages (may need review)
8. ✅ Drafting (can be automated)
9. ✅ Image concepts/prompts/captions (can be automated)
10. ✅ Image generation (can be automated)
11. ✅ Title & summary (can be automated)
12. ⚠️ Header image (may need review)
13. ⚠️ SEO meta (may need review)
14. ⚠️ Final review (manual)

**Review Gates Recommended:**
- After section structure (verify structure makes sense)
- After drafting (verify content quality)
- Before publication (final check)

---

### Recipe Posts

**Automation Stages:**
1. ✅ Taxonomy assignment (can be automated)
2. ✅ Topic brainstorming (can be automated)
3. ✅ Section structure design (can be automated)
4. ✅ Topic allocation (can be automated)
5. ✅ Section titling (can be automated)
6. ✅ Drafting (can be automated - uses recipe data)
7. ✅ Image concepts/prompts/captions (can be automated)
8. ✅ Image generation (can be automated)
9. ✅ Title & summary (can be automated)
10. ⚠️ Header image (may need review)
11. ⚠️ SEO meta (may need review)
12. ⚠️ Final review (manual)

**Review Gates Recommended:**
- After drafting (verify recipe accuracy)
- Before publication (final check)

---

### Product Profile Posts

**Automation Stages:**
1. ✅ Taxonomy assignment (can be automated)
2. ✅ Product data review (can be automated)
3. ✅ Section structure design (can be automated)
4. ✅ Topic allocation (can be automated)
5. ✅ Section titling (can be automated)
6. ✅ Drafting (can be automated - uses product data)
7. ✅ Image concepts/prompts/captions (can be automated)
8. ✅ Image generation (can be automated)
9. ✅ Title & summary (can be automated)
10. ⚠️ Header image (may need review)
11. ⚠️ SEO meta (may need review)
12. ⚠️ Final review (manual)

**Review Gates Recommended:**
- After product data review (verify data accuracy)
- After drafting (verify content quality)
- Before publication (final check)

---

### Surname Profile Posts

**Automation Stages:**
1. ✅ Taxonomy assignment (can be automated)
2. ✅ Category data review (can be automated)
3. ✅ Section structure design (can be automated)
4. ✅ Topic allocation (can be automated)
5. ✅ Section titling (can be automated)
6. ✅ Drafting (can be automated - uses category data)
7. ✅ Image concepts/prompts/captions (can be automated)
8. ✅ Image generation (can be automated)
9. ✅ Title & summary (can be automated)
10. ⚠️ Header image (may need review)
11. ⚠️ SEO meta (may need review)
12. ⚠️ Final review (manual)

**Review Gates Recommended:**
- After drafting (verify content quality)
- Before publication (final check)

---

### Family Profile Posts (Future)

**Automation Stages:**
1. ✅ Taxonomy assignment (can be automated)
2. ✅ Family research data review (can be automated - uses `families.research_data`)
3. ✅ Section structure design (can be automated)
4. ✅ Topic allocation (can be automated)
5. ✅ Section titling (can be automated)
6. ✅ Drafting (can be automated - uses family research data)
7. ✅ Image concepts/prompts/captions (can be automated)
8. ✅ Image generation (can be automated)
9. ✅ Title & summary (can be automated)
10. ⚠️ Header image (may need review)
11. ⚠️ SEO meta (may need review)
12. ⚠️ Final review (manual)

**Review Gates Recommended:**
- After family research data review (verify research accuracy)
- After drafting (verify content quality)
- Before publication (final check)

---

## Implementation Requirements

### 1. Automated Post Creator Script

**File**: `scripts/automated_blog_post_creator.py`

**Requirements:**
- Query calendar schedule for upcoming weeks (next 7 days)
- Use `resolve_item_for_week()` for each post type category
- Create `post` records with proper post type
- Schedule in `calendar_week_posts_v2` with correct weekday
- Prevent duplicates (check for existing posts)
- Handle all post types: theme, recipe, profile_product, profile_surname, family_profile

**Key Functions:**
- `create_themed_post(theme_item, year, week_number)` 
- `create_recipe_post(recipe_item, year, week_number)`
- `create_product_profile_post(profile_item, year, week_number)`
- `create_surname_profile_post(profile_item, year, week_number)`
- `create_family_profile_post(family_item, year, week_number)` (future)

---

### 2. Automated Workflow Executor Script

**File**: `scripts/automated_blog_post_workflow.py`

**Requirements:**
- Find draft posts (`status='draft'`)
- Determine post type
- Load substages from `config/post_type_substages.py`
- Execute each substage via `blueprints/automation_core.py`
- Handle review gates (pause if approval required)
- Update status to `'ready'` when complete
- Log progress and errors

**Key Functions:**
- `execute_substage(post_id, stage, substage)`
- `check_review_gates(post_id, stage)`
- `update_post_status(post_id, status)`

---

### 3. Background Monitor Integration

**File**: `scripts/background_posting_monitor.sh`

**Add steps:**
1. `automated_blog_post_creator.py` - Create posts
2. `automated_blog_post_workflow.py` - Execute workflows
3. (Existing steps for weekly content and product posts)

---

### 4. Review Gate System (Optional)

**Implementation Options:**

**Option A: Database Table**
- Create `post_approval` table
- Track approval status per stage/substage
- Automation checks approval before proceeding

**Option B: Status Flags**
- Use `post.status` values: 'draft', 'needs_review', 'ready', 'published'
- Add `post.approval_required_stages` JSONB array
- Automation pauses at flagged stages

**Option C: Configuration**
- Per-post-type configuration in `post_type_config`
- Define which stages require review
- Automation respects configuration

---

## Success Criteria

### Phase 1: Post Creation Automation
- ✅ Posts created automatically 1 week in advance
- ✅ All post types supported (themed, recipe, profiles)
- ✅ Proper calendar scheduling
- ✅ No duplicate creation

### Phase 2: Workflow Automation
- ✅ Automated execution of all substages
- ✅ Status progression: draft → ready
- ✅ Review gates respected (if configured)
- ✅ Error handling and logging

### Phase 3: Review & Publication
- ✅ Posts reach 'ready' status automatically
- ✅ Manual review available at key stages
- ✅ Publication workflow ready

---

## Timeline

**Immediate (Week 1):**
- Create `automated_blog_post_creator.py`
- Test post creation for all types
- Integrate with background monitor

**Short-term (Week 2):**
- Create `automated_blog_post_workflow.py`
- Test workflow execution
- Implement basic review gates

**Medium-term (Week 3-4):**
- Refine automation based on testing
- Add family profile support
- Enhance review gate system

---

## Related Documentation

- `docs/WEEKLY_CONTENT_AUTOMATION_COMPLETE.md` - Reference implementation
- `docs/AUTOMATION_PIPELINE_ARCHITECTURE.md` - Architecture framework
- `docs/ONE_CLICK_PUBLICATION_REPORT.md` - One-click system
- `docs/post-types-implementation.md` - Post type details

---

**Last Updated:** 2026-01-19
