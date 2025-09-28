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

/**
 * Show notification to user
 * @param {string} message - Notification message
 * @param {string} type - Notification type ('success', 'error', 'info')
 */
function showNotification(message, type = 'info') {
    // Simple notification - could be enhanced with a proper notification system
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 4px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        transition: all 0.3s ease;
    `;
    
    if (type === 'success') {
        notification.style.backgroundColor = '#10b981';
    } else if (type === 'error') {
        notification.style.backgroundColor = '#ef4444';
    } else {
        notification.style.backgroundColor = '#3b82f6';
    }
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

/**
 * Render calendar fallback when data loading fails
 * @param {number} currentYear - Current year
 * @param {number} currentWeekNumber - Current week number
 */
function renderCalendarFallback(currentYear, currentWeekNumber) {
    
    // Fallback to the original hardcoded generation
    const calendarGrid = document.getElementById('calendar-grid');
    if (!calendarGrid) {
        console.error('calendar-grid element not found!');
        return;
    }
    
    calendarGrid.innerHTML = '';
    
    // Group weeks by month
    const monthGroups = [];
    let currentMonth = -1;
    let currentGroup = [];
    
    for (let week = 1; week <= 52; week++) {
        const weekDates = DateUtils.getWeekDates(week, currentYear);
        const weekMonth = weekDates.start.getMonth();
        
        if (weekMonth !== currentMonth) {
            // New month - start a new group
            if (currentGroup.length > 0) {
                monthGroups.push(currentGroup);
            }
            currentGroup = [];
            currentMonth = weekMonth;
        }
        
        currentGroup.push(week);
    }
    
    // Add the last group
    if (currentGroup.length > 0) {
        monthGroups.push(currentGroup);
    }
    
    
    // Find the maximum number of weeks in any month
    const maxWeeks = Math.max(...monthGroups.map(group => group.length));
    
    // Set grid columns dynamically
    calendarGrid.style.gridTemplateColumns = `100px repeat(${maxWeeks}, 1fr)`;
    
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    // Create month rows
    monthGroups.forEach((weeks, groupIndex) => {
        const firstWeek = weeks[0];
        const weekDates = DateUtils.getWeekDates(firstWeek, currentYear);
        const monthName = monthNames[weekDates.start.getMonth()];
        
        
        // Month name cell
        const monthCell = document.createElement('div');
        monthCell.className = CONFIG.CSS.MONTH_CELL;
        monthCell.textContent = monthName;
        calendarGrid.appendChild(monthCell);
        
        // Create week cells for this month
        for (let i = 0; i < maxWeeks; i++) {
            const weekCell = document.createElement('div');
            weekCell.className = CONFIG.CSS.WEEK_CELL;
            
            if (i < weeks.length) {
                const week = weeks[i];
                const weekDates = DateUtils.getWeekDates(week, currentYear);
                const today = new Date();
                const isCurrentYear = today.getFullYear() === currentYear;
                const currentWeekNumber = isCurrentYear ? DateUtils.getWeekNumber(today) : 1;
                const isCurrentWeek = isCurrentYear && week === currentWeekNumber;
                
                if (isCurrentWeek) {
                    weekCell.classList.add(CONFIG.CSS.CURRENT_WEEK);
                }
                
                weekCell.innerHTML = `
                    <div class="week-dates">
                        ${weekDates.start.getDate()}-${weekDates.end.getDate()}
                    </div>
                    <div class="week-number">Week ${week}</div>
                `;
                
                // Add click handler for week selection
                weekCell.addEventListener('click', () => DateUtils.selectWeek(week, weekDates.start.getMonth()));
            } else {
                weekCell.innerHTML = '<div class="week-dates">-</div>';
            }
            
            calendarGrid.appendChild(weekCell);
        }
    });
    
}

// Export for use in other modules
export { getPrimaryCategory, getPrimaryCategoryFromTags, showNotification, renderCalendarFallback };
