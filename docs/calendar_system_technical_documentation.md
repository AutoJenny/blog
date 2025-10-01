# Calendar System Technical Documentation

## Overview

The Calendar System is a comprehensive content planning and scheduling system that enables strategic blog post planning based on seasonal ideas, recurring content, and one-off events. It provides a 52-week calendar structure that integrates with the existing blog post creation workflow.

## System Architecture

### Core Concept
- **52-Week Structure**: Each year is divided into 52 weeks for consistent content planning
- **Perpetual Ideas**: Recurring seasonal content that appears every year
- **One-off Events**: Specific events for particular years
- **Scheduling System**: Links ideas/events to actual blog posts
- **Priority Management**: Random vs. Mandatory content selection

### Database Schema

#### 1. `calendar_weeks` - Master Week Reference
```sql
CREATE TABLE calendar_weeks (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL, -- 1-52
    year INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    month_name VARCHAR(10) NOT NULL, -- Jan, Feb, Mar, etc.
    is_current_week BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(week_number, year)
);
```

**Purpose**: Master reference table defining the 52-week structure for each year.

#### 2. `calendar_ideas` - Perpetual Ideas
```sql
CREATE TABLE calendar_ideas (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL, -- 1-52 (perpetual)
    idea_title VARCHAR(255) NOT NULL,
    idea_description TEXT,
    seasonal_context TEXT, -- "Spring gardening", "Holiday baking", etc.
    content_type VARCHAR(50), -- "tutorial", "guide", "list", "review"
    priority VARCHAR(20) DEFAULT 'random', -- "random" or "mandatory"
    tags JSONB, -- ["gardening", "seasonal", "beginner"]
    is_recurring BOOLEAN DEFAULT TRUE,
    can_span_weeks BOOLEAN DEFAULT FALSE, -- For series
    max_weeks INTEGER DEFAULT 1, -- Maximum weeks for series
    is_evergreen BOOLEAN DEFAULT FALSE,
    evergreen_frequency VARCHAR(20) DEFAULT 'low-frequency',
    last_used_date DATE,
    usage_count INTEGER DEFAULT 0,
    evergreen_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Purpose**: Stores recurring seasonal ideas that appear every year in the same week.

#### 3. `calendar_events` - One-off Events
```sql
CREATE TABLE calendar_events (
    id SERIAL PRIMARY KEY,
    event_title VARCHAR(255) NOT NULL,
    event_description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    week_number INTEGER, -- Calculated from start_date
    year INTEGER NOT NULL,
    content_type VARCHAR(50),
    priority VARCHAR(20) DEFAULT 'random', -- "random" or "mandatory"
    tags JSONB,
    is_recurring BOOLEAN DEFAULT FALSE,
    can_span_weeks BOOLEAN DEFAULT FALSE,
    max_weeks INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Purpose**: Stores specific events for particular years (e.g., "2025 Product Launch").

#### 4. `calendar_schedule` - Actual Scheduling
```sql
CREATE TABLE calendar_schedule (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    idea_id INTEGER REFERENCES calendar_ideas(id) ON DELETE CASCADE,
    event_id INTEGER REFERENCES calendar_events(id) ON DELETE CASCADE,
    post_id INTEGER REFERENCES post(id) ON DELETE SET NULL, -- Links to actual blog post
    status VARCHAR(20) DEFAULT 'planned', -- planned, in_progress, published, cancelled
    scheduled_date DATE,
    notes TEXT,
    is_override BOOLEAN DEFAULT FALSE, -- Override for specific year
    original_idea_id INTEGER REFERENCES calendar_ideas(id), -- If this is an override
    priority VARCHAR(20) DEFAULT 'random', -- "random" or "mandatory"
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CHECK (idea_id IS NOT NULL OR event_id IS NOT NULL) -- Must have one or the other
);
```

**Purpose**: The central scheduling table that links ideas/events to actual blog posts and tracks their status.

#### 5. `calendar_categories` - Content Categories
```sql
CREATE TABLE calendar_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    color VARCHAR(7), -- Hex color code
    icon VARCHAR(50), -- Icon class or name
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Purpose**: Defines content categories with visual styling (colors, icons).

#### 6. Junction Tables
- `calendar_idea_categories` - Many-to-many relationship between ideas and categories
- `calendar_event_categories` - Many-to-many relationship between events and categories

## API Endpoints

### Calendar Management
- `GET /planning/api/calendar/weeks/<year>` - Get all weeks for a year
- `GET /planning/api/calendar/ideas/<week_number>` - Get ideas for a specific week
- `GET /planning/api/calendar/events/<year>/<week_number>` - Get events for a specific week/year
- `GET /planning/api/calendar/schedule/<year>/<week_number>` - Get scheduled items for a week

### CRUD Operations
- `POST /planning/api/calendar/ideas` - Create new idea
- `PUT /planning/api/calendar/ideas/<id>` - Update idea
- `DELETE /planning/api/calendar/ideas/<id>` - Delete idea
- `POST /planning/api/calendar/events` - Create new event
- `PUT /planning/api/calendar/events/<id>` - Update event
- `DELETE /planning/api/calendar/events/<id>` - Delete event
- `POST /planning/api/calendar/schedule` - Schedule an idea/event
- `PUT /planning/api/calendar/schedule/<id>` - Update schedule
- `DELETE /planning/api/calendar/schedule/<id>` - Remove from schedule

### Category Management
- `GET /planning/api/calendar/categories` - Get all categories
- `POST /planning/api/calendar/categories` - Create category
- `PUT /planning/api/calendar/categories/<id>` - Update category
- `DELETE /planning/api/calendar/categories/<id>` - Delete category

## User Interface

### Calendar View (`/planning/posts/<post_id>/calendar/view`)
- **52-week grid layout** with months as columns
- **Visual indicators** for different content types
- **Priority highlighting** (purple for mandatory, plain for random)
- **Category color coding** for easy identification
- **Interactive elements**:
  - Add new entries (+ button)
  - Edit/delete existing items
  - Change categories via dropdown
  - Drag-and-drop for rescheduling
  - Inline editing for titles/descriptions

### Category Management (`/planning/posts/<post_id>/calendar/categories`)
- **CRUD interface** for managing categories
- **Color picker** for category styling
- **Icon selection** for visual identification

## Workflow Integration

### Post Creation Process
1. **Calendar Planning**: Select ideas/events from calendar
2. **Scheduling**: Mark items as "planned" in `calendar_schedule`
3. **Post Creation**: Create blog post and link via `post_id`
4. **Status Tracking**: Update status (planned → in_progress → published)
5. **Completion**: Mark as published and update usage statistics

### Priority System
- **Random**: Content suggestions that can be selected or skipped
- **Mandatory**: Content that must be used (highlighted in purple)
- **Visual Distinction**: Random items have plain backgrounds, mandatory items are purple

### Evergreen Content
- **Tracking**: `is_evergreen`, `evergreen_frequency`, `usage_count`
- **Management**: Automatic suggestions based on usage patterns
- **Flexibility**: Can be overridden for specific years

## Data Flow

### 1. Calendar Initialization
```
Load calendar_weeks for current year
↓
Load calendar_ideas for all weeks
↓
Load calendar_events for current year
↓
Load calendar_schedule for current year
↓
Render 52-week grid with content
```

### 2. Content Selection
```
User selects idea/event from calendar
↓
Create entry in calendar_schedule
↓
Set status to 'planned'
↓
User creates blog post
↓
Link post_id to calendar_schedule
↓
Update status to 'in_progress'
```

### 3. Publishing Workflow
```
Post completed and published
↓
Update calendar_schedule status to 'published'
↓
Update usage_count in calendar_ideas
↓
Update last_used_date
```

## Key Features

### 1. Seasonal Content Management
- **Perpetual Ideas**: Automatically appear every year
- **Seasonal Context**: Rich descriptions for timing relevance
- **Flexible Scheduling**: Can be moved or overridden

### 2. Visual Organization
- **Category Colors**: Easy visual identification
- **Priority Highlighting**: Clear mandatory vs. random distinction
- **Month Grouping**: Logical organization by time periods

### 3. Content Series Support
- **Multi-week Content**: `can_span_weeks` and `max_weeks` fields
- **Series Tracking**: Linked content across multiple weeks
- **Flexible Duration**: Configurable series length

### 4. Override System
- **Year-specific Content**: Override perpetual ideas for specific years
- **Original Tracking**: Maintain reference to original idea
- **Flexible Planning**: Adapt to changing circumstances

## Technical Implementation

### Frontend (JavaScript)
- **Dynamic Loading**: AJAX calls to load calendar data
- **Interactive UI**: Drag-and-drop, inline editing, modals
- **Real-time Updates**: Immediate visual feedback for changes
- **Category Management**: Dynamic color application

### Backend (Python/Flask)
- **RESTful API**: Clean separation of concerns
- **Database Transactions**: Consistent data integrity
- **Error Handling**: Graceful failure management
- **Validation**: Input sanitization and validation

### Database Design
- **Normalized Structure**: Efficient data storage
- **Foreign Key Constraints**: Data integrity
- **Indexes**: Optimized query performance
- **JSONB Fields**: Flexible tag storage

## Future Enhancements

### Planned Features
1. **Content Analytics**: Usage statistics and performance tracking
2. **AI Suggestions**: Machine learning for content recommendations
3. **Social Media Integration**: Cross-platform content planning
4. **Team Collaboration**: Multi-user planning capabilities
5. **Content Templates**: Reusable content structures

### Scalability Considerations
- **Multi-year Support**: Automatic year generation
- **Performance Optimization**: Caching and query optimization
- **Mobile Responsiveness**: Touch-friendly interface
- **API Rate Limiting**: Protection against abuse

## Maintenance

### Regular Tasks
- **Week Generation**: Create calendar_weeks for new years
- **Data Cleanup**: Remove old, unused entries
- **Performance Monitoring**: Query optimization
- **Backup Management**: Regular database backups

### Troubleshooting
- **Common Issues**: Missing weeks, incorrect dates, display problems
- **Debug Tools**: Console logging, error tracking
- **Recovery Procedures**: Data restoration and repair

## Security Considerations

### Data Protection
- **Input Validation**: Prevent SQL injection and XSS
- **Access Control**: User authentication and authorization
- **Data Sanitization**: Clean user inputs
- **Audit Logging**: Track changes and access

### Privacy
- **Data Minimization**: Store only necessary information
- **Retention Policies**: Automatic cleanup of old data
- **User Consent**: Clear data usage policies

---

*This documentation is maintained as part of the blog system and should be updated as the calendar system evolves.*



