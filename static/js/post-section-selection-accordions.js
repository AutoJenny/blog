/**
 * Post Section Selection Accordions
 * Handles accordion functionality for the post section selection module
 */

class PostSectionAccordions {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Listen for accordion toggle events
        document.addEventListener('click', (e) => {
            if (e.target.closest('[data-accordion="post-section-selection"]')) {
                this.togglePostSectionSelectionAccordion();
            }
        });
    }

    togglePostSectionSelectionAccordion() {
        const accordion = document.querySelector('[data-accordion="post-section-selection"]');
        if (!accordion) return;

        const content = document.getElementById('post-section-selection-content');
        const chevron = document.getElementById('post-section-selection-chevron');
        
        if (!content || !chevron) return;

        const isCollapsed = accordion.classList.contains('collapsed');
        
        if (isCollapsed) {
            // Expand
            accordion.classList.remove('collapsed');
            content.style.display = 'block';
            chevron.style.transform = 'rotate(90deg)';
        } else {
            // Collapse
            accordion.classList.add('collapsed');
            content.style.display = 'none';
            chevron.style.transform = 'rotate(0deg)';
        }
    }

    expandPostSectionSelectionAccordion() {
        const accordion = document.querySelector('[data-accordion="post-section-selection"]');
        if (!accordion) return;

        const content = document.getElementById('post-section-selection-content');
        const chevron = document.getElementById('post-section-selection-chevron');
        
        if (!content || !chevron) return;

        accordion.classList.remove('collapsed');
        content.style.display = 'block';
        chevron.style.transform = 'rotate(90deg)';
    }

    collapsePostSectionSelectionAccordion() {
        const accordion = document.querySelector('[data-accordion="post-section-selection"]');
        if (!accordion) return;

        const content = document.getElementById('post-section-selection-content');
        const chevron = document.getElementById('post-section-selection-chevron');
        
        if (!content || !chevron) return;

        accordion.classList.add('collapsed');
        content.style.display = 'none';
        chevron.style.transform = 'rotate(0deg)';
    }
}
