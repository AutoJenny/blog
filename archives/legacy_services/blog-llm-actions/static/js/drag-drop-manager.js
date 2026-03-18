/**
 * Drag Drop Manager Module
 *
 * Responsibilities:
 * - Handle drag and drop functionality for reorderable elements
 * - Manage drag state and visual feedback
 * - Coordinate with element-ordering.js for programmatic reordering
 *
 * Dependencies: logger.js
 * Dependents: element-ordering.js
 *
 * @version 1.0
 */

// Drag drop state
const DRAG_DROP_STATE = {
    // Current drag state
    isDragging: false,
    draggedItem: null,
    draggedContainer: null,
    originalIndex: -1,
    
    // Visual elements
    ghostElement: null,
    placeholder: null,
    dropTarget: null,
    
    // Settings
    settings: {
        animationDuration: 200,
        dragThreshold: 5,
        autoScroll: true
    }
};

/**
 * Drag Drop Manager class
 */
class DragDropManager {
    constructor() {
        this.logger = window.logger;
        this.context = null;
        this.initialized = false;
        this.sortableContainers = new Map();
    }

    /**
     * Initialize the drag drop manager
     */
    async initialize(context) {
        this.logger.trace('dragDropManager', 'initialize', 'enter');
        this.context = context;
        
        try {
            await this.initializeSortableContainers();
            this.setupEventListeners();
            this.createVisualElements();
            
            this.initialized = true;
            this.logger.info('dragDropManager', 'Drag drop manager initialized');
            
        } catch (error) {
            this.logger.error('dragDropManager', 'Failed to initialize drag drop manager:', error);
            throw error;
        }
        
        this.logger.trace('dragDropManager', 'initialize', 'exit');
    }

    /**
     * Initialize sortable containers
     */
    async initializeSortableContainers() {
        this.logger.trace('dragDropManager', 'initializeSortableContainers', 'enter');
        
        const containers = document.querySelectorAll('[data-sortable]');
        this.logger.debug('dragDropManager', `Found ${containers.length} sortable containers`);
        
        for (const container of containers) {
            const containerId = container.dataset.sortable;
            await this.initializeSingleContainer(container);
            this.sortableContainers.set(containerId, container);
        }
        
        this.logger.trace('dragDropManager', 'initializeSortableContainers', 'exit');
    }

