# Calendar Ideas Page - Technical Documentation

## Overview

The Calendar Ideas page (`/planning/posts/<id>/calendar/ideas`) serves as the initial idea generation stage in the planning workflow. It allows users to select from pre-generated calendar ideas for a specific week and create or reuse blog posts based on those ideas.

## Purpose and Scope

- **Primary Function**: Select and confirm calendar ideas to create blog post foundations
- **Data Source**: `calendar_ideas` table filtered by week number
- **Output**: Creates or updates `post` records with `idea_seed` and `expanded_idea` fields
- **Workflow Position**: First step in concept development (now part of concept workflow)

## Technical Architecture

### Flask Route
```python
@bp.route('/posts/<int:post_id>/calendar/ideas')
def planning_calendar_ideas(post_id):
    """Calendar ideas page"""
    return ideas_func(post_id)
```

**File**: `blueprints/planning_calendar_clean.py:26-65`
- Fetches week number from `calendar_schedule` table
- Falls back to current week if no schedule found
- Renders template with post_id, year, week_number, and mode='post-based'

### Template Structure
**File**: `templates/planning/calendar/ideas.html`

**Key Components**:
- **Available Ideas Panel**: Lists ideas from `calendar_ideas` table
- **Selected Idea Panel**: Shows currently selected idea with confirmation
- **Current Idea Seed Display**: Shows the confirmed idea seed
- **LLM Module**: For generating expanded ideas

### Database Operations

#### Input Data Sources
1. **Calendar Schedule** (`calendar_schedule` table):
   ```sql
   SELECT cs.year, cs.week_number, cs.scheduled_date
   FROM calendar_schedule cs
   WHERE cs.post_id = %s
   ORDER BY cs.created_at DESC LIMIT 1
   ```

2. **Calendar Ideas** (`calendar_ideas` table):
   ```sql
   SELECT id, idea_title, idea_description, seasonal_context, 
          content_type, priority, tags, is_recurring
   FROM calendar_ideas 
   WHERE week_number = %s
   ORDER BY CASE priority 
       WHEN 'mandatory' THEN 1 
       WHEN 'random' THEN 2 
       ELSE 3 END, id
   ```

#### Output Data Storage
1. **Post Creation/Update**:
   - Creates new posts via `/planning/api/posts/create-new`
   - Updates `idea_seed` via `/planning/api/posts/<id>/idea-seed`
   - Generates `expanded_idea` via `/planning/api/posts/<id>/expanded-idea`

### API Endpoints

#### 1. Get Ideas for Week
```http
GET /planning/api/calendar/ideas/week/{week_number}
```
**Purpose**: Fetch available ideas for a specific week
**Response**: Array of idea objects with title, description, context, type, priority

#### 2. Check Topic Usage
```http
POST /planning/api/posts/check-topic
```
**Purpose**: Check if a topic has already been used this year
**Body**: `{topic: string, year: number}`
**Response**: `{success: bool, existing_post_id?: number}`

#### 3. Create New Post
```http
POST /planning/api/posts/create-new
```
**Purpose**: Create a new blog post for a topic
**Body**: `{topic: string, week_number: number}`
**Response**: `{success: bool, post_id: number}`

#### 4. Set Idea Seed
```http
POST /planning/api/posts/{post_id}/idea-seed
```
**Purpose**: Set the core idea seed for a post
**Body**: `{idea_seed: string}`
**Response**: `{success: bool, idea_seed: string}`

#### 5. Generate Expanded Idea
```http
POST /planning/api/posts/{post_id}/expanded-idea
```
**Purpose**: Generate expanded idea from seed
**Body**: `{idea_seed: string}`
**Response**: `{success: bool, expanded_idea: string}`

### JavaScript Modules

#### Core Functionality (`ideas.html` lines 368-735)
- **`loadIdeasForWeek()`**: Fetches and displays available ideas
- **`selectIdea(index)`**: Handles idea selection
- **`confirmSelection()`**: Processes idea confirmation and post creation
- **`generateExpandedIdea()`**: Triggers expanded idea generation
- **`autoSelectIdea()`**: Auto-selects mandatory or random ideas

#### LLM Integration
- Uses shared LLM module (`initializeLLMModule('ideas', postId)`)
- Overrides `generateContent()` method for expanded idea generation
- Handles loading states and error display

### Data Flow

#### 1. Page Load
```
User visits /planning/posts/69/calendar/ideas
↓
Fetch week number from calendar_schedule
↓
Load available ideas for that week
↓
Auto-select mandatory/random idea
↓
Display current idea seed (if exists)
```

