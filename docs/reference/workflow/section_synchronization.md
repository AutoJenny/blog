# Section Synchronization System

## Overview

The Section Synchronization System maintains data consistency between two complementary fields that manage section data in the blog workflow system:

- **`post_development.section_headings`** (Master Field): JSON array containing the complete list of section data
- **`post_section.section_heading`** (Individual Field): Simple text strings for each individual section

This dual-field architecture supports both LLM workflow planning (via the master field) and UI section management (via individual fields) while ensuring automatic data synchronization.

## Architecture

### Dual-Field Design

```
┌─────────────────────────────────────────────────────────────┐
│                    post_development                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ section_headings: JSON array                        │   │
│  │ [                                                   │   │
│  │   {"order": 1, "heading": "Intro", ...},           │   │
│  │   {"order": 2, "heading": "Main", ...},            │   │
│  │   {"order": 3, "heading": "Conclusion", ...}       │   │
│  │ ]                                                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Automatic Sync
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    post_section                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ id: 1       │  │ id: 2       │  │ id: 3       │        │
│  │ section_    │  │ section_    │  │ section_    │        │
│  │ heading:    │  │ heading:    │  │ heading:    │        │
│  │ "Intro"     │  │ "Main"      │  │ "Conclusion"│        │
│  │ section_    │  │ section_    │  │ section_    │        │
│  │ order: 1    │  │ order: 2    │  │ order: 3    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Field Purposes

#### post_development.section_headings (Master Field)
- **Purpose**: Master list of all section headings for a post
- **Usage**: LLM actions, workflow planning, and overall post structure
- **Format**: JSON array containing structured section data
- **Authority**: Primary source of truth for section structure
- **Access**: Used in workflow dropdowns and LLM action inputs/outputs

#### post_section.section_heading (Individual Field)
- **Purpose**: Individual section heading for UI display and management
- **Usage**: Green sections module, accordion display, drag-and-drop reordering
- **Format**: Simple text string for each section
- **Authority**: Derived from master field, used for UI interactions
- **Access**: Used in section management UI and individual section editing

## Data Formats

### Recommended JSON Format

The `section_headings` field uses a structured JSON array format:

```json
[
  {
    "order": 1,
    "heading": "Introduction",
    "description": "Overview of the topic",
    "status": "draft"
  },
  {
    "order": 2,
    "heading": "Main Content",
    "description": "Core discussion points",
    "status": "in_progress"
  },
  {
    "order": 3,
    "heading": "Conclusion",
    "description": "Summary and takeaways",
    "status": "complete"
  }
]
```

### Legacy Format Support

The system supports multiple formats during transition:

#### Simple Array Format
```json
["Section 1", "Section 2", "Section 3"]
```

#### Delimited String Format
```
"Section 1\nSection 2\nSection 3"
```

#### Numbered Format
```
"1. Section 1\n2. Section 2\n3. Section 3"
```

## Synchronization Strategy

### Primary Direction: post_development → post_section

**Trigger**: Any update to `post_development.section_headings`
**Action**: Automatically sync to individual `post_section` records
**Purpose**: Ensure UI sections reflect the master planning data

**Process**:
1. Parse JSON array from `section_headings`
2. Create/update `post_section` records for each item
3. Remove sections no longer in the master list
4. Maintain proper ordering

### Secondary Direction: post_section → post_development (Optional)

**Trigger**: When individual sections are created/updated/deleted
**Action**: Update the master list to reflect actual section data
**Purpose**: Keep planning data in sync with actual implementation

**Process**:
1. Query all `post_section` records for the post
2. Build JSON array from section data
3. Update `post_development.section_headings`
4. Maintain data consistency

## Implementation

### Database Triggers

#### Primary Sync Trigger

```sql
-- Trigger function for post_development.section_headings changes
CREATE OR REPLACE FUNCTION sync_section_headings_to_sections()
RETURNS TRIGGER AS $$
DECLARE
    section_data JSONB;
    section_item JSONB;
    section_id INTEGER;
    i INTEGER := 0;
