# One-Click Blog Automation System - Technical Implementation Plan

## Overview
This document provides comprehensive technical specifications for the One-Click Blog automation system, designed to automate the entire blog post creation pipeline from calendar selection to publication.

## Database Schema Design

### New Tables Required

#### 1. automation_state
Tracks the current state of automation for each post.

```sql
CREATE TABLE automation_state (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id) ON DELETE CASCADE,
    current_stage VARCHAR(50) NOT NULL, -- 'calendar', 'concept', 'authoring', 'imaging'
    current_substage VARCHAR(50), -- 'view', 'brainstorm', 'author-first-drafts', etc.
    automation_mode VARCHAR(20) DEFAULT 'auto', -- 'auto', 'manual', 'paused'
    last_action_at TIMESTAMP DEFAULT NOW(),
    error_count INTEGER DEFAULT 0,
    error_message TEXT,
    retry_after TIMESTAMP,
    metadata JSONB, -- stage-specific data like progress percentages, LLM responses, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(post_id)
);

-- Indexes
CREATE INDEX idx_automation_state_post_id ON automation_state(post_id);
CREATE INDEX idx_automation_state_stage ON automation_state(current_stage);
CREATE INDEX idx_automation_state_mode ON automation_state(automation_mode);
CREATE INDEX idx_automation_state_last_action ON automation_state(last_action_at);
```

#### 2. automation_history
Audit trail of all automation actions.

```sql
CREATE TABLE automation_history (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id) ON DELETE CASCADE,
    stage VARCHAR(50) NOT NULL,
    substage VARCHAR(50),
    action_type VARCHAR(50) NOT NULL, -- 'start', 'complete', 'error', 'retry', 'manual_intervention'
    status VARCHAR(20) NOT NULL, -- 'success', 'failed', 'skipped'
    duration_ms INTEGER, -- time taken for the action
    error_message TEXT,
    input_data JSONB, -- input parameters for the action
    output_data JSONB, -- output/result data
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_automation_history_post_id ON automation_history(post_id);
CREATE INDEX idx_automation_history_stage ON automation_history(stage);
CREATE INDEX idx_automation_history_action_type ON automation_history(action_type);
CREATE INDEX idx_automation_history_created_at ON automation_history(created_at);
```

#### 3. alert_queue
Header notification system for automation alerts.

```sql
CREATE TABLE alert_queue (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL, -- 'stuck_post', 'ready_publish', 'missing_schedule', 'low_queue', 'manual_review', 'completion'
    severity VARCHAR(20) DEFAULT 'info', -- 'info', 'warning', 'error', 'success'
    post_id INTEGER REFERENCES post(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    action_url VARCHAR(500), -- URL for action button
    action_text VARCHAR(100), -- text for action button
    is_read BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP, -- auto-expire old alerts
    metadata JSONB, -- additional data for alert handling
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_alert_queue_is_read ON alert_queue(is_read);
CREATE INDEX idx_alert_queue_alert_type ON alert_queue(alert_type);
CREATE INDEX idx_alert_queue_severity ON alert_queue(severity);
CREATE INDEX idx_alert_queue_created_at ON alert_queue(created_at);
CREATE INDEX idx_alert_queue_expires_at ON alert_queue(expires_at);
```

#### 4. automation_settings
User preferences for automation behavior.

```sql
CREATE TABLE automation_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Default settings
INSERT INTO automation_settings (setting_key, setting_value, description) VALUES
('default_automation_mode', '{"calendar": "auto", "concept": "auto", "authoring": "manual", "imaging": "auto"}', 'Default automation mode per stage'),
('retry_settings', '{"max_retries": 3, "retry_delay_minutes": 5, "exponential_backoff": true}', 'Retry configuration'),
('notification_preferences', '{"email": false, "browser": true, "sound": false}', 'Notification preferences'),
('publication_timing', '{"default_publish_time": "14:00", "require_approval": true, "auto_publish": false}', 'Publication timing defaults'),
('llm_providers', '{"calendar": "ollama", "concept": "ollama", "authoring": "ollama", "imaging": "ollama"}', 'LLM provider preferences per stage');
```

