/**
 * Context Panel - Modular Component
 * Self-contained module for managing context display with page-specific configuration
 */

class ContextPanel {
    constructor(options = {}) {
        this.containerId = options.containerId || 'context-panel';
        this.postId = options.postId || window.postId;
        
        // Callbacks for external communication
        this.callbacks = {
            onContextLoad: options.onContextLoad || (() => {}),
            onContextUpdate: options.onContextUpdate || (() => {})
        };
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.restoreAccordionState();
    }

    setupEventListeners() {
        // Accordion functionality is handled by the global toggleContextAccordion function
    }

    async loadPostContext() {
        try {
            const response = await fetch(`/planning/api/posts/${this.postId}`);
            const data = await response.json();
            
            if (data) {
                // Selected idea (idea_seed from post_development)
                if (data.post && data.post.idea_seed) {
                    const selectedIdeaDisplay = document.getElementById('selected-idea-display');
                    if (selectedIdeaDisplay) {
                        selectedIdeaDisplay.textContent = data.post.idea_seed;
                    }
                } else {
                    const selectedIdeaDisplay = document.getElementById('selected-idea-display');
                    if (selectedIdeaDisplay) {
                        selectedIdeaDisplay.textContent = 'No selected idea found';
                    }
                }
                
                // Expanded idea
                if (data.post && data.post.expanded_idea) {
                    const expandedIdeaDisplay = document.getElementById('expanded-idea-display');
                    if (expandedIdeaDisplay) {
                        expandedIdeaDisplay.textContent = data.post.expanded_idea;
                    }
                } else {
                    const expandedIdeaDisplay = document.getElementById('expanded-idea-display');
                    if (expandedIdeaDisplay) {
                        expandedIdeaDisplay.textContent = 'No expanded idea found';
                    }
                }
                
                this.callbacks.onContextLoad('post', data.post);
            }
        } catch (error) {
            console.error('Error loading post context:', error);
            const selectedIdeaDisplay = document.getElementById('selected-idea-display');
            const expandedIdeaDisplay = document.getElementById('expanded-idea-display');
            if (selectedIdeaDisplay) selectedIdeaDisplay.textContent = 'Error loading';
            if (expandedIdeaDisplay) expandedIdeaDisplay.textContent = 'Error loading';
        }
    }

    async loadSectionContext(sectionId) {
        try {
            // Get section data
            const sectionResponse = await fetch(`/authoring/api/posts/${this.postId}/sections/${sectionId}`);
            const sectionData = await sectionResponse.json();
            
            if (sectionData.success && sectionData.section) {
                const section = sectionData.section;
                
                // Update section context displays
                const sectionTitleDisplay = document.getElementById('section-title-display');
                if (sectionTitleDisplay) {
                    sectionTitleDisplay.textContent = section.title || section.section_heading || '-';
                }
                
                const sectionSubtitleDisplay = document.getElementById('section-subtitle-display');
                if (sectionSubtitleDisplay) {
                    sectionSubtitleDisplay.textContent = section.description || section.section_description || '-';
                }
                
                const sectionDescriptionDisplay = document.getElementById('section-description-display');
                if (sectionDescriptionDisplay) {
                    // Use detailed description from section_structure if available
                    sectionDescriptionDisplay.textContent = section.detailed_description || section.description || section.section_description || '-';
                }
                
                const sectionTopicsDisplay = document.getElementById('section-topics-display');
                if (sectionTopicsDisplay) {
                    // Handle topics as array or string
                    let topicsText = '-';
                    if (section.topics) {
                        if (Array.isArray(section.topics)) {
                            topicsText = section.topics.join(', ');
                        } else {
                            topicsText = section.topics;
                        }
                    }
                    sectionTopicsDisplay.textContent = topicsText;
                }
                
                const avoidTopicsDisplay = document.getElementById('avoid-topics-display');
                if (avoidTopicsDisplay) {
                    avoidTopicsDisplay.textContent = section.avoid_topics || '-';
                }
                
                // Add section content display for LLM prompt data
                const sectionContentDisplay = document.getElementById('section-content-display');
                if (sectionContentDisplay) {
                    const content = section.polished || section.draft || '-';
                    // Strip HTML tags for display
                    const plainText = content.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
                    sectionContentDisplay.textContent = plainText.substring(0, 200) + (plainText.length > 200 ? '...' : '');
                }
                
                this.callbacks.onContextLoad('section', section);
            }
        } catch (error) {
            console.error('Error loading section context:', error);
            // Set error state for section context
            const sectionTitleDisplay = document.getElementById('section-title-display');
            if (sectionTitleDisplay) sectionTitleDisplay.textContent = 'Error loading';
        }
    }

    restoreAccordionState() {
        const savedState = localStorage.getItem('context-accordion-state');
        if (savedState === 'open') {
            const content = document.getElementById('context-accordion-content');
            const icon = document.getElementById('context-accordion-icon');
            if (content && icon) {
                content.style.display = 'block';
                icon.classList.remove('fa-chevron-up');
                icon.classList.add('fa-chevron-down');
            }
        }
    }

    // Public API methods
    refreshContext(sectionId = null) {
        this.loadPostContext();
        if (sectionId) {
            this.loadSectionContext(sectionId);
        }
    }

    clearContext() {
        const elements = [
            'selected-idea-display',
            'expanded-idea-display', 
            'section-title-display',
            'section-subtitle-display',
            'section-description-display',
            'section-topics-display',
            'avoid-topics-display'
        ];
        
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = '-';
            }
        });
    }
}

// Accordion function for context panel
function toggleContextAccordion() {
    const content = document.getElementById('context-accordion-content');
    const icon = document.getElementById('context-accordion-icon');
    
    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
        localStorage.setItem('context-accordion-state', 'open');
    } else {
        content.style.display = 'none';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
        localStorage.setItem('context-accordion-state', 'closed');
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ContextPanel;
}
