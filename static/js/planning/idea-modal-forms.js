/**
 * Idea Modal Forms
 * Form rendering, field management, and form data collection
 */

class IdeaModalForms {
    constructor(modal) {
        this.modal = modal;
    }

    switchType(type) {
        // Preserve form values before switching (to prevent data loss)
        const titleValue = document.getElementById('idea-title')?.value || '';
        const descriptionValue = document.getElementById('idea-description')?.value || '';
        
        this.modal.currentType = type;
        const title = document.getElementById('idea-modal-title');
        if (type === 'theme') {
            title.textContent = 'Manage Theme';
        } else if (type === 'idea') {
            title.textContent = 'Manage Idea';
        } else if (type === 'annual_event') {
            title.textContent = 'Manage Annual Event';
        } else if (type === 'special_event') {
            title.textContent = 'Manage Special Event';
        } else {
            title.textContent = 'Manage Event';
        }
        
        // Restore form values after switching (in case they were cleared)
        setTimeout(() => {
            const titleInput = document.getElementById('idea-title');
            const descriptionInput = document.getElementById('idea-description');
            if (titleInput && titleValue && !titleInput.value) {
                titleInput.value = titleValue;
            }
            if (descriptionInput && descriptionValue && !descriptionInput.value) {
                descriptionInput.value = descriptionValue;
            }
        }, 0);
        
        // Show/hide fields based on type
        const weekGroup = document.querySelector('[for="idea-week-number"]')?.closest('.idea-form-group');
        const yearInputGroup = document.querySelector('[for="idea-year"]')?.closest('.idea-form-group');
        const seasonalGroup = document.querySelector('[for="idea-seasonal-context"]')?.closest('.idea-form-group');
        const startDateGroup = document.getElementById('event-start-date-group');
        const endDateGroup = document.getElementById('event-end-date-group');
        const yearGroup = document.getElementById('event-year-group');
        const evergreenSection = Array.from(document.querySelectorAll('.idea-section')).find(s => 
            s.querySelector('[for="idea-is-evergreen"]')
        );
        const sourcesSection = Array.from(document.querySelectorAll('.idea-section')).find(s => 
            s.querySelector('#idea-add-source')
        );
        
        if (type === 'theme' || type === 'idea') {
            // Show idea/theme-specific fields (same fields for both)
            if (weekGroup) weekGroup.style.display = 'block';
            if (yearInputGroup) yearInputGroup.style.display = 'block';
            if (seasonalGroup) seasonalGroup.style.display = 'block';
            if (evergreenSection) evergreenSection.style.display = 'block';
            if (sourcesSection) {
                sourcesSection.style.display = 'block';
                const addSourceBtn = document.getElementById('idea-add-source');
                if (addSourceBtn) addSourceBtn.style.display = 'block';
            }
            
            // Hide event-specific fields
            if (startDateGroup) startDateGroup.style.display = 'none';
            if (endDateGroup) endDateGroup.style.display = 'none';
            if (yearGroup) yearGroup.style.display = 'none';
        } else if (type === 'annual_event' || type === 'special_event') {
            // Show event-specific fields (both annual and special use same fields)
            this.ensureEventFieldsExist();
            
            if (startDateGroup) startDateGroup.style.display = 'block';
            if (endDateGroup) endDateGroup.style.display = 'block';
            if (yearGroup) yearGroup.style.display = 'block';
            const advanceNoticeGroup = document.getElementById('event-advance-notice-group');
            if (advanceNoticeGroup) advanceNoticeGroup.style.display = 'block';
            
            // Hide idea-specific fields
            if (weekGroup) weekGroup.style.display = 'none';
            if (yearInputGroup) yearInputGroup.style.display = 'none';
            if (seasonalGroup) seasonalGroup.style.display = 'none';
            if (evergreenSection) evergreenSection.style.display = 'none';
            if (sourcesSection) {
                const addSourceBtn = document.getElementById('idea-add-source');
                if (addSourceBtn) addSourceBtn.style.display = 'none';
                const sourcesContainer = document.getElementById('idea-sources-container');
                if (sourcesContainer && sourcesContainer.querySelector('.idea-source-item')) {
                    sourcesContainer.innerHTML = '<p class="idea-help-text">Events do not support sources.</p>';
                }
            }
        }
    }

