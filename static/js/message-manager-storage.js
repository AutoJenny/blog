/**
 * Message Manager Storage Module
 * Handles localStorage persistence
 */

// Message Manager Storage Class
class MessageManagerStorage {
    constructor() {
        this.logger = window.LLM_STATE?.logger || console;
        this.storageKey = 'messageManagerState';
    }

    /**
     * Initialize the storage module
     */
    initialize() {
        try {
            this.logger.info('messageManagerStorage', 'Initializing storage module...');
            
            this.loadSavedState();
            
            this.logger.info('messageManagerStorage', 'Storage module initialized successfully');
        } catch (error) {
            this.logger.error('messageManagerStorage', 'Failed to initialize storage module:', error);
            throw error;
        }
    }

    /**
     * Save element order and states to localStorage
     */
    saveElementOrder() {
        try {
            if (!window.MessageManagerElements) {
                this.logger.warn('messageManagerStorage', 'Elements module not available');
                return;
            }

            const elements = window.MessageManagerElements.getElements();
            const data = {
                elementOrder: elements.map(el => el.id),
                enabledElements: elements.filter(el => el.enabled).map(el => el.id),
                lastSaved: Date.now()
            };
            
            localStorage.setItem(this.storageKey, JSON.stringify(data));
            this.logger.debug('messageManagerStorage', 'Element order saved to localStorage');
        } catch (error) {
            this.logger.error('messageManagerStorage', 'Failed to save element order:', error);
        }
    }

    /**
     * Load element order and states from localStorage
     */
    loadSavedState() {
        try {
            const data = localStorage.getItem(this.storageKey);
            if (!data) {
                this.logger.debug('messageManagerStorage', 'No saved state found');
                return;
            }

            const parsed = JSON.parse(data);
            this.logger.debug('messageManagerStorage', 'Loaded saved state:', parsed);
            
            // Store the data for use by other modules
            this.savedState = parsed;
            
        } catch (error) {
            this.logger.error('messageManagerStorage', 'Failed to load saved state:', error);
            this.savedState = null;
        }
    }

    /**
     * Get saved state
     */
    getSavedState() {
        return this.savedState;
    }

    /**
     * Save configuration
     */
    saveConfiguration(config) {
        try {
            const data = {
                ...config,
                lastSaved: Date.now()
            };
            
            localStorage.setItem(`${this.storageKey}_config`, JSON.stringify(data));
            this.logger.debug('messageManagerStorage', 'Configuration saved');
        } catch (error) {
            this.logger.error('messageManagerStorage', 'Failed to save configuration:', error);
        }
    }

    /**
     * Load configuration
     */
    loadConfiguration() {
        try {
            const data = localStorage.getItem(`${this.storageKey}_config`);
            if (!data) {
                return null;
            }

            const parsed = JSON.parse(data);
            this.logger.debug('messageManagerStorage', 'Configuration loaded');
            return parsed;
        } catch (error) {
            this.logger.error('messageManagerStorage', 'Failed to load configuration:', error);
            return null;
        }
    }

    /**
     * Clear all saved data
     */
    clearAllData() {
        try {
            localStorage.removeItem(this.storageKey);
            localStorage.removeItem(`${this.storageKey}_config`);
            this.savedState = null;
            this.logger.info('messageManagerStorage', 'All saved data cleared');
        } catch (error) {
            this.logger.error('messageManagerStorage', 'Failed to clear data:', error);
        }
    }

    /**
     * Get storage info
     */
    getStorageInfo() {
        try {
            const elementData = localStorage.getItem(this.storageKey);
            const configData = localStorage.getItem(`${this.storageKey}_config`);
            
            return {
                hasElementData: !!elementData,
                hasConfigData: !!configData,
                elementDataSize: elementData ? elementData.length : 0,
                configDataSize: configData ? configData.length : 0
            };
        } catch (error) {
            this.logger.error('messageManagerStorage', 'Failed to get storage info:', error);
            return null;
        }
    }

    /**
     * Export data
     */
    exportData() {
        try {
            const elementData = localStorage.getItem(this.storageKey);
            const configData = localStorage.getItem(`${this.storageKey}_config`);
            
            return {
                elements: elementData ? JSON.parse(elementData) : null,
                config: configData ? JSON.parse(configData) : null,
                exportedAt: Date.now()
            };
        } catch (error) {
            this.logger.error('messageManagerStorage', 'Failed to export data:', error);
            return null;
        }
    }

    /**
     * Import data
     */
    importData(data) {
        try {
            if (data.elements) {
                localStorage.setItem(this.storageKey, JSON.stringify(data.elements));
            }
            
            if (data.config) {
                localStorage.setItem(`${this.storageKey}_config`, JSON.stringify(data.config));
            }
            
            this.logger.info('messageManagerStorage', 'Data imported successfully');
            return true;
        } catch (error) {
            this.logger.error('messageManagerStorage', 'Failed to import data:', error);
            return false;
        }
    }

    /**
     * Update context
     */
    updateContext(context) {
        this.context = context;
        this.logger.debug('messageManagerStorage', 'Context updated:', context);
    }
}

// Create and export the storage module
const messageManagerStorage = new MessageManagerStorage();

// Make it globally available
window.MessageManagerStorage = messageManagerStorage; 