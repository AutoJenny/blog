# Run LLM Section Processing Fixes - Implementation Memo

## Overview
The current Run LLM button in the Writing stage has significant issues that prevent proper section-specific processing. This memo documents all required fixes to implement iterative section processing with proper saving to output fields.

## Current Problems Identified

### 1. Frontend Issues
- **No Section Selection Collection**: Checkboxes exist but are not collected
- **Wrong API Endpoint**: Calls Planning stage endpoint instead of Writing stage
- **No Progress Feedback**: No indication of multi-section processing
- **Missing Output Field Mapping**: Doesn't use selected output field from purple panel

### 2. Backend Issues
- **Placeholder Implementation**: `process_sections_sequentially()` returns dummy data
- **No Real LLM Processing**: No actual LLM calls for sections
- **Missing Output Field Logic**: Doesn't save to specific output fields
- **No Error Handling**: No per-section error handling

## Required Implementation

### Frontend Changes

#### 1. Section Selection Collection
**File**: `app/static/js/enhanced_llm_message_manager.js`
**Function**: Add `getSelectedSectionIds()` method

```javascript
getSelectedSectionIds() {
    const checkboxes = Array.from(document.querySelectorAll('.section-select-checkbox'));
    return checkboxes
        .filter(cb => cb.checked)
        .map(cb => parseInt(cb.dataset.sectionId))
        .filter(id => !isNaN(id));
}
```

#### 2. Output Field Mapping
**File**: `app/static/js/enhanced_llm_message_manager.js`
**Function**: Add `getOutputFieldMapping()` method

```javascript
getOutputFieldMapping() {
    // Get output field selection from purple panel
    const outputSelector = document.querySelector('select[data-section="outputs"]');
    if (!outputSelector || !outputSelector.value) {
        throw new Error('No output field selected');
    }
    
    // Get field info from field selector
    const fieldInfo = window.fieldSelector?.fields?.[outputSelector.value];
    if (!fieldInfo) {
        throw new Error('Output field not found in field mapping');
    }
    
    return {
        field: fieldInfo.db_field,
        table: fieldInfo.db_table,
        display_name: fieldInfo.display_name
    };
}
```

#### 3. Modified LLM Execution
**File**: `app/static/js/enhanced_llm_message_manager.js`
**Function**: Replace `executeLLMRequest()` method

