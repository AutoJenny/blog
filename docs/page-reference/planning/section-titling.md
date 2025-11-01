# Section Titling Page - Technical Documentation

## Overview

The Section Titling page (`/planning/posts/<id>/concept/titling`) is the final stage in the concept development workflow. It takes the section ideas from the previous stage and generates imaginative, engaging titles and descriptions for each section based on their topics and the context of the whole post.

## Purpose and Scope

- **Primary Function**: Generate creative, engaging section titles and descriptions
- **Input Data**: Section ideas from `post_development.topic_allocation` and `expanded_idea`
- **Output Data**: Final section structure stored in `post_section` table and `post_development.sections`
- **Workflow Position**: Final step in concept development (after section ideas, before authoring)

## Technical Architecture

### Flask Route
```python
@bp.route('/posts/<int:post_id>/concept/titling')
def planning_concept_titling(post_id):
    """Titling page"""
    return titling_func(post_id)
```

**File**: `blueprints/planning_concept.py:27-30`
- Renders template with post_id and blueprint_name
- Simple pass-through to template rendering

### Template Structure
**File**: `templates/planning/concept/titling.html`

**Key Components**:
- **Input Data Panel**: Displays topic allocation from previous stage
- **Generation Controls**: Button to create titles and descriptions
- **Results Panel**: Shows generated sections with final titles
- **LLM Module**: Handles title generation via AI

### Database Operations

#### Input Data Sources
1. **Topic Allocation** (`post_development.topic_allocation`):
   ```sql
   SELECT topic_allocation FROM post_development WHERE post_id = %s
   ```

2. **Expanded Idea** (`post_development.expanded_idea`):
   ```sql
   SELECT expanded_idea FROM post_development WHERE post_id = %s
   ```

3. **Existing Sections** (`post_section` table):
   ```sql
   SELECT id, title, section_heading, section_order
   FROM post_section WHERE post_id = %s ORDER BY section_order
   ```

#### Output Data Storage
1. **Section Titles** (stored in `post_section` table):
   ```sql
   INSERT INTO post_section (post_id, section_heading, section_order, created_at, updated_at)
   VALUES (%s, %s, %s, %s, %s)
   ON CONFLICT (post_id, section_order) 
   DO UPDATE SET section_heading = %s, updated_at = %s
   ```

2. **Sections Data** (stored in `post_development.sections`):
   ```sql
   UPDATE post_development 
   SET sections = %s, updated_at = %s
   WHERE post_id = %s
   ```

### API Endpoints

#### 1. Generate Section Titles
```http
POST /planning/api/sections/title
```
**Purpose**: Generate creative titles and descriptions for sections
**Body**: `{topic_allocation: array, expanded_idea: string, post_id: number}`
**Response**: `{success: bool, sections: array}`

#### 2. Save Sections
```http
POST /planning/api/sections/save
```
**Purpose**: Save generated sections to database
**Body**: `{post_id: number, sections: array}`
**Response**: `{success: bool}`

#### 3. Get Topic Allocation
```http
GET /planning/api/sections/allocate-topics/{post_id}
```
**Purpose**: Fetch topic allocation for title generation
**Response**: `{success: bool, allocations: object}`

#### 4. Get Expanded Idea
```http
GET /planning/api/posts/{post_id}/expanded-idea
```
**Purpose**: Fetch expanded idea for context
**Response**: `{success: bool, expanded_idea: string}`

### JavaScript Modules

#### Core Functionality (`titling.html` lines 308-682)
- **`loadExistingSections()`**: Loads previously generated sections
- **`loadTopicAllocation()`**: Fetches topic allocation from previous stage
- **`startTitling()`**: Initiates title generation process
- **`displaySections(sectionsData)`**: Renders generated sections
- **`saveSectionsToDatabase(sectionsData)`**: Persists sections to database

#### Section Management
- **`displayTopicAllocation(allocations)`**: Shows input topic allocation
- **`getExpandedIdea()`**: Fetches expanded idea for context
- **`escapeHtml(text)`**: Sanitizes HTML content
- **Error Handling**: Comprehensive error management with retry logic

