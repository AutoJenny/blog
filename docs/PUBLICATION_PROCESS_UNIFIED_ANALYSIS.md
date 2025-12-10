# Publication Process - Unified Analysis & Proposal

**Date:** 2025-01-XX  
**Purpose:** Comprehensive review of blog creation and publishing process, identifying gaps and proposing unified solution

---

## Executive Summary

The system has multiple working components for calendar scheduling, blog post creation, and publishing, but they operate in isolation without a unified interface. This document analyzes the current state and proposes a unified publication management dashboard that ties everything together.

---

## Current State Analysis

### 1. Calendar Scheduling System ✅ (Well-Developed)

**Components:**
- **Week View**: `/planning/posts/0/calendar/week-view?year=2025&week=50`
  - Shows single week with all scheduled items
  - Displays: Themes (Mon), Recipes (Wed), Surnames (Fri), Products (Sat)
  - Words/Phrases/Insults on specific days
  - Integrated with new cyclic JSON-backed system
  
- **Annual Schedule**: `/planning/posts/0/calendar/scheduling`
  - Shows 52-week rolling window
  - Drag-and-drop reordering
  - Modal editing for all items
  - Range-based navigation (year/month forward/back)
  - Uses JSON-backed display API

**Strengths:**
- Fast JSON-backed display
- Comprehensive category support (7 categories)
- Good UI for viewing and editing schedules
- Well-documented architecture

**Gaps:**
- No connection to actual post creation workflow
- No visibility into post production status
- No integration with publishing automation

### 2. One-Click Blog Launchpad ⚠️ (Partially Integrated)

**Components:**
- **Main Page**: `/launchpad/one-click-blog`
  - "Next Up" panel showing current week's selected idea
  - Pipeline progress tracker (calendar → planning → authoring → imaging → header)
  - Post selector dropdown
  - Automation substage controls

**Current Functionality:**
- Loads current week from `/launchpad/one-click-blog/api/next-up`
- Shows selected idea and alternatives
- Displays pipeline status for selected post
- Allows running individual substages
- Shows production status (not_started, in_progress, completed)

**Issues Identified:**
1. **Calendar Sync Problem**: User reports it's "showing wrongly for this week"
   - Likely using old `calendar_schedule` table instead of new cyclic system
   - `/next-up` endpoint uses `calendar_weeks.is_current_week` and `calendar_schedule`
   - New calendar uses JSON files and cyclic resolver
   - **Mismatch**: Old system vs. new system

2. **Post Type Handling**: 
   - Designed primarily for "themed" posts
   - Doesn't handle recipes, profiles, words/phrases/insults differently
   - No post-type-specific workflows

3. **Limited Automation Scope**:
   - Only handles blog post creation
   - No newsletter integration
   - No social media syndication
   - No cross-publication workflows

**Strengths:**
- Good pipeline visualization
- Automation controls
- Post selection interface

**Gaps:**
- Not synced with new calendar system
- Doesn't handle all post types
- No multi-publication support

### 3. Newsletter System ✅ (Separate System)

**Components:**
- Multiple blueprints for newsletter generation
- Block-based content system
- LLM-powered content generation
- Preview and approval workflow

**Status:**
- Functional but isolated
- No integration with calendar
- No integration with blog post workflow
- Manual trigger process

### 4. Social Media Syndication ⚠️ (Partially Implemented)

**Components:**
- Daily product posts system (Facebook)
- Syndication progress tracking
- Automated posting queue
- Platform-specific content generation

**Status:**
- MVP implemented for Facebook
- Not integrated with calendar
- Not integrated with blog post workflow
- Separate management interface

### 5. Post Type Configuration ✅ (Implemented)

**Components:**
- `post_type_config` table with publication day settings
- Themed: Wednesday
- Recipe: Monday
- Profile: Thursday
- Cross-promotion: Friday

**Status:**
- Database structure exists
- Used in some scheduling logic
- Not fully integrated across all systems

---

## Key Problems Identified

### Problem 1: Calendar System Mismatch
- **New Calendar**: Uses JSON files, cyclic resolver, `calendar_themes`, `calendar_recipes`, etc.
- **Old Calendar**: Uses `calendar_schedule`, `calendar_week_posts`, `calendar_weeks.is_current_week`
- **One-Click Blog**: Still uses old system (`/next-up` endpoint)
- **Result**: Displays wrong week/items

### Problem 2: No Unified View
- Calendar shows schedule but not production status
- One-Click Blog shows production but not full calendar context
- Newsletter is completely separate
- Social media is completely separate
- **Result**: User must navigate multiple pages to understand full picture