### Schema Modifications to Existing Tables

#### calendar_schedule Enhancements
```sql
ALTER TABLE calendar_schedule 
ADD COLUMN automation_enabled BOOLEAN DEFAULT TRUE,
ADD COLUMN publish_time TIME DEFAULT '14:00:00',
ADD COLUMN auto_start_days_before INTEGER DEFAULT 7,
ADD COLUMN requires_approval BOOLEAN DEFAULT TRUE;

-- Indexes
CREATE INDEX idx_calendar_schedule_automation_enabled ON calendar_schedule(automation_enabled);
CREATE INDEX idx_calendar_schedule_publish_time ON calendar_schedule(publish_time);
```

#### post_development Enhancements
```sql
ALTER TABLE post_development 
ADD COLUMN automation_progress JSONB, -- tracks progress through substages
ADD COLUMN automation_metadata JSONB; -- additional automation data

-- Indexes
CREATE INDEX idx_post_development_automation_progress ON post_development USING GIN(automation_progress);
```

## API Endpoints Specification

### Base URL: `/launchpad/one-click-blog/api`

#### 1. Next Up Panel
```python
GET /next-up
Response: {
    "success": true,
    "data": {
        "current_week": {
            "week_number": 42,
            "year": 2025,
            "start_date": "2025-10-14",
            "end_date": "2025-10-20",
            "month_name": "Oct"
        },
        "selected_idea": {
            "id": 123,
            "title": "Halloween Traditions in Scottish Castles",
            "description": "Ghost stories and legends from historic Scottish castles",
            "categories": ["History", "Culture", "Halloween"],
            "priority": "high"
        },
        "alternative_ideas": [
            {
                "id": 124,
                "title": "Autumn Harvest Festivals in the Highlands",
                "description": "Traditional harvest celebrations and customs",
                "categories": ["Culture", "Seasonal"],
                "priority": "medium"
            },
            {
                "id": 125,
                "title": "Traditional Scottish Soups for Cold Weather",
                "description": "Hearty soups perfect for autumn and winter",
                "categories": ["Food", "Seasonal"],
                "priority": "medium"
            }
        ],
        "can_start_automation": true,
        "next_available_slot": "2025-10-15T09:00:00Z"
    }
}
```

#### 2. Pipeline Status
```python
GET /pipeline-status/<post_id>
Response: {
    "success": true,
    "data": {
        "post_id": 77,
        "title": "Welsh Myths and Legends",
        "current_stage": "authoring",
        "current_substage": "author-first-drafts",
        "overall_progress": 67,
        "stages": {
            "calendar": {
                "status": "complete",
                "progress": 100,
                "substages": {
                    "view": {"status": "complete", "completed_at": "2025-10-10T10:00:00Z"},
                    "ideas": {"status": "complete", "completed_at": "2025-10-10T10:15:00Z"}
                }
            },
            "concept": {
                "status": "complete",
                "progress": 100,
                "substages": {
                    "brainstorm": {"status": "complete", "completed_at": "2025-10-10T11:00:00Z"},
                    "section-structure": {"status": "complete", "completed_at": "2025-10-10T12:00:00Z"},
                    "topic-allocation": {"status": "complete", "completed_at": "2025-10-10T13:00:00Z"},
                    "titling": {"status": "complete", "completed_at": "2025-10-10T14:00:00Z"},
                    "outline": {"status": "complete", "completed_at": "2025-10-10T15:00:00Z"}
                }
            },
            "authoring": {
                "status": "in_progress",
                "progress": 60,
                "automation_mode": "manual",
                "substages": {
                    "author-first-drafts": {"status": "in_progress", "progress": 80},
                    "fix-language": {"status": "pending"},
                    "image-concepts": {"status": "pending"},
                    "image-prompts": {"status": "pending"},
                    "image-captions": {"status": "pending"}
                }
            },
            "imaging": {
                "status": "pending",
                "progress": 0,
                "automation_mode": "auto",
                "substages": {
                    "image-generation": {"status": "pending"},
                    "optimise": {"status": "pending"}
                }
            }
        },
        "estimated_completion": "2025-10-12T16:00:00Z",
        "last_action_at": "2025-10-10T15:30:00Z",
        "error_count": 0
    }
}
```

