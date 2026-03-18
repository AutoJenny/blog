# Unified Publication Dashboard - Implementation Plan

**Date:** 2025-01-XX  
**Status:** Approved for Implementation  
**Priority:** Build unified dashboard first, calendar sync fix later

---

## Executive Summary

This document outlines the implementation plan for a unified publication dashboard that serves as the central hub for all publication-related activities. The dashboard will integrate calendar scheduling, production pipeline, publication queue, and multi-publication support (blog, newsletter, social media).

---

## Architecture Decisions

### 1. Dashboard Location
- **New Route**: `/publication/dashboard`
- **One-Click Publication** (renamed from "One-Click Blog"): Becomes subsidiary, dynamically responds to selected publication and output channel
- **Relationship**: Dashboard is the master view, One-Click Publication is a detail/action view

### 2. Calendar Integration
- **Mini-View**: Embedded calendar showing current month
- **Full Calendar**: Link to `/planning/posts/0/calendar/scheduling`
- **Purpose**: Quick reference, not full editing interface

### 3. Post Type Handling
- **Type-Specific Views**: Each post type has its own workflow
- **Systematic Schema**: Need to review and potentially enhance post type schema
- **Unified Display**: All types visible in dashboard, but workflows are type-specific

### 4. Automation Level
- **Full Automation**: System can publish automatically
- **Review Gates**: User can review and approve before publication
- **Override**: User can intervene at any stage

### 5. Implementation Priority
- **Phase 1**: Build unified dashboard (current focus)
- **Phase 2**: Fix calendar sync (after dashboard is working)
- **Phase 3**: Enhance automation and review gates

---

## Post Type Schema Review

### Current Post Types

1. **Themed Posts**
   - Source: `calendar_themes` table
   - Publication Day: Wednesday (from `post_type_config`)
   - Workflow: Full pipeline (calendar → planning → authoring → imaging → header)

2. **Recipe Posts**
   - Source: `calendar_recipes` table
   - Publication Day: Monday (from `post_type_config`)
   - Workflow: Recipe-specific (may differ from themed)

3. **Profile Posts**
   - Source: `calendar_profile_sequence` (product/surname)
   - Publication Day: Thursday (product), Friday (surname) (from `post_type_config`)
   - Workflow: Profile-specific (may differ from themed)

4. **Weekly Word**
   - Source: `calendar_ideas` with `item_classification = 'weekly_word'`
   - Publication Day: Monday (assumed)
   - Workflow: Minimal (may not need full pipeline)

5. **Weekly Phrase**
   - Source: `calendar_ideas` with `item_classification = 'weekly_phrase'`
   - Publication Day: Wednesday (assumed)
   - Workflow: Minimal (may not need full pipeline)

6. **Weekly Insult**
   - Source: `calendar_ideas` with `item_classification = 'weekly_insult'`
   - Publication Day: Friday (assumed)
   - Workflow: Minimal (may not need full pipeline)

7. **Cross-Promotion Posts**
   - Source: `post.cross_promotion_category_id`
   - Publication Day: Friday (from `post_type_config`)
   - Workflow: Cross-promotion specific

### Proposed Post Type Schema Enhancement

