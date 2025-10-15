/**
 * Image Captions Output Panel
 * Handles display and editing of image captions and alt text
 */
class ImageCaptionsOutputPanel {
    constructor(postId) {
        this.postId = postId;
        this.currentSection = null;
        this.currentCaptions = null;
        this.init();
    }

    init() {
        this.bindElements();
        this.setupEventListeners();
        this.setupAccordion();
        console.log('[ImageCaptionsOutputPanel] Initialized for post:', this.postId);
    }

    bindElements() {
        this.generateBtn = document.getElementById('generate-captions-btn');
        this.saveBtn = document.getElementById('save-captions-btn');
        this.regenerateBtn = document.getElementById('regenerate-captions-btn');
        this.captionTextarea = document.getElementById('caption-text');
        this.altTextarea = document.getElementById('alt-text');
        this.wordCountSpan = document.getElementById('caption-word-count');
        this.lastSavedSpan = document.getElementById('last-saved-captions');
        this.accordionIcon = document.getElementById('image-captions-accordion-icon');
        this.content = document.getElementById('image-captions-content');
        
        console.log('[DEBUG] ImageCaptionsOutputPanel bindElements - generateBtn:', this.generateBtn);
    }

    setupEventListeners() {
        console.log('[DEBUG] ImageCaptionsOutputPanel setupEventListeners - generateBtn:', this.generateBtn);
        if (this.generateBtn) {
            console.log('[DEBUG] Adding click listener to generate button');
            this.generateBtn.addEventListener('click', () => this.generateCaptions());
        } else {
            console.warn('[DEBUG] Generate button not found!');
        }
        
        if (this.saveBtn) {
            this.saveBtn.addEventListener('click', () => this.saveCaptions());
        }
        
        if (this.regenerateBtn) {
            this.regenerateBtn.addEventListener('click', () => this.generateCaptions());
        }

        // Word count monitoring
        if (this.captionTextarea) {
            this.captionTextarea.addEventListener('input', () => this.updateWordCount());
        }
    }

    setupAccordion() {
        // Accordion state persistence
        this.restoreAccordionState();
    }

    restoreAccordionState() {
        const savedState = localStorage.getItem('image-captions-output-accordion-state');
        if (savedState === 'open') {
            this.content.classList.add('open');
            this.accordionIcon.classList.add('open');
        }
    }

    toggleAccordion() {
        const isOpen = this.content.classList.contains('open');
        
        if (isOpen) {
            this.content.classList.remove('open');
            this.accordionIcon.classList.remove('open');
            localStorage.setItem('image-captions-output-accordion-state', 'closed');
        } else {
            this.content.classList.add('open');
            this.accordionIcon.classList.add('open');
            localStorage.setItem('image-captions-output-accordion-state', 'open');
        }
    }

    onSectionSelected(event) {
        console.log('[DEBUG] ImageCaptionsOutputPanel received sectionSelected event:', event);
        const section = event.detail.section;
        this.currentSection = section;
        this.updateSectionTitle(section.title || section.section_heading || 'Unknown Section');
        this.loadExistingCaptions(section);
        this.updateButtonStates();
        console.log('[ImageCaptionsOutputPanel] Section selected:', section.id);
    }

    updateSectionTitle(title) {
        const titleElement = document.getElementById('current-section-title');
        if (titleElement) {
            titleElement.textContent = title;
        }
    }

    loadExistingCaptions(section) {
        if (section.image_captions || section.image_alt_text) {
            this.displayCaptions({
                caption: section.image_captions || '',
                alt_text: section.image_alt_text || ''
            });
        } else {
            this.clearCaptions();
        }
    }

    displayCaptions(captions) {
        if (this.captionTextarea) {
            this.captionTextarea.value = captions.caption || '';
        }
        if (this.altTextarea) {
            this.altTextarea.value = captions.alt_text || '';
        }
        
        this.currentCaptions = captions;
        this.updateWordCount();
        this.updateButtonStates();
    }

    clearCaptions() {
        if (this.captionTextarea) {
            this.captionTextarea.value = '';
        }
        if (this.altTextarea) {
            this.altTextarea.value = '';
        }
        
        this.currentCaptions = null;
        this.updateWordCount();
        this.updateButtonStates();
    }

    updateWordCount() {
        if (this.wordCountSpan && this.captionTextarea) {
            const text = this.captionTextarea.value;
            const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
            this.wordCountSpan.textContent = `${wordCount} words`;
        }
    }

