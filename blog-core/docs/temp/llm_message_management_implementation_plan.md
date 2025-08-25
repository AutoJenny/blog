# LLM Message Management Implementation Plan

## Current Status Summary

### ✅ COMPLETED PHASES:
- **Phase 1.5: Working Mockup** - Fully implemented with all UI features
- **Phase 2: UI Structure Enhancement** - Section selector, categorized sections, instruction buttons
- **Phase 3: Field Population and Management** - Partial: Task prompt gets real data, others are hard-coded
- **Phase 3.5: Real Content Display** - ✅ COMPLETE: Replace hard-coded content with actual database content
- **Phase 3.6: Section-Specific Input Fields** - ✅ COMPLETE: Filter input fields based on selected section, load section-specific content
- **Phase 4: Drag & Drop Implementation** - SortableJS integration, reordering, visual feedback
- **Phase 5: Instructional Text System** - Instruction templates, management, styling
- **Phase 6: Live Preview Assembly** - Assembly logic, real-time updates, preview features

### ❌ REMAINING PHASES:
- **Phase 7: Persistence and Integration** - Save/load functionality, system integration, error handling
- **Phase 8: Testing and Refinement** - Comprehensive testing, UX testing, final refinements

### 🎯 NEXT PRIORITY:
**Phase 7: Persistence and Integration** - Now that real content is displayed and section-specific filtering works, the enhanced modal needs persistence and integration with the existing LLM run functionality to be fully functional.

### CURRENT STATUS:
- **System Prompt**: ✅ Gets actual content from saved prompts API or textarea
- **Basic Idea**: ✅ Gets real basic_idea from post_development table
- **Section Headings**: ✅ Gets real section_headings from post_development table
- **Idea Scope**: ✅ Gets real idea_scope from post_development table
- **Task Prompt**: ✅ Gets actual task prompt from saved prompts API
- **Settings**: ✅ Gets actual LLM settings from purple panel
- **Input/Output Fields**: ✅ Populated with real field mappings
- **Section Selector**: ✅ Populated with actual section titles from post sections API
- **Section-Specific Input Fields**: ✅ Filter input fields based on selected section, load section-specific content
- **Preview Assembly**: ✅ Section-specific input fields now appear in preview with field labels
- **Draft Content**: ✅ Fixed content loading from section-specific data, added debugging
- **Field Content Loading**: ✅ Fixed post_section field content loading with proper fallbacks

## Overview
Transform the existing "Context Management" modal into a comprehensive "LLM Message Management" interface that allows users to organize, reorder, and customize LLM message assembly with drag & drop functionality and instructional text.

## Current State Analysis

### Research Phase
- [x] **Document current modal functionality**
  - [x] Test modal open/close behavior
  - [x] Verify button triggers work correctly
  - [x] Check existing field selector population
  - [x] Document current data flow and assembly logic
  - [x] Identify all existing event handlers and dependencies

- [x] **Map existing field sources**
  - [x] Context panel fields: `system_prompt`, `context_basic_idea`, `context_section_headings`, `context_idea_scope`
  - [x] Task panel fields: `task_prompt`
  - [x] Inputs panel fields: Dynamic from `#inputs-container .input-field-group`
  - [x] Outputs panel fields: Dynamic from `#outputs-container` elements
  - [x] Document field ID patterns and data attributes

- [x] **Analyze existing ContextManager class**
  - [x] Review current `context_manager.js` functionality
  - [x] Document existing save/load mechanisms
  - [x] Identify current preview assembly logic
  - [x] Map existing API endpoints and data structures

- [x] **Test current persistence system**
  - [x] Verify existing configuration save/load works
  - [x] Test current API endpoints: `/api/workflow/steps/{step_id}/context-config`
  - [x] Document current data format and structure

### Planning Phase
- [x] **Design data structure for enhanced functionality**
  - [x] Define message elements structure with sections (context, task, inputs, outputs)
  - [x] Plan instructional text data format
  - [x] Design exclude/enable toggle system
  - [x] Plan drag & drop order persistence

- [x] **Design UI layout and interactions**
  - [x] Create detailed wireframe of new modal layout
  - [x] Plan section selector dropdown behavior
  - [x] Design drag & drop visual feedback
  - [x] Plan instructional text creation and editing UX

- [x] **Plan integration strategy**
  - [x] Identify minimal changes to preserve existing functionality
  - [x] Plan progressive enhancement approach
  - [x] Design fallback mechanisms for each new feature
  - [x] Plan testing strategy for each phase

## Research Findings

