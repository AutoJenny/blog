# LLM Panel Implementation Plan

## Phase 1: Initial Display Structure

### Directory Structure
```
modules/llm_panel/
├── templates/
│   ├── panel.html             # Main template for the accordions
│   └── components/            # Reusable components
│       ├── inputs.html        # Inputs accordion
│       ├── prompt.html        # Prompt accordion
│       ├── settings.html      # Settings accordion
│       └── outputs.html       # Outputs accordion
├── static/
│   ├── css/
│   │   └── panel.css         # Styles for accordions
│   └── js/
│       ├── accordion.js       # Accordion functionality
│       └── field_selector.js  # Field mapping functionality
└── routes.py                  # Updated with template rendering
```

### Component Details

#### 1. Inputs Accordion (`inputs.html`)
- Header shows summary of all input values with field IDs
- For each input:
  - Field selector dropdown (populated by JavaScript)
  - Textarea with database field mapping
  - Data attributes for field mapping
  - Proper value display in header summary
- Field selector features:
  - Groups fields by stage/substage
  - Shows unmapped fields
  - Updates database on change
  - Handles errors gracefully

#### 2. Outputs Accordion (`outputs.html`)
- Similar structure to inputs
- Header shows summary of output values
- For each output:
  - Field selector dropdown
  - Textarea with database field mapping
  - Data attributes for mapping
  - Proper value display in header

#### 3. Settings Accordion (`settings.html`)
- Shows LLM configuration summary in header
- Displays all LLM parameters in a grid:
  - Model
  - Temperature
  - Max tokens
  - Top P
  - Frequency Penalty
  - Presence Penalty
- All fields are read-only
- Proper formatting and units

#### 4. Prompt Accordion (`prompt.html`)
- Shows first line of prompt in header
- Lists input mappings if configured
- Displays full prompt template in pre tag
- Handles both new and old config formats
- Proper syntax highlighting

### JavaScript Functionality

#### Field Selector (`field_selector.js`)
- Fetches available fields from API
- Groups fields by stage/substage
- Handles field selection changes
- Updates database mappings
- Error handling and recovery
- Proper state management

#### Accordion (`accordion.js`)
- Manages accordion open/close
- Handles transitions
- Updates icons
- Maintains state
- Proper event handling

### Implementation Steps

1. Create directory structure
2. Update routes.py with basic template rendering
3. Create panel.html main template
4. Break down accordions into components
5. Copy and adapt necessary static files

### Files to Copy from IMPORTED
- From: `modules/IMPORTED/templates/workflow/steps/planning_step.html`
  To: `modules/llm_panel/templates/panel.html`
  Purpose: Extract accordion structure and basic styling

- From: `modules/IMPORTED/static/js/workflow/main.js`
  To: `modules/llm_panel/static/js/accordion.js`
  Purpose: Extract accordion toggle functionality

- From: `modules/IMPORTED/static/css/nav.css`
  To: `modules/llm_panel/static/css/panel.css`
  Purpose: Copy relevant dark theme styles

### Initial Display Focus
- Maintain dark theme compatibility
- Keep accordion structure and animations
- Remove all functionality initially
- Preserve layout and visual hierarchy
- Keep expand/collapse functionality

### Important Notes
- DO NOT add any functionality beyond display
- DO NOT modify any files outside llm_panel module
- DO NOT change any existing routes or templates
- CHECK plan before each step
- GET explicit permission before any additional changes

### Phase 2: Field Selector Integration

1. Field Selector Features
   - Fetch available fields from API
   - Group by stage/substage
   - Handle selection changes
   - Update database mappings
   - Error handling
   - State management

2. Database Integration
   - Field mapping table
   - Update endpoints
   - Validation
   - Error handling

3. UI/UX
   - Dropdown styling
   - Loading states
   - Error messages
   - Success feedback

### Phase 3: Accordion Functionality

1. Accordion Features
   - Open/close handling
   - Icon transitions
   - State management
   - Event handling

2. Content Display
   - Value summaries
   - Field labels
   - Proper formatting
   - Error states

3. Styling
   - Dark theme
   - Transitions
   - Responsive design
   - Accessibility

### Testing & Validation

1. Field Selector
   - Field loading
   - Selection changes
   - Database updates
   - Error handling

2. Accordions
   - Open/close
   - Content display
   - State management
   - Transitions

3. Integration
   - Full workflow
   - Edge cases
   - Error conditions
   - Performance

### Documentation

1. Code Comments
   - Function documentation
   - Complex logic explanation
   - Important notes
   - TODOs

2. README Updates
   - Installation
   - Configuration
   - Usage
   - Examples

3. API Documentation
   - Endpoints
   - Parameters
   - Responses
   - Error codes 