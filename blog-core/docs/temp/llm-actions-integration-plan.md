# LLM-Actions Panel Integration Plan

## Overview
This document outlines the staged integration of the purple LLM-actions microservice (port 5002) into the blog-core workflow system (port 5001) for the planning stage. The integration uses Direct API Integration approach, avoiding iframes entirely.

## Integration Goals
- Display the full purple LLM-actions interface in the 5001 workflow content area
- Maintain the purple theme from blog-llm-actions
- Support real-time updates
- Provide specific LLM actions for each planning substage (idea, research, structure)
- Use database-defined actions and field mappings

## Staged Implementation Plan

### Stage 1: Visual Integration (Foundation)
**Goal**: Get the purple LLM-actions interface displaying in the 5001 workflow content area

**Changes**:
- [x] Replace the white "Workflow Content Area" in `blog-core/templates/workflow.html` with a flexible container hierarchy
- [x] Create main `workflow-content-container` with conditional structure for different stages
- [x] Implement planning stage single-panel layout with `workflow-llm-actions` container
- [x] Remove the white background styling from `.content-area` CSS
- [x] Create a simple proxy endpoint in `blog-core/app.py` that fetches the LLM-actions HTML content
- [x] Use AJAX to load the purple LLM-actions interface into the `workflow-llm-actions` container
- [x] Ensure proper error handling for when blog-llm-actions is not available
- [x] Add placeholder structure for future multi-panel layouts (writing stage)

**Test Benchmark**: 
- Navigate to `http://localhost:5001/workflow/` 
- Should see the purple LLM-actions interface embedded in the content area
- No white background visible
- Header/navigation on 5001 remains intact
- Content loads via API call, not iframe
- Container structure is ready for future multi-panel layouts

**Files to Modify**:
- `blog-core/templates/workflow.html` (replace content area with flexible container hierarchy + AJAX)
- `blog-core/app.py` (add proxy endpoint to fetch LLM-actions content)

---

### Stage 2: Proper Workflow Navigation
**Goal**: Implement the correct workflow navigation structure

**Changes**:
- [x] Replace `nav/nav.html` with proper `nav/workflow_nav.html` in workflow template
- [x] Update route to pass correct context variables (current_stage, current_substage, current_step, current_post_id)
- [x] Ensure planning stage navigation works correctly
- [x] Verify navigation styling matches the existing header theme
- [x] Fix template endpoint references to use correct route names

**Test Benchmark**:
- Workflow navigation shows Planning/Writing/Publishing stages
- Planning substages (Idea, Research, Structure) are clickable
- URL updates correctly when navigating
- LLM-actions content still loads via API
- Navigation styling is consistent with header

**Files to Modify**:
- `blog-core/templates/workflow.html` (update navigation include)
- `blog-core/app.py` (ensure proper context variables)
- `blog-core/modules/nav/templates/nav/workflow_nav.html` (fix endpoint references)

---

### Stage 3: Context-Aware Loading
**Goal**: Make LLM-actions content load based on current stage/substage

**Changes**:
- [x] Update workflow template to pass stage/substage context to JavaScript
- [x] Update JavaScript to send context parameters to API
- [x] Update proxy endpoint to forward context to LLM-actions service
- [x] Update LLM-actions service to accept and use context parameters
- [x] Update LLM-actions template to display context information
- [x] Test context-aware loading for different stages/substages

**Test Benchmark**:
- LLM-actions content shows current stage/substage context
- Content updates when navigating between substages
- Context parameters are passed correctly through the chain
- Loading messages reflect current substage

**Files to Modify**:
- `blog-core/templates/workflow.html` (update JavaScript)
- `blog-core/app.py` (update proxy endpoint)
- `blog-llm-actions/app.py` (add context support)
- `blog-llm-actions/templates/index.html` (add context display)

---

### Stage 4: Full Functionality
**Goal**: Complete integration with real-time updates and LLM action execution

**Changes**:
- [x] Implement real-time communication between panels
- [x] Add field mapping for planning stage using database tables
- [x] Enable LLM action execution from within the integrated panel
- [x] Add comprehensive error handling and loading states
- [x] Implement proper state management for workflow context
- [x] Add success/error feedback for LLM action execution

**Test Benchmark**:
- LLM actions can be executed from within 5001
- Results update in real-time
- Field mapping works correctly for planning stage
- Error handling is robust and user-friendly
- Workflow state is maintained across navigation
- Success/error messages are clear and informative

**Files to Modify**:
- `blog-core/app.py` (enhance proxy endpoints for action execution)
- `blog-core/templates/workflow.html` (add real-time update functionality)
- `blog-llm-actions/app.py` (add field mapping endpoint)
- `blog-llm-actions/templates/index.html` (add parent window communication)
- `blog-core/app/services/shared.py` (add field mapping service)

---

## Technical Implementation Details

### Container Architecture
- **Main Container**: `workflow-content-container` with conditional stage rendering
- **Panel Containers**: 
  - `workflow-llm-actions` (purple theme, `#2D0A50` background)
  - `workflow-sections` (green theme, `#013828` background, for writing stage)
- **Layout Flexibility**: Single-panel for planning, two-panel for writing, adaptable for other stages
- **Consistent IDs**: Same container IDs across all stages for easy JavaScript targeting

### API Integration Approach
- **Proxy Endpoints**: Create endpoints in blog-core that forward requests to blog-llm-actions
- **CORS Handling**: All cross-origin requests go through blog-core
- **Error Handling**: Graceful degradation when blog-llm-actions is unavailable
- **Real-time Updates**: WebSocket or polling for live content updates

### Database Integration
- **Field Mapping**: Use existing `workflow_field_mapping` table
- **LLM Actions**: Query `llm_action` table for planning-stage actions
- **Context Storage**: Store current stage/substage in session or URL parameters

### Styling and Theme
- **Purple Theme**: Maintain `#2D0A50` background from blog-llm-actions
- **Consistent UI**: Ensure integration doesn't break existing header/navigation
- **Responsive Design**: Maintain mobile compatibility
- **Container Structure**: Flexible hierarchy supporting single-panel (planning) and multi-panel (writing) layouts

## Success Criteria
- [ ] Purple LLM-actions interface displays correctly in 5001 workflow area
- [ ] Navigation between planning substages works smoothly
- [ ] LLM actions can be executed and results displayed
- [ ] Real-time updates function properly
- [ ] Error handling is robust and user-friendly
- [ ] Performance is acceptable (no significant lag)
- [ ] Mobile responsiveness is maintained

## Rollback Plan
If issues arise at any stage:
1. Revert to previous working commit
2. Document the specific issue encountered
3. Adjust the plan based on lessons learned
4. Resume from the previous stable stage

## Notes
- Each stage should be fully tested before proceeding to the next
- Document any deviations from the plan as they occur
- Maintain clear communication about progress and any blockers
- Focus on stability and user experience at each stage 