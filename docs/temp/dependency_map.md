# Function Dependency Map

## Main Entry Points
- **initializeCalendar()** (line 33) - Called on page load
- **updateCalendar()** (line 88) - Called by initializeCalendar and event handlers

## Core Dependencies

### initializeCalendar() calls:
- loadCategories()
- renderCalendarFallback()
- updateCalendar()

### updateCalendar() calls:
- getWeekNumber()
- loadCategories()
- renderCalendarFromData()
- loadCalendarContent()
- renderCalendarFallback()

### renderCalendarFromData() calls:
- getWeeksInMonth()
- selectWeek()
- renderWeekContent()

### renderWeekContent() calls:
- getPrimaryCategory()
- getPrimaryCategoryFromTags()
- formatDate()

## Data Loading Chain
1. **loadCategories()** - Loads category data
2. **loadCalendarContent()** - Loads calendar data
3. **loadWeekContent()** - Loads individual week data

## Rendering Chain
1. **renderCalendarFromData()** - Main calendar rendering
2. **renderWeekContent()** - Individual week rendering
3. **renderCalendarFallback()** - Fallback rendering

## CRUD Operations Dependencies
- All CRUD functions call **showNotification()** for user feedback
- Update functions call **updateCalendar()** to refresh display

## Drag and Drop Dependencies
- **initializeDragAndDrop()** - Sets up all drag handlers
- **handleDrop()** calls **moveItemToWeek()**
- **moveItemToWeek()** calls **updateCalendar()** to refresh

## UI Management Dependencies
- **addNewEntry()** and **saveNewEntry()** call **updateCalendar()**
- All functions use **showNotification()** for feedback

## Key Dependency Patterns

### High-Level Orchestration
- initializeCalendar() → updateCalendar() → renderCalendarFromData() → renderWeekContent()

### Data Flow
- loadCategories() → loadCalendarContent() → loadWeekContent()

### User Actions
- Any CRUD operation → updateCalendar() → renderCalendarFromData()

### Error Handling
- Any failure → renderCalendarFallback()

## Circular Dependencies
- None identified (good architecture)

## Critical Path Functions
1. **initializeCalendar()** - Entry point
2. **updateCalendar()** - Central refresh mechanism
3. **renderCalendarFromData()** - Main rendering logic
4. **renderWeekContent()** - Content rendering

## Independent Functions
- Date utilities (getWeekNumber, getWeekDates, formatDate)
- Individual CRUD operations
- Drag and drop handlers (except moveItemToWeek)
