# Calendar JavaScript Refactoring Roadmap

## Overview
This document provides a detailed technical roadmap for refactoring the 1,459-line `calendar-view.js` file into manageable, maintainable modules.

## Current State
- **File**: `/static/js/planning/calendar-view.js`
- **Size**: 1,459 lines
- **Functions**: 42 functions
- **Issues**: Monolithic structure, difficult to maintain, hard to debug

## Refactoring Goals
1. **Modularity**: Break into logical, focused modules
2. **Maintainability**: Easier to understand and modify
3. **Testability**: Individual modules can be tested separately
4. **Reusability**: Modules can be reused in other contexts
5. **Performance**: Better code organization and loading

---

## Phase 1: Analysis and Preparation

### 1.1 Function Analysis
**Duration**: 30 minutes

**Tasks**:
1. Create a complete function inventory with line numbers
2. Categorize functions by responsibility
3. Identify dependencies between functions
4. Map data flow and state management

**Technical Steps**:
```bash
# Create function inventory
grep -n "^function\|^async function" /static/js/planning/calendar-view.js > function_inventory.txt

# Analyze function sizes
grep -n "^function\|^async function" /static/js/planning/calendar-view.js | while read line; do
  echo "Function at line $line"
done
```

**Deliverables**:
- `function_inventory.txt` - Complete list of all functions
- `function_categories.md` - Functions grouped by responsibility
- `dependency_map.md` - Function call relationships

### 1.2 Create Module Structure
**Duration**: 15 minutes

**Tasks**:
1. Create directory structure for modules
2. Set up base module files
3. Define module interfaces

**Technical Steps**:
```bash
# Create module directories
mkdir -p /static/js/planning/calendar/modules
mkdir -p /static/js/planning/calendar/core
mkdir -p /static/js/planning/calendar/ui
mkdir -p /static/js/planning/calendar/api
mkdir -p /static/js/planning/calendar/utils
```

**Directory Structure**:
```
/static/js/planning/calendar/
├── calendar-main.js          # Main orchestrator
├── core/
│   ├── calendar-engine.js    # Core calendar logic
│   ├── date-utils.js         # Date manipulation
│   └── state-manager.js      # State management
├── ui/
│   ├── calendar-renderer.js  # DOM rendering
│   ├── drag-drop.js          # Drag and drop
│   └── event-handlers.js     # UI event handling
├── api/
│   ├── data-loader.js        # API calls
│   └── cache-manager.js      # Data caching
└── utils/
    ├── helpers.js            # Utility functions
    └── constants.js          # Constants and config
```

---

## Phase 2: Core Module Extraction

### 2.1 Date Utilities Module
**Duration**: 45 minutes
**File**: `/static/js/planning/calendar/utils/date-utils.js`

**Functions to Extract**:
- `getWeekNumber(date)`
- `getWeekDates(year, week)`
- `formatDate(date)`
- `getWeeksInMonth(year, month)`
- `selectWeek(weekNumber)`

**Technical Steps**:
1. Create `date-utils.js` with extracted functions
2. Add JSDoc documentation
3. Add unit tests
4. Update main file to import from module

**Code Structure**:
```javascript
/**
 * Date Utilities Module
 * Handles all date-related calculations and formatting
 */

class DateUtils {
    static getWeekNumber(date) { /* ... */ }
    static getWeekDates(year, week) { /* ... */ }
    static formatDate(date) { /* ... */ }
    static getWeeksInMonth(year, month) { /* ... */ }
    static selectWeek(weekNumber) { /* ... */ }
}

export default DateUtils;
```

### 2.2 Constants and Configuration
**Duration**: 30 minutes
**File**: `/static/js/planning/calendar/utils/constants.js`

**Content to Extract**:
- Color mappings
- Category configurations
- API endpoints
- UI constants

**Technical Steps**:
1. Extract all hardcoded values
2. Organize into logical groups
3. Add configuration validation
4. Create environment-specific configs

---

## Phase 3: API and Data Management

### 3.1 Data Loader Module
**Duration**: 60 minutes
**File**: `/static/js/planning/calendar/api/data-loader.js`

**Functions to Extract**:
- `loadCalendarData()`
- `loadIdeas()`
- `loadWeeks()`
- `loadCategories()`
- `loadSections()`

**Technical Steps**:
1. Create API abstraction layer
2. Add error handling and retry logic
3. Implement data validation
4. Add loading states and progress indicators

