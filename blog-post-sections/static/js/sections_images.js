// sections_images.js - Sections rendering for Image substage with simple image placeholders

// Global variables
let currentPostId = null;
let sectionsData = null;

// Iframe Communication Setup for LLM Actions Integration
// Listen for requests from purple panel (LLM Actions)
window.addEventListener('message', (event) => {
    console.log('Green panel (images) received message:', event.data);
    if (event.data.type === 'GET_SELECTED_SECTIONS') {
        console.log('Received GET_SELECTED_SECTIONS request from LLM Actions');
        const selectedIds = getSelectedSectionIds();
        console.log('Sending selected section IDs:', selectedIds);
        try {
            event.source.postMessage({
                type: 'SELECTED_SECTIONS_RESPONSE',
                sectionIds: selectedIds
            }, '*');
            console.log('Response sent successfully');
        } catch (error) {
            console.error('Error sending response:', error);
        }
    }
});

// Function to get selected section IDs for LLM Actions
function getSelectedSectionIds() {
    const checkboxes = document.querySelectorAll('.section-select-checkbox:checked');
    const selectedIds = Array.from(checkboxes).map(cb => cb.dataset.sectionId);
    console.log('getSelectedSectionIds called, found:', selectedIds);
    return selectedIds;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', async function() {
    console.log('Sections_images.js loaded - DOM Content Loaded event fired');
    
    // Add immediate visual feedback
    const panel = document.getElementById('sections-panel-content');
    if (panel) {
        panel.innerHTML = '<p style="color: #10b981;">JavaScript is working! Loading sections...</p>';
    }
    
    // Get post ID from URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    currentPostId = urlParams.get('post_id');
    
    if (!currentPostId) {
        console.log('No post_id found in URL, using default post_id=22');
        currentPostId = '22';
    }
    
    console.log('About to load sections for post:', currentPostId);
    loadSections(currentPostId).catch(error => {
        console.error('Failed to load sections:', error);
        const panel = document.getElementById('sections-panel-content');
        if (panel) {
            panel.innerHTML = `<p style="color: #ef4444;">Failed to load sections: ${error.message}</p>`;
        }
    });
    
    // Set up manual sync button
    const syncBtn = document.getElementById('manual-sync-sections-btn');
    if (syncBtn) {
        syncBtn.addEventListener('click', () => {
            if (currentPostId) {
                loadSections(currentPostId);
            }
        });
    }
});

