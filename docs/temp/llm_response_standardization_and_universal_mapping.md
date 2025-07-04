# LLM Response Standardization and Universal Input Mapping Implementation Plan

## Overview

This document outlines the comprehensive changes required to:
1. **Standardize backend responses** for LLM actions to ensure consistent frontend handling
2. **Expand field mapping UI** to support table selection for inputs/outputs
3. **Implement universal input mapping** system for future flexibility

## Current Issues

### 1. Response Structure Mismatch
- **Problem**: Frontend expects `data.data.result` but backend returns `output`, `result`, or other inconsistent keys
- **Impact**: JavaScript errors like `'parameters'` when trying to access non-existent keys
- **Location**: `app/static/js/llm_utils.js` line 67, `app/static/js/config/api.js`

### 2. Limited Input Mapping Flexibility
- **Problem**: Input mappings are hardcoded to specific tables (post_development, post_section)
- **Impact**: Cannot easily add new tables or change data sources
- **Location**: Field mapping configuration and backend field resolution logic

## Required Changes

### 1. Backend Response Standardization

#### A. API Endpoint Changes

**File**: `app/api/workflow/routes.py`

**Current Response Structure** (inconsistent):
```python
# writing_llm endpoint
return jsonify({
    'success': True,
    'output': output,           # Inconsistent key name
    'step': step,
    'sections_processed': section_ids
})

# process_step function
return jsonify({
    'success': True,
    'data': {
        'result': response      # Different structure
    }
})
```

**Required Standardized Response**:
```python
def standardize_llm_response(success, results, step, sections_processed, parameters=None):
    """Standardize all LLM action responses"""
    return jsonify({
        'success': success,
        'results': results,  # Array of result objects
        'step': step,
        'sections_processed': sections_processed,
        'parameters': parameters or {}
    })

# Example usage:
results = [
    {
        'section_id': section_id,
        'output': llm_response,
        'parameters': {
            'model': model_name,
            'temperature': temperature,
            'tokens_used': tokens_used
        }
    }
    for section_id, llm_response in zip(section_ids, responses)
]

return standardize_llm_response(
    success=True,
    results=results,
    step=step,
    sections_processed=section_ids,
    parameters={'total_tokens': sum(t['tokens_used'] for t in results)}
)
```

#### B. LLM Processor Changes

**File**: `app/workflow/scripts/llm_processor.py`

**Changes Required**:
1. Update `process_writing_step` function to return standardized response
2. Update `process_step` function to return standardized response
3. Add helper function for response standardization
4. Ensure all LLM calls include parameters in response

**Code Changes**:
```python
def standardize_llm_response(success, results, step, sections_processed, parameters=None):
    """Standardize LLM response format"""
    return {
        'success': success,
        'results': results,
        'step': step,
        'sections_processed': sections_processed,
        'parameters': parameters or {}
    }

def process_writing_step(post_id, stage, substage, step, section_ids, frontend_inputs=None):
    # ... existing logic ...
    
    # For section_headings step
    if normalized_step in ["section headings", "create sections"]:
        # ... existing section creation logic ...
        
        return standardize_llm_response(
            success=True,
            results=[{
                'section_id': None,  # Not applicable for section creation
                'output': f"Created {len(sections)} sections",
                'parameters': {'sections_created': len(sections)}
            }],
            step=step,
            sections_processed=section_ids
        )
    
    # For regular section processing
    results = []
    for section_id in section_ids:
        # ... existing LLM processing logic ...
        results.append({
            'section_id': section_id,
            'output': llm_response,
            'parameters': {
                'model': model_name,
                'temperature': temperature,
                'tokens_used': tokens_used
            }
        })
    
    return standardize_llm_response(
        success=True,
        results=results,
        step=step,
        sections_processed=section_ids
    )
```

### 2. Frontend Response Handling Updates

#### A. JavaScript Updates

**File**: `app/static/js/llm_utils.js`

**Current Code** (line 67):
```javascript
if (data.data && data.data.result) {
    // Update all output textarea fields
    const outputs = document.querySelectorAll('[data-section="outputs"] textarea');
    outputs.forEach(output => {
        output.value = data.data.result;  // Wrong key
    });
}
```