    /**
     * Initialize a single sortable container
     */
    async initializeSingleContainer(container) {
        const containerId = container.dataset.sortable;
        const items = container.querySelectorAll('[data-sortable-item]');
        
        this.logger.debug('dragDropManager', `Initializing container ${containerId} with ${items.length} items`);
        
        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            const itemId = item.dataset.sortableItem;
            await this.initializeSortableItem(containerId, item, i);
        }
    }

    /**
     * Initialize a single sortable item
     */
    async initializeSortableItem(containerId, item, index) {
        const itemId = item.dataset.sortableItem;
        
        this.setupItemDragListeners(containerId, item, itemId);
        this.addDragVisualIndicators(item);
        
        this.logger.debug('dragDropManager', `Initialized sortable item ${itemId} in container ${containerId}`);
    }

    /**
     * Setup drag listeners for an item
     */
    setupItemDragListeners(containerId, item, itemId) {
        item.addEventListener('mousedown', (event) => {
            if (event.button === 0) { // Left mouse button only
                this.startDrag(containerId, item, itemId, event);
            }
        });
        
        item.addEventListener('touchstart', (event) => {
            this.startDrag(containerId, item, itemId, event);
        });
    }

    /**
     * Add visual indicators for draggable items
     */
    addDragVisualIndicators(item) {
        item.style.cursor = 'grab';
        item.setAttribute('draggable', 'false'); // We handle drag manually
    }

    /**
     * Start drag operation
     */
    startDrag(containerId, item, itemId, event) {
        this.logger.debug('dragDropManager', `Starting drag for item ${itemId} in container ${containerId}`);
        
        event.preventDefault();
        
        DRAG_DROP_STATE.isDragging = true;
        DRAG_DROP_STATE.draggedItem = item;
        DRAG_DROP_STATE.draggedContainer = containerId;
        DRAG_DROP_STATE.originalIndex = Array.from(item.parentNode.children).indexOf(item);
        
        // Create ghost and placeholder
        this.createGhostElement(item);
        this.createPlaceholder(item);
        
        // Setup global drag listeners
        this.setupGlobalDragListeners(containerId);
        
        this.emitDragEvent('start', { containerId, itemId, originalIndex: DRAG_DROP_STATE.originalIndex });
    }

    /**
     * Create ghost element for drag feedback
     */
    createGhostElement(originalElement) {
        const ghost = originalElement.cloneNode(true);
        ghost.style.position = 'fixed';
        ghost.style.top = '-1000px';
        ghost.style.left = '-1000px';
        ghost.style.opacity = '0.8';
        ghost.style.pointerEvents = 'none';
        ghost.style.zIndex = '10000';
        
        document.body.appendChild(ghost);
        DRAG_DROP_STATE.ghostElement = ghost;
    }

    /**
     * Create placeholder element
     */
    createPlaceholder(originalElement) {
        const placeholder = originalElement.cloneNode(true);
        placeholder.style.opacity = '0.3';
        placeholder.style.backgroundColor = 'var(--llm-purple-light)';
        placeholder.style.border = '2px dashed var(--llm-purple)';
        
        originalElement.parentNode.insertBefore(placeholder, originalElement);
        originalElement.style.display = 'none';
        DRAG_DROP_STATE.placeholder = placeholder;
    }

    /**
     * Setup global drag listeners
     */
    setupGlobalDragListeners(containerId) {
        const handleMove = (event) => this.handleDragMove(event);
        const handleEnd = (event) => this.handleDragEnd(event, containerId);
        
        document.addEventListener('mousemove', handleMove);
        document.addEventListener('mouseup', handleEnd);
        document.addEventListener('touchmove', handleMove);
        document.addEventListener('touchend', handleEnd);
        
        // Store listeners for cleanup
        this.currentDragListeners = { handleMove, handleEnd };
    }

    /**
     * Handle drag move
     */
    handleDragMove(event) {
        if (!DRAG_DROP_STATE.isDragging) return;
        
        event.preventDefault();
        
        const clientX = event.clientX || (event.touches && event.touches[0].clientX);
        const clientY = event.clientY || (event.touches && event.touches[0].clientY);
        
        // Update ghost position
        if (DRAG_DROP_STATE.ghostElement) {
            DRAG_DROP_STATE.ghostElement.style.left = `${clientX + 10}px`;
            DRAG_DROP_STATE.ghostElement.style.top = `${clientY + 10}px`;
        }
        
        // Find drop target
        const dropTarget = this.findDropTarget(clientX, clientY);
        this.updateDropTarget(dropTarget);
    }

    /**
     * Handle drag end
     */
    handleDragEnd(event, containerId) {
        if (!DRAG_DROP_STATE.isDragging) return;
        
        event.preventDefault();
        
        if (DRAG_DROP_STATE.dropTarget) {
            this.performDrop(DRAG_DROP_STATE.dropTarget);
        }
        
        this.cancelDrag();
    }

    /**
     * Find drop target at position
     */
    findDropTarget(clientX, clientY) {
        const container = this.sortableContainers.get(DRAG_DROP_STATE.draggedContainer);
        if (!container) return null;
        
        const item = this.findItemAtPosition(container, clientX, clientY);
        if (item && item !== DRAG_DROP_STATE.draggedItem) {
            return item;
        }
        
        return null;
    }

    /**
     * Find item at position
     */
    findItemAtPosition(container, clientX, clientY) {
        const items = container.querySelectorAll('[data-sortable-item]');
        
        for (const item of items) {
            const rect = item.getBoundingClientRect();
            if (clientX >= rect.left && clientX <= rect.right &&
                clientY >= rect.top && clientY <= rect.bottom) {
                return item;
            }
        }
        
        return null;
    }

    /**
     * Update drop target visual feedback
     */
    updateDropTarget(dropTarget) {
        // Remove previous drop indicators
        this.removeDropIndicators();
        
        if (dropTarget) {
            dropTarget.style.borderTop = '2px solid var(--llm-purple)';
            DRAG_DROP_STATE.dropTarget = dropTarget;
        }
    }

    /**
     * Remove drop indicators
     */
    removeDropIndicators() {
        if (DRAG_DROP_STATE.dropTarget) {
            DRAG_DROP_STATE.dropTarget.style.borderTop = '';
            DRAG_DROP_STATE.dropTarget = null;
        }
    }

    /**
     * Perform drop operation
     */
    performDrop(dropTarget) {
        const containerId = DRAG_DROP_STATE.draggedContainer;
        const itemId = DRAG_DROP_STATE.draggedItem.dataset.sortableItem;
        const newIndex = Array.from(dropTarget.parentNode.children).indexOf(dropTarget);
        
        this.logger.debug('dragDropManager', `Dropping item ${itemId} at index ${newIndex}`);
        
        // Move the item
        dropTarget.parentNode.insertBefore(DRAG_DROP_STATE.draggedItem, dropTarget);
        
        // Update container order
        this.updateContainerItems(containerId);
        
        this.emitDragEvent('drop', { containerId, itemId, newIndex, originalIndex: DRAG_DROP_STATE.originalIndex });
    }

    /**
     * Cancel drag operation
     */
    cancelDrag() {
        this.logger.debug('dragDropManager', 'Canceling drag operation');
        
        // Restore original item
        if (DRAG_DROP_STATE.draggedItem) {
            DRAG_DROP_STATE.draggedItem.style.display = '';
        }
        
        this.cleanupDrag();
        this.emitDragEvent('cancel', {});
    }

    /**
     * Cleanup drag state
     */
    cleanupDrag() {
        // Remove ghost and placeholder
        if (DRAG_DROP_STATE.ghostElement) {
            DRAG_DROP_STATE.ghostElement.remove();
            DRAG_DROP_STATE.ghostElement = null;
        }
        
        if (DRAG_DROP_STATE.placeholder) {
            DRAG_DROP_STATE.placeholder.remove();
            DRAG_DROP_STATE.placeholder = null;
        }
        
        // Remove global listeners
        if (this.currentDragListeners) {
            document.removeEventListener('mousemove', this.currentDragListeners.handleMove);
            document.removeEventListener('mouseup', this.currentDragListeners.handleEnd);
            document.removeEventListener('touchmove', this.currentDragListeners.handleMove);
            document.removeEventListener('touchend', this.currentDragListeners.handleEnd);
            this.currentDragListeners = null;
        }
        
        // Reset state
        DRAG_DROP_STATE.isDragging = false;
        DRAG_DROP_STATE.draggedItem = null;
        DRAG_DROP_STATE.draggedContainer = null;
        DRAG_DROP_STATE.originalIndex = -1;
        this.removeDropIndicators();
    }

    /**
     * Update container items after drag
     */
    updateContainerItems(containerId) {
        const container = this.sortableContainers.get(containerId);
        if (!container) return;
        
        const items = Array.from(container.querySelectorAll('[data-sortable-item]'));
        const order = items.map(item => item.dataset.sortableItem);
        
        this.logger.debug('dragDropManager', `Updated container ${containerId} order:`, order);
    }

    /**
     * Create visual elements
     */
    createVisualElements() {
        // Add CSS for drag feedback
        const style = document.createElement('style');
        style.textContent = `
            [data-sortable-item] {
                transition: transform 0.2s ease;
            }
            [data-sortable-item]:hover {
                transform: translateY(-1px);
            }
            .drag-ghost {
                pointer-events: none;
                opacity: 0.8;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Emit drag event
     */
    emitDragEvent(type, data) {
        const event = new CustomEvent('dragDropEvent', {
            detail: { type, data }
        });
        document.dispatchEvent(event);
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Listen for external drag events
        document.addEventListener('dragDropEvent', (event) => {
            this.logger.debug('dragDropManager', 'Received drag event:', event.detail);
        });
    }

    /**
     * Start drag programmatically
     */
    startDragProgrammatically(containerId, itemId) {
        const container = this.sortableContainers.get(containerId);
        if (!container) {
            this.logger.warn('dragDropManager', `Container ${containerId} not found`);
            return;
        }
        
        const item = container.querySelector(`[data-sortable-item="${itemId}"]`);
        if (!item) {
            this.logger.warn('dragDropManager', `Item ${itemId} not found in container ${containerId}`);
            return;
        }
        
        this.startDrag(containerId, item, itemId, { preventDefault: () => {} });
    }

    /**
     * Update settings
     */
    updateSettings(newSettings) {
        Object.assign(DRAG_DROP_STATE.settings, newSettings);
        this.logger.debug('dragDropManager', 'Updated settings:', DRAG_DROP_STATE.settings);
    }

    /**
     * Get current state
     */
    getState() {
        return { ...DRAG_DROP_STATE };
    }

    /**
     * Get container order
     */
    getContainerOrder(containerId) {
        const container = this.sortableContainers.get(containerId);
        if (!container) return [];
        
        const items = Array.from(container.querySelectorAll('[data-sortable-item]'));
        return items.map(item => item.dataset.sortableItem);
    }

    /**
     * Reset container order
     */
    resetContainerOrder(containerId) {
        this.logger.debug('dragDropManager', `Resetting order for container ${containerId}`);
        // Implementation would depend on original order storage
    }

    /**
     * Cleanup
     */
    destroy() {
        this.logger.info('dragDropManager', 'Destroying drag drop manager');
        this.cleanupDrag();
        this.initialized = false;
    }
}

// Create and export global instance
const dragDropManager = new DragDropManager();
window.dragDropManager = dragDropManager;
window.DRAG_DROP_STATE = DRAG_DROP_STATE;

// Register with LLM module system
if (window.registerLLMModule) {
    window.registerLLMModule('dragDropManager', dragDropManager);
}

// Log initialization
if (window.logger) {
    window.logger.info('dragDropManager', 'Drag Drop Manager Module loaded');
} 