```python
# Post Type Configuration Schema
POST_TYPE_SCHEMA = {
    'themed': {
        'name': 'Themed Post',
        'source_table': 'calendar_themes',
        'id_column': 'id',
        'title_column': 'theme_title',
        'description_column': 'theme_description',
        'publication_day': 3,  # Wednesday
        'publication_time': '14:00:00',
        'workflow': 'full',  # calendar → planning → authoring → imaging → header
        'requires_pipeline': True,
        'requires_imaging': True,
        'requires_header': True,
        'icon': 'book',
        'color': '#3b82f6'
    },
    'recipe': {
        'name': 'Recipe Post',
        'source_table': 'calendar_recipes',
        'id_column': 'id',
        'title_column': 'recipe_title',
        'description_column': 'recipe_description',
        'publication_day': 1,  # Monday
        'publication_time': '10:00:00',
        'workflow': 'recipe',  # recipe-specific workflow
        'requires_pipeline': True,
        'requires_imaging': False,  # Recipes may use existing images
        'requires_header': True,
        'icon': 'utensils',
        'color': '#f59e0b'
    },
    'profile_product': {
        'name': 'Product Profile',
        'source_table': 'calendar_profile_sequence',
        'id_column': 'post_id',
        'title_column': 'post.title',
        'description_column': 'post.profile_standfirst',
        'publication_day': 4,  # Thursday
        'publication_time': '14:00:00',
        'workflow': 'profile',
        'requires_pipeline': True,
        'requires_imaging': True,
        'requires_header': True,
        'icon': 'tag',
        'color': '#8b5cf6'
    },
    'profile_surname': {
        'name': 'Surname Profile',
        'source_table': 'calendar_profile_sequence',
        'id_column': 'post_id',
        'title_column': 'post.title',
        'description_column': 'post.profile_standfirst',
        'publication_day': 5,  # Friday
        'publication_time': '14:00:00',
        'workflow': 'profile',
        'requires_pipeline': True,
        'requires_imaging': True,
        'requires_header': True,
        'icon': 'users',
        'color': '#10b981'
    },
    'weekly_word': {
        'name': 'Word of the Week',
        'source_table': 'calendar_ideas',
        'id_column': 'id',
        'title_column': 'idea_title',
        'description_column': 'idea_description',
        'publication_day': 1,  # Monday
        'publication_time': '09:00:00',
        'workflow': 'minimal',  # No full pipeline needed
        'requires_pipeline': False,
        'requires_imaging': False,
        'requires_header': False,
        'icon': 'book-open',
        'color': '#6366f1'
    },
    'weekly_phrase': {
        'name': 'Phrase of the Week',
        'source_table': 'calendar_ideas',
        'id_column': 'id',
        'title_column': 'idea_title',
        'description_column': 'idea_description',
        'publication_day': 3,  # Wednesday
        'publication_time': '09:00:00',
        'workflow': 'minimal',
        'requires_pipeline': False,
        'requires_imaging': False,
        'requires_header': False,
        'icon': 'quote-left',
        'color': '#8b5cf6'
    },
    'weekly_insult': {
        'name': 'Insult of the Week',
        'source_table': 'calendar_ideas',
        'id_column': 'id',
        'title_column': 'idea_title',
        'description_column': 'idea_description',
        'publication_day': 5,  # Friday
        'publication_time': '09:00:00',
        'workflow': 'minimal',
        'requires_pipeline': False,
        'requires_imaging': False,
        'requires_header': False,
        'icon': 'comment-dots',
        'color': '#ef4444'
    },
    'cross_promotion': {
        'name': 'Cross-Promotion Post',
        'source_table': 'post',
        'id_column': 'id',
        'title_column': 'title',
        'description_column': 'standfirst',
        'publication_day': 5,  # Friday
        'publication_time': '14:00:00',
        'workflow': 'cross_promotion',
        'requires_pipeline': True,
        'requires_imaging': True,
        'requires_header': True,
        'icon': 'link',
        'color': '#ec4899'
    }
}
```

### Implementation: Post Type Configuration Module

**File**: `config/post_type_schema.py`

```python
"""
Post Type Schema Configuration
Defines all post types, their workflows, and publication settings
"""

POST_TYPE_SCHEMA = {
    # ... schema as defined above
}

def get_post_type_config(post_type: str) -> dict:
    """Get configuration for a post type."""
    return POST_TYPE_SCHEMA.get(post_type, {})

def get_all_post_types() -> list:
    """Get list of all post types."""
    return list(POST_TYPE_SCHEMA.keys())

def get_post_types_by_workflow(workflow: str) -> list:
    """Get post types that use a specific workflow."""
    return [
        pt for pt, config in POST_TYPE_SCHEMA.items()
        if config.get('workflow') == workflow
    ]

def requires_pipeline(post_type: str) -> bool:
    """Check if post type requires full pipeline."""
    return POST_TYPE_SCHEMA.get(post_type, {}).get('requires_pipeline', False)
```

