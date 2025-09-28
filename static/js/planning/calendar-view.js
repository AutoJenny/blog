import DateUtils from './calendar/utils/date-utils.js';
import CONFIG from './calendar/utils/constants.js';

// Global variables
let currentYear = new Date().getFullYear();
let currentWeekNumber = DateUtils.getWeekNumber(new Date());
let categories = [];

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
        const response = await fetch(CONFIG.API.CATEGORIES);
        const data = await response.json();
        
        if (data.success) {
            categories = data.categories;
        } else {
            console.error(CONFIG.MESSAGES.CATEGORIES_ERROR, data.error);
        }
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
        console.log(CONFIG.MESSAGES.CATEGORIES_NOT_LOADED);
        await loadCategories();
    }
    
    try {
        // Load calendar weeks from database
        const response = await fetch(`${CONFIG.API.CALENDAR_DATA}/${currentYear}`);
        const data = await response.json();
        
        
        if (data.success && data.weeks && data.weeks.length > 0) {
            renderCalendarFromData(data.weeks, weekNumber);
            await loadCalendarContent(currentYear, data.weeks);
        } else {
            console.error(CONFIG.MESSAGES.CALENDAR_ERROR, data.error || 'No weeks data');
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
        // Load ideas (perpetual)
        const ideasResponse = await fetch(`/planning/api/calendar/ideas/${weekNumber}`);
        if (!ideasResponse.ok) {
            throw new Error(`HTTP ${ideasResponse.status}: ${ideasResponse.statusText}`);
        }
        const ideasData = await ideasResponse.json();
        
        // Load events (year-specific)
        const eventsResponse = await fetch(`/planning/api/calendar/events/${year}/${weekNumber}`);
        if (!eventsResponse.ok) {
            throw new Error(`HTTP ${eventsResponse.status}: ${eventsResponse.statusText}`);
        }
        const eventsData = await eventsResponse.json();
        
        // Load schedule
        const scheduleResponse = await fetch(`/planning/api/calendar/schedule/${year}/${weekNumber}`);
        if (!scheduleResponse.ok) {
            throw new Error(`HTTP ${scheduleResponse.status}: ${scheduleResponse.statusText}`);
        }
        const scheduleData = await scheduleResponse.json();
        
        // Render content for this week
        const weekCell = document.querySelector(`[data-week="${weekNumber}"]`);
        if (weekCell) {
            const contentDiv = weekCell.querySelector('.week-content');
            const renderedContent = renderWeekContent(ideasData.ideas, eventsData.events, scheduleData.schedule);
            contentDiv.innerHTML = renderedContent;
            
            // Debug: Check if Spring Cleaning Checklist dropdown was created
            const springCleaningItem = contentDiv.querySelector('[data-idea-id]');
            if (springCleaningItem) {
                const springCleaningTitle = springCleaningItem.querySelector('.idea-title');
                if (springCleaningTitle && springCleaningTitle.textContent === 'Spring Cleaning Checklist') {
                    const dropdown = springCleaningItem.querySelector('.category-select');
                    console.log('Spring Cleaning Checklist dropdown found in DOM:', dropdown);
                    if (dropdown) {
                        console.log('Dropdown options count:', dropdown.options.length);
                        console.log('Dropdown selected value:', dropdown.value);
                        
                        // Check computed styles and dimensions
                        const computedStyle = window.getComputedStyle(dropdown);
                        console.log('Dropdown computed styles:', {
                            display: computedStyle.display,
                            visibility: computedStyle.visibility,
                            opacity: computedStyle.opacity,
                            width: computedStyle.width,
                            height: computedStyle.height,
                            backgroundColor: computedStyle.backgroundColor,
                            color: computedStyle.color,
                            position: computedStyle.position,
                            zIndex: computedStyle.zIndex
                        });
                        
                        // Check bounding box
                        const rect = dropdown.getBoundingClientRect();
                        console.log('Dropdown bounding box:', rect);
                        
                        // Check if it's actually visible in viewport
                        console.log('Is dropdown in viewport?', rect.width > 0 && rect.height > 0 && rect.top >= 0 && rect.left >= 0);
                        
                        // Temporarily highlight the dropdown for debugging
                        dropdown.style.border = '3px solid red !important';
                        dropdown.style.backgroundColor = 'yellow !important';
                        dropdown.style.color = 'black !important';
                        console.log('Applied temporary debugging styles to dropdown');
                    } else {
                        console.log('ERROR: Dropdown not found in DOM!');
                    }
                }
            }
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
            
            // Debug specific item
            if (idea.idea_title === 'Spring Cleaning Checklist') {
                console.log('Rendering Spring Cleaning Checklist:', idea);
                console.log('Categories available:', categories.length);
                console.log('Idea tags:', idea.tags);
                
                // Test the category selection logic
                const testCategory = getPrimaryCategoryFromTags(idea.tags);
                console.log('Test category result:', testCategory);
                
                // Test if categories array has the expected category
                const generalCategory = categories.find(cat => cat.name === 'General');
                console.log('General category found:', generalCategory);
            }
            
            // Debug HTML generation for Spring Cleaning Checklist
            if (idea.idea_title === 'Spring Cleaning Checklist') {
                console.log('About to generate HTML for Spring Cleaning Checklist');
                console.log('Categories for dropdown:', categories.map(c => c.name));
                
                // Test the template generation step by step
                try {
                    const testCategory = getPrimaryCategoryFromTags(idea.tags);
                    console.log('Test category for template:', testCategory);
                    
                    // Test the template string generation
                    const testTemplate = `
                        <div class="idea-categories">
                            <select class="category-select" onchange="updateIdeaCategory(${idea.id}, this.value)" title="Change category">
                                <option value="">Select Category</option>
                                ${categories.map(cat => `<option value="${cat.name}">${cat.name}</option>`).join('')}
                            </select>
                        </div>
                    `;
                    console.log('Test template generated:', testTemplate);
                } catch (error) {
                    console.error('Error in template generation:', error);
                }
            }
            
            const ideaHtml = `
                <div class="idea-item ${idea.priority === 'mandatory' ? 'mandatory' : ''}" data-idea-id="${idea.id}" draggable="true">
                    <div class="idea-content">
                        <div class="idea-title">${idea.idea_title}</div>
                        <div class="idea-categories">
                            <select class="category-select" onchange="updateIdeaCategory(${idea.id}, this.value)" title="Change category" data-category-color="${(() => {
                                const category = getPrimaryCategoryFromTags(idea.tags);
                                return category.color;
                            })()}" style="background-color: ${(() => {
                                const category = getPrimaryCategoryFromTags(idea.tags);
                                return category.name ? category.color : '#6b7280';
                            })()}; color: white; border-color: ${(() => {
                                const category = getPrimaryCategoryFromTags(idea.tags);
                                return category.name ? category.color : '#6b7280';
                            })()};">
                                <option value="" ${(() => {
                                    const category = getPrimaryCategoryFromTags(idea.tags);
                                    return !category.name ? 'selected' : '';
                                })()}>Select Category</option>
                                ${categories.length > 0 ? categories.map(cat => {
                                    // Get the primary category for this idea
                                    const primaryCategory = getPrimaryCategoryFromTags(idea.tags);
                                    const isSelected = cat.name === primaryCategory.name;
                                    console.log('Rendering option for idea', idea.id, ':', cat.name, 'isSelected:', isSelected, 'primaryCategory:', primaryCategory.name);
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
            
            // Debug the generated HTML for Spring Cleaning Checklist
            if (idea.idea_title === 'Spring Cleaning Checklist') {
                console.log('Generated HTML for Spring Cleaning Checklist:', ideaHtml);
                console.log('Does HTML contain category-select?', ideaHtml.includes('category-select'));
                console.log('Does HTML contain idea-categories?', ideaHtml.includes('idea-categories'));
            }
            
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
                                const category = getPrimaryCategoryFromTags(event.tags);
                                return category.color;
                            })()}" style="background-color: ${(() => {
                                const category = getPrimaryCategoryFromTags(event.tags);
                                return category.name ? category.color : '#6b7280';
                            })()}; color: white; border-color: ${(() => {
                                const category = getPrimaryCategoryFromTags(event.tags);
                                return category.name ? category.color : '#6b7280';
                            })()};">
                                <option value="" ${(() => {
                                    const category = getPrimaryCategoryFromTags(event.tags);
                                    return !category.name ? 'selected' : '';
                                })()}>Select Category</option>
                                ${categories.length > 0 ? categories.map(cat => {
                                    // Get the primary category for this event
                                    const primaryCategory = getPrimaryCategoryFromTags(event.tags);
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

// Helper function to get primary category from tags array (for ideas/events)
function getPrimaryCategoryFromTags(tags) {
    console.log('getPrimaryCategoryFromTags called with tags:', tags, 'categories available:', categories.length);
    
    if (!tags || tags.length === 0) {
        console.log('No tags provided, returning default');
        return { name: '', color: '#6b7280' };
    }
    
    // Look for Holiday category first
    const holidayTag = tags.find(tag => 
        tag.toLowerCase().includes('holiday') || 
        tag.toLowerCase().includes('festival') ||
        tag.toLowerCase().includes('celebration')
    );
    
    const categoryName = holidayTag || tags[0] || '';
    console.log('Selected category name:', categoryName);
    
    // Find the category in our loaded categories
    const category = categories.find(cat => cat.name === categoryName);
    console.log('Found category:', category);
    
    const result = {
        name: categoryName,
        color: category ? category.color : '#6b7280'
    };
    console.log('Returning result:', result);
    
    return result;
}

// Category update functions
function updateIdeaCategory(ideaId, newCategory) {
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
    
    fetch(`/planning/api/calendar/ideas/${ideaId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            tags: [newCategory]
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`Idea category updated to ${newCategory}`, 'success');
            // Reload calendar content to show updated category
            updateCalendar();
        } else {
            showNotification('Error updating idea category: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating idea category', 'error');
    });
}

