/**
 * LLM Actions Orchestration Module
 *
 * Responsibilities:
 * - Coordinates satellite modules that are loaded via script tags
 * - Manages global state
 * - Provides single source of truth for step ID resolution
 *
 * @version 1.0
 */

console.log('[LLM-ACTIONS] Script loading...');

// Global state
const LLM_STATE = {
    context: null,
    modules: {},
    processing: false
};

/**
 * Main orchestrator class
 */
class LLMOrchestrator {
    constructor() {
        this.logger = window.logger || console;
        this.initialized = false;
    }

    /**
     * Initialize orchestrator
     */
    async initialize() {
        this.logger.info('orchestrator', 'Initializing LLM Actions...');
        
        try {
            // Extract context from URL parameters
            this.extractContext();
            
            // Initialize processing mode display with a delay to ensure sections iframe is loaded
            setTimeout(() => {
                this.initializeProcessingModeDisplay();
            }, 2000);
            
            // Resolve step_id from database - this is the single source of truth
            const stepId = await this.resolveStepId();
            if (!stepId) {
                throw new Error('Unable to resolve step ID from database');
            }
            
            // Update context with resolved step_id
            LLM_STATE.context.step_id = stepId;
            this.logger.info('orchestrator', `Resolved step_id: ${stepId} for step: ${LLM_STATE.context.step}`);
            
            // Initialize modules in the correct order
            await this.initModules();
            
            this.initialized = true;
            this.logger.info('orchestrator', 'LLM Actions initialized successfully');
            
        } catch (error) {
            this.logger.error('orchestrator', 'Failed to initialize LLM Actions:', error);
            this.showError(`Failed to initialize: ${error.message}`);
            throw error;
        }
    }

    /**
     * Extract workflow context from URL parameters or data attributes
     */
    extractContext() {
        // First try URL parameters (legacy support)
        const urlParams = new URLSearchParams(window.location.search);
        let stage = urlParams.get('stage');
        let substage = urlParams.get('substage');
        let step = urlParams.get('step');
        let post_id = urlParams.get('post_id');
        
        // If URL parameters are missing, try data attributes from container
        if (!stage || !substage || !step || !post_id) {
            const container = document.querySelector('.llm-container');
            if (container) {
                stage = stage || container.dataset.stage;
                substage = substage || container.dataset.substage;
                step = step || container.dataset.step;
                post_id = post_id || container.dataset.postId;
            }
        }
        
        this.logger.debug('orchestrator', 'Raw URL parameters:', { stage, substage, step, post_id });
        
        // Validate required parameters
        if (!stage || !substage || !step || !post_id) {
            const missing = [];
            if (!stage) missing.push('stage');
            if (!substage) missing.push('substage');
            if (!step) missing.push('step');
            if (!post_id) missing.push('post_id');
            
            throw new Error(`Missing required URL parameters: ${missing.join(', ')}`);
        }
        
        LLM_STATE.context = {
            stage,
            substage,
            step,
            post_id
        };
        
        this.logger.debug('orchestrator', 'Extracted context:', LLM_STATE.context);
    }



    /**
     * Determine processing mode based on stage and substage
     */
    determineProcessingMode() {
        const { stage, substage } = LLM_STATE.context;
        
        // Define which stages/substages use section iteration
        const sectionBasedStages = {
            'writing': ['sections', 'post_info', 'content'], // All writing substages
            'editing': ['sections'], // If editing has sections
            // Add other stages as needed
        };
        
        const mode = sectionBasedStages[stage]?.includes(substage) ? 'sections' : 'single';
        
        return {
            mode,
            stage,
            substage,
            postId: LLM_STATE.context.post_id
        };
    }

    /**
     * Get current section IDs if in section-based mode
     */
    async getCurrentSectionIds() {
        const processingMode = this.determineProcessingMode();
        
        if (processingMode.mode === 'sections') {
            try {
                this.logger.debug('orchestrator', 'Getting section IDs for sections mode...');
                
                // Try to get section IDs from iframe communication first
                const sectionIds = await this.getSelectedSectionIdsFromIframe();
                this.logger.debug('orchestrator', `Iframe communication result:`, sectionIds);
                
                if (sectionIds && sectionIds.length > 0) {
                    this.logger.debug('orchestrator', `Got ${sectionIds.length} section IDs from iframe:`, sectionIds);
                    return sectionIds;
                }
                
                this.logger.debug('orchestrator', 'Iframe communication failed, trying localStorage...');
                
                // Fallback to localStorage
                const storageSectionIds = this.getSelectedSectionIdsFromStorage();
                this.logger.debug('orchestrator', `localStorage result:`, storageSectionIds);
                
                if (storageSectionIds && storageSectionIds.length > 0) {
                    this.logger.debug('orchestrator', `Got ${storageSectionIds.length} section IDs from localStorage:`, storageSectionIds);
                    return storageSectionIds;
                }
                
                this.logger.debug('orchestrator', 'localStorage failed, trying API...');
                
                // Final fallback to API (will return all sections)
                const apiSectionIds = await this.getSelectedSectionIdsFromAPI();
                this.logger.debug('orchestrator', `API result:`, apiSectionIds);
                
                if (apiSectionIds && apiSectionIds.length > 0) {
                    this.logger.debug('orchestrator', `Got ${apiSectionIds.length} section IDs from API:`, apiSectionIds);
                    // Don't assume all sections are selected - this is incorrect
                    // Instead, return null to indicate we can't determine selection
                    this.logger.warn('orchestrator', 'Cannot determine which sections are selected, returning null');
                    return null;
                }
                
                this.logger.warn('orchestrator', 'No section IDs found from iframe, localStorage, or API');
                return null;
            } catch (error) {
                this.logger.warn('orchestrator', 'Failed to get section IDs:', error);
                return null;
            }
        }
        
        this.logger.debug('orchestrator', 'Not in sections mode, returning null');
        return null; // No sections for single post mode
    }

