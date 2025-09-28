import DateUtils from './calendar/utils/date-utils.js';
import CONFIG from './calendar/utils/constants.js';
import DataLoader from './calendar/api/data-loader.js';
import CacheManager from './calendar/api/cache-manager.js';
import { getPrimaryCategory, getPrimaryCategoryFromTags, showNotification, renderCalendarFallback, renderCalendarFromData, renderIdeaItem, renderEventItem, renderScheduleItem } from './calendar/ui/calendar-renderer.js';
import { DragDropManager } from './calendar/ui/drag-drop.js';

// Global variables
let currentYear = new Date().getFullYear();
let currentWeekNumber = DateUtils.getWeekNumber(new Date());
let categories = [];

// Initialize API modules
const dataLoader = new DataLoader('/planning/api/calendar');
const cacheManager = new CacheManager();

// Initialize drag and drop manager
const dragDropManager = new DragDropManager(dataLoader, cacheManager);

document.addEventListener('DOMContentLoaded', function() {
    
    // Set current stage for navigation
    window.currentStage = CONFIG.WINDOW.CURRENT_STAGE;
    window.currentSubstage = CONFIG.WINDOW.CURRENT_SUBSTAGE;
    // postId is set in the HTML template
    
    
    // Initialize calendar
    initializeCalendar();
    
    // Initialize drag and drop
    dragDropManager.initialize();
    
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
    renderCalendarFallback(currentYear, currentWeekNumber);
    
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
    
    // Update calendar header with post ID and current week info
    updateCalendarHeader(weekNumber);
    
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
            renderCalendarFallback(currentYear, currentWeekNumber);
        }
    } catch (error) {
        console.error(CONFIG.MESSAGES.CALENDAR_LOAD_ERROR, error);
        // Re-render fallback if database fails
        renderCalendarFallback();
    }
}

function updateCalendarHeader(weekNumber) {
    // Get the post ID from the window object (set in the HTML template)
    const postId = window.postId || 'Unknown';
    
    // Calculate the week dates for the current week
    const weekDates = DateUtils.getWeekDates(weekNumber, currentYear);
    
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
        titleElement.textContent = `Post ID: ${postId} - ${startDate}-${endDate} (Week ${weekNumber})`;
    }
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
            html += renderIdeaItem(idea, categories, isScheduled);
        });
        html += '</div>';
    }
    
    // Render events
    if (events && events.length > 0) {
        html += '<div class="events-section">';
        events.forEach(event => {
            const isScheduled = scheduledEventIds.has(event.id);
            html += renderEventItem(event, categories, isScheduled);
        });
        html += '</div>';
    }
    
    // Render schedule
    if (schedule && schedule.length > 0) {
        html += '<div class="schedule-section">';
        schedule.forEach(item => {
            html += renderScheduleItem(item);
        });
        html += '</div>';
    }
    
    return html;
}



// ============================================================================
// CALENDAR EDITING FUNCTIONS
// ============================================================================

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

// ============================================================================
// DRAG AND DROP FUNCTIONALITY
// ============================================================================
// Moved to DragDropManager class in drag-drop.js


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
window.loadWeekContent = loadWeekContent;