**Required Changes**:
```javascript
function handleLLMResponse(data) {
    if (data.success && data.results) {
        // Handle multiple results (for section processing)
        data.results.forEach(result => {
            const sectionId = result.section_id;
            const output = result.output;
            
            if (sectionId) {
                // Update specific section output
                const sectionOutput = document.querySelector(`[data-section-id="${sectionId}"] textarea[data-field="output"]`);
                if (sectionOutput) {
                    sectionOutput.value = output;
                }
            } else {
                // Update all outputs (for section creation)
                const outputs = document.querySelectorAll('[data-section="outputs"] textarea');
                outputs.forEach(output => {
                    output.value = output;
                });
            }
        });
        
        // Update parameters display if available
        if (data.parameters) {
            updateParametersDisplay(data.parameters);
        }
    } else {
        console.error('Invalid response format:', data);
    }
}

function updateParametersDisplay(parameters) {
    // Update UI with LLM call parameters (tokens, model, etc.)
    const paramsContainer = document.getElementById('llm-parameters');
    if (paramsContainer) {
        paramsContainer.innerHTML = `
            <div>Model: ${parameters.model || 'Unknown'}</div>
            <div>Tokens: ${parameters.tokens_used || 'Unknown'}</div>
            <div>Temperature: ${parameters.temperature || 'Unknown'}</div>
        `;
    }
}
```

#### B. API Configuration Updates

**File**: `app/static/js/config/api.js`

**Changes Required**:
1. Update response handling to use standardized format
2. Add error handling for malformed responses
3. Ensure consistent error reporting

### 3. Universal Input Mapping System

#### A. Database Schema Changes

**New Table**: `workflow_field_mapping`

```sql
CREATE TABLE workflow_field_mapping (
    id SERIAL PRIMARY KEY,
    workflow_step_id INTEGER REFERENCES workflow_step_entity(id),
    field_name VARCHAR(128) NOT NULL,
    field_type VARCHAR(32) NOT NULL, -- 'input' or 'output'
    table_name VARCHAR(64) NOT NULL, -- 'post_development', 'post_section', etc.
    column_name VARCHAR(64) NOT NULL,
    display_name VARCHAR(128) NOT NULL,
    is_required BOOLEAN DEFAULT false,
    default_value TEXT,
    validation_rules JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for efficient lookups
CREATE INDEX idx_workflow_field_mapping_step ON workflow_field_mapping(workflow_step_id, field_type);
```

**Update Existing Tables**:
```sql
-- Add table reference to existing field mappings if any
ALTER TABLE workflow_step_entity ADD COLUMN field_mappings JSONB DEFAULT '{}';
```

#### B. Backend Field Resolution Logic

**File**: `app/workflow/scripts/llm_processor.py`

**New Function**:
```python
def resolve_field_value(table_name, column_name, context):
    """
    Resolve field value from specified table based on context
    
    Args:
        table_name: Name of the table (post_development, post_section, etc.)
        column_name: Name of the column
        context: Dict with post_id, section_id, etc.
    
    Returns:
        Field value or None if not found
    """
    conn = get_db_conn()
    try:
        if table_name == 'post_development':
            # Fetch from post_development table
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT %s FROM post_development WHERE post_id = %s",
                (column_name, context['post_id'])
            )
            result = cursor.fetchone()
            return result[column_name] if result else None
            
        elif table_name == 'post_section':
            # Fetch from post_section table for specific section
            if 'section_id' not in context:
                raise ValueError("section_id required for post_section table")
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT %s FROM post_section WHERE id = %s AND post_id = %s",
                (column_name, context['section_id'], context['post_id'])
            )
            result = cursor.fetchone()
            return result[column_name] if result else None
            
        else:
            # Future tables can be added here
            raise ValueError(f"Unsupported table: {table_name}")
            
    finally:
        conn.close()

def load_field_mappings(workflow_step_id):
    """Load field mappings for a workflow step"""
    conn = get_db_conn()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT field_name, field_type, table_name, column_name, 
                   display_name, is_required, default_value, validation_rules
            FROM workflow_field_mapping 
            WHERE workflow_step_id = %s
            ORDER BY field_type, field_name
        """, (workflow_step_id,))
        return cursor.fetchall()
    finally:
        conn.close()

def prepare_prompt_with_mappings(prompt_template, field_mappings, context):
    """Prepare prompt by replacing [data:field] placeholders using field mappings"""
    prepared_prompt = prompt_template
    
    for mapping in field_mappings:
        if mapping['field_type'] == 'input':
            field_value = resolve_field_value(
                mapping['table_name'], 
                mapping['column_name'], 
                context
            )
            
            if field_value is None and mapping['is_required']:
                raise ValueError(f"Required field {mapping['field_name']} not found")
            
            if field_value is None:
                field_value = mapping['default_value'] or ''
            
            # Replace placeholder
            placeholder = f"[data:{mapping['field_name']}]"
            prepared_prompt = prepared_prompt.replace(placeholder, str(field_value))
    
    return prepared_prompt
```