### Current State Analysis
1. **Modal Structure**: The modal is currently a simple two-panel layout with "Prompt Preview" on the left and "Current Prompt" on the right
2. **ContextManager Class**: Currently only shows prompt from Prompt panel, no context sections
3. **Field Sources**: 
   - Context panel: system_prompt, context_basic_idea, context_section_headings, context_idea_scope
   - Task panel: task_prompt (from prompt.html component)
   - Inputs panel: Dynamic fields from #inputs-container
   - Outputs panel: Dynamic fields from #outputs-container
4. **Current Limitations**: 
   - No section selector dropdown
   - No categorized sections in left panel
   - No drag & drop functionality
   - No instructional text system
   - No field exclusion toggles
   - Only shows prompt from Prompt panel, not actual field content

### Required Enhancements
1. **Section Selector**: Add dropdown to switch between Context, Task, Inputs, Outputs sections
2. **Categorized Sections**: Replace "Prompt Preview" with structured sections showing actual field content
3. **Field Detection**: Dynamically detect and populate fields from all panels
4. **Drag & Drop**: Implement SortableJS for reordering within sections
5. **Instructional Text**: Add "Add Instruction" buttons and editable text areas
6. **Exclusion Toggles**: Add checkboxes to enable/disable individual fields
7. **Live Preview**: Real-time assembly of enabled fields and instructions
8. **Persistence**: Save/load configurations per workflow step

## Mockup Implementation Summary

### ✅ COMPLETED: Working Enhanced Modal Mockup

**Files Created:**
- `app/templates/modules/llm_panel/templates/enhanced_llm_message_modal.html` - Complete modal template with all features
- `app/static/js/enhanced_llm_message_manager.js` - Demonstration JavaScript with full functionality

**Features Implemented:**
1. **Section Selector Dropdown**: ✅ Working dropdown to switch between Context, Task, Inputs, Outputs
2. **Categorized Sections**: ✅ Structured sections with proper styling and organization
3. **Field Elements**: ✅ Sample field elements with toggles, edit buttons, and drag handles
4. **Instructional Text**: ✅ Green-styled instruction elements with add/remove functionality
5. **Live Preview**: ✅ Real-time assembly of enabled elements with character count
6. **Copy to Clipboard**: ✅ Working copy functionality with visual feedback
7. **Element Editing**: ✅ Inline editing with textarea replacement
8. **Save/Load Placeholders**: ✅ Button feedback for save and run operations

**Integration Status:**
- ✅ Modal included in panel template
- ✅ JavaScript loaded and initialized
- ✅ Preserves existing modal functionality
- ✅ Tested on workflow page: `http://localhost:5000/workflow/posts/1/planning/idea`

**Visual Design:**
- ✅ Dark theme consistent with existing UI
- ✅ Color-coded sections (Context=blue, Task=green, Inputs=yellow, Outputs=purple)
- ✅ Instructional text elements have distinct green styling
- ✅ Drag handles and edit buttons clearly visible
- ✅ Responsive layout with proper spacing

**Next Steps:**
The mockup is ready for user review and discussion. All requested features are visible and functional for demonstration purposes.

## Implementation Phases

### Phase 1: Foundation and Documentation
- [x] **Create backup of current working state**
  - [x] Commit current state to git
  - [x] Document current modal HTML structure
  - [x] Document current JavaScript functionality
  - [x] Create test cases for existing functionality

- [x] **Set up development environment**
  - [x] Create feature branch for development
  - [x] Set up testing framework for incremental testing
  - [x] Prepare rollback procedures

### Phase 1.5: Working Mockup (COMPLETED)
- [x] **Create enhanced modal template**
  - [x] Design new modal layout with section selector
  - [x] Add categorized sections (Context, Task, Inputs, Outputs)
  - [x] Include sample field elements with toggles
  - [x] Add instructional text elements with distinct styling
  - [x] Implement live preview panel with character count
  - [x] Add copy to clipboard functionality

- [x] **Create demonstration JavaScript**
  - [x] Implement section switching functionality
  - [x] Add element toggle and edit capabilities
  - [x] Create instructional text addition system
  - [x] Implement live preview assembly
  - [x] Add save/load placeholder functionality

- [x] **Integration with existing system**
  - [x] Include enhanced modal in panel template
  - [x] Load demonstration JavaScript
  - [x] Preserve existing modal functionality
  - [x] Test modal open/close behavior

### Phase 2: UI Structure Enhancement
- [x] **Add section selector dropdown**
  - [x] Add dropdown to modal header
  - [x] Implement section switching logic
  - [x] Test section visibility toggles

