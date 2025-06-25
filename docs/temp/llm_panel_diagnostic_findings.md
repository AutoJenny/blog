# LLM Panel Diagnostic Findings

## Phase 0.1: Target Identification

### 1. Outputs Component

**Current Location:** `app/templates/modules/llm_panel/templates/components/outputs.html`

**HTML Structure:**
```html
<div class="accordion-item">
    <!-- Accordion Header -->
    <button class="accordion-header">
        <span>Outputs</span>
        <span id="outputs-summary">...</span>
        <svg id="outputs-icon">...</svg>
    </button>
    
    <!-- Accordion Content -->
    <div id="outputs-content">
        <!-- For each output -->
        <div class="mb-4">
            <label>Output</label>
            <select class="field-selector" data-target="[output_id]" data-section="outputs">...</select>
            <textarea id="[output_id]" data-db-field="[field]" data-db-table="[table]">...</textarea>
        </div>
    </div>
</div>
```

**Unique Identifiers:**
1. IDs:
   - `outputs-summary`: Displays condensed output values
   - `outputs-icon`: Accordion toggle icon
   - `outputs-content`: Main content container
   - Dynamic IDs: Each output field gets unique `[output_id]`

2. Classes:
   - `accordion-item`: Container
   - `accordion-header`: Toggle button
   - `field-selector`: Field selection dropdown
   - Various utility classes for styling

**Data Attributes:**
1. On Select Elements:
   - `data-target`: Links to output ID
   - `data-section`: Always "outputs"
   - `data-current-substage`: Current workflow substage

2. On Textarea Elements:
   - `data-db-field`: Database field name
   - `data-db-table`: Database table name

**Template Variables:**
1. Configuration:
   - `step_config.outputs`: Dictionary of output configurations
   - `output_values`: Dictionary of current values
   - `current_substage`: Current workflow substage

2. Per Output:
   - `output_id`: Unique identifier
   - `output_config.db_field`: Database field
   - `output_config.db_table`: Database table
   - `output_config.placeholder`: Input placeholder

**Visual Location:**
- Appears as an accordion panel in the workflow UI
- Contains field selector dropdowns and textareas
- Shows output summary in header when collapsed
- Expands to show full interface when clicked

**Next Steps:**
1. Need to examine the inputs component
2. Need to examine the panel base template
3. Need to verify if this is indeed the active template being used

Would you like me to proceed with examining the inputs component next? 