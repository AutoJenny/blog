/**
 * Schedule Management Micro-Module
 * Handles post scheduling functionality for One-Click Blog
 */

class ScheduleManager {
    constructor() {
        this.currentSchedule = null;
        this.init();
    }

    init() {
        console.log('[Schedule Manager] Initialized');
    }

    /**
     * Load current schedule data from API
     */
    async loadCurrentSchedule() {
        try {
            console.log('[Schedule Manager] loadCurrentSchedule() called');
            const response = await fetch('/launchpad/one-click-blog/api/next-up');
            const result = await response.json();
            
            console.log('[Schedule Manager] API response:', result);
            
            if (result.success) {
                this.currentSchedule = result.data;
                console.log('[Schedule Manager] ✅ Loaded schedule data:', this.currentSchedule);
                console.log('[Schedule Manager] scheduled_date:', this.currentSchedule.scheduled_date);
                console.log('[Schedule Manager] scheduled_relative:', this.currentSchedule.scheduled_relative);
                return this.currentSchedule;
            } else {
                console.error('[Schedule Manager] API returned error:', result.error);
            }
        } catch (error) {
            console.error('[Schedule Manager] Error loading schedule:', error);
        }
        return null;
    }

    /**
     * Show schedule modal with current data
     */
    async showScheduleModal() {
        console.log('[Schedule Manager] Showing schedule modal');
        
        // Load fresh schedule data
        await this.loadCurrentSchedule();
        
        // Show modal
        const modal = document.getElementById('schedule-modal');
        if (modal) {
            modal.style.display = 'flex';
        }
        
        // Populate modal with current data
        this.populateScheduleModal();
    }

    /**
     * Populate schedule modal with current schedule data
     */
    populateScheduleModal() {
        console.log('[Schedule Manager] populateScheduleModal() called');
        console.log('[Schedule Manager] currentSchedule:', this.currentSchedule);
        
        if (!this.currentSchedule) {
            console.error('[Schedule Manager] No schedule data available');
            this.setDefaultSchedule();
            return;
        }

        const scheduleDate = this.currentSchedule.scheduled_date;
        console.log('[Schedule Manager] Populating modal with scheduleDate:', scheduleDate);

        if (scheduleDate && scheduleDate !== 'Not scheduled') {
            try {
                // Parse "Oct 12, 2025" to "2025-10-12"
                console.log('[Schedule Manager] Parsing date:', scheduleDate);
                const dateObj = new Date(scheduleDate);
                console.log('[Schedule Manager] Parsed dateObj:', dateObj);
                console.log('[Schedule Manager] dateObj.getTime():', dateObj.getTime());
                console.log('[Schedule Manager] isNaN check:', isNaN(dateObj.getTime()));
                
                if (!isNaN(dateObj.getTime())) {
                    // Use UTC methods to avoid timezone issues
                    const year = dateObj.getFullYear();
                    const month = String(dateObj.getMonth() + 1).padStart(2, '0');
                    const day = String(dateObj.getDate()).padStart(2, '0');
                    const isoDate = `${year}-${month}-${day}`;
                    console.log('[Schedule Manager] ISO date (UTC):', isoDate);
                    
                    const dateInput = document.getElementById('publish-date');
                    console.log('[Schedule Manager] dateInput element:', dateInput);
                    
                    if (dateInput) {
                        dateInput.value = isoDate;
                        console.log('[Schedule Manager] ✅ Set date input value to:', isoDate);
                        console.log('[Schedule Manager] Date input now shows:', dateInput.value);
                    } else {
                        console.error('[Schedule Manager] ❌ publish-date element not found');
                    }
                } else {
                    console.error('[Schedule Manager] Invalid date format:', scheduleDate);
                    this.setDefaultSchedule();
                }
            } catch (error) {
                console.error('[Schedule Manager] Error parsing date:', error);
                this.setDefaultSchedule();
            }
        } else {
            console.log('[Schedule Manager] No valid schedule date, using default');
            this.setDefaultSchedule();
        }

        // Set default time
        const timeInput = document.getElementById('publish-time');
        if (timeInput) {
            timeInput.value = '14:00';
            console.log('[Schedule Manager] ✅ Set time input to 14:00');
        }
    }

    /**
     * Set default schedule (today's date)
     */
    setDefaultSchedule() {
        const today = new Date();
        const isoDate = today.toISOString().split('T')[0];
        const dateInput = document.getElementById('publish-date');
        if (dateInput) {
            dateInput.value = isoDate;
            console.log('[Schedule Manager] Set default date to:', isoDate);
        }
    }

    /**
     * Close schedule modal
     */
    closeScheduleModal() {
        const modal = document.getElementById('schedule-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    /**
     * Update schedule with new date/time
     */
    async updateSchedule(newDate, newTime) {
        try {
            console.log('[Schedule Manager] Updating schedule to:', newDate, newTime);
            
            const response = await fetch('/launchpad/one-click-blog/api/update-schedule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    publish_date: newDate,
                    publish_time: newTime
                })
            });

            const result = await response.json();
            
            if (result.success) {
                console.log('[Schedule Manager] ✅ Schedule updated successfully');
                this.closeScheduleModal();
                
                // Refresh schedule data
                await this.loadCurrentSchedule();
                
                // Notify other modules
                this.notifyScheduleUpdated();
                
                return true;
            } else {
                console.error('[Schedule Manager] Update failed:', result.error);
                return false;
            }
        } catch (error) {
            console.error('[Schedule Manager] Error updating schedule:', error);
            return false;
        }
    }

    /**
     * Notify other modules that schedule was updated
     */
    notifyScheduleUpdated() {
        // Dispatch custom event for other modules to listen to
        const event = new CustomEvent('scheduleUpdated', {
            detail: { schedule: this.currentSchedule }
        });
        document.dispatchEvent(event);
    }

    /**
     * Get current schedule data
     */
    getCurrentSchedule() {
        return this.currentSchedule;
    }
}

// Export for use in other modules
window.ScheduleManager = ScheduleManager;
