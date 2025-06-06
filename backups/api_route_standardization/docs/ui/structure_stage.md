# Structure Stage UI/UX Documentation

## Overview
The Structure Stage provides an interface for planning and organizing blog post sections, including drag-and-drop functionality for section reordering and item assignment.

## User Interface Components

### 1. Inputs Panel
- **Title Input**: Text field for post title
- **Basic Idea Textarea**: Multi-line input for the post's main idea
- **Interesting Facts Textarea**: Multi-line input for facts to include

### 2. LLM Action Panel
- **Input Selection**: Checkboxes to select which inputs to use
- **Plan Sections Button**: Triggers LLM to generate section structure

### 3. Sections Panel
- **Section List**: Drag-and-drop list of sections
- **Section Items**:
  - Title (editable)
  - Description (editable)
  - Ideas (draggable tags)
  - Facts (draggable tags)
  - Remove buttons for items

### 4. Unassigned Items Panel
- **Ideas Section**: Container for unassigned ideas
- **Facts Section**: Container for unassigned facts

### 5. Save/Accept Panel
- **Accept Structure Button**: Saves the current structure

## User Flows

### 1. Initial Load
1. Page loads with existing post data
2. Input fields are pre-populated
3. Existing sections are displayed if any
4. Unassigned items are shown in their panel

### 2. Planning Sections
1. User reviews/edits input fields
2. User selects which inputs to use
3. User clicks "Plan Sections"
4. Loading state is shown
5. LLM generates section structure
6. Sections are displayed in the list

### 3. Editing Sections
1. User can edit section titles inline
2. User can edit section descriptions
3. User can drag sections to reorder
4. User can drag items between sections
5. User can remove items from sections

### 4. Managing Unassigned Items
1. Unassigned items appear in their panel
2. User can drag items to sections
3. User can drag items between sections
4. User can remove items

### 5. Saving Structure
1. User clicks "Accept Structure"
2. Validation runs:
   - All sections have titles
   - All items are assigned
3. If validation passes:
   - Structure is saved
   - User is redirected to next stage
4. If validation fails:
   - Error message is shown
   - User can fix issues

## Interaction Patterns

### Drag and Drop
- **Section Reordering**:
  - Drag handle on the right
  - Visual feedback during drag
  - Smooth animation
- **Item Assignment**:
  - Drag from unassigned to sections
  - Drag between sections
  - Visual feedback for valid drop targets

### Inline Editing
- **Title Editing**:
  - Click to edit
  - Enter to save
  - Esc to cancel
- **Description Editing**:
  - Click to edit
  - Multi-line support
  - Auto-expand as needed

### Validation
- **Real-time Validation**:
  - Required fields
  - Item assignment
  - Section order
- **Error Messages**:
  - Clear and specific
  - Near the relevant field
  - Actionable

## Responsive Design
- **Desktop**:
  - Full layout
  - Side-by-side panels
  - Drag-and-drop support
- **Tablet**:
  - Stacked panels
  - Touch-friendly drag-and-drop
- **Mobile**:
  - Single column layout
  - Touch-optimized controls
  - Simplified interactions

## Accessibility
- **Keyboard Navigation**:
  - Tab through fields
  - Arrow keys for drag-and-drop
  - Enter/Space for actions
- **Screen Reader Support**:
  - ARIA labels
  - Role attributes
  - Live regions for updates
- **Color Contrast**:
  - WCAG 2.1 compliant
  - High contrast mode support

## Error States
- **Input Validation**:
  - Required fields
  - Format validation
  - Length limits
- **API Errors**:
  - Network issues
  - Server errors
  - Timeout handling
- **LLM Errors**:
  - Generation failures
  - Invalid output
  - Retry mechanism

## Loading States
- **Initial Load**:
  - Skeleton screens
  - Progress indicators
- **Action Loading**:
  - Button states
  - Disabled controls
  - Loading spinners
- **Save Progress**:
  - Progress bar
  - Status messages
  - Success/error states

## Success States
- **Save Success**:
  - Success message
  - Progress to next stage
  - Confirmation dialog
- **Item Assignment**:
  - Visual feedback
  - Animation
  - Status update

## Future Enhancements
1. **Undo/Redo**:
   - Action history
   - Keyboard shortcuts
   - Visual indicators
2. **Bulk Operations**:
   - Multi-select
   - Batch assignment
   - Mass editing
3. **Templates**:
   - Save structures
   - Apply templates
   - Share templates
4. **Analytics**:
   - Usage tracking
   - Performance metrics
   - User behavior analysis 