    /**
     * Get selected section IDs from iframe communication
     */
    async getSelectedSectionIdsFromIframe() {
        return new Promise((resolve) => {
            this.logger.debug('orchestrator', 'Attempting iframe communication for section IDs...');
            
            // Flag to track if we've already received a response
            let responseReceived = false;
            
            // Retry mechanism - try up to 3 times
            let retryCount = 0;
            const maxRetries = 3;
            
            const attemptCommunication = () => {
                this.logger.debug('orchestrator', `Iframe communication attempt ${retryCount + 1}/${maxRetries}`);
                
                // Since we're in an iframe, we need to communicate with the parent window
                // to access the sections iframe which is in the parent document
                if (window.parent && window.parent !== window) {
                    this.logger.debug('orchestrator', 'We are in an iframe, communicating with parent...');
                    try {
                        // Send message to parent to get selected sections
                        window.parent.postMessage({
                            type: 'GET_SELECTED_SECTIONS_FROM_LLM'
                        }, '*');
                        
                        // Set up listener for response from parent
                        const messageHandler = (event) => {
                            this.logger.debug('orchestrator', 'Received message:', event.data);
                            if (event.data && event.data.type === 'SELECTED_SECTIONS_RESPONSE_TO_LLM') {
                                this.logger.debug('orchestrator', 'Received section IDs from parent:', event.data.sectionIds);
                                responseReceived = true;
                                window.removeEventListener('message', messageHandler);
                                clearTimeout(timeoutId);
                                resolve(event.data.sectionIds || []);
                            }
                        };
                        
                        window.addEventListener('message', messageHandler);
                        
                        // Timeout after 3 seconds
                        const timeoutId = setTimeout(() => {
                            if (!responseReceived) {
                                this.logger.warn('orchestrator', 'Parent iframe communication timeout');
                                window.removeEventListener('message', messageHandler);
                                
                                // Retry if we haven't exceeded max retries
                                if (retryCount < maxRetries - 1) {
                                    retryCount++;
                                    setTimeout(attemptCommunication, 1000);
                                } else {
                                    resolve(null);
                                }
                            }
                        }, 3000);
                    } catch (error) {
                        this.logger.warn('orchestrator', 'Parent iframe communication failed:', error);
                        
                        // Retry if we haven't exceeded max retries
                        if (retryCount < maxRetries - 1) {
                            retryCount++;
                            setTimeout(attemptCommunication, 1000);
                        } else {
                            resolve(null);
                        }
                    }
                } else {
                    this.logger.debug('orchestrator', 'Not in an iframe, trying direct iframe access...');
                    
                    // Try multiple iframe selectors since the iframe might be in different contexts
                    const sectionsFrame = document.querySelector('iframe[src*="blog-post-sections"]') || 
                                         document.querySelector('iframe[src*="sections"]') ||
                                         document.querySelector('iframe[title*="Sections"]');
                    
                    if (sectionsFrame && sectionsFrame.contentWindow) {
                        this.logger.debug('orchestrator', 'Found sections iframe, sending message...');
                        try {
                            // Send message to get selected sections
                            sectionsFrame.contentWindow.postMessage({
                                type: 'GET_SELECTED_SECTIONS'
                            }, '*');
                            
                            // Set up listener for response
                            const messageHandler = (event) => {
                                this.logger.debug('orchestrator', 'Received message:', event.data);
                                if (event.data && event.data.type === 'SELECTED_SECTIONS_RESPONSE') {
                                    this.logger.debug('orchestrator', 'Received section IDs from iframe:', event.data.sectionIds);
                                    responseReceived = true;
                                    window.removeEventListener('message', messageHandler);
                                    clearTimeout(timeoutId);
                                    resolve(event.data.sectionIds || []);
                                }
                            };
                            
                            window.addEventListener('message', messageHandler);
                            
                            // Timeout after 3 seconds
                            const timeoutId = setTimeout(() => {
                                if (!responseReceived) {
                                    this.logger.warn('orchestrator', 'Iframe communication timeout');
                                    window.removeEventListener('message', messageHandler);
                                    
                                    // Retry if we haven't exceeded max retries
                                    if (retryCount < maxRetries - 1) {
                                        retryCount++;
                                        setTimeout(attemptCommunication, 1000);
                                    } else {
                                        resolve(null);
                                    }
                                }
                            }, 3000);
                        } catch (error) {
                            this.logger.warn('orchestrator', 'Iframe communication failed:', error);
                            
                            // Retry if we haven't exceeded max retries
                            if (retryCount < maxRetries - 1) {
                                retryCount++;
                                setTimeout(attemptCommunication, 1000);
                            } else {
                                resolve(null);
                            }
                        }
                    } else {
                        this.logger.debug('orchestrator', 'No sections iframe found');
                        
                        // Retry if we haven't exceeded max retries
                        if (retryCount < maxRetries - 1) {
                            retryCount++;
                            setTimeout(attemptCommunication, 1000);
                        } else {
                            resolve(null);
                        }
                    }
                }
            };
            
            // Start the first attempt
            attemptCommunication();
        });
    }