**Code Structure**:
```javascript
/**
 * Data Loader Module
 * Handles all API calls and data fetching
 */

class DataLoader {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.cache = new Map();
    }

    async loadCalendarData(postId) { /* ... */ }
    async loadIdeas(postId) { /* ... */ }
    async loadWeeks(year) { /* ... */ }
    // ... other methods
}

export default DataLoader;
```

### 3.2 Cache Manager Module
**Duration**: 45 minutes
**File**: `/static/js/planning/calendar/api/cache-manager.js`

**Functions to Extract**:
- Cache management logic
- Data invalidation
- Memory management

**Technical Steps**:
1. Implement LRU cache
2. Add cache expiration
3. Create cache invalidation strategies
4. Add cache statistics

---

## Phase 4: UI and Rendering

### 4.1 Calendar Renderer Module
**Duration**: 90 minutes
**File**: `/static/js/planning/calendar/ui/calendar-renderer.js`

**Functions to Extract**:
- `renderCalendarFromData()`
- `renderCalendarFallback()`
- `renderWeekContent()`
- `getPrimaryCategory()`
- `getPrimaryCategoryFromTags()`

**Technical Steps**:
1. Create DOM manipulation abstraction
2. Implement virtual DOM for performance
3. Add rendering optimizations
4. Create reusable UI components

**Code Structure**:
```javascript
/**
 * Calendar Renderer Module
 * Handles all DOM rendering and updates
 */

class CalendarRenderer {
    constructor(container) {
        this.container = container;
        this.virtualDOM = new Map();
    }

    renderCalendarFromData(data) { /* ... */ }
    renderWeekContent(weekData) { /* ... */ }
    updateWeek(weekId, data) { /* ... */ }
    // ... other methods
}

export default CalendarRenderer;
```

### 4.2 Drag and Drop Module
**Duration**: 75 minutes
**File**: `/static/js/planning/calendar/ui/drag-drop.js`

**Functions to Extract**:
- `initializeDragAndDrop()`
- `handleDragStart()`
- `handleDragOver()`
- `handleDrop()`
- `updateSectionOrder()`

**Technical Steps**:
1. Implement HTML5 drag and drop API
2. Add visual feedback during drag
3. Create drop zone validation
4. Add accessibility support

---

## Phase 5: Event Handling and State Management

### 5.1 Event Handlers Module
**Duration**: 60 minutes
**File**: `/static/js/planning/calendar/ui/event-handlers.js`

**Functions to Extract**:
- All event listener functions
- Event delegation logic
- Event cleanup

**Technical Steps**:
1. Implement event delegation
2. Add event cleanup on destroy
3. Create event bus for communication
4. Add keyboard navigation support

### 5.2 State Manager Module
**Duration**: 45 minutes
**File**: `/static/js/planning/calendar/core/state-manager.js`

**Functions to Extract**:
- State management logic
- Data synchronization
- State persistence

**Technical Steps**:
1. Implement state store
2. Add state change listeners
3. Create state persistence
4. Add state validation

---

## Phase 6: Core Calendar Engine

### 6.1 Calendar Engine Module
**Duration**: 90 minutes
**File**: `/static/js/planning/calendar/core/calendar-engine.js`

**Functions to Extract**:
- `initializeCalendar()`
- `updateCalendar()`
- `refreshCalendar()`
- `navigateToWeek()`
- `navigateToMonth()`

**Technical Steps**:
1. Create main calendar controller
2. Implement calendar navigation
3. Add calendar state management
4. Create calendar lifecycle hooks

**Code Structure**:
```javascript
/**
 * Calendar Engine Module
 * Main calendar controller and orchestrator
 */

class CalendarEngine {
    constructor(options) {
        this.options = options;
        this.state = new StateManager();
        this.renderer = new CalendarRenderer(options.container);
        this.dataLoader = new DataLoader(options.apiUrl);
    }

    async initialize() { /* ... */ }
    async update() { /* ... */ }
    async refresh() { /* ... */ }
    // ... other methods
}

export default CalendarEngine;
```

---

## Phase 7: Integration and Testing

### 7.1 Main Orchestrator
**Duration**: 45 minutes
**File**: `/static/js/planning/calendar/calendar-main.js`

**Tasks**:
1. Create main entry point
2. Initialize all modules
3. Handle module communication
4. Add error boundaries

