/**
 * Output Manager Module
 *
 * Responsibilities:
 * - Manage output fields and result display
 * - Handle LLM processing results
 * - Coordinate with LLM processor for result display
 * - Manage output field interactions and formatting
 * - Provide output data to other modules
 *
 * Dependencies: logger.js, llm-processor.js
 * Dependents: None
 *
 * @version 1.0
 */

// Output state
const OUTPUT_STATE = {
    // Output field data
    outputs: {},
    
    // Output field elements
    elements: {},
    
    // Processing results
    results: [],
    
    // Display state
    displayMode: 'list', // 'list', 'grid', 'detailed'
    autoScroll: true,
    
    // UI state
    initialized: false,
    loading: false
};

/**
 * Output Manager class
 */
class OutputManager {
    constructor() {
        this.logger = window.logger;
        this.context = null;
        this.initialized = false;
    }

    /**
     * Initialize the output manager
     */
    async initialize(context) {
        this.logger.trace('outputManager', 'initialize', 'enter');
        this.context = context;
        
        try {
            // Initialize output fields
            await this.initializeOutputFields();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Set up LLM processor integration
            this.setupLLMProcessorIntegration();
            
            this.initialized = true;
            OUTPUT_STATE.initialized = true;
            
            this.logger.info('outputManager', 'Output manager initialized');
            
        } catch (error) {
            this.logger.error('outputManager', 'Failed to initialize output manager:', error);
            throw error;
        }
        
        this.logger.trace('outputManager', 'initialize', 'exit');
    }

    /**
     * Initialize output fields
     */
    async initializeOutputFields() {
        this.logger.trace('outputManager', 'initializeOutputFields', 'enter');
        
        // Find all output fields
        const outputElements = document.querySelectorAll('.output-field, .result-display, [data-output-field]');
        this.logger.debug('outputManager', `Found ${outputElements.length} output elements`);
        
        for (const element of outputElements) {
            await this.initializeSingleOutput(element);
        }
        
        this.logger.trace('outputManager', 'initializeOutputFields', 'exit');
    }

    /**
     * Initialize a single output field
     */
    async initializeSingleOutput(element) {
        const outputId = element.id || element.getAttribute('data-output-field');
        const outputType = element.getAttribute('data-output-type') || 'text';
        const outputLabel = element.getAttribute('data-output-label') || outputId;
        
        this.logger.debug('outputManager', `Initializing output: ${outputId} (${outputType})`);
        
        // Store element reference
        OUTPUT_STATE.elements[outputId] = {
            element: element,
            type: outputType,
            label: outputLabel,
            value: element.textContent || element.value || ''
        };
        
        // Set up output-specific event listeners
        this.setupOutputEventListeners(element, outputId);
    }

    /**
     * Set up output-specific event listeners
     */
    setupOutputEventListeners(element, outputId) {
        // Click event for copy functionality
        element.addEventListener('click', (event) => {
            if (event.target.classList.contains('copy-button') || element.hasAttribute('data-copyable')) {
                this.copyOutputContent(outputId);
            }
        });
        
        // Double-click for edit mode (if enabled)
        element.addEventListener('dblclick', (event) => {
            if (element.hasAttribute('data-editable')) {
                this.enableOutputEdit(outputId);
            }
        });
        
        // Auto-scroll for new content
        if (OUTPUT_STATE.autoScroll) {
            element.addEventListener('DOMSubtreeModified', () => {
                this.autoScrollToBottom(element);
            });
        }
    }

    /**
     * Set up LLM processor integration
     */
    setupLLMProcessorIntegration() {
        // Listen for LLM processing events
        document.addEventListener('llmProcessingStarted', () => {
            this.handleProcessingStarted();
        });
        
        document.addEventListener('llmProcessingCompleted', (event) => {
            this.handleProcessingCompleted(event.detail);
        });
        
        document.addEventListener('llmProcessingError', (event) => {
            this.handleProcessingError(event.detail);
        });
        
        // Listen for individual result updates
        document.addEventListener('llmResultUpdated', (event) => {
            this.handleResultUpdated(event.detail);
        });
    }