function updateEventCategory(eventId, newCategory) {
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
    
    fetch(`/planning/api/calendar/events/${eventId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            tags: [newCategory]
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`Event category updated to ${newCategory}`, 'success');
            // Reload calendar content to show updated category
            updateCalendar();
        } else {
            showNotification('Error updating event category: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating event category', 'error');
    });
}

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

function updateIdeaTitle(ideaId, newTitle) {
    fetch(`/planning/api/calendar/ideas/${ideaId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            idea_title: newTitle
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the display
            const ideaItem = document.querySelector(`[data-idea-id="${ideaId}"]`);
            if (ideaItem) {
                ideaItem.querySelector('.idea-title').textContent = newTitle;
            }
            showNotification('Idea title updated successfully', 'success');
        } else {
            showNotification('Error updating idea: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating idea', 'error');
    });
}

function deleteIdea(ideaId) {
    if (confirm('Are you sure you want to delete this idea?')) {
        fetch(`/planning/api/calendar/ideas/${ideaId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reload calendar content
                updateCalendar();
                showNotification('Idea deleted successfully', 'success');
            } else {
                showNotification('Error deleting idea: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error deleting idea', 'error');
        });
    }
}

function scheduleIdea(ideaId) {
    console.log('Schedule idea:', ideaId);
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

function updateEventTitle(eventId, newTitle) {
    fetch(`/planning/api/calendar/events/${eventId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            event_title: newTitle
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the display
            const eventItem = document.querySelector(`[data-event-id="${eventId}"]`);
            if (eventItem) {
                eventItem.querySelector('.event-title').textContent = newTitle;
            }
            showNotification('Event title updated successfully', 'success');
        } else {
            showNotification('Error updating event: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating event', 'error');
    });
}

function deleteEvent(eventId) {
    if (confirm('Are you sure you want to delete this event?')) {
        fetch(`/planning/api/calendar/events/${eventId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reload calendar content
                updateCalendar();
                showNotification('Event deleted successfully', 'success');
            } else {
                showNotification('Error deleting event: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error deleting event', 'error');
        });
    }
}

function scheduleEvent(eventId) {
    console.log('Schedule event:', eventId);
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

function updateScheduleTitle(scheduleId, newTitle) {
    // For schedule items, we need to update the related idea or event
    // This is a simplified version - in a full implementation, we'd need to
    // determine whether this is an idea or event and update accordingly
    showNotification('Schedule title editing requires updating the related idea/event', 'info');
}

function deleteSchedule(scheduleId) {
    if (confirm('Are you sure you want to delete this schedule entry?')) {
        fetch(`/planning/api/calendar/schedule/${scheduleId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reload calendar content
                updateCalendar();
                showNotification('Schedule entry deleted successfully', 'success');
            } else {
                showNotification('Error deleting schedule: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error deleting schedule', 'error');
        });
    }
}

function updateIdeaPriority(ideaId, newPriority) {
    fetch(`/planning/api/calendar/ideas/${ideaId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            priority: newPriority
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the visual state immediately
            const ideaItem = document.querySelector(`[data-idea-id="${ideaId}"]`);
            if (ideaItem) {
                if (newPriority === 'mandatory') {
                    ideaItem.classList.add('mandatory');
                } else {
                    ideaItem.classList.remove('mandatory');
                }
            }
            showNotification(`Idea priority set to ${newPriority}`, 'success');
        } else {
            showNotification('Error updating idea priority: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating idea priority', 'error');
    });
}

function updateEventPriority(eventId, newPriority) {
    fetch(`/planning/api/calendar/events/${eventId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            priority: newPriority
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the visual state immediately
            const eventItem = document.querySelector(`[data-event-id="${eventId}"]`);
            if (eventItem) {
                if (newPriority === 'mandatory') {
                    eventItem.classList.add('mandatory');
                } else {
                    eventItem.classList.remove('mandatory');
                }
            }
            showNotification(`Event priority set to ${newPriority}`, 'success');
        } else {
            showNotification('Error updating event priority: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating event priority', 'error');
    });
}

function updateSchedulePriority(scheduleId, newPriority) {
    fetch(`/planning/api/calendar/schedule/${scheduleId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            priority: newPriority
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
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
            showNotification(`Schedule priority set to ${newPriority}`, 'success');
        } else {
            showNotification('Error updating schedule priority: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating schedule priority', 'error');
    });
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
    
    console.log('Drag started:', draggedType, draggedId);
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
    
    console.log('Drag ended');
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
    
    console.log('Drop:', draggedType, draggedId, 'to week', targetWeek);
    
    // Remove drag-over class
    weekCell.classList.remove('drag-over');
    
    // Move the item
    moveItemToWeek(draggedType, draggedId, parseInt(targetWeek));
}

function moveItemToWeek(itemType, itemId, targetWeek) {
    let endpoint = '';
    let data = { week_number: targetWeek };
    
    if (itemType === 'idea') {
        endpoint = `/planning/api/calendar/ideas/${itemId}`;
    } else if (itemType === 'event') {
        endpoint = `/planning/api/calendar/events/${itemId}`;
        data.year = currentYear; // Events need year
    } else if (itemType === 'schedule') {
        endpoint = `/planning/api/calendar/schedule/${itemId}`;
        data.year = currentYear; // Schedule needs year
    }
    
    fetch(endpoint, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`${itemType.charAt(0).toUpperCase() + itemType.slice(1)} moved to week ${targetWeek}`, 'success');
            // Reload calendar content
            updateCalendar();
        } else {
            showNotification(`Error moving ${itemType}: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification(`Error moving ${itemType}`, 'error');
    });
}