---

## Unified Dashboard Structure

### Route: `/publication/dashboard`

**Blueprint**: `blueprints/publication_dashboard.py`

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Publication Dashboard Header                                │
│  - Current Week Display                                      │
│  - Quick Stats (Scheduled, In Progress, Ready, Published)   │
│  - View Toggle (Week View / Month View)                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Section 1: Week Overview                                    │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Current Week: W50 (Dec 8-14, 2025)                   │ │
│  │  [Mini Calendar View]                                 │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Scheduled Items Grid                                 │ │
│  │  Mon: Theme ✅ | Recipe 🟡 | Word ✅                  │ │
│  │  Wed: Phrase ✅                                        │ │
│  │  Thu: Product Profile 🟡                             │ │
│  │  Fri: Surname Profile ⚠️ | Insult ✅                 │ │
│  │  Sat: Product Profile ✅                              │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Section 2: Publication Queue                                │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Today's Publications                                 │ │
│  │  - Theme: "Hogmanay Traditions" [Approve] [Publish]   │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  This Week's Publications                             │ │
│  │  - Mon: Recipe, Word                                  │ │
│  │  - Wed: Phrase                                        │ │
│  │  - Thu: Product Profile                               │ │
│  │  - Fri: Surname Profile, Insult                      │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Section 3: Production Pipeline                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  In Progress                                          │ │
│  │  - Recipe: "Cullen Skink" [Authoring Stage]         │ │
│  │  - Product Profile: "Tartan Scarf" [Imaging]        │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Upcoming (Next Week)                                 │ │
│  │  - Theme: "Burns Night" [Not Started]                │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Section 4: Alerts & Actions Needed                          │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  ⚠️ Surname Profile for Week 50 missing content        │ │
│  │  ⚠️ Recipe post not approved for publication          │ │
│  │  ℹ️ Newsletter issue ready for review                  │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Section 5: Multi-Publication Status                         │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Blog Posts: 5 scheduled this week                    │ │
│  │  Newsletter: Issue #42 ready for review              │ │
│  │  Social Media: 7 posts queued                         │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Status Indicators

- ✅ **Ready**: Post complete, approved, ready to publish
- 🟡 **In Progress**: Post in production pipeline
- ⚠️ **Needs Attention**: Missing content, blocked, or overdue
- ❌ **Missing**: Scheduled but no post created
- ⏸️ **Paused**: User paused automation
- 🔒 **Locked**: Awaiting review/approval

---

## API Endpoints

### 1. Main Dashboard Data

**Endpoint**: `GET /api/publication/dashboard`

**Query Parameters**:
- `week` (optional): Week number (default: current week)
- `year` (optional): Year (default: current year)
- `view` (optional): 'week' or 'month' (default: 'week')