#### 3. Blog Queue
```python
GET /blog-queue?filter=all&sort=week&page=1&limit=20
Response: {
    "success": true,
    "data": {
        "posts": [
            {
                "post_id": 77,
                "title": "Welsh Myths and Legends",
                "week_number": 41,
                "week_dates": "Oct 7-13, 2025",
                "status": "in_progress",
                "current_stage": "authoring",
                "current_substage": "author-first-drafts",
                "progress": 67,
                "last_updated": "2025-10-10T15:30:00Z",
                "automation_mode": "manual",
                "can_resume": true,
                "can_pause": true
            },
            {
                "post_id": 78,
                "title": "Halloween Traditions in Scottish Castles",
                "week_number": 42,
                "week_dates": "Oct 14-20, 2025",
                "status": "pending",
                "current_stage": "calendar",
                "current_substage": "view",
                "progress": 0,
                "last_updated": "2025-10-10T16:00:00Z",
                "automation_mode": "auto",
                "can_resume": false,
                "can_pause": false
            }
        ],
        "pagination": {
            "current_page": 1,
            "total_pages": 3,
            "total_posts": 45,
            "has_next": true,
            "has_prev": false
        },
        "filters": {
            "available": ["all", "draft", "in_progress", "scheduled", "published", "failed"],
            "current": "all"
        },
        "sort_options": {
            "available": ["week", "status", "progress", "updated"],
            "current": "week"
        }
    }
}
```

#### 4. Alerts
```python
GET /alerts?unread_only=true
Response: {
    "success": true,
    "data": {
        "alerts": [
            {
                "id": 1,
                "alert_type": "stuck_post",
                "severity": "warning",
                "post_id": 76,
                "title": "Post #76 Stuck at Image Generation",
                "message": "Failed 3 times - needs manual attention",
                "action_url": "/launchpad/one-click-blog?post=76",
                "action_text": "View Post",
                "created_at": "2025-10-10T14:30:00Z"
            },
            {
                "id": 2,
                "alert_type": "ready_publish",
                "severity": "info",
                "post_id": 75,
                "title": "Post #75 Ready for Publication",
                "message": "Scheduled for today at 2:00 PM",
                "action_url": "/launchpad/one-click-blog?post=75&action=publish",
                "action_text": "Publish Now",
                "created_at": "2025-10-10T13:00:00Z"
            }
        ],
        "unread_count": 2
    }
}
```

#### 5. Automation Control
```python
POST /start-automation
Body: {
    "post_id": 78,
    "idea_id": 123,
    "publish_time": "2025-10-15T14:00:00Z",
    "require_approval": true
}
Response: {
    "success": true,
    "data": {
        "automation_id": "auto_78_20251010_160000",
        "status": "started",
        "estimated_completion": "2025-10-12T16:00:00Z",
        "current_stage": "calendar",
        "message": "Automation started successfully"
    }
}

POST /toggle-mode
Body: {
    "post_id": 77,
    "stage": "authoring",
    "mode": "manual"
}
Response: {
    "success": true,
    "data": {
        "stage": "authoring",
        "mode": "manual",
        "message": "Mode updated successfully"
    }
}

POST /alert/dismiss/<alert_id>
Response: {
    "success": true,
    "data": {
        "alert_id": 1,
        "message": "Alert dismissed successfully"
    }
}
```

## UI Component Specifications

### 1. Next Up Panel
- **Purpose**: Show next scheduled week and selected idea
- **Layout**: Horizontal card with week info, idea details, and action buttons
- **Interactions**: 
  - Dropdown to change idea selection
  - "Start Production" button to initiate automation
  - "Schedule" button to set publish date/time
  - Visual timeline showing current week position

### 2. Pipeline Progress Tracker
- **Purpose**: Real-time visualization of automation progress
- **Layout**: Vertical accordion with collapsible stages
- **Features**:
  - Progress bars for each stage
  - Status indicators (complete, in progress, pending, failed)
  - Per-stage automation mode toggles
  - Substage breakdown with individual status
  - Action buttons (Review, Skip, Manual/Auto toggle)
  - Estimated time remaining
  - Last action timestamp

