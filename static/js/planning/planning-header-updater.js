/**
 * Planning Header Updater
 * Updates the shared planning header with post ID and current week information
 * Used across all planning pages
 */

import DateUtils from './calendar/utils/date-utils.js';

class PlanningHeaderUpdater {
    constructor() {
        this.currentYear = new Date().getFullYear();
        this.currentWeekNumber = DateUtils.getWeekNumber(new Date());
    }

    /**
     * Update the planning header with post ID and week information
     * @param {number} weekNumber - The week number to display (optional, defaults to current week)
     */
    updateHeader(weekNumber = null) {
        const weekToShow = weekNumber || this.currentWeekNumber;
        
        // Get the post ID from the window object (set in each page's template)
        const postId = window.postId || 'Unknown';
        
        // Calculate the week dates for the specified week
        const weekDates = DateUtils.getWeekDates(weekToShow, this.currentYear);
        
        // Format the dates nicely
        const startDate = weekDates.start.toLocaleDateString('en-US', { 
            month: 'long', 
            day: 'numeric' 
        });
        const endDate = weekDates.end.toLocaleDateString('en-US', { 
            month: 'long', 
            day: 'numeric',
            year: 'numeric'
        });
        
        // Update the shared planning header title
        const titleElement = document.getElementById('planning-title');
        if (titleElement) {
            titleElement.textContent = `Post ID: ${postId} - ${startDate}-${endDate} (Week ${weekToShow})`;
        }
    }

    /**
     * Initialize the header updater
     * This should be called on page load
     */
    initialize() {
        // Update header immediately
        this.updateHeader();
        
        // Set up any periodic updates if needed
        // For now, we'll just update once on page load
    }
}

// Create global instance
window.planningHeaderUpdater = new PlanningHeaderUpdater();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.planningHeaderUpdater) {
        window.planningHeaderUpdater.initialize();
    }
});

// Export for module usage
export default PlanningHeaderUpdater;