**Code Structure**:
```javascript
/**
 * Calendar Main Module
 * Entry point and module orchestrator
 */

import CalendarEngine from './core/calendar-engine.js';
import DateUtils from './utils/date-utils.js';
import DataLoader from './api/data-loader.js';
// ... other imports

class CalendarMain {
    constructor(options) {
        this.engine = new CalendarEngine(options);
    }

    async init() {
        await this.engine.initialize();
    }

    destroy() {
        this.engine.destroy();
    }
}

// Auto-initialize if postId is available
if (window.postId) {
    const calendar = new CalendarMain({
        postId: window.postId,
        container: document.getElementById('calendar-grid'),
        apiUrl: '/planning/api/calendar'
    });
    
    calendar.init();
}

export default CalendarMain;
```

### 7.2 Update HTML Template
**Duration**: 15 minutes
**File**: `/templates/planning/calendar/view.html`

**Tasks**:
1. Replace single script with module imports
2. Add module loading
3. Update error handling

**Technical Steps**:
```html
<!-- Replace single script with module imports -->
<script type="module" src="/static/js/planning/calendar/calendar-main.js"></script>
```

---

## Phase 8: Testing and Validation

### 8.1 Unit Testing
**Duration**: 120 minutes

**Tasks**:
1. Create test files for each module
2. Add test coverage reporting
3. Implement integration tests
4. Add performance benchmarks

**Test Structure**:
```
/tests/calendar/
├── unit/
│   ├── date-utils.test.js
│   ├── data-loader.test.js
│   ├── calendar-renderer.test.js
│   └── drag-drop.test.js
├── integration/
│   └── calendar-integration.test.js
└── performance/
    └── calendar-performance.test.js
```

### 8.2 Browser Testing
**Duration**: 60 minutes

**Tasks**:
1. Test in multiple browsers
2. Test with different data sets
3. Test error scenarios
4. Test performance with large datasets

---

## Phase 9: Documentation and Cleanup

### 9.1 Documentation
**Duration**: 90 minutes

**Tasks**:
1. Create API documentation
2. Add usage examples
3. Create migration guide
4. Update README

**Deliverables**:
- `API_DOCUMENTATION.md`
- `USAGE_EXAMPLES.md`
- `MIGRATION_GUIDE.md`
- `README.md`

### 9.2 Cleanup
**Duration**: 30 minutes

**Tasks**:
1. Remove old calendar-view.js file
2. Clean up unused code
3. Optimize bundle size
4. Add source maps

---

## Implementation Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1 | 45 min | None |
| Phase 2 | 75 min | Phase 1 |
| Phase 3 | 105 min | Phase 1 |
| Phase 4 | 165 min | Phase 2, 3 |
| Phase 5 | 105 min | Phase 4 |
| Phase 6 | 90 min | Phase 5 |
| Phase 7 | 60 min | Phase 6 |
| Phase 8 | 180 min | Phase 7 |
| Phase 9 | 120 min | Phase 8 |

**Total Estimated Time**: 945 minutes (15.75 hours)

---

## Risk Mitigation

### High Risk Areas
1. **Template Variable Dependencies**: Ensure all template variables are properly handled
2. **Event Handler Dependencies**: Maintain proper event cleanup
3. **State Synchronization**: Ensure state consistency across modules
4. **Performance Regression**: Monitor performance during refactoring

### Mitigation Strategies
1. **Incremental Testing**: Test after each phase
2. **Backup Strategy**: Keep original file until fully tested
3. **Rollback Plan**: Ability to revert to original implementation
4. **Performance Monitoring**: Continuous performance testing

---

## Success Criteria

### Functional Requirements
- [ ] All existing functionality preserved
- [ ] No performance regression
- [ ] All tests passing
- [ ] Cross-browser compatibility maintained

### Non-Functional Requirements
- [ ] Code maintainability improved
- [ ] Module reusability achieved
- [ ] Documentation complete
- [ ] Error handling robust

---

## Post-Refactoring Benefits

1. **Maintainability**: Easier to understand and modify individual modules
2. **Testability**: Each module can be tested independently
3. **Reusability**: Modules can be reused in other calendar implementations
4. **Performance**: Better code organization and loading strategies
5. **Debugging**: Easier to isolate and fix issues
6. **Collaboration**: Multiple developers can work on different modules
7. **Scalability**: Easier to add new features and functionality

---

## Next Steps

1. **Review and Approve**: Get approval for the roadmap
2. **Set Up Environment**: Prepare development environment
3. **Start Phase 1**: Begin with function analysis
4. **Regular Checkpoints**: Review progress after each phase
5. **Testing Strategy**: Implement comprehensive testing
6. **Documentation**: Maintain documentation throughout process

---

*This roadmap provides a structured approach to refactoring the calendar JavaScript while minimizing risk and ensuring maintainability.*
