# Function Categories Analysis

## Core Calendar Functions (8 functions)
- `initializeCalendar()` - Main initialization (line 33)
- `updateCalendar()` - Calendar refresh logic (line 88)
- `renderCalendarFromData()` - Database-driven rendering (line 127)
- `renderCalendarFallback()` - Fallback rendering (line 498)
- `getWeeksInMonth()` - Calendar navigation (line 600)
- `selectWeek()` - Week selection (line 607)
- `loadCalendarContent()` - Calendar data loading (line 207)
- `loadWeekContent()` - Week data loading (line 216)

## Date Utilities (3 functions)
- `getWeekNumber()` - Date calculation (line 63)
- `getWeekDates()` - Date calculation (line 69)
- `formatDate()` - Date formatting (line 83)

## Rendering Functions (3 functions)
- `renderWeekContent()` - Week content rendering (line 287)
- `getPrimaryCategory()` - Category determination (line 617)
- `getPrimaryCategoryFromTags()` - Tag-based category (line 637)

## Data Management Functions (6 functions)
- `loadCategories()` - Category loading (line 18)
- `updateIdeaCategory()` - Idea category update (line 669)
- `updateEventCategory()` - Event category update (line 713)
- `updateIdeaPriority()` - Idea priority update (line 1083)
- `updateEventPriority()` - Event priority update (line 1116)
- `updateSchedulePriority()` - Schedule priority update (line 1149)

## CRUD Operations - Ideas (4 functions)
- `editIdea()` - Idea editing (line 758)
- `updateIdeaTitle()` - Idea title update (line 815)
- `deleteIdea()` - Idea deletion (line 844)
- `scheduleIdea()` - Idea scheduling (line 869)

## CRUD Operations - Events (4 functions)
- `editEvent()` - Event editing (line 876)
- `updateEventTitle()` - Event title update (line 933)
- `deleteEvent()` - Event deletion (line 962)
- `scheduleEvent()` - Event scheduling (line 987)

## CRUD Operations - Schedule (3 functions)
- `editSchedule()` - Schedule editing (line 994)
- `updateScheduleTitle()` - Schedule title update (line 1051)
- `deleteSchedule()` - Schedule deletion (line 1058)

## Drag and Drop Functions (6 functions)
- `initializeDragAndDrop()` - Drag initialization (line 1235)
- `handleDragStart()` - Drag start handler (line 1245)
- `handleDragEnd()` - Drag end handler (line 1270)
- `handleDragOver()` - Drag over handler (line 1291)
- `handleDragEnter()` - Drag enter handler (line 1296)
- `handleDragLeave()` - Drag leave handler (line 1303)
- `handleDrop()` - Drop handler (line 1310)
- `moveItemToWeek()` - Item movement (line 1328)

## UI Management Functions (3 functions)
- `showNotification()` - Notification display (line 1189)
- `addNewEntry()` - New entry creation (line 1366)
- `saveNewEntry()` - New entry saving (line 1414)

## Summary
- **Total Functions**: 42
- **Core Calendar**: 8 functions
- **Date Utilities**: 3 functions
- **Rendering**: 3 functions
- **Data Management**: 6 functions
- **CRUD Operations**: 11 functions (Ideas: 4, Events: 4, Schedule: 3)
- **Drag and Drop**: 8 functions
- **UI Management**: 3 functions
