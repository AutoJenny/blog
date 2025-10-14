/**
 * Image Prompts Output Panel
 * Handles sophisticated DB-driven image prompt generation with character limits
 */

class ImagePromptsOutputPanel {
    constructor(options = {}) {
        this.postId = options.postId || window.postId;
        this.currentSection = null;
        this.selectedConcept = null;
        this.generatedPrompt = null;
        this.modelSettings = {
            model: 'sdxl-lora',
            limit: 400,
            style: 'inkwash and watercolour'
        };
        
        this.initializeElements();
        this.bindEvents();
        this.loadModelSettings();
    }
    
    initializeElements() {
        this.elements = {
            panel: document.getElementById('image-prompts-output-panel'),
            sectionTitle: document.getElementById('current-section-title'),
            conceptText: document.getElementById('concept-text'),
            generatedPromptText: document.getElementById('generated-prompt-text'),
            characterCount: document.getElementById('character-count'),
            modelLimit: document.getElementById('character-limit'),
            selectedModel: document.getElementById('selected-model'),
            styleGuidelines: document.getElementById('style-guidelines'),
            generateBtn: document.getElementById('generate-prompt-btn'),
            editBtn: document.getElementById('edit-prompt-btn'),
            regenerateBtn: document.getElementById('regenerate-prompt-btn'),
            saveBtn: document.getElementById('save-prompt-btn'),
            accordionContent: document.getElementById('image-prompts-accordion-content'),
            accordionIcon: document.getElementById('image-prompts-accordion-icon')
        };
    }
    
    bindEvents() {
        // Generate button
        this.elements.generateBtn.addEventListener('click', () => this.generatePrompt());
        
        // Edit button
        this.elements.editBtn.addEventListener('click', () => this.toggleEditMode());
        
        // Regenerate button
        this.elements.regenerateBtn.addEventListener('click', () => this.generatePrompt());
        
        // Save button
        this.elements.saveBtn.addEventListener('click', () => this.savePrompt());
        
        // Character count monitoring
        this.elements.generatedPromptText.addEventListener('input', () => this.updateCharacterCount());
        
        // Listen for section selection events
        window.addEventListener('sectionSelected', (event) => {
            this.onSectionSelected(event.detail.section);
        });
    }
    
    async loadModelSettings() {
        try {
            const response = await fetch(`/authoring/api/posts/${this.postId}/imaging-model-selection`);
            const data = await response.json();
            
            if (data.success && data.model_selection) {
                this.modelSettings.model = data.model_selection;
                this.updateModelSettings();
            }
        } catch (error) {
            console.error('Error loading model settings:', error);
        }
    }
    
    updateModelSettings() {
        const modelLimits = {
            'dall-e-3': 4000,
            'dall-e-2': 1000,
            'sdxl-lora': 400,
            'gpt-image-1': 2000,
        };
        
        this.modelSettings.limit = modelLimits[this.modelSettings.model] || 400;
        
        this.elements.selectedModel.textContent = this.modelSettings.model.toUpperCase();
        this.elements.modelLimit.textContent = `${this.modelSettings.limit} chars`;
    }
    
    onSectionSelected(section) {
        this.currentSection = section;
        this.elements.sectionTitle.textContent = section.title || section.section_heading || 'Unknown Section';
        
        // Load selected concept for this section
        this.loadSelectedConcept(section);
        
        // Load existing image prompt if available
        this.loadExistingPrompt(section);
    }
    
    async loadSelectedConcept(section) {
        try {
            // Get the selected concept from the section data
            const selectedConcept = section.selected_image_concept;
            
            if (selectedConcept) {
                this.selectedConcept = selectedConcept;
                this.elements.conceptText.textContent = selectedConcept;
                this.elements.generateBtn.disabled = false;
            } else {
                this.selectedConcept = null;
                this.elements.conceptText.textContent = 'No concept selected. Please select a concept on the Image Concepts page first.';
                this.elements.generateBtn.disabled = true;
            }
        } catch (error) {
            console.error('Error loading selected concept:', error);
            this.elements.conceptText.textContent = 'Error loading concept';
        }
    }
    
    async loadExistingPrompt(section) {
        try {
            const imagePrompts = section.image_prompts;
            
            if (imagePrompts) {
                let promptData;
                if (typeof imagePrompts === 'string') {
                    promptData = JSON.parse(imagePrompts);
                } else {
                    promptData = imagePrompts;
                }
                
                this.generatedPrompt = promptData.image_prompt || promptData;
                this.elements.generatedPromptText.value = this.generatedPrompt;
                this.updateCharacterCount();
                this.elements.editBtn.disabled = false;
                this.elements.regenerateBtn.disabled = false;
                this.elements.saveBtn.disabled = false;
            } else {
                this.generatedPrompt = null;
                this.elements.generatedPromptText.value = '';
                this.updateCharacterCount();
                this.elements.editBtn.disabled = true;
                this.elements.regenerateBtn.disabled = true;
                this.elements.saveBtn.disabled = true;
            }
        } catch (error) {
            console.error('Error loading existing prompt:', error);
        }
    }
    
