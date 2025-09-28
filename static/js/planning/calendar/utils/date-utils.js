/**
 * Date Utilities Module
 * Handles all date-related calculations and formatting
 */

class DateUtils {
    static getWeekNumber(date) {
        // Use the same algorithm as getWeekDates for consistency
        const year = date.getFullYear();
        const jan1 = new Date(year, 0, 1);
        let daysSinceMonday = jan1.getDay(); // Sunday=0, Monday=1, ..., Saturday=6
        
        // Convert to Monday=0, Sunday=6 format like Python
        if (daysSinceMonday === 0) {
            daysSinceMonday = 6; // Sunday becomes 6
        } else {
            daysSinceMonday = daysSinceMonday - 1; // Monday=1 becomes 0, etc.
        }
        
        let firstMonday;
        if (daysSinceMonday === 6) { // Sunday
            firstMonday = new Date(jan1);
            firstMonday.setDate(jan1.getDate() - 1); // Go back 1 day to get Monday
        } else {
            firstMonday = new Date(jan1);
            firstMonday.setDate(jan1.getDate() - daysSinceMonday); // Go back to Monday
        }
        
        // Calculate week number
        const pastDaysOfYear = (date - firstMonday) / 86400000;
        return Math.floor(pastDaysOfYear / 7) + 1;
    }

    static getWeekDates(weekNumber, year) {
        // Match the Python algorithm exactly
        const jan1 = new Date(year, 0, 1);
        let daysSinceMonday = jan1.getDay(); // Sunday=0, Monday=1, ..., Saturday=6
        
        // Convert to Monday=0, Sunday=6 format like Python
        if (daysSinceMonday === 0) {
            daysSinceMonday = 6; // Sunday becomes 6
        } else {
            daysSinceMonday = daysSinceMonday - 1; // Monday=1 becomes 0, etc.
        }
        
        let firstMonday;
        if (daysSinceMonday === 6) { // Sunday
            firstMonday = new Date(jan1);
            firstMonday.setDate(jan1.getDate() - 1); // Go back 1 day to get Monday
        } else {
            firstMonday = new Date(jan1);
            firstMonday.setDate(jan1.getDate() - daysSinceMonday); // Go back to Monday
        }
        
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
