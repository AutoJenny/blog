/**
 * Idea Modal Renderers
 * UI rendering helpers for categories, sources, notes, and tags
 */

class IdeaModalRenderers {
    constructor(modal) {
        this.modal = modal; // Reference to parent modal instance
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    renderCategories(selectedCategories) {
        const container = document.getElementById('idea-categories-container');
        if (!container) return;
        
        container.innerHTML = '';

        this.modal.categories.forEach(cat => {
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
        if (!container) return;
        
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
                this.modal.removeSource(index);
            });
        });
    }

    addSource() {
        const sources = this.modal.getSourcesFromForm();
        sources.push({ title: '', url: '', author: '', date: '', notes: '' });
        this.renderSources(sources);
    }

    removeSource(index) {
        const sources = this.modal.getSourcesFromForm();
        sources.splice(index, 1);
        this.renderSources(sources);
    }

    getSourcesFromForm() {
        const sources = [];
        const sourceItems = document.querySelectorAll('.idea-source-item');
        
        sourceItems.forEach((item) => {
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
        if (!container) return;
        
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
                this.modal.editNote(noteId);
            });
        });

        container.querySelectorAll('.idea-note-save').forEach(btn => {
            btn.addEventListener('click', () => {
                const noteId = btn.dataset.noteId;
                this.modal.saveNote(noteId);
            });
        });

        container.querySelectorAll('.idea-note-cancel').forEach(btn => {
            btn.addEventListener('click', () => {
                const noteId = btn.dataset.noteId;
                this.modal.cancelEditNote(noteId);
            });
        });

        container.querySelectorAll('.idea-note-remove').forEach(btn => {
            btn.addEventListener('click', () => {
                const noteId = btn.dataset.noteId;
                this.modal.removeNote(noteId);
            });
        });
    }

    addNote() {
        const notes = this.modal.getNotesFromForm();
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
        const notes = this.modal.getNotesFromForm();
        const noteIndex = notes.findIndex(n => (n.id || n._tempId) === noteId);
        if (noteIndex !== -1) {
            notes[noteIndex]._editing = true;
            notes[noteIndex]._originalText = notes[noteIndex].text;
            this.renderNotes(notes);
        }
    }

    saveNote(noteId) {
        const notes = this.modal.getNotesFromForm();
        const noteIndex = notes.findIndex(n => (n.id || n._tempId) === noteId);
        if (noteIndex !== -1) {
            const textarea = document.querySelector(`textarea[data-note-id="${noteId}"]`);
            if (textarea) {
                const newText = textarea.value.trim();
                if (!newText) {
                    // Empty note - remove it
                    this.modal.removeNote(noteId);
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
        const notes = this.modal.getNotesFromForm();
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
        const notes = this.modal.getNotesFromForm();
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
            const existingNote = this.modal._notesData?.find(n => (n.id || n._tempId) === noteId);
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
        if (!container) return;
        
        container.innerHTML = '';

        // Ensure tags is an array
        if (!tags) {
            tags = [];
        } else if (!Array.isArray(tags)) {
            // If tags is an object, convert to array of strings
            if (typeof tags === 'object') {
                tags = Object.keys(tags).map(key => {
                    const value = tags[key];
                    return value ? `${key}: ${value}` : key;
                });
            } else {
                tags = [];
            }
        }

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
                this.modal.removeTag(tag);
            });
        });
    }

    addTag(tag) {
        if (!tag) return;
        const tags = this.modal.getTagsFromForm();
        if (!tags.includes(tag)) {
            tags.push(tag);
            this.renderTags(tags);
        }
    }

    removeTag(tag) {
        const tags = this.modal.getTagsFromForm();
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
}