BEGIN
    -- Only proceed if section_headings was updated
    IF OLD.section_headings IS NOT DISTINCT FROM NEW.section_headings THEN
        RETURN NEW;
    END IF;
    
    -- Parse the section_headings JSON
    IF NEW.section_headings IS NULL OR NEW.section_headings = '' THEN
        -- Clear all sections for this post
        DELETE FROM post_section WHERE post_id = NEW.post_id;
        RETURN NEW;
    END IF;
    
    BEGIN
        section_data := NEW.section_headings::JSONB;
    EXCEPTION WHEN OTHERS THEN
        -- Handle invalid JSON - log error but don't fail
        RAISE WARNING 'Invalid JSON in section_headings for post %: %', NEW.post_id, NEW.section_headings;
        RETURN NEW;
    END;
    
    -- Process each section in the array
    FOR section_item IN SELECT * FROM jsonb_array_elements(section_data)
    LOOP
        i := i + 1;
        
        -- Extract section data
        DECLARE
            heading TEXT;
            description TEXT;
            status TEXT;
        BEGIN
            -- Handle different JSON formats
            IF jsonb_typeof(section_item) = 'string' THEN
                heading := section_item::TEXT;
                description := '';
                status := 'draft';
            ELSE
                heading := COALESCE(section_item->>'heading', section_item->>'title', 'Section ' || i);
                description := COALESCE(section_item->>'description', '');
                status := COALESCE(section_item->>'status', 'draft');
            END IF;
            
            -- Find existing section or create new one
            SELECT id INTO section_id 
            FROM post_section 
            WHERE post_id = NEW.post_id AND section_order = i;
            
            IF section_id IS NULL THEN
                -- Create new section
                INSERT INTO post_section (
                    post_id, section_order, section_heading, 
                    section_description, status
                ) VALUES (
                    NEW.post_id, i, heading, description, status
                );
            ELSE
                -- Update existing section
                UPDATE post_section 
                SET section_heading = heading,
                    section_description = description,
                    status = status,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = section_id;
            END IF;
        END;
    END LOOP;
    
    -- Remove sections that are no longer in the list
    DELETE FROM post_section 
    WHERE post_id = NEW.post_id AND section_order > i;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger on post_development updates
CREATE TRIGGER trigger_sync_section_headings
    AFTER UPDATE OF section_headings ON post_development
    FOR EACH ROW
    EXECUTE FUNCTION sync_section_headings_to_sections();
```

#### Secondary Sync Trigger (Optional)

```sql
-- Trigger function for post_section changes
CREATE OR REPLACE FUNCTION sync_sections_to_section_headings()
RETURNS TRIGGER AS $$
DECLARE
    section_headings JSONB;
    section_record RECORD;
