/**
 * Output Panel - Modular Component
 * Self-contained module for managing content editing and output display
 */

class OutputPanel {
    constructor(options = {}) {
        this.containerId = options.containerId || 'output-panel';
        this.postId = options.postId || window.postId;
        this.currentSectionId = null;
        
        // Callbacks for external communication
        this.callbacks = {
            onContentChange: options.onContentChange || (() => {}),
            onSave: options.onSave || (() => {}),
            onRegenerate: options.onRegenerate || (() => {}),
            onPreview: options.onPreview || (() => {}),
            onSectionLoad: options.onSectionLoad || (() => {})
        };
        
        // DOM elements
        this.panel = null;
        this.contentEditor = null;
        this.currentSectionTitle = null;
        this.wordCount = null;
        this.lastSaved = null;
        this.saveBtn = null;
        this.regenerateBtn = null;
        this.previewBtn = null;
        
        this.init();
    }

    init() {
        this.bindElements();
        this.setupEventListeners();
        this.restoreAccordionState();
    }

    bindElements() {
        this.panel = document.getElementById(this.containerId);
        this.contentEditor = document.getElementById('content-editor');
        this.currentSectionTitle = document.getElementById('current-section-title');
        this.wordCount = document.getElementById('word-count');
        this.lastSaved = document.getElementById('last-saved');
        this.saveBtn = document.getElementById('save-btn');
        this.regenerateBtn = document.getElementById('regenerate-btn');
        this.previewBtn = document.getElementById('preview-btn');
    }

    setupEventListeners() {
        // Content editor events
        if (this.contentEditor) {
            this.contentEditor.addEventListener('input', () => {
                this.updateWordCount();
                this.callbacks.onContentChange(this.getContent());
            });
        }
        
        // Save button
        if (this.saveBtn) {
            this.saveBtn.addEventListener('click', () => {
                this.saveSection();
            });
        }
        
        // Regenerate button
        if (this.regenerateBtn) {
            this.regenerateBtn.addEventListener('click', () => {
                this.regenerateSection();
            });
        }
        
        // Preview button
        if (this.previewBtn) {
            this.previewBtn.addEventListener('click', () => {
                this.callbacks.onPreview(this.getContent());
            });
        }
    }

    // Public API methods
    loadSection(sectionId, sectionData) {
        this.currentSectionId = sectionId;
        
        if (this.currentSectionTitle && sectionData.title) {
            this.currentSectionTitle.textContent = sectionData.title;
        }
        
        if (this.contentEditor) {
            this.contentEditor.value = sectionData.content || '';
            this.contentEditor.disabled = false;
            this.updateWordCount();
        }
        
        this.enableButtons();
        this.callbacks.onSectionLoad(sectionId, sectionData);
        
        console.log(`[Output Panel] Loaded section ${sectionId}:`, sectionData.title);
    }

    clearContent() {
        if (this.contentEditor) {
            this.contentEditor.value = '';
            this.contentEditor.disabled = true;
        }
        
        if (this.currentSectionTitle) {
            this.currentSectionTitle.textContent = 'Select a section to begin editing';
        }
        
        if (this.wordCount) {
            this.wordCount.textContent = '0 words';
        }
        
        if (this.lastSaved) {
            this.lastSaved.textContent = 'Not saved';
        }
        
        this.disableButtons();
        this.currentSectionId = null;
    }

    setContent(content) {
        if (this.contentEditor) {
            this.contentEditor.value = content;
            this.updateWordCount();
        }
    }

    getContent() {
        return this.contentEditor ? this.contentEditor.value : '';
    }

    updateWordCount() {
        if (!this.contentEditor || !this.wordCount) return;
        
        const content = this.contentEditor.value;
        const wordCount = content.trim().split(/\s+/).filter(word => word.length > 0).length;
        this.wordCount.textContent = `${wordCount} words`;
    }

    async saveSection() {
        if (!this.currentSectionId) return;
        
        const content = this.getContent();
        
        try {
            const response = await fetch(`/authoring/api/posts/${this.postId}/sections/${this.currentSectionId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: content,
                    status: 'draft'
                })
            });
            
            if (response.ok) {
                if (this.lastSaved) {
                    this.lastSaved.textContent = 'Saved just now';
                }
                this.callbacks.onSave(this.currentSectionId, content);
                console.log(`[Output Panel] Section ${this.currentSectionId} saved successfully`);
            } else {
                throw new Error(`Failed to save section: ${response.statusText}`);
            }
        } catch (error) {
            console.error('[Output Panel] Error saving section:', error);
            if (this.lastSaved) {
                this.lastSaved.textContent = 'Save failed';
            }
        }
    }

    async regenerateSection() {
        if (!this.currentSectionId) return;
        
        this.callbacks.onRegenerate(this.currentSectionId);
        console.log(`[Output Panel] Regenerate requested for section ${this.currentSectionId}`);
    }

    enableButtons() {
        if (this.saveBtn) this.saveBtn.disabled = false;
        if (this.regenerateBtn) this.regenerateBtn.disabled = false;
        if (this.previewBtn) this.previewBtn.disabled = false;
    }

    disableButtons() {
        if (this.saveBtn) this.saveBtn.disabled = true;
        if (this.regenerateBtn) this.regenerateBtn.disabled = true;
        if (this.previewBtn) this.previewBtn.disabled = true;
    }

    setLoading(isLoading) {
        if (this.contentEditor) {
            this.contentEditor.disabled = isLoading;
        }
        
        if (this.regenerateBtn) {
            this.regenerateBtn.disabled = isLoading;
            this.regenerateBtn.textContent = isLoading ? 'Generating...' : 'Regenerate';
        }
    }

    restoreAccordionState() {
        const savedState = localStorage.getItem('output-accordion-state');
        if (savedState === 'closed') {
            const content = document.getElementById('output-accordion-content');
            const icon = document.getElementById('output-accordion-icon');
            if (content && icon) {
                content.style.display = 'none';
                icon.classList.remove('fa-chevron-down');
                icon.classList.add('fa-chevron-up');
            }
        }
    }

    // Public API for external access
    getCurrentSectionId() {
        return this.currentSectionId;
    }

    getWordCount() {
        if (!this.contentEditor) return 0;
        const content = this.contentEditor.value;
        return content.trim().split(/\s+/).filter(word => word.length > 0).length;
    }

    isContentModified() {
        // This could be enhanced to track if content has been modified since last save
        return this.getContent().length > 0;
    }
}

// Accordion function for output panel
function toggleOutputAccordion() {
    const content = document.getElementById('output-accordion-content');
    const icon = document.getElementById('output-accordion-icon');
    
    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
        localStorage.setItem('output-accordion-state', 'open');
    } else {
        content.style.display = 'none';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
        localStorage.setItem('output-accordion-state', 'closed');
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OutputPanel;
}