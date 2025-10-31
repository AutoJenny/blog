/**
 * Standalone Idea Management Modal Component
 * Handles displaying and editing calendar ideas in a beautiful modal
 */

class IdeaModal {
    constructor() {
        this.currentIdeaId = null;
        this.currentEventId = null;
        this.currentType = 'idea'; // 'idea' or 'event'
        this.categories = [];
        this.init();
    }

    switchType(type) {
        this.currentType = type;
        const title = document.getElementById('idea-modal-title');
        title.textContent = type === 'idea' ? 'Manage Idea' : 'Manage Event';
        
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
        
        if (type === 'idea') {
            // Show idea-specific fields
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
                    
                    const newYearGroup = document.createElement('div');
                    newYearGroup.className = 'idea-form-group';
                    newYearGroup.id = 'event-year-group';
                    newYearGroup.innerHTML = `
                        <label for="event-year" class="idea-label required">Year</label>
                        <input type="number" id="event-year" name="year" class="idea-input" min="2020" max="2100" required />
                    `;
                    newEndDateGroup.parentNode.insertBefore(newYearGroup, newEndDateGroup.nextSibling);
                }
            } else {
                if (startDateGroup) startDateGroup.style.display = 'block';
                if (endDateGroup) endDateGroup.style.display = 'block';
                if (yearGroup) yearGroup.style.display = 'block';
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

        // Type selector (Idea/Event) toggle
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
            // Load existing idea
            this.currentType = 'idea';
            document.getElementById('type-idea').checked = true;
            document.getElementById('type-event').checked = false;
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
                    
                    yearGroup = document.createElement('div');
                    yearGroup.className = 'idea-form-group';
                    yearGroup.id = 'event-year-group';
                    yearGroup.innerHTML = `
                        <label for="event-year" class="idea-label required">Year</label>
                        <input type="number" id="event-year" name="year" class="idea-input" min="2020" max="2100" required />
                    `;
                    endDateGroup.parentNode.insertBefore(yearGroup, endDateGroup.nextSibling);
                }
            } else {
                startDateGroup.style.display = 'block';
                endDateGroup.style.display = 'block';
                if (yearGroup) yearGroup.style.display = 'block';
            }
            
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
                document.getElementById('event-year').value = eventData.year || new Date().getFullYear();
            }
            
            // Load categories (events have categories too)
            this.renderCategories(eventData.categories || []);
            
            // Load tags
            this.renderTags(eventData.tags || []);
            
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

        } catch (error) {
            console.error('Error loading idea:', error);
            alert('Failed to load idea: ' + error.message);
        }
    }

    resetForm() {
        document.getElementById('idea-modal-form').reset();
        document.getElementById('idea-id').value = '';
        this.renderCategories([]);
        this.renderSources([]);
        this.renderTags([]);
        document.getElementById('idea-evergreen-group').style.display = 'none';
        document.getElementById('idea-evergreen-notes-group').style.display = 'none';
        document.getElementById('idea-max-weeks-group').style.display = 'none';
        
        // Reset modal title
        document.getElementById('idea-modal-title').textContent = 'Manage Idea';
        
        // Show/hide fields based on type
        const weekGroup = document.querySelector('[for="idea-week-number"]')?.closest('.idea-form-group');
        if (weekGroup) weekGroup.style.display = 'block';
        
        const startDateGroup = document.getElementById('event-start-date-group');
        const endDateGroup = document.getElementById('event-end-date-group');
        if (startDateGroup) startDateGroup.style.display = 'none';
        if (endDateGroup) endDateGroup.style.display = 'none';
        
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

        // Determine if this is an idea or event based on type selector
        const isEvent = document.getElementById('type-event')?.checked || false;
        
        // Get week number - default to current week if not set (for ideas)
        let week_number = document.getElementById('idea-week-number').value;
        if (!week_number && !isEvent) {
            week_number = this.getISOWeekNumber(new Date());
        }

        const formData = {
            idea_title: document.getElementById('idea-title').value,
            idea_description: document.getElementById('idea-description').value,
            week_number: week_number ? parseInt(week_number) : null,
            content_type: document.getElementById('idea-content-type').value || null,
            seasonal_context: document.getElementById('idea-seasonal-context').value || null,
            priority: document.getElementById('idea-priority').value,
            is_recurring: document.getElementById('idea-is-recurring').checked,
            is_evergreen: document.getElementById('idea-is-evergreen').checked,
            evergreen_frequency: document.getElementById('idea-evergreen-frequency').value,
            evergreen_notes: document.getElementById('idea-evergreen-notes').value || null,
            can_span_weeks: document.getElementById('idea-can-span-weeks').checked,
            max_weeks: parseInt(document.getElementById('idea-max-weeks').value) || 1,
            tags: this.getTagsFromForm(),
            sources: this.getSourcesFromForm(),
            categories: selectedCategories
        };

        // Add event-specific fields if it's an event
        if (isEvent) {
            const startDateInput = document.getElementById('event-start-date');
            const endDateInput = document.getElementById('event-end-date');
            const yearInput = document.getElementById('event-year');
            if (startDateInput) formData.start_date = startDateInput.value;
            if (endDateInput) formData.end_date = endDateInput.value;
            if (yearInput) formData.year = parseInt(yearInput.value);
        }

        try {
            // If we're converting from event to idea, always create new (ideaId will be event ID)
            // If ideaId exists and it's actually an idea (not event), update it
            // Otherwise create new
            const shouldCreate = !ideaId || (this.currentEventId && ideaId == this.currentEventId);
            
            const url = shouldCreate 
                ? '/planning/api/calendar/ideas/add'
                : `/planning/api/calendar/ideas/${ideaId}`;
            const method = shouldCreate ? 'POST' : 'PUT';

            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to save idea');
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