### 3. Blog Queue Panel
- **Purpose**: Manage all posts in the pipeline
- **Layout**: Card-based list with filtering and sorting
- **Features**:
  - Filter by status (All, Draft, In Progress, Scheduled, Published, Failed)
  - Sort by week, status, progress, or last updated
  - Card view showing week, title, progress, current stage
  - Quick actions (View, Resume, Pause, Delete)
  - Pagination for large lists
  - "Create New Post" button

### 4. Header Alert System
- **Purpose**: Show automation alerts and notifications
- **Layout**: Bell icon with badge count, dropdown panel on click
- **Features**:
  - Badge showing unread count
  - Alert cards with icon, message, timestamp
  - Action buttons (View, Retry, Skip, Dismiss)
  - "Mark all as read" option
  - Auto-expire old alerts

## JavaScript Architecture

### OneClickBlogManager Class
```javascript
class OneClickBlogManager {
    constructor() {
        this.currentPostId = null;
        this.automationState = {};
        this.alerts = [];
        this.pollingInterval = null;
        this.init();
    }

    // Core methods
    init() { /* Initialize UI and event handlers */ }
    loadNextUp() { /* Load next scheduled week and ideas */ }
    loadPipelineStatus(postId) { /* Load current pipeline state */ }
    loadBlogQueue(filters = {}) { /* Load blog queue with filters */ }
    loadAlerts() { /* Load unread alerts */ }
    
    // Automation control
    startAutomation(postId, ideaId, options) { /* Start automation */ }
    toggleMode(postId, stage, mode) { /* Toggle manual/auto mode */ }
    pauseAutomation(postId) { /* Pause automation */ }
    resumeAutomation(postId) { /* Resume automation */ }
    
    // UI interactions
    changeIdea(ideaId) { /* Change selected idea */ }
    schedulePost(postId, publishTime) { /* Schedule post publication */ }
    dismissAlert(alertId) { /* Dismiss alert */ }
    
    // Real-time updates
    startPolling() { /* Start polling for updates */ }
    stopPolling() { /* Stop polling */ }
    updateProgress() { /* Update progress indicators */ }
    
    // State management
    savePreferences() { /* Save UI preferences to localStorage */ }
    loadPreferences() { /* Load UI preferences from localStorage */ }
}
```

## CSS Design System

### Color Palette
- **Primary**: #8b5cf6 (Purple) - Automation elements
- **Success**: #10b981 (Green) - Completed stages
- **Warning**: #f59e0b (Amber) - In progress/warnings
- **Error**: #ef4444 (Red) - Failed stages/errors
- **Info**: #3b82f6 (Blue) - Information/links
- **Background**: #0f172a (Dark) - Main background
- **Surface**: #1e293b (Dark Gray) - Card backgrounds
- **Border**: #334155 (Gray) - Borders and dividers

### Typography
- **Font Family**: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
- **Headings**: 1.5rem - 2.5rem, font-weight: 600-700
- **Body**: 1rem, font-weight: 400
- **Small**: 0.875rem, font-weight: 500

### Spacing System
- **xs**: 0.25rem (4px)
- **sm**: 0.5rem (8px)
- **md**: 1rem (16px)
- **lg**: 1.5rem (24px)
- **xl**: 2rem (32px)
- **2xl**: 3rem (48px)

### Animation System
- **Duration**: 0.2s - 0.3s for interactions
- **Easing**: ease-out for entrances, ease-in for exits
- **Progress bars**: Smooth transitions with easing
- **Hover effects**: Subtle scale and color transitions

## Error Handling Strategy

### 1. Automation Failures
- **Detection**: Monitor LLM API responses, database errors, timeout conditions
- **Response**: Pause automation, increment error count, create alert
- **Recovery**: Manual intervention required, retry after fixing issue
- **Logging**: Full error context saved to automation_history

