/**
 * Standalone Idea Management Modal Component
 * Handles displaying and editing calendar ideas in a beautiful modal
 */

class IdeaModal {
    constructor() {
        this.currentIdeaId = null;
        this.currentEventId = null;
        this.currentType = 'idea'; // 'theme', 'idea', or 'event'
        this.categories = [];
        this.init();
    }

    switchType(type) {
        // Preserve form values before switching (to prevent data loss)
        const titleValue = document.getElementById('idea-title')?.value || '';
        const descriptionValue = document.getElementById('idea-description')?.value || '';
        
        this.currentType = type;
        const title = document.getElementById('idea-modal-title');
        if (type === 'theme') {
            title.textContent = 'Manage Theme';
        } else if (type === 'idea') {
            title.textContent = 'Manage Idea';
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
        } else {
            // Show event-specific fields
            if (!startDateGroup) {
                // Create date fields if they don't exist
                const weekNumGroup = document.querySelector('[for="idea-week-number"]')?.closest('.idea-form-group');
                if (weekNumGroup && weekNumGroup.parentNode) {
                    const newStartDateGroup = document.createElement('div');
                    newStartDateGroup.className = 'idea-form-group';
                    newStartDateGroup.id = 'event-start-date-group';
                    newStartDateGroup.innerHTML = `
                        <label for="event-start-date" class="idea-label required">Start Date</label>
                        <input type="date" id="event-start-date" name="start_date" class="idea-input" required />
                    `;
                    weekNumGroup.parentNode.insertBefore(newStartDateGroup, weekNumGroup.nextSibling);
                    
                    const newEndDateGroup = document.createElement('div');
                    newEndDateGroup.className = 'idea-form-group';
                    newEndDateGroup.id = 'event-end-date-group';
                    newEndDateGroup.innerHTML = `
                        <label for="event-end-date" class="idea-label required">End Date</label>
                        <input type="date" id="event-end-date" name="end_date" class="idea-input" required />
                    `;
                    newStartDateGroup.parentNode.insertBefore(newEndDateGroup, newStartDateGroup.nextSibling);
                    
                    // Auto-update end date when start date changes (only if end date is empty)
                    const startDateInput = newStartDateGroup.querySelector('#event-start-date');
                    if (startDateInput) {
                        startDateInput.addEventListener('change', (e) => {
                            const endDateInput = document.getElementById('event-end-date');
                            if (endDateInput && !endDateInput.value) {
                                endDateInput.value = e.target.value;
                            }
                        });
                    }
                    
                    const newYearGroup = document.createElement('div');
                    newYearGroup.className = 'idea-form-group';
                    newYearGroup.id = 'event-year-group';
                    // Build year dropdown: "Every year" first, then current year + next 10 years
                    const currentYear = new Date().getFullYear();
                    let yearOptions = '<option value="every_year">Every year</option>';
                    for (let i = 0; i <= 10; i++) {
                        const year = currentYear + i;
                        yearOptions += `<option value="${year}" ${i === 0 ? 'selected' : ''}>${year}</option>`;
                    }
                    newYearGroup.innerHTML = `
                        <label for="event-year" class="idea-label required">Year</label>
                        <select id="event-year" name="year" class="idea-select" required>
                            ${yearOptions}
                        </select>
                    `;
                    newEndDateGroup.parentNode.insertBefore(newYearGroup, newEndDateGroup.nextSibling);
                    
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
                    newYearGroup.parentNode.insertBefore(newAdvanceNoticeGroup, newYearGroup.nextSibling);
                }
            } else {
                if (startDateGroup) startDateGroup.style.display = 'block';
                if (endDateGroup) endDateGroup.style.display = 'block';
                if (yearGroup) yearGroup.style.display = 'block';
                // Show advance notice group if it exists
                const advanceNoticeGroup = document.getElementById('event-advance-notice-group');
                if (advanceNoticeGroup) advanceNoticeGroup.style.display = 'block';
            }
            
            // Hide idea-specific fields
            if (weekGroup) weekGroup.style.display = 'none';
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

    init() {
        // Load categories on init
        this.loadCategories();

        // Set up event listeners
        document.getElementById('idea-modal-close')?.addEventListener('click', () => this.close());
        document.getElementById('idea-modal-cancel')?.addEventListener('click', () => this.close());
        document.getElementById('idea-modal-save')?.addEventListener('click', () => this.save());
        
        // Close on overlay click
        document.getElementById('idea-modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'idea-modal') this.close();
        });

        // Add source button
        document.getElementById('idea-add-source')?.addEventListener('click', () => this.addSource());

        // Add note button
        document.getElementById('idea-add-note')?.addEventListener('click', () => this.addNote());

        // Type selector (Theme/Idea/Event) toggle
        document.getElementById('type-theme')?.addEventListener('change', () => this.switchType('theme'));
        document.getElementById('type-idea')?.addEventListener('change', () => this.switchType('idea'));
        document.getElementById('type-event')?.addEventListener('change', () => this.switchType('event'));

        // Evergreen checkbox toggle
        document.getElementById('idea-is-evergreen')?.addEventListener('change', (e) => {
            const evergreenGroup = document.getElementById('idea-evergreen-group');
            const evergreenNotesGroup = document.getElementById('idea-evergreen-notes-group');
            if (e.target.checked) {
                evergreenGroup.style.display = 'block';
                evergreenNotesGroup.style.display = 'block';
            } else {
                evergreenGroup.style.display = 'none';
                evergreenNotesGroup.style.display = 'none';
            }
        });

        // Can span weeks toggle
        document.getElementById('idea-can-span-weeks')?.addEventListener('change', (e) => {
            const maxWeeksGroup = document.getElementById('idea-max-weeks-group');
            maxWeeksGroup.style.display = e.target.checked ? 'block' : 'none';
        });

        // Tags input handler
        document.getElementById('idea-tags-input')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.addTag(e.target.value.trim());
                e.target.value = '';
            }
        });
    }

    async loadCategories() {
        try {
            const response = await fetch('/planning/api/calendar/categories');
            if (response.ok) {
                const data = await response.json();
                this.categories = data.categories || [];
            }
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    async open(ideaId = null, eventData = null) {
        this.currentIdeaId = ideaId;
        this.currentEventId = eventData?.id || null;
        const modal = document.getElementById('idea-modal');
        const loading = document.getElementById('idea-modal-loading');
        const form = document.getElementById('idea-modal-form');

        modal.style.display = 'flex';
        loading.style.display = 'block';
        form.style.display = 'none';

        if (eventData) {
            // Load event data directly
            this.currentType = 'event';
            document.getElementById('type-event').checked = true;
            document.getElementById('type-idea').checked = false;
            await this.loadEvent(eventData);
        } else if (ideaId) {
            // Load existing idea (will determine if it's theme or idea in loadIdea)
            // Default to idea, but loadIdea will check item_classification
            this.currentType = 'idea';
            document.getElementById('type-idea').checked = true;
            document.getElementById('type-event').checked = false;
            document.getElementById('type-theme').checked = false;
            await this.loadIdea(ideaId);
        } else {
            // New item - default to idea
            this.currentType = 'idea';
            document.getElementById('type-idea').checked = true;
            document.getElementById('type-event').checked = false;
            this.resetForm();
        }

        // Apply type-specific field visibility
        this.switchType(this.currentType);

        loading.style.display = 'none';
        form.style.display = 'block';
    }

    openNew(type = 'idea', weekNumber = null) {
        // Reset everything
        this.resetForm();
        
        // Set the type
        this.currentType = type;
        this.currentIdeaId = null;
        this.currentEventId = null;
        
        // Check the appropriate radio button
        document.getElementById('type-theme').checked = (type === 'theme');
        document.getElementById('type-idea').checked = (type === 'idea');
        document.getElementById('type-event').checked = (type === 'event');
        
        // Apply type-specific field visibility
        this.switchType(type);
        
        // Auto-fill week number if provided
        if (weekNumber && type !== 'event') {
            const weekInput = document.getElementById('idea-week-number');
            if (weekInput) {
                weekInput.value = weekNumber;
            }
        } else if (!weekNumber && type !== 'event') {
            // Auto-fill with current week if not provided
            const currentWeek = this.getISOWeekNumber(new Date());
            const weekInput = document.getElementById('idea-week-number');
            if (weekInput) {
                weekInput.value = currentWeek;
            }
        }
        
        // Open the modal
        const modal = document.getElementById('idea-modal');
        const loading = document.getElementById('idea-modal-loading');
        const form = document.getElementById('idea-modal-form');
        
        modal.style.display = 'flex';
        loading.style.display = 'none';
        form.style.display = 'block';
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
                    // Default to current year, or next year if start date is already past this year
                    const today = new Date();
                    const currentYear = today.getFullYear();
                    let yearOptions = '<option value="every_year">Every year</option>';
                    let defaultYear = currentYear;
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
                    
                    // Update default year based on start date when it changes
                    if (startDateInput) {
                        startDateInput.addEventListener('change', (e) => {
                            const yearSelect = document.getElementById('event-year');
                            if (yearSelect && yearSelect.value === String(currentYear)) {
                                const selectedDate = new Date(e.target.value);
                                const selectedYear = selectedDate.getFullYear();
                                if (selectedYear < currentYear || (selectedYear === currentYear && selectedDate < today)) {
                                    // Date is in the past or already passed this year, default to next year
                                    yearSelect.value = String(currentYear + 1);
                                } else {
                                    yearSelect.value = String(selectedYear);
                                }
                            }
                        });
                    }
                    
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
            } else {
                startDateGroup.style.display = 'block';
                endDateGroup.style.display = 'block';
                if (yearGroup) yearGroup.style.display = 'block';
                // Show advance notice group if it exists
                const advanceNoticeGroup = document.getElementById('event-advance-notice-group');
                if (advanceNoticeGroup) advanceNoticeGroup.style.display = 'block';
            }
            
            // Store notes data for reference
            this._notesData = eventData.important_notes || [];
            
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
            const advanceNoticeGroup = document.getElementById('event-advance-notice-group');
            const advanceNoticeSelect = document.getElementById('event-advance-notice');
            if (advanceNoticeSelect && eventData.advance_notice !== undefined && eventData.advance_notice !== null) {
                advanceNoticeSelect.value = String(eventData.advance_notice);
            }
            
            // Load categories (events have categories too)
            this.renderCategories(eventData.categories || []);
            
            // Load tags
            this.renderTags(eventData.tags || []);
            
            // Load important notes
            this.renderNotes(eventData.important_notes || []);
            
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

            // Determine if it's a theme or regular idea
            const classification = (idea.item_classification || 'idea').toLowerCase();
            const isTheme = classification === 'theme';
            
            // Set the appropriate type
            this.currentType = isTheme ? 'theme' : 'idea';
            document.getElementById('type-theme').checked = isTheme;
            document.getElementById('type-idea').checked = !isTheme;
            document.getElementById('type-event').checked = false;
            
            // Update modal title and apply type switching
            this.switchType(isTheme ? 'theme' : 'idea');

            // Store notes data for reference
            this._notesData = idea.important_notes || [];
            
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
            this.renderCategories(idea.categories || []);

            // Load sources (handle both array and JSONB formats)
            let sources = idea.sources || [];
            if (typeof sources === 'string') {
                try {
                    sources = JSON.parse(sources);
                } catch (e) {
                    sources = [];
                }
            }
            this.renderSources(Array.isArray(sources) ? sources : []);

            // Load tags
            this.renderTags(idea.tags || []);
            
            // Load important notes
            this.renderNotes(idea.important_notes || []);

        } catch (error) {
            console.error('Error loading idea:', error);
            alert('Failed to load idea: ' + error.message);
        }
    }

    getISOWeekNumber(date) {
        // Get ISO week number for a date (matches calendar-week-view.js logic)
        const target = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
        const dayNr = (target.getUTCDay() + 6) % 7; // Monday=0
        target.setUTCDate(target.getUTCDate() - dayNr + 3);
        const firstThursday = new Date(Date.UTC(target.getUTCFullYear(), 0, 4));
        const weekNumber = 1 + Math.round(((target - firstThursday) / 86400000 - 3 + ((firstThursday.getUTCDay() + 6) % 7)) / 7);
        return weekNumber;
    }

    resetForm() {
        document.getElementById('idea-modal-form').reset();
        document.getElementById('idea-id').value = '';
        this.currentIdeaId = null;
        this.currentEventId = null;
        this._notesData = [];
        this.renderCategories([]);
        this.renderSources([]);
        this.renderNotes([]);
        this.renderTags([]);
        document.getElementById('idea-evergreen-group').style.display = 'none';
        document.getElementById('idea-evergreen-notes-group').style.display = 'none';
        document.getElementById('idea-max-weeks-group').style.display = 'none';
        
        // Reset type selector - default to idea
        this.currentType = 'idea';
        document.getElementById('type-idea').checked = true;
        document.getElementById('type-theme').checked = false;
        document.getElementById('type-event').checked = false;
        document.getElementById('idea-modal-title').textContent = 'Manage Idea';
        
        // Auto-fill week number with current week (for ideas/themes, not events)
        const currentWeek = this.getISOWeekNumber(new Date());
        const weekInput = document.getElementById('idea-week-number');
        if (weekInput) {
            weekInput.value = currentWeek;
            weekInput.removeAttribute('required'); // Remove required since we auto-fill
        }
        
        // Show/hide fields based on default type (idea)
        const weekGroup = document.querySelector('[for="idea-week-number"]')?.closest('.idea-form-group');
        if (weekGroup) weekGroup.style.display = 'block';
        
        const startDateGroup = document.getElementById('event-start-date-group');
        const endDateGroup = document.getElementById('event-end-date-group');
        const yearGroup = document.getElementById('event-year-group');
        if (startDateGroup) startDateGroup.style.display = 'none';
        if (endDateGroup) endDateGroup.style.display = 'none';
        if (yearGroup) yearGroup.style.display = 'none';
        
        // Show all sections
        Array.from(document.querySelectorAll('.idea-section')).forEach(s => s.style.display = 'block');
    }

    renderCategories(selectedCategories) {
        const container = document.getElementById('idea-categories-container');
        container.innerHTML = '';

        this.categories.forEach(cat => {
            const isSelected = selectedCategories.some(sc => sc.id === cat.id);
            const div = document.createElement('div');
            div.className = `idea-category-item ${isSelected ? 'selected' : ''}`;
            div.innerHTML = `
                <input type="checkbox" value="${cat.id}" ${isSelected ? 'checked' : ''} />
                <span class="idea-category-color" style="background-color: ${cat.color || '#60a5fa'}"></span>
                <span>${cat.name}</span>
            `;
            container.appendChild(div);
        });
    }

    renderSources(sources) {
        const container = document.getElementById('idea-sources-container');
        container.innerHTML = '';

        if (sources.length === 0) {
            container.innerHTML = '<p class="idea-help-text">No sources added yet. Click the + button to add one.</p>';
            return;
        }

        sources.forEach((source, index) => {
            const sourceDiv = document.createElement('div');
            sourceDiv.className = 'idea-source-item';
            sourceDiv.innerHTML = `
                <div class="idea-source-header">
                    <span class="idea-source-item-number">Source ${index + 1}</span>
                    <button type="button" class="idea-source-remove" data-index="${index}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <div class="idea-source-grid">
                    <div class="idea-form-group">
                        <label class="idea-label">Title</label>
                        <input type="text" class="idea-input" data-field="title" data-index="${index}" 
                               value="${this.escapeHtml(source.title || '')}" />
                    </div>
                    <div class="idea-form-group">
                        <label class="idea-label">URL</label>
                        <input type="url" class="idea-input" data-field="url" data-index="${index}" 
                               value="${this.escapeHtml(source.url || '')}" />
                    </div>
                    <div class="idea-form-group">
                        <label class="idea-label">Author</label>
                        <input type="text" class="idea-input" data-field="author" data-index="${index}" 
                               value="${this.escapeHtml(source.author || '')}" />
                    </div>
                    <div class="idea-form-group">
                        <label class="idea-label">Date</label>
                        <input type="date" class="idea-input" data-field="date" data-index="${index}" 
                               value="${source.date || ''}" />
                    </div>
                    <div class="idea-form-group idea-form-group-full">
                        <label class="idea-label">Notes</label>
                        <textarea class="idea-textarea" data-field="notes" data-index="${index}" rows="2">${this.escapeHtml(source.notes || '')}</textarea>
                    </div>
                </div>
            `;
            container.appendChild(sourceDiv);
        });

        // Add remove handlers
        container.querySelectorAll('.idea-source-remove').forEach(btn => {
            btn.addEventListener('click', () => {
                const index = parseInt(btn.dataset.index);
                this.removeSource(index);
            });
        });
    }

    addSource() {
        const sources = this.getSourcesFromForm();
        sources.push({ title: '', url: '', author: '', date: '', notes: '' });
        this.renderSources(sources);
    }

    removeSource(index) {
        const sources = this.getSourcesFromForm();
        sources.splice(index, 1);
        this.renderSources(sources);
    }

    getSourcesFromForm() {
        const sources = [];
        const sourceItems = document.querySelectorAll('.idea-source-item');
        
        sourceItems.forEach((item, index) => {
            const source = {
                title: item.querySelector('[data-field="title"]')?.value || '',
                url: item.querySelector('[data-field="url"]')?.value || '',
                author: item.querySelector('[data-field="author"]')?.value || '',
                date: item.querySelector('[data-field="date"]')?.value || '',
                notes: item.querySelector('[data-field="notes"]')?.value || ''
            };
            sources.push(source);
        });

        return sources;
    }

    renderNotes(notes) {
        const container = document.getElementById('idea-notes-container');
        container.innerHTML = '';

        if (notes.length === 0) {
            return; // Don't show message when empty
        }

        notes.forEach((note, index) => {
            const noteId = note.id || `temp-${Date.now()}-${index}`;
            const isEditing = note._editing || false;
            const noteDiv = document.createElement('div');
            noteDiv.className = `idea-note-item ${isEditing ? 'editing' : ''}`;
            noteDiv.dataset.noteId = noteId;
            
            if (isEditing) {
                noteDiv.innerHTML = `
                    <div class="idea-note-header">
                        <span style="color: #94a3b8; font-size: 0.875rem;">Note ${index + 1}</span>
                        <div class="idea-note-actions">
                            <button type="button" class="idea-note-save" data-note-id="${noteId}">
                                <i class="fas fa-check"></i> Save
                            </button>
                            <button type="button" class="idea-note-cancel" data-note-id="${noteId}">
                                <i class="fas fa-times"></i> Cancel
                            </button>
                        </div>
                    </div>
                    <textarea class="idea-note-textarea" data-note-id="${noteId}">${this.escapeHtml(note.text || '')}</textarea>
                `;
            } else {
                noteDiv.innerHTML = `
                    <div class="idea-note-header">
                        <span style="color: #94a3b8; font-size: 0.875rem;">Note ${index + 1}</span>
                        <div class="idea-note-actions">
                            <button type="button" class="idea-note-edit" data-note-id="${noteId}">
                                <i class="fas fa-edit"></i> Edit
                            </button>
                            <button type="button" class="idea-note-remove" data-note-id="${noteId}">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="idea-note-text">${this.escapeHtml(note.text || '')}</div>
                `;
            }
            
            container.appendChild(noteDiv);
        });

        // Add event handlers
        container.querySelectorAll('.idea-note-edit').forEach(btn => {
            btn.addEventListener('click', () => {
                const noteId = btn.dataset.noteId;
                this.editNote(noteId);
            });
        });

        container.querySelectorAll('.idea-note-save').forEach(btn => {
            btn.addEventListener('click', () => {
                const noteId = btn.dataset.noteId;
                this.saveNote(noteId);
            });
        });

        container.querySelectorAll('.idea-note-cancel').forEach(btn => {
            btn.addEventListener('click', () => {
                const noteId = btn.dataset.noteId;
                this.cancelEditNote(noteId);
            });
        });

        container.querySelectorAll('.idea-note-remove').forEach(btn => {
            btn.addEventListener('click', () => {
                const noteId = btn.dataset.noteId;
                this.removeNote(noteId);
            });
        });
    }

    addNote() {
        const notes = this.getNotesFromForm();
        const newNote = {
            id: `temp-${Date.now()}`,
            text: '',
            created_at: new Date().toISOString(),
            _editing: true
        };
        notes.push(newNote);
        this.renderNotes(notes);
    }

    editNote(noteId) {
        const notes = this.getNotesFromForm();
        const noteIndex = notes.findIndex(n => (n.id || n._tempId) === noteId);
        if (noteIndex !== -1) {
            notes[noteIndex]._editing = true;
            notes[noteIndex]._originalText = notes[noteIndex].text;
            this.renderNotes(notes);
        }
    }

    saveNote(noteId) {
        const notes = this.getNotesFromForm();
        const noteIndex = notes.findIndex(n => (n.id || n._tempId) === noteId);
        if (noteIndex !== -1) {
            const textarea = document.querySelector(`textarea[data-note-id="${noteId}"]`);
            if (textarea) {
                const newText = textarea.value.trim();
                if (!newText) {
                    // Empty note - remove it
                    this.removeNote(noteId);
                    return;
                }
                notes[noteIndex].text = newText;
                notes[noteIndex]._editing = false;
                delete notes[noteIndex]._originalText;
                // Ensure it has an ID if it was temporary
                if (!notes[noteIndex].id || notes[noteIndex].id.startsWith('temp-')) {
                    notes[noteIndex].id = notes[noteIndex].id || `temp-${Date.now()}`;
                }
                if (!notes[noteIndex].created_at) {
                    notes[noteIndex].created_at = new Date().toISOString();
                }
                this.renderNotes(notes);
            }
        }
    }

    cancelEditNote(noteId) {
        const notes = this.getNotesFromForm();
        const noteIndex = notes.findIndex(n => (n.id || n._tempId) === noteId);
        if (noteIndex !== -1) {
            if (notes[noteIndex]._originalText !== undefined) {
                notes[noteIndex].text = notes[noteIndex]._originalText;
            }
            notes[noteIndex]._editing = false;
            delete notes[noteIndex]._originalText;
            // If it was a new empty note, remove it
            if (!notes[noteIndex].text && (!notes[noteIndex].id || notes[noteIndex].id.startsWith('temp-'))) {
                notes.splice(noteIndex, 1);
            }
            this.renderNotes(notes);
        }
    }

    removeNote(noteId) {
        if (!confirm('Delete this note?')) return;
        const notes = this.getNotesFromForm();
        const noteIndex = notes.findIndex(n => (n.id || n._tempId) === noteId);
        if (noteIndex !== -1) {
            notes.splice(noteIndex, 1);
            this.renderNotes(notes);
        }
    }

    getNotesFromForm() {
        const notes = [];
        const noteItems = document.querySelectorAll('.idea-note-item');
        
        noteItems.forEach((item) => {
            const noteId = item.dataset.noteId;
            const isEditing = item.classList.contains('editing');
            
            let text = '';
            if (isEditing) {
                const textarea = item.querySelector('.idea-note-textarea');
                text = textarea ? textarea.value.trim() : '';
            } else {
                const textDiv = item.querySelector('.idea-note-text');
                text = textDiv ? textDiv.textContent.trim() : '';
            }
            
            // Find the original note data if it exists
            const existingNote = this._notesData?.find(n => (n.id || n._tempId) === noteId);
            const note = {
                id: existingNote?.id || noteId,
                text: text,
                created_at: existingNote?.created_at || new Date().toISOString(),
                _editing: isEditing,
                _tempId: noteId
            };
            
            // Only include non-empty notes or existing notes
            if (text || existingNote) {
                notes.push(note);
            }
        });
        
        return notes;
    }

    renderTags(tags) {
        const container = document.getElementById('idea-tags-container');
        container.innerHTML = '';

        tags.forEach(tag => {
            const tagDiv = document.createElement('div');
            tagDiv.className = 'idea-tag';
            tagDiv.innerHTML = `
                <span>${this.escapeHtml(tag)}</span>
                <button type="button" class="idea-tag-remove" data-tag="${this.escapeHtml(tag)}">
                    <i class="fas fa-times"></i>
                </button>
            `;
            container.appendChild(tagDiv);
        });

        // Add remove handlers
        container.querySelectorAll('.idea-tag-remove').forEach(btn => {
            btn.addEventListener('click', () => {
                const tag = btn.dataset.tag;
                this.removeTag(tag);
            });
        });
    }

    addTag(tag) {
        if (!tag) return;
        const tags = this.getTagsFromForm();
        if (!tags.includes(tag)) {
            tags.push(tag);
            this.renderTags(tags);
        }
    }

    removeTag(tag) {
        const tags = this.getTagsFromForm();
        const index = tags.indexOf(tag);
        if (index > -1) {
            tags.splice(index, 1);
            this.renderTags(tags);
        }
    }

    getTagsFromForm() {
        const tags = [];
        document.querySelectorAll('.idea-tag span').forEach(span => {
            const text = span.textContent.trim();
            if (text) tags.push(text);
        });
        return tags;
    }

    async save() {
        const form = document.getElementById('idea-modal-form');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const ideaId = document.getElementById('idea-id').value;
        const selectedCategories = Array.from(document.querySelectorAll('.idea-category-item input:checked'))
            .map(cb => parseInt(cb.value));

        // Determine type based on type selector
        const isTheme = document.getElementById('type-theme')?.checked || false;
        const isEvent = document.getElementById('type-event')?.checked || false;
        const isIdea = document.getElementById('type-idea')?.checked || false;
        
        // Get week number - default to current week if not set (for ideas/themes)
        let week_number = document.getElementById('idea-week-number').value;
        if (!week_number && !isEvent) {
            week_number = this.getISOWeekNumber(new Date());
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
            formData.seasonal_context = clean(document.getElementById('idea-seasonal-context').value);
            formData.is_evergreen = !!document.getElementById('idea-is-evergreen').checked;
            formData.can_span_weeks = !!document.getElementById('idea-can-span-weeks').checked;
            formData.max_weeks = parseInt(document.getElementById('idea-max-weeks').value, 10) || 1;
            formData.sources = this.getSourcesFromForm();
        }
        
        // Common fields
        formData.content_type = clean(document.getElementById('idea-content-type').value);
        formData.priority = clean(document.getElementById('idea-priority').value) || 'random';
        formData.is_recurring = !!document.getElementById('idea-is-recurring').checked;
        formData.tags = this.getTagsFromForm();
        formData.categories = selectedCategories;
        
        // Important notes (clean up temporary fields before saving)
        const notes = this.getNotesFromForm().map(note => {
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

        // Set item_classification for themes and ideas (only for ideas/themes, not events)
        if (!isEvent) {
            if (isTheme) {
                formData.item_classification = 'theme';
            } else if (isIdea) {
                formData.item_classification = 'idea';
            }
            
            // Only include evergreen fields if is_evergreen
            if (formData.is_evergreen) {
                formData.evergreen_frequency = clean(document.getElementById('idea-evergreen-frequency').value);
                formData.evergreen_notes = clean(document.getElementById('idea-evergreen-notes').value);
            }
        }

        // Add event-specific fields if it's an event
        if (isEvent) {
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

        try {
            // Check if we're converting an event to an idea
            // We started with an event (currentEventId exists) but now saving as an idea (type is "idea", not "event")
            // Also check if ideaId matches currentEventId (event ID was put in idea-id field when loading event)
            const isConvertingEventToIdea = !isEvent && this.currentEventId && 
                (!ideaId || String(ideaId) === String(this.currentEventId));
            
            // Check if we're converting an idea to an event
            // We started with an idea (currentIdeaId exists) but now saving as an event (type is "event")
            const isConvertingIdeaToEvent = isEvent && this.currentIdeaId && !this.currentEventId;
            
            // Remove nulls to avoid sending empty values that may violate patterns
            Object.keys(formData).forEach((k) => {
                if (formData[k] === null || (Array.isArray(formData[k]) && formData[k].length === 0)) {
                    delete formData[k];
                }
            });

            let url, method;
            
            if (isConvertingEventToIdea) {
                // Use conversion endpoint to atomically convert event to idea
                url = `/planning/api/calendar/events/${this.currentEventId}/convert-to-idea`;
                method = 'POST';
            } else if (isConvertingIdeaToEvent) {
                // Converting idea to event: create new event and delete the idea
                // First, create the event
                url = '/planning/api/calendar/events';
                method = 'POST';
                
                const response = await fetch(url, {
                    method,
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
                if (this.currentIdeaId && newEventId) {
                    const deleteResponse = await fetch(`/planning/api/calendar/ideas/${this.currentIdeaId}`, {
                        method: 'DELETE'
                    });
                    if (!deleteResponse.ok) {
                        console.warn('Event created but failed to delete original idea:', this.currentIdeaId);
                    }
                }

                alert('Idea converted to event successfully');
                this.close();
                // Trigger page reload or refresh calendar
                if (window.location.pathname.includes('/calendar')) {
                    window.location.reload();
                }
                return;
            } else if (isEvent) {
                // Handle events separately
                // For events, use currentEventId (ignore ideaId which might contain the event ID)
                if (this.currentEventId) {
                    // Updating an existing event (using event ID from currentEventId)
                    url = `/planning/api/calendar/events/${this.currentEventId}`;
                    method = 'PUT';
                } else {
                    // Creating a new event
                    url = '/planning/api/calendar/events';
                    method = 'POST';
                }
            } else if (!ideaId) {
                // Creating a new idea
                url = '/planning/api/calendar/ideas';
                method = 'POST';
            } else {
                // Updating an existing idea
                url = `/planning/api/calendar/ideas/${ideaId}`;
                method = 'PUT';
            }

            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                let message = 'Failed to save idea';
                try {
                    const error = await response.json();
                    message = error.error || message;
                } catch (_) {
                    const text = await response.text();
                    message = text || message;
                }
                throw new Error(message);
            }

            const data = await response.json();
            this.close();
            
            // Trigger custom event for other components to refresh
            window.dispatchEvent(new CustomEvent('idea-saved', { detail: data }));
            
        } catch (error) {
            console.error('Error saving idea:', error);
            alert('Failed to save idea: ' + error.message);
        }
    }

    close() {
        document.getElementById('idea-modal').style.display = 'none';
        this.currentIdeaId = null;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize singleton instance
let ideaModalInstance = null;

function getIdeaModal() {
    if (!ideaModalInstance) {
        ideaModalInstance = new IdeaModal();
    }
    return ideaModalInstance;
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { IdeaModal, getIdeaModal };
}

