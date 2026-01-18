/**
 * Knowledge Base Navigation and Interaction
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize sidebar navigation
    initSidebarNavigation();
    
    // Auto-expand current section
    expandCurrentSection();
});

function initSidebarNavigation() {
    const sectionHeaders = document.querySelectorAll('.kb-nav-section-header');
    
    sectionHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const section = this.closest('.kb-nav-section');
            section.classList.toggle('collapsed');
        });
    });
}

function expandCurrentSection() {
    // Find active page
    const activePage = document.querySelector('.kb-nav-page.active');
    if (activePage) {
        const section = activePage.closest('.kb-nav-section');
        if (section) {
            section.classList.remove('collapsed');
        }
    }
}

// Search functionality (to be implemented)
function performSearch(query) {
    // TODO: Implement full-text search
    console.log('Searching for:', query);
}