### Problem 3: No Publication Workflow
- Calendar shows what's scheduled
- One-Click Blog shows what's in production
- No view showing: "What needs to be published today/this week?"
- No automated publishing trigger
- **Result**: Manual coordination required

### Problem 4: Post Type Fragmentation
- Different post types (themed, recipe, profile, word/phrase/insult) handled differently
- Calendar shows all types
- One-Click Blog primarily handles themed posts
- **Result**: Inconsistent experience

### Problem 5: No Review/Approval Workflow
- Calendar allows scheduling
- One-Click Blog allows production
- No unified "ready for review" queue
- No "approve and publish" workflow
- **Result**: Manual checking required

---

## Proposed Unified Solution

### Core Concept: Publication Management Dashboard

A single unified interface that shows:
1. **What's Scheduled** (from calendar)
2. **What's In Production** (from pipeline)
3. **What's Ready to Publish** (status checks)
4. **What's Published** (recent publications)
5. **What Needs Attention** (overdue, missing content, etc.)

### Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│         Unified Publication Dashboard                   │
│  (Single UI showing all publication-related info)      │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼──────┐  ┌───────▼──────┐  ┌───────▼──────┐
│   Calendar   │  │   Pipeline   │  │  Publishing   │
│   Service    │  │   Service    │  │   Service    │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
              ┌───────────▼───────────┐
              │   Unified Data Layer  │
              │  (Aggregates all data) │
              └────────────────────────┘