    ensureEventFieldsExist() {
        let startDateGroup = document.getElementById('event-start-date-group');
        let endDateGroup = document.getElementById('event-end-date-group');
        let yearGroup = document.getElementById('event-year-group');
        
        if (!startDateGroup) {
            const weekNumGroup = document.querySelector('[for="idea-week-number"]')?.closest('.idea-form-group');
            if (weekNumGroup && weekNumGroup.parentNode) {
                startDateGroup = document.createElement('div');
                startDateGroup.className = 'idea-form-group';
                startDateGroup.id = 'event-start-date-group';
                startDateGroup.innerHTML = `
                    <label for="event-start-date" class="idea-label required">Start Date</label>
                    <input type="date" id="event-start-date" name="start_date" class="idea-input" required />
                `;
                weekNumGroup.parentNode.insertBefore(startDateGroup, weekNumGroup.nextSibling);
                
                endDateGroup = document.createElement('div');
                endDateGroup.className = 'idea-form-group';
                endDateGroup.id = 'event-end-date-group';
                endDateGroup.innerHTML = `
                    <label for="event-end-date" class="idea-label required">End Date</label>
                    <input type="date" id="event-end-date" name="end_date" class="idea-input" required />
                `;
                startDateGroup.parentNode.insertBefore(endDateGroup, startDateGroup.nextSibling);
                
                // Auto-update end date when start date changes (only if end date is empty)
                const startDateInput = startDateGroup.querySelector('#event-start-date');
                if (startDateInput) {
                    startDateInput.addEventListener('change', (e) => {
                        const endDateInput = document.getElementById('event-end-date');
                        if (endDateInput && !endDateInput.value) {
                            endDateInput.value = e.target.value;
                        }
                    });
                }
                
                yearGroup = document.createElement('div');
                yearGroup.className = 'idea-form-group';
                yearGroup.id = 'event-year-group';
                // Build year dropdown: "Every year" first, then current year + next 10 years
                const currentYear = new Date().getFullYear();
                let yearOptions = '<option value="every_year">Every year</option>';
                for (let i = 0; i <= 10; i++) {
                    const year = currentYear + i;
                    yearOptions += `<option value="${year}" ${i === 0 ? 'selected' : ''}>${year}</option>`;
                }
                yearGroup.innerHTML = `
                    <label for="event-year" class="idea-label required">Year</label>
                    <select id="event-year" name="year" class="idea-select" required>
                        ${yearOptions}
                    </select>
                `;
                endDateGroup.parentNode.insertBefore(yearGroup, endDateGroup.nextSibling);
                
                // Add advance notice field
                const newAdvanceNoticeGroup = document.createElement('div');
                newAdvanceNoticeGroup.className = 'idea-form-group';
                newAdvanceNoticeGroup.id = 'event-advance-notice-group';
                newAdvanceNoticeGroup.innerHTML = `
                    <label for="event-advance-notice" class="idea-label">Advance Notice</label>
                    <select id="event-advance-notice" name="advance_notice" class="idea-select">
                        <option value="">No advance notice</option>
                        <option value="1">1 week</option>
                        <option value="2">2 weeks</option>
                        <option value="4">4 weeks</option>
                        <option value="8">8 weeks</option>
                        <option value="12">12 weeks</option>
                    </select>
                    <small class="idea-help-text" style="display: block; margin-top: 0.25rem; font-size: 0.75rem; color: #94a3b8;">
                        How far ahead to start promoting this event
                    </small>
                `;
                yearGroup.parentNode.insertBefore(newAdvanceNoticeGroup, yearGroup.nextSibling);
            }
        }
    }