    /**
     * Get selected section IDs from localStorage
     */
    getSelectedSectionIdsFromStorage() {
        try {
            const postId = LLM_STATE.context.post_id;
            
            // Try multiple possible localStorage keys
            const possibleKeys = [
                `sections_selection_post_${postId}`,
                `sections_selection_${postId}`,
                `post_${postId}_sections_selection`,
                `selected_sections_post_${postId}`
            ];
            
            this.logger.debug('orchestrator', `Checking localStorage with keys:`, possibleKeys);
            
            for (const storageKey of possibleKeys) {
                const savedSelection = localStorage.getItem(storageKey);
                if (savedSelection) {
                    this.logger.debug('orchestrator', `Found data in localStorage key: ${storageKey}`);
                    
                    try {
                        const parsed = JSON.parse(savedSelection);
                        this.logger.debug('orchestrator', 'Parsed selection from localStorage:', parsed);
                        
                        // Handle different data structures
                        let selectedIds = [];
                        
                        if (Array.isArray(parsed)) {
                            // If it's an array, assume it contains selected IDs
                            selectedIds = parsed;
                        } else if (typeof parsed === 'object') {
                            // If it's an object, filter by truthy values
                            selectedIds = Object.keys(parsed).filter(id => parsed[id]);
                        }
                        
                        this.logger.debug('orchestrator', 'Selected section IDs from localStorage:', selectedIds);
                        return selectedIds;
                    } catch (parseError) {
                        this.logger.warn('orchestrator', `Failed to parse localStorage data from ${storageKey}:`, parseError);
                        continue;
                    }
                }
            }
            
            this.logger.debug('orchestrator', 'No section selection data found in localStorage');
            return null;
        } catch (error) {
            this.logger.warn('orchestrator', 'Failed to get section IDs from localStorage:', error);
            return null;
        }
    }