```

### Proposed Dashboard Structure

#### Section 1: Week Overview
- **Current Week Display**
  - Week number, dates, year
  - All scheduled items (from calendar JSON)
  - Production status for each item
  - Publication status for each item
  - Visual indicators: ✅ Ready, 🟡 In Progress, ⚠️ Needs Attention, ❌ Missing

#### Section 2: Publication Queue
- **Today's Publications**
  - Items scheduled to publish today
  - Status: Ready/Needs Review/Blocked
  - Quick actions: Approve, Publish, Reschedule
  
- **This Week's Publications**
  - All items scheduled this week
  - Grouped by day
  - Status indicators
  - Drag-and-drop rescheduling

#### Section 3: Production Pipeline
- **In Progress**
  - Items currently in production
  - Pipeline stage for each
  - Progress indicators
  - Quick links to edit/continue
  
- **Upcoming**
  - Next week's items
  - Pre-production status
  - Can start early

#### Section 4: Content Calendar Integration
- **Embedded Calendar View**
  - Mini version of full calendar
  - Click to expand to full view
  - Shows all categories
  - Color-coded by status

#### Section 5: Multi-Publication Support
- **Blog Posts**
  - Themed, Recipe, Profile, Word/Phrase/Insult
  - All in one view with type badges
  
- **Newsletter**
  - Current issue status
  - Next issue planning
  - Quick generate/preview
  
- **Social Media**
  - Scheduled posts
  - Queue status
  - Platform-specific views

### Technical Implementation

#### New Unified API Endpoint

```python
GET /api/publication/dashboard
```

**Returns:**
```json
{
  "current_week": {
    "year": 2025,
    "week": 50,
    "start_date": "2025-12-08",
    "end_date": "2025-12-14"
  },
  "scheduled_items": [
    {
      "category": "theme",
      "item_id": 123,
      "title": "Hogmanay Traditions",
      "scheduled_week": 50,
      "scheduled_day": 1,  // Monday
      "post_id": 456,
      "post_status": "draft",
      "pipeline_stage": "authoring",
      "publication_status": "scheduled",
      "publication_date": "2025-12-08T14:00:00Z",
      "needs_attention": false,
      "post_type": "themed"
    },
    // ... more items
  ],
  "publication_queue": {
    "today": [...],
    "this_week": [...],
    "upcoming": [...]
  },
  "production_pipeline": {
    "in_progress": [...],
    "upcoming": [...]
  },
  "alerts": [
    {
      "type": "warning",
      "message": "Recipe post for week 50 is missing content",
      "item_id": 789,
      "action_url": "/launchpad/one-click-blog?post=789"
    }
  ]
}
```

#### Data Aggregation Logic

1. **Load Calendar Data**
   - Use `utils/calendar_resolver.py` to get current week's items
   - For each category, resolve item for current week
   - Get item details (title, description, etc.)

2. **Load Post Status**
   - For each calendar item, check if post exists
   - Query `post` table for status
   - Query `post_development` for pipeline stage
   - Query `calendar_week_posts` for publication date

3. **Load Pipeline Status**
   - For posts in production, get pipeline stage
   - Check substage completion
   - Calculate progress percentage

4. **Calculate Publication Status**
   - Compare current date/time to scheduled publication
   - Determine: scheduled, ready, published, overdue
   - Check for blockers (missing content, not approved, etc.)

5. **Generate Alerts**
   - Items scheduled but no post created
   - Posts in draft but publication date approaching
   - Overdue publications
   - Missing required content

### UI Components

#### 1. Week Overview Card
- Large display of current week
- Grid of scheduled items with status badges
- Click item to open detail modal
- Quick actions: Edit, View Post, Publish

#### 2. Publication Queue Table
- Sortable table of upcoming publications
- Filters: Today, This Week, All
- Status column with color coding
- Action buttons: Approve, Publish, Reschedule, View

#### 3. Production Pipeline View
- Kanban-style board (Not Started → In Progress → Ready → Published)
- Drag-and-drop between stages
- Progress indicators
- Quick links to continue work

#### 4. Calendar Mini-View
- Compact calendar showing current month
- Color dots for scheduled items
- Click to expand full calendar
- Navigation to other weeks

#### 5. Alerts Panel
- List of items needing attention
- Grouped by severity
- Action buttons for each alert
- Dismissible notifications

### Integration Points

#### Fix Calendar Sync
1. Update `/next-up` endpoint to use new calendar system
2. Replace `calendar_schedule` queries with `resolve_item_for_week()`
3. Use JSON-backed calendar data
4. Ensure week calculation matches calendar view

#### Unify Post Type Handling
1. Extend pipeline manager to handle all post types
2. Add post-type-specific workflows
3. Show type badges throughout UI
4. Use `post_type_config` for scheduling

#### Connect Newsletter
1. Add newsletter section to dashboard
2. Show current issue status
3. Link to newsletter generation
4. Schedule newsletter alongside blog posts

#### Connect Social Media
1. Show scheduled social posts
2. Link to syndication queue
3. Show cross-publication status
4. Unified approval workflow

### Migration Path

#### Phase 1: Fix Calendar Sync (Immediate)
- Update `/next-up` endpoint
- Test with current week
- Verify alignment with calendar view

#### Phase 2: Create Unified API (Week 1)
- Implement `/api/publication/dashboard`
- Aggregate data from all sources
- Return unified JSON structure

#### Phase 3: Build Dashboard UI (Week 2)
- Create new dashboard template
- Implement week overview
- Implement publication queue
- Add alerts panel

#### Phase 4: Integrate Production Pipeline (Week 3)
- Connect pipeline status
- Add production view
- Link to One-Click Blog

#### Phase 5: Add Multi-Publication (Week 4)
- Newsletter integration
- Social media integration
- Unified approval workflow

#### Phase 6: Automation (Week 5)
- Automated publishing triggers
- Review/approval workflow
- Notification system

---

## Benefits of Unified Approach

1. **Single Source of Truth**
   - One place to see everything
   - No context switching
   - Consistent data

2. **Better Visibility**
   - See what's scheduled, in production, and ready to publish
   - Identify bottlenecks
   - Plan ahead

3. **Streamlined Workflow**
   - Clear next actions
   - Reduced clicks
   - Faster decision-making

4. **Automation Ready**
   - Clear status indicators
   - Automated triggers
   - Approval workflows

5. **User-Friendly**
   - Intuitive interface
   - Visual indicators
   - Quick actions

---

## Questions for Discussion

1. **Dashboard Location**: New route (`/publication/dashboard`) or enhance existing (`/launchpad/one-click-blog`)?

2. **Calendar Integration**: Embed full calendar or mini-view with link?

3. **Post Type Handling**: Unified workflow or type-specific views?

4. **Automation Level**: Full automation with review gates, or manual approval required?

5. **Notification System**: In-app alerts, email, or both?

6. **Multi-User Support**: Role-based permissions, approval chains?

---

## Next Steps

1. **Review this analysis** - Confirm understanding of current state
2. **Discuss proposal** - Refine unified dashboard concept
3. **Prioritize phases** - Decide what to build first
4. **Create detailed spec** - Technical implementation details
5. **Begin implementation** - Start with Phase 1 (calendar sync fix)

---

*Document Status: Draft for Discussion*  
*Created: 2025-01-XX*  
*Author: AI Assistant*  
*Reviewer: User*

