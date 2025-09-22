/**
 * Message Manager UI Module
 * Handles layout creation and CSS injection
 */

// Message Manager UI Class
class MessageManagerUI {
    constructor() {
        this.logger = window.LLM_STATE?.logger || console;
    }

    /**
     * Initialize the UI
     */
    initialize() {
        try {
            this.logger.info('messageManagerUI', 'Initializing UI...');
            
            this.setupTwoPaneLayout();
            this.addLayoutStyles();
            
            this.logger.info('messageManagerUI', 'UI initialized successfully');
        } catch (error) {
            this.logger.error('messageManagerUI', 'Failed to initialize UI:', error);
            throw error;
        }
    }

    /**
     * Set up two-pane layout with message elements and preview
     */
    setupTwoPaneLayout() {
        const messageContainer = document.getElementById('message-management');
        if (!messageContainer) {
            this.logger.warn('messageManagerUI', 'Message management container not found');
            return;
        }

        // Clear any existing content and create the two-pane layout
        messageContainer.innerHTML = `
            <div class="section-title">
                <i class="fas fa-cogs"></i>
                LLM Message Management
            </div>

            <div class="message-management-layout">
                <!-- Left: Message Elements Pane -->
                <div class="message-elements-pane">
                    <div class="pane-header">
                        <h4>Message Elements</h4>
                    </div>
                    
                    <div class="elements-container">
                        <!-- Elements will be populated here -->
                    </div>
                </div>

                <!-- Right: Preview Pane -->
                <div class="message-preview-pane">
                    <div class="pane-header">
                        <h4>Live Preview</h4>
                    </div>
                    
                    <div class="preview-container">
                        <div id="enhanced-prompt-preview" class="preview-content">
                            <!-- Preview content will be assembled here -->
                        </div>
                        <div class="preview-stats">
                            <span id="preview-stats">0 elements, 0 characters</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Add CSS styles for the two-pane layout
     */
    addLayoutStyles() {
        // Check if styles already exist
        if (document.getElementById('message-manager-styles')) {
            return;
        }

        const styleSheet = document.createElement('style');
        styleSheet.id = 'message-manager-styles';
        styleSheet.textContent = `
            .message-management-layout {
                display: flex;
                gap: 20px;
                margin-top: 15px;
                min-height: 400px;
            }

            .message-elements-pane,
            .message-preview-pane {
                flex: 1;
                background: var(--llm-surface);
                border: 1px solid var(--llm-border);
                border-radius: 8px;
                display: flex;
                flex-direction: column;
            }

            .pane-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 20px;
                border-bottom: 1px solid var(--llm-border);
                background: var(--llm-bg);
                border-radius: 8px 8px 0 0;
            }

            .pane-header h4 {
                margin: 0;
                color: var(--llm-purple-light);
                font-size: 16px;
                font-weight: 600;
            }

            .elements-container,
            .preview-container {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
            }

            .preview-content {
                background: var(--llm-bg);
                border: 1px solid var(--llm-border);
                border-radius: 6px;
                padding: 15px;
                min-height: 200px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.4;
                white-space: pre-wrap;
                word-wrap: break-word;
                color: #e0e0e0;
            }

            .preview-stats {
                margin-top: 10px;
                text-align: right;
                font-size: 11px;
                color: var(--llm-purple-light);
                opacity: 0.7;
            }

            /* Responsive design for narrower views */
            @media (max-width: 768px) {
                .message-management-layout {
                    flex-direction: column;
                    gap: 15px;
                }

                .message-elements-pane,
                .message-preview-pane {
                    min-height: 300px;
                }

                .pane-header {
                    padding: 12px 15px;
                }

                .elements-container,
                .preview-container {
                    padding: 15px;
                }

                .preview-content {
                    min-height: 150px;
                    font-size: 12px;
                }
            }

            /* Even smaller screens */
            @media (max-width: 480px) {
                .preview-content {
                    min-height: 120px;
                    font-size: 11px;
                }
            }
        `;

        document.head.appendChild(styleSheet);
    }

    /**
     * Update context
     */
    updateContext(context) {
        this.context = context;
        this.logger.debug('messageManagerUI', 'Context updated:', context);
    }
}

// Create and export the UI module
const messageManagerUI = new MessageManagerUI();

// Make it globally available
window.MessageManagerUI = messageManagerUI; 