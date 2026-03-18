/**
 * Element Ordering Module
 *
 * Responsibilities:
 * - Handle element ordering operations (move up/down, reorder)
 * - Coordinate with drag-drop-manager
 * - Provide ordering API for other modules
 * - Manage ordering state and persistence
 *
 * Dependencies: logger.js, drag-drop-manager.js
 * Dependents: preview-manager.js
 *
 * @version 1.0
 */

// Element ordering state
const ELEMENT_ORDERING_STATE = {
    // Ordering operations
    isReordering: false,
    currentOperation: null,
    
    // Orderable containers
    orderableContainers: {},
    
    // Order history
    orderHistory: [],
    maxHistorySize: 10,
    
    // Settings
    settings: {
        enableAnimations: true,
        animationDuration: 300,
        enableUndo: true,
        autoSave: true,
        saveDelay: 1000
    },
    
    // UI state
    initialized: false
};

/**
 * Element Ordering Manager class
 */
class ElementOrderingManager {
    constructor() {
        this.logger = window.logger;
        this.context = null;
        this.initialized = false;
        this.saveTimeout = null;
    }

    /**
     * Initialize the element ordering manager
     */
    async initialize(context) {
        this.logger.trace('elementOrderingManager', 'initialize', 'enter');
        this.context = context;
        
        try {
            // Wait for drag drop manager
            await this.waitForDragDropManager();
            
            // Initialize orderable containers
            await this.initializeOrderableContainers();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Create ordering controls
            this.createOrderingControls();
            
            this.initialized = true;
            ELEMENT_ORDERING_STATE.initialized = true;
            
            this.logger.info('elementOrderingManager', 'Element ordering manager initialized');
            
        } catch (error) {
            this.logger.error('elementOrderingManager', 'Failed to initialize element ordering manager:', error);
            throw error;
        }
        
        this.logger.trace('elementOrderingManager', 'initialize', 'exit');
    }

