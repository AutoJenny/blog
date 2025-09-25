// Data Management for Item Selection - INCLUDES THE BROKEN PERSISTENCE CODE
class ItemSelectionData {
    constructor() {
        this.init();
    }
    
    init() {
        // Data-specific initialization
    }
    
    async loadCategories() {
        try {
            const response = await fetch('/launchpad/api/syndication/categories');
            const data = await response.json();
            
            if (data.success) {
                const categoryCount = document.getElementById('category-count');
                const categoryList = document.getElementById('category-list');
                
                if (categoryCount) categoryCount.textContent = `${data.categories.length} categories`;
                
                // Display categories with proper hierarchy tree
                let html = '';
                
                // Build category tree structure
                const categoryMap = {};
                const rootCategories = [];
                
                data.categories.forEach(cat => {
                    categoryMap[cat.id] = {
                        ...cat,
                        children: []
                    };
                });
                
                // Build parent-child relationships
                data.categories.forEach(cat => {
                    if (cat.parent_id && categoryMap[cat.parent_id]) {
                        categoryMap[cat.parent_id].children.push(categoryMap[cat.id]);
                    } else {
                        rootCategories.push(categoryMap[cat.id]);
                    }
                });
                
                // Sort categories by name
                function sortCategories(categories) {
                    categories.sort((a, b) => a.name.localeCompare(b.name));
                    categories.forEach(cat => {
                        if (cat.children.length > 0) {
                            sortCategories(cat.children);
                        }
                    });
                }
                
                sortCategories(rootCategories);
                
                // Render category tree
                function renderCategoryTree(categories, level = 0) {
                    let html = '';
                    const indent = '&nbsp;'.repeat(level * 3);
                    const isLast = (index, array) => index === array.length - 1;
                    
                    categories.forEach((cat, index) => {
                        const hasChildren = cat.children.length > 0;
                        const connector = isLast(index, categories) ? '└─' : '├─';
                        const childConnector = isLast(index, categories) ? '&nbsp;&nbsp;' : '│&nbsp;&nbsp;';
                        
                        html += `<div style="margin: 2px 0; font-size: 0.85rem;">`;
                        html += `${indent}${connector} `;
                        html += `<span style="color: ${hasChildren ? '#f1f5f9' : '#94a3b8'}; font-weight: ${hasChildren ? '600' : '400'};">${cat.name}</span>`;
                        html += ` <span style="color: #64748b; font-size: 0.75rem;">(ID: ${cat.id})</span>`;
                        html += `</div>`;
                        
                        if (hasChildren && level < 3) { // Limit depth to avoid overwhelming display
                            html += renderCategoryTree(cat.children, level + 1);
                        } else if (hasChildren && level >= 3) {
                            html += `<div style="margin-left: ${(level + 1) * 12}px; color: #64748b; font-style: italic;">... ${cat.children.length} subcategories</div>`;
                        }
                    });
                    
                    return html;
                }
                
                // Show top-level categories and their immediate children
                const topLevelCategories = rootCategories.filter(cat => cat.level <= 2);
                html = renderCategoryTree(topLevelCategories);
                
                // Add summary
                const totalCategories = data.categories.length;
                const displayedCategories = topLevelCategories.length + topLevelCategories.reduce((sum, cat) => sum + cat.children.length, 0);
                const remainingCategories = totalCategories - displayedCategories;
                
                if (remainingCategories > 0) {
                    html += `<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #334155; color: #64748b; font-style: italic;">... and ${remainingCategories} more categories</div>`;
                }
                
                if (categoryList) categoryList.innerHTML = html;
            }
        } catch (error) {
            console.error('Error loading categories:', error);
            const categoryList = document.getElementById('category-list');
            if (categoryList) categoryList.innerHTML = 'Error loading categories';
        }
    }
    
    async loadLastUpdated() {
        try {
            const response = await fetch('/launchpad/api/syndication/last-updated');
            const data = await response.json();
            
            if (data.success) {
                const lastUpdatedText = document.getElementById('last-updated-text');
                if (data.last_updated && lastUpdatedText) {
                    const date = new Date(data.last_updated);
                    const now = new Date();
                    const diffMs = now - date;
                    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
                    const diffDays = Math.floor(diffHours / 24);
                    
                    let timeAgo;
                    if (diffDays > 0) {
                        timeAgo = `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
                    } else if (diffHours > 0) {
                        timeAgo = `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
                    } else {
                        timeAgo = 'Just now';
                    }
                    
                    lastUpdatedText.textContent = `Last Updated: ${timeAgo} (${data.total_products} products)`;
                } else if (lastUpdatedText) {
                    lastUpdatedText.textContent = 'No products found';
                }
            } else {
                console.error('Error loading last updated timestamp:', data.error);
                const lastUpdatedText = document.getElementById('last-updated-text');
                if (lastUpdatedText) lastUpdatedText.textContent = 'Error loading timestamp';
            }
        } catch (error) {
            console.error('Error loading last updated timestamp:', error);
            const lastUpdatedText = document.getElementById('last-updated-text');
            if (lastUpdatedText) lastUpdatedText.textContent = 'Error loading timestamp';
        }
    }
    