BEGIN
    -- Build JSON array from current sections
    section_headings := '[]'::JSONB;
    
    FOR section_record IN 
        SELECT section_order, section_heading, section_description, status
        FROM post_section 
        WHERE post_id = COALESCE(NEW.post_id, OLD.post_id)
        ORDER BY section_order
    LOOP
        section_headings := section_headings || jsonb_build_object(
            'order', section_record.section_order,
            'heading', section_record.section_heading,
            'description', COALESCE(section_record.section_description, ''),
            'status', COALESCE(section_record.status, 'draft')
        );
    END LOOP;
    
    -- Update post_development
    UPDATE post_development 
    SET section_headings = section_headings::TEXT,
        updated_at = CURRENT_TIMESTAMP
    WHERE post_id = COALESCE(NEW.post_id, OLD.post_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Triggers for post_section changes
CREATE TRIGGER trigger_sync_sections_to_headings_insert
    AFTER INSERT ON post_section
    FOR EACH ROW
    EXECUTE FUNCTION sync_sections_to_section_headings();

CREATE TRIGGER trigger_sync_sections_to_headings_update
    AFTER UPDATE ON post_section
    FOR EACH ROW
    EXECUTE FUNCTION sync_sections_to_section_headings();

CREATE TRIGGER trigger_sections_to_headings_delete
    AFTER DELETE ON post_section
    FOR EACH ROW
    EXECUTE FUNCTION sync_sections_to_section_headings();
```

### Application-Level Synchronization

#### Manual Sync API Endpoint

```python
@bp.route('/posts/<int:post_id>/sync-sections', methods=['POST'])
def sync_sections(post_id):
    """Manually sync section data between post_development and post_section"""
    direction = request.json.get('direction', 'both')  # 'to_sections', 'to_development', 'both'
    
    try:
        if direction in ['to_sections', 'both']:
            # Sync post_development.section_headings → post_section
            post_dev = get_post_development(post_id)
            if post_dev and post_dev.section_headings:
                sync_section_headings_to_sections(post_id, post_dev.section_headings)
        
        if direction in ['to_development', 'both']:
            # Sync post_section → post_development.section_headings
            sync_sections_to_section_headings(post_id)
        
        return jsonify({
            'status': 'success', 
            'direction': direction,
            'message': f'Sections synchronized successfully'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Sync failed: {str(e)}'
        }), 500
```

#### Synchronization Functions

```python
def sync_section_headings_to_sections(post_id: int, section_headings_json: str):
    """
    Parse section_headings from post_development and sync to post_section records
    """
    try:
        # Parse the JSON array
        sections_data = json.loads(section_headings_json)
        
        # Clear existing sections for this post
        with get_db_conn() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM post_section WHERE post_id = %s", (post_id,))
            
            # Create new sections from the JSON data
            for i, section_info in enumerate(sections_data):
                if isinstance(section_info, str):
                    # Simple string format
                    heading = section_info
                    description = ""
                    status = "draft"
                else:
                    # Structured format
                    heading = section_info.get('heading', section_info.get('title', f'Section {i+1}'))
                    description = section_info.get('description', '')
                    status = section_info.get('status', 'draft')
                
                # Insert new section
                cur.execute("""
                    INSERT INTO post_section (
                        post_id, section_order, section_heading, 
                        section_description, status
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (post_id, i+1, heading, description, status))
            
            conn.commit()
            
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in section_headings: {e}")
    except Exception as e:
        raise Exception(f"Failed to sync sections: {e}")

def sync_sections_to_section_headings(post_id: int):
    """
    Update post_development.section_headings based on current post_section records
    """
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get all sections for this post
        cur.execute("""
            SELECT section_order, section_heading, section_description, status
            FROM post_section 
            WHERE post_id = %s 
            ORDER BY section_order
        """, (post_id,))
        
        sections = cur.fetchall()
        
        # Build JSON array
        section_headings = []
        for section in sections:
            section_headings.append({
                "order": section['section_order'],
                "heading": section['section_heading'],
                "description": section['section_description'] or "",
                "status": section['status'] or "draft"
            })
        
        # Update post_development
        cur.execute("""
            UPDATE post_development 
            SET section_headings = %s
            WHERE post_id = %s
        """, (json.dumps(section_headings), post_id))
        
        conn.commit()
```

## API Endpoints

### Manual Synchronization

#### Sync Sections
```http
POST /api/workflow/posts/{post_id}/sync-sections
```

**Parameters**:
- `direction` (string, optional): Sync direction
  - `"to_sections"`: Sync from post_development to post_section only
  - `"to_development"`: Sync from post_section to post_development only
  - `"both"`: Sync both directions (default)

**Example Requests**:
```bash
# Sync both directions
curl -X POST "http://localhost:5000/api/workflow/posts/22/sync-sections" \
  -H "Content-Type: application/json" \
  -d '{"direction": "both"}'

# Sync only to sections
curl -X POST "http://localhost:5000/api/workflow/posts/22/sync-sections" \
  -H "Content-Type: application/json" \
  -d '{"direction": "to_sections"}'

# Sync only to development
curl -X POST "http://localhost:5000/api/workflow/posts/22/sync-sections" \
  -H "Content-Type: application/json" \
  -d '{"direction": "to_development"}'
```

**Response**:
```json
{
  "status": "success",
  "direction": "both",
  "message": "Sections synchronized successfully"
}
```

**Error Response**:
```json
{
  "status": "error",
  "message": "Sync failed: Invalid JSON in section_headings"
}
```

## Migration and Deployment

### Implementation Phases

#### Phase 1: Basic Synchronization (Immediate)
1. **Database Triggers**: Implement primary sync trigger (post_development → post_section)
2. **Manual Sync API**: Add `/api/workflow/posts/{post_id}/sync-sections` endpoint
3. **Documentation**: Update all relevant documentation
4. **Testing**: Test with existing data

#### Phase 2: Enhanced Synchronization (Next)
1. **Secondary Triggers**: Add post_section → post_development sync triggers
2. **Format Standardization**: Migrate to standardized JSON format
3. **Error Handling**: Add comprehensive error handling and logging
4. **Validation**: Add data validation for sync operations

#### Phase 3: Advanced Features (Future)
1. **Conflict Resolution**: Handle sync conflicts between fields
2. **Performance Optimization**: Optimize sync performance for large datasets
3. **Monitoring**: Add sync monitoring and alerting
4. **Rollback Capability**: Add ability to rollback sync operations

### Migration Scripts

#### Data Format Migration
```sql
-- Migrate existing section_headings to standardized JSON format
UPDATE post_development 
SET section_headings = (
    SELECT json_agg(
        json_build_object(
            'order', s.section_order,
            'heading', s.section_heading,
            'description', COALESCE(s.section_description, ''),
            'status', COALESCE(s.status, 'draft')
        )
    )
    FROM post_section s 
    WHERE s.post_id = post_development.post_id
    ORDER BY s.section_order
)
WHERE section_headings IS NULL OR section_headings = '';
```

#### Validation Script
```sql
-- Validate sync consistency
SELECT 
    pd.post_id,
    pd.section_headings,
    COUNT(ps.id) as section_count,
    CASE 
        WHEN pd.section_headings IS NULL THEN 'No master data'
        WHEN COUNT(ps.id) = 0 THEN 'No sections'
        WHEN json_array_length(pd.section_headings::json) != COUNT(ps.id) THEN 'Count mismatch'
        ELSE 'OK'
    END as sync_status
FROM post_development pd
LEFT JOIN post_section ps ON pd.post_id = ps.post_id
GROUP BY pd.post_id, pd.section_headings
HAVING COUNT(ps.id) > 0 OR pd.section_headings IS NOT NULL;
```

## Testing Strategy

### Unit Tests

```python
def test_sync_section_headings_to_sections():
    """Test synchronization from post_development to post_section"""
    # Test data
    post_id = 1
    section_headings = json.dumps([
        {"order": 1, "heading": "Intro", "description": "Overview"},
        {"order": 2, "heading": "Main", "description": "Content"}
    ])
    
    # Execute sync
    sync_section_headings_to_sections(post_id, section_headings)
    
    # Verify results
    sections = get_post_sections(post_id)
    assert len(sections) == 2
    assert sections[0].section_heading == "Intro"
    assert sections[1].section_heading == "Main"

def test_sync_sections_to_section_headings():
    """Test synchronization from post_section to post_development"""
    # Test data
    post_id = 1
    create_test_sections(post_id)
    
    # Execute sync
    sync_sections_to_section_headings(post_id)
    
    # Verify results
    post_dev = get_post_development(post_id)
    section_headings = json.loads(post_dev.section_headings)
    assert len(section_headings) == 2
    assert section_headings[0]["heading"] == "Test Section 1"
```

### Integration Tests

```python
def test_sync_api_endpoint():
    """Test the manual sync API endpoint"""
    response = client.post(f'/api/workflow/posts/1/sync-sections', 
                          json={'direction': 'both'})
    assert response.status_code == 200
    assert response.json['status'] == 'success'

def test_database_triggers():
    """Test database trigger synchronization"""
    # Update post_development.section_headings
    update_post_development(1, {'section_headings': '["New Section"]'})
    
    # Verify post_section was automatically updated
    sections = get_post_sections(1)
    assert len(sections) == 1
    assert sections[0].section_heading == "New Section"
```

## Troubleshooting

### Common Issues

#### 1. Sync Not Working
**Symptoms**: Changes to post_development.section_headings don't appear in post_section
**Causes**: 
- Database triggers not installed
- Invalid JSON format in section_headings
- Database connection issues

**Solutions**:
```bash
# Check if triggers exist
psql -d blog -c "\d+ post_development"

# Test manual sync
curl -X POST "http://localhost:5000/api/workflow/posts/1/sync-sections" \
  -H "Content-Type: application/json" \
  -d '{"direction": "to_sections"}'

# Check JSON format
psql -d blog -c "SELECT post_id, section_headings FROM post_development WHERE post_id = 1;"
```

#### 2. Data Inconsistency
**Symptoms**: post_development and post_section have different section data
**Causes**:
- Manual updates bypassing sync
- Sync errors not handled properly
- Concurrent updates

**Solutions**:
```bash
# Force sync both directions
curl -X POST "http://localhost:5000/api/workflow/posts/1/sync-sections" \
  -H "Content-Type: application/json" \
  -d '{"direction": "both"}'

# Check data consistency
psql -d blog -c "
SELECT 
    pd.post_id,
    pd.section_headings,
    COUNT(ps.id) as section_count
FROM post_development pd
LEFT JOIN post_section ps ON pd.post_id = ps.post_id
WHERE pd.post_id = 1
GROUP BY pd.post_id, pd.section_headings;
"
```

#### 3. Performance Issues
**Symptoms**: Slow sync operations with large datasets
**Causes**:
- Inefficient database queries
- Large JSON parsing overhead
- Missing indexes

**Solutions**:
```sql
-- Add performance indexes
CREATE INDEX CONCURRENTLY idx_post_section_post_order 
ON post_section(post_id, section_order);

CREATE INDEX CONCURRENTLY idx_post_development_section_headings 
ON post_development USING GIN ((section_headings::jsonb));

-- Optimize sync function
-- (Add batch processing for large datasets)
```

### Monitoring and Logging

#### Database Logging
```sql
-- Enable trigger logging
CREATE OR REPLACE FUNCTION log_sync_operations()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO sync_log (
        operation_type, 
        post_id, 
        old_data, 
        new_data, 
        timestamp
    ) VALUES (
        TG_OP,
        COALESCE(NEW.post_id, OLD.post_id),
        OLD.section_headings,
        NEW.section_headings,
        CURRENT_TIMESTAMP
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
```

#### Application Logging
```python
import logging

logger = logging.getLogger(__name__)

def sync_section_headings_to_sections(post_id: int, section_headings_json: str):
    """Parse section_headings from post_development and sync to post_section records"""
    logger.info(f"Starting sync for post {post_id}")
    
    try:
        # ... sync logic ...
        logger.info(f"Sync completed successfully for post {post_id}")
    except Exception as e:
        logger.error(f"Sync failed for post {post_id}: {e}")
        raise
```

## Best Practices

### Data Management
1. **Always use post_development.section_headings as the master source**
2. **Let automatic sync handle post_section updates**
3. **Use manual sync only for troubleshooting or bulk operations**
4. **Validate JSON format before updates**

### Performance
1. **Batch large sync operations**
2. **Use database indexes for sync queries**
3. **Monitor sync performance with large datasets**
4. **Consider async processing for non-critical syncs**

### Error Handling
1. **Always wrap sync operations in try-catch blocks**
2. **Log sync errors for debugging**
3. **Provide fallback mechanisms for sync failures**
4. **Validate data before and after sync operations**

### Testing
1. **Test sync with various data formats**
2. **Test concurrent updates**
3. **Test sync with large datasets**
4. **Test sync error conditions**

## Integration with Workflow System

### LLM Actions Integration
The `post_development.section_headings` field is available as an input/output option in LLM actions, allowing for:
- Section generation from prompts
- Section restructuring and reordering
- Section content enhancement
- Section allocation of facts and ideas

### Workflow Field Mapping
The field is mapped in the workflow system under the "Outlining Stage" and can be used in:
- Input field dropdowns for LLM actions
- Output field dropdowns for LLM results
- Workflow step configuration
- Field mapping settings

### UI Integration
The `post_section.section_heading` fields are used in:
- Green sections module display
- Section accordion functionality
- Drag-and-drop reordering
- Individual section editing

## References

- [Section-Based Workflow Documentation](sections.md)
- [Database Schema Documentation](../database/schema.md)
- [Workflow System Overview](README.md)
- [API Endpoints Reference](endpoints.md)

---

This documentation provides a complete guide to the section synchronization system, ensuring data consistency between planning and implementation phases of the blog workflow. 