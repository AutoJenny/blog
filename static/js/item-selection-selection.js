// Product Selection Management
class ItemSelectionSelection {
    constructor() {
        this.init();
    }
    
    init() {
        // Selection-specific initialization
    }
    
    async selectCurrentProduct() {
        if (window.itemSelectionManager.filteredProducts.length === 0) {
            if (window.itemSelectionUtils) {
                window.itemSelectionUtils.showNotification('No products available to select.', 'error');
            }
            return;
        }
        
        const currentProduct = window.itemSelectionManager.filteredProducts[window.itemSelectionManager.currentProductIndex];
        window.itemSelectionManager.selectedProduct = currentProduct;
        this.displayProduct(window.itemSelectionManager.selectedProduct);
        
        // Save to database
        if (window.itemSelectionData) {
            await window.itemSelectionData.saveSelectedProduct(currentProduct);
        }
        
        // Update accordion header
        if (window.itemSelectionUtils) {
            window.itemSelectionUtils.updateSelectedProductDisplay(currentProduct.name);
        }
        
        // Notify other components that a product has been selected
        this.notifyProductSelected(currentProduct);
        
        if (window.itemSelectionUtils) {
            window.itemSelectionUtils.showNotification(`Selected: ${currentProduct.name}`, 'success');
        }
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
                window.itemSelectionManager.selectedProduct = data.product;
                this.displayProduct(window.itemSelectionManager.selectedProduct);
                
                // Save to database
                if (window.itemSelectionData) {
                    await window.itemSelectionData.saveSelectedProduct(data.product);
                }
                
                // Update accordion header
                if (window.itemSelectionUtils) {
                    window.itemSelectionUtils.updateSelectedProductDisplay(data.product.name);
                }
                
                // Notify other components that a product has been selected
                this.notifyProductSelected(data.product);
                
                if (window.itemSelectionUtils) {
                    window.itemSelectionUtils.showNotification(`Random product selected: ${data.product.name}`, 'success');
                }
            } else {
                if (window.itemSelectionUtils) {
                    window.itemSelectionUtils.showNotification('Error selecting product: ' + data.error, 'error');
                }
            }
        } catch (error) {
            console.error('Error selecting product:', error);
            if (window.itemSelectionUtils) {
                window.itemSelectionUtils.showNotification('Error selecting product. Please try again.', 'error');
            }
        } finally {
            if (selectRandomProductBtn) {
                selectRandomProductBtn.classList.remove('loading');
                selectRandomProductBtn.innerHTML = '<i class="fas fa-random"></i> Random';
            }
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
    
    notifyProductSelected(product) {
        // Create standardized data package
        const dataPackage = {
            data_type: 'product',
            platform: window.itemSelectionManager.platform,
            channel_type: window.itemSelectionManager.channelType,
            source_data: product,
            generation_config: {
                content_types: ['feature', 'benefit', 'story'],
                max_length: 280,
                include_hashtags: true,
                include_price: true
            },
            timestamp: new Date().toISOString()
        };
        
        // Dispatch custom event for other components to listen to
        const event = new CustomEvent('dataSelected', {
            detail: { dataPackage: dataPackage }
        });
        document.dispatchEvent(event);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.itemSelectionSelection = new ItemSelectionSelection();
});