// Load sections from API
async function loadSections(postId) {
    try {
        console.log('Loading sections for post:', postId);
        const response = await fetch(`/api/sections/${postId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        sectionsData = data;
        
        console.log('Sections data loaded:', data);
        console.log('About to render sections for images...');
        renderSections(data);
        console.log('Sections rendered for images');
        
    } catch (error) {
        console.error('Error loading sections:', error);
        document.getElementById('sections-panel-content').innerHTML = 
            `<p style="color: #ef4444;">Error loading sections: ${error.message}</p>`;
    }
}

// Render sections in the panel for Image substage
function renderSections(data) {
    const panel = document.getElementById('sections-panel-content');
    
    if (!data || !data.sections || data.sections.length === 0) {
        panel.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: #9ca3af;">
                <i class="fas fa-images" style="font-size: 3rem; margin-bottom: 1rem; color: #10b981;"></i>
                <h3 style="color: #7dd3fc; margin-bottom: 0.5rem;">No Sections Found</h3>
                <p>Create sections in the Post Info substage first.</p>
            </div>
        `;
        return;
    }
    
    const sectionsHtml = data.sections.map((section, index) => 
        renderSectionImage(section, index, data.sections.length)
    ).join('');
    
    panel.innerHTML = sectionsHtml;
    
    // Initialize functionality
    initSectionSelection();
    initReorderButtons();
    initAccordions();
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Render a single section with image support for Image substage
function renderSectionImage(section, index, totalSections) {
    const sectionId = section.id;
    const heading = escapeHtml(section.section_heading || section.title || `Section ${index + 1}`);
    const description = escapeHtml(section.section_description || section.description || '');
    
    // Handle image display with new structure
    let imageContent = '';
    if (section.image) {
        if (section.image.path && !section.image.placeholder) {
            // Found actual image
            imageContent = `
                <div style="text-align: center; margin: 1rem 0;">
                    <img src="http://localhost:5001${section.image.path}" 
                         alt="${escapeHtml(section.image.alt_text || 'Section image')}" 
                         style="max-width: 100%; max-height: 200px; border-radius: 0.5rem; border: 2px solid #10b981;"
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                    <div class="image-error" style="display: none; color: #ef4444; background: #1f2937; padding: 0.5rem; border-radius: 0.25rem; margin: 0.5rem 0;">
                        <small><strong>Image not found:</strong> ${escapeHtml(section.image.path)}</small>
                    </div>
                </div>
            `;
        } else {
            // No image available - show placeholder
            imageContent = `
                <div style="text-align: center; padding: 2rem; background: #065f46; border: 2px dashed #10b981; border-radius: 0.5rem; margin: 1rem 0;">
                    <i class="fas fa-image" style="font-size: 3rem; color: #a7f3d0; margin-bottom: 1rem;"></i>
                    <p style="color: #a7f3d0;">${escapeHtml(section.image.alt_text || 'No image available')}</p>
                </div>
            `;
        }
    } else {
        // Fallback for sections without image data
        imageContent = `
            <div style="text-align: center; padding: 2rem; background: #065f46; border: 2px dashed #10b981; border-radius: 0.5rem; margin: 1rem 0;">
                <i class="fas fa-image" style="font-size: 3rem; color: #a7f3d0; margin-bottom: 1rem;"></i>
                <p style="color: #a7f3d0;">No image data available</p>
            </div>
        `;
    }
    
    const sectionHtml = `
        <div class="section" data-section-id="${sectionId}" style="background:#14342b;border-radius:1rem;box-shadow:0 2px 12px #0004;margin-bottom:1.5rem;">
            <div style="display:flex;align-items:center;gap:1em;padding:1.2rem 2rem 0 2rem;">
                <input type="checkbox" class="section-select-checkbox" data-section-id="${sectionId}" checked style="width:1.2em;height:1.2em;">
                <button class="section-accordion-trigger" type="button" aria-expanded="false" aria-controls="section-accordion-${index}" style="display:flex;align-items:center;width:100%;background:none;border:none;cursor:pointer;padding:0;text-align:left;">
                    <span class="section-drag-handle" style="cursor:grab;margin-right:1rem;color:#b9e0ff;font-size:1.5rem;user-select:none;">&#x2630;</span>
                    <h2 style="color:#7dd3fc;font-size:1.5rem;font-weight:bold;flex:1;margin:0;display:inline-block;vertical-align:middle;">${index + 1}. ${heading}</h2>
                    <span class="section-arrow" style="color:#b9e0ff;font-size:1.5rem;user-select:none;transition:transform 0.2s;">&#x25BC;</span>
                </button>
                <div style="display:flex;flex-direction:column;gap:0.25rem;">
                    <button class="section-reorder-btn" data-section-id="${sectionId}" data-direction="up" ${index === 0 ? 'disabled' : ''} style="background:none;border:none;color:#b9e0ff;cursor:pointer;font-size:1rem;padding:0.25rem;${index === 0 ? 'opacity:0.5;cursor:not-allowed;' : ''}">&#x25B2;</button>
                    <button class="section-reorder-btn" data-section-id="${sectionId}" data-direction="down" ${index === totalSections - 1 ? 'disabled' : ''} style="background:none;border:none;color:#b9e0ff;cursor:pointer;font-size:1rem;padding:0.25rem;${index === totalSections - 1 ? 'opacity:0.5;cursor:not-allowed;' : ''}">&#x25BC;</button>
                </div>
            </div>
            <div style="padding:0 2rem 1.5rem 2rem;" onclick="event.stopPropagation();">
                <div style="color:#b9e0ff;font-size:1.1rem;margin-bottom:0.5rem;">${description}</div>
            </div>
            <div id="section-accordion-${index}" style="display:none;padding:0 2rem 2rem 2rem;">
                <div style="color: #e5e7eb;">
                    ${imageContent}
                </div>
            </div>
        </div>
    `;
    
    console.log(`Section ${index + 1} rendered for images (ID: ${sectionId})`);
    
    return sectionHtml;
}

// Initialize accordion functionality
function initAccordions() {
    console.log('Initializing accordions for images...');
    
    const accordionTriggers = document.querySelectorAll('.section-accordion-trigger');
    
    accordionTriggers.forEach(trigger => {
        trigger.addEventListener('click', function() {
            const accordionId = this.getAttribute('aria-controls');
            const accordion = document.getElementById(accordionId);
            const arrow = this.querySelector('.section-arrow');
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            
            // Toggle accordion
            if (isExpanded) {
                accordion.style.display = 'none';
                this.setAttribute('aria-expanded', 'false');
                arrow.style.transform = 'rotate(0deg)';
            } else {
                accordion.style.display = 'block';
                this.setAttribute('aria-expanded', 'true');
                arrow.style.transform = 'rotate(180deg)';
            }
        });
    });
}

// Initialize section selection functionality
function initSectionSelection() {
    console.log('Initializing section selection for images...');
    
    const checkboxes = document.querySelectorAll('.section-select-checkbox');
    
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSelectionCount();
            saveSelection();
        });
    });
    
    updateSelectionCount();
}

// Update the selection count display
function updateSelectionCount() {
    const checkboxes = document.querySelectorAll('.section-select-checkbox');
    const checkedBoxes = document.querySelectorAll('.section-select-checkbox:checked');
    
    console.log(`Section selection updated: ${checkedBoxes.length}/${checkboxes.length} sections selected`);
}

// Save selection to localStorage
function saveSelection() {
    const checkboxes = document.querySelectorAll('.section-select-checkbox');
    const selection = {};
    
    checkboxes.forEach(checkbox => {
        selection[checkbox.dataset.sectionId] = checkbox.checked;
    });
    
    localStorage.setItem(`section-selection-${currentPostId}`, JSON.stringify(selection));
    console.log('Section selection saved to localStorage');
}

// Initialize reorder buttons
function initReorderButtons() {
    console.log('Initializing reorder buttons for images...');
    
    const reorderButtons = document.querySelectorAll('.section-reorder-btn');
    
    reorderButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const sectionId = this.dataset.sectionId;
            const direction = this.dataset.direction;
            
            console.log(`Moving section ${sectionId} ${direction}`);
            moveSection(sectionId, direction);
        });
    });
}

// Move section up or down
async function moveSection(sectionId, direction) {
    try {
        const response = await fetch(`/api/sections/${sectionId}/move`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ direction: direction })
        });
        
        if (response.ok) {
            console.log(`Section ${sectionId} moved ${direction} successfully`);
            // Reload sections to reflect the new order
            if (currentPostId) {
                loadSections(currentPostId);
            }
        } else {
            console.error(`Failed to move section ${sectionId} ${direction}`);
        }
    } catch (error) {
        console.error('Error moving section:', error);
    }
} 