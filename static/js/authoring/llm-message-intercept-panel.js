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
        this.setupAccordion();
        this.updateStatus('No message ready', false);
        this.loadAllSectionsLLMData(); // Load LLM data for all sections on init
        
        // Auto-load data for current section on page load
        setTimeout(() => {
            this.autoLoadCurrentSectionData();
        }, 1000);
    }

    setupAccordion() {
        this.restoreAccordionState();
    }

    restoreAccordionState() {
        const savedState = sessionStorage.getItem('llm-message-accordion-state');
        const content = document.getElementById('llm-message-accordion-content');
        const icon = document.getElementById('llm-message-accordion-icon');
        
        if (content && icon) {
            if (savedState === 'open') {
                content.style.display = 'block';
                icon.classList.remove('fa-chevron-up');
                icon.classList.add('fa-chevron-down');
            } else {
                content.style.display = 'none';
                icon.classList.remove('fa-chevron-down');
                icon.classList.add('fa-chevron-up');
            }
        }
    }

    toggleAccordion() {
        const content = document.getElementById('llm-message-accordion-content');
        const icon = document.getElementById('llm-message-accordion-icon');
        
        if (!content || !icon) return;
        
        const isCollapsed = content.style.display === 'none' || content.style.display === '';
        
        if (isCollapsed) {
            content.style.display = 'block';
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
            sessionStorage.setItem('llm-message-accordion-state', 'open');
        } else {
            content.style.display = 'none';
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-up');
            sessionStorage.setItem('llm-message-accordion-state', 'closed');
        }
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
    
    async loadAllSectionsLLMData() {
        console.log('[LLMMessageIntercept] Loading LLM data for all sections');
        
        try {
            // Get all sections from the sections panel
            if (window.sectionsPanel && window.sectionsPanel.sections) {
                const sections = window.sectionsPanel.sections;
                console.log(`[LLMMessageIntercept] Found ${sections.length} sections to load LLM data for`);
                
                // Load LLM data for each section
                for (const section of sections) {
                    await this.loadSectionLLMData(section.id);
                }
            } else {
                console.log('[LLMMessageIntercept] Sections panel not available yet, will retry');
                // Retry after a short delay
                setTimeout(() => this.loadAllSectionsLLMData(), 1000);
            }
        } catch (error) {
            console.error('[LLMMessageIntercept] Error loading all sections LLM data:', error);
        }
    }
    
    async loadSectionLLMData(sectionId) {
        try {
            const response = await fetch(`/authoring/api/posts/${window.postId}/sections/${sectionId}/intercepted-message`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.raw_http_request) {
                    // Store the LLM data for this section
                    if (!this.sectionsLLMData) {
                        this.sectionsLLMData = {};
                    }
                    this.sectionsLLMData[sectionId] = data.raw_http_request;
                    console.log(`[LLMMessageIntercept] Loaded LLM data for section ${sectionId}`);
                }
            }
        } catch (error) {
            console.error(`[LLMMessageIntercept] Error loading LLM data for section ${sectionId}:`, error);
        }
    }
    
    async autoLoadCurrentSectionData() {
        console.log('[LLMMessageIntercept] Auto-loading current section data');
        
        try {
            // Get the currently selected section dynamically
            let currentSectionId = null;
            
            // Try to get from sections panel first
            if (window.sectionsPanel && window.sectionsPanel.sections && window.sectionsPanel.sections.length > 0) {
                // Find the currently selected section from JavaScript objects
                const selectedSection = window.sectionsPanel.sections.find(section => 
                    section.selected === true
                );
                if (selectedSection) {
                    currentSectionId = selectedSection.id;
                } else {
                    // If no section is explicitly selected, use the first one
                    currentSectionId = window.sectionsPanel.sections[0].id;
                }
            }
            
            // Fallback: try to get from URL or other sources
            if (!currentSectionId) {
                const urlMatch = window.location.pathname.match(/\/sections\/(\d+)/);
                if (urlMatch) {
                    currentSectionId = parseInt(urlMatch[1]);
                }
            }
            
            if (currentSectionId) {
                console.log('[LLMMessageIntercept] Auto-loading data for section:', currentSectionId);
                await this.loadAndDisplaySectionData(currentSectionId);
            } else {
                console.log('[LLMMessageIntercept] No current section identified');
            }
        } catch (error) {
            console.error('[LLMMessageIntercept] Error auto-loading current section data:', error);
        }
    }
    
    async loadAndDisplaySectionData(sectionId) {
        try {
            const response = await fetch(`/authoring/api/posts/${window.postId}/sections/${sectionId}/intercepted-message`);
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success && data.raw_http_request) {
                    // Display the exact raw HTTP request that goes to the LLM
                    const exactLLMInput = data.raw_http_request;
                    this.currentMessage = exactLLMInput;
                    this.isReady = true;
                    this.updateMessage(exactLLMInput, `Raw HTTP Request (${data.created_at ? new Date(data.created_at).toLocaleString() : 'unknown time'})`, true);
                    
                    console.log(`[LLMMessageIntercept] Successfully loaded stored data for section ${sectionId}`);
                } else {
                    console.log(`[LLMMessageIntercept] No stored data found for section ${sectionId}`);
                    this.updateMessage('No LLM messages stored yet. Generate a prompt to see the exact input sent to the LLM.', 'No data available', false);
                }
            } else {
                console.error(`[LLMMessageIntercept] Failed to load data for section ${sectionId}:`, response.statusText);
                this.updateMessage('Error loading stored data. Please try again.', 'Error', false);
            }
        } catch (error) {
            console.error(`[LLMMessageIntercept] Error loading section ${sectionId} data:`, error);
            this.updateMessage('Error loading stored data. Please try again.', 'Error', false);
        }
    }
    
    async assembleMessageForSection(section) {
        console.log('[LLMMessageIntercept] Loading intercepted message for section:', section.id);
        
        // Use the centralized method to load and display section data
        await this.loadAndDisplaySectionData(section.id);
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
