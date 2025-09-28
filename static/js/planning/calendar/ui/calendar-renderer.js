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

import DateUtils from '../utils/date-utils.js';
import CONFIG from '../utils/constants.js';

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

/**
 * Render calendar from database data
 * @param {Array} weeks - Array of week objects from database
 * @param {number} currentWeekNumber - Current week number
 */
function renderCalendarFromData(weeks, currentWeekNumber) {
    
    const calendarGrid = document.getElementById('calendar-grid');
    if (!calendarGrid) {
        console.error('Calendar grid not found in renderCalendarFromData');
        return;
    }
    
    calendarGrid.innerHTML = '';
    
    // Group weeks by month
    const monthGroups = {};
    weeks.forEach(week => {
        if (!monthGroups[week.month_name]) {
            monthGroups[week.month_name] = [];
        }
        monthGroups[week.month_name].push(week);
    });
    
    
    // Find the maximum number of weeks in any month
    const maxWeeks = Math.max(...Object.values(monthGroups).map(group => group.length));
    
    // Set grid columns dynamically
    calendarGrid.style.gridTemplateColumns = `100px repeat(${maxWeeks}, 1fr)`;
    
    // Create month rows in chronological order
    const monthOrder = CONFIG.MONTHS;
    const sortedMonths = monthOrder.filter(month => monthGroups[month]);
    
    sortedMonths.forEach(monthName => {
        const monthWeeks = monthGroups[monthName];
        
        // Month name cell
        const monthCell = document.createElement('div');
        monthCell.className = CONFIG.CSS.MONTH_CELL;
        monthCell.textContent = monthName;
        calendarGrid.appendChild(monthCell);
        
        // Create week cells for this month
        for (let i = 0; i < maxWeeks; i++) {
            const weekCell = document.createElement('div');
            weekCell.className = CONFIG.CSS.WEEK_CELL;
            
            if (i < monthWeeks.length) {
                const week = monthWeeks[i];
                const isCurrentWeek = week.is_current_week;
                
                if (isCurrentWeek) {
                    weekCell.classList.add(CONFIG.CSS.CURRENT_WEEK);
                }
                
                // Add data-week attribute for content loading
                weekCell.setAttribute('data-week', week.week_number);
                
                weekCell.innerHTML = `
                    <div class="week-number">W${week.week_number}</div>
                    <div class="week-dates">${DateUtils.formatDate(week.start_date)} - ${DateUtils.formatDate(week.end_date)}</div>
                    <div class="week-content">
                        <!-- Ideas and events will be loaded here -->
                    </div>
                    <div class="week-actions">
                        <button class="btn-add-entry" onclick="addNewEntry(${week.week_number})" title="Add new entry">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                `;
                
                // Add click handler for week selection
                weekCell.addEventListener('click', () => DateUtils.selectWeek(week.week_number, week.month_name));
            } else {
                weekCell.innerHTML = '<div class="week-dates">-</div>';
            }
            
            calendarGrid.appendChild(weekCell);
        }
    });
    
}

/**
 * Render idea item HTML
 * @param {Object} idea - Idea object
 * @param {Array} categories - Array of category objects
 * @param {boolean} isScheduled - Whether the idea is already scheduled
 * @returns {string} HTML string for idea item
 */
function renderIdeaItem(idea, categories, isScheduled) {
    if (isScheduled) {
        return ''; // Skip scheduled ideas
    }
    
    const primaryCategory = getPrimaryCategoryFromTags(idea.tags, categories);
    
    return `
        <div class="idea-item ${idea.priority === 'mandatory' ? 'mandatory' : ''}" data-idea-id="${idea.id}" draggable="true">
            <div class="idea-content">
                <div class="idea-title">${idea.idea_title}</div>
                <div class="idea-categories">
                    <select class="category-select" onchange="updateIdeaCategory(${idea.id}, this.value)" title="Change category" data-category-color="${primaryCategory.color}" style="background-color: ${primaryCategory.name ? primaryCategory.color : '#6b7280'}; color: white; border-color: ${primaryCategory.name ? primaryCategory.color : '#6b7280'};">
                        <option value="" ${!primaryCategory.name ? 'selected' : ''}>Select Category</option>
                        ${categories.length > 0 ? categories.map(cat => {
                            const isSelected = cat.name === primaryCategory.name;
                            return `<option value="${cat.name}" ${isSelected ? 'selected' : ''}>${cat.name}</option>`;
                        }).join('') : '<option value="">No categories loaded</option>'}
                    </select>
                </div>
            </div>
            <div class="idea-actions">
                <select class="priority-select" onchange="updateIdeaPriority(${idea.id}, this.value)" title="Set priority">
                    <option value="random" ${idea.priority === 'mandatory' ? '' : 'selected'}>Random</option>
                    <option value="mandatory" ${idea.priority === 'mandatory' ? 'selected' : ''}>Mandatory</option>
                </select>
                <button class="btn-edit" onclick="editIdea(${idea.id})" title="Edit idea">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn-delete" onclick="deleteIdea(${idea.id})" title="Delete idea">
                    <i class="fas fa-trash"></i>
                </button>
                <button class="btn-schedule" onclick="scheduleIdea(${idea.id})" title="Schedule this idea">
                    <i class="fas fa-calendar-plus"></i>
                </button>
            </div>
        </div>
    `;
}

