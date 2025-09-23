/**
 * Queue Manager - Shared functionality for posting queue display
 * Handles loading, filtering, and rendering of queue data across different page types
 */

class QueueManager {
    constructor() {
        this.queueData = [];
        this.pageType = this.detectPageType();
        this.init();
    }

    /**
     * Detect page type from URL path
     */
    detectPageType() {
        const path = window.location.pathname;
        if (path.includes('/product_post')) {
            return 'product';
        } else if (path.includes('/blog_post')) {
            return 'blog_post';
        }
        return 'all'; // Default to showing all
    }

    /**
     * Initialize the queue manager
     */
    init() {
        console.log(`Initializing queue manager for page type: ${this.pageType}`);
        this.setupAccordion();
        this.setupEventListeners();
        this.loadQueueData();
    }

    /**
     * Setup accordion functionality
     */
    setupAccordion() {
        // Set initial state for posting queue accordion
        const postingQueueContent = document.getElementById('posting-queue-content');
        const postingQueueChevron = document.getElementById('posting-queue-chevron');
        
        if (postingQueueContent && postingQueueChevron) {
            postingQueueContent.classList.add('active');
            postingQueueChevron.classList.add('rotated');
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Add 10 Items button
        const add10ItemsBtn = document.getElementById('add-10-items-btn');
        if (add10ItemsBtn) {
            add10ItemsBtn.addEventListener('click', () => this.add10Items());
        }
    }

    /**
     * Load queue data from API
     */
    async loadQueueData() {
        console.log(`Loading queue data for ${this.pageType} posts...`);
        try {
            const response = await fetch('/launchpad/api/queue');
            const data = await response.json();
            
            console.log('API response:', data);
            
            if (data.success) {
                // Filter data based on page type
                this.queueData = this.filterQueueData(data.items);
                console.log('Filtered queue data:', this.queueData);
                this.renderQueue();
                this.updateQueueCount();
            } else {
                console.error('Error loading queue:', data.error);
                this.showEmptyQueue();
            }
        } catch (error) {
            console.error('Error loading queue:', error);
            this.showEmptyQueue();
        }
    }

    /**
     * Filter queue data based on page type
     */
    filterQueueData(items) {
        if (this.pageType === 'all') {
            return items;
        }
        return items.filter(item => item.content_type === this.pageType);
    }

    /**
     * Render queue table
     */
    renderQueue() {
        const queueTableContainer = document.getElementById('queue-table-container');
        const emptyQueue = document.getElementById('empty-queue');
        const queueTableBody = document.getElementById('queue-table-body');
        
        if (this.queueData.length === 0) {
            this.showEmptyQueue();
            return;
        }
        
        emptyQueue.style.display = 'none';
        queueTableContainer.style.display = 'block';
        
        let html = '';
        this.queueData.forEach(item => {
            html += this.renderQueueItem(item);
        });
        
        queueTableBody.innerHTML = html;
    }

    /**
     * Render individual queue item based on content type
     */
    renderQueueItem(item) {
        const date = new Date(item.scheduled_timestamp || item.created_at);
        const dateStr = date.toLocaleDateString();
        const timeStr = date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        if (item.content_type === 'product') {
            return this.renderProductItem(item, dateStr, timeStr);
        } else {
            return this.renderBlogItem(item, dateStr, timeStr);
        }
    }

    /**
     * Render product item
     */
    renderProductItem(item, dateStr, timeStr) {
        // Product thumbnail
        let thumbnail = '';
        if (item.product_image) {
            thumbnail = `<img src="${item.product_image}" alt="Product thumbnail" style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px;" onerror="this.style.display='none'">`;
        } else {
            thumbnail = '<div style="width: 60px; height: 60px; background: #334155; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 0.8rem;">No img</div>';
        }
        
        return `
            <tr style="border-bottom: 1px solid #374151;">
                <td style="padding: 15px; vertical-align: top;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        ${thumbnail}
                        <div>
                            <div style="font-weight: 600; color: #f1f5f9; margin-bottom: 5px;">${dateStr}</div>
                            <div style="color: #94a3b8; font-size: 0.9rem;">${timeStr}</div>
                        </div>
                    </div>
                </td>
                <td style="padding: 15px; vertical-align: top;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="max-width: 400px; flex: 1;">
                            <div style="font-weight: 600; color: #f1f5f9; margin-bottom: 8px; font-size: 1.1rem;">
                                ${item.product_name || 'Unknown Product'}
                            </div>
                            <div style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 8px;">
                                SKU: ${item.product_sku || 'N/A'} | Price: $${item.product_price || '0.00'}
                            </div>
                            <div style="color: #e0e0e0; font-size: 0.95rem; line-height: 1.4;">
                                ${item.generated_content ? item.generated_content.substring(0, 200) + (item.generated_content.length > 200 ? '...' : '') : 'No content'}
                            </div>
                        </div>
                        <button onclick="queueManager.deleteQueueItem(${item.id})" 
                                style="background: #ef4444; border: none; border-radius: 4px; padding: 8px 12px; color: white; cursor: pointer; font-size: 0.8rem; margin-left: 15px; flex-shrink: 0;"
                                title="Delete this item">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    /**
     * Render blog item
     */
    renderBlogItem(item, dateStr, timeStr) {
        // Blog post thumbnail
        let thumbnail = '';
        if (item.post_title) {
            thumbnail = `<div style="width: 60px; height: 60px; background: #3b82f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-size: 0.8rem; font-weight: bold;">B</div>`;
        } else {
            thumbnail = '<div style="width: 60px; height: 60px; background: #334155; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 0.8rem;">B</div>';
        }
        
        return `
            <tr style="border-bottom: 1px solid #374151;">
                <td style="padding: 15px; vertical-align: top;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        ${thumbnail}
                        <div>
                            <div style="font-weight: 600; color: #f1f5f9; margin-bottom: 5px;">${dateStr}</div>
                            <div style="color: #94a3b8; font-size: 0.9rem;">${timeStr}</div>
                        </div>
                    </div>
                </td>
                <td style="padding: 15px; vertical-align: top;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="max-width: 400px; flex: 1;">
                            <div style="font-weight: 600; color: #f1f5f9; margin-bottom: 8px; font-size: 1.1rem;">
                                ${item.post_title || 'Blog Post'}
                            </div>
                            <div style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 8px;">
                                Section: ${item.section_title || 'N/A'} | Post ID: ${item.post_id || 'N/A'}
                            </div>
                            <div style="color: #e0e0e0; font-size: 0.95rem; line-height: 1.4;">
                                ${item.generated_content ? item.generated_content.substring(0, 200) + (item.generated_content.length > 200 ? '...' : '') : 'No content'}
                            </div>
                        </div>
                        <button onclick="queueManager.deleteQueueItem(${item.id})" 
                                style="background: #ef4444; border: none; border-radius: 4px; padding: 8px 12px; color: white; cursor: pointer; font-size: 0.8rem; margin-left: 15px; flex-shrink: 0;"
                                title="Delete this item">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    /**
     * Show empty queue state
     */
    showEmptyQueue() {
        const queueTableContainer = document.getElementById('queue-table-container');
        const emptyQueue = document.getElementById('empty-queue');
        
        queueTableContainer.style.display = 'none';
        emptyQueue.style.display = 'block';
    }

    /**
     * Update queue count badge
     */
    updateQueueCount() {
        const queueCount = document.getElementById('queue-count');
        if (queueCount) {
            queueCount.textContent = this.queueData.length;
        }
    }

    /**
     * Delete a single queue item
     */
    async deleteQueueItem(itemId) {
        if (!confirm('Are you sure you want to delete this queue item?')) {
            return;
        }

        try {
            const response = await fetch(`/launchpad/api/queue/${itemId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Remove item from local data
                this.queueData = this.queueData.filter(item => item.id !== itemId);
                this.renderQueue();
                this.updateQueueCount();
                
                // Show success message
                this.showNotification('Queue item deleted successfully', 'success');
            } else {
                this.showNotification('Error deleting queue item: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error deleting queue item:', error);
            this.showNotification('Error deleting queue item: ' + error.message, 'error');
        }
    }

    /**
     * Delete all queue items
     */
    async deleteAllQueueItems() {
        if (!confirm('Are you sure you want to delete ALL queue items? This cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch('/launchpad/api/queue/clear', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Clear local data
                this.queueData = [];
                this.renderQueue();
                this.updateQueueCount();
                
                // Show success message
                this.showNotification('All queue items deleted successfully', 'success');
            } else {
                this.showNotification('Error clearing queue: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error clearing queue:', error);
            this.showNotification('Error clearing queue: ' + error.message, 'error');
        }
    }

    /**
     * Show notification message
     */
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 6px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            max-width: 400px;
            word-wrap: break-word;
        `;
        
        // Set background color based on type
        switch (type) {
            case 'success':
                notification.style.backgroundColor = '#10b981';
                break;
            case 'error':
                notification.style.backgroundColor = '#ef4444';
                break;
            default:
                notification.style.backgroundColor = '#3b82f6';
        }
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Remove notification after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    /**
     * Add 10 items to the queue by running the sequence 10 times:
     * 1) Generate random product selection
     * 2) Generate AI content for that product
     * 3) Add to queue
     */
    async add10Items() {
        const button = document.getElementById('add-10-items-btn');
        const originalText = button.innerHTML;
        
        try {
            // Disable button and show progress
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding Items...';
            
            let successCount = 0;
            let errorCount = 0;
            
            for (let i = 1; i <= 10; i++) {
                try {
                    // Update progress
                    button.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Adding Item ${i}/10...`;
                    
                    // Step 1: Generate random product selection
                    if (window.itemSelectionManager) {
                        await window.itemSelectionManager.selectRandomProduct();
                        // Wait a moment for the selection to process
                        await new Promise(resolve => setTimeout(resolve, 500));
                    }
                    
                    // Step 2: Generate AI content
                    if (window.aiContentGenerationManager) {
                        await window.aiContentGenerationManager.generateContent();
                        // Wait a moment for content generation
                        await new Promise(resolve => setTimeout(resolve, 1000));
                    }
                    
                    // Step 3: Add to queue (silent mode)
                    if (window.aiContentGenerationManager) {
                        const queueResult = await window.aiContentGenerationManager.addToQueue(true);
                        if (!queueResult) {
                            throw new Error('Failed to add to queue');
                        }
                        // Wait a moment for queue addition
                        await new Promise(resolve => setTimeout(resolve, 500));
                    }
                    
                    successCount++;
                    
                } catch (error) {
                    console.error(`Error adding item ${i}:`, error);
                    errorCount++;
                }
            }
            
            // Reload queue data to show new items
            await this.loadQueueData();
            
            // Show completion message
            this.showNotification(`Added ${successCount} items to queue${errorCount > 0 ? ` (${errorCount} errors)` : ''}`, 'success');
            
        } catch (error) {
            console.error('Error in add10Items:', error);
            this.showNotification('Error adding items to queue: ' + error.message, 'error');
        } finally {
            // Re-enable button
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }
}

// Global accordion function (for backward compatibility)
function toggleAccordion(sectionId) {
    const content = document.getElementById(sectionId + '-content');
    const chevron = document.getElementById(sectionId + '-chevron');
    
    if (content.classList.contains('active')) {
        content.classList.remove('active');
        chevron.classList.remove('rotated');
    } else {
        content.classList.add('active');
        chevron.classList.add('rotated');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we're on a page with queue functionality
    if (document.getElementById('posting-queue-content')) {
        window.queueManager = new QueueManager();
    }
});