```javascript
async executeLLMRequest(message) {
    const pathParts = window.location.pathname.split('/');
    const postId = pathParts[3];
    const stage = pathParts[4];
    const substage = pathParts[5];
    
    const panel = document.querySelector('[data-current-stage]');
    const step = panel ? panel.dataset.currentStep : 'section_headings';
    
    // Get selected sections and output field mapping
    const selectedSectionIds = this.getSelectedSectionIds();
    const outputMapping = this.getOutputFieldMapping();
    
    if (selectedSectionIds.length === 0) {
        throw new Error('No sections selected for processing');
    }
    
    console.log('[ENHANCED_LLM] Processing sections:', selectedSectionIds);
    console.log('[ENHANCED_LLM] Output mapping:', outputMapping);
    
    // Show loading state
    const runBtn = document.getElementById('run-llm-btn');
    if (runBtn) {
        runBtn.textContent = `Processing ${selectedSectionIds.length} sections...`;
        runBtn.disabled = true;
    }
    
    try {
        // Use Writing stage endpoint for section-specific processing
        const response = await fetch(`/api/workflow/posts/${postId}/${stage}/${substage}/writing_llm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                step: step,
                selected_section_ids: selectedSectionIds,
                inputs: {
                    prompt: message,
                    output_field: outputMapping.field,
                    output_table: outputMapping.table
                }
            })
        });

        const data = await response.json();
        
        if (data.success) {
            alert(`LLM processing completed! Processed ${data.parameters.sections_processed.length} sections.`);
        } else {
            throw new Error(data.error || 'Unknown error');
        }
        
        return data;
    } catch (error) {
        console.error('[ENHANCED_LLM] LLM run error:', error);
        alert('LLM run failed: ' + error.message);
        throw error;
    } finally {
        if (runBtn) {
            runBtn.textContent = 'Run LLM';
            runBtn.disabled = false;
        }
    }
}
```

### Backend Changes

#### 1. Enhanced Section Processing
**File**: `app/api/workflow/routes.py`
**Function**: Replace `process_sections_sequentially()` method

```python
def process_sections_sequentially(conn, post_id, step_id, section_ids, timeout_per_section, output_field, output_table):
    """Process sections sequentially with actual LLM processing."""
    results = {}
    total_time = 0
    
    # Get LLM configuration
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT provider_type, model_name, api_base
        FROM llm_config
        WHERE is_active = true
        ORDER BY id DESC
        LIMIT 1
    """)
    config = cur.fetchone()
    if not config:
        config = {
            'provider_type': 'ollama',
            'model_name': 'llama3.1:70b',
            'api_base': 'http://localhost:11434'
        }
    
    # Get step prompts
    cur.execute("""
        SELECT prompt_template FROM workflow_step_prompt 
        WHERE step_id = %s AND prompt_type = 'task_prompt'
    """, (step_id,))
    prompt_result = cur.fetchone()
    task_prompt = prompt_result[0] if prompt_result else "Generate content for this section."
    
    for section_id in section_ids:
        start_time = datetime.now()
        
        try:
            # Get section data for context
            cur.execute("""
                SELECT section_heading, section_description, draft, ideas_to_include, facts_to_include
                FROM post_section 
                WHERE id = %s AND post_id = %s
            """, (section_id, post_id))
            section_data = cur.fetchone()
            
            if not section_data:
                raise Exception(f"Section {section_id} not found")
            
            # Build section-specific prompt
            section_prompt = f"""
{task_prompt}

Section: {section_data['section_heading']}
Description: {section_data['section_description'] or 'No description'}
Current Content: {section_data['draft'] or 'No content yet'}
Ideas to Include: {section_data['ideas_to_include'] or 'None specified'}
Facts to Include: {section_data['facts_to_include'] or 'None specified'}

