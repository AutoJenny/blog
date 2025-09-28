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

/**
 * Get primary category from tags array (for ideas/events)
 * @param {Array} tags - Array of tag strings
 * @param {Array} categories - Array of category objects
 * @returns {Object} Object with name and color properties
 */
function getPrimaryCategoryFromTags(tags, categories) {
    if (!tags || tags.length === 0) {
        return { name: '', color: '#6b7280' };
    }
    
    // Look for Holiday category first
    const holidayTag = tags.find(tag => 
        tag.toLowerCase().includes('holiday') || 
        tag.toLowerCase().includes('festival') ||
        tag.toLowerCase().includes('celebration')
    );
    
    const categoryName = holidayTag || tags[0] || '';
    
    // Find the category in our loaded categories
    const category = categories.find(cat => cat.name === categoryName);
    
    // If no exact match, try case-insensitive match
    if (!category) {
        const caseInsensitiveCategory = categories.find(cat => 
            cat.name.toLowerCase() === categoryName.toLowerCase()
        );
        if (caseInsensitiveCategory) {
            return {
                name: caseInsensitiveCategory.name,
                color: caseInsensitiveCategory.color
            };
        }
    }
    
    return {
        name: categoryName,
        color: category ? category.color : '#6b7280'
    };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { getPrimaryCategory, getPrimaryCategoryFromTags };
}