    async generatePrompt() {
        if (!this.selectedConcept) {
            alert('Please select a concept on the Image Concepts page first.');
            return;
        }
        
        this.setLoading(true);
        
        try {
            // Get the current LLM settings
            const llmSettings = await this.getLLMSettings();
            
            // Prepare the compiled prompt using the sophisticated DB-driven protocol
            const compiledPrompt = this.buildCompiledPrompt();
            
            const response = await fetch('/api/generate-image-prompt-from-builder', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    compiled_prompt: compiledPrompt,
                    llm_provider: llmSettings.provider,
                    llm_model: llmSettings.model,
                    temperature: llmSettings.temperature,
                    max_tokens: llmSettings.max_tokens,
                    post_id: this.postId,
                    section_id: this.currentSection.id
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.generatedPrompt = data.image_prompt;
                this.elements.generatedPromptText.value = this.generatedPrompt;
                this.updateCharacterCount();
                this.elements.editBtn.disabled = false;
                this.elements.regenerateBtn.disabled = false;
                this.elements.saveBtn.disabled = false;
                
                console.log('Image prompt generated successfully:', this.generatedPrompt);
            } else {
                throw new Error(data.error || 'Failed to generate image prompt');
            }
        } catch (error) {
            console.error('Error generating image prompt:', error);
            alert(`Error generating image prompt: ${error.message}`);
        } finally {
            this.setLoading(false);
        }
    }
    
    buildCompiledPrompt() {
        // Build the sophisticated prompt using the DB-driven protocol
        return `Convert the Selected Concept into a single detailed image prompt.

REQUIREMENTS:
- Use only the elements provided in the Selected Concept
- Expand into visual composition, atmosphere, and lighting without adding new objects or ideas
- MAXIMUM ${this.modelSettings.limit} CHARACTERS TOTAL - COUNT YOUR CHARACTERS
- Output must be one coherent sentence, with no labels, commentary, or extra formatting

Selected Concept:
${this.selectedConcept}

Output exactly ${this.modelSettings.limit} characters or less:`;
    }
    
    async getLLMSettings() {
        try {
            const response = await fetch(`/authoring/api/posts/${this.postId}/llm-settings`);
            const data = await response.json();
            
            if (data.success) {
                return {
                    provider: data.settings.provider || 'Ollama',
                    model: data.settings.model || 'llama3.2:latest',
                    temperature: data.settings.temperature || 0.7,
                    max_tokens: data.settings.max_tokens || 2000
                };
            }
        } catch (error) {
            console.error('Error loading LLM settings:', error);
        }
        
        // Fallback settings
        return {
            provider: 'Ollama',
            model: 'llama3.2:latest',
            temperature: 0.7,
            max_tokens: 2000
        };
    }
    
    toggleEditMode() {
        const isReadonly = this.elements.generatedPromptText.readOnly;
        this.elements.generatedPromptText.readOnly = !isReadonly;
        this.elements.editBtn.textContent = isReadonly ? 'Done Editing' : 'Edit Prompt';
        
        if (!isReadonly) {
            this.elements.generatedPromptText.focus();
        }
    }
    
    async savePrompt() {
        if (!this.generatedPrompt) {
            alert('No prompt to save');
            return;
        }
        
        try {
            const response = await fetch(`/authoring/api/posts/${this.postId}/sections/${this.currentSection.id}/save-image-prompt`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image_prompt: this.elements.generatedPromptText.value
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.generatedPrompt = this.elements.generatedPromptText.value;
                console.log('Image prompt saved successfully');
            } else {
                throw new Error(data.error || 'Failed to save image prompt');
            }
        } catch (error) {
            console.error('Error saving image prompt:', error);
            alert(`Error saving image prompt: ${error.message}`);
        }
    }
    
    updateCharacterCount() {
        const text = this.elements.generatedPromptText.value;
        const count = text.length;
        const limit = this.modelSettings.limit;
        
        this.elements.characterCount.textContent = `${count} characters`;
        
        // Update styling based on character count
        this.elements.characterCount.className = '';
        if (count > limit) {
            this.elements.characterCount.classList.add('error');
        } else if (count > limit * 0.9) {
            this.elements.characterCount.classList.add('warning');
        } else if (count > limit * 0.7) {
            this.elements.characterCount.classList.add('success');
        }
    }
    
    setLoading(loading) {
        if (loading) {
            this.elements.panel.classList.add('loading');
            this.elements.generateBtn.disabled = true;
            this.elements.generateBtn.textContent = 'Generating...';
        } else {
            this.elements.panel.classList.remove('loading');
            this.elements.generateBtn.disabled = false;
            this.elements.generateBtn.textContent = 'Generate Prompt';
        }
    }
    
    show(section) {
        this.onSectionSelected(section);
    }
}

// Global functions for accordion control
function toggleImagePromptsOutputAccordion() {
    const content = document.getElementById('image-prompts-accordion-content');
    const icon = document.getElementById('image-prompts-accordion-icon');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.classList.remove('rotated');
    } else {
        content.style.display = 'none';
        icon.classList.add('rotated');
    }
}

// Initialize the panel when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (window.postId) {
        window.imagePromptsOutputPanel = new ImagePromptsOutputPanel({
            postId: window.postId
        });
    }
});