    /**
     * Handle processing started
     */
    handleProcessingStarted() {
        this.logger.debug('outputManager', 'LLM processing started');
        
        // Clear previous results
        this.clearAllOutputs();
        
        // Show processing indicator
        this.showProcessingIndicator();
        
        // Update UI state
        OUTPUT_STATE.loading = true;
    }

    /**
     * Handle processing completed
     */
    handleProcessingCompleted(results) {
        this.logger.debug('outputManager', 'LLM processing completed', results);
        
        // Hide processing indicator
        this.hideProcessingIndicator();
        
        // Display results
        this.displayResults(results);
        
        // Update UI state
        OUTPUT_STATE.loading = false;
        OUTPUT_STATE.results = results.results || [];
    }

    /**
     * Handle processing error
     */
    handleProcessingError(error) {
        this.logger.error('outputManager', 'LLM processing error:', error);
        
        // Hide processing indicator
        this.hideProcessingIndicator();
        
        // Display error
        this.displayError(error);
        
        // Update UI state
        OUTPUT_STATE.loading = false;
    }

    /**
     * Handle result updated
     */
    handleResultUpdated(result) {
        this.logger.debug('outputManager', 'LLM result updated:', result);
        
        // Update specific result
        this.updateResult(result);
    }

    /**
     * Display results
     */
    displayResults(results) {
        this.logger.trace('outputManager', 'displayResults', 'enter');
        
        const { results: resultList, summary } = results;
        
        // Display summary
        this.displaySummary(summary);
        
        // Display individual results
        if (resultList && resultList.length > 0) {
            resultList.forEach(result => {
                this.displaySingleResult(result);
            });
        }
        
        this.logger.trace('outputManager', 'displayResults', 'exit');
    }

    /**
     * Display summary
     */
    displaySummary(summary) {
        const summaryElement = document.getElementById('processing-summary');
        if (!summaryElement) return;
        
        const { total, processed, failed, successRate } = summary;
        
        summaryElement.innerHTML = `
            <div class="summary-stats">
                <span class="stat total">Total: ${total}</span>
                <span class="stat processed">Processed: ${processed}</span>
                <span class="stat failed">Failed: ${failed}</span>
                <span class="stat success-rate">Success Rate: ${successRate.toFixed(1)}%</span>
            </div>
        `;
        
        this.logger.debug('outputManager', 'Summary displayed:', summary);
    }

    /**
     * Display single result
     */
    displaySingleResult(result) {
        const { sectionId, success, output, error } = result;
        
        if (success) {
            this.displaySuccessfulResult(sectionId, output);
        } else {
            this.displayFailedResult(sectionId, error);
        }
    }

    /**
     * Display successful result
     */
    displaySuccessfulResult(sectionId, output) {
        const resultContainer = document.getElementById('results-container');
        if (!resultContainer) return;
        
        const resultElement = document.createElement('div');
        resultElement.className = 'result-item success';
        resultElement.innerHTML = `
            <div class="result-header">
                <span class="section-id">Section ${sectionId}</span>
                <span class="status success">✓ Success</span>
                <button class="copy-button" onclick="outputManager.copyResultContent('${sectionId}')">Copy</button>
            </div>
            <div class="result-content">
                <pre>${this.escapeHtml(output)}</pre>
            </div>
        `;
        
        resultContainer.appendChild(resultElement);
        
        this.logger.debug('outputManager', `Successful result displayed for section ${sectionId}`);
    }

    /**
     * Display failed result
     */
    displayFailedResult(sectionId, error) {
        const resultContainer = document.getElementById('results-container');
        if (!resultContainer) return;
        
        const resultElement = document.createElement('div');
        resultElement.className = 'result-item error';
        resultElement.innerHTML = `
            <div class="result-header">
                <span class="section-id">Section ${sectionId}</span>
                <span class="status error">✗ Failed</span>
            </div>
            <div class="result-content">
                <pre class="error-message">${this.escapeHtml(error)}</pre>
            </div>
        `;
        
        resultContainer.appendChild(resultElement);
        
        this.logger.debug('outputManager', `Failed result displayed for section ${sectionId}`);
    }