#### C. Field Mapping UI Enhancement

**File**: `app/templates/settings/workflow_field_mapping.html`

**New Features Required**:
1. Table selection dropdown for each field mapping
2. Dynamic field selection based on selected table
3. Validation rules configuration
4. Required/optional field toggle
5. Default value input

**UI Structure**:
```html
<div class="field-mapping-row">
    <div class="field-info">
        <input type="text" name="field_name" placeholder="Field Name" required>
        <select name="field_type" required>
            <option value="input">Input</option>
            <option value="output">Output</option>
        </select>
    </div>
    
    <div class="table-selection">
        <select name="table_name" class="table-selector" required>
            <option value="">Select Table</option>
            <option value="post_development">Post Development</option>
            <option value="post_section">Post Section</option>
            <!-- Future tables -->
        </select>
        
        <select name="column_name" class="column-selector" required>
            <option value="">Select Column</option>
            <!-- Dynamically populated based on table -->
        </select>
    </div>
    
    <div class="field-config">
        <input type="text" name="display_name" placeholder="Display Name" required>
        <label>
            <input type="checkbox" name="is_required"> Required
        </label>
        <input type="text" name="default_value" placeholder="Default Value">
    </div>
    
    <button type="button" class="remove-field">Remove</button>
</div>
```

**JavaScript for Dynamic UI**:
```javascript
// Dynamic column loading based on table selection
document.querySelectorAll('.table-selector').forEach(selector => {
    selector.addEventListener('change', async function() {
        const tableName = this.value;
        const columnSelector = this.closest('.field-mapping-row').querySelector('.column-selector');
        
        if (tableName) {
            const columns = await fetchTableColumns(tableName);
            columnSelector.innerHTML = '<option value="">Select Column</option>';
            columns.forEach(column => {
                columnSelector.innerHTML += `<option value="${column}">${column}</option>`;
            });
        } else {
            columnSelector.innerHTML = '<option value="">Select Column</option>';
        }
    });
});

async function fetchTableColumns(tableName) {
    const response = await fetch(`/api/database/tables/${tableName}/columns`);
    const data = await response.json();
    return data.columns;
}
```

#### D. API Endpoints for Field Mapping

**New Endpoints Required**:

1. **Get Available Tables**:
```http
GET /api/workflow/field-mapping/tables
```

2. **Get Table Columns**:
```http
GET /api/workflow/field-mapping/tables/{table_name}/columns
```

3. **Save Field Mappings**:
```http
POST /api/workflow/field-mapping/steps/{step_id}
```

4. **Get Field Mappings**:
```http
GET /api/workflow/field-mapping/steps/{step_id}
```

**Implementation in `app/api/workflow/routes.py`**:
```python
@app.route('/api/workflow/field-mapping/tables', methods=['GET'])
def get_available_tables():
    """Get list of available tables for field mapping"""
    tables = [
        {'name': 'post_development', 'display_name': 'Post Development'},
        {'name': 'post_section', 'display_name': 'Post Section'},
        # Future tables can be added here
    ]
    return jsonify({'tables': tables})

@app.route('/api/workflow/field-mapping/tables/<table_name>/columns', methods=['GET'])
def get_table_columns(table_name):
    """Get columns for a specific table"""
    conn = get_db_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        columns = [row[0] for row in cursor.fetchall()]
        return jsonify({'columns': columns})
    finally:
        conn.close()

@app.route('/api/workflow/field-mapping/steps/<int:step_id>', methods=['GET', 'POST'])
def manage_field_mappings(step_id):
    """Get or save field mappings for a workflow step"""
    if request.method == 'GET':
        mappings = load_field_mappings(step_id)
        return jsonify({'mappings': mappings})
    
    elif request.method == 'POST':
        data = request.get_json()
        save_field_mappings(step_id, data['mappings'])
        return jsonify({'success': True})
```

### 4. Settings Page Updates

#### A. Field Mapping Settings Page

**File**: `app/templates/settings/workflow_field_mapping.html`

**Features**:
1. Workflow step selection
2. Dynamic field mapping configuration
3. Table and column selection
4. Validation rules
5. Preview of mapped fields

#### B. Route Updates

**File**: `app/routes/settings.py`