    // UPDATED PERSISTENCE CODE - NOW USES NEW STATE MANAGER
    async loadSelectedProduct() {
        try {
            console.log('Loading selected product from database...');
            
            // Use the new state manager instead of direct API calls
            if (window.stateManager) {
                const selection = await window.stateManager.getSelection('product_post', 'product');
                
                if (selection && selection.selected_data) {
                    const product = selection.selected_data;
                    window.itemSelectionManager.selectedProduct = product;
                    if (window.itemSelectionUtils) {
                        window.itemSelectionUtils.updateSelectedProductDisplay(product.name);
                    }
                    
                    // Notify other components that a product has been selected
                    if (window.itemSelectionSelection) {
                        window.itemSelectionSelection.notifyProductSelected(product);
                    }
                    console.log('Selected product loaded and displayed via state manager:', product.name);
                } else {
                    console.log('No selected product found in database via state manager');
                }
            } else {
                console.error('State manager not available, falling back to direct API call');
                // Fallback to direct API call if state manager not available
                const response = await fetch('/launchpad/api/selected-product');
                const data = await response.json();
                console.log('Load selected product response:', data);
                
                if (data.product) {
                    window.itemSelectionManager.selectedProduct = data.product;
                    if (window.itemSelectionUtils) {
                        window.itemSelectionUtils.updateSelectedProductDisplay(data.product.name);
                    }
                    
                    // Notify other components that a product has been selected
                    if (window.itemSelectionSelection) {
                        window.itemSelectionSelection.notifyProductSelected(data.product);
                    }
                    console.log('Selected product loaded and displayed:', data.product.name);
                } else {
                    console.log('No selected product found in database');
                }
            }
        } catch (error) {
            console.error('Error loading selected product:', error);
        }
    }
    
    // UPDATED PERSISTENCE CODE - NOW USES NEW STATE MANAGER
    async saveSelectedProduct(product) {
        try {
            console.log('Saving selected product to database:', product.id, product.name);
            
            // Use the new state manager instead of direct API calls
            if (window.stateManager) {
                const success = await window.stateManager.setSelection(
                    'product_post', 
                    'product', 
                    product.id, 
                    product
                );
                
                if (success) {
                    console.log('Product saved successfully to database via state manager');
                } else {
                    console.error('Failed to save selected product via state manager');
                }
            } else {
                console.error('State manager not available, falling back to direct API call');
                // Fallback to direct API call if state manager not available
                const response = await fetch('/launchpad/api/selected-product', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        product_id: product.id
                    })
                });
                
                const data = await response.json();
                console.log('Save selected product response:', data);
                if (!data.success) {
                    console.error('Failed to save selected product:', data.error);
                } else {
                    console.log('Product saved successfully to database');
                }
            }
        } catch (error) {
            console.error('Error saving selected product:', error);
        }
    }
    
    async updateProducts() {
        const updateProductsBtn = document.getElementById('update-products-btn');
        const updateStatus = document.getElementById('update-status');
        const updateSpinner = document.getElementById('update-spinner');
        const updateMessage = document.getElementById('update-message');
        const updateProgress = document.getElementById('update-progress');
        const updateProgressBar = document.getElementById('update-progress-bar');
        const updateProgressText = document.getElementById('update-progress-text');
        
        if (updateProductsBtn) {
            updateProductsBtn.classList.add('loading');
            updateProductsBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';
        }
        
        if (updateStatus) updateStatus.style.display = 'block';
        if (updateSpinner) updateSpinner.style.display = 'block';
        if (updateMessage) updateMessage.textContent = 'Checking for product updates...';
        if (updateProgress) updateProgress.style.display = 'none';
        
        try {
            const response = await fetch('/launchpad/api/syndication/update-products', {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                if (updateMessage) {
                    updateMessage.innerHTML = `<i class="fas fa-check-circle" style="color: #10b981;"></i> ${data.message}`;
                }
                if (updateSpinner) updateSpinner.style.display = 'none';
                
                // Show progress if there are updates
                if (data.stats && updateProgress) {
                    updateProgress.style.display = 'block';
                    if (updateProgressBar) updateProgressBar.style.width = '100%';
                    if (updateProgressText) {
                        updateProgressText.textContent = `Updated: ${data.stats.updated || 0} products`;
                    }
                }
                
                // Refresh categories if they were updated
                if (data.stats && data.stats.categories_updated) {
                    await this.loadCategories();
                }
                
                // Refresh last updated timestamp
                await this.loadLastUpdated();
            } else {
                if (updateMessage) {
                    updateMessage.innerHTML = `<i class="fas fa-exclamation-triangle" style="color: #f59e0b;"></i> ${data.error}`;
                }
                if (updateSpinner) updateSpinner.style.display = 'none';
            }
        } catch (error) {
            console.error('Error updating products:', error);
            if (updateMessage) {
                updateMessage.innerHTML = `<i class="fas fa-times-circle" style="color: #ef4444;"></i> Error updating products. Please try again.`;
            }
            if (updateSpinner) updateSpinner.style.display = 'none';
        } finally {
            if (updateProductsBtn) {
                updateProductsBtn.classList.remove('loading');
                updateProductsBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Check for Updates';
            }
            
            // Hide status after 5 seconds
            setTimeout(() => {
                if (updateStatus) updateStatus.style.display = 'none';
            }, 5000);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.itemSelectionData = new ItemSelectionData();
});
