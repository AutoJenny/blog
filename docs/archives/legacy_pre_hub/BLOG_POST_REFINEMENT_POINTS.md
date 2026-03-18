# Blog Post Creation Refinement Points

**Date:** 2026-01-19  
**Purpose:** Specific refinement points identified for one-click functionality and automation

---

## Executive Summary

After walking through the current blog post creation process, the following refinement points have been identified to achieve the goal of self-generating posts to 'ready' status one week in advance.

---

## Refinement Category 1: One-Click Publication Functionality

### 1.1 Calendar Sync Issue

**Current Problem:**
- One-click publication may use deprecated calendar tables
- Inconsistent with unified calendar resolver system

**Location**: `blueprints/automation_calendar.py::get_next_up()`

**Refinement Needed:**
- Update to use `utils/calendar_resolver.py::resolve_item_for_week()`
- Remove queries to deprecated tables (`calendar_weeks_deprecated`, `calendar_ideas_deprecated`)
- Ensure consistency with unified calendar system

**Files to Update:**
- `blueprints/automation_calendar.py`
- `blueprints/launchpad/one_click_blog.py` (if exists)

---

### 1.2 Post Type Support

**Current Problem:**
- One-click may not fully support all post types
- Family profiles not yet integrated

**Refinement Needed:**
- Ensure all post types work in one-click: themed, recipe, profile_product, profile_surname
- Add family_profile support when implemented
- Test each post type flow

**Files to Update:**
- `config/post_type_substages.py` (add family_profile)
- `blueprints/automation_core.py` (ensure all types supported)
- `templates/launchpad/one_click_publication.html` (or similar)

---

### 1.3 Output Channel Support

**Current Problem:**
- No output channel-specific stages system
- All pipelines assume blog output

**Refinement Needed:**
- Create `config/output_channel_stages.py`
- Define stages per (post_type, output_channel) combination
- Update UI to support channel selection

**Files to Create/Update:**
- `config/output_channel_stages.py` (NEW)
- `blueprints/automation_core.py` (add channel support)
- `templates/launchpad/one_click_publication.html` (add channel selector)

---

### 1.4 Navigation Flow

**Current Problem:**
- Manual navigation between stages
- No clear "next" button or progress indicator

**Refinement Needed:**
- Add "Next Stage" buttons
- Show progress indicator
- Auto-navigate when stage completes

**Files to Update:**
- All planning/authoring/imaging/header templates
- Add navigation JavaScript

---

## Refinement Category 2: Automation

### 2.1 Automated Post Creation

**Current Problem:**
- Posts created manually via UI
- No automated creation from calendar schedule

**Refinement Needed:**
- Create `scripts/automated_blog_post_creator.py`
- Query calendar schedule for upcoming weeks
- Create posts 1 week in advance
- Support all post types

**Script Requirements:**
```python
# Pseudo-code structure
def create_blog_posts_for_upcoming_weeks(days_ahead=7):
    # Get current week
    # For each upcoming week (next 7 days):
    #   - Resolve calendar items using resolve_item_for_week()
    #   - For each item (theme, recipe, profile):
    #     - Check if post already exists
    #     - Create post if needed
    #     - Schedule in calendar_week_posts_v2
    #     - Set status='draft'
```

**Files to Create:**
- `scripts/automated_blog_post_creator.py`

**Integration:**
- Add to `scripts/background_posting_monitor.sh`

---

### 2.2 Automated Workflow Execution

**Current Problem:**
- All workflow stages executed manually
- No automation to process posts to 'ready' status

**Refinement Needed:**
- Create `scripts/automated_blog_post_workflow.py`
- Execute all automatable substages
- Respect review gates
- Update status to 'ready' when complete

**Script Requirements:**
```python
# Pseudo-code structure
def execute_workflow_for_draft_posts():
    # Find draft posts
    # For each draft post:
    #   - Determine post type
    #   - Load substages from config/post_type_substages.py
    #   - For each automatable substage:
    #     - Check if already complete
    #     - Check review gates
    #     - Execute substage via automation_core.py
    #     - Update progress
    #   - If all automatable stages complete:
    #     - Update status to 'ready'
```

**Files to Create:**
- `scripts/automated_blog_post_workflow.py`

**Integration:**
- Add to `scripts/background_posting_monitor.sh`
- Use `blueprints/automation_core.py::execute_substage()`

---

### 2.3 Review Gate System

**Current Problem:**
- No review gate system
- Cannot pause automation for manual review

**Refinement Needed:**
- Implement review gate configuration
- Add approval workflow
- Pause automation at review gates

**Implementation Options:**

**Option A: Database Table**
```sql
CREATE TABLE post_approval (
    post_id INTEGER,
    stage VARCHAR(50),
    substage VARCHAR(50),
    approval_status VARCHAR(50), -- 'pending', 'approved', 'rejected'
    approver_id INTEGER,
    approved_at TIMESTAMP
);
```

**Option B: Status Flags**
- Use `post.status` values: 'draft', 'needs_review', 'ready'
- Add `post.approval_required_stages` JSONB array
- Automation checks flags before proceeding

**Option C: Configuration**
- Per-post-type config in `post_type_config`
- Define which stages require review
- Automation respects config

**Recommended**: Option B (Status Flags) - simplest, no new tables

