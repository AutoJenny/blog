// Accordion Management for Item Selection
class ItemSelectionAccordions {
    constructor() {
        this.init();
    }
    
    init() {
        // Initialize accordion states
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
            if (window.itemSelectionManager && window.itemSelectionManager.allProducts.length === 0) {
                if (window.itemSelectionBrowser) {
                    window.itemSelectionBrowser.loadAllProducts();
                }
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

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.itemSelectionAccordions = new ItemSelectionAccordions();
});
