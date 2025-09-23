class ItemSelectionManager {
    constructor() {
        this.selectedProduct = null;
        this.allProducts = [];
        this.filteredProducts = [];
        this.currentProductIndex = 0;
        
        // Get platform and channel data from template
        this.platform = window.pageData?.platform || { name: 'facebook', display_name: 'Facebook' };
        this.channelType = window.pageData?.channel_type || { name: 'product_post', display_name: 'Product Posts' };
        
        this.initEventListeners();
        this.loadInitialData();
        this.loadSelectedProduct();
    }

    initEventListeners() {
        // Category accordion toggle
        const categoryHeader = document.getElementById('category-accordion-header');
        if (categoryHeader) {
            categoryHeader.addEventListener('click', () => this.toggleCategoryAccordion());
        }

        // Products browser accordion toggle
        const productsBrowserHeader = document.getElementById('products-browser-accordion-header');
        if (productsBrowserHeader) {
            productsBrowserHeader.addEventListener('click', () => this.toggleProductsBrowserAccordion());
        }

        // Product selection buttons
        const selectThisProductBtn = document.getElementById('select-this-product-btn');
        if (selectThisProductBtn) {
            selectThisProductBtn.addEventListener('click', () => this.selectCurrentProduct());
        }

        const selectRandomProductBtn = document.getElementById('select-random-product-btn');
        if (selectRandomProductBtn) {
            selectRandomProductBtn.addEventListener('click', () => this.selectRandomProduct());
        }

        // Update products button
        const updateProductsBtn = document.getElementById('update-products-btn');
        if (updateProductsBtn) {
            updateProductsBtn.addEventListener('click', () => this.updateProducts());
        }

        // Navigation buttons
        const prevBtn = document.getElementById('prev-product-btn');
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.goToPreviousProduct());
        }

        const nextBtn = document.getElementById('next-product-btn');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.goToNextProduct());
        }

        // Product filter
        const productFilter = document.getElementById('product-filter');
        if (productFilter) {
            productFilter.addEventListener('input', () => this.filterProducts());
        }
    }

    async loadInitialData() {
        await this.loadCategories();
        await this.loadLastUpdated();
    }

    toggleCategoryAccordion() {
        const content = document.getElementById('category-accordion-content');
        const chevron = document.getElementById('category-chevron');
        
        if (content.style.display === 'none') {
            content.style.display = 'block';
            chevron.style.transform = 'rotate(90deg)';
        } else {
            content.style.display = 'none';
            chevron.style.transform = 'rotate(0deg)';
        }
    }

    toggleProductsBrowserAccordion() {
        const content = document.getElementById('products-browser-accordion-content');
        const chevron = document.getElementById('products-browser-chevron');
        
        if (content.style.display === 'none') {
            content.style.display = 'block';
            chevron.style.transform = 'rotate(90deg)';
            // Load products when accordion is opened
            if (this.allProducts.length === 0) {
                this.loadAllProducts();
            }
            // Enable selection buttons when accordion is opened
            this.enableSelectionButtons();
        } else {
            content.style.display = 'none';
            chevron.style.transform = 'rotate(0deg)';
        }
    }

    enableSelectionButtons() {
        const selectThisProductBtn = document.getElementById('select-this-product-btn');
        const selectRandomProductBtn = document.getElementById('select-random-product-btn');
        
        if (selectThisProductBtn) selectThisProductBtn.disabled = false;
        if (selectRandomProductBtn) selectRandomProductBtn.disabled = false;
    }

    async selectCurrentProduct() {
        if (this.filteredProducts.length === 0) {
            this.showNotification('No products available to select.', 'error');
            return;
        }
        
        const currentProduct = this.filteredProducts[this.currentProductIndex];
        this.selectedProduct = currentProduct;
        this.displayProduct(this.selectedProduct);
        
        // Save to database
        await this.saveSelectedProduct(currentProduct);
        
        // Update accordion header
        this.updateSelectedProductDisplay(currentProduct.name);
        
        // Notify other components that a product has been selected
        this.notifyProductSelected(currentProduct);
        
        this.showNotification(`Selected: ${currentProduct.name}`, 'success');
    }

    async selectRandomProduct() {
        const selectRandomProductBtn = document.getElementById('select-random-product-btn');
        if (selectRandomProductBtn) {
            selectRandomProductBtn.classList.add('loading');
            selectRandomProductBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Selecting...';
        }
        
        try {
            const response = await fetch('/launchpad/api/syndication/select-product', {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                this.selectedProduct = data.product;
                this.displayProduct(this.selectedProduct);
                
                // Save to database
                await this.saveSelectedProduct(data.product);
                
                // Update accordion header
                this.updateSelectedProductDisplay(data.product.name);
                
                // Notify other components that a product has been selected
                this.notifyProductSelected(data.product);
                
                this.showNotification(`Random product selected: ${data.product.name}`, 'success');
            } else {
                this.showNotification('Error selecting product: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error selecting product:', error);
            this.showNotification('Error selecting product. Please try again.', 'error');
        } finally {
            if (selectRandomProductBtn) {
                selectRandomProductBtn.classList.remove('loading');
                selectRandomProductBtn.innerHTML = '<i class="fas fa-random"></i> Random';
            }
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

    displayProduct(product) {
        const productDisplay = document.getElementById('product-display');
        const noProduct = document.getElementById('no-product');
        
        if (!productDisplay || !noProduct) return;
        
        // Update product information
        const productName = document.getElementById('product-name');
        const productPrice = document.getElementById('product-price');
        const productDescription = document.getElementById('product-description');
        const productImage = document.getElementById('product-image');
        const productUrl = document.getElementById('product-url');
        
        if (productName) productName.textContent = product.name;
        if (productPrice) productPrice.textContent = `£${product.price}`;
        if (productDescription) productDescription.textContent = product.description || 'No description available';
        
        // Handle image - most products have placeholder, show a fallback
        if (productImage) {
            const imageUrl = product.image_url;
            if (imageUrl && !imageUrl.includes('essential.jpg')) {
                productImage.src = imageUrl;
            } else {
                // Use a generic product placeholder for products without real images
                productImage.src = 'https://via.placeholder.com/400x400/8B4513/FFFFFF?text=Clan.com+Product';
            }
        }
        
        if (productUrl) productUrl.href = product.url || '#';
        
        // Display categories if available
        this.displayProductCategories(product);
        
        productDisplay.style.display = 'block';
        noProduct.style.display = 'none';
    }

    displayProductCategories(product) {
        const categoryContainer = document.getElementById('product-categories');
        if (!categoryContainer) return;
        
        if (product.category_hierarchy && Array.isArray(product.category_hierarchy)) {
            // Group categories by type (product vs other)
            const productCategories = product.category_hierarchy.filter(cat => cat.is_product_category);
            const otherCategories = product.category_hierarchy.filter(cat => !cat.is_product_category);
            
            // Filter out redundant top-level categories
            const redundantCategories = ['Products', 'Departments', 'Collections', 'CLAN Main Category'];
            const filteredOtherCategories = otherCategories.filter(cat => 
                !redundantCategories.includes(cat.breadcrumb) && 
                !redundantCategories.some(redundant => cat.breadcrumb.includes(redundant))
            );
            
            let html = '<strong>Categories:</strong> ';
            let categoryParts = [];
            
            // For product categories, build a clean hierarchy
            if (productCategories.length > 0) {
                // Remove duplicates by name and keep the deepest level
                const uniqueProductCategories = {};
                productCategories.forEach(cat => {
                    if (!uniqueProductCategories[cat.breadcrumb] || 
                        cat.level > uniqueProductCategories[cat.breadcrumb].level) {
                        uniqueProductCategories[cat.breadcrumb] = cat;
                    }
                });
                
                // Convert to array and sort by level (deepest first)
                const sortedCategories = Object.values(uniqueProductCategories)
                    .sort((a, b) => b.level - a.level);
                
                // Build breadcrumb path - prioritize the most specific category and its parents
                const pathParts = [];
                let lastLevel = -1;
                
                // First, try to find a clear hierarchy by looking for the most specific category
                // and then finding its parent categories
                const mostSpecific = sortedCategories[0];
                pathParts.push(mostSpecific);
                lastLevel = mostSpecific.level;
                
                // Add parent categories that are at a higher level (lower number)
                for (let i = 1; i < sortedCategories.length; i++) {
                    const cat = sortedCategories[i];
                    if (cat.level < lastLevel) {
                        pathParts.unshift(cat); // Add to beginning to maintain hierarchy order
                        lastLevel = cat.level;
                    }
                }
                
                // If we have a good hierarchy (at least 2 levels), use it
                if (pathParts.length > 1) {
                    categoryParts.push(pathParts.map(cat => cat.breadcrumb).join(' > '));
                } else {
                    // Otherwise just show the most specific category
                    categoryParts.push(mostSpecific.breadcrumb);
                }
            }
            
            // For other categories, show unique names only
            if (filteredOtherCategories.length > 0) {
                const uniqueOtherCategories = [...new Set(filteredOtherCategories.map(cat => cat.breadcrumb))];
                categoryParts.push(uniqueOtherCategories.join(', '));
            }
            
            if (categoryParts.length > 0) {
                if (categoryParts.length === 1) {
                    // Only product categories
                    html += categoryParts[0];
                } else {
                    // Product categories on first line, other departments on second line
                    html += categoryParts[0];
                    html += '<br><span style="color: #3b82f6; font-size: 0.85rem;">Other: ' + categoryParts[1] + '</span>';
                }
                categoryContainer.innerHTML = html;
                categoryContainer.style.display = 'block';
            } else {
                categoryContainer.style.display = 'none';
            }
        } else if (product.category_ids && Array.isArray(product.category_ids)) {
            // Fallback to old format if hierarchy not available
            categoryContainer.innerHTML = '<strong>Categories:</strong> ' + product.category_ids.join(', ');
            categoryContainer.style.display = 'block';
        } else if (product.category_ids && typeof product.category_ids === 'string') {
            try {
                const categories = JSON.parse(product.category_ids);
                categoryContainer.innerHTML = '<strong>Categories:</strong> ' + categories.join(', ');
                categoryContainer.style.display = 'block';
            } catch (e) {
                categoryContainer.style.display = 'none';
            }
        } else {
            categoryContainer.style.display = 'none';
        }
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

    async loadAllProducts() {
        try {
            const response = await fetch('/launchpad/api/syndication/products');
            const data = await response.json();
            
            if (data.success) {
                this.allProducts = data.products;
                this.filteredProducts = [...this.allProducts];
                this.currentProductIndex = 0;
                
                // Update count display
                const productsBrowserCount = document.getElementById('products-browser-count');
                if (productsBrowserCount) {
                    productsBrowserCount.textContent = `${this.allProducts.length} products`;
                }
                
                // Display first product
                this.displayCurrentProduct();
                this.updateNavigationButtons();
            } else {
                console.error('Error loading products:', data.error);
                const productBrowserDisplay = document.getElementById('product-browser-display');
                if (productBrowserDisplay) {
                    productBrowserDisplay.innerHTML = 'Error loading products';
                }
            }
        } catch (error) {
            console.error('Error loading products:', error);
            const productBrowserDisplay = document.getElementById('product-browser-display');
            if (productBrowserDisplay) {
                productBrowserDisplay.innerHTML = 'Error loading products';
            }
        }
    }

    displayCurrentProduct() {
        const productBrowserDisplay = document.getElementById('product-browser-display');
        if (!productBrowserDisplay) return;
        
        if (this.filteredProducts.length === 0) {
            productBrowserDisplay.innerHTML = 
                '<div style="text-align: center; color: #94a3b8; font-style: italic;">No products found</div>';
            return;
        }
        
        const product = this.filteredProducts[this.currentProductIndex];
        const productCounter = document.getElementById('product-counter');
        if (productCounter) {
            productCounter.textContent = `Product ${this.currentProductIndex + 1} of ${this.filteredProducts.length}`;
        }
        
        // Create product display HTML
        let html = `
            <div style="display: flex; gap: 20px; margin-bottom: 15px;">
                <div style="flex-shrink: 0;">
                    <img src="${product.image_url || '/static/images/placeholder.jpg'}" 
                         alt="${product.name}" 
                         style="width: 120px; height: 120px; object-fit: cover; border-radius: 8px; border: 1px solid #334155;">
                </div>
                <div style="flex: 1;">
                    <h4 style="color: #f1f5f9; margin: 0 0 10px 0; font-size: 1.2rem;">${product.name}</h4>
                    <div style="color: #10b981; font-weight: 600; margin-bottom: 10px; font-size: 1.1rem;">£${product.price || 'N/A'}</div>
                    <div style="color: #94a3b8; margin-bottom: 8px;"><strong>SKU:</strong> ${product.sku}</div>
                    <div style="color: #94a3b8; margin-bottom: 8px;"><strong>ID:</strong> ${product.id}</div>
                    <div style="color: #94a3b8; margin-bottom: 8px;"><strong>Design Type:</strong> ${product.printable_design_type || 'N/A'}</div>
                    ${product.url ? `<div style="color: #94a3b8; margin-bottom: 8px;"><strong>URL:</strong> <a href="${product.url}" target="_blank" style="color: #3b82f6;">View Product</a></div>` : ''}
                </div>
            </div>
        `;
        
        if (product.description) {
            html += `
                <div style="margin-top: 15px;">
                    <h5 style="color: #f1f5f9; margin: 0 0 8px 0;">Description:</h5>
                    <div style="color: #e2e8f0; line-height: 1.5; background: #0f172a; padding: 10px; border-radius: 6px; border: 1px solid #334155;">
                        ${product.description}
                    </div>
                </div>
            `;
        }
        
        if (product.category_ids && product.category_ids.length > 0) {
            html += `
                <div style="margin-top: 15px;">
                    <h5 style="color: #f1f5f9; margin: 0 0 8px 0;">Categories:</h5>
                    <div style="color: #e2e8f0;">
                        ${product.category_ids.map(id => `<span style="background: #334155; padding: 2px 8px; border-radius: 4px; margin-right: 5px; font-size: 0.8rem;">${id}</span>`).join('')}
                    </div>
                </div>
            `;
        }
        
        productBrowserDisplay.innerHTML = html;
    }

    updateNavigationButtons() {
        const prevBtn = document.getElementById('prev-product-btn');
        const nextBtn = document.getElementById('next-product-btn');
        
        if (prevBtn) prevBtn.disabled = this.currentProductIndex === 0;
        if (nextBtn) nextBtn.disabled = this.currentProductIndex >= this.filteredProducts.length - 1;
    }

    goToPreviousProduct() {
        if (this.currentProductIndex > 0) {
            this.currentProductIndex--;
            this.displayCurrentProduct();
            this.updateNavigationButtons();
        }
    }

    goToNextProduct() {
        if (this.currentProductIndex < this.filteredProducts.length - 1) {
            this.currentProductIndex++;
            this.displayCurrentProduct();
            this.updateNavigationButtons();
        }
    }

    filterProducts() {
        const productFilter = document.getElementById('product-filter');
        if (!productFilter) return;
        
        const filterValue = productFilter.value.toLowerCase();
        
        if (filterValue === '') {
            this.filteredProducts = [...this.allProducts];
        } else {
            this.filteredProducts = this.allProducts.filter(product => 
                product.name.toLowerCase().includes(filterValue)
            );
        }
        
        this.currentProductIndex = 0;
        this.displayCurrentProduct();
        this.updateNavigationButtons();
    }

    notifyProductSelected(product) {
        // Create standardized data package
        const dataPackage = this.createDataPackage(product);
        
        // Dispatch custom event for other components to listen to
        const event = new CustomEvent('dataSelected', {
            detail: { dataPackage: dataPackage }
        });
        document.dispatchEvent(event);
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // Public method to get the currently selected product
    getSelectedProduct() {
        return this.selectedProduct;
    }

    // Load selected product from database on page load
    async loadSelectedProduct() {
        try {
            console.log('Loading selected product from database...');
            const response = await fetch('/launchpad/api/syndication/get-selected-product');
            const data = await response.json();
            console.log('Load selected product response:', data);
            
            if (data.success && data.product) {
                this.selectedProduct = data.product;
                this.updateSelectedProductDisplay(data.product.name);
                
                // Notify other components that a product has been selected
                this.notifyProductSelected(data.product);
                console.log('Selected product loaded and displayed:', data.product.name);
            } else {
                console.log('No selected product found in database');
            }
        } catch (error) {
            console.error('Error loading selected product:', error);
        }
    }

    // Save selected product to database
    async saveSelectedProduct(product) {
        try {
            console.log('Saving selected product to database:', product.id, product.name);
            const response = await fetch('/launchpad/api/syndication/save-selected-product', {
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
                console.error('Failed to save selected product:', data.message);
            } else {
                console.log('Product saved successfully to database');
            }
        } catch (error) {
            console.error('Error saving selected product:', error);
        }
    }

    // Update the accordion header display
    updateSelectedProductDisplay(productName) {
        const selectedProductDisplay = document.getElementById('selected-product-display');
        if (selectedProductDisplay) {
            selectedProductDisplay.textContent = productName;
        }
    }

    // Create standardized data package for other modules
    createDataPackage(sourceData) {
        return {
            data_type: 'product',
            platform: this.platform,
            channel_type: this.channelType,
            source_data: sourceData,
            generation_config: {
                content_types: ['feature', 'benefit', 'story'],
                max_length: 280,
                include_hashtags: true,
                include_price: true
            },
            timestamp: new Date().toISOString()
        };
    }
}

// Global accordion toggle function (for HTML onclick handlers)
function toggleAccordion(sectionId) {
    const content = document.getElementById(`${sectionId}-content`);
    const chevron = document.getElementById(`${sectionId}-chevron`);
    
    if (content && chevron) {
        if (content.style.display === 'none' || content.style.display === '') {
            content.style.display = 'block';
            chevron.style.transform = 'rotate(90deg)';
        } else {
            content.style.display = 'none';
            chevron.style.transform = 'rotate(0deg)';
        }
    }
}

// Auto-initialize when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.itemSelectionManager = new ItemSelectionManager();
});
