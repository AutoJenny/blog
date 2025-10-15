/**
 * Mini-Preview Panel - Tab switching and content management
 */

// Tab switching functionality
function switchPreviewTab(tabName) {
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Remove active class from all tab panes
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    
    // Add active class to selected tab button
    const selectedButton = document.querySelector(`[data-tab="${tabName}"]`);
    if (selectedButton) {
        selectedButton.classList.add('active');
    }
    
    // Add active class to selected tab pane
    const selectedPane = document.getElementById(`${tabName}-tab`);
    if (selectedPane) {
        selectedPane.classList.add('active');
    }
    
    console.log(`[Mini-Preview Panel] Switched to ${tabName} tab`);
}

// Accordion functionality for long content fields
function toggleFieldAccordion(fieldId) {
    const content = document.getElementById(`${fieldId}-content`);
    const icon = document.getElementById(`${fieldId}-icon`);
    
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

// Load sections data
async function loadSections() {
    try {
        const response = await fetch(`/authoring/api/posts/${window.postId}/sections`);
        const data = await response.json();
        
        if (data.success && data.sections) {
            const sectionsContainer = document.getElementById('sections-container');
            if (sectionsContainer) {
                sectionsContainer.innerHTML = '';
                
                data.sections.forEach(section => {
                    const sectionItem = document.createElement('div');
                    sectionItem.className = 'section-item';
                    sectionItem.innerHTML = `
                        <div class="section-header" onclick="toggleSectionAccordion('section-${section.id}')">
                            <div class="section-title">${section.title || section.section_heading || `Section ${section.id}`}</div>
                            <i class="fas fa-chevron-down section-chevron" id="section-${section.id}-chevron"></i>
                        </div>
                        <div class="section-content collapsed" id="section-${section.id}-content">
                            <div class="section-draft">${section.draft || section.section_text || 'No draft content available'}</div>
                        </div>
                    `;
                    sectionsContainer.appendChild(sectionItem);
                });
            }
        }
    } catch (error) {
        console.error('[Mini-Preview Panel] Error loading sections:', error);
        const sectionsContainer = document.getElementById('sections-container');
        if (sectionsContainer) {
            sectionsContainer.innerHTML = '<div class="content-field"><div class="field-value">Error loading sections</div></div>';
        }
    }
}

// Toggle section accordion
function toggleSectionAccordion(sectionId) {
    const content = document.getElementById(`${sectionId}-content`);
    const chevron = document.getElementById(`${sectionId}-chevron`);
    
    if (content && chevron) {
        content.classList.toggle('collapsed');
        chevron.classList.toggle('open');
    }
}

// Load post context data
async function loadPostContext() {
    try {
        const response = await fetch(`/planning/api/posts/${window.postId}`);
        const data = await response.json();
        
        if (data && data.post) {
            // Update selected idea
            const selectedIdeaElement = document.getElementById('dev-selected-idea');
            if (selectedIdeaElement) {
                selectedIdeaElement.textContent = data.post.idea_seed || 'No selected idea found';
            }
            
            // Update expanded idea
            const expandedIdeaElement = document.getElementById('dev-expanded-idea');
            const expandedIdeaPreview = document.getElementById('dev-expanded-idea-preview');
            if (expandedIdeaElement && expandedIdeaPreview) {
                const expandedIdea = data.post.expanded_idea || 'No expanded idea found';
                expandedIdeaElement.textContent = expandedIdea;
                
                // Create preview (first 100 characters)
                const preview = expandedIdea.length > 100 
                    ? expandedIdea.substring(0, 100) + '...' 
                    : expandedIdea;
                expandedIdeaPreview.textContent = preview;
            }
        }
    } catch (error) {
        console.error('[Mini-Preview Panel] Error loading post context:', error);
        // Set error states
        const selectedIdeaElement = document.getElementById('dev-selected-idea');
        const expandedIdeaElement = document.getElementById('dev-expanded-idea');
        const expandedIdeaPreview = document.getElementById('dev-expanded-idea-preview');
        
        if (selectedIdeaElement) selectedIdeaElement.textContent = 'Error loading';
        if (expandedIdeaElement) expandedIdeaElement.textContent = 'Error loading';
        if (expandedIdeaPreview) expandedIdeaPreview.textContent = 'Error loading';
    }
}


// Initialize the panel
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Mini-Preview Panel] Initialized');
    
    // Ensure development tab is active by default
    switchPreviewTab('development');
    
    // Load initial data
    loadPostContext();
    loadSections();
    
    // Note: Only Post Content is shown in this panel per requirements
});

// Export functions for external use
window.switchPreviewTab = switchPreviewTab;
window.toggleFieldAccordion = toggleFieldAccordion;
window.toggleSectionAccordion = toggleSectionAccordion;
window.loadPostContext = loadPostContext;
window.loadSections = loadSections;