#### LLM Integration
- Uses shared LLM module (`initializeLLMModule('titling', postId)`)
- Custom generation logic for section titles
- Handles loading states and error display
- Implements retry mechanism for failed generations

### Data Flow

#### 1. Page Load
```
User visits /planning/posts/69/concept/titling
↓
Load existing sections from post_section table
↓
Load topic allocation from topic_allocation field
↓
Display topic allocation in input panel
↓
Show existing sections (if any)
```

#### 2. Title Generation
```
User clicks "Create Titles & Descriptions"
↓
Fetch expanded_idea for context
↓
Send topic_allocation + expanded_idea to /planning/api/sections/title
↓
LLM generates creative titles and descriptions
↓
Display sections with final titles
↓
Auto-save sections to post_section table
```

#### 3. Section Display
```
Parse generated sections data
↓
Render sections with titles, subtitles, topics
↓
Show section metadata (order, topic count)
↓
Handle both array and object formats
```

### UI Components

#### Input Data Panel
- **Topic Allocation Display**: Shows topic allocation from previous stage
- **Section Organization**: Topics grouped by section theme
- **Visual Hierarchy**: Clear organization and readability
- **Validation**: Ensures topic allocation exists before generation

#### Generation Controls
- **Single Action Button**: "Create Titles & Descriptions"
- **Loading States**: Visual feedback during generation
- **Retry Logic**: Automatic retry for failed generations
- **Error Handling**: Clear error messages and recovery options

#### Results Panel
- **Section List**: Generated sections with final titles
- **Section Metadata**: Order, topic count, and organization
- **Rich Display**: Titles, subtitles, and associated topics
- **Visual Design**: Clean, professional section presentation

#### Section Items
- **Section Title**: Creative, engaging final title
- **Section Subtitle**: Descriptive subtitle or tagline
- **Section Order**: Numerical order in the post
- **Topic Count**: Number of topics in each section
- **Associated Topics**: Topics that belong to each section

### Error Handling

#### Client-Side Errors
- **Missing Topic Allocation**: Prevents generation without input
- **API Failures**: Displays error messages with retry options
- **Retry Logic**: Automatic retry for LLM failures
- **Data Format Issues**: Handles various section format variations

#### Server-Side Errors
- **LLM Failures**: Graceful handling of AI generation errors
- **Database Issues**: Error logging and user notification
- **Data Validation**: Ensures required fields are present
  - **Section Count Validation**: Ensures LLM generates exactly the number of sections requested
  - **Missing Section Detection**: Raises error if any section is missing a title
  - **Index Matching**: Validates that all sections have matching indices
- **Retry Mechanism**: Built-in retry for transient failures

### Recent Improvements (November 2025)

- **Enhanced LLM Prompting**: Prompt now explicitly lists all sections with themes and topics, making it clear that ALL sections need titles
- **Mandatory Section Generation**: Added validation to ensure LLM generates exactly `len(topic_allocation)` titles - returns error if fewer sections are generated
- **Fixed Section Matching**: Corrected bug in section matching logic that was overwriting outer loop variable
- **Direct post_section Writes**: Save function now writes directly to `post_section` table in addition to `post_development.sections`, ensuring all sections are persisted even if database triggers fail

### Integration Points

#### With Topic Allocation Stage
- **Data Dependency**: Requires topic allocation from previous stage
- **Format Compatibility**: Handles allocation format
- **Validation**: Checks for required allocation data

#### With Authoring Stage
- **Data Handoff**: Provides final section structure for authoring
- **Format Compatibility**: Ensures section format matches expectations
- **Section Persistence**: Maintains section data in post_section table

### Performance Considerations

#### Database Queries
- **Efficient Loading**: Single queries for allocation and existing sections
- **JSON Handling**: Proper parsing of topic_allocation
- **Batch Operations**: Efficient section creation and updates
- **Transaction Safety**: Atomic operations for data consistency

