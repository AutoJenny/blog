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
    // Top-level sections
    const sectionHeaders = document.querySelectorAll('.kb-nav-section-header');
    
    sectionHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const section = this.closest('.kb-nav-section');
            section.classList.toggle('collapsed');
        });
    });
    
    // Nested subsections (Blog Posts, Social Posts, etc.)
    const subsectionHeaders = document.querySelectorAll('.kb-nav-subsection-header');
    
    subsectionHeaders.forEach(header => {
        header.addEventListener('click', function(e) {
            // Don't toggle if clicking the link itself
            if (e.target.tagName === 'A') {
                return;
            }
            const subsection = this.closest('.kb-nav-subsection');
            subsection.classList.toggle('collapsed');
        });
    });
}

function expandCurrentSection() {
    // Find active page
    const activePage = document.querySelector('.kb-nav-page.active, .kb-nav-subpage.active');
    if (activePage) {
        // Expand parent section
        const section = activePage.closest('.kb-nav-section');
        if (section) {
            section.classList.remove('collapsed');
        }
        
        // Expand parent subsection if it's a subpage
        const subsection = activePage.closest('.kb-nav-subsection');
        if (subsection) {
            subsection.classList.remove('collapsed');
        }
    }
    
    // Also expand if subsection link is active
    const activeSubsectionLink = document.querySelector('.kb-nav-subsection-link.active');
    if (activeSubsectionLink) {
        const subsection = activeSubsectionLink.closest('.kb-nav-subsection');
        if (subsection) {
            subsection.classList.remove('collapsed');
        }
        const section = subsection.closest('.kb-nav-section');
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