    updateButtonStates() {
        const hasSection = this.currentSection !== null;
        const hasCaptions = this.captionTextarea?.value.trim() || this.altTextarea?.value.trim();
        
        if (this.generateBtn) this.generateBtn.disabled = !hasSection;
        if (this.saveBtn) this.saveBtn.disabled = !hasCaptions;
        if (this.regenerateBtn) this.regenerateBtn.disabled = !hasSection;
    }

    async generateCaptions() {
        console.log('[DEBUG] generateCaptions called, currentSection:', this.currentSection);
        if (!this.currentSection) {
            console.warn('[ImageCaptionsOutputPanel] No section selected');
            return;
        }

        const generateBtn = document.getElementById('generate-captions-btn');
        const regenerateBtn = document.getElementById('regenerate-captions-btn');
        
        // Set loading state
        if (generateBtn) {
            generateBtn.disabled = true;
            generateBtn.textContent = 'Generating...';
        }
        if (regenerateBtn) {
            regenerateBtn.disabled = true;
            regenerateBtn.textContent = 'Generating...';
        }

        try {
            const response = await fetch(`/authoring/api/posts/${this.postId}/sections/${this.currentSection.id}/generate-image-captions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            });

            if (!response.ok) {
                throw new Error(`Generation failed: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('[ImageCaptionsOutputPanel] Generation response:', data);
            
            if (data.success && data.image_captions && data.image_alt_text) {
                this.displayCaptions({
                    caption: data.image_captions,
                    alt_text: data.image_alt_text
                });
                
                if (this.lastSavedSpan) {
                    this.lastSavedSpan.textContent = 'Generated just now';
                }
            } else {
                throw new Error(data.error || 'No captions generated');
            }

        } catch (error) {
            console.error('[ImageCaptionsOutputPanel] Error generating captions:', error);
            if (this.captionTextarea) {
                this.captionTextarea.value = `Error generating captions: ${error.message}`;
            }
        } finally {
            if (generateBtn) {
                generateBtn.disabled = false;
                generateBtn.textContent = 'Generate';
            }
            if (regenerateBtn) {
                regenerateBtn.disabled = false;
                regenerateBtn.textContent = 'Regenerate';
            }
        }
    }

    async saveCaptions() {
        if (!this.currentSection) {
            console.warn('[ImageCaptionsOutputPanel] No section selected');
            return;
        }

        const caption = this.captionTextarea?.value.trim();
        const altText = this.altTextarea?.value.trim();

        if (!caption || !altText) {
            console.warn('[ImageCaptionsOutputPanel] Missing caption or alt text');
            return;
        }

        const saveBtn = document.getElementById('save-captions-btn');
        
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.textContent = 'Saving...';
        }

        try {
            const response = await fetch(`/authoring/api/posts/${this.postId}/sections/${this.currentSection.id}/save-image-captions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    caption: caption,
                    alt_text: altText
                })
            });

            if (!response.ok) {
                throw new Error(`Save failed: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('[ImageCaptionsOutputPanel] Save response:', data);
            
            if (data.success) {
                if (this.lastSavedSpan) {
                    this.lastSavedSpan.textContent = 'Saved just now';
                }
                
                // Update current section data
                if (this.currentSection) {
                    this.currentSection.image_captions = caption;
                    this.currentSection.image_alt_text = altText;
                }
            } else {
                throw new Error(data.error || 'Save failed');
            }

        } catch (error) {
            console.error('[ImageCaptionsOutputPanel] Error saving captions:', error);
            alert(`Error saving captions: ${error.message}`);
        } finally {
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save';
            }
        }
    }

    onBatchGenerate(sectionIds) {
        console.log('[ImageCaptionsOutputPanel] Batch generation started for sections:', sectionIds);
        // Batch generation is handled by the sections panel
        // This panel just needs to be ready to display results
    }
}

// Global accordion function
function toggleImageCaptionsOutputAccordion() {
    if (window.imageCaptionsOutputPanel) {
        window.imageCaptionsOutputPanel.toggleAccordion();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.postId) {
        window.imageCaptionsOutputPanel = new ImageCaptionsOutputPanel(window.postId);
        
        // Listen for section selection events
        window.addEventListener('sectionSelected', (event) => {
            window.imageCaptionsOutputPanel.onSectionSelected(event);
        });
        
        // Listen for batch generation events
        window.addEventListener('sections:batch-generate', (event) => {
            window.imageCaptionsOutputPanel.onBatchGenerate(event.detail.ids);
        });
    }
});
