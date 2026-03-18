# Section Structure Design Page - Technical Documentation

## Overview

The Section Structure Design page (`/planning/posts/<id>/concept/section-structure`) is the third stage in the planning workflow. It takes the generated topics from brainstorming and creates a logical structure for organizing them into blog post sections with provisional technical titles.

## Purpose and Scope

- **Primary Function**: Design logical section structure based on generated topics
- **Input Data**: Topics from `idea_scope.generated_topics` and `expanded_idea` from previous stages
- **Output Data**: Section structure stored in `post_development.section_structure` JSON field
- **Workflow Position**: Third step in concept development (after brainstorming, before section ideas)

## Technical Architecture

### Flask Route
```python
@bp.route('/posts/<int:post_id>/concept/section-structure')
def planning_concept_section_structure(post_id):
    """Section structure page"""
    return section_structure_func(post_id)
```

**File**: `blueprints/planning_concept.py:17-20`
- Renders template with post_id and blueprint_name
- Simple pass-through to template rendering

### Template Structure
**File**: `templates/planning/concept/section_structure.html`

**Key Components**:
- **Input Data Panel**: Displays topics from brainstorming stage
- **Structure Settings**: Configurable structure generation parameters
- **Results Panel**: Shows generated section structure
- **LLM Module**: Handles structure generation via AI

### Database Operations

#### Input Data Sources
1. **Generated Topics** (`post_development.idea_scope`):
   ```sql
   SELECT idea_scope FROM post_development WHERE post_id = %s
   ```

2. **Expanded Idea** (`post_development.expanded_idea`):
   ```sql
   SELECT expanded_idea FROM post_development WHERE post_id = %s
   ```

#### Output Data Storage
1. **Section Structure** (stored in `post_development.section_structure`):
   ```sql
   UPDATE post_development 
   SET section_structure = %s, structure_design_at = %s, updated_at = %s
   WHERE post_id = %s
   ```

### API Endpoints

#### 1. Design Section Structure
```http
POST /planning/api/sections/design-structure
```
**Purpose**: Generate section structure based on topics and expanded idea
**Body**: `{topics: array, post_id: number, expanded_idea: string}`
**Response**: `{success: bool, section_structure: array, raw_response: string}`

**Structure Types**:
- `chronological`: Time-based organization
- `thematic`: Topic-based grouping
- `progressive`: Building complexity approach
- `comparative`: Contrasting views structure

#### 2. Get Section Structure
```http
GET /planning/api/sections/design-structure/{post_id}
```
**Purpose**: Retrieve existing section structure
**Response**: `{success: bool, section_structure: array}`

#### 3. Get Post Data
```http
GET /planning/api/posts/{post_id}
```
**Purpose**: Fetch post data including topics and expanded idea
**Response**: `{success: bool, post: object}`

### JavaScript Modules

#### Core Functionality (`section_structure.html` lines 329-528)
- **`loadBrainstormTopics()`**: Fetches and displays topics from brainstorming
- **`loadExistingStructure()`**: Loads previously generated structure
- **`generateSectionStructure()`**: Initiates structure generation process
- **`displaySectionStructure(structure)`**: Renders generated structure
- **`displayTopics()`**: Shows input topics in organized format

#### Structure Management
- **`displayRawResponse(rawResponse)`**: Shows LLM raw response
- **`escapeHtml(text)`**: Sanitizes HTML content
- **Error Handling**: Comprehensive error management

#### LLM Integration
- Uses shared LLM module (`initializeLLMModule('section_structure', postId)`)
- Custom generation logic for structure design
- Handles loading states and error display

### Data Flow

#### 1. Page Load
```
User visits /planning/posts/69/concept/section-structure
↓
Load topics from idea_scope.generated_topics
↓
Load expanded_idea from post_development
↓
Display topics in input panel
↓
Load existing structure (if any)
```

#### 2. Structure Generation
```
User selects structure type (chronological/thematic/progressive/comparative)
↓
User clicks "Design Section Structure"
↓
Send topics + expanded_idea + structure_type to API
↓
LLM generates section structure with codes, titles, descriptions
↓
Display structure in results panel
↓
Save structure to section_structure field
```

#### 3. Structure Display
```
Parse generated structure (array or object format)
↓
Render sections with codes (S01, S02, etc.)
↓
Show titles, descriptions, boundaries, topics, exclusions
↓
Handle both new and legacy format compatibility
```

### UI Components

#### Input Data Panel
- **Topics Display**: Shows generated topics from brainstorming
- **Visual Organization**: Clean, categorized topic presentation
- **Validation**: Ensures topics exist before generation

#### Structure Settings Panel
- **Type Selection**: Dropdown for structure approach
- **Visual Design**: Accessible form controls
- **Default Values**: Sensible defaults for structure types

