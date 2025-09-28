import DateUtils from './calendar/utils/date-utils.js';
import CONFIG from './calendar/utils/constants.js';
import DataLoader from './calendar/api/data-loader.js';
import CacheManager from './calendar/api/cache-manager.js';
import { getPrimaryCategory, getPrimaryCategoryFromTags } from './calendar/ui/calendar-renderer.js';

// Global variables
let currentYear = new Date().getFullYear();
let currentWeekNumber = DateUtils.getWeekNumber(new Date());
let categories = [];

// Initialize API modules
const dataLoader = new DataLoader('/planning/api/calendar');
const cacheManager = new CacheManager();

document.addEventListener('DOMContentLoaded', function() {
    
    // Set current stage for navigation
    window.currentStage = CONFIG.WINDOW.CURRENT_STAGE;
    window.currentSubstage = CONFIG.WINDOW.CURRENT_SUBSTAGE;
    // postId is set in the HTML template
    
    
    // Initialize calendar
    initializeCalendar();
    
});

async function loadCategories() {
    try {
        // Check cache first
        let categoriesData = cacheManager.getCategories();
        if (!categoriesData) {
            categoriesData = await dataLoader.loadCategories();
            if (categoriesData.length > 0) {
                cacheManager.setCategories(categoriesData);
            }
        }
        categories = categoriesData;
    } catch (error) {
        console.error(CONFIG.MESSAGES.CATEGORIES_ERROR, error);
    }
}

async function initializeCalendar() {
    
    // Test if calendar grid exists
    const calendarGrid = document.getElementById(CONFIG.UI.CALENDAR_GRID);
    if (!calendarGrid) {
        console.error(CONFIG.MESSAGES.CRITICAL_GRID_ERROR);
        return;
    }
    
    // Load categories first
    await loadCategories();
    
    // Always render the fallback first to ensure calendar is visible
    renderCalendarFallback();
    
    // Then try to load from database
    updateCalendar();
    
    // Event listeners
    document.getElementById('prev-year').addEventListener('click', () => {
        currentYear--;
        updateCalendar();
    });
    
    document.getElementById('next-year').addEventListener('click', () => {
        currentYear++;
        updateCalendar();
    });
}


async function updateCalendar() {
    
    document.getElementById(CONFIG.UI.CURRENT_YEAR).textContent = currentYear;
    
    // Calculate current week for this year
    const today = new Date();
    const isCurrentYear = today.getFullYear() === currentYear;
    const weekNumber = isCurrentYear ? DateUtils.getWeekNumber(today) : 1;
    
    document.getElementById(CONFIG.UI.CURRENT_WEEK).textContent = 
        `Week ${weekNumber} of 52`;
    
    // Ensure categories are loaded before rendering content
    if (categories.length === 0) {
        await loadCategories();
    }
    
    try {
        // Check cache first
        let weeksData = cacheManager.getCalendarData(currentYear);
        if (!weeksData || weeksData.length === 0) {
            weeksData = await dataLoader.loadCalendarData(currentYear);
            if (weeksData.length > 0) {
                cacheManager.setCalendarData(currentYear, weeksData);
            }
        }
        
        if (weeksData && weeksData.length > 0) {
            renderCalendarFromData(weeksData, weekNumber);
            await loadCalendarContent(currentYear, weeksData);
        } else {
            console.error(CONFIG.MESSAGES.CALENDAR_ERROR, 'No weeks data');
            // Re-render fallback if database fails
            renderCalendarFallback();
        }
    } catch (error) {
        console.error(CONFIG.MESSAGES.CALENDAR_LOAD_ERROR, error);
        // Re-render fallback if database fails
        renderCalendarFallback();
    }
}

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

async function loadCalendarContent(year, weeks) {
    
    // Load ideas and events for each week with rate limiting
    for (let i = 0; i < weeks.length; i++) {
        const week = weeks[i];
        try {
            await loadWeekContent(year, week.week_number);
            // Add small delay to prevent overwhelming the server
            if (i < weeks.length - 1) {
                await new Promise(resolve => setTimeout(resolve, 50));
            }
        } catch (error) {
            console.error(`Failed to load content for week ${week.week_number}:`, error);
            // Continue with next week even if one fails
        }
    }
    
}

