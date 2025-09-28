/**
 * Date Utilities Module
 * Handles all date-related calculations and formatting
 */

class DateUtils {
    static getWeekNumber(date) {
        const firstDayOfYear = new Date(date.getFullYear(), 0, 1);
        const pastDaysOfYear = (date - firstDayOfYear) / 86400000;
        return Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
    }

    static getWeekDates(weekNumber, year) {
        const firstDayOfYear = new Date(year, 0, 1);
        const firstMonday = new Date(firstDayOfYear);
        firstMonday.setDate(firstDayOfYear.getDate() + (firstDayOfYear.getDay() === 0 ? 1 : 8 - firstDayOfYear.getDay()));
        
        const weekStart = new Date(firstMonday);
        weekStart.setDate(firstMonday.getDate() + (weekNumber - 1) * 7);
        
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekStart.getDate() + 6);
        
        return { start: weekStart, end: weekEnd };
    }

    static formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }

    static getWeeksInMonth(monthStart, monthEnd) {
        // Calculate how many weeks this month spans
        const firstWeek = DateUtils.getWeekNumber(monthStart);
        const lastWeek = DateUtils.getWeekNumber(monthEnd);
        return lastWeek - firstWeek + 1;
    }

    static selectWeek(weekNumber, month) {
        // Implement week selection functionality
        // This could open a detailed view or allow scheduling posts for that week
    }
}

export default DateUtils;
