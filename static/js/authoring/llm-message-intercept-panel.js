/**
 * LLM Message Intercept Panel
 * Single source of truth for LLM messages - assembles and stores actual messages
 */
class LLMMessageInterceptPanel {
    constructor() {
        this.messageDisplay = null;
        this.statusIndicator = null;
        this.characterCount = null;
        this.currentMessage = null;
        this.isReady = false;
        
        this.init();
    }
    
    init() {
        this.bindElements();
        this.setupEventListeners();
        this.updateStatus('No message ready', false);
    }
    
    bindElements() {
        this.messageDisplay = document.getElementById('llm-message-display');
        this.statusIndicator = document.getElementById('message-status-indicator');
        this.characterCount = document.getElementById('message-character-count');
    }
    
    setupEventListeners() {
        // Listen for section selection to assemble message
        window.addEventListener('sectionSelected', (event) => {
            if (event.detail && event.detail.section) {
                this.assembleMessageForSection(event.detail.section);
            }
        });
        
        // Listen for concept selection changes
        window.addEventListener('conceptSelected', (event) => {
            this.assembleMessageForCurrentSection();
        });
        
        // Listen for model changes that affect message assembly
        window.addEventListener('modelChanged', (event) => {
            this.assembleMessageForCurrentSection();
        });
        
        // Listen for generation completion to refresh intercepted message
        window.addEventListener('promptGenerated', (event) => {
            this.refreshInterceptedMessage();
        });
        
        // Listen for any LLM generation completion
        window.addEventListener('llmGenerationComplete', (event) => {
            this.refreshInterceptedMessage();
        });
    }
    
    async assembleMessageForSection(section) {
        console.log('[LLMMessageIntercept] Loading intercepted message for section:', section.id);
        
        try {
            // Load the actual intercepted message from the database
            const response = await fetch(`/authoring/api/posts/${window.postId}/sections/${section.id}/intercepted-message`);
            
            if (!response.ok) {
                throw new Error(`Failed to load intercepted message: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.message) {
                // Display the actual intercepted message
                this.currentMessage = data.message;
                this.isReady = true;
                this.updateMessage(data.message, `Actual LLM message (${data.created_at ? new Date(data.created_at).toLocaleString() : 'unknown time'})`, true);
                
                console.log('[LLMMessageIntercept] Loaded actual intercepted message');
            } else {
                // No intercepted message yet - show placeholder
                this.updateMessage('', 'No LLM call made yet - message will appear here after generation', false);
                console.log('[LLMMessageIntercept] No intercepted message found yet');
            }
            
        } catch (error) {
            console.error('[LLMMessageIntercept] Error loading intercepted message:', error);
            this.updateMessage('', 'Error loading intercepted message', false);
        }
    }
    
    assembleMessageForCurrentSection() {
        // Re-assemble message when concept or model changes
        const currentSection = this.getCurrentSection();
        if (currentSection) {
            this.assembleMessageForSection(currentSection);
        }
    }
    
    async refreshInterceptedMessage() {
        // Refresh the intercepted message after an LLM call
        const currentSection = this.getCurrentSection();
        if (currentSection) {
            await this.assembleMessageForSection(currentSection);
        }
    }
    
    getSelectedConceptContent(section) {
        // Get concept content from the prompt builder panel or section data
        if (window.promptBuilderPanel && window.promptBuilderPanel.selectedConceptContent) {
            return window.promptBuilderPanel.selectedConceptContent;
        }
        
        // Fallback: get from section data
        if (section.selected_image_concept && section.image_concepts) {
            try {
                const conceptsData = JSON.parse(section.image_concepts);
                const selectedConcept = conceptsData.concepts.find(
                    c => c.concept_id === section.selected_image_concept
                );
                if (selectedConcept) {
                    return {
                        description: selectedConcept.concept_description,
                        mood: selectedConcept.concept_mood,
                        elements: selectedConcept.key_visual_elements
                    };
                }
            } catch (e) {
                console.error('Error parsing concepts data:', e);
            }
        }
        
        return null;
    }
    
    buildCompiledPrompt(conceptContent) {
        // Use the same logic as prompt builder panel
        if (window.promptBuilderPanel && window.promptBuilderPanel.buildCompiledPrompt) {
            const config = window.promptBuilderPanel.modelConfig?.[window.promptBuilderPanel.modelSelection] || 
                          { limit: 400, style: 'inkwash and watercolour' };
            return window.promptBuilderPanel.buildCompiledPrompt(conceptContent, config);
        }
        
        // Fallback compilation
        return `Create an image showing: ${conceptContent.description}`;
    }
    
    getCurrentSection() {
        // Get current section from sections panel
        if (window.sectionsPanel && window.sectionsPanel.currentSectionId) {
            return window.sectionsPanel.sections.find(
                s => s.id === window.sectionsPanel.currentSectionId
            );
        }
        return null;
    }
    
    updateMessage(message, status, isReady) {
        if (this.messageDisplay) {
            this.messageDisplay.value = message;
        }
        
        this.updateStatus(status, isReady);
        this.updateCharacterCount(message.length);
        
        this.currentMessage = message;
        this.isReady = isReady;
    }
    
    updateStatus(status, isReady) {
        if (this.statusIndicator) {
            this.statusIndicator.textContent = status;
            this.statusIndicator.className = `status-indicator ${isReady ? 'ready' : 'not-ready'}`;
        }
    }
    
    updateCharacterCount(count) {
        if (this.characterCount) {
            this.characterCount.textContent = `${count} characters`;
        }
    }
    
    // Public method to get the stored message for LLM calls
    getStoredMessage() {
        if (!this.isReady || !this.currentMessage) {
            throw new Error('No message ready for LLM call');
        }
        return this.currentMessage;
    }
    
    // Public method to check if message is ready
    isMessageReady() {
        return this.isReady && this.currentMessage;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.llmMessageInterceptPanel = new LLMMessageInterceptPanel();
});
