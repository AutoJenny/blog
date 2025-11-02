/**
 * Idea Modal Conversions
 * Type conversion logic for theme↔idea, idea↔event conversions
 */

class IdeaModalConversions {
    constructor(modal) {
        this.modal = modal;
    }

    detectConversion(isTheme, isEvent, ideaId) {
        // Check if we started with a theme (use originalType, not currentType which gets updated by switchType)
        const wasTheme = this.modal.originalType === 'theme' && this.modal.currentIdeaId;
        const isConvertingThemeToIdea = !isTheme && wasTheme;
        
        // Check if we're converting an event to an idea
        // We started with an event (currentEventId exists) but now saving as an idea (type is "idea", not "event")
        // Also check if ideaId matches currentEventId (event ID was put in idea-id field when loading event)
        const isConvertingEventToIdea = !isEvent && this.modal.currentEventId && 
            (!ideaId || String(ideaId) === String(this.modal.currentEventId));
        
        // Check if we're converting an idea to an event
        // We started with an idea (currentIdeaId exists) but now saving as an event (type is "event")
        const isConvertingIdeaToEvent = isEvent && this.modal.currentIdeaId && !this.modal.currentEventId;
        
        // Debug logging for conversion detection
        console.log('[IdeaModal] Conversion check:', {
            isTheme,
            originalType: this.modal.originalType,
            currentIdeaId: this.modal.currentIdeaId,
            currentEventId: this.modal.currentEventId,
            wasTheme,
            isConvertingThemeToIdea,
            isConvertingEventToIdea,
            isConvertingIdeaToEvent
        });
        
        return {
            isConvertingThemeToIdea,
            isConvertingEventToIdea,
            isConvertingIdeaToEvent
        };
    }

    async convertThemeToIdea(formData) {
        console.log('[IdeaModal] Converting theme to idea', {
            themeId: this.modal.currentIdeaId,
            formData
        });
        
        // Creating new idea with theme data
        const response = await fetch('/planning/api/calendar/ideas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            let message = 'Failed to create idea';
            try {
                const error = await response.json();
                message = error.error || message;
                console.error('[IdeaModal] Failed to create idea:', error);
            } catch (_) {
                message = `Failed to create idea: ${response.statusText}`;
            }
            throw new Error(message);
        }

        const result = await response.json();
        const newIdeaId = result.idea?.id || result.id;
        console.log('[IdeaModal] Created new idea:', newIdeaId);

        // Update schedule entries: set idea_id to newIdeaId where theme_id matches old theme
        if (this.modal.currentIdeaId && newIdeaId) {
            try {
                // Update schedule entries manually
                console.log('[IdeaModal] Updating schedule entries...');
                const updateScheduleResp = await fetch(`/planning/api/calendar/schedule/update-theme-to-idea`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ theme_id: this.modal.currentIdeaId, idea_id: newIdeaId })
                });
                
                if (!updateScheduleResp.ok) {
                    const errorText = await updateScheduleResp.text();
                    console.error('[IdeaModal] Failed to update schedule:', errorText);
                    throw new Error('Failed to update schedule references');
                }
                
                const updateResult = await updateScheduleResp.json();
                console.log('[IdeaModal] Schedule updated:', updateResult);
            } catch (e) {
                console.error('[IdeaModal] Error updating schedule references:', e);
                alert('Idea created but failed to update schedule references: ' + e.message);
            }
            
            // Delete the original theme
            try {
                console.log('[IdeaModal] Deleting original theme...');
                const deleteResponse = await fetch(`/planning/api/calendar/themes/${this.modal.currentIdeaId}`, {
                    method: 'DELETE'
                });
                if (!deleteResponse.ok) {
                    const errorText = await deleteResponse.text();
                    console.error('[IdeaModal] Failed to delete theme:', errorText);
                    throw new Error('Failed to delete original theme');
                }
                console.log('[IdeaModal] Theme deleted successfully');
            } catch (e) {
                console.error('[IdeaModal] Error deleting theme:', e);
                alert('Idea created but failed to delete original theme: ' + e.message);
            }
        }

        return { success: true, newIdeaId };
    }

    async convertEventToIdea(formData) {
        // Use conversion endpoint to atomically convert event to idea
        const response = await fetch(`/planning/api/calendar/events/${this.modal.currentEventId}/convert-to-idea`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            let message = 'Failed to convert event to idea';
            try {
                const error = await response.json();
                message = error.error || message;
            } catch (_) {
                message = `Failed to convert event: ${response.statusText}`;
            }
            throw new Error(message);
        }

        return await response.json();
    }

    async convertIdeaToEvent(formData) {
        // First, create the event
        const response = await fetch('/planning/api/calendar/events', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            let message = 'Failed to create event';
            try {
                const error = await response.json();
                message = error.error || message;
            } catch (_) {
                message = `Failed to create event: ${response.statusText}`;
            }
            throw new Error(message);
        }

        const result = await response.json();
        const newEventId = result.id || result.event?.id;

        // Then delete the original idea
        if (this.modal.currentIdeaId && newEventId) {
            const deleteResponse = await fetch(`/planning/api/calendar/ideas/${this.modal.currentIdeaId}`, {
                method: 'DELETE'
            });
            if (!deleteResponse.ok) {
                console.warn('Event created but failed to delete original idea:', this.modal.currentIdeaId);
            }
        }

        return { success: true, newEventId };
    }
}

