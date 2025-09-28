/**
 * Constants and Configuration Module
 * Contains all constants, configurations, and settings
 */

const CONFIG = {
    API: {
        CATEGORIES: '/planning/api/calendar/categories',
        CALENDAR_DATA: '/planning/api/calendar/weeks',
        IDEAS: '/planning/api/calendar/ideas',
        EVENTS: '/planning/api/calendar/events',
        SCHEDULE: '/planning/api/calendar/schedule'
    },
    UI: {
        CALENDAR_GRID: 'calendar-grid',
        CURRENT_YEAR: 'current-year',
        CURRENT_WEEK: 'current-week',
        PREV_YEAR: 'prev-year',
        NEXT_YEAR: 'next-year'
    },
    CSS: {
        MONTH_CELL: 'month-cell',
        WEEK_CELL: 'week-cell',
        CURRENT_WEEK: 'current-week',
        WEEK_NUMBER: 'week-number',
        WEEK_DATES: 'week-dates',
        WEEK_CONTENT: 'week-content'
    },
    DATE_FORMATTING: {
        LOCALE: 'en-US',
        OPTIONS: { month: 'short', day: 'numeric' }
    },
    MONTHS: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    WINDOW: {
        CURRENT_STAGE: 'calendar',
        CURRENT_SUBSTAGE: 'view'
    },
    MESSAGES: {
        CATEGORIES_ERROR: 'Error loading categories:',
        CALENDAR_ERROR: 'Error loading calendar data or no weeks found:',
        CALENDAR_LOAD_ERROR: 'Error loading calendar data:',
        CRITICAL_GRID_ERROR: 'CRITICAL: calendar-grid element not found!',
        CALENDAR_GRID_ERROR: 'Calendar grid not found in renderCalendarFromData',
        CATEGORIES_NOT_LOADED: 'Categories not loaded yet, loading now...'
    }
};

export default CONFIG;