- [x] **Create categorized sections in left panel**
  - [x] Replace hardcoded "Prompt Preview" with structured sections
  - [x] Add Context section with field elements
  - [x] Add Task section with field elements
  - [x] Add Inputs section with dynamic field detection
  - [x] Add Outputs section with dynamic field detection

- [x] **Add "Add Instruction" buttons**
  - [x] Add instruction buttons to each section
  - [x] Create instruction creation logic
  - [x] Test instruction element creation

### Phase 3: Field Population and Management
- [x] **Implement field detection logic**
  - [x] Create function to detect all available fields from panels
  - [x] Map field IDs to display names
  - [x] Handle dynamic input/output field detection
  - [x] Test field population with various panel states

- [x] **Add exclude/enable toggles**
  - [x] Add checkboxes to each field element
  - [x] Implement toggle functionality
  - [x] Test enable/disable behavior

- [x] **Create field element templates**
  - [x] Design field element HTML structure
  - [x] Create JavaScript template system
  - [x] Test element creation and rendering

### Phase 4: Drag & Drop Implementation
- [x] **Integrate SortableJS library**
  - [x] Verify SortableJS is available and working
  - [x] Initialize Sortable on each section container
  - [x] Test basic drag & drop functionality

- [x] **Implement reordering logic**
  - [x] Handle drag & drop events
  - [x] Update data structure on reorder
  - [x] Test order persistence within sections

- [x] **Add visual feedback**
  - [x] Implement drag handles
  - [x] Add ghost effects during drag
  - [x] Test visual feedback across different sections

### Phase 5: Instructional Text System
- [x] **Create instruction template**
  - [x] Design instruction element HTML structure
  - [x] Create editable textarea for instruction content
  - [x] Test instruction element creation

- [x] **Implement instruction management**
  - [x] Add instruction creation via "Add Instruction" buttons
  - [x] Implement instruction editing functionality
  - [x] Add instruction removal capability
  - [x] Test instruction drag & drop

- [x] **Style instructional text elements**
  - [x] Design distinct styling for instruction elements
  - [x] Implement visual differentiation from field elements
  - [x] Test styling across different sections

### Phase 6: Live Preview Assembly
- [x] **Implement assembly logic**
  - [x] Create function to assemble message from enabled elements
  - [x] Implement proper spacing and formatting
  - [x] Test assembly with various element combinations

- [x] **Add real-time updates**
  - [x] Connect assembly to element changes
  - [x] Implement live preview updates
  - [x] Test real-time functionality

- [x] **Add preview features**
  - [x] Add character count display
  - [x] Implement copy to clipboard functionality
  - [x] Test preview features

### Phase 3.5: Real Content Display
- [x] **Replace hard-coded content with actual database content**
  - [x] **System Prompt**: Get actual system prompt from saved prompts API or textarea
  - [x] **Basic Idea**: Fetch real basic_idea from post_development table
  - [x] **Section Headings**: Fetch real section_headings from post_development table  
  - [x] **Idea Scope**: Fetch real idea_scope from post_development table
  - [x] **Settings**: Get actual LLM settings from purple panel (model, temperature, etc.)
  - [x] **Input Fields**: Populate with real field mappings from inputs panel
  - [x] **Output Fields**: Populate with real field mappings from outputs panel
  - [x] **Test all content displays** with various post states

- [x] **Update content population logic**
  - [x] Modify `detectAvailableFields()` to fetch real data for all sections
  - [x] Update `updateAccordionContent()` to handle all element types
  - [x] Add error handling for missing or empty content
  - [x] Test content updates when modal is refreshed

- [x] **Remove hard-coded HTML content**
  - [x] Replace hard-coded text in modal template with dynamic placeholders
  - [x] Ensure all content is populated via JavaScript
  - [x] Test modal with empty/null content scenarios

### Phase 3.6: Section-Specific Input Fields (COMPLETED)
- [x] **Populate section selector with actual section titles**
  - [x] Update `loadPostSections()` to fetch real section data from `/api/workflow/posts/{post_id}/sections`
  - [x] Populate dropdown with section titles from API response
  - [x] Set default selection to first section when modal opens
  - [x] Test section selector with posts that have multiple sections

- [x] **Add section-specific content loading**
  - [x] Create `getSectionSpecificContent()` method to fetch individual section data
  - [x] Create `updateInputFieldsForSection()` method to filter and populate input fields
  - [x] Create `populateInputFieldsWithAllSections()` method for "All Sections" view
  - [x] Test content loading with different section selections