#### Client-Side Optimization
- **Lazy Rendering**: Sections rendered on demand
- **State Management**: Efficient DOM updates
- **Memory Management**: Proper cleanup of event listeners
- **Retry Optimization**: Efficient retry mechanisms

### Security Considerations

#### Input Validation
- **Post ID Validation**: Ensures valid post references
- **Content Sanitization**: Prevents XSS in section content
- **JSON Safety**: Validates JSON structure before storage

#### Data Integrity
- **Foreign Key Constraints**: Maintains referential integrity
- **Transaction Safety**: Atomic operations for data updates
- **Backup Strategy**: Preserves existing data during updates
- **Conflict Resolution**: Handles section order conflicts

### Configuration Options

#### Generation Parameters
- **Topic Context**: Uses topic allocation for context
- **Post Context**: Incorporates expanded idea
- **Title Style**: Configurable title generation style
- **Description Length**: Adjustable description detail level

#### LLM Settings
- **Provider Selection**: Configurable AI provider
- **Model Parameters**: Adjustable generation settings
- **Prompt Templates**: Customizable title generation prompts
- **Response Parsing**: Configurable section extraction

### Monitoring and Analytics

#### Usage Tracking
- **Generation Patterns**: Track title generation success rates
- **Retry Patterns**: Monitor retry frequency and success
- **User Engagement**: Track interaction patterns
- **Section Quality**: Monitor generated section quality

#### Performance Metrics
- **Generation Time**: Monitor LLM response times
- **Retry Success**: Track retry success rates
- **User Engagement**: Track interaction patterns
- **Error Rates**: Monitor failure patterns

### Data Structure

#### Section Format
```json
{
  "sections": [
    {
      "id": 1,
      "title": "Creative Section Title",
      "subtitle": "Engaging subtitle or description",
      "order": 1,
      "topics": [
        "Topic 1 for this section",
        "Topic 2 for this section"
      ]
    }
  ],
  "metadata": {
    "total_sections": 5,
    "generated_at": "2025-01-01T00:00:00Z"
  }
}
```

#### Database Storage Format
```sql
-- post_section table
INSERT INTO post_section (post_id, section_heading, section_order, created_at, updated_at)
VALUES (69, 'Creative Section Title', 1, NOW(), NOW());

-- post_development.sections (JSON)
UPDATE post_development 
SET sections = '{"sections": [...], "metadata": {...}}'
WHERE post_id = 69;
```

### Future Enhancements

#### Potential Improvements
- **Title Refinement**: Allow editing of generated titles
- **Title Variations**: Generate multiple title options
- **Advanced Customization**: More granular title control
- **Title Validation**: Automatic title quality checks

#### Technical Debt
- **Error Handling**: Standardize error response formats
- **Testing Coverage**: Add comprehensive test suite
- **Performance Optimization**: Improve rendering performance
- **Code Consolidation**: Reduce duplication in section handling

### Troubleshooting

#### Common Issues
- **Missing Topic Allocation**: Guide users to previous stage
- **Generation Failures**: Provide retry mechanisms
- **Retry Exhaustion**: Handle multiple retry failures
- **Data Persistence**: Ensure sections are saved properly

#### Debug Information
- **Console Logging**: Detailed error information
- **API Responses**: Full response data for debugging
- **State Tracking**: Monitor application state changes
- **Performance Metrics**: Track timing and resource usage

### Migration Notes

#### Legacy Support
- **Format Compatibility**: Handles various section formats
- **Data Migration**: Gradual transition to standardized format
- **Error Recovery**: Graceful handling of format mismatches
- **Backward Compatibility**: Maintains existing functionality

#### Section Synchronization
- **Dual Storage**: Maintains both post_section and post_development.sections
- **Sync Strategy**: Ensures consistency between storage locations
- **Conflict Resolution**: Handles section order conflicts
- **Data Integrity**: Maintains referential integrity