**Add new route**:
```python
@app.route('/settings/workflow_field_mapping')
def workflow_field_mapping():
    """Field mapping configuration page"""
    return render_template('settings/workflow_field_mapping.html')
```

### 5. Testing and Validation

#### A. Unit Tests

**File**: `tests/workflow/test_field_mapping.py`

**Test Cases**:
1. Field resolution from different tables
2. Response standardization
3. UI field mapping configuration
4. Error handling for missing fields

#### B. Integration Tests

**File**: `tests/workflow/integration/test_llm_actions.py`

**Test Cases**:
1. End-to-end LLM action with field mappings
2. Response format consistency
3. Error handling and recovery

### 6. Migration Strategy

#### A. Database Migration

**File**: `migrations/202501XX_add_workflow_field_mapping.sql`

```sql
-- Create new table
CREATE TABLE workflow_field_mapping (
    id SERIAL PRIMARY KEY,
    workflow_step_id INTEGER REFERENCES workflow_step_entity(id),
    field_name VARCHAR(128) NOT NULL,
    field_type VARCHAR(32) NOT NULL,
    table_name VARCHAR(64) NOT NULL,
    column_name VARCHAR(64) NOT NULL,
    display_name VARCHAR(128) NOT NULL,
    is_required BOOLEAN DEFAULT false,
    default_value TEXT,
    validation_rules JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_workflow_field_mapping_step ON workflow_field_mapping(workflow_step_id, field_type);

-- Migrate existing field mappings if any
-- (This will depend on current implementation)
```

#### B. Code Migration

1. **Phase 1**: Implement response standardization
2. **Phase 2**: Add field mapping database schema
3. **Phase 3**: Update backend field resolution
4. **Phase 4**: Enhance UI for field mapping
5. **Phase 5**: Migrate existing configurations

### 7. Documentation Updates

#### A. API Documentation

**File**: `docs/reference/api/current/workflow.md`

**Updates Required**:
1. Standardized response format documentation
2. Field mapping API endpoints
3. Error handling and validation

#### B. User Documentation

**File**: `docs/workflow/field_mapping.md`

**New Documentation**:
1. How to configure field mappings
2. Table and column selection
3. Validation rules
4. Best practices

### 8. Rollback Plan

#### A. Database Rollback

```sql
-- Drop new table if needed
DROP TABLE IF EXISTS workflow_field_mapping CASCADE;
```

#### B. Code Rollback

1. Revert response standardization changes
2. Remove field mapping UI components
3. Restore original field resolution logic

## Implementation Timeline

### Week 1: Response Standardization
- [ ] Update backend response format
- [ ] Update frontend response handling
- [ ] Test with existing LLM actions

### Week 2: Database Schema
- [ ] Create workflow_field_mapping table
- [ ] Add migration scripts
- [ ] Test database operations

### Week 3: Backend Field Resolution
- [ ] Implement universal field resolution
- [ ] Add field mapping API endpoints
- [ ] Update LLM processor

### Week 4: UI Enhancement
- [ ] Create field mapping settings page
- [ ] Implement dynamic table/column selection
- [ ] Add validation and error handling

### Week 5: Testing and Documentation
- [ ] Comprehensive testing
- [ ] Update documentation
- [ ] User acceptance testing

## Success Criteria

1. **Response Standardization**:
   - All LLM actions return consistent response format
   - Frontend handles responses without errors
   - Parameters and metadata are properly included

2. **Universal Input Mapping**:
   - Users can select any table for field mappings
   - Dynamic column selection works correctly
   - Field resolution works for all supported tables

3. **UI Enhancement**:
   - Field mapping configuration is intuitive
   - Validation provides clear feedback
   - Settings are properly saved and loaded

4. **Performance**:
   - No significant performance degradation
   - Efficient database queries
   - Responsive UI interactions

## Risk Assessment

### High Risk
- **Breaking Changes**: Response format changes could break existing integrations
- **Data Loss**: Database schema changes could affect existing data

### Medium Risk
- **UI Complexity**: New field mapping UI might be confusing
- **Performance**: Additional database queries could slow down operations

### Low Risk
- **Documentation**: Keeping docs updated with new features
- **Testing**: Ensuring comprehensive test coverage

## Mitigation Strategies

1. **Backward Compatibility**: Maintain old response format during transition
2. **Data Backup**: Full database backup before schema changes
3. **Gradual Rollout**: Implement changes in phases with testing
4. **User Training**: Provide clear documentation and examples
5. **Monitoring**: Track performance and error rates during rollout 