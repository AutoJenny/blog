/**
 * Calendar Renderer Module
 * Handles all DOM rendering and updates
 * 
 * Functions to be extracted in Phase 4:
 * - renderCalendarFromData()
 * - renderCalendarFallback()
 * - renderWeekContent()
 * - getPrimaryCategory()
 * - getPrimaryCategoryFromTags()
 * 
 * Currently placeholder for future implementation
 */

/**
 * Get primary category HTML from categories array
 * @param {Array} categories - Array of category objects
 * @returns {string} HTML string for primary category
 */
function getPrimaryCategory(categories) {
    if (!categories || categories.length === 0) return '';
    
    // Look for Holiday category first
    const holidayCategory = categories.find(cat => 
        cat.name.toLowerCase().includes('holiday') || 
        cat.name.toLowerCase().includes('festival') ||
        cat.name.toLowerCase().includes('celebration')
    );
    
    if (holidayCategory) {
        return `<span class="category-tag primary" style="background-color: ${holidayCategory.color}">${holidayCategory.name}</span>`;
    }
    
    // If no holiday, use the first category
    const primaryCategory = categories[0];
    return `<span class="category-tag primary" style="background-color: ${primaryCategory.color}">${primaryCategory.name}</span>`;
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { getPrimaryCategory };
}
