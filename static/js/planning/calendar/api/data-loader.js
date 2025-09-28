/**
 * Data Loader Module
 * Handles all API calls and data fetching
 */

class DataLoader {
    constructor(baseUrl = '/planning/api/calendar') {
        this.baseUrl = baseUrl;
    }

    async loadCategories() {
        try {
            const response = await fetch(`${this.baseUrl}/categories`);
            const data = await response.json();
            
            if (data.success) {
                return data.categories;
            } else {
                console.error('Error loading categories:', data.error);
                return [];
            }
        } catch (error) {
            console.error('Error loading categories:', error);
            return [];
        }
    }

    async loadCalendarData(year) {
        try {
            const response = await fetch(`${this.baseUrl}/weeks/${year}`);
            const data = await response.json();
            
            if (data.success && data.weeks && data.weeks.length > 0) {
                return data.weeks;
            } else {
                console.error('Error loading calendar data or no weeks found:', data.error || 'No weeks data');
                return [];
            }
        } catch (error) {
            console.error('Error loading calendar data:', error);
            return [];
        }
    }

    async loadWeekContent(year, weekNumber) {
        try {
            // Load ideas (perpetual)
            const ideasResponse = await fetch(`${this.baseUrl}/ideas/${weekNumber}`);
            if (!ideasResponse.ok) {
                throw new Error(`HTTP ${ideasResponse.status}: ${ideasResponse.statusText}`);
            }
            const ideasData = await ideasResponse.json();
            
            // Load events (year-specific)
            const eventsResponse = await fetch(`${this.baseUrl}/events/${year}/${weekNumber}`);
            if (!eventsResponse.ok) {
                throw new Error(`HTTP ${eventsResponse.status}: ${eventsResponse.statusText}`);
            }
            const eventsData = await eventsResponse.json();
            
            // Load schedule
            const scheduleResponse = await fetch(`${this.baseUrl}/schedule/${year}/${weekNumber}`);
            if (!scheduleResponse.ok) {
                throw new Error(`HTTP ${scheduleResponse.status}: ${scheduleResponse.statusText}`);
            }
            const scheduleData = await scheduleResponse.json();
            
            return {
                ideas: ideasData.ideas || [],
                events: eventsData.events || [],
                schedule: scheduleData.schedule || []
            };
        } catch (error) {
            console.error(`Error loading content for week ${weekNumber}:`, error);
            return {
                ideas: [],
                events: [],
                schedule: []
            };
        }
    }

    async loadCalendarContent(year, weeks) {
        // Load ideas and events for each week with rate limiting
        for (let i = 0; i < weeks.length; i++) {
            const week = weeks[i];
            try {
                const weekData = await this.loadWeekContent(year, week.week_number);
                // Store week data for rendering
                week.ideas = weekData.ideas;
                week.events = weekData.events;
                week.schedule = weekData.schedule;
                
                // Add small delay to prevent overwhelming the server
                if (i < weeks.length - 1) {
                    await new Promise(resolve => setTimeout(resolve, 50));
                }
            } catch (error) {
                console.error(`Failed to load content for week ${week.week_number}:`, error);
                // Continue with next week even if one fails
            }
        }
        return weeks;
    }