**Response Structure**:
```json
{
  "success": true,
  "data": {
    "current_week": {
      "year": 2025,
      "week": 50,
      "start_date": "2025-12-08",
      "end_date": "2025-12-14",
      "month_name": "December"
    },
    "stats": {
      "scheduled": 7,
      "in_progress": 2,
      "ready": 4,
      "published_today": 1,
      "needs_attention": 1
    },
    "scheduled_items": [
      {
        "category": "theme",
        "post_type": "themed",
        "item_id": 123,
        "title": "Hogmanay Traditions",
        "description": "Exploring Scottish New Year celebrations",
        "scheduled_day": 1,
        "scheduled_date": "2025-12-08",
        "scheduled_time": "14:00:00",
        "post_id": 456,
        "post_status": "ready",
        "pipeline_stage": "header",
        "pipeline_progress": 100,
        "publication_status": "ready",
        "needs_attention": false,
        "alerts": [],
        "workflow": "full",
        "icon": "book",
        "color": "#3b82f6"
      }
      // ... more items
    ],
    "publication_queue": {
      "today": [
        {
          "item_id": 123,
          "title": "Hogmanay Traditions",
          "post_type": "themed",
          "scheduled_time": "2025-12-08T14:00:00Z",
          "status": "ready",
          "can_publish": true,
          "requires_approval": true,
          "approved": false
        }
      ],
      "this_week": [
        // All items scheduled this week
      ],
      "upcoming": [
        // Next week's items
      ]
    },
    "production_pipeline": {
      "in_progress": [
        {
          "item_id": 789,
          "title": "Cullen Skink Recipe",
          "post_type": "recipe",
          "post_id": 790,
          "pipeline_stage": "authoring",
          "pipeline_progress": 60,
          "next_action": "Continue writing",
          "action_url": "/launchpad/one-click-blog?post=790"
        }
      ],
      "upcoming": [
        // Next week's items not yet started
      ]
    },
    "alerts": [
      {
        "type": "warning",
        "severity": "medium",
        "message": "Surname Profile for week 50 is missing content",
        "item_id": 999,
        "category": "profile_surname",
        "action_url": "/launchpad/one-click-blog?post=999",
        "action_label": "Create Post"
      }
    ],
    "multi_publication": {
      "blog_posts": {
        "scheduled_this_week": 5,
        "published_today": 1,
        "in_progress": 2
      },
      "newsletter": {
        "current_issue": {
          "id": 42,
          "status": "ready_for_review",
          "scheduled_date": "2025-12-10",
          "action_url": "/newsletter/issues/42"
        },
        "next_issue": {
          "scheduled_date": "2025-12-17",
          "status": "not_started"
        }
      },
      "social_media": {
        "queued_posts": 7,
        "scheduled_today": 2,
        "platforms": {
          "facebook": 4,
          "instagram": 2,
          "twitter": 1
        }
      }
    },
    "mini_calendar": {
      "current_month": 12,
      "current_year": 2025,
      "weeks": [
        {
          "week": 49,
          "start_date": "2025-12-01",
          "end_date": "2025-12-07",
          "item_count": 5
        },
        {
          "week": 50,
          "start_date": "2025-12-08",
          "end_date": "2025-12-14",
          "item_count": 7,
          "is_current": true
        }
        // ... more weeks
      ]
    }
  }
}
```

### 2. Publication Actions

**Endpoint**: `POST /api/publication/approve`
- Approve item for publication
- Body: `{"item_id": 123, "post_type": "themed"}`

**Endpoint**: `POST /api/publication/publish`
- Publish item immediately
- Body: `{"item_id": 123, "post_type": "themed"}`

**Endpoint**: `POST /api/publication/reschedule`
- Reschedule publication
- Body: `{"item_id": 123, "new_date": "2025-12-10", "new_time": "15:00:00"}`

**Endpoint**: `POST /api/publication/pause`
- Pause automation for item
- Body: `{"item_id": 123}`

**Endpoint**: `POST /api/publication/resume`
- Resume automation for item
- Body: `{"item_id": 123}`

### 3. One-Click Blog Integration

**Endpoint**: `GET /api/publication/item/<item_id>/workflow`
- Get workflow details for specific item
- Returns: Post ID, pipeline status, next actions
- Used to dynamically configure One-Click Blog

---

## Implementation Phases

### Phase 1: Foundation (Week 1)

**Tasks:**
1. Create `config/post_type_schema.py` with post type definitions
2. Create `blueprints/publication_dashboard.py` blueprint
3. Create `templates/publication/dashboard.html` template
4. Create `static/js/publication/dashboard.js` JavaScript
5. Create `static/css/publication/dashboard.css` styles