    /**
     * Display error
     */
    displayError(error) {
        const errorContainer = document.getElementById('error-container');
        if (!errorContainer) return;
        
        errorContainer.innerHTML = `
            <div class="error-display">
                <h3>Processing Error</h3>
                <p>${this.escapeHtml(error.message || error)}</p>
            </div>
        `;
        
        errorContainer.style.display = 'block';
        
        this.logger.debug('outputManager', 'Error displayed:', error);
    }

    /**
     * Show processing indicator
     */
    showProcessingIndicator() {
        const indicator = document.getElementById('processing-indicator');
        if (indicator) {
            indicator.style.display = 'block';
            indicator.innerHTML = `
                <div class="processing-spinner"></div>
                <span>Processing sections...</span>
            `;
        }
    }

    /**
     * Hide processing indicator
     */
    hideProcessingIndicator() {
        const indicator = document.getElementById('processing-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    /**
     * Clear all outputs
     */
    clearAllOutputs() {
        // Clear result container
        const resultContainer = document.getElementById('results-container');
        if (resultContainer) {
            resultContainer.innerHTML = '';
        }
        
        // Clear error container
        const errorContainer = document.getElementById('error-container');
        if (errorContainer) {
            errorContainer.style.display = 'none';
            errorContainer.innerHTML = '';
        }
        
        // Clear summary
        const summaryElement = document.getElementById('processing-summary');
        if (summaryElement) {
            summaryElement.innerHTML = '';
        }
        
        this.logger.debug('outputManager', 'All outputs cleared');
    }

    /**
     * Copy output content
     */
    copyOutputContent(outputId) {
        const output = OUTPUT_STATE.elements[outputId];
        if (!output) return;
        
        const content = output.value || output.element.textContent;
        
        navigator.clipboard.writeText(content).then(() => {
            this.showCopySuccess(outputId);
            this.logger.debug('outputManager', `Content copied for ${outputId}`);
        }).catch(error => {
            this.logger.error('outputManager', 'Failed to copy content:', error);
        });
    }

    /**
     * Copy result content
     */
    copyResultContent(sectionId) {
        const resultElement = document.querySelector(`[data-section-id="${sectionId}"] .result-content pre`);
        if (!resultElement) return;
        
        const content = resultElement.textContent;
        
        navigator.clipboard.writeText(content).then(() => {
            this.showCopySuccess(`result-${sectionId}`);
            this.logger.debug('outputManager', `Result content copied for section ${sectionId}`);
        }).catch(error => {
            this.logger.error('outputManager', 'Failed to copy result content:', error);
        });
    }

    /**
     * Show copy success feedback
     */
    showCopySuccess(elementId) {
        const element = document.getElementById(elementId) || document.querySelector(`[data-section-id="${elementId.replace('result-', '')}"]`);
        if (!element) return;
        
        const originalText = element.textContent;
        element.textContent = 'Copied!';
        element.classList.add('copy-success');
        
        setTimeout(() => {
            element.textContent = originalText;
            element.classList.remove('copy-success');
        }, 2000);
    }

    /**
     * Enable output edit mode
     */
    enableOutputEdit(outputId) {
        const output = OUTPUT_STATE.elements[outputId];
        if (!output || !output.element.hasAttribute('data-editable')) return;
        
        const currentContent = output.value || output.element.textContent;
        
        // Create textarea for editing
        const textarea = document.createElement('textarea');
        textarea.value = currentContent;
        textarea.className = 'output-edit-textarea';
        
        // Replace element content
        output.element.innerHTML = '';
        output.element.appendChild(textarea);
        textarea.focus();
        
        // Set up save/cancel functionality
        textarea.addEventListener('blur', () => {
            this.saveOutputEdit(outputId, textarea.value);
        });
        
        textarea.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && event.ctrlKey) {
                this.saveOutputEdit(outputId, textarea.value);
            } else if (event.key === 'Escape') {
                this.cancelOutputEdit(outputId, currentContent);
            }
        });
    }

    /**
     * Save output edit
     */
    saveOutputEdit(outputId, newContent) {
        const output = OUTPUT_STATE.elements[outputId];
        if (!output) return;
        
        output.value = newContent;
        output.element.innerHTML = `<pre>${this.escapeHtml(newContent)}</pre>`;
        
        this.logger.debug('outputManager', `Output edit saved for ${outputId}`);
    }

    /**
     * Cancel output edit
     */
    cancelOutputEdit(outputId, originalContent) {
        const output = OUTPUT_STATE.elements[outputId];
        if (!output) return;
        
        output.element.innerHTML = `<pre>${this.escapeHtml(originalContent)}</pre>`;
        
        this.logger.debug('outputManager', `Output edit cancelled for ${outputId}`);
    }

    /**
     * Auto-scroll to bottom
     */
    autoScrollToBottom(element) {
        element.scrollTop = element.scrollHeight;
    }

    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Set output value
     */
    setOutputValue(outputId, value) {
        const output = OUTPUT_STATE.elements[outputId];
        if (!output) {
            this.logger.warn('outputManager', `Output not found: ${outputId}`);
            return;
        }
        
        output.value = value;
        
        if (output.type === 'text' || output.type === 'html') {
            output.element.innerHTML = `<pre>${this.escapeHtml(value)}</pre>`;
        } else {
            output.element.textContent = value;
        }
        
        this.logger.debug('outputManager', `Set output value: ${outputId} = "${value}"`);
    }

    /**
     * Get output value
     */
    getOutputValue(outputId) {
        const output = OUTPUT_STATE.elements[outputId];
        return output ? output.value : '';
    }

    /**
     * Get all output values
     */
    getAllOutputValues() {
        const values = {};
        for (const [outputId, output] of Object.entries(OUTPUT_STATE.elements)) {
            values[outputId] = output.value;
        }
        return values;
    }

    /**
     * Set display mode
     */
    setDisplayMode(mode) {
        OUTPUT_STATE.displayMode = mode;
        this.updateDisplayMode();
        this.logger.debug('outputManager', `Display mode set to: ${mode}`);
    }

    /**
     * Update display mode
     */
    updateDisplayMode() {
        const container = document.getElementById('results-container');
        if (!container) return;
        
        container.className = `results-container ${OUTPUT_STATE.displayMode}-mode`;
    }

    /**
     * Toggle auto-scroll
     */
    toggleAutoScroll() {
        OUTPUT_STATE.autoScroll = !OUTPUT_STATE.autoScroll;
        this.logger.debug('outputManager', `Auto-scroll ${OUTPUT_STATE.autoScroll ? 'enabled' : 'disabled'}`);
    }

    /**
     * Set up global event listeners
     */
    setupEventListeners() {
        // Listen for display mode changes
        document.addEventListener('displayModeChanged', (event) => {
            this.setDisplayMode(event.detail.mode);
        });
        
        // Listen for auto-scroll toggle
        document.addEventListener('autoScrollToggled', () => {
            this.toggleAutoScroll();
        });
    }

    /**
     * Get current state
     */
    getState() {
        return { ...OUTPUT_STATE };
    }

    /**
     * Refresh output display
     */
    refresh() {
        this.logger.info('outputManager', 'Refreshing output display');
        this.updateDisplayMode();
    }

    /**
     * Cleanup
     */
    destroy() {
        this.logger.info('outputManager', 'Destroying output manager');
        this.initialized = false;
        OUTPUT_STATE.initialized = false;
    }
}

// Create and export global instance
const outputManager = new OutputManager();
window.outputManager = outputManager;
window.OUTPUT_STATE = OUTPUT_STATE;

// Log initialization
if (window.logger) {
    window.logger.info('outputManager', 'Output Manager Module loaded');
} 