#### 2. Idea Selection
```
User clicks "Select" on an idea
↓
Update selected idea display
↓
Enable "Confirm & Generate" button
```

#### 3. Idea Confirmation
```
User clicks "Confirm & Generate"
↓
Check if topic already exists this year
↓
Create new post OR reuse existing post
↓
Set idea_seed in post_development
↓
Generate expanded_idea via LLM
↓
Redirect to brainstorm page (if new post)
```

### UI Components

#### Available Ideas List
- **Priority-based ordering**: Mandatory → Random → Custom
- **Visual indicators**: Color-coded priority badges
- **Interactive selection**: Click to select, visual feedback
- **Auto-selection**: Automatically selects mandatory ideas

#### Selected Idea Display
- **Comprehensive view**: Title, description, context, type
- **Confirmation action**: Single button to proceed
- **Validation**: Ensures idea is selected before confirmation

#### Idea Seed Display
- **Current state**: Shows confirmed idea seed
- **Generation trigger**: Button to generate expanded idea
- **LLM integration**: Uses shared LLM module for generation

### Error Handling

#### Client-Side Errors
- **No ideas available**: Shows "No ideas available for this week"
- **Selection validation**: Prevents confirmation without selection
- **API failures**: Displays error messages with retry options

#### Server-Side Errors
- **Database connection**: Graceful fallback to current week
- **Missing data**: Clear error messages for missing requirements
- **LLM failures**: Error logging and user notification

### Integration Points

#### With Planning Workflow
- **Next Step**: Redirects to `/planning/posts/{post_id}/concept/brainstorm`
- **Data Handoff**: Provides `idea_seed` and `expanded_idea` for brainstorming
- **Post Creation**: Creates foundation for entire planning process

#### With Calendar System
- **Week-based**: Operates within weekly calendar context
- **Schedule Integration**: Uses `calendar_schedule` for timing
- **Idea Management**: Leverages `calendar_ideas` for content

### Performance Considerations

#### Database Queries
- **Efficient filtering**: Uses indexed week_number for fast lookups
- **Minimal data**: Only fetches necessary fields
- **Caching potential**: Ideas could be cached by week

#### Client-Side Optimization
- **Lazy loading**: Ideas loaded on demand
- **State management**: Efficient DOM updates
- **Error recovery**: Graceful handling of network issues

### Security Considerations

#### Input Validation
- **Post ID validation**: Ensures valid post references
- **Topic sanitization**: Prevents injection attacks
- **Week number bounds**: Validates week ranges

#### Data Integrity
- **Foreign key constraints**: Maintains referential integrity
- **Transaction safety**: Atomic operations for post creation
- **Duplicate prevention**: Checks for existing topics

### Configuration Options

#### Idea Priority System
- **Mandatory**: High-priority, auto-selected ideas
- **Random**: Medium-priority, randomly selected
- **Custom**: User-defined ideas

#### LLM Settings
- **Provider selection**: Configurable LLM provider
- **Model parameters**: Adjustable generation settings
- **Prompt templates**: Customizable prompt structure

### Monitoring and Analytics

#### Usage Tracking
- **Idea selection patterns**: Track popular idea types
- **Generation success rates**: Monitor LLM performance
- **User flow analysis**: Understand navigation patterns

#### Performance Metrics
- **Page load times**: Monitor template rendering
- **API response times**: Track endpoint performance
- **Error rates**: Monitor failure patterns

### Automation Integration

**Current State**: Manual idea selection and confirmation

**Future State**: Automated post creation 1 week in advance

**Automation Flow**:
1. Background monitor runs `automated_blog_post_creator.py`
2. Script resolves themes for upcoming weeks
3. Creates posts automatically with `status='draft'`
4. Sets `idea_seed` from theme title
5. Schedules in `calendar_week_items`

**See**: `docs/BLOG_POST_AUTOMATION_GOALS.md` for detailed automation plan

### Future Enhancements

#### Potential Improvements
- **Bulk idea processing**: Handle multiple ideas simultaneously
- **Advanced filtering**: More sophisticated idea selection
- **Integration expansion**: Connect with external idea sources
- **Analytics dashboard**: Visualize idea usage patterns
- **Automated creation**: Posts created 1 week in advance automatically

#### Technical Debt
- **Code consolidation**: Reduce duplication in API calls
- **Error handling**: Standardize error response formats
- **Testing coverage**: Add comprehensive test suite
- **Documentation**: Expand inline code documentation