/**
 * Render event item HTML
 * @param {Object} event - Event object
 * @param {Array} categories - Array of category objects
 * @param {boolean} isScheduled - Whether the event is already scheduled
 * @returns {string} HTML string for event item
 */
function renderEventItem(event, categories, isScheduled) {
    if (isScheduled) {
        return ''; // Skip scheduled events
    }
    
    const primaryCategory = getPrimaryCategoryFromTags(event.tags, categories);
    
    return `
        <div class="event-item ${event.priority === 'mandatory' ? 'mandatory' : ''}" data-event-id="${event.id}" draggable="true">
            <div class="event-content">
                <div class="event-title">${event.event_title}</div>
                <div class="event-categories">
                    <select class="category-select" onchange="updateEventCategory(${event.id}, this.value)" title="Change category" data-category-color="${primaryCategory.color}" style="background-color: ${primaryCategory.name ? primaryCategory.color : '#6b7280'}; color: white; border-color: ${primaryCategory.name ? primaryCategory.color : '#6b7280'};">
                        <option value="" ${!primaryCategory.name ? 'selected' : ''}>Select Category</option>
                        ${categories.length > 0 ? categories.map(cat => {
                            const isSelected = cat.name === primaryCategory.name;
                            return `<option value="${cat.name}" ${isSelected ? 'selected' : ''}>${cat.name}</option>`;
                        }).join('') : '<option value="">No categories loaded</option>'}
                    </select>
                </div>
            </div>
            <div class="event-actions">
                <select class="priority-select" onchange="updateEventPriority(${event.id}, this.value)" title="Set priority">
                    <option value="random" ${event.priority === 'mandatory' ? '' : 'selected'}>Random</option>
                    <option value="mandatory" ${event.priority === 'mandatory' ? 'selected' : ''}>Mandatory</option>
                </select>
                <button class="btn-edit" onclick="editEvent(${event.id})" title="Edit event">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn-delete" onclick="deleteEvent(${event.id})" title="Delete event">
                    <i class="fas fa-trash"></i>
                </button>
                <button class="btn-schedule" onclick="scheduleEvent(${event.id})" title="Schedule this event">
                    <i class="fas fa-calendar-plus"></i>
                </button>
            </div>
        </div>
    `;
}

/**
 * Render schedule item HTML
 * @param {Object} item - Schedule item object
 * @returns {string} HTML string for schedule item
 */
function renderScheduleItem(item) {
    const title = item.idea_title || item.event_title || item.post_title || 'Scheduled Item';
    
    return `
        <div class="schedule-item ${item.priority === 'mandatory' ? 'mandatory' : ''}" data-schedule-id="${item.id}" draggable="true">
            <div class="schedule-content">
                <div class="schedule-title">${title}</div>
            </div>
            <div class="schedule-actions">
                <select class="priority-select" onchange="updateSchedulePriority(${item.id}, this.value)" title="Set priority">
                    <option value="random" ${item.priority === 'random' ? 'selected' : ''}>Random</option>
                    <option value="mandatory" ${item.priority === 'mandatory' ? 'selected' : ''}>Mandatory</option>
                </select>
                <button class="btn-edit" onclick="editSchedule(${item.id})" title="Edit schedule">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn-delete" onclick="deleteSchedule(${item.id})" title="Delete schedule">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;
}

// Export for use in other modules
export { getPrimaryCategory, getPrimaryCategoryFromTags, showNotification, renderCalendarFallback, renderCalendarFromData, renderIdeaItem, renderEventItem, renderScheduleItem };
