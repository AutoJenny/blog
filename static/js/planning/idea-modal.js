/**
 * Standalone Idea Management Modal Component
 * Handles displaying and editing calendar ideas in a beautiful modal
 */

class IdeaModal {
    constructor() {
        this.currentIdeaId = null;
        this.categories = [];
        this.init();
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

    async open(ideaId = null) {
        this.currentIdeaId = ideaId;
        const modal = document.getElementById('idea-modal');
        const loading = document.getElementById('idea-modal-loading');
        const form = document.getElementById('idea-modal-form');

        modal.style.display = 'flex';
        loading.style.display = 'block';
        form.style.display = 'none';

        if (ideaId) {
            // Load existing idea
            await this.loadIdea(ideaId);
        } else {
            // New idea
            this.resetForm();
        }

        loading.style.display = 'none';
        form.style.display = 'block';
    }

    async loadIdea(ideaId) {
        try {
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

            // Load sources
            this.renderSources(idea.sources || []);

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

        const formData = {
            idea_title: document.getElementById('idea-title').value,
            idea_description: document.getElementById('idea-description').value,
            week_number: parseInt(document.getElementById('idea-week-number').value),
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

        try {
            const url = ideaId 
                ? `/planning/api/calendar/ideas/${ideaId}`
                : '/planning/api/calendar/ideas/add';
            const method = ideaId ? 'PUT' : 'POST';

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