- [x] **Implement section filtering logic**
  - [x] Filter input fields to show only section-specific fields (post_section source)
  - [x] Load section-specific content for each field based on selected section
  - [x] Handle "All Sections" view to show all input fields
  - [x] Test filtering with various section selections

- [x] **Update event handlers and initialization**
  - [x] Update section selector change event to call filtering methods
  - [x] Update `openModal()` to initialize with selected section
  - [x] Update `refreshContext()` to maintain section selection
  - [x] Test event handling and initialization flow

- [x] **Test section-specific functionality**
  - [x] Test with posts that have multiple sections
  - [x] Test with posts that have no sections
  - [x] Test section switching and content updates
  - [x] Verify API endpoints work correctly

- [x] **Fix preview assembly for section-specific fields**
  - [x] Update `updatePreview()` to collect content from individual field elements within accordions
  - [x] Update `updateSummary()` to properly count individual field elements
  - [x] Add preview and summary updates to input field population methods
  - [x] Test that section-specific input fields appear in preview with field labels

- [x] **Fix draft content from purple dropdown**
  - [x] Move post_section fields from outputs to inputs array for Writing stage
  - [x] Update filtering logic to include all post_section fields (including draft)
  - [x] Fix field detection to properly include purple dropdown fields in preview
  - [x] Add debugging to track field detection and content loading
  - [x] Fix post_section field content loading with proper fallbacks
  - [x] Set post_section field content to null during detection, load from section data later

### Phase 7: Persistence and Integration
- [ ] **Enhance save/load functionality**
  - [ ] Extend existing save mechanism for new data structure
  - [ ] Implement load functionality for enhanced configurations
  - [ ] Test save/load with complex configurations

- [ ] **Integrate with existing systems**
  - [ ] Ensure compatibility with existing field selectors
  - [ ] Test integration with existing LLM run functionality
  - [ ] Verify backward compatibility

- [ ] **Add error handling**
  - [ ] Implement graceful fallbacks for missing elements
  - [ ] Add error handling for save/load operations
  - [ ] Test error scenarios

### Phase 8: Testing and Refinement
- [ ] **Comprehensive testing**
  - [ ] Test all functionality with various panel states
  - [ ] Test edge cases (empty panels, missing fields)
  - [ ] Test performance with large numbers of elements

- [ ] **User experience testing**
  - [ ] Test modal open/close behavior
  - [ ] Test section switching
  - [ ] Test drag & drop usability
  - [ ] Test instruction creation and editing

- [ ] **Final refinements**
  - [ ] Optimize performance
  - [ ] Improve visual design
  - [ ] Add any missing features

## Risk Mitigation

### Rollback Strategy
- [ ] **Git checkpoints**
  - [ ] Commit after each phase
  - [ ] Create feature branches for major changes
  - [ ] Maintain working state documentation

### Fallback Mechanisms
- [ ] **Preserve existing functionality**
  - [ ] Keep existing modal structure as backup
  - [ ] Maintain existing ContextManager functionality
  - [ ] Test thoroughly before removing old code

### Testing Strategy
- [ ] **Incremental testing**
  - [ ] Test each phase before proceeding
  - [ ] Verify existing functionality still works
  - [ ] Test edge cases and error scenarios

## Success Criteria

### Functional Requirements
- [ ] Modal opens and closes correctly
- [ ] All existing dropdowns populate correctly
- [ ] Section selector works and shows correct sections
- [ ] Drag & drop reordering works smoothly
- [ ] Instructional text can be created, edited, and reordered
- [ ] Live preview updates in real-time
- [ ] Save/load functionality works correctly
- [ ] Exclude toggles work properly

### User Experience Requirements
- [ ] Interface is intuitive and easy to use
- [ ] Visual feedback is clear and helpful
- [ ] Performance is acceptable with reasonable numbers of elements
- [ ] Error states are handled gracefully

### Technical Requirements
- [ ] Code is maintainable and well-documented
- [ ] Integration with existing systems is seamless
- [ ] Backward compatibility is maintained
- [ ] Performance impact is minimal

## Timeline Estimate

### Research and Planning: 1-2 days
### Phase 1-2 (Foundation): 1 day
### Phase 3-4 (Core Features): 2-3 days
### Phase 5-6 (Advanced Features): 2-3 days
### Phase 7-8 (Integration & Testing): 2-3 days

**Total Estimated Time: 8-12 days**

## Notes

- **Critical**: Preserve existing functionality at all costs
- **Incremental**: Make small, testable changes
- **Documentation**: Document each change thoroughly
- **Testing**: Test extensively before proceeding to next phase
- **Communication**: Report progress and issues regularly 