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
        // Generate prompt button
        const generateBtn = document.getElementById('generate-image-prompt-btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.generateImagePrompt());
        }

        // Save prompt button
        const saveBtn = document.getElementById('save-prompt-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.savePrompt());
        }

        // Regenerate prompt button
        const regenerateBtn = document.getElementById('regenerate-prompt-btn');
        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', () => this.generateImagePrompt());
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
            // Keep output panel permanently open (no accordion functionality)
            content.style.display = 'block';
            icon.style.display = 'none'; // Hide the chevron icon since it's not functional
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

    displayPrompt(prompt, metadata) {
        console.log('[ImagePromptsOutputPanel] Displaying prompt:', prompt?.substring(0, 50) + '...');
        
        this.currentPrompt = prompt;
        this.currentMetadata = metadata;
        
        // Update display
        const textarea = document.getElementById('generated-prompt-textarea');
        const charCount = document.getElementById('char-count');
        
        if (textarea) {
            textarea.value = prompt;
        }
        
        if (charCount) {
            charCount.textContent = `${prompt.length} chars`;
        }
        
        // Update metadata
        if (metadata) {
            this.updateMetadata(metadata);
        }
        
        // Update last saved status
        const lastSaved = document.getElementById('last-saved');
        if (lastSaved) {
            lastSaved.textContent = 'Generated just now';
        }
        
        this.updateButtonStates();
    }

    onPromptGenerated(detail) {
        console.log('[ImagePromptsOutputPanel] Prompt generated:', detail);
        
        this.displayPrompt(detail.prompt, detail.metadata);
    }

    updateButtonStates() {
        const generateBtn = document.getElementById('generate-image-prompt-btn');
        const saveBtn = document.getElementById('save-prompt-btn');
        const regenerateBtn = document.getElementById('regenerate-prompt-btn');
        
        const hasSection = this.currentSection !== null;
        const hasPrompt = this.currentPrompt || (this.currentSection && this.currentSection.image_prompts);
        
        if (generateBtn) generateBtn.disabled = !hasSection;
        if (saveBtn) saveBtn.disabled = !hasPrompt;
        if (regenerateBtn) regenerateBtn.disabled = !hasSection;
    }

    async generateImagePrompt() {
        console.log('[DEBUG] generateImagePrompt called');
        console.log('[DEBUG] this.currentSection:', this.currentSection);
        
        if (!this.currentSection) {
            console.warn('[ImagePromptsOutputPanel] No section selected');
            return;
        }

        const generateBtn = document.getElementById('generate-image-prompt-btn');
        const regenerateBtn = document.getElementById('regenerate-prompt-btn');
        
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
            // Get the exact raw HTTP request from the Complete LLM Input field
            const llmMessageDisplay = document.getElementById('llm-message-display');
            if (!llmMessageDisplay || !llmMessageDisplay.value.trim()) {
                throw new Error('No LLM message available. Please ensure a concept is selected and the Complete LLM Input field is populated.');
            }
            
            const rawHttpRequest = llmMessageDisplay.value.trim();
            console.log('[ImagePromptsOutputPanel] Using raw HTTP request from Complete LLM Input field');
            
            // Parse the raw HTTP request to extract the JSON payload
            const jsonMatch = rawHttpRequest.match(/\{[\s\S]*\}/);
            if (!jsonMatch) {
                throw new Error('Could not parse JSON from raw HTTP request');
            }
            
            const requestPayload = JSON.parse(jsonMatch[0]);
            console.log('[ImagePromptsOutputPanel] Parsed request payload:', requestPayload);
            
            // Send the exact stored messages to the LLM
            const response = await fetch('/authoring/api/generate-image-prompt-from-builder-v2', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    post_id: window.postId,
                    section_id: this.currentSection.id,
                    exact_messages: requestPayload.messages,
                    exact_model: requestPayload.model,
                    exact_options: requestPayload.options,
                    use_exact_request: true
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success && result.image_prompt) {
                // Display the generated prompt
                const textarea = document.getElementById('generated-prompt-textarea');
                if (textarea) {
                    textarea.value = result.image_prompt;
                }
                
                console.log('[ImagePromptsOutputPanel] Generation completed using exact stored messages');
            } else {
                throw new Error(result.error || 'Unknown error occurred');
            }
            
        } catch (error) {
            console.error('[ImagePromptsOutputPanel] Error generating prompt:', error);
            const textarea = document.getElementById('generated-prompt-textarea');
            if (textarea) {
                textarea.value = `Error generating prompt: ${error.message}`;
            }
        } finally {
            // Reset loading state
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

// Global accordion function (disabled for output panel)
function toggleImagePromptsOutputAccordion() {
    // Output panel is permanently open - no accordion functionality
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.postId && window.currentSubstage === 'image-prompts') {
        window.imagePromptsOutputPanel = new ImagePromptsOutputPanel(window.postId);
    }
});
