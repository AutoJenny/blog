/**
 * Header Workspace - Main coordination script for header stage
 * Handles panel initialization and coordination
 */

// Header Workspace - Main coordination script
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Header Workspace] Initializing...');
    
    // Initialize Uber Generate button
    initUberGenerate();
    
    // Initialize all panels
    // Panel initialization will be added as panels are developed
    
    console.log('[Header Workspace] All panels initialized');
});

// Uber Generate functionality
function initUberGenerate() {
    const uberBtn = document.getElementById('uber-generate-btn');
    if (!uberBtn) return;

    uberBtn.addEventListener('click', async function() {
        console.log('[Uber Generate] Starting generation of all header elements');
        
        // Disable button during generation
        uberBtn.disabled = true;
        uberBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        
        try {
            // Make single API call to generate all elements
            const response = await fetch(`/header/api/posts/${window.postId}/generate-title-summary`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log('[Uber Generate] Success, emitting events to all panels');
                
                // Emit custom event with all generated data
                const event = new CustomEvent('uberGenerateTitleSummary', {
                    detail: {
                        title_options: data.title_options || [],
                        subtitle: data.subtitle || '',
                        summary: data.summary || '',
                        slug: data.slug || ''
                    }
                });
                
                document.dispatchEvent(event);
                
                // Show success message
                uberBtn.innerHTML = '<i class="fas fa-check"></i> Generated Successfully!';
                setTimeout(() => {
                    uberBtn.innerHTML = '<i class="fas fa-magic"></i> Generate All (Title, Subtitle, Summary, Slug)';
                }, 2000);

                // Notify opener (launchpad) that header title & summary completed
                try { if (window.opener) window.opener.postMessage('header_title_summary_complete', '*'); } catch (_) {}
                
            } else {
                throw new Error(data.error || 'Generation failed');
            }
            
        } catch (error) {
            console.error('[Uber Generate] Error:', error);
            uberBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Generation Failed';
            setTimeout(() => {
                uberBtn.innerHTML = '<i class="fas fa-magic"></i> Generate All (Title, Subtitle, Summary, Slug)';
            }, 3000);
        } finally {
            uberBtn.disabled = false;
        }
    });
}

// Accordion toggle functions
function toggleTitleGenerationAccordion() {
    const content = document.getElementById('title-generation-content');
    const icon = document.getElementById('title-generation-accordion-icon');
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

function toggleSummaryGenerationAccordion() {
    const content = document.getElementById('summary-generation-content');
    const icon = document.getElementById('summary-generation-accordion-icon');
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

function toggleSlugAccordion() {
    const content = document.getElementById('slug-content');
    const icon = document.getElementById('slug-accordion-icon');
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

function toggleImageGenerationAccordion() {
    const content = document.getElementById('image-generation-content');
    const icon = document.getElementById('image-generation-accordion-icon');
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

function toggleImageDetailsAccordion() {
    const content = document.getElementById('image-details-content');
    const icon = document.getElementById('image-details-accordion-icon');
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

function toggleTitleSummaryOutputAccordion() {
    const content = document.getElementById('title-summary-output-content');
    const icon = document.getElementById('title-summary-output-accordion-icon');
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

// Placeholder functions for other accordions
function toggleImagePreviewAccordion() {
    const content = document.getElementById('image-preview-content');
    const icon = document.getElementById('image-preview-accordion-icon');
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

function toggleMetaTitleAccordion() {
    const content = document.getElementById('meta-title-content');
    const icon = document.getElementById('meta-title-accordion-icon');
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

function toggleMetaDescriptionAccordion() {
    const content = document.getElementById('meta-description-content');
    const icon = document.getElementById('meta-description-accordion-icon');
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

function toggleMetaTagsAccordion() {
    const content = document.getElementById('meta-tags-content');
    const icon = document.getElementById('meta-tags-accordion-icon');
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

function toggleSeoAnalysisAccordion() {
    const content = document.getElementById('seo-analysis-content');
    const icon = document.getElementById('seo-analysis-accordion-icon');
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

function toggleAuthorSelectionAccordion() {
    const content = document.getElementById('author-selection-content');
    const icon = document.getElementById('author-selection-accordion-icon');
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

function toggleWordCountAccordion() {
    const content = document.getElementById('word-count-content');
    const icon = document.getElementById('word-count-accordion-icon');
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

function togglePublishDateAccordion() {
    const content = document.getElementById('publish-date-content');
    const icon = document.getElementById('publish-date-accordion-icon');
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

function toggleStatusAccordion() {
    const content = document.getElementById('status-content');
    const icon = document.getElementById('status-accordion-icon');
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

function toggleCompleteReviewAccordion() {
    const content = document.getElementById('complete-review-content');
    const icon = document.getElementById('complete-review-accordion-icon');
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

function toggleValidationAccordion() {
    const content = document.getElementById('validation-content');
    const icon = document.getElementById('validation-accordion-icon');
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

function toggleFinalEditAccordion() {
    const content = document.getElementById('final-edit-content');
    const icon = document.getElementById('final-edit-accordion-icon');
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}
