/**
 * LLM Processor Module
 *
 * Responsibilities:
 * - Process sections through LLM
 * - Handle LLM API calls and responses
 * - Manage processing state and progress
 * - Provide processing results to other modules
 *
 * Dependencies: logger.js, config-manager.js, section-gatherer.js
 * Dependents: output-manager.js
 *
 * @version 1.0
 */

// Processing state
const PROCESSING_STATE = {
    // Current processing status
    status: 'idle', // 'idle', 'processing', 'completed', 'error'
    
    // Processing progress
    currentSection: 0,
    totalSections: 0,
    processedSections: 0,
    failedSections: 0,
    
    // Results
    results: [],
    errors: [],
    
    // Processing options
    options: {
        batchSize: 1,
        retryAttempts: 3,
        timeout: 30000
    }
};

/**
 * LLM Processor class
 */
class LLMProcessor {
    constructor() {
        this.logger = window.logger;
        this.context = null;
        this.initialized = false;
        this.abortController = null;
    }

    /**
     * Initialize the LLM processor
     */
    async initialize(context) {
        this.logger.trace('llmProcessor', 'initialize', 'enter');
        this.context = context;
        this.initialized = true;
        this.logger.info('llmProcessor', 'LLM processor initialized');
        this.logger.trace('llmProcessor', 'initialize', 'exit');
    }

    /**
     * Process sections through LLM
     */
    async processSections() {
        this.logger.trace('llmProcessor', 'processSections', 'enter');
        
        // Check prerequisites
        if (!this.checkPrerequisites()) {
            return false;
        }
        
        // Get sections to process
        const sections = sectionGatherer.getSectionsForProcessing();
        if (sections.length === 0) {
            this.logger.warn('llmProcessor', 'No sections to process');
            return false;
        }
        
        // Initialize processing state
        this.initializeProcessingState(sections);
        
        try {
            // Start processing
            await this.startProcessing(sections);
            return true;
            
        } catch (error) {
            this.logger.error('llmProcessor', 'Processing failed:', error);
            PROCESSING_STATE.status = 'error';
            PROCESSING_STATE.errors.push(error.message);
            return false;
        }
        
        this.logger.trace('llmProcessor', 'processSections', 'exit');
    }

    /**
     * Check prerequisites for processing
     */
    checkPrerequisites() {
        // Check if configuration is ready
        if (!configManager.isConfigured()) {
            this.logger.error('llmProcessor', 'Configuration not complete');
            return false;
        }
        
        // Check if sections are ready
        if (!sectionGatherer.isReady()) {
            this.logger.error('llmProcessor', 'Sections not ready');
            return false;
        }
        
        // Check if not already processing
        if (PROCESSING_STATE.status === 'processing') {
            this.logger.warn('llmProcessor', 'Already processing');
            return false;
        }
        
        return true;
    }

    /**
     * Initialize processing state
     */
    initializeProcessingState(sections) {
        PROCESSING_STATE.status = 'processing';
        PROCESSING_STATE.currentSection = 0;
        PROCESSING_STATE.totalSections = sections.length;
        PROCESSING_STATE.processedSections = 0;
        PROCESSING_STATE.failedSections = 0;
        PROCESSING_STATE.results = [];
        PROCESSING_STATE.errors = [];
        
        this.logger.info('llmProcessor', `Starting processing of ${sections.length} sections`);
    }

    /**
     * Start processing sections
     */
    async startProcessing(sections) {
        this.logger.trace('llmProcessor', 'startProcessing', 'enter');
        
        // Create abort controller for cancellation
        this.abortController = new AbortController();
        
        // Process sections sequentially
        for (let i = 0; i < sections.length; i++) {
            if (this.abortController.signal.aborted) {
                this.logger.info('llmProcessor', 'Processing cancelled');
                break;
            }
            
            PROCESSING_STATE.currentSection = i + 1;
            const section = sections[i];
            
            try {
                this.logger.debug('llmProcessor', `Processing section ${section.id}`);
                
                // Process single section
                const result = await this.processSection(section);
                
                if (result.success) {
                    PROCESSING_STATE.results.push(result);
                    PROCESSING_STATE.processedSections++;
                    this.logger.debug('llmProcessor', `Section ${section.id} processed successfully`);
                } else {
                    PROCESSING_STATE.errors.push(result.error);
                    PROCESSING_STATE.failedSections++;
                    this.logger.error('llmProcessor', `Section ${section.id} failed:`, result.error);
                }
                
            } catch (error) {
                PROCESSING_STATE.errors.push(error.message);
                PROCESSING_STATE.failedSections++;
                this.logger.error('llmProcessor', `Section ${section.id} failed:`, error);
            }
            
            // Update progress
            this.updateProgress();
        }
        
        // Mark as completed
        PROCESSING_STATE.status = 'completed';
        this.logger.info('llmProcessor', 'Processing completed', {
            processed: PROCESSING_STATE.processedSections,
            failed: PROCESSING_STATE.failedSections,
            total: PROCESSING_STATE.totalSections
        });
        
        this.logger.trace('llmProcessor', 'startProcessing', 'exit');
    }

