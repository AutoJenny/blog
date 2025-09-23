// Product Browser Management
class ItemSelectionBrowser {
    constructor() {
        this.init();
    }
    
    init() {
        // Browser-specific initialization
    }
    
    async loadAllProducts() {
        try {
            const response = await fetch('/launchpad/api/syndication/products');
            const data = await response.json();
            
            if (data.success) {
                window.itemSelectionManager.allProducts = data.products;
                window.itemSelectionManager.filteredProducts = [...data.products];
                window.itemSelectionManager.currentProductIndex = 0;
                
                // Update count display
                const productsBrowserCount = document.getElementById('products-browser-count');
                if (productsBrowserCount) {
                    productsBrowserCount.textContent = `${data.products.length} products`;
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
        
        if (window.itemSelectionManager.filteredProducts.length === 0) {
            productBrowserDisplay.innerHTML = 
                '<div style="text-align: center; color: #94a3b8; font-style: italic;">No products found</div>';
            return;
        }
        
        const product = window.itemSelectionManager.filteredProducts[window.itemSelectionManager.currentProductIndex];
        const productCounter = document.getElementById('product-counter');
        if (productCounter) {
            productCounter.textContent = `Product ${window.itemSelectionManager.currentProductIndex + 1} of ${window.itemSelectionManager.filteredProducts.length}`;
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
        
        if (prevBtn) prevBtn.disabled = window.itemSelectionManager.currentProductIndex === 0;
        if (nextBtn) nextBtn.disabled = window.itemSelectionManager.currentProductIndex >= window.itemSelectionManager.filteredProducts.length - 1;
    }
    
    goToPreviousProduct() {
        if (window.itemSelectionManager.currentProductIndex > 0) {
            window.itemSelectionManager.currentProductIndex--;
            const product = window.itemSelectionManager.filteredProducts[window.itemSelectionManager.currentProductIndex];
            this.displayCurrentProduct();
            this.updateNavigationButtons();
            // Persist selection to database
            if (window.itemSelectionData) {
                window.itemSelectionData.saveSelectedProduct(product);
            }
            if (window.itemSelectionUtils) {
                window.itemSelectionUtils.updateSelectedProductDisplay(product.name);
            }
        }
    }
    
    goToNextProduct() {
        if (window.itemSelectionManager.currentProductIndex < window.itemSelectionManager.filteredProducts.length - 1) {
            window.itemSelectionManager.currentProductIndex++;
            const product = window.itemSelectionManager.filteredProducts[window.itemSelectionManager.currentProductIndex];
            this.displayCurrentProduct();
            this.updateNavigationButtons();
            // Persist selection to database
            if (window.itemSelectionData) {
                window.itemSelectionData.saveSelectedProduct(product);
            }
            if (window.itemSelectionUtils) {
                window.itemSelectionUtils.updateSelectedProductDisplay(product.name);
            }
        }
    }
    
    filterProducts() {
        const productFilter = document.getElementById('product-filter');
        if (!productFilter) return;
        
        const filterValue = productFilter.value.toLowerCase();
        const currentProduct = window.itemSelectionManager.filteredProducts[window.itemSelectionManager.currentProductIndex];
        
        if (filterValue === '') {
            window.itemSelectionManager.filteredProducts = [...window.itemSelectionManager.allProducts];
        } else {
            window.itemSelectionManager.filteredProducts = window.itemSelectionManager.allProducts.filter(product => 
                product.name.toLowerCase().includes(filterValue)
            );
        }
        
        // Try to preserve current product position if it still matches filter
        if (currentProduct && window.itemSelectionManager.filteredProducts.length > 0) {
            const newIndex = window.itemSelectionManager.filteredProducts.findIndex(p => p.id === currentProduct.id);
            if (newIndex !== -1) {
                window.itemSelectionManager.currentProductIndex = newIndex;
            } else {
                window.itemSelectionManager.currentProductIndex = 0;
            }
        } else {
            window.itemSelectionManager.currentProductIndex = 0;
        }
        
        this.displayCurrentProduct();
        this.updateNavigationButtons();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.itemSelectionBrowser = new ItemSelectionBrowser();
});