// Add new entry function
function addNewEntry(weekNumber) {
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

function saveNewEntry(weekNumber, title) {
    const categorySelect = document.getElementById('new-entry-category');
    const category = categorySelect.value;
    
    if (!category) {
        alert('Please select a category');
        return;
    }
    
    // Create the new idea
    fetch('/planning/api/calendar/ideas', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            idea_title: title,
            week_number: weekNumber,
            tags: [category],
            priority: 'random',
            is_evergreen: true
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('New entry added successfully', 'success');
            // Remove modal
            document.querySelector('.modal').remove();
            // Reload calendar
            updateCalendar();
        } else {
            showNotification('Error adding entry: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error adding entry', 'error');
    });
}

// Make functions globally accessible for HTML onclick handlers
window.deleteIdea = deleteIdea;
window.deleteEvent = deleteEvent;
window.deleteSchedule = deleteSchedule;
window.updateIdeaPriority = updateIdeaPriority;
window.updateEventPriority = updateEventPriority;
window.updateSchedulePriority = updateSchedulePriority;
window.updateIdeaCategory = updateIdeaCategory;
window.updateEventCategory = updateEventCategory;
window.editIdea = editIdea;
window.editEvent = editEvent;
window.editSchedule = editSchedule;
window.scheduleIdea = scheduleIdea;
window.scheduleEvent = scheduleEvent;
window.addNewEntry = addNewEntry;
window.saveNewEntry = saveNewEntry;

// Initialize drag and drop when calendar loads
document.addEventListener('DOMContentLoaded', function() {
    initializeDragAndDrop();
});