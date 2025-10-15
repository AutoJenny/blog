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

// Load section context data
async function loadSectionContext(sectionId) {
    try {
        const response = await fetch(`/authoring/api/posts/${window.postId}/sections/${sectionId}`);
        const data = await response.json();
        
        if (data.success && data.section) {
            const section = data.section;
            
            // Update section fields
            const sectionTitleElement = document.getElementById('dev-section-title');
            if (sectionTitleElement) {
                sectionTitleElement.textContent = section.title || section.section_heading || '-';
            }
            
            const sectionSubtitleElement = document.getElementById('dev-section-subtitle');
            if (sectionSubtitleElement) {
                sectionSubtitleElement.textContent = section.description || section.section_description || '-';
            }
            
            const sectionGroupElement = document.getElementById('dev-section-group');
            if (sectionGroupElement) {
                sectionGroupElement.textContent = section.section_heading || section.title || '-';
            }
            
            // Update group summary with accordion
            const groupSummaryElement = document.getElementById('dev-group-summary');
            const groupSummaryPreview = document.getElementById('dev-group-summary-preview');
            if (groupSummaryElement && groupSummaryPreview) {
                const groupSummary = section.section_description || section.description || 'No group summary found';
                groupSummaryElement.textContent = groupSummary;
                
                // Create preview (first 100 characters)
                const preview = groupSummary.length > 100 
                    ? groupSummary.substring(0, 100) + '...' 
                    : groupSummary;
                groupSummaryPreview.textContent = preview;
            }
            
            // Update topics
            const sectionTopicsElement = document.getElementById('dev-section-topics');
            if (sectionTopicsElement) {
                if (section.topics && Array.isArray(section.topics)) {
                    sectionTopicsElement.textContent = section.topics.join(', ');
                } else {
                    sectionTopicsElement.textContent = 'No topics found';
                }
            }
            
            // Update avoid topics
            const avoidTopicsElement = document.getElementById('dev-avoid-topics');
            if (avoidTopicsElement) {
                if (section.avoid_topics && Array.isArray(section.avoid_topics)) {
                    avoidTopicsElement.textContent = section.avoid_topics.join(', ');
                } else {
                    avoidTopicsElement.textContent = 'No avoid topics found';
                }
            }
        }
    } catch (error) {
        console.error('[Mini-Preview Panel] Error loading section context:', error);
        // Set error states for section fields
        const sectionFields = ['dev-section-title', 'dev-section-subtitle', 'dev-section-group', 'dev-group-summary', 'dev-section-topics', 'dev-avoid-topics'];
        sectionFields.forEach(fieldId => {
            const element = document.getElementById(fieldId);
            if (element) element.textContent = 'Error loading';
        });
    }
}

// Initialize the panel
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Mini-Preview Panel] Initialized');
    
    // Ensure development tab is active by default
    switchPreviewTab('development');
    
    // Load initial data
    loadPostContext();
    
    // Listen for section selection events
    window.addEventListener('sectionSelected', function(event) {
        if (event.detail && event.detail.section) {
            loadSectionContext(event.detail.section.id);
        }
    });
});

// Export functions for external use
window.switchPreviewTab = switchPreviewTab;
window.toggleFieldAccordion = toggleFieldAccordion;
window.loadPostContext = loadPostContext;
window.loadSectionContext = loadSectionContext;
