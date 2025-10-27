/**
 * Authoring Workspace - Main Coordination Script
 * Handles initialization and coordination between all modular panels
 */

// Helper functions for Context panel updates
async function loadSectionContext(sectionId) {
    try {
        // Get section data
        const sectionResponse = await fetch(`/authoring/api/posts/${window.postId}/sections/${sectionId}`);
        const sectionData = await sectionResponse.json();
        
        if (sectionData.success && sectionData.section) {
            const sectionOrder = sectionData.section.order;
            
            // Get planning data for this section from the main post data
            const planningResponse = await fetch(`/planning/api/posts/${window.postId}`);
            const planningData = await planningResponse.json();
            
            if (planningData.post && planningData.post.topic_allocation && planningData.post.topic_allocation.allocations) {
                const sectionAllocation = planningData.post.topic_allocation.allocations.find(a => a.section_id === `section_${sectionOrder}`);
                
                if (sectionAllocation) {
                    // Subtitle (section description)
                    document.getElementById('section-subtitle-display').textContent = sectionAllocation.section_theme || '-';
                    
                    // Description (from section_structure)
                    // This will be loaded separately from the API
                    
                    // Topics
                    if (sectionAllocation.topics) {
                        const topicsDisplay = document.getElementById('section-topics-display');
                        topicsDisplay.innerHTML = sectionAllocation.topics.map(topic => 
                            `<span class="topic-tag">${topic}</span>`
                        ).join('');
                    } else {
                        document.getElementById('section-topics-display').textContent = 'No topics found';
                    }
                    
                } else {
                    document.getElementById('section-subtitle-display').textContent = 'No group data found';
                    document.getElementById('section-description-display').textContent = 'No description found';
                    document.getElementById('section-topics-display').textContent = 'No topics found';
                }
            } else {
                document.getElementById('section-subtitle-display').textContent = 'No planning data found';
                document.getElementById('section-description-display').textContent = 'No description found';
                document.getElementById('section-topics-display').textContent = 'No topics found';
            }
        }
    } catch (error) {
        console.error('Error loading section context:', error);
        document.getElementById('section-subtitle-display').textContent = 'Error loading';
        document.getElementById('section-description-display').textContent = 'Error loading';
        document.getElementById('section-topics-display').textContent = 'Error loading';
    }
}

async function loadPostContext() {
    try {
        const response = await fetch(`/planning/api/posts/${window.postId}`);
        const data = await response.json();
        
        if (data) {
            // Selected idea (idea_seed from post_development)
            if (data.post && data.post.idea_seed) {
                const selectedIdeaDisplay = document.getElementById('selected-idea-display');
                if (selectedIdeaDisplay) {
                    selectedIdeaDisplay.textContent = data.post.idea_seed;
                }
            }
            
            // Expanded idea
            if (data.post && data.post.expanded_idea) {
                const expandedIdeaDisplay = document.getElementById('expanded-idea-display');
                if (expandedIdeaDisplay) {
                    expandedIdeaDisplay.textContent = data.post.expanded_idea;
                }
            }
        }
    } catch (error) {
        console.error('Error loading post context:', error);
    }
}

async function loadSectionDraft(sectionId) {
    try {
        const response = await fetch(`/authoring/api/posts/${window.postId}/sections/${sectionId}`);
        const data = await response.json();
        
        if (data.success && data.section) {
            const section = data.section;
            
            // Update section-specific input data display
            document.getElementById('section-title-display').textContent = section.title || '-';
            document.getElementById('section-subtitle-display').textContent = section.subtitle || '-';
            
            // Load all context data
            loadPostContext();
            loadSectionContext(sectionId);
            
            // Load existing draft content
            const contentEditor = document.getElementById('content-editor');
            if (section.draft) {
                contentEditor.value = section.draft;
                contentEditor.disabled = false;
                // Update word count if function exists
                if (typeof updateWordCount === 'function') {
                    updateWordCount();
                }
            } else {
                contentEditor.value = '';
                contentEditor.disabled = false;
            }
            
            // Enable controls
            document.getElementById('preview-btn').disabled = false;
            document.getElementById('save-btn').disabled = false;
            document.getElementById('regenerate-btn').disabled = false;
        }
    } catch (error) {
        console.error('Error loading section draft:', error);
    }
}

