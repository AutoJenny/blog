# Family Data Review Page - Technical Documentation

## Overview

The Family Data Review page (`/planning/posts/<post_id>/calendar/family-data-review`) serves as a data review stage for family profile posts. It allows users to review family research data from the `families` table before proceeding to content creation.

## Purpose and Scope

- **Primary Function**: Review and confirm family research data for family profile posts
- **Data Source**: `families` table with `research_data` JSONB field
- **Output**: Confirmed family data ready for drafting
- **Workflow Position**: After taxonomy, before topic brainstorming (similar to product_data_review)

## Technical Architecture

### Flask Route (To Be Created)

```python
@bp.route('/posts/<int:post_id>/calendar/family-data-review')
def planning_calendar_family_data_review(post_id):
    """Family data review page"""
    # Get year/week from URL params
    # Get post data
    # Get family data from families table
    # Render template with family data
```

**File**: `blueprints/planning_calendar_clean.py` (new function)

### Template Structure (To Be Created)

**File**: `templates/planning/calendar/family_data_review.html`

**Key Components**:
- **Family Information Panel**: Basic family data (name, is_clan, etc.)
- **Research Data Display**: Comprehensive research_data JSONB content
- **Family Relationships**: Septs, aliases, spellings
- **Resources**: Images, text, JSON data
- **Confirmation Action**: Button to proceed to next stage

### Database Operations

#### Input Data Sources

1. **Post Data**:
   ```sql
   SELECT p.id, p.title, p.status, p.profile_family_id
   FROM post p
   WHERE p.id = %s
   ```

2. **Family Data**:
   ```sql
   SELECT f.id, f.name, f.is_clan, f.is_canonical, f.research_data
   FROM families f
   WHERE f.id = %s
   ```

3. **Family Relationships**:
   ```sql
   -- Septs
   SELECT fs.sept_name, fs.sept_of_id
   FROM family_septs fs
   WHERE fs.sept_of_id = %s
   
   -- Aliases
   SELECT fa.alias_name
   FROM family_aliases fa
   WHERE fa.family_id = %s
   
   -- Spellings
   SELECT fs.spelling_name, fs.spelling_of_id
   FROM family_spellings fs
   WHERE fs.spelling_of_id = %s
   ```

#### Output Data Storage

- No direct database writes (review only)
- Data confirmed for use in subsequent stages
- Family data loaded into post context for drafting

### API Endpoints (To Be Created)

#### 1. Get Family Data
```http
GET /planning/api/families/<family_id>
```
**Purpose**: Fetch family data and research_data
**Response**: Family object with research_data JSONB

#### 2. Confirm Family Data
```http
POST /planning/api/posts/<post_id>/confirm-family-data
```
**Purpose**: Confirm family data is correct and proceed
**Body**: `{family_id: int, confirmed: bool}`
**Response**: `{success: bool, message: string}`

### JavaScript Modules

#### Core Functionality
- **`loadFamilyData()`**: Fetches and displays family data
- **`displayResearchData()`**: Renders research_data JSONB
- **`displayRelationships()`**: Shows family relationships
- **`confirmFamilyData()`**: Confirms data and proceeds

### Data Flow

#### 1. Page Load
```
User visits /planning/posts/123/calendar/family-data-review
↓
Fetch post data (get profile_family_id)
↓
Fetch family data from families table
↓
Load research_data JSONB
↓
Display family information and research data
```

#### 2. Data Review
```
User reviews family data
↓
Checks research_data completeness
↓
Reviews family relationships
↓
Confirms data is correct
```

#### 3. Confirmation
```
User clicks "Confirm & Continue"
↓
Data confirmed (stored in post context)
↓
Redirect to next stage (topic brainstorming)
```

### UI Components

#### Family Information Panel
- **Family Name**: Display family/clan name
- **Clan Status**: Indicate if official clan
- **Canonical Status**: Show if canonical name
- **Basic Metadata**: ID, created/updated dates

#### Research Data Display
- **Etymology**: Name origin and meaning
- **Early Records**: Historical mentions
- **Distribution**: Geographic spread (historic and modern)
- **Clan Association**: Clan connections
- **Heraldry**: Coat of arms, symbols, mottos
- **Story Facts**: Key figures, turning points, places, legends, themes
- **Notables**: Significant individuals
- **Migration**: Movement patterns

#### Family Relationships Panel
- **Septs**: Sub-families belonging to clan
- **Aliases**: Alternative names
- **Spellings**: Spelling variations

#### Resources Panel
- **Images**: Family-related images
- **Text**: Historical text resources
- **JSON Data**: Additional structured data

### Integration Points

#### With Planning Workflow
- **Previous Step**: Taxonomy assignment
- **Next Step**: Topic brainstorming (uses family data)
- **Data Handoff**: Provides family research data for content generation

#### With Family Research Framework
- **Data Source**: Uses `families.research_data` JSONB
- **Narrative Generation**: Prepares data for `generate_narrative()`
- **Research Tools**: Links to family research utilities

### Error Handling

#### Client-Side Errors
- **No family data**: Shows "Family data not found"
- **Missing research_data**: Shows "Research data incomplete"
- **API failures**: Displays error messages with retry options

#### Server-Side Errors
- **Post not found**: Clear error message
- **Family not found**: Error handling for missing family
- **Data loading failures**: Graceful fallback

### Configuration Options

#### Research Data Display
- **Format**: JSON viewer or formatted display
- **Sections**: Collapsible sections for different data types
- **Relationships**: Expandable relationship trees

#### Confirmation Options
- **Auto-confirm**: Option to skip review if data complete
- **Manual review**: Required confirmation for all posts
- **Partial confirmation**: Confirm specific sections only

### Performance Considerations

#### Database Queries
- **Efficient loading**: Single query for family data
- **JSONB queries**: Use GIN indexes for research_data
- **Relationship queries**: Batch load relationships

#### Client-Side Optimization
- **Lazy loading**: Load relationships on demand
- **Caching**: Cache family data in session
- **Progressive display**: Show basic info first, details on expand

### Security Considerations

#### Input Validation
- **Post ID validation**: Ensure valid post references
- **Family ID validation**: Verify family exists
- **Data sanitization**: Sanitize JSONB display

#### Data Integrity
- **Foreign key constraints**: Maintain referential integrity
- **Read-only review**: No data modification in review stage
- **Audit trail**: Log data review actions

### Future Enhancements

#### Potential Improvements
- **Edit research data**: Allow inline editing of research_data
- **Research tools integration**: Direct links to research utilities
- **Data completeness indicators**: Show what data is missing
- **Comparison view**: Compare with other family profiles

#### Technical Debt
- **Code consolidation**: Reuse components from product_data_review
- **Error handling**: Standardize error response formats
- **Testing coverage**: Add comprehensive test suite
- **Documentation**: Expand inline code documentation

---

## Related Pages

- `docs/page-reference/planning/product-data-review.md` - Similar page for product profiles
- `docs/FAMILY_PROFILE_POST_TYPE.md` - Family profile integration guide
- `docs/families_research_implementation_plan.md` - Family research process

---

**Last Updated:** 2026-01-19
