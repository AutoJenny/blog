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
            document.getElementById('type-event').checked = false;
            
            // Update modal title and apply type switching
            this.modal.forms.switchType(isTheme ? 'theme' : 'idea');

            // Store notes data for reference
            this.modal._notesData = idea.important_notes || [];
            
            // Populate form fields
            document.getElementById('idea-id').value = idea.id || '';
            document.getElementById('idea-title').value = idea.idea_title || '';
            document.getElementById('idea-description').value = idea.idea_description || '';
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
            // Update modal title
            document.getElementById('idea-modal-title').textContent = 'Manage Event';
            
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
            
            // Load tags
            this.modal.renderers.renderTags(eventData.tags || []);
            
            // Load important notes
            this.modal.renderers.renderNotes(eventData.important_notes || []);
            
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

    loadThemeData(theme) {
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
        
        if (theme.seasonal_context) {
            const seasonalInput = document.getElementById('idea-seasonal-context');
            if (seasonalInput) seasonalInput.value = theme.seasonal_context;
        }
        
        if (theme.priority) {
            const priorityInput = document.getElementById('idea-priority');
            if (priorityInput) priorityInput.value = theme.priority;
        }
        
        // Handle tags (JSONB array)
        if (theme.tags) {
            const tagsInput = document.getElementById('idea-tags');
            if (tagsInput) {
                if (Array.isArray(theme.tags)) {
                    tagsInput.value = theme.tags.join(', ');
                } else {
                    tagsInput.value = theme.tags;
                }
            }
        }
        
        // Handle evergreen fields
        if (theme.is_evergreen !== undefined) {
            const evergreenCheckbox = document.getElementById('idea-is-evergreen');
            if (evergreenCheckbox) evergreenCheckbox.checked = theme.is_evergreen;
        }
        
        if (theme.evergreen_frequency) {
            const freqInput = document.getElementById('idea-evergreen-frequency');
            if (freqInput) freqInput.value = theme.evergreen_frequency;
        }
        
        if (theme.evergreen_notes) {
            const notesInput = document.getElementById('idea-evergreen-notes');
            if (notesInput) notesInput.value = theme.evergreen_notes;
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

