/**
 * Post Section Selection Core Module
 * Main coordinator for post section selection functionality
 */

class PostSectionSelectionManager {
    constructor() {
        this.dataManager = new PostSectionDataManager();
        this.browser = new PostSectionBrowser(this.dataManager);
        this.selection = new PostSectionSelection(this.dataManager);
        this.accordions = new PostSectionAccordions();
        this.init();
    }

    init() {
        // Restore previous selection after a short delay to ensure DOM is ready
        setTimeout(() => {
            this.browser.restorePreviousSelection();
        }, 100);
    }

    // Public methods for other modules
    getCurrentPost() {
        return this.dataManager.getCurrentPost();
    }

    getCurrentSections() {
        return this.dataManager.getCurrentSections();
    }

    getSelectedSection() {
        return this.dataManager.getSelectedSection();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.postSectionSelectionManager = new PostSectionSelectionManager();
});