    /**
     * Wait for drag drop manager to be ready
     */
    async waitForDragDropManager() {
        let attempts = 0;
        const maxAttempts = 50; // 5 seconds
        
        while (!window.dragDropManager?.initialized && attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        if (!window.dragDropManager?.initialized) {
            throw new Error('Drag drop manager not available');
        }
        
        this.logger.debug('elementOrderingManager', 'Drag drop manager ready');
    }

    /**
     * Initialize orderable containers
     */
    async initializeOrderableContainers() {
        this.logger.trace('elementOrderingManager', 'initializeOrderableContainers', 'enter');
        
        // Find all orderable containers
        const containers = document.querySelectorAll('.orderable-container, [data-orderable]');
        this.logger.debug('elementOrderingManager', `Found ${containers.length} orderable containers`);
        
        for (const container of containers) {
            await this.initializeSingleContainer(container);
        }
        
        this.logger.trace('elementOrderingManager', 'initializeOrderableContainers', 'exit');
    }

    /**
     * Initialize a single orderable container
     */
    async initializeSingleContainer(container) {
        const containerId = container.id || container.getAttribute('data-orderable');
        const orderableItems = container.querySelectorAll('.orderable-item, [data-orderable-item]');
        
        this.logger.debug('elementOrderingManager', `Initializing container: ${containerId} with ${orderableItems.length} items`);
        
        // Store container reference
        ELEMENT_ORDERING_STATE.orderableContainers[containerId] = {
            element: container,
            items: [],
            originalOrder: [],
            currentOrder: []
        };
        
        // Initialize orderable items
        for (let i = 0; i < orderableItems.length; i++) {
            const item = orderableItems[i];
            await this.initializeOrderableItem(containerId, item, i);
        }
        
        // Store original and current order
        const itemIds = Array.from(orderableItems).map(item => 
            item.getAttribute('data-item-id') || item.id
        );
        ELEMENT_ORDERING_STATE.orderableContainers[containerId].originalOrder = [...itemIds];
        ELEMENT_ORDERING_STATE.orderableContainers[containerId].currentOrder = [...itemIds];
        
        // Add ordering controls to container
        this.addOrderingControls(container, containerId);
    }

    /**
     * Initialize a single orderable item
     */
    async initializeOrderableItem(containerId, item, index) {
        const itemId = item.id || item.getAttribute('data-item-id') || `item-${index}`;
        
        this.logger.debug('elementOrderingManager', `Initializing orderable item: ${itemId} in container ${containerId}`);
        
        // Store item reference
        ELEMENT_ORDERING_STATE.orderableContainers[containerId].items.push({
            element: item,
            id: itemId,
            index: index
        });
        
        // Add ordering controls to item
        this.addItemOrderingControls(item, containerId, itemId, index);
        
        // Add visual indicators
        this.addOrderingVisualIndicators(item);
    }

    /**
     * Add ordering controls to container
     */
    addOrderingControls(container, containerId) {
        // Create container controls
        const controls = document.createElement('div');
        controls.className = 'ordering-controls';
        controls.setAttribute('data-container-id', containerId);
        
        controls.innerHTML = `
            <button class="btn btn-sm btn-outline-secondary move-all-top" title="Move all to top">
                <i class="fas fa-arrow-up"></i> All Top
            </button>
            <button class="btn btn-sm btn-outline-secondary move-all-bottom" title="Move all to bottom">
                <i class="fas fa-arrow-down"></i> All Bottom
            </button>
            <button class="btn btn-sm btn-outline-secondary reset-order" title="Reset to original order">
                <i class="fas fa-undo"></i> Reset
            </button>
            <button class="btn btn-sm btn-outline-secondary undo-order" title="Undo last change">
                <i class="fas fa-undo-alt"></i> Undo
            </button>
        `;
        
        // Insert controls before container
        container.parentNode.insertBefore(controls, container);
        
        // Set up event listeners
        this.setupContainerControlListeners(controls, containerId);
    }

    /**
     * Add ordering controls to item
     */
    addItemOrderingControls(item, containerId, itemId, index) {
        // Create item controls
        const controls = document.createElement('div');
        controls.className = 'item-ordering-controls';
        controls.setAttribute('data-item-id', itemId);
        
        controls.innerHTML = `
            <button class="btn btn-sm btn-outline-primary move-up" title="Move up">
                <i class="fas fa-chevron-up"></i>
            </button>
            <button class="btn btn-sm btn-outline-primary move-down" title="Move down">
                <i class="fas fa-chevron-down"></i>
            </button>
            <button class="btn btn-sm btn-outline-primary move-top" title="Move to top">
                <i class="fas fa-arrow-up"></i>
            </button>
            <button class="btn btn-sm btn-outline-primary move-bottom" title="Move to bottom">
                <i class="fas fa-arrow-down"></i>
            </button>
        `;
        
        // Insert controls into item
        item.appendChild(controls);
        
        // Set up event listeners
        this.setupItemControlListeners(controls, containerId, itemId, index);
    }

    /**
     * Add ordering visual indicators
     */
    addOrderingVisualIndicators(item) {
        // Add orderable class
        item.classList.add('orderable-item');
        
        // Add position indicator
        const indicator = document.createElement('div');
        indicator.className = 'position-indicator';
        indicator.innerHTML = '<span class="position-number"></span>';
        item.appendChild(indicator);
    }

    /**
     * Set up container control listeners
     */
    setupContainerControlListeners(controls, containerId) {
        // Move all to top
        controls.querySelector('.move-all-top').addEventListener('click', () => {
            this.moveAllToTop(containerId);
        });
        
        // Move all to bottom
        controls.querySelector('.move-all-bottom').addEventListener('click', () => {
            this.moveAllToBottom(containerId);
        });
        
        // Reset order
        controls.querySelector('.reset-order').addEventListener('click', () => {
            this.resetOrder(containerId);
        });
        
        // Undo order
        controls.querySelector('.undo-order').addEventListener('click', () => {
            this.undoOrder(containerId);
        });
    }

    /**
     * Set up item control listeners
     */
    setupItemControlListeners(controls, containerId, itemId, index) {
        // Move up
        controls.querySelector('.move-up').addEventListener('click', () => {
            this.moveItemUp(containerId, itemId);
        });
        
        // Move down
        controls.querySelector('.move-down').addEventListener('click', () => {
            this.moveItemDown(containerId, itemId);
        });
        
        // Move to top
        controls.querySelector('.move-top').addEventListener('click', () => {
            this.moveItemToTop(containerId, itemId);
        });
        
        // Move to bottom
        controls.querySelector('.move-bottom').addEventListener('click', () => {
            this.moveItemToBottom(containerId, itemId);
        });
    }

    /**
     * Move item up
     */
    moveItemUp(containerId, itemId) {
        this.logger.debug('elementOrderingManager', `Moving item ${itemId} up in container ${containerId}`);
        
        const container = ELEMENT_ORDERING_STATE.orderableContainers[containerId];
        if (!container) return;
        
        const currentIndex = container.currentOrder.indexOf(itemId);
        if (currentIndex <= 0) return; // Already at top
        
        // Save current state to history
        this.saveToHistory(containerId, 'moveUp', { itemId, fromIndex: currentIndex, toIndex: currentIndex - 1 });
        
        // Update order
        const newOrder = [...container.currentOrder];
        const item = newOrder.splice(currentIndex, 1)[0];
        newOrder.splice(currentIndex - 1, 0, item);
        container.currentOrder = newOrder;
        
        // Update DOM
        this.updateContainerOrder(containerId, newOrder);
        
        // Emit order change event
        this.emitOrderChangeEvent(containerId, 'moveUp', { itemId, fromIndex: currentIndex, toIndex: currentIndex - 1 });
    }

    /**
     * Move item down
     */
    moveItemDown(containerId, itemId) {
        this.logger.debug('elementOrderingManager', `Moving item ${itemId} down in container ${containerId}`);
        
        const container = ELEMENT_ORDERING_STATE.orderableContainers[containerId];
        if (!container) return;
        
        const currentIndex = container.currentOrder.indexOf(itemId);
        if (currentIndex >= container.currentOrder.length - 1) return; // Already at bottom
        
        // Save current state to history
        this.saveToHistory(containerId, 'moveDown', { itemId, fromIndex: currentIndex, toIndex: currentIndex + 1 });
        
        // Update order
        const newOrder = [...container.currentOrder];
        const item = newOrder.splice(currentIndex, 1)[0];
        newOrder.splice(currentIndex + 1, 0, item);
        container.currentOrder = newOrder;
        
        // Update DOM
        this.updateContainerOrder(containerId, newOrder);
        
        // Emit order change event
        this.emitOrderChangeEvent(containerId, 'moveDown', { itemId, fromIndex: currentIndex, toIndex: currentIndex + 1 });
    }

    /**
     * Move item to top
     */
    moveItemToTop(containerId, itemId) {
        this.logger.debug('elementOrderingManager', `Moving item ${itemId} to top in container ${containerId}`);
        
        const container = ELEMENT_ORDERING_STATE.orderableContainers[containerId];
        if (!container) return;
        
        const currentIndex = container.currentOrder.indexOf(itemId);
        if (currentIndex <= 0) return; // Already at top
        
        // Save current state to history
        this.saveToHistory(containerId, 'moveToTop', { itemId, fromIndex: currentIndex, toIndex: 0 });
        
        // Update order
        const newOrder = [...container.currentOrder];
        const item = newOrder.splice(currentIndex, 1)[0];
        newOrder.unshift(item);
        container.currentOrder = newOrder;
        
        // Update DOM
        this.updateContainerOrder(containerId, newOrder);
        
        // Emit order change event
        this.emitOrderChangeEvent(containerId, 'moveToTop', { itemId, fromIndex: currentIndex, toIndex: 0 });
    }

    /**
     * Move item to bottom
     */
    moveItemToBottom(containerId, itemId) {
        this.logger.debug('elementOrderingManager', `Moving item ${itemId} to bottom in container ${containerId}`);
        
        const container = ELEMENT_ORDERING_STATE.orderableContainers[containerId];
        if (!container) return;
        
        const currentIndex = container.currentOrder.indexOf(itemId);
        if (currentIndex >= container.currentOrder.length - 1) return; // Already at bottom
        
        // Save current state to history
        this.saveToHistory(containerId, 'moveToBottom', { itemId, fromIndex: currentIndex, toIndex: container.currentOrder.length - 1 });
        
        // Update order
        const newOrder = [...container.currentOrder];
        const item = newOrder.splice(currentIndex, 1)[0];
        newOrder.push(item);
        container.currentOrder = newOrder;
        
        // Update DOM
        this.updateContainerOrder(containerId, newOrder);
        
        // Emit order change event
        this.emitOrderChangeEvent(containerId, 'moveToBottom', { itemId, fromIndex: currentIndex, toIndex: container.currentOrder.length - 1 });
    }

    /**
     * Move all items to top
     */
    moveAllToTop(containerId) {
        this.logger.debug('elementOrderingManager', `Moving all items to top in container ${containerId}`);
        
        const container = ELEMENT_ORDERING_STATE.orderableContainers[containerId];
        if (!container) return;
        
        // Save current state to history
        this.saveToHistory(containerId, 'moveAllToTop', { fromOrder: [...container.currentOrder] });
        
        // Update order (reverse to move all to top)
        const newOrder = [...container.currentOrder].reverse();
        container.currentOrder = newOrder;
        
        // Update DOM
        this.updateContainerOrder(containerId, newOrder);
        
        // Emit order change event
        this.emitOrderChangeEvent(containerId, 'moveAllToTop', { newOrder });
    }

    /**
     * Move all items to bottom
     */
    moveAllToBottom(containerId) {
        this.logger.debug('elementOrderingManager', `Moving all items to bottom in container ${containerId}`);
        
        const container = ELEMENT_ORDERING_STATE.orderableContainers[containerId];
        if (!container) return;
        
        // Save current state to history
        this.saveToHistory(containerId, 'moveAllToBottom', { fromOrder: [...container.currentOrder] });
        
        // Update order (reverse to move all to bottom)
        const newOrder = [...container.currentOrder].reverse();
        container.currentOrder = newOrder;
        
        // Update DOM
        this.updateContainerOrder(containerId, newOrder);
        
        // Emit order change event
        this.emitOrderChangeEvent(containerId, 'moveAllToBottom', { newOrder });
    }

    /**
     * Reset order to original
     */
    resetOrder(containerId) {
        this.logger.debug('elementOrderingManager', `Resetting order in container ${containerId}`);
        
        const container = ELEMENT_ORDERING_STATE.orderableContainers[containerId];
        if (!container) return;
        
        // Save current state to history
        this.saveToHistory(containerId, 'resetOrder', { fromOrder: [...container.currentOrder] });
        
        // Restore original order
        const newOrder = [...container.originalOrder];
        container.currentOrder = newOrder;
        
        // Update DOM
        this.updateContainerOrder(containerId, newOrder);
        
        // Emit order change event
        this.emitOrderChangeEvent(containerId, 'resetOrder', { newOrder });
    }

    /**
     * Undo last order change
     */
    undoOrder(containerId) {
        this.logger.debug('elementOrderingManager', `Undoing last order change in container ${containerId}`);
        
        const history = ELEMENT_ORDERING_STATE.orderHistory.filter(h => h.containerId === containerId);
        if (history.length === 0) {
            this.logger.warn('elementOrderingManager', 'No history to undo');
            return;
        }
        
        const lastChange = history[history.length - 1];
        const container = ELEMENT_ORDERING_STATE.orderableContainers[containerId];
        if (!container) return;
        
        // Restore previous order
        container.currentOrder = [...lastChange.previousOrder];
        
        // Update DOM
        this.updateContainerOrder(containerId, container.currentOrder);
        
        // Remove from history
        ELEMENT_ORDERING_STATE.orderHistory = ELEMENT_ORDERING_STATE.orderHistory.filter(h => h !== lastChange);
        
        // Emit order change event
        this.emitOrderChangeEvent(containerId, 'undo', { newOrder: container.currentOrder });
    }

    /**
     * Update container order in DOM
     */
    updateContainerOrder(containerId, newOrder) {
        const container = ELEMENT_ORDERING_STATE.orderableContainers[containerId];
        if (!container) return;
        
        ELEMENT_ORDERING_STATE.isReordering = true;
        
        // Reorder DOM elements
        newOrder.forEach((itemId, index) => {
            const item = container.items.find(item => item.id === itemId);
            if (item) {
                // Move element to correct position
                container.element.appendChild(item.element);
                
                // Update position indicator
                const indicator = item.element.querySelector('.position-indicator .position-number');
                if (indicator) {
                    indicator.textContent = index + 1;
                }
                
                // Update item index
                item.index = index;
            }
        });
        
        // Update drag drop manager
        if (window.dragDropManager) {
            window.dragDropManager.updateContainerItems(containerId);
        }
        
        // Auto-save if enabled
        if (ELEMENT_ORDERING_STATE.settings.autoSave) {
            this.scheduleAutoSave(containerId);
        }
        
        ELEMENT_ORDERING_STATE.isReordering = false;
    }

    /**
     * Save to history
     */
    saveToHistory(containerId, operation, data) {
        const container = ELEMENT_ORDERING_STATE.orderableContainers[containerId];
        if (!container) return;
        
        const historyEntry = {
            containerId: containerId,
            operation: operation,
            data: data,
            previousOrder: [...container.currentOrder],
            timestamp: Date.now()
        };
        
        ELEMENT_ORDERING_STATE.orderHistory.push(historyEntry);
        
        // Limit history size
        if (ELEMENT_ORDERING_STATE.orderHistory.length > ELEMENT_ORDERING_STATE.maxHistorySize) {
            ELEMENT_ORDERING_STATE.orderHistory.shift();
        }
        
        this.logger.debug('elementOrderingManager', 'Saved to history:', historyEntry);
    }

    /**
     * Schedule auto save
     */
    scheduleAutoSave(containerId) {
        // Clear existing timeout
        if (this.saveTimeout) {
            clearTimeout(this.saveTimeout);
        }
        
        // Schedule new save
        this.saveTimeout = setTimeout(() => {
            this.saveOrderToBackend(containerId);
        }, ELEMENT_ORDERING_STATE.settings.saveDelay);
    }

    /**
     * Save order to backend
     */
    async saveOrderToBackend(containerId) {
        const container = ELEMENT_ORDERING_STATE.orderableContainers[containerId];
        if (!container) return;
        
        try {
            this.logger.debug('elementOrderingManager', `Saving order to backend for container ${containerId}`);
            
            // Emit save event for other modules to handle
            const event = new CustomEvent('saveOrder', {
                detail: {
                    containerId: containerId,
                    order: container.currentOrder,
                    originalOrder: container.originalOrder
                }
            });
            document.dispatchEvent(event);
            
        } catch (error) {
            this.logger.error('elementOrderingManager', 'Failed to save order to backend:', error);
        }
    }

    /**
     * Create ordering controls
     */
    createOrderingControls() {
        // Add CSS for ordering controls
        const style = document.createElement('style');
        style.textContent = `
            .ordering-controls {
                margin-bottom: 10px;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #dee2e6;
            }
            .ordering-controls button {
                margin-right: 5px;
            }
            .item-ordering-controls {
                position: absolute;
                top: 5px;
                right: 5px;
                display: flex;
                gap: 2px;
                opacity: 0;
                transition: opacity 0.2s ease;
            }
            .orderable-item:hover .item-ordering-controls {
                opacity: 1;
            }
            .item-ordering-controls button {
                padding: 2px 4px;
                font-size: 10px;
            }
            .position-indicator {
                position: absolute;
                top: 5px;
                left: 5px;
                background: #007bff;
                color: white;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 10px;
                font-weight: bold;
            }
            .orderable-item {
                position: relative;
                transition: transform 0.2s ease;
            }
            .orderable-item.reordering {
                transform: scale(1.02);
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Emit order change event
     */
    emitOrderChangeEvent(containerId, operation, data) {
        const event = new CustomEvent('orderChange', {
            detail: {
                containerId: containerId,
                operation: operation,
                data: data,
                timestamp: Date.now()
            }
        });
        document.dispatchEvent(event);
        
        this.logger.debug('elementOrderingManager', `Order change event emitted: ${operation}`, data);
    }

    /**
     * Set up global event listeners
     */
    setupEventListeners() {
        // Listen for drag drop events
        document.addEventListener('dragDropEvent', (event) => {
            const { type, data } = event.detail;
            
            if (type === 'drop') {
                this.handleDragDropReorder(data);
            }
        });
        
        // Listen for external order requests
        document.addEventListener('reorderItems', (event) => {
            const { containerId, newOrder } = event.detail;
            this.reorderItems(containerId, newOrder);
        });
        
        // Listen for settings changes
        document.addEventListener('updateOrderingSettings', (event) => {
            const { settings } = event.detail;
            this.updateSettings(settings);
        });
    }

    /**
     * Handle drag drop reorder
     */
    handleDragDropReorder(data) {
        const { containerId, fromIndex, toIndex } = data;
        
        this.logger.debug('elementOrderingManager', 'Handling drag drop reorder:', data);
        
        // Update our internal order
        const container = ELEMENT_ORDERING_STATE.orderableContainers[containerId];
        if (!container) return;
        
        // Get current order from drag drop manager
        const newOrder = window.dragDropManager.getContainerOrder(containerId);
        container.currentOrder = newOrder;
        
        // Save to history
        this.saveToHistory(containerId, 'dragDrop', { fromIndex, toIndex });
        
        // Emit order change event
        this.emitOrderChangeEvent(containerId, 'dragDrop', { fromIndex, toIndex, newOrder });
    }

    /**
     * Reorder items programmatically
     */
    reorderItems(containerId, newOrder) {
        this.logger.debug('elementOrderingManager', `Reordering items in container ${containerId}:`, newOrder);
        
        const container = ELEMENT_ORDERING_STATE.orderableContainers[containerId];
        if (!container) return;
        
        // Save current state to history
        this.saveToHistory(containerId, 'programmaticReorder', { fromOrder: [...container.currentOrder] });
        
        // Update order
        container.currentOrder = [...newOrder];
        
        // Update DOM
        this.updateContainerOrder(containerId, newOrder);
        
        // Emit order change event
        this.emitOrderChangeEvent(containerId, 'programmaticReorder', { newOrder });
    }

    /**
     * Update settings
     */
    updateSettings(newSettings) {
        ELEMENT_ORDERING_STATE.settings = { ...ELEMENT_ORDERING_STATE.settings, ...newSettings };
        this.logger.debug('elementOrderingManager', 'Settings updated:', ELEMENT_ORDERING_STATE.settings);
    }

    /**
     * Get current state
     */
    getState() {
        return { ...ELEMENT_ORDERING_STATE };
    }

    /**
     * Get container order
     */
    getContainerOrder(containerId) {
        const container = ELEMENT_ORDERING_STATE.orderableContainers[containerId];
        if (!container) return [];
        
        return [...container.currentOrder];
    }

    /**
     * Get original container order
     */
    getOriginalContainerOrder(containerId) {
        const container = ELEMENT_ORDERING_STATE.orderableContainers[containerId];
        if (!container) return [];
        
        return [...container.originalOrder];
    }

    /**
     * Check if order has changed
     */
    hasOrderChanged(containerId) {
        const container = ELEMENT_ORDERING_STATE.orderableContainers[containerId];
        if (!container) return false;
        
        return JSON.stringify(container.currentOrder) !== JSON.stringify(container.originalOrder);
    }

    /**
     * Get order history
     */
    getOrderHistory(containerId = null) {
        if (containerId) {
            return ELEMENT_ORDERING_STATE.orderHistory.filter(h => h.containerId === containerId);
        }
        return [...ELEMENT_ORDERING_STATE.orderHistory];
    }

    /**
     * Clear order history
     */
    clearOrderHistory(containerId = null) {
        if (containerId) {
            ELEMENT_ORDERING_STATE.orderHistory = ELEMENT_ORDERING_STATE.orderHistory.filter(h => h.containerId !== containerId);
        } else {
            ELEMENT_ORDERING_STATE.orderHistory = [];
        }
        
        this.logger.debug('elementOrderingManager', 'Order history cleared');
    }

    /**
     * Cleanup
     */
    destroy() {
        this.logger.info('elementOrderingManager', 'Destroying element ordering manager');
        
        // Clear save timeout
        if (this.saveTimeout) {
            clearTimeout(this.saveTimeout);
        }
        
        this.initialized = false;
        ELEMENT_ORDERING_STATE.initialized = false;
    }
}

// Create and export global instance
const elementOrderingManager = new ElementOrderingManager();
window.elementOrderingManager = elementOrderingManager;
window.ELEMENT_ORDERING_STATE = ELEMENT_ORDERING_STATE;

// Register with LLM module system
if (window.registerLLMModule) {
    window.registerLLMModule('elementOrderingManager', elementOrderingManager);
}

// Log initialization
if (window.logger) {
    window.logger.info('elementOrderingManager', 'Element Ordering Manager Module loaded');
} 