async function loadWeekContent(year, weekNumber) {
    try {
        // Check cache first
        let weekData = cacheManager.getWeekData(year, weekNumber);
        if (!weekData) {
            weekData = await dataLoader.loadWeekContent(year, weekNumber);
            if (weekData.ideas.length > 0 || weekData.events.length > 0 || weekData.schedule.length > 0) {
                cacheManager.setWeekData(year, weekNumber, weekData);
            }
        }
        
        // Render content for this week
        const weekCell = document.querySelector(`[data-week="${weekNumber}"]`);
        if (weekCell) {
            const contentDiv = weekCell.querySelector('.week-content');
            const renderedContent = renderWeekContent(weekData.ideas, weekData.events, weekData.schedule);
            contentDiv.innerHTML = renderedContent;
            
        } else {
        }
        
    } catch (error) {
        console.error(`Error loading content for week ${weekNumber}:`, error);
    }
}

function renderWeekContent(ideas, events, schedule) {
    let html = '';
    
    // Get scheduled idea IDs to mark them differently
    const scheduledIdeaIds = new Set();
    const scheduledEventIds = new Set();
    if (schedule && schedule.length > 0) {
        schedule.forEach(item => {
            if (item.idea_id) scheduledIdeaIds.add(item.idea_id);
            if (item.event_id) scheduledEventIds.add(item.event_id);
        });
    }
    
    // Render ideas
    if (ideas && ideas.length > 0) {
        html += '<div class="ideas-section">';
        ideas.forEach(idea => {
            const isScheduled = scheduledIdeaIds.has(idea.id);
            if (isScheduled) {
                // Skip perpetual ideas that are already scheduled - they'll show in the schedule section
                return;
            }
            
            
            
            const ideaHtml = `
                <div class="idea-item ${idea.priority === 'mandatory' ? 'mandatory' : ''}" data-idea-id="${idea.id}" draggable="true">
                    <div class="idea-content">
                        <div class="idea-title">${idea.idea_title}</div>
                        <div class="idea-categories">
                            <select class="category-select" onchange="updateIdeaCategory(${idea.id}, this.value)" title="Change category" data-category-color="${(() => {
                                const category = getPrimaryCategoryFromTags(idea.tags, categories);
                                return category.color;
                            })()}" style="background-color: ${(() => {
                                const category = getPrimaryCategoryFromTags(idea.tags, categories);
                                return category.name ? category.color : '#6b7280';
                            })()}; color: white; border-color: ${(() => {
                                const category = getPrimaryCategoryFromTags(idea.tags, categories);
                                return category.name ? category.color : '#6b7280';
                            })()};">
                                <option value="" ${(() => {
                                    const category = getPrimaryCategoryFromTags(idea.tags, categories);
                                    return !category.name ? 'selected' : '';
                                })()}>Select Category</option>
                                ${categories.length > 0 ? categories.map(cat => {
                                    // Get the primary category for this idea
                                    const primaryCategory = getPrimaryCategoryFromTags(idea.tags, categories);
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
            
            
            html += ideaHtml;
        });
        html += '</div>';
    }
    
    // Render events
    if (events && events.length > 0) {
        html += '<div class="events-section">';
        events.forEach(event => {
            const isScheduled = scheduledEventIds.has(event.id);
            if (isScheduled) {
                // Skip perpetual events that are already scheduled - they'll show in the schedule section
                return;
            }
            html += `
                <div class="event-item ${event.priority === 'mandatory' ? 'mandatory' : ''}" data-event-id="${event.id}" draggable="true">
                    <div class="event-content">
                        <div class="event-title">${event.event_title}</div>
                        <div class="event-categories">
                            <select class="category-select" onchange="updateEventCategory(${event.id}, this.value)" title="Change category" data-category-color="${(() => {
                                const category = getPrimaryCategoryFromTags(event.tags, categories);
                                return category.color;
                            })()}" style="background-color: ${(() => {
                                const category = getPrimaryCategoryFromTags(event.tags, categories);
                                return category.name ? category.color : '#6b7280';
                            })()}; color: white; border-color: ${(() => {
                                const category = getPrimaryCategoryFromTags(event.tags, categories);
                                return category.name ? category.color : '#6b7280';
                            })()};">
                                <option value="" ${(() => {
                                    const category = getPrimaryCategoryFromTags(event.tags, categories);
                                    return !category.name ? 'selected' : '';
                                })()}>Select Category</option>
                                ${categories.length > 0 ? categories.map(cat => {
                                    // Get the primary category for this event
                                    const primaryCategory = getPrimaryCategoryFromTags(event.tags, categories);
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
        });
        html += '</div>';
    }
    
    // Render schedule
    if (schedule && schedule.length > 0) {
        html += '<div class="schedule-section">';
        schedule.forEach(item => {
            const title = item.idea_title || item.event_title || item.post_title || 'Scheduled Item';
            html += `
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
        });
        html += '</div>';
    }
    
    return html;
}

function renderCalendarFallback() {
    
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
                    <div class="week-number">W${week}</div>
                    <div class="week-dates">${DateUtils.formatDate(weekDates.start)} - ${DateUtils.formatDate(weekDates.end)}</div>
                    <div class="week-content">
                        <!-- Posts will be loaded here -->
                    </div>
                    <div class="week-actions">
                        <button class="btn-add-entry" onclick="addNewEntry(${week})" title="Add new entry">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
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


// ============================================================================
// CALENDAR EDITING FUNCTIONS
// ============================================================================

// Helper function to get primary category (Holiday if exists, otherwise first available)


// Category update functions
async function updateIdeaCategory(ideaId, newCategory) {
    
    // Handle empty category selection
    if (!newCategory) {
        showNotification('Please select a category', 'error');
        return;
    }
    
    // Find the new category color
    const newCategoryData = categories.find(cat => cat.name === newCategory);
    const newColor = newCategoryData ? newCategoryData.color : '#6b7280';
    
    // Update the visual styling immediately
    const selectElement = document.querySelector(`[data-idea-id="${ideaId}"] .category-select`);
    if (selectElement) {
        selectElement.style.backgroundColor = newColor;
        selectElement.style.borderColor = newColor;
        selectElement.setAttribute('data-category-color', newColor);
    }
    
    try {
        const result = await dataLoader.updateIdeaCategory(ideaId, newCategory);
        showNotification(result.message, 'success');
        // Invalidate cache for this week
        cacheManager.invalidateWeek(currentYear, currentWeekNumber);
        // Reload current week's content to show updated category
        await loadWeekContent(currentYear, currentWeekNumber);
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message, 'error');
    }
}

// Make functions globally accessible immediately after definition
window.updateIdeaCategory = updateIdeaCategory;
window.editIdea = editIdea;
window.deleteIdea = deleteIdea;

async function updateEventCategory(eventId, newCategory) {
    // Handle empty category selection
    if (!newCategory) {
        showNotification('Please select a category', 'error');
        return;
    }
    
    // Find the new category color
    const newCategoryData = categories.find(cat => cat.name === newCategory);
    const newColor = newCategoryData ? newCategoryData.color : '#6b7280';
    
    // Update the visual styling immediately
    const selectElement = document.querySelector(`[data-event-id="${eventId}"] .category-select`);
    if (selectElement) {
        selectElement.style.backgroundColor = newColor;
        selectElement.style.borderColor = newColor;
        selectElement.setAttribute('data-category-color', newColor);
    }
    
    try {
        const result = await dataLoader.updateEventCategory(eventId, newCategory);
        showNotification(result.message, 'success');
        // Invalidate cache for this week
        cacheManager.invalidateWeek(currentYear, currentWeekNumber);
        // Reload current week's content to show updated category
        await loadWeekContent(currentYear, currentWeekNumber);
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message, 'error');
    }
}

// Make functions globally accessible immediately after definition
window.updateEventCategory = updateEventCategory;
window.editEvent = editEvent;
window.deleteEvent = deleteEvent;

// Idea editing functions
function editIdea(ideaId) {
    const ideaItem = document.querySelector(`[data-idea-id="${ideaId}"]`);
    if (!ideaItem) return;
    
    const titleElement = ideaItem.querySelector('.idea-title');
    const currentTitle = titleElement.textContent;
    
    // Create input field
    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentTitle;
    input.className = 'inline-edit-input';
    input.style.cssText = `
        width: 100%;
        padding: 4px 8px;
        border: 2px solid #3b82f6;
        border-radius: 4px;
        font-size: 14px;
        background: white;
    `;
    
    // Replace title with input
    titleElement.style.display = 'none';
    titleElement.parentNode.insertBefore(input, titleElement);
    input.focus();
    input.select();
    
    // Handle save
    const saveEdit = () => {
        const newTitle = input.value.trim();
        if (newTitle && newTitle !== currentTitle) {
            updateIdeaTitle(ideaId, newTitle);
        }
        // Restore original display
        input.remove();
        titleElement.style.display = '';
    };
    
    // Handle cancel
    const cancelEdit = () => {
        input.remove();
        titleElement.style.display = '';
    };
    
    // Event listeners
    input.addEventListener('blur', saveEdit);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            saveEdit();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            cancelEdit();
        }
    });
}

async function updateIdeaTitle(ideaId, newTitle) {
    try {
        const result = await dataLoader.updateIdeaTitle(ideaId, newTitle);
        // Update the display
        const ideaItem = document.querySelector(`[data-idea-id="${ideaId}"]`);
        if (ideaItem) {
            ideaItem.querySelector('.idea-title').textContent = newTitle;
        }
        showNotification(result.message, 'success');
        // Invalidate cache for this week
        cacheManager.invalidateWeek(currentYear, currentWeekNumber);
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message, 'error');
    }
}

async function deleteIdea(ideaId) {
    if (confirm('Are you sure you want to delete this idea?')) {
        try {
        const result = await dataLoader.deleteIdea(ideaId);
        // Invalidate cache for this week
        cacheManager.invalidateWeek(currentYear, currentWeekNumber);
        // Reload current week's content
        await loadWeekContent(currentYear, currentWeekNumber);
            showNotification(result.message, 'success');
        } catch (error) {
            console.error('Error:', error);
            showNotification(error.message, 'error');
        }
    }
}

function scheduleIdea(ideaId) {
    // TODO: Open scheduling modal
    showNotification('Schedule idea functionality coming soon!', 'info');
}

// Event editing functions
function editEvent(eventId) {
    const eventItem = document.querySelector(`[data-event-id="${eventId}"]`);
    if (!eventItem) return;
    
    const titleElement = eventItem.querySelector('.event-title');
    const currentTitle = titleElement.textContent;
    
    // Create input field
    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentTitle;
    input.className = 'inline-edit-input';
    input.style.cssText = `
        width: 100%;
        padding: 4px 8px;
        border: 2px solid #3b82f6;
        border-radius: 4px;
        font-size: 14px;
        background: white;
    `;
    
    // Replace title with input
    titleElement.style.display = 'none';
    titleElement.parentNode.insertBefore(input, titleElement);
    input.focus();
    input.select();
    
    // Handle save
    const saveEdit = () => {
        const newTitle = input.value.trim();
        if (newTitle && newTitle !== currentTitle) {
            updateEventTitle(eventId, newTitle);
        }
        // Restore original display
        input.remove();
        titleElement.style.display = '';
    };
    
    // Handle cancel
    const cancelEdit = () => {
        input.remove();
        titleElement.style.display = '';
    };
    
    // Event listeners
    input.addEventListener('blur', saveEdit);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            saveEdit();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            cancelEdit();
        }
    });
}

async function updateEventTitle(eventId, newTitle) {
    try {
        const result = await dataLoader.updateEventTitle(eventId, newTitle);
        // Update the display
        const eventItem = document.querySelector(`[data-event-id="${eventId}"]`);
        if (eventItem) {
            eventItem.querySelector('.event-title').textContent = newTitle;
        }
        showNotification(result.message, 'success');
        // Invalidate cache for this week
        cacheManager.invalidateWeek(currentYear, currentWeekNumber);
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message, 'error');
    }
}

async function deleteEvent(eventId) {
    if (confirm('Are you sure you want to delete this event?')) {
        try {
        const result = await dataLoader.deleteEvent(eventId);
        // Invalidate cache for this week
        cacheManager.invalidateWeek(currentYear, currentWeekNumber);
        // Reload current week's content
        await loadWeekContent(currentYear, currentWeekNumber);
            showNotification(result.message, 'success');
        } catch (error) {
            console.error('Error:', error);
            showNotification(error.message, 'error');
        }
    }
}

function scheduleEvent(eventId) {
    // TODO: Open scheduling modal
    showNotification('Schedule event functionality coming soon!', 'info');
}

// Schedule editing functions
function editSchedule(scheduleId) {
    const scheduleItem = document.querySelector(`[data-schedule-id="${scheduleId}"]`);
    if (!scheduleItem) return;
    
    const titleElement = scheduleItem.querySelector('.schedule-title');
    const currentTitle = titleElement.textContent;
    
    // Create input field
    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentTitle;
    input.className = 'inline-edit-input';
    input.style.cssText = `
        width: 100%;
        padding: 4px 8px;
        border: 2px solid #3b82f6;
        border-radius: 4px;
        font-size: 14px;
        background: white;
    `;
    
    // Replace title with input
    titleElement.style.display = 'none';
    titleElement.parentNode.insertBefore(input, titleElement);
    input.focus();
    input.select();
    
    // Handle save
    const saveEdit = () => {
        const newTitle = input.value.trim();
        if (newTitle && newTitle !== currentTitle) {
            updateScheduleTitle(scheduleId, newTitle);
        }
        // Restore original display
        input.remove();
        titleElement.style.display = '';
    };
    
    // Handle cancel
    const cancelEdit = () => {
        input.remove();
        titleElement.style.display = '';
    };
    
    // Event listeners
    input.addEventListener('blur', saveEdit);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            saveEdit();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            cancelEdit();
        }
    });
}

async function updateScheduleTitle(scheduleId, newTitle) {
    try {
        const result = await dataLoader.updateScheduleTitle(scheduleId, newTitle);
        // Update the display
        const scheduleItem = document.querySelector(`[data-schedule-id="${scheduleId}"]`);
        if (scheduleItem) {
            scheduleItem.querySelector('.schedule-title').textContent = newTitle;
        }
        showNotification(result.message, 'success');
        // Invalidate cache for this week
        cacheManager.invalidateWeek(currentYear, currentWeekNumber);
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message, 'error');
    }
}

async function deleteSchedule(scheduleId) {
    if (confirm('Are you sure you want to delete this schedule entry?')) {
        try {
        const result = await dataLoader.deleteSchedule(scheduleId);
        // Invalidate cache for this week
        cacheManager.invalidateWeek(currentYear, currentWeekNumber);
        // Reload current week's content
        await loadWeekContent(currentYear, currentWeekNumber);
            showNotification(result.message, 'success');
        } catch (error) {
            console.error('Error:', error);
            showNotification(error.message, 'error');
        }
    }
}

// Make schedule functions globally accessible
window.editSchedule = editSchedule;
window.deleteSchedule = deleteSchedule;

async function updateIdeaPriority(ideaId, newPriority) {
    try {
        const result = await dataLoader.updateIdeaPriority(ideaId, newPriority);
        // Update the visual state immediately
        const ideaItem = document.querySelector(`[data-idea-id="${ideaId}"]`);
        if (ideaItem) {
            if (newPriority === 'mandatory') {
                ideaItem.classList.add('mandatory');
            } else {
                ideaItem.classList.remove('mandatory');
            }
        }
        showNotification(result.message, 'success');
        // Invalidate cache for this week
        cacheManager.invalidateWeek(currentYear, currentWeekNumber);
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message, 'error');
    }
}

async function updateEventPriority(eventId, newPriority) {
    try {
        const result = await dataLoader.updateEventPriority(eventId, newPriority);
        // Update the visual state immediately
        const eventItem = document.querySelector(`[data-event-id="${eventId}"]`);
        if (eventItem) {
            if (newPriority === 'mandatory') {
                eventItem.classList.add('mandatory');
            } else {
                eventItem.classList.remove('mandatory');
            }
        }
        showNotification(result.message, 'success');
        // Invalidate cache for this week
        cacheManager.invalidateWeek(currentYear, currentWeekNumber);
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message, 'error');
    }
}

async function updateSchedulePriority(scheduleId, newPriority) {
    try {
        const result = await dataLoader.updateSchedulePriority(scheduleId, newPriority);
        // Update the visual state immediately
        const scheduleItem = document.querySelector(`[data-schedule-id="${scheduleId}"]`);
        if (scheduleItem) {
            if (newPriority === 'mandatory') {
                scheduleItem.classList.add('mandatory');
            } else {
                scheduleItem.classList.remove('mandatory');
            }
            // Update the status display
            const statusElement = scheduleItem.querySelector('.schedule-status');
            if (statusElement) {
                statusElement.textContent = newPriority;
                statusElement.className = `schedule-status status-${newPriority}`;
            }
        }
        showNotification(result.message, 'success');
        // Invalidate cache for this week
        cacheManager.invalidateWeek(currentYear, currentWeekNumber);
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message, 'error');
    }
}

// Utility function for notifications
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

// ============================================================================
// DRAG AND DROP FUNCTIONALITY
// ============================================================================

let draggedElement = null;
let draggedType = null;
let draggedId = null;
let dragGhost = null;

function initializeDragAndDrop() {
    // Add drag event listeners to all draggable items
    document.addEventListener('dragstart', handleDragStart);
    document.addEventListener('dragend', handleDragEnd);
    document.addEventListener('dragover', handleDragOver);
    document.addEventListener('drop', handleDrop);
    document.addEventListener('dragenter', handleDragEnter);
    document.addEventListener('dragleave', handleDragLeave);
}

function handleDragStart(e) {
    const item = e.target.closest('.idea-item, .event-item, .schedule-item');
    if (!item) return;
    
    draggedElement = item;
    draggedType = item.classList.contains('idea-item') ? 'idea' : 
                  item.classList.contains('event-item') ? 'event' : 'schedule';
    draggedId = item.dataset.ideaId || item.dataset.eventId || item.dataset.scheduleId;
    
    // Add dragging class
    item.classList.add('dragging');
    
    // Create drag ghost
    dragGhost = document.createElement('div');
    dragGhost.className = 'drag-ghost';
    dragGhost.textContent = item.querySelector('.idea-title, .event-title, .schedule-title').textContent;
    document.body.appendChild(dragGhost);
    
    // Set drag image
    e.dataTransfer.setDragImage(dragGhost, 0, 0);
    e.dataTransfer.effectAllowed = 'move';
    
}

function handleDragEnd(e) {
    if (draggedElement) {
        draggedElement.classList.remove('dragging');
        draggedElement = null;
        draggedType = null;
        draggedId = null;
    }
    
    if (dragGhost) {
        document.body.removeChild(dragGhost);
        dragGhost = null;
    }
    
    // Remove all drag-over classes
    document.querySelectorAll('.week-cell.drag-over').forEach(cell => {
        cell.classList.remove('drag-over');
    });
    
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
}

function handleDragEnter(e) {
    const weekCell = e.target.closest('.week-cell');
    if (weekCell && weekCell.querySelector('.week-content')) {
        weekCell.classList.add('drag-over');
    }
}

function handleDragLeave(e) {
    const weekCell = e.target.closest('.week-cell');
    if (weekCell && !weekCell.contains(e.relatedTarget)) {
        weekCell.classList.remove('drag-over');
    }
}

function handleDrop(e) {
    e.preventDefault();
    
    const weekCell = e.target.closest('.week-cell');
    if (!weekCell || !draggedElement) return;
    
    const targetWeek = weekCell.dataset.week;
    if (!targetWeek) return;
    
    
    // Remove drag-over class
    weekCell.classList.remove('drag-over');
    
    // Move the item
    moveItemToWeek(draggedType, draggedId, parseInt(targetWeek));
}

async function moveItemToWeek(itemType, itemId, targetWeek) {
    try {
        let result;
        if (itemType === 'idea') {
            result = await dataLoader.updateIdeaTitle(itemId, targetWeek); // This needs to be updated to handle week movement
        } else if (itemType === 'event') {
            result = await dataLoader.updateEventTitle(itemId, targetWeek); // This needs to be updated to handle week movement
        } else if (itemType === 'schedule') {
            result = await dataLoader.updateScheduleTitle(itemId, targetWeek); // This needs to be updated to handle week movement
        }
        
        showNotification(`${itemType.charAt(0).toUpperCase() + itemType.slice(1)} moved to week ${targetWeek}`, 'success');
        // Invalidate cache for this week
        cacheManager.invalidateWeek(currentYear, currentWeekNumber);
        // Reload current week's content
        await loadWeekContent(currentYear, currentWeekNumber);
    } catch (error) {
        console.error('Error:', error);
        showNotification(`Error moving ${itemType}`, 'error');
    }
}

// Add new entry function
async function addNewEntry(weekNumber) {
    const title = prompt('Enter the title for the new entry:');
    if (!title) return;
    
    // Show category selection
    const categoryOptions = categories.map(cat => `<option value="${cat.name}">${cat.name}</option>`).join('');
    const categoryHtml = `
        <div style="margin: 10px 0;">
            <label for="new-entry-category">Category:</label>
            <select id="new-entry-category" style="margin-left: 10px; padding: 4px;">
                <option value="">Select Category</option>
                ${categoryOptions}
            </select>
        </div>
    `;
    
    // Create a simple modal
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    `;
    
    modal.innerHTML = `
        <div style="background: white; padding: 20px; border-radius: 8px; min-width: 300px;">
            <h3>Add New Entry</h3>
            <p><strong>Title:</strong> ${title}</p>
            <p><strong>Week:</strong> ${weekNumber}</p>
            ${categoryHtml}
            <div style="margin-top: 20px; text-align: right;">
                <button onclick="this.closest('.modal').remove()" style="margin-right: 10px; padding: 8px 16px;">Cancel</button>
                <button onclick="saveNewEntry(${weekNumber}, '${title.replace(/'/g, "\\'")}')" style="background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 4px;">Save</button>
            </div>
        </div>
    `;
    
    modal.className = 'modal';
    document.body.appendChild(modal);
}

async function saveNewEntry(weekNumber, title) {
    const categorySelect = document.getElementById('new-entry-category');
    const category = categorySelect.value;
    
    if (!category) {
        alert('Please select a category');
        return;
    }
    
    try {
        const result = await dataLoader.saveNewEntry(weekNumber, title);
        showNotification(result.message, 'success');
        // Remove modal
        document.querySelector('.modal').remove();
        // Invalidate cache for this week
        cacheManager.invalidateWeek(currentYear, currentWeekNumber);
        // Reload current week's content
        await loadWeekContent(currentYear, currentWeekNumber);
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message, 'error');
    }
}

// Make functions globally accessible for HTML onclick handlers
// This needs to be done after the functions are defined
window.updateIdeaPriority = updateIdeaPriority;
window.updateEventPriority = updateEventPriority;
window.updateSchedulePriority = updateSchedulePriority;

// Initialize drag and drop when calendar loads
document.addEventListener('DOMContentLoaded', function() {
    initializeDragAndDrop();
});