    /**
     * Process a single section
     */
    async processSection(section) {
        this.logger.trace('llmProcessor', 'processSection', 'enter', { sectionId: section.id });
        
        try {
            // Get configuration
            const fullPrompt = configManager.getFullPrompt();
            const { post_id, step_id } = this.context;
            
            // Prepare request data
            const requestData = {
                post_id: post_id,
                step_id: step_id,
                section_id: section.id,
                message_content: fullPrompt,
                context: {
                    section_ids: [section.id],
                    section_content: section.content || '',
                    section_title: section.title || '',
                    section_type: section.type || 'text'
                }
            };
            
            // Make API call
            const response = await this.callLLMAPI(requestData);
            
            // Process response
            const result = this.processResponse(response, section);
            
            this.logger.trace('llmProcessor', 'processSection', 'exit', { success: result.success });
            return result;
            
        } catch (error) {
            this.logger.error('llmProcessor', `Error processing section ${section.id}:`, error);
            return {
                success: false,
                sectionId: section.id,
                error: error.message
            };
        }
    }

    /**
     * Call LLM API
     */
    async callLLMAPI(requestData) {
        this.logger.trace('llmProcessor', 'callLLMAPI', 'enter');
        
        const response = await fetch('http://localhost:5000/api/workflow/execute-step', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData),
            signal: this.abortController.signal,
            timeout: PROCESSING_STATE.options.timeout
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        this.logger.trace('llmProcessor', 'callLLMAPI', 'exit');
        return data;
    }

    /**
     * Process API response
     */
    processResponse(response, section) {
        this.logger.trace('llmProcessor', 'processResponse', 'enter');
        
        try {
            if (response.success) {
                return {
                    success: true,
                    sectionId: section.id,
                    result: response.result,
                    output: response.output,
                    metadata: response.metadata || {}
                };
            } else {
                return {
                    success: false,
                    sectionId: section.id,
                    error: response.error || 'Unknown error'
                };
            }
            
        } catch (error) {
            this.logger.error('llmProcessor', 'Error processing response:', error);
            return {
                success: false,
                sectionId: section.id,
                error: 'Failed to process response'
            };
        }
        
        this.logger.trace('llmProcessor', 'processResponse', 'exit');
    }

    /**
     * Update progress display
     */
    updateProgress() {
        const progress = (PROCESSING_STATE.processedSections + PROCESSING_STATE.failedSections) / PROCESSING_STATE.totalSections * 100;
        
        // Update progress bar
        const progressBar = document.getElementById('processing-progress');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            progressBar.textContent = `${Math.round(progress)}%`;
        }
        
        // Update status text
        const statusText = document.getElementById('processing-status');
        if (statusText) {
            statusText.textContent = `Processing ${PROCESSING_STATE.currentSection} of ${PROCESSING_STATE.totalSections} sections`;
        }
        
        // Update results count
        const resultsCount = document.getElementById('results-count');
        if (resultsCount) {
            resultsCount.textContent = `${PROCESSING_STATE.processedSections} successful, ${PROCESSING_STATE.failedSections} failed`;
        }
    }

    /**
     * Cancel processing
     */
    cancelProcessing() {
        this.logger.info('llmProcessor', 'Cancelling processing');
        
        if (this.abortController) {
            this.abortController.abort();
        }
        
        PROCESSING_STATE.status = 'cancelled';
    }

    /**
     * Get processing results
     */
    getResults() {
        return {
            status: PROCESSING_STATE.status,
            results: PROCESSING_STATE.results,
            errors: PROCESSING_STATE.errors,
            summary: {
                total: PROCESSING_STATE.totalSections,
                processed: PROCESSING_STATE.processedSections,
                failed: PROCESSING_STATE.failedSections,
                successRate: PROCESSING_STATE.totalSections > 0 ? 
                    (PROCESSING_STATE.processedSections / PROCESSING_STATE.totalSections * 100) : 0
            }
        };
    }

    /**
     * Get current state
     */
    getState() {
        return { ...PROCESSING_STATE };
    }

    /**
     * Check if processing is active
     */
    isProcessing() {
        return PROCESSING_STATE.status === 'processing';
    }

    /**
     * Set processing options
     */
    setOptions(options) {
        PROCESSING_STATE.options = { ...PROCESSING_STATE.options, ...options };
        this.logger.debug('llmProcessor', 'Processing options updated:', PROCESSING_STATE.options);
    }

    /**
     * Cleanup
     */
    destroy() {
        this.logger.info('llmProcessor', 'Destroying LLM processor');
        
        if (this.abortController) {
            this.abortController.abort();
        }
        
        this.initialized = false;
        PROCESSING_STATE.status = 'idle';
    }
}

// Create and export global instance
const llmProcessor = new LLMProcessor();
window.llmProcessor = llmProcessor;
window.PROCESSING_STATE = PROCESSING_STATE;

// Log initialization
if (window.logger) {
    window.logger.info('llmProcessor', 'LLM Processor Module loaded');
} 