#### Results Panel
- **Section Structure**: Displays generated sections
- **Section Codes**: Unique identifiers (S01, S02, etc.)
- **Rich Information**: Titles, descriptions, boundaries, topics
- **Format Compatibility**: Handles multiple data formats

#### Section Items
- **Section Code**: Unique identifier (e.g., {S01})
- **Title**: Provisional technical title
- **Description**: Detailed section description
- **Boundaries**: Section scope and limitations
- **Topics**: Associated topics from brainstorming
- **Exclusions**: What the section should not cover

### Error Handling

#### Client-Side Errors
- **Missing Topics**: Prevents generation without input
- **API Failures**: Displays error messages with retry options
- **Format Issues**: Handles various data format variations

#### Server-Side Errors
- **LLM Failures**: Graceful handling of AI generation errors
- **Database Issues**: Error logging and user notification
- **Data Validation**: Ensures required fields are present

### Integration Points

#### With Topic Brainstorming Stage
- **Data Dependency**: Requires generated topics from previous stage
- **Format Compatibility**: Handles topic object structure
- **Validation**: Checks for required topic data

#### With Topic Allocation Stage
- **Data Handoff**: Provides section structure for topic allocation
- **Format Compatibility**: Ensures structure format matches expectations
- **Section Codes**: Maintains unique section identifiers

### Performance Considerations

#### Database Queries
- **Efficient Loading**: Single query for topics and expanded idea
- **JSON Handling**: Proper parsing of idea_scope and section_structure
- **Update Optimization**: Batch updates for structure persistence

#### Client-Side Optimization
- **Lazy Rendering**: Structure rendered on demand
- **State Management**: Efficient DOM updates
- **Memory Management**: Proper cleanup of event listeners

### Security Considerations

#### Input Validation
- **Post ID Validation**: Ensures valid post references
- **Content Sanitization**: Prevents XSS in structure content
- **JSON Safety**: Validates JSON structure before storage

#### Data Integrity
- **Foreign Key Constraints**: Maintains referential integrity
- **Transaction Safety**: Atomic operations for data updates
- **Backup Strategy**: Preserves existing data during updates

### Configuration Options

#### Structure Types
- **Chronological**: Time-based organization (past → present → future)
- **Thematic**: Topic-based grouping (related concepts together)
- **Progressive**: Building complexity (simple → complex)
- **Comparative**: Contrasting views (pros/cons, alternatives)

#### LLM Settings
- **Provider Selection**: Configurable AI provider
- **Model Parameters**: Adjustable generation settings
- **Prompt Templates**: Customizable structure generation prompts
- **Response Parsing**: Configurable structure extraction

### Monitoring and Analytics

#### Usage Tracking
- **Structure Patterns**: Track popular structure types
- **Generation Success**: Monitor structure generation success rates
- **User Preferences**: Track structure type preferences

#### Performance Metrics
- **Generation Time**: Monitor LLM response times
- **User Engagement**: Track interaction patterns
- **Error Rates**: Monitor failure patterns

### Data Structure

#### Section Structure Format (New)
```json
[
  {
    "section_code": "S01",
    "title": "Introduction to Topic",
    "description": "Overview and context setting",
    "boundaries": ["Scope limitations"],
    "topics": ["Topic 1", "Topic 2"],
    "exclusions": ["What not to cover"]
  }
]
```

#### Section Structure Format (Legacy)
```json
{
  "sections": [
    {
      "section_code": "S01",
      "theme": "Introduction",
      "description": "Overview section",
      "boundaries": "Scope limits",
      "topics": ["Topic 1", "Topic 2"],
      "exclusions": ["Excluded content"]
    }
  ]
}
```

### Future Enhancements

#### Potential Improvements
- **Structure Templates**: Pre-defined structure patterns
- **Advanced Customization**: More granular structure control
- **Visual Editor**: Drag-and-drop structure design
- **Structure Validation**: Automatic structure quality checks

#### Technical Debt
- **Format Standardization**: Unify new and legacy formats
- **Error Handling**: Standardize error response formats
- **Testing Coverage**: Add comprehensive test suite
- **Performance Optimization**: Improve rendering performance

### Troubleshooting

#### Common Issues
- **Missing Topics**: Guide users to previous stage
- **Generation Failures**: Provide retry mechanisms
- **Format Problems**: Handle various data format variations
- **Data Persistence**: Ensure structure is saved properly

#### Debug Information
- **Console Logging**: Detailed error information
- **API Responses**: Full response data for debugging
- **State Tracking**: Monitor application state changes
- **Performance Metrics**: Track timing and resource usage

### Migration Notes

#### Legacy Format Support
- **Backward Compatibility**: Handles both array and object formats
- **Data Migration**: Gradual transition to new format
- **Format Detection**: Automatic format detection and handling
- **Error Recovery**: Graceful handling of format mismatches