    resetForm() {
        document.getElementById('idea-modal-form').reset();
        document.getElementById('idea-id').value = '';
        this.modal.currentIdeaId = null;
        this.modal.currentEventId = null;
        this.modal._notesData = [];
        this.modal.renderers.renderCategories([]);
        this.modal.renderers.renderSources([]);
        this.modal.renderers.renderNotes([]);
        this.modal.renderers.renderTags([]);
        document.getElementById('idea-evergreen-group').style.display = 'none';
        document.getElementById('idea-evergreen-notes-group').style.display = 'none';
        document.getElementById('idea-max-weeks-group').style.display = 'none';
        
        // Reset type selector - default to idea
        this.modal.currentType = 'idea';
        document.getElementById('type-idea').checked = true;
        document.getElementById('type-theme').checked = false;
        document.getElementById('type-annual-event').checked = false;
        document.getElementById('type-special-event').checked = false;
        document.getElementById('idea-modal-title').textContent = 'Manage Idea';
        
        // Auto-fill week number with current week (for ideas/themes, not events)
        const currentWeek = this.modal.getISOWeekNumber(new Date());
        const weekInput = document.getElementById('idea-week-number');
        if (weekInput) {
            weekInput.value = currentWeek;
            weekInput.removeAttribute('required'); // Remove required since we auto-fill
        }
        
        // Show/hide fields based on default type (idea)
        const weekGroup = document.querySelector('[for="idea-week-number"]')?.closest('.idea-form-group');
        const yearInputGroup = document.querySelector('[for="idea-year"]')?.closest('.idea-form-group');
        if (weekGroup) weekGroup.style.display = 'block';
        if (yearInputGroup) yearInputGroup.style.display = 'block';
        
        const startDateGroup = document.getElementById('event-start-date-group');
        const endDateGroup = document.getElementById('event-end-date-group');
        const yearGroup = document.getElementById('event-year-group');
        if (startDateGroup) startDateGroup.style.display = 'none';
        if (endDateGroup) endDateGroup.style.display = 'none';
        if (yearGroup) yearGroup.style.display = 'none';
        
        // Show all sections
        Array.from(document.querySelectorAll('.idea-section')).forEach(s => s.style.display = 'block');
    }