**Files to Update:**
- `scripts/automated_blog_post_workflow.py` (check review gates)
- `blueprints/automation_core.py` (respect review gates)
- Add approval UI (optional)

---

### 2.4 Status Management

**Current Problem:**
- Status flow not clearly defined for automation
- No clear 'ready' status definition

**Refinement Needed:**
- Define status flow: draft → in_progress → needs_review → ready → published
- Update automation to set appropriate statuses
- Add status tracking

**Status Flow:**
```
draft (created)
  ↓
in_progress (automation running)
  ↓
needs_review (at review gate)
  ↓
ready (all automated stages complete, review passed)
  ↓
published (manually published)
```

**Files to Update:**
- `scripts/automated_blog_post_workflow.py`
- Status update logic in automation_core.py

---

## Refinement Category 3: Process Improvements

### 3.1 Ideas Page Flow

**Current Problem:**
- Ideas page doesn't show available ideas clearly
- No clear selection/confirmation flow
- Expanded idea generation is optional

**Refinement Needed:**
- Show available ideas from calendar
- Add selection/confirmation flow
- Auto-generate expanded idea after confirmation
- Auto-navigate to next stage

**Files to Update:**
- `templates/planning/calendar/ideas.html`
- Add idea selection UI
- Add confirmation flow

---

### 3.2 Stage Completion Detection

**Current Problem:**
- No clear way to detect if stage is complete
- Manual checking required

**Refinement Needed:**
- Add completion detection logic
- Check database for required data
- Mark stages as complete automatically

**Implementation:**
- Check if required fields are populated
- Check if required substages are done
- Update stage status in workflow tracking

**Files to Update:**
- `blueprints/automation_core.py` (add completion detection)
- Workflow status tracking

---

### 3.3 Error Handling & Recovery

**Current Problem:**
- No robust error handling in automation
- Failed stages may block progress

**Refinement Needed:**
- Add comprehensive error handling
- Log errors for debugging
- Retry failed stages
- Skip problematic stages (with flag)

**Files to Update:**
- `scripts/automated_blog_post_workflow.py`
- Add error logging
- Add retry logic

---

## Refinement Category 4: Family Profile Integration

### 4.1 Database Schema

**Current Problem:**
- No `profile_family_id` field in post table
- Family profiles not linked to posts

**Refinement Needed:**
- Add `profile_family_id` to `post` table
- Link to `families.id`
- Or extend `profile_type` to include 'family'

**Migration Needed:**
```sql
ALTER TABLE post ADD COLUMN profile_family_id INTEGER REFERENCES families(id);
CREATE INDEX idx_post_profile_family ON post(profile_family_id);
```

**Files to Create:**
- `migrations/add_profile_family_id_to_post.sql`

---

### 4.2 Post Type Configuration

**Current Problem:**
- Family profiles not in `config/post_type_substages.py`
- No publication day/time config

**Refinement Needed:**
- Add `family_profile` to `config/post_type_substages.py`
- Define stages: planning → authoring → imaging → header
- Add to `post_type_config` table

**Files to Update:**
- `config/post_type_substages.py`
- `blueprints/post_type_config.py` (add family_profile config)

---

### 4.3 Calendar Integration

**Current Problem:**
- Family profiles not in calendar system
- No schedule for family profiles

**Refinement Needed:**
- Add `family_profile` category to calendar resolver
- Create schedule (JSON files or database table)
- Integrate with `resolve_item_for_week()`

**Files to Update:**
- `utils/calendar_resolver.py` (add family_profile support)
- Calendar schedule JSON files or database

---

### 4.4 Research Integration

**Current Problem:**
- Family research data not used in post creation
- No integration with family research framework

**Refinement Needed:**
- Use `utils/family_research/` for data extraction
- Leverage `families.research_data` JSONB field
- Follow family research workflow

**Files to Update:**
- Post creation logic to use family research
- Planning stages to display family research data

---

## Priority Ranking

### High Priority (Immediate)
1. ✅ Automated post creation script
2. ✅ Automated workflow execution script
3. ✅ Review gate system
4. ✅ Status management

### Medium Priority (Short-term)
5. Calendar sync fix
6. Post type support (all types)
7. Navigation flow improvements
8. Stage completion detection

### Low Priority (Future)
9. Output channel stages system
10. Family profile integration
11. Error handling enhancements
12. Ideas page flow improvements

---

## Implementation Order

### Phase 1: Core Automation (Week 1)
1. Create `automated_blog_post_creator.py`
2. Create `automated_blog_post_workflow.py`
3. Add to background monitor
4. Test with themed posts

### Phase 2: Review Gates (Week 2)
1. Implement review gate system
2. Add status management
3. Test review workflow

### Phase 3: Process Improvements (Week 3)
1. Fix calendar sync
2. Improve navigation
3. Add completion detection

### Phase 4: Family Profiles (Week 4)
1. Database schema
2. Post type config
3. Calendar integration
4. Research integration

---

## Success Metrics

### Automation Success
- ✅ Posts created 1 week in advance
- ✅ Posts reach 'ready' status automatically
- ✅ Review gates respected
- ✅ All post types supported

### Process Success
- ✅ Clear navigation flow
- ✅ Progress tracking visible
- ✅ Error handling robust
- ✅ User experience improved

---

**Last Updated:** 2026-01-19
