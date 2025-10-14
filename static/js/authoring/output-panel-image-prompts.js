/**
 * Image Prompts Output Panel - Simplified Results Display
 * Handles display and saving of generated image prompts
 */

class ImagePromptsOutputPanel {
    constructor(postId) {
        this.postId = postId;
        this.currentSection = null;
        this.currentPrompt = null;
        this.currentMetadata = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupAccordion();
        console.log('[ImagePromptsOutputPanel] Initialized for post:', this.postId);
    }

    setupEventListeners() {
        // Save prompt button
        const saveBtn = document.getElementById('save-prompt-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.savePrompt());
        }

        // Regenerate prompt button
        const regenerateBtn = document.getElementById('regenerate-prompt-btn');
        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', () => this.regeneratePrompt());
        }

        // Listen for prompt generation events from prompt builder
        window.addEventListener('promptGenerated', (event) => {
            this.onPromptGenerated(event.detail);
        });

        // Listen for section selection events
        window.addEventListener('sectionSelected', (event) => {
            this.onSectionSelected(event.detail.section);
        });

        // Listen for batch generation events
        window.addEventListener('sections:batch-generate', (event) => {
            this.onBatchGenerate(event.detail.ids);
        });
    }

    setupAccordion() {
        const header = document.querySelector('#image-prompts-output-panel .panel-header');
        const content = document.getElementById('image-prompts-accordion-content');
        const icon = document.getElementById('image-prompts-accordion-icon');

        if (header && content && icon) {
            header.addEventListener('click', () => {
                const isCollapsed = content.style.display === 'none';
                content.style.display = isCollapsed ? 'block' : 'none';
                icon.classList.toggle('rotated', !isCollapsed);
            });
        }
    }

    onSectionSelected(section) {
        this.currentSection = section;
        this.updateSectionTitle(section.title || section.section_heading || 'Unknown Section');
        this.loadExistingPrompt(section);
        this.updateButtonStates();
        console.log('[ImagePromptsOutputPanel] Section selected:', section.id);
    }

    updateSectionTitle(title) {
        const titleElement = document.getElementById('current-section-title');
        if (titleElement) {
            titleElement.textContent = title;
        }
    }

    loadExistingPrompt(section) {
        const textarea = document.getElementById('generated-prompt-textarea');
        const charCount = document.getElementById('char-count');
        
        if (!textarea || !charCount) return;

        // Check if section has existing image prompts
        if (section.image_prompts) {
            let promptText = '';
            
            if (typeof section.image_prompts === 'string') {
                try {
                    const parsed = JSON.parse(section.image_prompts);
                    promptText = parsed.image_prompt || parsed.prompt || section.image_prompts;
                } catch (e) {
                    promptText = section.image_prompts;
                }
            } else if (typeof section.image_prompts === 'object') {
                promptText = section.image_prompts.image_prompt || section.image_prompts.prompt || '';
            }
            
            textarea.value = promptText;
            charCount.textContent = `${promptText.length} chars`;
            
            // Update metadata if available
            this.updateMetadata(section.image_prompts);
            
        } else {
            textarea.value = '';
            charCount.textContent = '0 chars';
            this.clearMetadata();
        }
        
        this.updateButtonStates();
    }

    updateMetadata(promptData) {
        const modelElement = document.getElementById('prompt-model');
        const charCountElement = document.getElementById('prompt-character-count');
        const styleElement = document.getElementById('prompt-style');
        const timeElement = document.getElementById('prompt-generated-time');
        
        if (typeof promptData === 'object' && promptData) {
            if (modelElement) modelElement.textContent = promptData.model || '-';
            if (charCountElement) charCountElement.textContent = promptData.character_count || '-';
            if (styleElement) styleElement.textContent = promptData.style || '-';
            if (timeElement) timeElement.textContent = promptData.generated_at || '-';
        } else {
            this.clearMetadata();
        }
    }

    clearMetadata() {
        const elements = ['prompt-model', 'prompt-character-count', 'prompt-style', 'prompt-generated-time'];
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.textContent = '-';
        });
    }

    onPromptGenerated(detail) {
        console.log('[ImagePromptsOutputPanel] Prompt generated:', detail);
        
        this.currentPrompt = detail.prompt;
        this.currentMetadata = detail.metadata;
        
        // Update display
        const textarea = document.getElementById('generated-prompt-textarea');
        const charCount = document.getElementById('char-count');
        
        if (textarea) {
            textarea.value = detail.prompt;
        }
        
        if (charCount) {
            charCount.textContent = `${detail.prompt.length} chars`;
        }
        
        // Update metadata
        if (detail.metadata) {
            this.updateMetadata(detail.metadata);
        }
        
        // Update last saved status
        const lastSaved = document.getElementById('last-saved');
        if (lastSaved) {
            lastSaved.textContent = 'Generated';
        }
        
        this.updateButtonStates();
    }

    updateButtonStates() {
        const saveBtn = document.getElementById('save-prompt-btn');
        const regenerateBtn = document.getElementById('regenerate-prompt-btn');
        
        const hasPrompt = this.currentPrompt || (this.currentSection && this.currentSection.image_prompts);
        
        if (saveBtn) saveBtn.disabled = !hasPrompt;
        if (regenerateBtn) regenerateBtn.disabled = !this.currentSection;
    }

    async savePrompt() {
        if (!this.currentSection || !this.currentPrompt) {
            console.warn('[ImagePromptsOutputPanel] No section or prompt to save');
            return;
        }

        const saveBtn = document.getElementById('save-prompt-btn');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.textContent = 'Saving...';
        }

        try {
            const response = await fetch(`/authoring/api/posts/${this.postId}/sections/${this.currentSection.id}/save-image-prompt`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image_prompt: this.currentPrompt,
                    metadata: this.currentMetadata
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('[ImagePromptsOutputPanel] Prompt saved successfully:', data);
                
                // Update last saved status
                const lastSaved = document.getElementById('last-saved');
                if (lastSaved) {
                    lastSaved.textContent = 'Saved';
                }
                
                // Update section data
                if (this.currentSection) {
                    this.currentSection.image_prompts = this.currentPrompt;
                }
                
            } else {
                const error = await response.json();
                console.error('[ImagePromptsOutputPanel] Error saving prompt:', error);
                alert('Error saving prompt: ' + (error.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('[ImagePromptsOutputPanel] Error saving prompt:', error);
            alert('Error saving prompt: ' + error.message);
        } finally {
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save';
            }
        }
    }

    regeneratePrompt() {
        // Trigger prompt builder to regenerate
        if (window.promptBuilderPanel && this.currentSection) {
            window.promptBuilderPanel.generatePrompt();
        }
    }

    async onBatchGenerate(sectionIds) {
        console.log('[ImagePromptsOutputPanel] Batch generation started for sections:', sectionIds);
        
        // The actual generation is handled by the prompt builder panel
        // This panel just needs to be ready to receive the results
        
        // Update last saved status to show batch processing
        const lastSaved = document.getElementById('last-saved');
        if (lastSaved) {
            lastSaved.textContent = 'Batch processing...';
        }
    }
}

// Global accordion function
function toggleImagePromptsOutputAccordion() {
    const content = document.getElementById('image-prompts-accordion-content');
    const icon = document.getElementById('image-prompts-accordion-icon');
    
    if (content && icon) {
        const isCollapsed = content.style.display === 'none';
        content.style.display = isCollapsed ? 'block' : 'none';
        icon.classList.toggle('rotated', !isCollapsed);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.postId && window.currentSubstage === 'image-prompts') {
        window.imagePromptsOutputPanel = new ImagePromptsOutputPanel(window.postId);
    }
});
