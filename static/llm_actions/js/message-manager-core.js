/**
 * Message Manager Core Module
 * Main orchestrator for message management functionality
 */

// Global state for message management
const MESSAGE_STATE = {
    elements: [],
    previewText: '',
    previewStats: {
        characterCount: 0,
        elementCount: 0
    },
    elementOrder: [],
    enabledElements: new Set()
};

// Message Manager Core Class
class MessageManagerCore {
    constructor(context) {
        this.context = context;
        this.logger = window.LLM_STATE?.logger || console;
        this.modules = {};
    }

    /**
     * Initialize the message manager core
     */
    async initialize() {
        try {
            this.logger.info('messageManager', 'Initializing message manager core...');
            
            // Debug: Check which modules are available
            this.logger.debug('messageManager', 'Available modules:', {
                ui: !!window.MessageManagerUI,
                elements: !!window.MessageManagerElements,
                preview: !!window.MessageManagerPreview,
                storage: !!window.MessageManagerStorage
            });
            
            // Register sub-modules
            this.registerModule('ui', window.MessageManagerUI);
            this.registerModule('elements', window.MessageManagerElements);
            this.registerModule('preview', window.MessageManagerPreview);
            this.registerModule('storage', window.MessageManagerStorage);
            
            // Initialize UI first
            if (window.MessageManagerUI) {
                this.logger.debug('messageManager', 'Initializing UI module...');
                window.MessageManagerUI.initialize();
            } else {
                this.logger.warn('messageManager', 'MessageManagerUI not found');
            }
            
            // Initialize other modules
            if (window.MessageManagerElements) {
                this.logger.debug('messageManager', 'Initializing Elements module...');
                window.MessageManagerElements.initialize();
            } else {
                this.logger.warn('messageManager', 'MessageManagerElements not found');
            }
            
            if (window.MessageManagerPreview) {
                this.logger.debug('messageManager', 'Initializing Preview module...');
                window.MessageManagerPreview.initialize();
            } else {
                this.logger.warn('messageManager', 'MessageManagerPreview not found');
            }
            
            if (window.MessageManagerStorage) {
                this.logger.debug('messageManager', 'Initializing Storage module...');
                window.MessageManagerStorage.initialize();
            } else {
                this.logger.warn('messageManager', 'MessageManagerStorage not found');
            }
            
            this.logger.info('messageManager', 'Message manager core initialized successfully');
        } catch (error) {
            this.logger.error('messageManager', 'Failed to initialize message manager core:', error);
            throw error;
        }
    }

    /**
     * Register a sub-module
     */
    registerModule(name, module) {
        this.modules[name] = module;
        this.logger.debug('messageManager', `Registered module: ${name}`);
    }

    /**
     * Get a sub-module
     */
    getModule(name) {
        return this.modules[name];
    }

    /**
     * Update context (called by orchestrator after initialization)
     */
    updateContext(context) {
        this.context = context;
        this.logger.debug('messageManager', 'Context updated:', context);
        
        // Pass context to sub-modules
        Object.values(this.modules).forEach(module => {
            if (module.updateContext) {
                module.updateContext(context);
            }
        });
    }

    /**
     * Get current state
     */
    getState() {
        return MESSAGE_STATE;
    }

    /**
     * Update state
     */
    updateState(newState) {
        Object.assign(MESSAGE_STATE, newState);
        this.logger.debug('messageManager', 'State updated:', newState);
    }
}

// Create and export the message manager core instance
const messageManagerCore = new MessageManagerCore();

// Register the module
window.registerLLMModule('messageManager', messageManagerCore); 