Please generate content for this section.
"""
            
            # Call LLM
            import requests
            llm_request = {
                "model": config['model_name'],
                "prompt": section_prompt,
                "temperature": 0.7,
                "max_tokens": 1000,
                "stream": False
            }
            
            response = requests.post(
                f"{config['api_base']}/api/generate",
                json=llm_request,
                timeout=timeout_per_section
            )
            
            if response.status_code != 200:
                raise Exception(f"LLM request failed: {response.text}")
            
            result = response.json()
            output = result.get('response', '').strip()
            
            # Save output to specific section
            if output_table == 'post_section':
                cur.execute(f"""
                    UPDATE post_section 
                    SET {output_field} = %s 
                    WHERE id = %s AND post_id = %s
                """, (output, section_id, post_id))
            else:
                # Fallback to post_development if needed
                cur.execute(f"""
                    UPDATE post_development 
                    SET {output_field} = %s 
                    WHERE post_id = %s
                """, (output, post_id))
            
            conn.commit()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            total_time += processing_time
            
            results[section_id] = {
                "success": True,
                "result": output,
                "processing_time": processing_time,
                "section_heading": section_data['section_heading']
            }
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            total_time += processing_time
            results[section_id] = {
                "success": False,
                "error": str(e),
                "section_id": section_id,
                "processing_time": processing_time
            }
    
    return {
        "results": results,
        "summary": f"Processed {len(section_ids)} sections in {total_time:.2f} seconds",
        "total_time": total_time
    }
```

#### 2. Enhanced Writing Step Processing
**File**: `app/api/workflow/routes.py`
**Function**: Update `process_writing_step()` method

```python
def process_writing_step(post_id, stage, substage, step, section_ids, frontend_inputs):
    """Process a Writing stage step with section-specific handling."""
    try:
        conn = get_db_conn()
        step_id = get_step_id(conn, stage, substage, step)
        
        # Extract output field mapping from frontend inputs
        output_field = frontend_inputs.get('output_field') if frontend_inputs else None
        output_table = frontend_inputs.get('output_table', 'post_section') if frontend_inputs else 'post_section'
        
        if not output_field:
            raise Exception("No output field specified")
        
        # If section_ids are provided, use sequential processing
        if section_ids:
            timeout_per_section = frontend_inputs.get('timeout_per_section', 300) if frontend_inputs else 300
            
            result = process_sections_sequentially(
                conn, post_id, step_id, section_ids, timeout_per_section, 
                output_field, output_table
            )
            
            conn.close()
            
            return {
                'success': True,
                'results': result['results'],
                'summary': result['summary'],
                'parameters': {
                    'sections_processed': section_ids,
                    'timeout_per_section': timeout_per_section,
                    'output_field': output_field,
                    'output_table': output_table,
                    'total_time': result['total_time']
                }
            }
        else:
            # Fallback to standard processing if no sections specified
            result = process_step(post_id, stage, substage, step, frontend_inputs)
            conn.close()
            
            return {
                'success': True,
                'results': [{'output': result}],
                'parameters': {'sections_processed': []}
            }
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return {
            'success': False,
            'error': str(e),
            'sections_processed': section_ids if section_ids else []
        }
```

#### 3. Enhanced Writing LLM Endpoint
**File**: `app/api/workflow/routes.py`
**Function**: Update `run_writing_llm()` endpoint

```python
@bp.route('/posts/<int:post_id>/<stage>/<substage>/writing_llm', methods=['POST'])
def run_writing_llm(post_id, stage, substage):
    """Run LLM for Writing stage with section-specific processing."""
    try:
        data = request.get_json()
        step = data.get('step')
        section_ids = data.get('selected_section_ids', [])
        frontend_inputs = data.get('inputs', {})
        
        print(f"[WRITING_LLM] Processing step: {step}")
        print(f"[WRITING_LLM] Section IDs: {section_ids}")
        print(f"[WRITING_LLM] Frontend inputs: {frontend_inputs}")
        
        result = process_writing_step(post_id, stage, substage, step, section_ids, frontend_inputs)
        
        print(f"[WRITING_LLM] Result success: {result.get('success')}")
        if result.get('success'):
            print(f"[WRITING_LLM] Processed {len(result.get('parameters', {}).get('sections_processed', []))} sections")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[WRITING_LLM] Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

### Database Tables and Fields

#### 1. Primary Tables
- **`post_section`**: Main table for section data
  - `id`: Section ID (primary key)
  - `post_id`: Post ID (foreign key)
  - `section_heading`: Section title
  - `section_description`: Section description
  - `draft`: Main content field
  - `ideas_to_include`: Ideas for the section
  - `facts_to_include`: Facts for the section
  - `polished`: Polished content
  - `highlighting`: Highlighting/themes
  - `image_concepts`: Image concepts
  - `image_prompts`: Image prompts
  - `watermarking`: Watermarking info
  - `image_meta_descriptions`: Image metadata
  - `image_captions`: Image captions
  - `generated_image_url`: Generated image URL
  - `image_generation_metadata`: Image generation metadata
  - `image_id`: Image ID
  - `status`: Section status
  - `section_order`: Section order

- **`post_development`**: Post-level data (context)
  - `post_id`: Post ID (primary key)
  - `basic_idea`: Basic idea
  - `idea_scope`: Idea scope
  - `section_headings`: Master section structure (JSON)
  - `interesting_facts`: Interesting facts
  - `topics_to_cover`: Topics to cover

- **`workflow_step_entity`**: Step configuration
  - `id`: Step ID (primary key)
  - `name`: Step name
  - `config`: Step configuration (JSON)

- **`workflow_step_prompt`**: Step prompts
  - `step_id`: Step ID (foreign key)
  - `prompt_type`: Prompt type (system_prompt, task_prompt)
  - `prompt_template`: Prompt template

- **`llm_config`**: LLM configuration
  - `provider_type`: Provider type (ollama, openai, etc.)
  - `model_name`: Model name
  - `api_base`: API base URL
  - `is_active`: Active configuration flag

#### 2. Field Mapping Tables
- **`workflow_step_entity.config.settings.llm`**: Field mapping configuration
  - `user_input_mappings`: Input field mappings
  - `user_output_mapping`: Output field mapping
  - `user_context_mappings`: Context field mappings

### API Endpoints

#### 1. Writing Stage LLM Endpoint
- **URL**: `/api/workflow/posts/{post_id}/{stage}/{substage}/writing_llm`
- **Method**: POST
- **Purpose**: Process sections with LLM and save to specific output fields
- **Request Body**:
  ```json
  {
    "step": "section_headings",
    "selected_section_ids": [1, 2, 3],
    "inputs": {
      "prompt": "LLM prompt content",
      "output_field": "draft",
      "output_table": "post_section"
    }
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "results": {
      "1": {
        "success": true,
        "result": "Generated content for section 1",
        "processing_time": 2.5,
        "section_heading": "Section 1"
      }
    },
    "summary": "Processed 3 sections in 7.5 seconds",
    "parameters": {
      "sections_processed": [1, 2, 3],
      "timeout_per_section": 300,
      "output_field": "draft",
      "output_table": "post_section",
      "total_time": 7.5
    }
  }
  ```

#### 2. Section Data Endpoint
- **URL**: `/api/workflow/posts/{post_id}/sections`
- **Method**: GET
- **Purpose**: Get all sections for a post
- **Response**: Array of section objects with all fields

#### 3. Field Selection Endpoint
- **URL**: `/api/workflow/steps/{step_id}/field_selection`
- **Method**: GET/POST
- **Purpose**: Get/save field selection configuration

### File Paths Summary

#### Frontend Files
- `app/static/js/enhanced_llm_message_manager.js` - Main LLM manager
- `app/static/js/workflow/template_view.js` - Section rendering and selection
- `app/static/modules/llm_panel/js/field_selector.js` - Field selection logic

#### Backend Files
- `app/api/workflow/routes.py` - Main API routes and processing logic
- `app/workflow/routes.py` - Additional workflow routes

#### Template Files
- `app/templates/modules/llm_panel/templates/panel.html` - LLM panel template
- `app/templates/workflow/index.html` - Main workflow template

#### Configuration Files
- `docs/workflow/README.md` - Workflow documentation
- `docs/reference/workflow/sections.md` - Section system documentation

### Testing Strategy

#### 1. Frontend Testing
- Test section selection collection
- Test output field mapping
- Test API request formation
- Test progress feedback

#### 2. Backend Testing
- Test section data retrieval
- Test LLM processing per section
- Test output field saving
- Test error handling

#### 3. Integration Testing
- Test complete workflow from selection to saving
- Test multiple section processing
- Test error scenarios
- Test performance with large numbers of sections

### Implementation Priority

1. **High Priority**: Frontend section selection collection
2. **High Priority**: Backend LLM processing implementation
3. **High Priority**: Output field mapping and saving
4. **Medium Priority**: Progress feedback and error handling
5. **Medium Priority**: Performance optimization
6. **Low Priority**: Additional features (batch processing, etc.)

### Notes

- This implementation creates a parallel system to the Planning stage LLM processing
- The Planning stage endpoint (`/api/workflow/llm/direct`) remains unchanged
- The Writing stage uses a completely separate endpoint and processing logic
- Section-specific processing ensures data isolation between sections
- Output field mapping allows flexible targeting of different section fields
- Error handling ensures partial failures don't stop entire batch processing 