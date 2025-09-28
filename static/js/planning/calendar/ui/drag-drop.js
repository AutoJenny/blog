/**
 * Drag and Drop Module
 * Handles drag and drop functionality
 * 
 * Implemented Classes:
 * - DragDropManager - Main class that handles all drag and drop state and functionality
 * 
 * Implemented Methods:
 * - initialize() - Initialize drag and drop event listeners
 * - handleDragStart() - Handle drag start event
 * - handleDragEnd() - Handle drag end event
 * - handleDragOver() - Handle drag over event
 * - handleDragEnter() - Handle drag enter event
 * - handleDragLeave() - Handle drag leave event
 * - handleDrop() - Handle drop event
 * - moveItemToWeek() - Move item to a different week
 */

import DataLoader from '../api/data-loader.js';
import CacheManager from '../api/cache-manager.js';
import { showNotification } from './calendar-renderer.js';

/**
 * Drag and Drop Manager Class
 * Handles all drag and drop state and functionality
 */
class DragDropManager {
    constructor(dataLoader, cacheManager) {
        this.dataLoader = dataLoader;
        this.cacheManager = cacheManager;
        this.draggedElement = null;
        this.draggedType = null;
        this.draggedId = null;
        this.dragGhost = null;
    }

    /**
     * Initialize drag and drop event listeners
     */
    initialize() {
        // Add drag event listeners to all draggable items
        document.addEventListener('dragstart', this.handleDragStart.bind(this));
        document.addEventListener('dragend', this.handleDragEnd.bind(this));
        document.addEventListener('dragover', this.handleDragOver.bind(this));
        document.addEventListener('drop', this.handleDrop.bind(this));
        document.addEventListener('dragenter', this.handleDragEnter.bind(this));
        document.addEventListener('dragleave', this.handleDragLeave.bind(this));
    }

    /**
     * Handle drag start event
     * @param {DragEvent} e - Drag event
     */
    handleDragStart(e) {
        const item = e.target.closest('.idea-item, .event-item, .schedule-item');
        if (!item) return;
        
        this.draggedElement = item;
        this.draggedType = item.classList.contains('idea-item') ? 'idea' : 
                          item.classList.contains('event-item') ? 'event' : 'schedule';
        this.draggedId = item.dataset.ideaId || item.dataset.eventId || item.dataset.scheduleId;
        
        // Add dragging class
        item.classList.add('dragging');
        
        // Set drag data
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', '');
        
        // Create drag ghost
        this.dragGhost = item.cloneNode(true);
        this.dragGhost.style.opacity = '0.5';
        this.dragGhost.style.position = 'absolute';
        this.dragGhost.style.pointerEvents = 'none';
        this.dragGhost.style.zIndex = '1000';
        document.body.appendChild(this.dragGhost);
        
        // Update ghost position
        e.dataTransfer.setDragImage(this.dragGhost, 0, 0);
    }

    /**
     * Handle drag end event
     * @param {DragEvent} e - Drag event
     */
    handleDragEnd(e) {
        if (this.draggedElement) {
            this.draggedElement.classList.remove('dragging');
        }
        
        // Remove drag ghost
        if (this.dragGhost) {
            document.body.removeChild(this.dragGhost);
            this.dragGhost = null;
        }
        
        // Clear drag state
        this.draggedElement = null;
        this.draggedType = null;
        this.draggedId = null;
        
        // Remove all drag-over classes
        document.querySelectorAll('.drag-over').forEach(el => {
            el.classList.remove('drag-over');
        });
    }

    /**
     * Handle drag over event
     * @param {DragEvent} e - Drag event
     */
    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }

    /**
     * Handle drag enter event
     * @param {DragEvent} e - Drag event
     */
    handleDragEnter(e) {
        const weekCell = e.target.closest('.week-cell');
        if (weekCell && weekCell.querySelector('.week-content')) {
            weekCell.classList.add('drag-over');
        }
    }

    /**
     * Handle drag leave event
     * @param {DragEvent} e - Drag event
     */
    handleDragLeave(e) {
        const weekCell = e.target.closest('.week-cell');
        if (weekCell && !weekCell.contains(e.relatedTarget)) {
            weekCell.classList.remove('drag-over');
        }
    }

    /**
     * Handle drop event
     * @param {DragEvent} e - Drag event
     */
    handleDrop(e) {
        e.preventDefault();
        
        const weekCell = e.target.closest('.week-cell');
        if (!weekCell || !this.draggedElement) return;
        
        const targetWeek = weekCell.getAttribute('data-week');
        if (!targetWeek) return;
        
        // Remove drag-over class
        weekCell.classList.remove('drag-over');
        
        // Move the item
        this.moveItemToWeek(this.draggedType, this.draggedId, parseInt(targetWeek));
    }

    /**
     * Move item to a different week
     * @param {string} itemType - Type of item (idea, event, schedule)
     * @param {string} itemId - ID of the item
     * @param {number} targetWeek - Target week number
     */
    async moveItemToWeek(itemType, itemId, targetWeek) {
        try {
            let result;
            if (itemType === 'idea') {
                result = await this.dataLoader.updateIdeaWeek(itemId, targetWeek);
            } else if (itemType === 'event') {
                result = await this.dataLoader.updateEventWeek(itemId, targetWeek);
            } else if (itemType === 'schedule') {
                result = await this.dataLoader.updateScheduleWeek(itemId, targetWeek);
            }
            
            showNotification(`${itemType.charAt(0).toUpperCase() + itemType.slice(1)} moved to week ${targetWeek}`, 'success');
            // Invalidate cache for this week
            this.cacheManager.invalidateWeek(window.currentYear, window.currentWeekNumber);
            // Reload current week's content
            if (window.loadWeekContent) {
                await window.loadWeekContent(window.currentYear, window.currentWeekNumber);
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification(`Error moving ${itemType}`, 'error');
        }
    }
}

// Export for use in other modules
export { DragDropManager };