function initializeLLMForSection(sectionId) {
    // Initialize LLM module for this section
    console.log('Initialize LLM for section:', sectionId);
    // This would integrate with the existing LLM module
}

// Accordion Functions for Context, Batch Progress, and Output panels
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

function toggleBatchProgressAccordion() {
    const content = document.getElementById('batch-progress-accordion-content');
    const icon = document.getElementById('batch-progress-accordion-icon');
    
    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
        localStorage.setItem('batch-progress-accordion-state', 'open');
    } else {
        content.style.display = 'none';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
        localStorage.setItem('batch-progress-accordion-state', 'closed');
    }
}

function toggleOutputAccordion() {
    const content = document.getElementById('output-accordion-content');
    const icon = document.getElementById('output-accordion-icon');
    
    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
        localStorage.setItem('output-accordion-state', 'open');
    } else {
        content.style.display = 'none';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
        localStorage.setItem('output-accordion-state', 'closed');
    }
}

// Restore accordion states on page load
function restoreAccordionStates() {
    // Restore Context accordion state
    const contextState = localStorage.getItem('context-accordion-state');
    if (contextState === 'open') {
        const content = document.getElementById('context-accordion-content');
        const icon = document.getElementById('context-accordion-icon');
        if (content && icon) {
            content.style.display = 'block';
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
        }
    }
    
    // Restore Batch Progress accordion state
    const batchState = localStorage.getItem('batch-progress-accordion-state');
    if (batchState === 'open') {
        const content = document.getElementById('batch-progress-accordion-content');
        const icon = document.getElementById('batch-progress-accordion-icon');
        if (content && icon) {
            content.style.display = 'block';
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
        }
    }
    
    // Restore Output accordion state
    const outputState = localStorage.getItem('output-accordion-state');
    if (outputState === 'open') {
        const content = document.getElementById('output-accordion-content');
        const icon = document.getElementById('output-accordion-icon');
        if (content && icon) {
            content.style.display = 'block';
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
        }
    }
    
    // Restore LLM Message accordion state
    const llmMessageState = localStorage.getItem('llm-message-accordion-state');
    if (llmMessageState === 'open') {
        const content = document.getElementById('llm-message-accordion-content');
        const icon = document.getElementById('llm-message-accordion-icon');
        if (content && icon) {
            content.style.display = 'block';
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Authoring workspace loaded, initializing panels');
    
    // Restore accordion states
    restoreAccordionStates();
    
    // Initialize Sections Panel with callbacks
    const sectionsPanel = new SectionsPanel({
        postId: window.postId,
        onSectionSelect: async (data) => {
            // Load section into appropriate output panel
            if (window.currentSubstage === 'image-concepts') {
                if (window.imageConceptsOutputPanel) {
                    window.imageConceptsOutputPanel.show({
                        id: data.sectionId,
                        title: data.section.title,
                        subtitle: data.section.subtitle,
                        order: data.section.order,
                        topics: data.section.topics,
                        image_concepts: data.section.image_concepts || '',
                        selected_image_concept: data.section.selected_image_concept || ''
                    });
                }
            } else if (window.currentSubstage === 'image-prompts') {
                // Emit sectionSelected event for PromptBuilderPanel and ImagePromptsOutputPanel
                console.log('[DEBUG] Dispatching sectionSelected event for image-prompts with section:', data.section);
                window.dispatchEvent(new CustomEvent('sectionSelected', {
                    detail: { section: data.section }
                }));
            } else if (window.currentSubstage === 'image-captions') {
                // Emit sectionSelected event for ImageCaptionsOutputPanel
                window.dispatchEvent(new CustomEvent('sectionSelected', {
                    detail: { section: data.section }
                }));
            } else if (typeof outputPanel !== 'undefined') {
                outputPanel.loadSection(data.sectionId, data.section);
            }
            
            // Load Context panel data
            if (typeof contextPanel !== 'undefined') {
                await contextPanel.loadPostContext();
                await contextPanel.loadSectionContext(data.sectionId);
            }
            
            // Initialize LLM module
            initializeLLMForSection(data.sectionId);
            
            // Load existing draft (skip for specialized UIs)
            if (window.currentSubstage !== 'image-concepts' && window.currentSubstage !== 'image-prompts' && window.currentSubstage !== 'image-captions') {
                await loadSectionDraft(data.sectionId);
            }
        },
        onBatchStart: (selectedIds) => {
            if (typeof batchProgressPanel !== 'undefined') {
                batchProgressPanel.startBatch(selectedIds, 'generate');
            }
        },
        onBatchProgress: (progress) => {
            // Update Batch Progress panel
            console.log('Batch progress:', progress);
        },
        onBatchComplete: (result) => {
            // Hide or update Batch Progress panel
            console.log('Batch complete:', result);
        }
    });
    
    // Initialize LLM Settings Panel with callbacks
    const llmSettingsPanel = new LLMSettingsPanel({
        storageKey: 'section-drafting-llm-settings',
        onSettingsChange: (settings) => {
            console.log('[Drafting] LLM Settings changed:', settings);
            // Settings can be used by other panels (LLM Prompts, Output)
        },
        onProviderChange: (settings) => {
            console.log('[Drafting] Provider changed:', settings.provider);
            // Could trigger model-specific behavior
        },
        onModelChange: (settings) => {
            console.log('[Drafting] Model changed:', settings.model);
            // Could update prompts or generation behavior
        },
        onParameterChange: (settings) => {
            console.log('[Drafting] Parameters changed:', settings);
            // Could affect generation quality/temperature
        }
    });
    
    // Initialize LLM Prompts Panel with callbacks
    const llmPromptsPanel = new LLMPromptsPanel({
        postId: window.postId,
        onPromptChange: (prompt) => {
            console.log('[Drafting] LLM Prompt changed:', prompt);
            // Prompt changes can trigger other panel updates
        },
        onPromptLoad: (prompt) => {
            console.log('[Drafting] Prompt loaded:', prompt);
            // Prompt loaded successfully
        },
        onPromptSave: (promptData) => {
            console.log('[Drafting] Prompt saved:', promptData);
            // Prompt saved successfully
        }
    });
    
    // Initialize Context Panel with callbacks
    const contextPanel = new ContextPanel({
        postId: window.postId,
        onContextLoad: (type, data) => {
            console.log(`[Drafting] Context loaded (${type}):`, data);
        },
        onContextUpdate: (data) => {
            console.log('[Drafting] Context updated:', data);
        }
    });
    
    // Make contextPanel globally available
    window.contextPanel = contextPanel;
    
    // Initialize Batch Progress Panel with callbacks
    const batchProgressPanel = new BatchProgressPanel({
        postId: window.postId,
        onBatchStart: (batch) => {
            console.log('[Drafting] Batch started:', batch);
        },
        onBatchProgress: (data) => {
            console.log('[Drafting] Batch progress:', data);
        },
        onBatchComplete: (data) => {
            console.log('[Drafting] Batch completed:', data);
        },
        onBatchCancel: (batch) => {
            console.log('[Drafting] Batch cancelled:', batch);
        }
    });
    
    // Initialize Output Panel with callbacks
    // Skip generic OutputPanel on image-concepts, image-prompts, and image-captions (specialized panels are used)
    if (window.currentSubstage !== 'image-concepts' && window.currentSubstage !== 'image-prompts' && window.currentSubstage !== 'image-captions') {
    const outputPanel = new OutputPanel({
        postId: window.postId,
        onContentChange: (content) => {
            console.log('[Drafting] Content changed:', content.length, 'characters');
        },
        onSave: (sectionId, content) => {
            console.log('[Drafting] Section saved:', sectionId);
        },
        onRegenerate: (sectionId) => {
            console.log('[Drafting] Regenerate requested for section:', sectionId);
            // This would trigger the LLM module to regenerate content
        },
        onPreview: (content) => {
            console.log('[Drafting] Preview requested:', content.length, 'characters');
        },
        onSectionLoad: (sectionId, sectionData) => {
            console.log('[Drafting] Section loaded:', sectionId, sectionData.title);
        }
    });
    }
    
    console.log('All panels initialized successfully');
});

// Export functions for global access
window.loadSectionContext = loadSectionContext;
window.loadPostContext = loadPostContext;
window.loadSectionDraft = loadSectionDraft;
window.initializeLLMForSection = initializeLLMForSection;
window.toggleContextAccordion = toggleContextAccordion;
window.toggleBatchProgressAccordion = toggleBatchProgressAccordion;
window.toggleOutputAccordion = toggleOutputAccordion;
