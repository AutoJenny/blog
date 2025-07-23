/**
 * Section Drag and Drop Module
 * Isolated module for reordering workflow sections
 * Does NOT modify existing accordion functionality
 */

class SectionDragDrop {
    constructor() {
        this.container = null;
        this.postId = null;
        this.isInitialized = false;
        this.sectionsById = {};
    }

    /**
     * Initialize drag-and-drop for sections
     * @param {string} containerId - ID of the sections container
     * @param {number} postId - Post ID for API calls
     * @param {Array} sections - Array of section objects (full data)
     */
    init(containerId, postId, sections = []) {
        if (this.isInitialized) {
            console.log('SectionDragDrop already initialized');
            return;
        }

        this.postId = postId;
        this.container = document.getElementById(containerId);
        // Build a map of section data by ID
        this.sectionsById = {};
        for (const s of sections) {
            this.sectionsById[s.id] = { ...s };
        }
        
        if (!this.container) {
            console.warn('Sections container not found:', containerId);
            return;
        }

        // Wait for SortableJS to be available
        this.waitForSortableJS().then(() => {
            this.createSortable();
        }).catch(error => {
            console.error('Failed to initialize drag-and-drop:', error);
        });
    }

    /**
     * Wait for SortableJS to be loaded
     */
    async waitForSortableJS() {
        // Check if SortableJS is already available
        if (window.Sortable) {
            return;
        }

        // Load SortableJS if not available
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js';
            script.onload = () => {
                console.log('SortableJS loaded successfully');
                resolve();
            };
            script.onerror = () => {
                reject(new Error('Failed to load SortableJS'));
            };
            document.head.appendChild(script);
        });
    }

    /**
     * Create Sortable instance
     */
    createSortable() {
        if (!window.Sortable) {
            console.error('SortableJS not available');
            return;
        }

        try {
            new window.Sortable(this.container, {
                animation: 150,
                handle: '.section-drag-handle',
                ghostClass: 'sortable-ghost',
                chosenClass: 'sortable-chosen',
                dragClass: 'sortable-drag',
                onStart: (evt) => {
                    console.log('Drag started');
                    evt.item.classList.add('dragging');
                },
                onEnd: async (evt) => {
                    console.log('Drag ended');
                    evt.item.classList.remove('dragging');
                    await this.updateSectionOrder();
                }
            });
            
            this.isInitialized = true;
            console.log('Section drag-and-drop initialized successfully');
        } catch (error) {
            console.error('Error creating Sortable instance:', error);
        }
    }

    /**
     * Update section order after drag-and-drop
     */
    async updateSectionOrder() {
        if (!this.container || !this.postId) {
            console.error('Container or postId not available');
            return;
        }

        try {
            // Get new order of section IDs
            const newOrder = Array.from(this.container.children).map(child => {
                const sectionId = child.dataset.sectionId;
                if (!sectionId) {
                    console.warn('Section element missing data-section-id');
                    return null;
                }
                return parseInt(sectionId);
            }).filter(id => id !== null);

            console.log('New section order:', newOrder);

            // Update each section's orderIndex and send full data
            for (let i = 0; i < newOrder.length; i++) {
                const sectionId = newOrder[i];
                const section = this.sectionsById[sectionId];
                if (!section) {
                    console.warn(`No section data found for id ${sectionId}`);
                    continue;
                }
                
                // Update the section order in the database
                const response = await fetch(`/api/sections/${sectionId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        orderIndex: i + 1  // section_order is 1-based
                    })
                });

                if (!response.ok) {
                    throw new Error(`Failed to update section ${sectionId}: ${response.statusText}`);
                }
            }

            console.log('Section order updated successfully');
            // Reload the page to reflect new order
            window.location.reload();
        } catch (error) {
            console.error('Error updating section order:', error);
            alert('Failed to save section order: ' + error.message);
        }
    }

    /**
     * Destroy drag-and-drop functionality
     */
    destroy() {
        if (this.container && this.isInitialized) {
            // SortableJS doesn't have a destroy method, but we can remove the instance
            this.isInitialized = false;
            console.log('Section drag-and-drop destroyed');
        }
    }
}

// Initialize drag and drop when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for sections to be rendered
    setTimeout(() => {
        const container = document.getElementById('sections-sortable-container');
        if (container) {
            // Get post ID from URL
            const urlParams = new URLSearchParams(window.location.search);
            const postId = urlParams.get('post_id');
            
            if (postId) {
                // Initialize drag and drop
                window.sectionDragDrop = new SectionDragDrop();
                window.sectionDragDrop.init('sections-sortable-container', postId);
            }
        }
    }, 1000);
}); 