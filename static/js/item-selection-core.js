// Core Item Selection Manager - Main coordination and initialization
class ItemSelectionCore {
    constructor() {
        this.selectedProduct = null;
        this.allProducts = [];
        this.filteredProducts = [];
        this.currentProductIndex = 0;
        
        // Get platform and channel data from template
        this.platform = window.pageData?.platform || { name: 'facebook', display_name: 'Facebook' };
        this.channelType = window.pageData?.channel_type || { name: 'product_post', display_name: 'Product Posts' };
        
        this.init();
    }
    
    init() {
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
    
    // Delegate methods to specialized modules
    toggleCategoryAccordion() {
        if (window.itemSelectionAccordions) {
            window.itemSelectionAccordions.toggleCategoryAccordion();
        }
    }
    
    toggleProductsBrowserAccordion() {
        if (window.itemSelectionAccordions) {
            window.itemSelectionAccordions.toggleProductsBrowserAccordion();
        }
    }
    
    selectCurrentProduct() {
        if (window.itemSelectionSelection) {
            window.itemSelectionSelection.selectCurrentProduct();
        }
    }
    
    selectRandomProduct() {
        if (window.itemSelectionSelection) {
            window.itemSelectionSelection.selectRandomProduct();
        }
    }
    
    updateProducts() {
        if (window.itemSelectionData) {
            window.itemSelectionData.updateProducts();
        }
    }
    
    goToPreviousProduct() {
        if (window.itemSelectionBrowser) {
            window.itemSelectionBrowser.goToPreviousProduct();
        }
    }
    
    goToNextProduct() {
        if (window.itemSelectionBrowser) {
            window.itemSelectionBrowser.goToNextProduct();
        }
    }
    
    filterProducts() {
        if (window.itemSelectionBrowser) {
            window.itemSelectionBrowser.filterProducts();
        }
    }
    
    loadCategories() {
        if (window.itemSelectionData) {
            window.itemSelectionData.loadCategories();
        }
    }
    
    loadLastUpdated() {
        if (window.itemSelectionData) {
            window.itemSelectionData.loadLastUpdated();
        }
    }
    
    loadSelectedProduct() {
        if (window.itemSelectionData) {
            window.itemSelectionData.loadSelectedProduct();
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.itemSelectionManager = new ItemSelectionCore();
});