    /**
     * Get section IDs directly from API (fallback method)
     */
    async getSelectedSectionIdsFromAPI() {
        try {
            const postId = LLM_STATE.context.post_id;
            this.logger.debug('orchestrator', `Fetching sections from main blog API for post ${postId}...`);
            
            // Call the main blog service on port 5000
            const response = await fetch(`/post-sections/api/sections/${postId}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.logger.debug('orchestrator', 'Sections data from main blog API:', data);
            
            // Extract section IDs from the sections array
            const sections = data.sections || [];
            const sectionIds = sections.map(section => section.id);
            this.logger.debug('orchestrator', 'Section IDs from main blog API:', sectionIds);
            
            return sectionIds;
        } catch (error) {
            this.logger.warn('orchestrator', 'Failed to get section IDs from main blog API:', error);
            return null;
        }
    }

    /**
     * Initialize and update processing mode display
     */
    async initializeProcessingModeDisplay() {
        const displayElement = document.getElementById('processing-mode-text');
        if (!displayElement) {
            this.logger.warn('orchestrator', 'Processing mode display element not found');
            return;
        }

        try {
            const processingMode = this.determineProcessingMode();
            const sectionIds = await this.getCurrentSectionIds();
            
            let displayText = `Post: ${processingMode.postId}`;
            
            if (processingMode.mode === 'sections' && sectionIds?.length > 0) {
                displayText += ` | Sections: ${sectionIds.length} selected [${sectionIds.join(', ')}]`;
            } else if (processingMode.mode === 'sections') {
                displayText += ` | Sections: None selected`;
            } else {
                displayText += ` | Mode: Single post processing`;
            }
            
            displayElement.textContent = displayText;
            this.logger.debug('orchestrator', 'Updated processing mode display:', displayText);
            
            // Set up listener for section selection changes
            this.setupSectionSelectionListener();
            
        } catch (error) {
            this.logger.error('orchestrator', 'Failed to update processing mode display:', error);
            displayElement.textContent = `Post: ${LLM_STATE.context.post_id} | Error loading processing mode`;
        }
    }

    /**
     * Set up listener for section selection changes
     */
    setupSectionSelectionListener() {
        // Listen for messages from sections iframe
        window.addEventListener('message', (event) => {
            if (event.data && event.data.type === 'SECTION_SELECTION_CHANGED') {
                this.updateProcessingModeDisplay();
            }
        });

        // Also listen for localStorage changes as fallback
        window.addEventListener('storage', (event) => {
            const postId = LLM_STATE.context.post_id;
            const storageKey = `sections_selection_post_${postId}`;
            if (event.key === storageKey) {
                this.updateProcessingModeDisplay();
            }
        });
    }

    /**
     * Update processing mode display (can be called externally)
     */
    async updateProcessingModeDisplay() {
        this.logger.debug('orchestrator', 'Updating processing mode display...');
        await this.initializeProcessingModeDisplay();
    }

    /**
     * Force refresh processing mode display (for debugging)
     */
    async forceRefreshProcessingMode() {
        this.logger.info('orchestrator', 'Force refreshing processing mode display...');
        await this.initializeProcessingModeDisplay();
    }

    /**
     * Resolve step_id from database - single source of truth
     */
    async resolveStepId() {
        const { stage, substage, step } = LLM_STATE.context;
        
        try {
            this.logger.debug('orchestrator', `Resolving step_id for: ${stage}/${substage}/${step}`);
            
            const response = await fetch(`/llm-actions/api/step-config/${stage}/${substage}/${step}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            const stepId = data.step_id;
            
            if (!stepId) {
                throw new Error('No step_id returned from API');
            }
            
            this.logger.info('orchestrator', `Resolved step_id: ${stepId}`);
            return stepId;
            
        } catch (error) {
            this.logger.error('orchestrator', 'Failed to resolve step_id:', error);
            throw error;
        }
    }

    /**
     * Initialize modules in the correct order
     */
    async initModules() {
        this.logger.debug('orchestrator', 'Initializing modules...');
        
        // Wait for all modules to be registered
        await this.waitForModules();
        
        // Initialize modules in dependency order
        const moduleOrder = [
            'configManager',  // Load data first
            'promptManager',  // Handle persistence
            'uiConfig',       // Update UI
            'fieldSelector',  // Handle field mappings
            'messageManager', // Handle message management
            'accordionManager', // Handle accordion functionality
            'llmConfigManager' // Handle LLM configuration
        ];
        
        this.logger.debug('orchestrator', 'Available modules:', Object.keys(LLM_STATE.modules));
        
        for (const moduleName of moduleOrder) {
            try {
                const module = this.getModule(moduleName);
                if (!module) {
                    this.logger.warn('orchestrator', `Module ${moduleName} not found`);
                    continue;
                }
                
                if (typeof module.initialize === 'function') {
                    this.logger.debug('orchestrator', `Initializing module: ${moduleName}`);
                    
                    // Pass context to modules that need it
                    if (moduleName === 'configManager' || moduleName === 'promptManager' || moduleName === 'fieldSelector' || moduleName === 'messageManager' || moduleName === 'accordionManager' || moduleName === 'llmConfigManager') {
                        await module.initialize(LLM_STATE.context);
                    } else {
                        await module.initialize();
                    }
                    
                    this.logger.debug('orchestrator', `Module ${moduleName} initialized successfully`);
                } else {
                    this.logger.warn('orchestrator', `Module ${moduleName} missing initialize method`);
                }
            } catch (error) {
                this.logger.error('orchestrator', `Failed to initialize module ${moduleName}:`, error);
                throw error;
            }
        }
        
        this.logger.info('orchestrator', 'All modules initialized successfully');
    }

    /**
     * Wait for all required modules to be registered
     */
    async waitForModules() {
        const requiredModules = ['configManager', 'promptManager', 'uiConfig', 'fieldSelector', 'messageManager', 'accordionManager', 'llmConfigManager'];
        let attempts = 0;
        const maxAttempts = 50; // 5 seconds max
        
        while (attempts < maxAttempts) {
            const missingModules = requiredModules.filter(name => !LLM_STATE.modules[name]);
            
            if (missingModules.length === 0) {
                this.logger.debug('orchestrator', 'All required modules registered');
                return;
            }
            
            this.logger.debug('orchestrator', `Waiting for modules: ${missingModules.join(', ')}`);
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        const missingModules = requiredModules.filter(name => !LLM_STATE.modules[name]);
        throw new Error(`Timeout waiting for modules: ${missingModules.join(', ')}`);
    }

    /**
     * Show error message to user
     */
    showError(message) {
        // Create error display
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #dc2626;
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000;
            max-width: 600px;
            text-align: center;
        `;
        errorDiv.innerHTML = `
            <h3 style="margin: 0 0 10px 0;">Initialization Error</h3>
            <p style="margin: 0;">${message}</p>
            <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.8;">
                Please check the browser console for more details.
            </p>
        `;
        
        document.body.appendChild(errorDiv);
        
        // Remove after 10 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 10000);
    }

    /**
     * Get module
     */
    getModule(name) {
        return LLM_STATE.modules[name];
    }

    /**
     * Get state
     */
    getState() {
        return {
            ...LLM_STATE,
            processingMode: this.determineProcessingMode()
        };
    }

    /**
     * Get selected output field from the output field selector
     */
    getSelectedOutputField() {
        const outputFieldSelect = document.getElementById('output-field-select');
        if (!outputFieldSelect) {
            this.logger.warn('orchestrator', 'Output field selector not found');
            return null;
        }
        
        const selectedValue = outputFieldSelect.value;
        if (!selectedValue || selectedValue.trim() === '') {
            this.logger.debug('orchestrator', 'No output field selected');
            return null;
        }
        
        this.logger.debug('orchestrator', `Selected output field: ${selectedValue}`);
        return selectedValue;
    }

    /**
     * Get message content from the Live Preview
     */
    async getMessageContentFromIframe() {
        try {
            // Try to get content from the message manager preview module
            if (window.MessageManagerPreview && typeof window.MessageManagerPreview.getPreviewText === 'function') {
                const content = window.MessageManagerPreview.getPreviewText();
                this.logger.debug('orchestrator', `Got message content from preview module: ${content ? content.length : 0} characters`);
                return content;
            }
            
            // Fallback: try to get content directly from the preview element
            const previewElement = document.getElementById('enhanced-prompt-preview');
            if (previewElement) {
                const content = previewElement.textContent || '';
                this.logger.debug('orchestrator', `Got message content from preview element: ${content.length} characters`);
                return content;
            }
            
            this.logger.warn('orchestrator', 'No message content found - preview module or element not available');
            return '';
            
        } catch (error) {
            this.logger.error('orchestrator', 'Error getting message content:', error);
            return '';
        }
    }

    /**
     * Process content with LLM
     */
    async processWithLLM(messageContent, outputField = null) {
        try {
            this.logger.debug('orchestrator', 'Processing with LLM:', { messageContentLength: messageContent?.length, outputField });
            
            // Get current context
            const currentContext = LLM_STATE.context;
            if (!currentContext) {
                throw new Error('No workflow context available');
            }
            
            // Extract field name from full field ID (e.g., "post_development.basic_idea" -> "basic_idea")
            let fieldName = outputField || 'basic_idea';
            if (fieldName && fieldName.includes('.')) {
                fieldName = fieldName.split('.').pop();
            }
            
            // Prepare the request payload for /api/run-llm
            const payload = {
                post_id: currentContext.post_id,
                stage: currentContext.stage,
                substage: currentContext.substage,
                step: currentContext.step,
                task: messageContent,
                output_field: fieldName
            };
            
            this.logger.debug('orchestrator', 'Sending LLM request with payload:', payload);
            
            // Make the API call to the LLM service
            const response = await fetch('/llm-actions/api/run-llm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`LLM API error (${response.status}): ${errorText}`);
            }
            
            const result = await response.json();
            this.logger.debug('orchestrator', 'LLM response received:', result);
            
            // Refresh the output field content to show the new result
            await this.refreshOutputFieldContent(fieldName, result.result || result.output);
            
            return result;
            
        } catch (error) {
            this.logger.error('orchestrator', 'Error processing with LLM:', error);
            throw error;
        }
    }

    /**
     * Refresh output field content after LLM processing
     */
    async refreshOutputFieldContent(fieldName, content) {
        try {
            this.logger.debug('orchestrator', `Refreshing output field content for ${fieldName}`);
            
            // Update the output content textarea
            const outputContent = document.getElementById('output-content');
            if (outputContent) {
                outputContent.value = content;
                this.logger.debug('orchestrator', 'Updated output-content textarea');
            }
            
            // Also update the output field selector to show the new content
            const outputFieldSelect = document.getElementById('output-field-select');
            if (outputFieldSelect && outputFieldSelect.value) {
                // Trigger a change event to refresh the field content display
                outputFieldSelect.dispatchEvent(new Event('change'));
                this.logger.debug('orchestrator', 'Triggered output field selector change event');
            }
            
        } catch (error) {
            this.logger.error('orchestrator', 'Error refreshing output field content:', error);
        }
    }

    /**
     * Cleanup
     */
    destroy() {
        this.logger.info('orchestrator', 'Destroying LLM Actions');
        for (const module of Object.values(LLM_STATE.modules)) {
            if (module && typeof module.destroy === 'function') {
                module.destroy();
            }
        }
        this.initialized = false;
    }
}

// Create and export global instance
const llmOrchestrator = new LLMOrchestrator();
window.llmOrchestrator = llmOrchestrator;
window.LLM_STATE = LLM_STATE;

// Register any modules that have already loaded
if (window.configManager) { LLM_STATE.modules.configManager = window.configManager; }
if (window.uiConfig) { LLM_STATE.modules.uiConfig = window.uiConfig; }
if (window.promptManager) { LLM_STATE.modules.promptManager = window.promptManager; }
if (window.fieldSelector) { LLM_STATE.modules.fieldSelector = window.fieldSelector; }

// Global function for modules to register themselves
window.registerLLMModule = function(name, module) {
    console.log(`[LLM-ACTIONS] Registering module: ${name}`, module);
    if (window.LLM_STATE) {
        window.LLM_STATE.modules[name] = module;
        console.log(`[LLM-ACTIONS] Successfully registered module: ${name}`);
    } else {
        console.warn(`[LLM-ACTIONS] LLM_STATE not available for module: ${name}`);
    }
};

// Global function for debugging processing mode
window.debugProcessingMode = function() {
    if (window.llmOrchestrator) {
        window.llmOrchestrator.forceRefreshProcessingMode();
    } else {
        console.error('LLM Orchestrator not available');
    }
};

// Global function to inspect localStorage
window.debugLocalStorage = function() {
    console.log('=== localStorage Debug ===');
    const postId = window.LLM_STATE?.context?.post_id || '53';
    console.log('Current post ID:', postId);
    
    // Check all localStorage keys
    console.log('All localStorage keys:');
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        const value = localStorage.getItem(key);
        console.log(`  ${key}:`, value);
        
        // If it looks like section data, try to parse it
        if (key.includes('section') || key.includes('post')) {
            try {
                const parsed = JSON.parse(value);
                console.log(`    Parsed ${key}:`, parsed);
            } catch (e) {
                // Not JSON, that's fine
            }
        }
    }
    
    // Check specific section selection keys
    const possibleKeys = [
        `sections_selection_post_${postId}`,
        `sections_selection_${postId}`,
        `post_${postId}_sections_selection`,
        `selected_sections_post_${postId}`
    ];
    
    console.log(`\nChecking specific keys for post ${postId}:`);
    for (const storageKey of possibleKeys) {
        const sectionData = localStorage.getItem(storageKey);
        console.log(`  ${storageKey}:`, sectionData);
        
        if (sectionData) {
            try {
                const parsed = JSON.parse(sectionData);
                console.log(`    Parsed:`, parsed);
                if (Array.isArray(parsed)) {
                    console.log(`    Selected IDs (array):`, parsed);
                } else if (typeof parsed === 'object') {
                    const selectedIds = Object.keys(parsed).filter(id => parsed[id]);
                    console.log(`    Selected IDs (object):`, selectedIds);
                }
            } catch (e) {
                console.error(`    Error parsing ${storageKey}:`, e);
            }
        }
    }
    
    console.log('=== End localStorage Debug ===');
};

// Global function to test iframe communication
window.debugIframeCommunication = function() {
    console.log('=== Iframe Communication Debug ===');
    
    if (window.llmOrchestrator) {
        window.llmOrchestrator.getSelectedSectionIdsFromIframe().then(sectionIds => {
            console.log('Iframe communication result:', sectionIds);
        });
    } else {
        console.error('LLM Orchestrator not available');
    }
    
    console.log('=== End Iframe Communication Debug ===');
};

// Global function to test API method
window.debugAPISections = function() {
    console.log('=== API Sections Debug ===');
    
    if (window.llmOrchestrator) {
        window.llmOrchestrator.getSelectedSectionIdsFromAPI().then(sectionIds => {
            console.log('API sections result:', sectionIds);
        });
    } else {
        console.error('LLM Orchestrator not available');
    }
    
    console.log('=== End API Sections Debug ===');
};

// Global function to start Ollama
window.startOllama = async function() {
    try {
        console.log('[StartOllama] Attempting to start Ollama...');
        
        const response = await fetch('/llm-actions/api/ollama/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('[StartOllama] Ollama started successfully');
            console.log('[StartOllama] Ollama started successfully!');
        } else {
            throw new Error(data.error || 'Failed to start Ollama');
        }
        
    } catch (error) {
        console.error('[StartOllama] Error starting Ollama:', error);
        console.log(`[StartOllama] Failed to start Ollama: ${error.message}\n\nPlease start Ollama manually by running 'ollama serve' in your terminal.`);
    }
};

// Global function to run LLM processing
window.runLLM = async function() {
    // Prevent multiple simultaneous calls
    if (window.runLLM.processing) {
        console.log('[RunLLM] Already processing, ignoring duplicate call');
        return;
    }
    
    window.runLLM.processing = true;
    
    // Update button state to show it's running
    const runButton = document.querySelector('.btn-run-llm');
    if (runButton) {
        runButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
        runButton.disabled = true;
    }
    
    try {
        console.log('[RunLLM] Starting LLM execution...');
        
        // Check if orchestrator is initialized
        if (!window.llmOrchestrator || !window.llmOrchestrator.initialized) {
            throw new Error('LLM Actions not initialized. Please wait for the page to load completely.');
        }
        
        // Get current context
        const context = window.LLM_STATE?.context;
        if (!context) {
            throw new Error('No workflow context available');
        }
        
        console.log('[RunLLM] Context:', context);
        
        // Get message content from Live Preview
        const messageContent = await window.llmOrchestrator.getMessageContentFromIframe();
        console.log('[RunLLM] Message content length:', messageContent?.length);
        
        if (!messageContent || messageContent.trim() === '') {
            console.log('[RunLLM] No content in Live Preview. Please add some content to the message elements.');
            alert('No content in Live Preview. Please add some content to the message elements.');
            return;
        }
        
        // Get selected output field
        const outputField = window.llmOrchestrator.getSelectedOutputField();
        console.log('[RunLLM] Selected output field:', outputField);
        
        if (!outputField) {
            console.log('[RunLLM] Please select an output field to save the LLM response.');
            alert('Please select an output field to save the LLM response.');
            return;
        }
        
        console.log('[RunLLM] Processing with context:', {
            stage: context.stage,
            substage: context.substage,
            step: context.step,
            postId: context.post_id,
            outputField: outputField
        });
        
        // Process based on substage
        if (context.substage === 'sections') {
            console.log('[RunLLM] Processing sections with LLM...');
            await processSectionsWithLLM(outputField, messageContent);
        } else {
            console.log('[RunLLM] Processing individual action with LLM...');
            await processIndividualActionWithLLM(outputField, messageContent);
        }
        
        console.log('[RunLLM] LLM processing completed successfully');
        
    } catch (error) {
        console.error('[RunLLM] Error:', error);
        console.log(`[RunLLM] LLM processing failed: ${error.message}`);
        alert(`LLM processing failed: ${error.message}`);
    } finally {
        window.runLLM.processing = false;
        
        // Restore button state
        const runButton = document.querySelector('.btn-run-llm');
        if (runButton) {
            runButton.innerHTML = '<i class="fas fa-play"></i> Run LLM';
            runButton.disabled = false;
        }
    }
};

// Helper function for image generation
async function runImageGeneration() {
    try {
        console.log('[ImageGeneration] Starting image generation...');
        
        // Get selected section IDs
        const selectedSectionIds = await window.llmOrchestrator.getSelectedSectionIdsFromIframe();
        
        if (!selectedSectionIds || selectedSectionIds.length === 0) {
            console.log('[ImageGeneration] Please select at least one section in the green panel for image generation.');
            return;
        }
        
        console.log('[ImageGeneration] Selected sections:', selectedSectionIds);
        
        // Call the image generation API
        const response = await fetch('/images/api/generate-images', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                section_ids: selectedSectionIds
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('[ImageGeneration] Image generation result:', result);
        console.log('[ImageGeneration] Image generation completed! Check the section directories for generated images.');
        
    } catch (error) {
        console.error('[ImageGeneration] Error:', error);
        console.log(`[ImageGeneration] Image generation failed: ${error.message}`);
    }
}

// Helper function for image concepts
async function runImageConcepts() {
    try {
        console.log('[ImageConcepts] Starting image concepts processing...');
        
        const context = window.LLM_STATE?.context;
        const postId = context?.post_id;
        
        if (!postId) {
            throw new Error('No post ID available for image concepts');
        }
        
        // Call the image concepts API
        const response = await fetch('/llm-actions/api/workflow/execute-step', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                post_id: postId,
                step_id: '53'
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('[ImageConcepts] Image concepts result:', result);
        console.log('[ImageConcepts] Image concepts processing completed!');
        
    } catch (error) {
        console.error('[ImageConcepts] Error:', error);
        console.log(`[ImageConcepts] Image concepts processing failed: ${error.message}`);
    }
}

// Helper function for processing sections with LLM
async function processSectionsWithLLM(outputField, messageContent) {
    console.log('[ProcessSections] Starting section processing...');
    
    // Show loading state
    const runButton = document.querySelector('.btn-run-llm');
    const originalButtonText = runButton ? runButton.innerHTML : 'Run LLM';
    if (runButton) {
        runButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing Sections...';
        runButton.disabled = true;
    }
    
    try {
        // Get selected section IDs
        const selectedSectionIds = await window.llmOrchestrator.getSelectedSectionIdsFromIframe();
        console.log('[ProcessSections] Received section IDs:', selectedSectionIds);
        
        if (!selectedSectionIds || selectedSectionIds.length === 0) {
            console.log('[ProcessSections] Please select at least one section in the green panel.');
            return;
        }
        
        let successCount = 0;
        let failureCount = 0;
        
        // Process each section individually
        for (const sectionId of selectedSectionIds) {
            try {
                console.log(`[ProcessSections] Processing section ${sectionId}`);
                
                // Get section context
                const sectionContext = await getSectionContext(sectionId);
                
                // Process with LLM
                const result = await window.llmOrchestrator.processWithLLM(messageContent, outputField);
                
                // Save to output field
                await saveToOutputField(outputField, result, sectionId);
                
                successCount++;
                console.log(`[ProcessSections] Successfully processed section ${sectionId}`);
                
            } catch (error) {
                failureCount++;
                console.error(`[ProcessSections] Error processing section ${sectionId}:`, error);
            }
        }
        
        // Show results
        if (failureCount === 0) {
            console.log(`[ProcessSections] Successfully processed all ${successCount} sections!`);
        } else {
            console.log(`[ProcessSections] Processing completed: ${successCount} successful, ${failureCount} failed. Check console for details.`);
        }
        
    } catch (error) {
        console.error('[ProcessSections] Error:', error);
        console.log(`[ProcessSections] Section processing failed: ${error.message}`);
    } finally {
        // Restore button state
        if (runButton) {
            runButton.innerHTML = originalButtonText;
            runButton.disabled = false;
        }
    }
}

// Helper function for processing individual actions with LLM
async function processIndividualActionWithLLM(outputField, messageContent) {
    console.log('[ProcessIndividualAction] Starting individual action processing...');
    
    try {
        // Process with LLM
                    const result = await window.llmOrchestrator.processWithLLM(messageContent, outputField);
        
        // Save to output field
        await saveToOutputField(outputField, result);
        
        console.log('[ProcessIndividualAction] LLM processing completed successfully!');
        
    } catch (error) {
        console.error('[ProcessIndividualAction] Error:', error);
        console.log(`[ProcessIndividualAction] Individual action processing failed: ${error.message}`);
    }
}

// Helper function for processing a single section
async function processSectionWithLLM(sectionId, outputField, messageContent) {
    try {
        console.log(`[ProcessSection] Processing section ${sectionId}`);
        
        // Get section context
        const sectionContext = await getSectionContext(sectionId);
        
        // Prepare request data with section context
        const requestData = {
            task_prompt_id: window.configManager?.getTaskPrompt(),
            system_prompt_id: window.configManager?.getSystemPrompt(),
            user_input: messageContent,
            output_field: outputField,
            section_id: sectionId,
            section_context: sectionContext
        };
        
        console.log(`[ProcessSection] Request data for section ${sectionId}:`, requestData);
        
        // Call LLM API
        const response = await fetch('http://localhost:5002/api/run-llm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log(`[ProcessSection] Section ${sectionId} response:`, result);
        
        // Save to output field
        await saveToOutputField(outputField, result.response, sectionId);
        
    } catch (error) {
        console.error(`[ProcessSection] Error processing section ${sectionId}:`, error);
        throw error;
    }
}

// Helper function to get section context
async function getSectionContext(sectionId) {
    try {
        const context = window.LLM_STATE?.context;
        const postId = context?.post_id;
        
        if (!postId) {
            console.warn('[GetSectionContext] No post ID available');
            return {};
        }
        
        // Use the correct API endpoint that exists
        const response = await fetch(`http://localhost:5000/api/sections/${postId}`);
        
        if (!response.ok) {
            console.warn(`[GetSectionContext] HTTP error! status: ${response.status} for post ${postId}`);
            return {};
        }
        
        const sectionsData = await response.json();
        console.log(`[GetSectionContext] All sections data:`, sectionsData);
        
        // Find the specific section
        const section = sectionsData.sections?.find(s => s.id == sectionId);
        if (section) {
            console.log(`[GetSectionContext] Found section ${sectionId}:`, section);
            return section;
        } else {
            console.warn(`[GetSectionContext] Section ${sectionId} not found`);
            return {};
        }
        
    } catch (error) {
        console.error(`[GetSectionContext] Error getting context for section ${sectionId}:`, error);
        return {};
    }
}

// Helper function to save to output field
async function saveToOutputField(fieldName, content, sectionId = null) {
    try {
        const context = window.LLM_STATE?.context;
        const postId = context?.post_id;
        
        if (!postId) {
            throw new Error('No post ID available');
        }
        
        console.log('[SaveToOutputField] Saving content for field:', fieldName, 'section:', sectionId);
        
        // For now, just log the content that would be saved
        // TODO: Implement actual save functionality when API is ready
        console.log(`[SaveToOutputField] Content prepared for section ${sectionId}, field ${fieldName}:`, content);
        
        // Remove the alert - just log to console instead
        console.log(`[SaveToOutputField] Content prepared for section ${sectionId}, field ${fieldName}. Please save manually for now.`);
        
        return true;
        
    } catch (error) {
        console.error('[SaveToOutputField] Error saving content:', error);
        return false;
    }
}

// Auto-initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('[LLM-ACTIONS] DOM loaded, initializing orchestrator...');
        setTimeout(() => llmOrchestrator.initialize(), 100);
    });
} else {
    console.log('[LLM-ACTIONS] DOM already loaded, initializing orchestrator...');
    setTimeout(() => llmOrchestrator.initialize(), 100);
}