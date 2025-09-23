/**
 * Posting Control Manager
 * Handles scheduling, manual posting, and queue management for syndication pages
 */
class PostingControlManager {
    constructor() {
        this.schedules = [];
        this.currentPost = null;
        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeScheduleControls();
            this.loadTodayStatus();
            this.loadAllSchedules();
        });
    }

    // Schedule Management Functions
    initializeScheduleControls() {
        // Get schedule control elements
        const addScheduleBtn = document.getElementById('add-schedule-btn');
        const addScheduleForm = document.getElementById('add-schedule-form');
        const saveNewScheduleBtn = document.getElementById('save-new-schedule-btn');
        const cancelNewScheduleBtn = document.getElementById('cancel-new-schedule-btn');
        const testAllSchedulesBtn = document.getElementById('test-all-schedules-btn');
        const clearAllSchedulesBtn = document.getElementById('clear-all-schedules-btn');

        // New schedule form elements
        const newScheduleName = document.getElementById('new-schedule-name');
        const newScheduleTime = document.getElementById('new-schedule-time');
        const newScheduleTimezone = document.getElementById('new-schedule-timezone');
        const newDayCheckboxes = document.querySelectorAll('input[type="checkbox"][id^="new-day-"]');
        const newPresetWeekdays = document.getElementById('new-preset-weekdays');
        const newPresetWeekends = document.getElementById('new-preset-weekends');
        const newPresetEveryday = document.getElementById('new-preset-everyday');

        // Add event listeners
        if (addScheduleBtn) addScheduleBtn.addEventListener('click', () => this.showAddScheduleForm());
        if (cancelNewScheduleBtn) cancelNewScheduleBtn.addEventListener('click', () => this.hideAddScheduleForm());
        if (saveNewScheduleBtn) saveNewScheduleBtn.addEventListener('click', () => this.handleSaveNewSchedule());
        if (testAllSchedulesBtn) testAllSchedulesBtn.addEventListener('click', () => this.handleTestAllSchedules());
        if (clearAllSchedulesBtn) clearAllSchedulesBtn.addEventListener('click', () => this.handleClearAllSchedules());

        // New schedule form preset buttons
        if (newPresetWeekdays) newPresetWeekdays.addEventListener('click', () => this.setNewPresetDays([1,2,3,4,5]));
        if (newPresetWeekends) newPresetWeekends.addEventListener('click', () => this.setNewPresetDays([6,7]));
        if (newPresetEveryday) newPresetEveryday.addEventListener('click', () => this.setNewPresetDays([1,2,3,4,5,6,7]));
    }

    // Multiple Schedule Management Functions
    showAddScheduleForm() {
        const form = document.getElementById('add-schedule-form');
        const btn = document.getElementById('add-schedule-btn');
        if (form) form.style.display = 'block';
        if (btn) btn.style.display = 'none';
    }

    hideAddScheduleForm() {
        const form = document.getElementById('add-schedule-form');
        const btn = document.getElementById('add-schedule-btn');
        if (form) form.style.display = 'none';
        if (btn) btn.style.display = 'block';
        this.resetNewScheduleForm();
    }

    resetNewScheduleForm() {
        const nameField = document.getElementById('new-schedule-name');
        const timeField = document.getElementById('new-schedule-time');
        const timezoneField = document.getElementById('new-schedule-timezone');
        
        if (nameField) nameField.value = '';
        if (timeField) timeField.value = '17:00';
        if (timezoneField) timezoneField.value = 'GMT';
        this.setNewPresetDays([1,2,3,4,5]); // Default to weekdays
    }

    getNewSelectedDays() {
        const dayMap = {
            'new-day-mon': 1, 'new-day-tue': 2, 'new-day-wed': 3, 'new-day-thu': 4,
            'new-day-fri': 5, 'new-day-sat': 6, 'new-day-sun': 7
        };
        
        const selectedDays = [];
        Object.keys(dayMap).forEach(dayId => {
            const checkbox = document.getElementById(dayId);
            if (checkbox && checkbox.checked) {
                selectedDays.push(dayMap[dayId]);
            }
        });
        
        return selectedDays;
    }

    setNewPresetDays(days) {
        const dayMap = {
            1: 'new-day-mon', 2: 'new-day-tue', 3: 'new-day-wed', 4: 'new-day-thu',
            5: 'new-day-fri', 6: 'new-day-sat', 7: 'new-day-sun'
        };
        
        // Clear all checkboxes
        Object.values(dayMap).forEach(dayId => {
            const checkbox = document.getElementById(dayId);
            if (checkbox) checkbox.checked = false;
        });
        
        // Check selected days
        days.forEach(day => {
            if (dayMap[day]) {
                const checkbox = document.getElementById(dayMap[day]);
                if (checkbox) checkbox.checked = true;
            }
        });
    }

    formatTimeForDisplay(time) {
        const [hours, minutes] = time.split(':');
        const hour = parseInt(hours);
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
        return `${displayHour}:${minutes} ${ampm}`;
    }

    getDayName(dayNumber) {
        const days = ['', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        return days[dayNumber];
    }

    formatSchedulePattern(days, time, timezone) {
        const timeFormatted = this.formatTimeForDisplay(time);
        
        if (days.length === 7) {
            return `Every day at ${timeFormatted} ${timezone}`;
        } else if (days.length === 5 && days.includes(1) && days.includes(5)) {
            return `Weekdays at ${timeFormatted} ${timezone}`;
        } else if (days.length === 2 && days.includes(6) && days.includes(7)) {
            return `Weekends at ${timeFormatted} ${timezone}`;
        } else {
            const dayNames = days.map(day => this.getDayName(day)).join(', ');
            return `${dayNames} at ${timeFormatted} ${timezone}`;
        }
    }

    calculateNextPostTime(days, time, timezone) {
        const now = new Date();
        const today = now.getDay() || 7; // Convert Sunday (0) to 7
        
        // Find next selected day
        let nextDay = null;
        for (let i = 0; i < 7; i++) {
            const checkDay = ((today + i - 1) % 7) + 1;
            if (days.includes(checkDay)) {
                nextDay = checkDay;
                break;
            }
        }
        
        if (!nextDay) {
            return 'No posts scheduled';
        }
        
        // Calculate days until next post
        const daysUntilNext = nextDay > today ? nextDay - today : (7 - today) + nextDay;
        const nextPostDate = new Date(now);
        nextPostDate.setDate(nextPostDate.getDate() + daysUntilNext);
        
        // Set the time
        const [hours, minutes] = time.split(':');
        nextPostDate.setHours(parseInt(hours), parseInt(minutes), 0, 0);
        
        const dayName = this.getDayName(nextDay);
        const timeFormatted = this.formatTimeForDisplay(time);
        
        if (daysUntilNext === 0) {
            return `Today at ${timeFormatted} ${timezone}`;
        } else if (daysUntilNext === 1) {
            return `Tomorrow at ${timeFormatted} ${timezone}`;
        } else {
            return `${dayName} at ${timeFormatted} ${timezone}`;
        }
    }

    async handleSaveNewSchedule() {
        const nameField = document.getElementById('new-schedule-name');
        const timeField = document.getElementById('new-schedule-time');
        const timezoneField = document.getElementById('new-schedule-timezone');
        
        const name = nameField ? nameField.value.trim() : '';
        const time = timeField ? timeField.value : '17:00';
        const timezone = timezoneField ? timezoneField.value : 'GMT';
        const selectedDays = this.getNewSelectedDays();
        
        if (!name) {
            alert('Please enter a schedule name.');
            return;
        }
        
        if (selectedDays.length === 0) {
            alert('Please select at least one day for posting.');
            return;
        }
        
        try {
            const response = await fetch('/launchpad/api/syndication/schedules', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name,
                    time: time,
                    timezone: timezone,
                    days: selectedDays
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.hideAddScheduleForm();
                this.loadAllSchedules();
                
                // Show success message
                const saveBtn = document.getElementById('save-new-schedule-btn');
                if (saveBtn) {
                    const originalText = saveBtn.innerHTML;
                    saveBtn.innerHTML = '<i class="fas fa-check"></i> Saved';
                    saveBtn.style.backgroundColor = '#10b981';
                    
                    setTimeout(() => {
                        saveBtn.innerHTML = originalText;
                        saveBtn.style.backgroundColor = '';
                    }, 2000);
                }
            } else {
                alert('Error saving schedule: ' + data.error);
            }
        } catch (error) {
            console.error('Error saving schedule:', error);
            alert('Error saving schedule. Please try again.');
        }
    }

    async handleDeleteSchedule(scheduleId) {
        if (!confirm('Are you sure you want to delete this schedule?')) {
            return;
        }
        
        try {
            const response = await fetch(`/launchpad/api/syndication/schedules/${scheduleId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.loadAllSchedules();
            } else {
                alert('Error deleting schedule: ' + data.error);
            }
        } catch (error) {
            console.error('Error deleting schedule:', error);
            alert('Error deleting schedule. Please try again.');
        }
    }

    async handleTestAllSchedules() {
        try {
            const response = await fetch('/launchpad/api/syndication/schedules/test');
            const data = await response.json();
            
            if (data.success) {
                const preview = data.preview || 'No schedules active';
                alert('Schedule Preview (Next 7 Days):\n\n' + preview);
            } else {
                alert('Error testing schedules: ' + data.error);
            }
        } catch (error) {
            console.error('Error testing schedules:', error);
            alert('Error testing schedules. Please try again.');
        }
    }

    async handleClearAllSchedules() {
        if (!confirm('Are you sure you want to clear ALL schedules?')) {
            return;
        }
        
        try {
            const response = await fetch('/launchpad/api/syndication/schedules/clear', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.loadAllSchedules();
                
                // Show success message
                const clearBtn = document.getElementById('clear-all-schedules-btn');
                if (clearBtn) {
                    const originalText = clearBtn.innerHTML;
                    clearBtn.innerHTML = '<i class="fas fa-check"></i> Cleared';
                    clearBtn.style.backgroundColor = '#10b981';
                    
                    setTimeout(() => {
                        clearBtn.innerHTML = originalText;
                        clearBtn.style.backgroundColor = '';
                    }, 2000);
                }
            } else {
                alert('Error clearing schedules: ' + data.error);
            }
        } catch (error) {
            console.error('Error clearing schedules:', error);
            alert('Error clearing schedules. Please try again.');
        }
    }

    async loadAllSchedules() {
        try {
            // Get platform and content_type from page data
            const platform = window.pageData?.platform?.name || 'facebook';
            const contentType = window.pageData?.channel_type?.name === 'product_post' ? 'product' : 'blog_post';
            
            const response = await fetch(`/launchpad/api/syndication/schedules?platform=${platform}&content_type=${contentType}`);
            const data = await response.json();
            
            if (data.success) {
                this.schedules = data.schedules || [];
                this.displaySchedules(this.schedules);
                this.updateScheduleSummary(this.schedules);
            } else {
                console.error('Error loading schedules:', data.error);
                this.displaySchedules([]);
            }
        } catch (error) {
            console.error('Error loading schedules:', error);
            this.displaySchedules([]);
        }
    }

    displaySchedules(schedules) {
        const schedulesList = document.getElementById('schedules-list');
        if (!schedulesList) return;
        
        if (schedules.length === 0) {
            schedulesList.innerHTML = '<div style="color: #94a3b8; font-style: italic; text-align: center; padding: 20px;">No schedules configured</div>';
            return;
        }
        
        let html = '';
        schedules.forEach(schedule => {
            const pattern = this.formatSchedulePattern(schedule.days, schedule.time, schedule.timezone);
            const nextPost = this.calculateNextPostTime(schedule.days, schedule.time, schedule.timezone);
            const scheduleName = schedule.name || `Schedule ${schedule.id}`;
            
            html += `
                <div style="background: #1e293b; border: 1px solid #334155; border-radius: 6px; padding: 15px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="color: #f1f5f9; font-weight: 600; margin-bottom: 5px;">${scheduleName}</div>
                        <div style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 3px;">${pattern}</div>
                        <div style="color: #10b981; font-size: 0.85rem;">Next: ${nextPost}</div>
                    </div>
                    <button onclick="postingControlManager.handleDeleteSchedule(${schedule.id})" 
                            style="background: #ef4444; border: none; border-radius: 4px; padding: 6px 10px; color: white; cursor: pointer; font-size: 0.8rem;">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
        });
        
        schedulesList.innerHTML = html;
    }

    updateScheduleSummary(schedules) {
        const nextPostsInfo = document.getElementById('next-posts-info');
        if (!nextPostsInfo) return;
        
        if (schedules.length === 0) {
            nextPostsInfo.textContent = 'No schedules active';
            return;
        }
        
        // Calculate next posts for all schedules
        const nextPosts = schedules.map(schedule => {
            const nextPost = this.calculateNextPostTime(schedule.days, schedule.time, schedule.timezone);
            const scheduleName = schedule.name || `Schedule ${schedule.id}`;
            return `${scheduleName}: ${nextPost}`;
        });
        
        nextPostsInfo.innerHTML = nextPosts.join('<br>');
    }

    async loadTodayStatus() {
        try {
            const response = await fetch('/launchpad/api/syndication/today-status');
            const data = await response.json();
            
            if (data.success) {
                this.currentPost = data.post;
                this.updatePostStatus(data.post);
            }
        } catch (error) {
            console.error('Error loading today\'s status:', error);
        }
    }

    updatePostStatus(post) {
        const statusElement = document.getElementById('post-status');
        const lastPostInfo = document.getElementById('last-post-info');
        
        if (!statusElement) return;
        
        if (post && post.status === 'posted') {
            statusElement.textContent = 'Posted';
            statusElement.className = 'status-indicator status-posted';
            if (lastPostInfo) {
                lastPostInfo.textContent = `Posted at ${post.posted_at || 'Unknown time'}`;
            }
        } else if (post && post.status === 'scheduled') {
            statusElement.textContent = 'Scheduled';
            statusElement.className = 'status-indicator status-scheduled';
            if (lastPostInfo) {
                lastPostInfo.textContent = `Scheduled for ${post.scheduled_at || 'Unknown time'}`;
            }
        } else {
            statusElement.textContent = 'Draft';
            statusElement.className = 'status-indicator status-draft';
            if (lastPostInfo) {
                lastPostInfo.textContent = 'No posts today';
            }
        }
    }

    // Manual posting functions
    async postNow() {
        const postNowBtn = document.getElementById('post-now-btn');
        if (postNowBtn) postNowBtn.disabled = true;
        
        try {
            const response = await fetch('/launchpad/api/syndication/post-now', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert('Post published successfully!');
                this.loadTodayStatus();
            } else {
                alert('Error posting: ' + data.error);
            }
        } catch (error) {
            console.error('Error posting:', error);
            alert('Error posting. Please try again.');
        } finally {
            if (postNowBtn) postNowBtn.disabled = false;
        }
    }

    async scheduleTomorrow() {
        const scheduleBtn = document.getElementById('schedule-tomorrow-btn');
        if (scheduleBtn) scheduleBtn.disabled = true;
        
        try {
            const response = await fetch('/launchpad/api/syndication/schedule-tomorrow', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert('Post scheduled for tomorrow!');
                this.loadTodayStatus();
            } else {
                alert('Error scheduling: ' + data.error);
            }
        } catch (error) {
            console.error('Error scheduling:', error);
            alert('Error scheduling. Please try again.');
        } finally {
            if (scheduleBtn) scheduleBtn.disabled = false;
        }
    }
}

// Initialize the posting control manager
const postingControlManager = new PostingControlManager();

// Global functions for button handlers
function toggleAccordion(sectionId) {
    const content = document.getElementById(sectionId + '-content');
    const chevron = document.getElementById(sectionId + '-chevron');
    
    if (content && chevron) {
        if (content.classList.contains('active')) {
            content.classList.remove('active');
            chevron.classList.remove('rotated');
        } else {
            content.classList.add('active');
            chevron.classList.add('rotated');
        }
    }
}

// Manual posting button handlers
document.addEventListener('DOMContentLoaded', () => {
    const postNowBtn = document.getElementById('post-now-btn');
    const scheduleTomorrowBtn = document.getElementById('schedule-tomorrow-btn');
    
    if (postNowBtn) {
        postNowBtn.addEventListener('click', () => postingControlManager.postNow());
    }
    
    if (scheduleTomorrowBtn) {
        scheduleTomorrowBtn.addEventListener('click', () => postingControlManager.scheduleTomorrow());
    }
});
