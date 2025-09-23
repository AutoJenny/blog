// Utilities for Item Selection
class ItemSelectionUtils {
    constructor() {
        this.init();
    }
    
    init() {
        // Utils-specific initialization
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
        return window.itemSelectionManager ? window.itemSelectionManager.selectedProduct : null;
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
            platform: window.itemSelectionManager ? window.itemSelectionManager.platform : { name: 'facebook', display_name: 'Facebook' },
            channel_type: window.itemSelectionManager ? window.itemSelectionManager.channelType : { name: 'product_post', display_name: 'Product Posts' },
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

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.itemSelectionUtils = new ItemSelectionUtils();
});