    async updateIdeaCategory(ideaId, newCategory) {
        // Handle empty category selection
        if (!newCategory) {
            throw new Error('Please select a category');
        }
        
        const response = await fetch(`${this.baseUrl}/ideas/${ideaId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tags: [newCategory]
            })
        });
        
        const data = await response.json();
        if (data.success) {
            return { success: true, message: `Idea category updated to ${newCategory}` };
        } else {
            throw new Error('Error updating idea category: ' + data.error);
        }
    }

    async updateEventCategory(eventId, newCategory) {
        // Handle empty category selection
        if (!newCategory) {
            throw new Error('Please select a category');
        }
        
        const response = await fetch(`${this.baseUrl}/events/${eventId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tags: [newCategory]
            })
        });
        
        const data = await response.json();
        if (data.success) {
            return { success: true, message: `Event category updated to ${newCategory}` };
        } else {
            throw new Error('Error updating event category: ' + data.error);
        }
    }

    async updateIdeaTitle(ideaId, newTitle) {
        const response = await fetch(`${this.baseUrl}/ideas/${ideaId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                idea_title: newTitle
            })
        });
        
        const data = await response.json();
        if (data.success) {
            return { success: true, message: 'Idea title updated successfully' };
        } else {
            throw new Error('Error updating idea title: ' + data.error);
        }
    }

    async deleteIdea(ideaId) {
        const response = await fetch(`${this.baseUrl}/ideas/${ideaId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        if (data.success) {
            return { success: true, message: 'Idea deleted successfully' };
        } else {
            throw new Error('Error deleting idea: ' + data.error);
        }
    }

    async updateEventTitle(eventId, newTitle) {
        const response = await fetch(`${this.baseUrl}/events/${eventId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                event_title: newTitle
            })
        });
        
        const data = await response.json();
        if (data.success) {
            return { success: true, message: 'Event title updated successfully' };
        } else {
            throw new Error('Error updating event title: ' + data.error);
        }
    }

    async deleteEvent(eventId) {
        const response = await fetch(`${this.baseUrl}/events/${eventId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        if (data.success) {
            return { success: true, message: 'Event deleted successfully' };
        } else {
            throw new Error('Error deleting event: ' + data.error);
        }
    }

    async updateScheduleTitle(scheduleId, newTitle) {
        const response = await fetch(`${this.baseUrl}/schedule/${scheduleId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: newTitle
            })
        });
        
        const data = await response.json();
        if (data.success) {
            return { success: true, message: 'Schedule title updated successfully' };
        } else {
            throw new Error('Error updating schedule title: ' + data.error);
        }
    }

    async deleteSchedule(scheduleId) {
        const response = await fetch(`${this.baseUrl}/schedule/${scheduleId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        if (data.success) {
            return { success: true, message: 'Schedule entry deleted successfully' };
        } else {
            throw new Error('Error deleting schedule: ' + data.error);
        }
    }

    async updateIdeaPriority(ideaId, newPriority) {
        const response = await fetch(`${this.baseUrl}/ideas/${ideaId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                priority: newPriority
            })
        });
        
        const data = await response.json();
        if (data.success) {
            return { success: true, message: 'Idea priority updated successfully' };
        } else {
            throw new Error('Error updating idea priority: ' + data.error);
        }
    }

    async updateEventPriority(eventId, newPriority) {
        const response = await fetch(`${this.baseUrl}/events/${eventId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                priority: newPriority
            })
        });
        
        const data = await response.json();
        if (data.success) {
            return { success: true, message: 'Event priority updated successfully' };
        } else {
            throw new Error('Error updating event priority: ' + data.error);
        }
    }

    async updateSchedulePriority(scheduleId, newPriority) {
        const response = await fetch(`${this.baseUrl}/schedule/${scheduleId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                priority: newPriority
            })
        });
        
        const data = await response.json();
        if (data.success) {
            return { success: true, message: 'Schedule priority updated successfully' };
        } else {
            throw new Error('Error updating schedule priority: ' + data.error);
        }
    }

    async scheduleIdea(ideaId) {
        // This function currently just shows a notification
        // Implementation depends on the specific scheduling logic
        return { success: true, message: 'Idea scheduled successfully' };
    }

    async scheduleEvent(eventId) {
        // This function currently just shows a notification
        // Implementation depends on the specific scheduling logic
        return { success: true, message: 'Event scheduled successfully' };
    }

    async addNewEntry(weekNumber) {
        // This function shows a modal for adding new entries
        // The actual saving is handled by saveNewEntry
        return { success: true, message: 'Add new entry modal opened' };
    }

    async saveNewEntry(weekNumber, title) {
        const response = await fetch(`${this.baseUrl}/ideas`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                idea_title: title,
                week_number: weekNumber,
                post_id: window.postId
            })
        });
        
        const data = await response.json();
        if (data.success) {
            return { success: true, message: 'New entry added successfully' };
        } else {
            throw new Error('Error adding entry: ' + data.error);
        }
    }
}

export default DataLoader;