    buildFormData() {
        const form = document.getElementById('idea-modal-form');
        if (!form.checkValidity()) {
            form.reportValidity();
            return null;
        }

        const ideaId = document.getElementById('idea-id').value;
        const selectedCategories = Array.from(document.querySelectorAll('.idea-category-item input:checked'))
            .map(cb => parseInt(cb.value));

        // Determine type based on type selector
        const isTheme = document.getElementById('type-theme')?.checked || false;
        const isAnnualEvent = document.getElementById('type-annual-event')?.checked || false;
        const isSpecialEvent = document.getElementById('type-special-event')?.checked || false;
        const isEvent = isAnnualEvent || isSpecialEvent;
        
        // Get week number and year - default to current week/year if not set (for ideas/themes)
        let week_number = document.getElementById('idea-week-number').value;
        let year = document.getElementById('idea-year')?.value;
        if (!week_number && !isEvent) {
            week_number = this.modal.getISOWeekNumber(new Date());
        }
        if (!year && !isEvent) {
            year = new Date().getFullYear();
        }

        // Helper to clean string -> null if empty
        const clean = (s) => {
            if (s === undefined || s === null) return null;
            const t = String(s).trim();
            return t.length ? t : null;
        };

        // Build form data with sanitization
        // For events, use event_title/event_description; for ideas/themes, use idea_title/idea_description
        const titleField = isEvent ? 'event_title' : 'idea_title';
        const descriptionField = isEvent ? 'event_description' : 'idea_description';
        
        const formData = {};
        formData[titleField] = clean(document.getElementById('idea-title').value);
        formData[descriptionField] = clean(document.getElementById('idea-description').value);
        
        // Only add idea/theme-specific fields if not an event
        if (!isEvent) {
            formData.week_number = week_number ? Math.max(1, Math.min(53, parseInt(week_number, 10) || 0)) : null;
            formData.year = year ? parseInt(year, 10) : new Date().getFullYear();
            formData.seasonal_context = clean(document.getElementById('idea-seasonal-context').value);
            formData.is_evergreen = !!document.getElementById('idea-is-evergreen').checked;
            formData.can_span_weeks = !!document.getElementById('idea-can-span-weeks').checked;
            formData.max_weeks = parseInt(document.getElementById('idea-max-weeks').value, 10) || 1;
            formData.sources = this.modal.renderers.getSourcesFromForm();
        }
        
        // Common fields
        formData.content_type = clean(document.getElementById('idea-content-type').value);
        formData.priority = clean(document.getElementById('idea-priority').value) || 'random';
        formData.is_recurring = !!document.getElementById('idea-is-recurring').checked;
        formData.tags = this.modal.renderers.getTagsFromForm();
        formData.categories = selectedCategories;
        
        // Important notes (clean up temporary fields before saving)
        const notes = this.modal.renderers.getNotesFromForm().map(note => {
            const cleaned = { text: note.text || '' };
            if (note.id && !note.id.startsWith('temp-')) {
                cleaned.id = note.id;
            } else {
                // Generate UUID-like ID for new notes
                cleaned.id = 'note-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
            }
            if (note.created_at) cleaned.created_at = note.created_at;
            return cleaned;
        }).filter(note => note.text.trim().length > 0);
        if (notes.length > 0) {
            formData.important_notes = notes;
        }

        // Themes and ideas are separate tables - no item_classification needed
        if (!isEvent) {
            // Only include evergreen fields if is_evergreen
            if (formData.is_evergreen) {
                formData.evergreen_frequency = clean(document.getElementById('idea-evergreen-frequency').value);
                formData.evergreen_notes = clean(document.getElementById('idea-evergreen-notes').value);
            }
        }

        // Add event-specific fields if it's an event
        if (isEvent) {
            // Set event_recurrence_type based on which event type is selected
            if (isSpecialEvent) {
                formData.event_recurrence_type = 'one_off';
            } else if (isAnnualEvent) {
                formData.event_recurrence_type = 'annual';
            }
            
            const startDateInput = document.getElementById('event-start-date');
            const endDateInput = document.getElementById('event-end-date');
            const yearInput = document.getElementById('event-year');
            const advanceNoticeInput = document.getElementById('event-advance-notice');
            
            if (startDateInput && clean(startDateInput.value)) formData.start_date = clean(startDateInput.value);
            if (endDateInput && clean(endDateInput.value)) formData.end_date = clean(endDateInput.value);
            
            // Handle year: "every_year" sets is_recurring=true, otherwise use the year value
            if (yearInput && yearInput.value) {
                if (yearInput.value === 'every_year') {
                    formData.is_recurring = true;
                    // For recurring events, we still need a year for the initial occurrence
                    // Use the year from start_date or current year
                    if (startDateInput && startDateInput.value) {
                        const startDate = new Date(startDateInput.value);
                        formData.year = startDate.getFullYear();
                    } else {
                        formData.year = new Date().getFullYear();
                    }
                } else {
                    formData.year = parseInt(yearInput.value, 10) || null;
                }
            }
            
            // Handle advance notice
            if (advanceNoticeInput && advanceNoticeInput.value) {
                formData.advance_notice = parseInt(advanceNoticeInput.value, 10) || null;
            }
        }

        // Remove nulls to avoid sending empty values that may violate patterns
        Object.keys(formData).forEach((k) => {
            if (formData[k] === null || (Array.isArray(formData[k]) && formData[k].length === 0)) {
                delete formData[k];
            }
        });

        return { formData, ideaId, isTheme, isEvent };
    }
}

