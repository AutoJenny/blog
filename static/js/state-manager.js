/**
 * Centralized State Manager
 * Replaces localStorage, sessionStorage, and in-memory state
 * Uses database persistence through RESTful APIs
 */

class StateManager {
    constructor(userId = 1) {
        this.userId = userId;
        this.cache = new Map();
        this.cacheTimeout = 30000; // 30 seconds
    }

    // Selection State Management
    async getSelection(pageType, selectionType) {
        const cacheKey = `selection_${pageType}_${selectionType}`;
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        try {
            const response = await fetch(`/api/ui/selection-state?page_type=${pageType}&selection_type=${selectionType}`);
            const data = await response.json();
            
            if (data.selections && data.selections.length > 0) {
                const selection = data.selections[0];
                this.cache.set(cacheKey, selection);
                setTimeout(() => this.cache.delete(cacheKey), this.cacheTimeout);
                return selection;
            }
            return null;
        } catch (error) {
            console.error('Error getting selection:', error);
            return null;
        }
    }

    async setSelection(pageType, selectionType, selectedId, selectedData) {
        try {
            const response = await fetch('/api/ui/selection-state', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    page_type: pageType,
                    selection_type: selectionType,
                    selected_id: selectedId,
                    selected_data: selectedData
                })
            });

            if (response.ok) {
                const cacheKey = `selection_${pageType}_${selectionType}`;
                this.cache.delete(cacheKey);
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error setting selection:', error);
            return false;
        }
    }

    async clearSelection(pageType, selectionType) {
        try {
            const response = await fetch(`/api/ui/selection-state?page_type=${pageType}&selection_type=${selectionType}`, {
                method: 'DELETE'
            });
            return response.ok;
        } catch (error) {
            console.error('Error clearing selection:', error);
            return false;
        }
    }

    // UI State Management
    async getUIState(pageType, stateKey) {
        const cacheKey = `ui_${pageType}_${stateKey}`;
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        try {
            const response = await fetch(`/api/ui/ui-state?page_type=${pageType}&state_key=${stateKey}`);
            const data = await response.json();
            
            if (data.ui_states && data.ui_states.length > 0) {
                const state = data.ui_states[0];
                this.cache.set(cacheKey, state);
                setTimeout(() => this.cache.delete(cacheKey), this.cacheTimeout);
                return state;
            }
            return null;
        } catch (error) {
            console.error('Error getting UI state:', error);
            return null;
        }
    }

    async setUIState(pageType, stateKey, stateData) {
        try {
            const response = await fetch('/api/ui/ui-state', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    page_type: pageType,
                    state_key: stateKey,
                    state_data: stateData
                })
            });

            if (response.ok) {
                const cacheKey = `ui_${pageType}_${stateKey}`;
                this.cache.delete(cacheKey);
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error setting UI state:', error);
            return false;
        }
    }

    // Workflow State Management
    async getWorkflowState(pageType, workflowId) {
        const cacheKey = `workflow_${pageType}_${workflowId}`;
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        try {
            const response = await fetch(`/api/ui/workflow-state?page_type=${pageType}&workflow_id=${workflowId}`);
            const data = await response.json();
            
            if (data.workflow_states && data.workflow_states.length > 0) {
                const state = data.workflow_states[0];
                this.cache.set(cacheKey, state);
                setTimeout(() => this.cache.delete(cacheKey), this.cacheTimeout);
                return state;
            }
            return null;
        } catch (error) {
            console.error('Error getting workflow state:', error);
            return null;
        }
    }

    async setWorkflowState(pageType, workflowId, stateData) {
        try {
            const response = await fetch('/api/ui/workflow-state', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    page_type: pageType,
                    workflow_id: workflowId,
                    state_data: stateData
                })
            });

            if (response.ok) {
                const cacheKey = `workflow_${pageType}_${workflowId}`;
                this.cache.delete(cacheKey);
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error setting workflow state:', error);
            return false;
        }
    }

    // Queue State Management
    async getQueueState(pageType, queueType) {
        const cacheKey = `queue_${pageType}_${queueType}`;
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        try {
            const response = await fetch(`/api/ui/queue-state?page_type=${pageType}&queue_type=${queueType}`);
            const data = await response.json();
            
            if (data.queue_states && data.queue_states.length > 0) {
                const state = data.queue_states[0];
                this.cache.set(cacheKey, state);
                setTimeout(() => this.cache.delete(cacheKey), this.cacheTimeout);
                return state;
            }
            return null;
        } catch (error) {
            console.error('Error getting queue state:', error);
            return null;
        }
    }

    async setQueueState(pageType, queueType, stateData) {
        try {
            const response = await fetch('/api/ui/queue-state', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    page_type: pageType,
                    queue_type: queueType,
                    state_data: stateData
                })
            });

            if (response.ok) {
                const cacheKey = `queue_${pageType}_${queueType}`;
                this.cache.delete(cacheKey);
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error setting queue state:', error);
            return false;
        }
    }

    // Unified State Management
    async getAllState(pageType) {
        try {
            const response = await fetch(`/api/ui/state?page_type=${pageType}`);
            const data = await response.json();
            
            if (data.error) {
                console.error('Error getting all state:', data.message);
                return null;
            }
            
            return data;
        } catch (error) {
            console.error('Error getting all state:', error);
            return null;
        }
    }

    async setAllState(pageType, stateData) {
        try {
            const response = await fetch('/api/ui/state', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    page_type: pageType,
                    ...stateData
                })
            });

            return response.ok;
        } catch (error) {
            console.error('Error setting all state:', error);
            return false;
        }
    }

    // Clear all state for a page
    async clearPageState(pageType) {
        try {
            const response = await fetch(`/api/ui/state?page_type=${pageType}`, {
                method: 'DELETE'
            });
            return response.ok;
        } catch (error) {
            console.error('Error clearing page state:', error);
            return false;
        }
    }

    // Utility methods
    clearCache() {
        this.cache.clear();
    }

    getCacheSize() {
        return this.cache.size;
    }

    // Legacy compatibility methods (for gradual migration)
    async getLegacySelection(key) {
        // Map legacy keys to new system
        const keyMappings = {
            'selectedProduct': { pageType: 'product_post', selectionType: 'product' },
            'selectedBlogPost': { pageType: 'blog_post', selectionType: 'blog_post' },
            'selectedSection': { pageType: 'blog_post', selectionType: 'section' }
        };

        const mapping = keyMappings[key];
        if (mapping) {
            return await this.getSelection(mapping.pageType, mapping.selectionType);
        }
        return null;
    }

    async setLegacySelection(key, data) {
        const keyMappings = {
            'selectedProduct': { pageType: 'product_post', selectionType: 'product' },
            'selectedBlogPost': { pageType: 'blog_post', selectionType: 'blog_post' },
            'selectedSection': { pageType: 'blog_post', selectionType: 'section' }
        };

        const mapping = keyMappings[key];
        if (mapping) {
            return await this.setSelection(mapping.pageType, mapping.selectionType, data.id, data);
        }
        return false;
    }
}

// Global instance
window.stateManager = new StateManager();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StateManager;
}