### 2. UI Error States
- **Network Errors**: Show retry button, maintain local state
- **Data Loading**: Skeleton loaders, graceful degradation
- **Validation Errors**: Inline error messages, prevent invalid actions
- **Timeout Handling**: Show loading states, retry mechanisms

### 3. Alert System Integration
- **Severity Levels**: info, warning, error, success
- **Auto-expiration**: Remove old alerts automatically
- **Action Integration**: Direct links to relevant pages/actions
- **Persistence**: Alerts persist across sessions until dismissed

## Performance Considerations

### 1. Database Optimization
- **Indexes**: Strategic indexes on frequently queried columns
- **Query Optimization**: Use specific column selection, avoid N+1 queries
- **Connection Pooling**: Efficient database connection management
- **Caching**: Cache frequently accessed data (calendar weeks, settings)

### 2. Frontend Performance
- **Lazy Loading**: Load components and data as needed
- **Debouncing**: Debounce user input and API calls
- **Virtual Scrolling**: For large blog queue lists
- **Image Optimization**: Compress and optimize images
- **Bundle Splitting**: Separate automation-specific code

### 3. Real-time Updates
- **Polling Strategy**: Intelligent polling based on activity
- **WebSocket Integration**: Real-time updates for active automations
- **State Synchronization**: Keep UI state in sync with backend
- **Offline Handling**: Graceful degradation when offline

## Security Considerations

### 1. API Security
- **Authentication**: Session-based authentication for all endpoints
- **Authorization**: Role-based access control for automation features
- **Input Validation**: Validate all input parameters and data
- **Rate Limiting**: Prevent abuse of automation endpoints

### 2. Data Protection
- **Sensitive Data**: Encrypt sensitive automation data
- **Audit Trail**: Complete audit trail of all automation actions
- **Data Retention**: Automatic cleanup of old automation history
- **Backup Strategy**: Regular backups of automation state

## Testing Strategy

### 1. Unit Tests
- **API Endpoints**: Test all automation API endpoints
- **Database Operations**: Test CRUD operations for new tables
- **JavaScript Functions**: Test OneClickBlogManager methods
- **CSS Components**: Test responsive design and animations

### 2. Integration Tests
- **End-to-End Automation**: Test complete automation flow
- **Error Scenarios**: Test error handling and recovery
- **UI Interactions**: Test all user interactions and state changes
- **Performance**: Test under load and with large datasets

### 3. User Acceptance Testing
- **UI/UX Testing**: Validate user experience and workflow
- **Accessibility**: Test keyboard navigation and screen readers
- **Cross-browser**: Test on different browsers and devices
- **Performance**: Test on various network conditions

## Deployment Considerations

### 1. Database Migrations
- **Migration Scripts**: Create and test migration scripts
- **Rollback Strategy**: Plan for rollback if issues occur
- **Data Migration**: Migrate existing data to new schema
- **Index Creation**: Create indexes after data migration

### 2. Configuration Management
- **Environment Variables**: Configure for different environments
- **Feature Flags**: Toggle automation features on/off
- **Monitoring**: Set up monitoring and alerting
- **Logging**: Configure comprehensive logging

### 3. Rollout Strategy
- **Phased Rollout**: Deploy to staging, then production
- **Feature Toggle**: Enable automation features gradually
- **User Training**: Provide documentation and training
- **Support**: Plan for user support and issue resolution

## Future Enhancements

### 1. Advanced Automation
- **Machine Learning**: Learn from user preferences and patterns
- **Smart Scheduling**: Optimize scheduling based on performance data
- **Content Optimization**: A/B test different content approaches
- **Predictive Analytics**: Predict automation success rates

### 2. Integration Expansion
- **Additional Platforms**: Support more social media platforms
- **Content Types**: Support different content types (videos, podcasts)
- **Workflow Customization**: Allow users to customize automation workflows
- **Team Collaboration**: Support multiple users and team workflows

### 3. Analytics and Reporting
- **Performance Metrics**: Track automation performance and success rates
- **Content Analytics**: Analyze content performance and engagement
- **Automation Insights**: Provide insights into automation patterns
- **Custom Reports**: Allow users to create custom reports and dashboards

