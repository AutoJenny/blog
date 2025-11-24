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

#### 4. `calendar_schedule` - Actual Scheduling (Deprecated)
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

**Status**: ⚠️ **Deprecated** - This table is still used for backwards compatibility but is being phased out in favor of the Week Persistence V2 architecture (`calendar_week_selection` and `calendar_week_posts`). New implementations should use the V2 tables.

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

#### 6. `calendar_themes` - Perpetual Themes
```sql
CREATE TABLE calendar_themes (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL, -- 1-52 (perpetual)
    theme_title VARCHAR(255) NOT NULL,
    theme_description TEXT,
    seasonal_context TEXT,
    priority VARCHAR(20) DEFAULT 'random' CHECK (priority IN ('random', 'mandatory')),
    tags JSONB,
    is_recurring BOOLEAN DEFAULT TRUE,
    can_span_weeks BOOLEAN DEFAULT FALSE,
    max_weeks INTEGER DEFAULT 1,
    is_evergreen BOOLEAN DEFAULT FALSE,
    evergreen_frequency VARCHAR(20) DEFAULT 'low-frequency',
    last_used_date DATE,
    usage_count INTEGER DEFAULT 0,
    evergreen_notes TEXT,
    sources JSONB DEFAULT '[]'::jsonb,
    important_notes JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Purpose**: Stores week-wide themes (concepts) that are completely separate from calendar_ideas. Themes are perpetual and appear every year in the same week.

**Note**: Themes are distinct from ideas - themes represent week-wide concepts, while ideas represent specific content suggestions.

#### 7. `calendar_week_selection` - Week Persistence V2 (Theme Selection)
```sql
CREATE TABLE calendar_week_selection (
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    selected_theme_id INTEGER NOT NULL REFERENCES calendar_themes(id) ON DELETE RESTRICT,
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (year, week_number),
    UNIQUE(year, week_number)
);
```

**Purpose**: Stores the selected theme for each week. One theme must be selected per week (enforced by PRIMARY KEY). This is part of the Week Persistence V2 architecture.

**Key Constraints**:
- PRIMARY KEY on `(year, week_number)` ensures only one selection per week
- `selected_theme_id` is NOT NULL - theme selection is required
- ON DELETE RESTRICT prevents deleting a theme that's selected

**Related Documentation**: See `docs/WEEK_PERSISTENCE_V2_SYSTEM.md` for complete architecture details.

#### 8. `calendar_week_posts` - Week Persistence V2 (Post Assignments)
```sql
CREATE TABLE calendar_week_posts (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    post_id INTEGER NOT NULL REFERENCES post(id) ON DELETE CASCADE,
    scheduled_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(year, week_number, post_id)
);
```

**Purpose**: Stores post assignments to weeks. Multiple posts can be assigned to the same week. This is part of the Week Persistence V2 architecture.

**Key Constraints**:
- UNIQUE on `(year, week_number, post_id)` prevents duplicate assignments
- Foreign key to `post` with CASCADE delete

**Related Documentation**: See `docs/WEEK_PERSISTENCE_V2_SYSTEM.md` for complete architecture details.

#### 9. Junction Tables
- `calendar_idea_categories` - Many-to-many relationship between ideas and categories
- `calendar_event_categories` - Many-to-many relationship between events and categories

**Note on `calendar_schedule`**: The `calendar_schedule` table is still used for backwards compatibility but is being phased out in favor of the Week Persistence V2 architecture (`calendar_week_selection` and `calendar_week_posts`).

## API Endpoints

### Calendar Management
- `GET /planning/api/calendar/weeks/<year>` - Get all weeks for a year
- `GET /planning/api/calendar/ideas/week/<week_number>` - Get ideas for a specific week (week-only, no year)
- `GET /planning/api/calendar/themes/week/<week_number>` - Get themes for a specific week (week-only, no year)
- `GET /planning/api/calendar/events/<year>/<week_number>` - Get events for a specific week/year
- `GET /planning/api/calendar/schedule/<year>/<week_number>` - Get scheduled items for a week

### Week View Endpoints
The week view (`/planning/posts/<post_id>/calendar/week-view`) uses the following additional endpoints:
- `GET /planning/api/calendar/profiles/<year>/<week_number>` - Get product/profile posts for a week
- `GET /planning/api/calendar/recipes/<year>/<week_number>` - Get recipe posts for a week
- `GET /planning/api/calendar/content-generator/<year>/<week_number>` - Get content generator posts for a week
- `GET /launchpad/api/syndication/schedules?platform=facebook&content_type=product` - Get product syndication schedules
- `GET /launchpad/api/syndication/schedules?platform=facebook&content_type=blog_post` - Get blog post syndication schedules
- `GET /planning/api/social-focus/week` - Get weekly social focus data

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

### Calendar Week View (`/planning/posts/<post_id>/calendar/week-view?year=YYYY&week=W`)
The week view provides a detailed, day-by-day view of a single week. **Week context is required** via URL query parameters (`year` and `week`).

#### Route Handler Behavior
**File**: `blueprints/planning_calendar_clean.py:104-168`

**Key Features**:
1. **Week Context Required**: Reads `year` and `week` from URL query parameters
2. **Post Resolution**: Uses `resolve_post_for_week()` to resolve the correct post for themed posts
3. **Post Type Handling**: 
   - **Recipe/Profile posts**: Preserves original `post_id` to maintain recipe/profile association
   - **Themed posts**: Resolves to week-specific post if available
4. **Template**: Renders `planning/calendar/week_view.html`

#### Week Navigation Controls
- **Previous/Next Week Buttons**: Navigate between weeks
- **"This Week" Button**: Jump to current week
- **Week Picker Popup**: Month/year selector for quick navigation
- **Week Display**: Shows year, week number, and date range (Mon-Sun)

#### Content Type Filters
The week view includes 8 filter toggles to show/hide different content types:
- **Themes**: Week-wide themes (full-width row above day headers)
- **Annual Events**: Recurring annual events (7-day grid row)
- **Special Events**: One-off special events (7-day grid row)
- **Ideas**: Content ideas (7-day grid row)
- **Syndication**: Social media scheduled posts (7-day grid row)
- **Profiles**: Product/profile posts (7-day grid row)
- **Content Generator**: AI-generated posts (7-day grid row)
- **Recipes**: Recipe posts (7-day grid row)

#### Content Rows
Each content type (except themes) is displayed in a horizontal row aligned with the 7-day grid:
- **Row Header**: Content type name with "Add New" button
- **7-Day Grid**: One cell per day (Mon-Sun)
- **Items**: Content items placed in appropriate day cells based on scheduled dates

#### Themes Row
Themes are displayed in a full-width row above the day headers:
- Shows all available themes for the week
- Selected theme is highlighted
- Click to edit theme details
- "Add New" button to create new themes

#### Day Headers
Each day column includes:
- **Day Name**: Mon, Tue, Wed, etc.
- **Calendar Day Number**: Actual date number
- **Social Focus Indicator**: Clickable indicator showing daily social media focus

#### Advance Notice System
Events can span multiple weeks with advance notice:
- **Visual Indicators**: Events starting in future weeks show advance notice
- **Arrow Indicators**: Show event progression across days
- **Clickable**: Click to view/edit event details

#### Modal Interactions
The week view includes several modals:
- **Idea Modal**: For creating/editing themes, ideas, and events
- **Profile Modal**: For creating/editing product profiles
- **Content Generator Modal**: For generating new posts
- **Social Focus Modal**: For setting daily social media focus

#### JavaScript Implementation
**File**: `static/js/planning/calendar-week-view.js`

The week view loads data from **9 different API endpoints** in parallel:
1. Ideas (week-only, no year)
2. Events (year + week)
3. Schedule (year + week)
4. Product syndication schedules
5. Blog post syndication schedules
6. Social focus (week-only)
7. Profiles (year + week)
8. Recipes (year + week)
9. Content generator posts (year + week)

**Week Context Management**: Uses `WeekContext` module to maintain year/week in URL and update navigation links automatically.

### Category Management (`/planning/posts/<post_id>/calendar/categories`)
- **CRUD interface** for managing categories
- **Color picker** for category styling
- **Icon selection** for visual identification

## Workflow Integration

### Post Creation Process
1. **Calendar Planning**: Select ideas/events from calendar
2. **Theme Selection**: Select theme for week (stored in `calendar_week_selection`)
3. **Scheduling**: Assign posts to weeks (stored in `calendar_week_posts` or `calendar_schedule` for backwards compatibility)
4. **Post Creation**: Create blog post and link via `post_id`
5. **Status Tracking**: Update status (planned → in_progress → published)
6. **Completion**: Mark as published and update usage statistics

### Week Context and Post Resolution

#### Week Context Requirement
The week view requires week context via URL query parameters:
- **URL Format**: `/planning/posts/<post_id>/calendar/week-view?year=YYYY&week=W`
- **Parameters**: 
  - `year`: Year (e.g., 2025)
  - `week`: Week number (1-52)

#### Post Resolution Logic
**File**: `utils/week_post_resolver.py`

The system uses `resolve_post_for_week(year, week)` to resolve the correct post for a given week:

1. **For Themed Posts**: 
   - Queries `calendar_week_posts` to find posts assigned to the week
   - Returns the most recently created post for that week
   - Falls back to original `post_id` if no week-specific post found

2. **For Recipe/Profile Posts**:
   - **Preserves original `post_id`** to maintain recipe/profile association
   - Does not resolve to week-specific posts
   - Recipe posts are tied to `recipe_week_number` field
   - Profile posts maintain their original post association

3. **Week Persistence V2**:
   - Uses `calendar_week_selection` for theme selection (one per week)
   - Uses `calendar_week_posts` for post assignments (multiple allowed)
   - See `docs/WEEK_PERSISTENCE_V2_SYSTEM.md` for complete details

#### Navigation with Week Context
- **Week Context Persistence**: Once set in URL, week context persists across navigation
- **Automatic Link Updates**: Navigation links automatically include `?year=X&week=Y` parameters
- **WeekContext Module**: JavaScript module manages week context in URL and updates links

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

## Related Documentation

### Week Persistence V2
- **`docs/WEEK_PERSISTENCE_V2_SYSTEM.md`**: Complete architecture documentation
- **`docs/WEEK_PERSISTENCE_V2_API_REFERENCE.md`**: API endpoint reference
- **`docs/WEEK_PERSISTENCE_V2_QUICK_REFERENCE.md`**: Quick reference guide

### Content Types
- **Product Profiles**: See `docs/data_intelligence/products/PRODUCT_CATEGORY_PROFILES_DOCUMENTATION.md`
- **Recipes**: See recipe-related documentation
- **Content Generator**: See content generation documentation

### Calendar Week View
- **`docs/CALENDAR_WEEK_VIEW_DOCUMENTATION_REVIEW.md`**: Detailed review of week-view implementation vs. documentation

## Future Enhancements

### Planned Features
1. **Content Analytics**: Usage statistics and performance tracking
2. **AI Suggestions**: Machine learning for content recommendations
3. **Social Media Integration**: Cross-platform content planning (partially implemented via syndication)
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