**Deliverables:**
- Basic dashboard route working
- Post type schema module
- Empty dashboard template (structure only)

### Phase 2: Data Aggregation (Week 1-2)

**Tasks:**
1. Implement `/api/publication/dashboard` endpoint
2. Aggregate calendar data using `utils/calendar_resolver.py`
3. Query post status for each scheduled item
4. Calculate pipeline progress
5. Generate alerts

**Deliverables:**
- Dashboard API returning unified data
- All scheduled items with status
- Basic alerts system

### Phase 3: UI Components (Week 2)

**Tasks:**
1. Build Week Overview section
2. Build Publication Queue section
3. Build Production Pipeline section
4. Build Alerts panel
5. Build Mini Calendar component

**Deliverables:**
- All dashboard sections rendering
- Status indicators working
- Click handlers for actions

### Phase 4: One-Click Blog Integration (Week 2-3)

**Tasks:**
1. Update One-Click Blog to accept item_id parameter
2. Make One-Click Blog dynamically configure based on post type
3. Add navigation from dashboard to One-Click Blog
4. Add "Return to Dashboard" link in One-Click Blog

**Deliverables:**
- One-Click Blog responds to dashboard selections
- Post type-specific workflows in One-Click Blog
- Seamless navigation between dashboard and One-Click Blog

### Phase 5: Publication Actions (Week 3)

**Tasks:**
1. Implement approve endpoint
2. Implement publish endpoint
3. Implement reschedule endpoint
4. Implement pause/resume endpoints
5. Add review gates UI

**Deliverables:**
- All publication actions working
- Review/approval workflow
- Automation controls

### Phase 6: Multi-Publication Integration (Week 3-4)

**Tasks:**
1. Add newsletter status to dashboard
2. Add social media status to dashboard
3. Create unified approval workflow
4. Add cross-publication scheduling

**Deliverables:**
- Newsletter integration
- Social media integration
- Unified approval system

### Phase 7: Automation & Review Gates (Week 4-5)

**Tasks:**
1. Implement automated publishing triggers
2. Implement review gate system
3. Add notification system
4. Add user intervention overrides

**Deliverables:**
- Full automation with review gates
- Notification system
- User intervention capabilities

### Phase 8: Calendar Sync Fix (Week 5)

**Tasks:**
1. Update `/next-up` endpoint to use new calendar system
2. Replace old calendar queries with cyclic resolver
3. Test alignment with calendar view
4. Update One-Click Blog to use fixed endpoint

**Deliverables:**
- Calendar sync fixed
- One-Click Blog showing correct week
- All systems aligned

---

## File Structure

```
blueprints/
  publication_dashboard.py          # Main dashboard blueprint
  publication_actions.py           # Publication action endpoints

config/
  post_type_schema.py              # Post type configuration

templates/
  publication/
    dashboard.html                  # Main dashboard template
    components/
      week_overview.html           # Week overview component
      publication_queue.html       # Publication queue component
      production_pipeline.html     # Production pipeline component
      alerts_panel.html            # Alerts panel component
      mini_calendar.html           # Mini calendar component

static/
  js/
    publication/
      dashboard.js                 # Main dashboard controller
      week_overview.js             # Week overview logic
      publication_queue.js         # Publication queue logic
      production_pipeline.js       # Production pipeline logic
      alerts.js                    # Alerts handling
      mini_calendar.js             # Mini calendar logic
  css/
    publication/
      dashboard.css                # Dashboard styles

utils/
  publication_aggregator.py       # Data aggregation logic
  publication_status.py            # Status calculation logic
```

---

## Next Steps

1. **Review this plan** - Confirm approach and priorities
2. **Start Phase 1** - Create foundation files
3. **Iterate** - Build and test incrementally
4. **Refine** - Adjust based on user feedback

---

*Document Status: Implementation Plan*  
*Created: 2025-01-XX*  
*Author: AI Assistant*  
*Reviewer: User*