## Sequential Implementation Approach

**Updated Strategy**: Replace mock data with real data progressively, one panel/stage at a time, maintaining UI-first development while ensuring each step works end-to-end.

### Phase 1A: Sequential Real Data Integration

**Step 1: Next Up Panel (Real Data)**
- **Data Source**: Existing calendar tables (`calendar_schedule`, `calendar_ideas`)
- **Implementation**: 
  - Determine current/next week from calendar system
  - Fetch real ideas for the week
  - Apply selection rules (random + priority + learning stub)
  - Show selected idea + alternatives
  - "Start Production" creates new `post` + `post_development` records
- **Verification**: curl endpoint before UI binding
- **Safety**: Read-only first, write path only after approval

**Step 2: Pipeline Progress - Calendar Stage Only**
- **Data Source**: Existing calendar pages' readiness state
- **Implementation**:
  - Replace mock calendar stage with computed status (view loaded, ideas present)
  - Keep other stages mocked with "mocked" badge
  - Show mixed real/mocked data clearly
- **Verification**: Calendar stage shows real status, others remain mocked

**Step 3: Blog Queue Panel (Real Data)**
- **Data Source**: Existing `post` + `post_development` + schedule state
- **Implementation**:
  - Populate from real database tables
  - Map to statuses (Draft/In Progress/Scheduled/Published)
  - Real filters, sorting, pagination
- **Verification**: All queue operations work with real data

**Step 4: Alerts Header (Hybrid Real/Mock)**
- **Data Source**: Minimal real feed + mocked alerts
- **Implementation**:
  - Real alerts: stuck authoring, missing schedule, ready-to-publish
  - Mocked alerts: non-critical until generating logic exists
  - Clear visual distinction between real and mock alerts
- **Verification**: Real alerts appear in header dropdown

**Step 5: Planning Stage Substages (Real)**
- **Data Source**: Existing planning routes and data presence
- **Implementation**:
  - Calendar → Ideas → Titling → Outline: real stage/substage status
  - "Review" buttons navigate to actual pages
  - Progress based on actual data completion
- **Verification**: Planning stages show real progress

**Step 6: Authoring Stage (Real, Read-Only)**
- **Data Source**: Existing authoring endpoints
- **Implementation**:
  - Surface current substage and progress from real data
  - Display only, no orchestration yet
  - Show actual draft completion status
- **Verification**: Authoring progress reflects real state

**Step 7: Imaging Stage (Defer Real)**
- **Implementation**: Keep mocked until image flows connected
- **Labeling**: Clear "Not Connected" indicators
- **Future**: Connect when image generation pipeline ready

### Phase 1B: UI Development (Completed)
- ✅ Build main One-Click Blog page UI with mock data
- ✅ Add header alert system UI  
- ✅ Create JavaScript state management
- ✅ Add CSS styling and animations
- ✅ Create mock API endpoints
- ✅ Test and refine UI with user

### Phase 2: Backend Integration (After Sequential Real Data)

**2.1 Database Migrations**
- Create automation tables (`automation_state`, `automation_history`, `alert_queue`)
- Schema modifications to existing tables
- Indexes for performance

**2.2 Automation Orchestrator**
- Build core automation engine
- Stage execution methods
- Error handling and retry logic
- Progress tracking and state persistence

**2.3 Stage Automation Modules**
- Individual automation modules for each stage
- Real automation triggers
- WebSocket integration for real-time updates

### Guardrails and Process

**No Schema Changes Without Approval**
- Follow `/docs` requirement: only lookups first
- Write paths wait for explicit go-ahead
- Feature flags per data source

**Verification Process**
- curl each new endpoint before UI binding
- Log and iterate until no errors
- Keep mock responses as fallback if real query fails
- Never break the page

**Rollback Safety**
- Mock responses remain as fallback
- Clear visual indicators for mocked vs real data
- No cross-page side effects during integration

**Dependencies**
- Follow `docs/calendar_system_technical_documentation.md` exactly
- Learning system starts as simple last-N weeks check
- Mixed real/mocked data clearly marked
