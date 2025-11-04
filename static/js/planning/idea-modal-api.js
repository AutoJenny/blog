/**
 * Idea Modal API
 * API calls and data loading for ideas, themes, and events
 */

class IdeaModalAPI {
    constructor(modal) {
        this.modal = modal;
    }

    async loadCategories() {
        try {
            const response = await fetch('/planning/api/calendar/categories');
            if (response.ok) {
                const data = await response.json();
                this.modal.categories = data.categories || [];
            }
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    async loadIdea(ideaId) {
        try {
            // Reset modal title
            document.getElementById('idea-modal-title').textContent = 'Manage Idea';
            
            // Show all idea-specific fields, hide event-specific fields
            const weekGroup = document.querySelector('[for="idea-week-number"]')?.closest('.idea-form-group');
            if (weekGroup) weekGroup.style.display = 'block';
            const seasonalGroup = document.querySelector('[for="idea-seasonal-context"]')?.closest('.idea-form-group');
            if (seasonalGroup) seasonalGroup.style.display = 'block';
            
            const startDateGroup = document.getElementById('event-start-date-group');
            const endDateGroup = document.getElementById('event-end-date-group');
            const yearGroup = document.getElementById('event-year-group');
            if (startDateGroup) startDateGroup.style.display = 'none';
            if (endDateGroup) endDateGroup.style.display = 'none';
            if (yearGroup) yearGroup.style.display = 'none';
            
            // Show all sections for ideas
            Array.from(document.querySelectorAll('.idea-section')).forEach(s => s.style.display = 'block');
            
            const response = await fetch(`/planning/api/calendar/ideas/${ideaId}`);
            if (!response.ok) throw new Error('Failed to load idea');

            const data = await response.json();
            const idea = data.idea || data;

            // Themes and ideas are separate - check if this is from calendar_themes or calendar_ideas
            // If idea has theme_title, it's from calendar_themes
            const isTheme = idea.theme_title !== undefined || (idea.id && await this.isThemeId(idea.id));
            
            // Set the appropriate type
            this.modal.currentType = isTheme ? 'theme' : 'idea';
            this.modal.originalType = isTheme ? 'theme' : 'idea'; // Track original type for conversion detection
            document.getElementById('type-theme').checked = isTheme;
            document.getElementById('type-idea').checked = !isTheme;
            document.getElementById('type-annual-event').checked = false;
            document.getElementById('type-special-event').checked = false;
            
            // Update modal title and apply type switching
            this.modal.forms.switchType(isTheme ? 'theme' : 'idea');

            // Store notes data for reference
            this.modal._notesData = idea.important_notes || [];
            
            // Populate form fields
            document.getElementById('idea-id').value = idea.id || '';
            document.getElementById('idea-title').value = idea.idea_title || '';
            document.getElementById('idea-description').value = idea.idea_description || '';
            const yearInput = document.getElementById('idea-year');
            if (yearInput) {
                yearInput.value = idea.year || '';
            }
            document.getElementById('idea-week-number').value = idea.week_number || '';
            document.getElementById('idea-content-type').value = idea.content_type || '';
            document.getElementById('idea-seasonal-context').value = idea.seasonal_context || '';
            document.getElementById('idea-priority').value = idea.priority || 'random';
            document.getElementById('idea-is-recurring').checked = idea.is_recurring !== false;
            document.getElementById('idea-is-evergreen').checked = idea.is_evergreen === true;
            document.getElementById('idea-evergreen-frequency').value = idea.evergreen_frequency || 'low-frequency';
            document.getElementById('idea-evergreen-notes').value = idea.evergreen_notes || '';
            document.getElementById('idea-can-span-weeks').checked = idea.can_span_weeks === true;
            document.getElementById('idea-max-weeks').value = idea.max_weeks || 1;

            // Update UI based on checkboxes
            if (idea.is_evergreen) {
                document.getElementById('idea-evergreen-group').style.display = 'block';
                document.getElementById('idea-evergreen-notes-group').style.display = 'block';
            }
            if (idea.can_span_weeks) {
                document.getElementById('idea-max-weeks-group').style.display = 'block';
            }

            // Load categories
            this.modal.renderers.renderCategories(idea.categories || []);

            // Load sources (handle both array and JSONB formats)
            let sources = idea.sources || [];
            if (typeof sources === 'string') {
                try {
                    sources = JSON.parse(sources);
                } catch (e) {
                    sources = [];
                }
            }
            this.modal.renderers.renderSources(Array.isArray(sources) ? sources : []);

            // Load tags
            this.modal.renderers.renderTags(idea.tags || []);
            
            // Load important notes
            this.modal.renderers.renderNotes(idea.important_notes || []);

        } catch (error) {
            console.error('Error loading idea:', error);
            alert('Failed to load idea: ' + error.message);
        }
    }

    async loadEvent(eventData) {
        try {
            // Determine if this is an annual or special event based on event_recurrence_type
            const isSpecialEvent = eventData.event_recurrence_type === 'one_off';
            const eventType = isSpecialEvent ? 'special_event' : 'annual_event';
            
            // Update modal title and type selector
            if (isSpecialEvent) {
                document.getElementById('idea-modal-title').textContent = 'Manage Special Event';
                document.getElementById('type-special-event').checked = true;
                document.getElementById('type-annual-event').checked = false;
            } else {
                document.getElementById('idea-modal-title').textContent = 'Manage Annual Event';
                document.getElementById('type-annual-event').checked = true;
                document.getElementById('type-special-event').checked = false;
            }
            document.getElementById('type-theme').checked = false;
            document.getElementById('type-idea').checked = false;
            
            // Update modal currentType
            this.modal.currentType = eventType;
            this.modal.originalType = eventType;
            
            // Hide week number and seasonal context (events use dates instead)
            const weekGroup = document.querySelector('[for="idea-week-number"]')?.closest('.idea-form-group');
            if (weekGroup) weekGroup.style.display = 'none';
            const seasonalGroup = document.querySelector('[for="idea-seasonal-context"]')?.closest('.idea-form-group');
            if (seasonalGroup) seasonalGroup.style.display = 'none';
            
            // Show date fields (add if not exist)
            this.modal.forms.ensureEventFieldsExist();
            const startDateGroup = document.getElementById('event-start-date-group');
            const endDateGroup = document.getElementById('event-end-date-group');
            const yearGroup = document.getElementById('event-year-group');
            
            if (startDateGroup) startDateGroup.style.display = 'block';
            if (endDateGroup) endDateGroup.style.display = 'block';
            if (yearGroup) yearGroup.style.display = 'block';
            const advanceNoticeGroup = document.getElementById('event-advance-notice-group');
            if (advanceNoticeGroup) advanceNoticeGroup.style.display = 'block';
            
            // Store notes data for reference
            this.modal._notesData = eventData.important_notes || [];
            
            // Populate form with ALL event data
            document.getElementById('idea-id').value = eventData.id || '';
            document.getElementById('idea-title').value = eventData.event_title || '';
            document.getElementById('idea-description').value = eventData.event_description || '';
            document.getElementById('idea-content-type').value = eventData.content_type || '';
            document.getElementById('idea-priority').value = eventData.priority || 'random';
            document.getElementById('idea-is-recurring').checked = eventData.is_recurring === true;
            document.getElementById('idea-can-span-weeks').checked = eventData.can_span_weeks === true;
            document.getElementById('idea-max-weeks').value = eventData.max_weeks || 1;
            
            if (startDateGroup) {
                const startDate = eventData.start_date ? new Date(eventData.start_date).toISOString().split('T')[0] : '';
                document.getElementById('event-start-date').value = startDate;
            }
            if (endDateGroup) {
                const endDate = eventData.end_date ? new Date(eventData.end_date).toISOString().split('T')[0] : '';
                document.getElementById('event-end-date').value = endDate;
            }
            if (yearGroup) {
                const yearSelect = document.getElementById('event-year');
                if (yearSelect) {
                    // Handle both number inputs (old) and select dropdowns (new)
                    if (yearSelect.tagName === 'SELECT') {
                        // It's a dropdown - set value to year or "every_year" if is_recurring
                        const yearValue = eventData.is_recurring ? 'every_year' : (eventData.year || new Date().getFullYear());
                        if (yearSelect.querySelector(`option[value="${yearValue}"]`)) {
                            yearSelect.value = String(yearValue);
                        } else {
                            // Year not in dropdown, default to current year
                            yearSelect.value = String(new Date().getFullYear());
                        }
                    } else {
                        // Old number input (shouldn't happen, but handle it)
                        yearSelect.value = eventData.year || new Date().getFullYear();
                    }
                }
            }
            
            // Load advance notice
            const advanceNoticeSelect = document.getElementById('event-advance-notice');
            if (advanceNoticeSelect && eventData.advance_notice !== undefined && eventData.advance_notice !== null) {
                advanceNoticeSelect.value = String(eventData.advance_notice);
            }
            
            // Load categories (events have categories too)
            this.modal.renderers.renderCategories(eventData.categories || []);
            
            // For special events, tags contains source info object - extract it before rendering
            let sourceInfo = null;
            let tagsToRender = eventData.tags || [];
            
            if (isSpecialEvent && eventData.tags && typeof eventData.tags === 'object' && !Array.isArray(eventData.tags)) {
                // Extract source info from tags object
                sourceInfo = eventData.tags;
                // Don't render source info as tags - render empty array instead
                tagsToRender = [];
            }
            
            // Load tags (skip source info for special events)
            this.modal.renderers.renderTags(tagsToRender);
            
            // Load important notes
            this.modal.renderers.renderNotes(eventData.important_notes || []);
            
            // Show source information for special events
            if (isSpecialEvent && sourceInfo) {
                this.renderSpecialEventSource(sourceInfo);
            } else {
                // Hide source section for annual events
                const sourceSection = document.getElementById('special-event-source-section');
                if (sourceSection) sourceSection.style.display = 'none';
            }
            
            // Events don't have sources or evergreen fields - hide only evergreen section, keep sources visible but empty
            const sourcesSection = Array.from(document.querySelectorAll('.idea-section')).find(s => 
                s.querySelector('#idea-add-source')
            );
            if (sourcesSection) {
                // Clear sources container but keep section visible
                document.getElementById('idea-sources-container').innerHTML = '<p class="idea-help-text">Events do not support sources.</p>';
            }
            
            const evergreenSection = Array.from(document.querySelectorAll('.idea-section')).find(s => 
                s.querySelector('[for="idea-is-evergreen"]')
            );
            if (evergreenSection) evergreenSection.style.display = 'none';
            
        } catch (error) {
            console.error('Error loading event:', error);
            alert('Failed to load event: ' + error.message);
        }
    }

    renderSpecialEventSource(sourceInfo) {
        // sourceInfo is either an object (from tags) or we need to extract it
        let sourceData = null;
        
        // If tags is an object with source info
        if (sourceInfo && typeof sourceInfo === 'object' && !Array.isArray(sourceInfo)) {
            sourceData = sourceInfo;
        }
        
        const container = document.getElementById('special-event-source-container');
        const section = document.getElementById('special-event-source-section');
        
        if (!container || !section) return;
        
        if (sourceData && (sourceData.source_name || sourceData.newsletter_event_id)) {
            section.style.display = 'block';
            
            let html = '<div class="idea-source-info" style="display: flex; flex-direction: column; gap: 12px;">';
            
            if (sourceData.source_name) {
                html += `
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-newspaper" style="color: #64748b;"></i>
                        <span style="font-weight: 600; color: #1e293b;">Source:</span>
                        <span style="color: #475569;">${this.escapeHtml(sourceData.source_name)}</span>
                    </div>
                `;
            }
            
            if (sourceData.location) {
                html += `
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-map-marker-alt" style="color: #64748b;"></i>
                        <span style="font-weight: 600; color: #1e293b;">Location:</span>
                        <span style="color: #475569;">${this.escapeHtml(sourceData.location)}</span>
                    </div>
                `;
            }
            
            if (sourceData.url) {
                html += `
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-external-link-alt" style="color: #64748b;"></i>
                        <span style="font-weight: 600; color: #1e293b;">Original URL:</span>
                        <a href="${this.escapeHtml(sourceData.url)}" target="_blank" rel="noopener noreferrer" 
                           style="color: #3b82f6; text-decoration: none; max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            ${this.escapeHtml(sourceData.url)}
                        </a>
                    </div>
                `;
            }
            
            if (sourceData.newsletter_event_id) {
                const detailUrl = `/newsletter/events/${sourceData.newsletter_event_id}`;
                html += `
                    <div style="margin-top: 8px; padding-top: 12px; border-top: 1px solid #e2e8f0;">
                        <a href="${detailUrl}" target="_blank" rel="noopener noreferrer" 
                           class="idea-btn idea-btn-secondary" 
                           style="display: inline-flex; align-items: center; gap: 6px; text-decoration: none;">
                            <i class="fas fa-eye"></i>
                            View Full Details in Newsletter Events
                        </a>
                    </div>
                `;
            }
            
            html += '</div>';
            container.innerHTML = html;
        } else {
            section.style.display = 'none';
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    loadThemeData(theme) {
        // Set the theme ID in the hidden field
        const ideaIdInput = document.getElementById('idea-id');
        if (ideaIdInput) {
            ideaIdInput.value = theme.id || '';
        }
        
        // Map theme fields to form fields
        if (theme.theme_title) {
            const titleInput = document.getElementById('idea-title');
            if (titleInput) titleInput.value = theme.theme_title;
        }
        
        if (theme.theme_description) {
            const descInput = document.getElementById('idea-description');
            if (descInput) descInput.value = theme.theme_description;
        }
        
        if (theme.week_number) {
            const weekInput = document.getElementById('idea-week-number');
            if (weekInput) weekInput.value = theme.week_number;
        }
        
        if (theme.year) {
            const yearInput = document.getElementById('idea-year');
            if (yearInput) yearInput.value = theme.year;
        } else {
            // If no year in theme data, try to get it from URL or use current year
            const urlParams = new URLSearchParams(window.location.search);
            const year = parseInt(urlParams.get('year')) || new Date().getFullYear();
            const yearInput = document.getElementById('idea-year');
            if (yearInput) yearInput.value = year;
        }
        
        if (theme.seasonal_context) {
            const seasonalInput = document.getElementById('idea-seasonal-context');
            if (seasonalInput) seasonalInput.value = theme.seasonal_context;
        }
        
        if (theme.priority) {
            const priorityInput = document.getElementById('idea-priority');
            if (priorityInput) priorityInput.value = theme.priority;
        }
        
        if (theme.content_type) {
            const contentTypeInput = document.getElementById('idea-content-type');
            if (contentTypeInput) contentTypeInput.value = theme.content_type;
        }
        
        if (theme.is_recurring !== undefined) {
            const recurringCheckbox = document.getElementById('idea-is-recurring');
            if (recurringCheckbox) recurringCheckbox.checked = theme.is_recurring;
        }
        
        if (theme.can_span_weeks !== undefined) {
            const canSpanCheckbox = document.getElementById('idea-can-span-weeks');
            if (canSpanCheckbox) canSpanCheckbox.checked = theme.can_span_weeks;
            if (theme.can_span_weeks) {
                const maxWeeksGroup = document.getElementById('idea-max-weeks-group');
                if (maxWeeksGroup) maxWeeksGroup.style.display = 'block';
            }
        }
        
        if (theme.max_weeks) {
            const maxWeeksInput = document.getElementById('idea-max-weeks');
            if (maxWeeksInput) maxWeeksInput.value = theme.max_weeks;
        }
        
        // Handle tags (JSONB array)
        if (theme.tags) {
            this.modal.renderers.renderTags(Array.isArray(theme.tags) ? theme.tags : []);
        }
        
        // Handle evergreen fields
        if (theme.is_evergreen !== undefined) {
            const evergreenCheckbox = document.getElementById('idea-is-evergreen');
            if (evergreenCheckbox) evergreenCheckbox.checked = theme.is_evergreen;
            if (theme.is_evergreen) {
                const evergreenGroup = document.getElementById('idea-evergreen-group');
                const evergreenNotesGroup = document.getElementById('idea-evergreen-notes-group');
                if (evergreenGroup) evergreenGroup.style.display = 'block';
                if (evergreenNotesGroup) evergreenNotesGroup.style.display = 'block';
            }
        }
        
        if (theme.evergreen_frequency) {
            const freqInput = document.getElementById('idea-evergreen-frequency');
            if (freqInput) freqInput.value = theme.evergreen_frequency;
        }
        
        if (theme.evergreen_notes) {
            const notesInput = document.getElementById('idea-evergreen-notes');
            if (notesInput) notesInput.value = theme.evergreen_notes;
        }
        
        // Handle categories
        if (theme.categories && Array.isArray(theme.categories)) {
            this.modal.renderers.renderCategories(theme.categories);
        }
        
        // Handle sources and important_notes (JSONB arrays)
        if (theme.sources && Array.isArray(theme.sources)) {
            this.modal.renderers.renderSources(theme.sources);
        }
        
        if (theme.important_notes && Array.isArray(theme.important_notes)) {
            this.modal.renderers.renderNotes(theme.important_notes);
        }
    }

    async isThemeId(id) {
        // Check if an ID belongs to a theme by trying to fetch it from themes API
        try {
            const response = await fetch(`/planning/api/calendar/themes/${id}`);
            return response.ok;
        } catch {
            return false;
        }
    }
}

