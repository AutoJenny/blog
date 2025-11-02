/**
 * Idea Modal Core
 * Main class and coordination for the idea management modal
 */

class IdeaModal {
    constructor() {
        this.currentIdeaId = null;
        this.currentEventId = null;
        this.currentType = 'idea'; // 'theme', 'idea', or 'event'
        this.originalType = null; // Track original type before any switching
        this.categories = [];
        this._notesData = [];
        
        // Initialize sub-modules
        this.renderers = new IdeaModalRenderers(this);
        this.forms = new IdeaModalForms(this);
        this.api = new IdeaModalAPI(this);
        this.conversions = new IdeaModalConversions(this);
        
        this.init();
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

    init() {
        // Load categories on init
        this.api.loadCategories();

        // Set up event listeners
        document.getElementById('idea-modal-close')?.addEventListener('click', () => this.close());
        document.getElementById('idea-modal-cancel')?.addEventListener('click', () => this.close());
        document.getElementById('idea-modal-save')?.addEventListener('click', () => this.save());
        document.getElementById('idea-modal-delete')?.addEventListener('click', () => this.delete());
        
        // Close on overlay click
        document.getElementById('idea-modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'idea-modal') this.close();
        });

        // Add source button
        document.getElementById('idea-add-source')?.addEventListener('click', () => this.renderers.addSource());

        // Add note button
        document.getElementById('idea-add-note')?.addEventListener('click', () => this.renderers.addNote());

        // Type selector (Theme/Idea/Event) toggle
        document.getElementById('type-theme')?.addEventListener('change', () => this.forms.switchType('theme'));
        document.getElementById('type-idea')?.addEventListener('change', () => this.forms.switchType('idea'));
        document.getElementById('type-event')?.addEventListener('change', () => this.forms.switchType('event'));

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
                this.renderers.addTag(e.target.value.trim());
                e.target.value = '';
            }
        });
    }

    async openTheme(themeId, themeData = null) {
        // Load theme data if not provided
        if (!themeData && themeId) {
            try {
                const response = await fetch(`/planning/api/calendar/themes/${themeId}`);
                if (!response.ok) throw new Error('Failed to load theme');
                const data = await response.json();
                themeData = data.theme || data;
            } catch (error) {
                console.error('Error loading theme:', error);
                alert('Failed to load theme: ' + error.message);
                return;
            }
        }
        
        // Reset form
        this.forms.resetForm();
        
        // Set current theme ID
        this.currentIdeaId = themeId;
        this.currentEventId = null;
        this.currentType = 'theme';
        this.originalType = 'theme'; // Track that we started with a theme
        
        // Set radio button
        document.getElementById('type-theme').checked = true;
        document.getElementById('type-idea').checked = false;
        document.getElementById('type-event').checked = false;
        
        // Show delete button for existing themes
        const deleteBtn = document.getElementById('idea-modal-delete');
        if (deleteBtn) {
            deleteBtn.style.display = 'block';
        }
        
        // Apply type-specific field visibility
        this.forms.switchType('theme');
        
        // Populate form with theme data
        if (themeData) {
            this.api.loadThemeData(themeData);
        }
        
        // Open modal
        const modal = document.getElementById('idea-modal');
        const loading = document.getElementById('idea-modal-loading');
        const form = document.getElementById('idea-modal-form');
        
        if (modal) {
            modal.style.display = 'flex';
            loading.style.display = 'none';
            form.style.display = 'block';
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
            this.originalType = 'event';
            document.getElementById('type-event').checked = true;
            document.getElementById('type-idea').checked = false;
            await this.api.loadEvent(eventData);
        } else if (ideaId) {
            // Load existing idea (will determine if it's theme or idea in loadIdea)
            this.currentType = 'idea';
            this.originalType = 'idea'; // Will be updated if loadIdea finds it's a theme
            document.getElementById('type-idea').checked = true;
            document.getElementById('type-event').checked = false;
            document.getElementById('type-theme').checked = false;
            await this.api.loadIdea(ideaId);
        } else {
            // New item - default to idea
            this.currentType = 'idea';
            this.originalType = 'idea';
            document.getElementById('type-idea').checked = true;
            document.getElementById('type-event').checked = false;
            this.forms.resetForm();
        }
        
        // Show delete button only for existing items (ideas or events)
        const deleteBtn = document.getElementById('idea-modal-delete');
        if (deleteBtn) {
            if ((this.currentIdeaId || this.currentEventId)) {
                deleteBtn.style.display = 'block';
            } else {
                deleteBtn.style.display = 'none';
            }
        }

        // Apply type-specific field visibility
        this.forms.switchType(this.currentType);

        loading.style.display = 'none';
        form.style.display = 'block';
    }

    openNew(type = 'idea', weekNumber = null) {
        // Reset everything
        this.forms.resetForm();
        
        // Set the type
        this.currentType = type;
        this.originalType = type; // Track original type
        this.currentIdeaId = null;
        this.currentEventId = null;
        
        // Hide delete button for new items
        const deleteBtn = document.getElementById('idea-modal-delete');
        if (deleteBtn) {
            deleteBtn.style.display = 'none';
        }
        
        // Check the appropriate radio button
        document.getElementById('type-theme').checked = (type === 'theme');
        document.getElementById('type-idea').checked = (type === 'idea');
        document.getElementById('type-event').checked = (type === 'event');
        
        // Apply type-specific field visibility
        this.forms.switchType(type);
        
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

    async save() {
        // Build form data
        const formResult = this.forms.buildFormData();
        if (!formResult) return; // Validation failed
        
        const { formData, ideaId, isTheme, isEvent } = formResult;

        try {
            // Detect conversions
            const conversions = this.conversions.detectConversion(isTheme, isEvent, ideaId);
            const { isConvertingThemeToIdea, isConvertingEventToIdea, isConvertingIdeaToEvent } = conversions;
            
            let url, method;
            let result;
            
            if (isConvertingEventToIdea) {
                result = await this.conversions.convertEventToIdea(formData);
                alert('Event converted to idea successfully');
                this.close();
                if (window.location.pathname.includes('/calendar')) {
                    window.location.reload();
                }
                return;
            } else if (isConvertingIdeaToEvent) {
                await this.conversions.convertIdeaToEvent(formData);
                alert('Idea converted to event successfully');
                this.close();
                if (window.location.pathname.includes('/calendar')) {
                    window.location.reload();
                }
                return;
            } else if (isConvertingThemeToIdea) {
                await this.conversions.convertThemeToIdea(formData);
                alert('Theme converted to idea successfully');
                this.close();
                if (window.location.pathname.includes('/calendar')) {
                    window.location.reload();
                }
                return;
            } else if (isTheme) {
                // Handle themes separately
                const wasTheme = this.originalType === 'theme' && this.currentIdeaId;
                if (this.currentIdeaId && wasTheme) {
                    // Updating an existing theme
                    url = `/planning/api/calendar/themes/${this.currentIdeaId}`;
                    method = 'PUT';
                    // Map idea_title to theme_title
                    if (formData.idea_title) {
                        formData.theme_title = formData.idea_title;
                        delete formData.idea_title;
                    }
                    if (formData.idea_description) {
                        formData.theme_description = formData.idea_description;
                        delete formData.idea_description;
                    }
                } else {
                    // Creating a new theme
                    url = '/planning/api/calendar/themes';
                    method = 'POST';
                    // Map idea_title to theme_title
                    if (formData.idea_title) {
                        formData.theme_title = formData.idea_title;
                        delete formData.idea_title;
                    }
                    if (formData.idea_description) {
                        formData.theme_description = formData.idea_description;
                        delete formData.idea_description;
                    }
                }
            } else if (isEvent) {
                // Handle events separately
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
                let message = 'Failed to save item';
                try {
                    const error = await response.json();
                    message = error.error || message;
                } catch (_) {
                    const text = await response.text();
                    message = text || message;
                }
                throw new Error(message);
            }

            result = await response.json();
            this.close();
            
            // Trigger custom event for other components to refresh
            window.dispatchEvent(new CustomEvent('idea-saved', { detail: result }));
            
        } catch (error) {
            console.error('Error saving item:', error);
            alert('Failed to save item: ' + error.message);
        }
    }

    async isThemeId(id) {
        return this.api.isThemeId(id);
    }
    
    async delete() {
        if (!this.currentIdeaId && !this.currentEventId) {
            return;
        }
        
        if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
            return;
        }
        
        try {
            let url, itemType;
            // Check if it's a theme (currentType is theme)
            const isTheme = this.currentType === 'theme';
            
            if (this.currentEventId) {
                url = `/planning/api/calendar/events/${this.currentEventId}`;
                itemType = 'event';
            } else if (isTheme && this.currentIdeaId) {
                url = `/planning/api/calendar/themes/${this.currentIdeaId}`;
                itemType = 'theme';
            } else if (this.currentIdeaId) {
                url = `/planning/api/calendar/ideas/${this.currentIdeaId}`;
                itemType = 'idea';
            } else {
                return;
            }
            
            const response = await fetch(url, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `Failed to delete ${itemType}`);
            }
            
            alert(`${itemType.charAt(0).toUpperCase() + itemType.slice(1)} deleted successfully`);
            this.close();
            
            // Trigger page reload or refresh calendar if we're on a calendar page
            if (window.location.pathname.includes('/calendar')) {
                window.location.reload();
            } else {
                // Trigger a custom event that pages can listen to
                window.dispatchEvent(new CustomEvent('idea-deleted', {
                    detail: { id: this.currentIdeaId || this.currentEventId, type: itemType }
                }));
            }
        } catch (error) {
            console.error('Error deleting item:', error);
            alert(`Failed to delete: ${error.message}`);
        }
    }

    close() {
        document.getElementById('idea-modal').style.display = 'none';
        this.currentIdeaId = null;
    }

    // Delegation methods for backward compatibility
    addSource() { this.renderers.addSource(); }
    removeSource(index) { this.renderers.removeSource(index); }
    getSourcesFromForm() { return this.renderers.getSourcesFromForm(); }
    addNote() { this.renderers.addNote(); }
    editNote(noteId) { this.renderers.editNote(noteId); }
    saveNote(noteId) { this.renderers.saveNote(noteId); }
    cancelEditNote(noteId) { this.renderers.cancelEditNote(noteId); }
    removeNote(noteId) { this.renderers.removeNote(noteId); }
    getNotesFromForm() { return this.renderers.getNotesFromForm(); }
    addTag(tag) { this.renderers.addTag(tag); }
    removeTag(tag) { this.renderers.removeTag(tag); }
    getTagsFromForm() { return this.renderers.getTagsFromForm(); }
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

