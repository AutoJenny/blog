/**
 * Message Manager Preview Module
 * Handles preview assembly and display
 */

// Message Manager Preview Class
class MessageManagerPreview {
    constructor() {
        this.logger = window.LLM_STATE?.logger || console;
    }

    /**
     * Initialize the preview module
     */
    initialize() {
        try {
            this.logger.info('messageManagerPreview', 'Initializing preview module...');
            
            this.setupEventListeners();
            
            this.logger.info('messageManagerPreview', 'Preview module initialized successfully');
        } catch (error) {
            this.logger.error('messageManagerPreview', 'Failed to initialize preview module:', error);
            throw error;
        }
    }

    /**
     * Set up event listeners for preview functionality
     */
    setupEventListeners() {
        // Copy preview button
        document.addEventListener('click', (e) => {
            if (e.target.id === 'copy-preview-btn' || e.target.closest('#copy-preview-btn')) {
                this.copyPreview();
            }
        });
    }

    /**
     * Update the preview with assembled content
     */
    updatePreview() {
        try {
            const elements = this.getEnabledElements();
            const previewText = this.assemblePreviewText(elements);
            const stats = this.calculateStats(elements);
            
            this.updatePreviewDisplay(previewText);
            this.updatePreviewStats(stats);
            
            this.logger.debug('messageManagerPreview', `Preview updated: ${stats.elementCount} elements, ${stats.characterCount} characters`);
        } catch (error) {
            this.logger.error('messageManagerPreview', 'Failed to update preview:', error);
        }
    }

    /**
     * Get enabled elements from elements module
     */
    getEnabledElements() {
        if (window.MessageManagerElements) {
            return window.MessageManagerElements.getEnabledElements();
        }
        return [];
    }

    /**
     * Assemble preview text from enabled elements
     */
    assemblePreviewText(elements) {
        return elements
            .map(element => this.formatElementContent(element))
            .filter(content => content.trim())
            .join('\n\n');
    }

    /**
     * Format element content for preview
     */
    formatElementContent(element) {
        if (!element || !element.content) return '';
        
        // Add title as header if it exists
        let content = element.title ? `## ${element.title}\n\n` : '';
        content += element.content;
        
        return content;
    }

    /**
     * Calculate preview statistics
     */
    calculateStats(elements) {
        const elementCount = elements.length;
        const characterCount = elements.reduce((total, element) => {
            return total + (element.content ? element.content.length : 0);
        }, 0);
        
        return { elementCount, characterCount };
    }

    /**
     * Update preview display
     */
    updatePreviewDisplay(previewText) {
        const previewElement = document.getElementById('enhanced-prompt-preview');
        if (previewElement) {
            previewElement.textContent = previewText;
        }
    }

    /**
     * Update preview statistics display
     */
    updatePreviewStats(stats) {
        const statsElement = document.getElementById('preview-stats');
        if (statsElement) {
            statsElement.textContent = `${stats.elementCount} elements, ${stats.characterCount} characters`;
        }
    }

    /**
     * Copy preview to clipboard
     */
    async copyPreview() {
        try {
            const previewElement = document.getElementById('enhanced-prompt-preview');
            if (!previewElement || !previewElement.textContent) {
                this.logger.warn('messageManagerPreview', 'No preview content to copy');
                return;
            }

            await navigator.clipboard.writeText(previewElement.textContent);
            this.logger.info('messageManagerPreview', 'Preview copied to clipboard');
            
            // Show feedback
            this.showCopyFeedback();
        } catch (error) {
            this.logger.error('messageManagerPreview', 'Failed to copy preview:', error);
        }
    }

    /**
     * Show copy feedback
     */
    showCopyFeedback() {
        const copyButton = document.getElementById('copy-preview-btn');
        if (copyButton) {
            const originalText = copyButton.textContent;
            copyButton.textContent = 'Copied!';
            setTimeout(() => {
                copyButton.textContent = originalText;
            }, 2000);
        }
    }

    /**
     * Get current preview text
     */
    getPreviewText() {
        const previewElement = document.getElementById('enhanced-prompt-preview');
        return previewElement ? previewElement.textContent : '';
    }

    /**
     * Clear preview
     */
    clearPreview() {
        this.updatePreviewDisplay('');
        this.updatePreviewStats({ elementCount: 0, characterCount: 0 });
    }

    /**
     * Update context
     */
    updateContext(context) {
        this.context = context;
        this.logger.debug('messageManagerPreview', 'Context updated:', context);
    }
}

// Create and export the preview module
const messageManagerPreview = new MessageManagerPreview();

// Make it globally available
window.MessageManagerPreview = messageManagerPreview; 