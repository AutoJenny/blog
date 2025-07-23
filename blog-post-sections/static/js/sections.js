// sections.js - Main sections rendering and interaction logic

// Global variables
let currentPostId = null;
let sectionsData = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', async function() {
    console.log('Sections.js loaded');
    
    // Get post ID from URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    currentPostId = urlParams.get('post_id');
    
    if (!currentPostId) {
        // Fetch most recent post and redirect
        try {
            const resp = await fetch('/api/posts/most_recent');
            if (resp.ok) {
                const data = await resp.json();
                if (data && data.id) {
                    window.location.href = `/sections?post_id=${data.id}`;
                    return;
                }
            }
            document.getElementById('sections-panel-content').innerHTML = '<p style="color: #ef4444;">Error: Could not determine most recent post.</p>';
        } catch (err) {
            document.getElementById('sections-panel-content').innerHTML = `<p style="color: #ef4444;">Error: ${err.message}</p>`;
        }
        return;
    }
    
    loadSections(currentPostId);
    
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
        renderSections(data);
        
    } catch (error) {
        console.error('Error loading sections:', error);
        document.getElementById('sections-panel-content').innerHTML = 
            `<p style="color: #ef4444;">Error loading sections: ${error.message}</p>`;
    }
}

// Render sections in the panel
function renderSections(data) {
    const panel = document.getElementById('sections-panel-content');
    
    if (!data.sections || data.sections.length === 0) {
        panel.innerHTML = '<p style="color: #9ca3af;">No sections found for this post.</p>';
        return;
    }
    
    const sectionsHtml = data.sections.map((section, index) => {
        return renderSection(section, index, data.sections.length);
    }).join('');
    
    panel.innerHTML = `
        <div class="sections-container" style="display: flex; flex-direction: column; gap: 1rem;">
            ${sectionsHtml}
        </div>
    `;
    
    // Initialize interactive elements
    initAccordions();
    initReorderButtons();
    initSectionSelection();
}

// Render individual section
function renderSection(section, index, totalSections) {
    const sectionId = section.id;
    const accordionId = `section-accordion-${index}`;
    const heading = section.title || section.section_heading || `Section ${index + 1}`;
    const description = section.description || section.section_description || '';
    const content = section.draft || section.content || '';
    const ideas = section.ideas_to_include || '';
    const facts = section.facts_to_include || '';
    
    // Thumbnail if available
    const thumbnail = section.generated_image_url 
        ? `<img src="${section.generated_image_url}" alt="Section Image" style="width: 32px; height: 32px; object-fit: cover; border-radius: 0.3em; margin-right: 0.75em; border: 2px solid #4ade80; vertical-align: middle;">`
        : '';
    
    return `
        <div class="section" data-section-id="${sectionId}" style="background: #14342b; border-radius: 0.5rem; border: 1px solid #065f46; overflow: hidden;">
            <!-- Section Header -->
            <div class="section-header" style="display: flex; align-items: center; padding: 1rem; background: #0f2e23; border-bottom: 1px solid #065f46;">
                <!-- Reorder Controls -->
                <div class="section-reorder-controls" style="display: flex; flex-direction: column; margin-right: 0.75rem; gap: 0.25rem;">
                    <button class="reorder-btn reorder-up" data-section-id="${sectionId}" title="Move Up" 
                            style="background: #059669; color: white; border: none; border-radius: 0.25rem; width: 24px; height: 24px; cursor: pointer; font-size: 12px; ${index === 0 ? 'opacity: 0.5; cursor: not-allowed;' : ''}">
                        ▲
                    </button>
                    <button class="reorder-btn reorder-down" data-section-id="${sectionId}" title="Move Down" 
                            style="background: #059669; color: white; border: none; border-radius: 0.25rem; width: 24px; height: 24px; cursor: pointer; font-size: 12px; ${index === totalSections - 1 ? 'opacity: 0.5; cursor: not-allowed;' : ''}">
                        ▼
                    </button>
                </div>
                
                <!-- Section Number and Thumbnail -->
                <div style="display: flex; align-items: center; margin-right: 0.75rem;">
                    ${thumbnail}
                    <span style="color: #4ade80; font-weight: bold; font-size: 0.875rem; min-width: 2rem;">${index + 1}</span>
                </div>
                
                <!-- Section Title -->
                <div style="flex: 1;">
                    <h3 style="margin: 0; color: #e5e7eb; font-size: 1rem; font-weight: 600;">${heading}</h3>
                    ${description ? `<p style="margin: 0.25rem 0 0 0; color: #9ca3af; font-size: 0.875rem;">${description}</p>` : ''}
                </div>
                
                <!-- Accordion Toggle -->
                <button class="section-accordion-trigger" aria-controls="${accordionId}" aria-expanded="false" 
                        style="background: none; border: none; color: #4ade80; cursor: pointer; padding: 0.5rem; font-size: 1.25rem;">
                    <span class="section-arrow">▼</span>
                </button>
            </div>
            
            <!-- Section Content (Accordion) -->
            <div id="${accordionId}" class="section-content" style="display: none; padding: 1rem; background: #14342b;">
                <!-- Content Tabs -->
                <div class="section-tabs" style="display: flex; border-bottom: 1px solid #065f46; margin-bottom: 1rem;">
                    <button class="tab-btn active" data-tab="content" style="background: #059669; color: white; border: none; padding: 0.5rem 1rem; cursor: pointer; border-radius: 0.25rem 0.25rem 0 0;">Content</button>
                    <button class="tab-btn" data-tab="ideas" style="background: #374151; color: #9ca3af; border: none; padding: 0.5rem 1rem; cursor: pointer; border-radius: 0.25rem 0.25rem 0 0;">Ideas</button>
                    <button class="tab-btn" data-tab="facts" style="background: #374151; color: #9ca3af; border: none; padding: 0.5rem 1rem; cursor: pointer; border-radius: 0.25rem 0.25rem 0 0;">Facts</button>
                </div>
                
                <!-- Tab Content -->
                <div class="tab-content active" data-tab="content" style="color: #e5e7eb; line-height: 1.6;">
                    ${content ? content.replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No content available</em>'}
                </div>
                
                <div class="tab-content" data-tab="ideas" style="display: none; color: #e5e7eb; line-height: 1.6;">
                    ${ideas ? ideas.replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No ideas specified</em>'}
                </div>
                
                <div class="tab-content" data-tab="facts" style="display: none; color: #e5e7eb; line-height: 1.6;">
                    ${facts ? facts.replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No facts specified</em>'}
                </div>
            </div>
        </div>
    `;
}

// Initialize accordion functionality
function initAccordions() {
    document.querySelectorAll('.section-accordion-trigger').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            
            const section = btn.closest('.section');
            const accordionId = btn.getAttribute('aria-controls');
            const content = document.getElementById(accordionId);
            const arrow = btn.querySelector('.section-arrow');
            const expanded = btn.getAttribute('aria-expanded') === 'true';
            
            // Toggle state
            btn.setAttribute('aria-expanded', !expanded);
            
            // Toggle content visibility
            if (content) {
                content.style.display = expanded ? 'none' : 'block';
            }
            
            // Update arrow
            if (arrow) {
                arrow.innerHTML = expanded ? '▼' : '▲';
            }
        });
    });
}

// Initialize reorder buttons
function initReorderButtons() {
    document.querySelectorAll('.reorder-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            
            const sectionId = btn.dataset.sectionId;
            const direction = btn.classList.contains('reorder-up') ? 'up' : 'down';
            
            if (!btn.disabled) {
                moveSection(sectionId, direction);
            }
        });
    });
}

// Initialize tab functionality
function initSectionSelection() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            
            const section = btn.closest('.section');
            const tabName = btn.dataset.tab;
            
            // Update active tab button
            section.querySelectorAll('.tab-btn').forEach(b => {
                b.classList.remove('active');
                b.style.background = '#374151';
                b.style.color = '#9ca3af';
            });
            btn.classList.add('active');
            btn.style.background = '#059669';
            btn.style.color = 'white';
            
            // Update active tab content
            section.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
                content.style.display = 'none';
            });
            section.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
            section.querySelector(`[data-tab="${tabName}"]`).style.display = 'block';
        });
    });
}

// Move section up or down
async function moveSection(sectionId, direction) {
    try {
        console.log(`Moving section ${sectionId} ${direction}`);
        
        const response = await fetch(`/api/sections/${currentPostId}/reorder`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                section_id: sectionId,
                direction: direction
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Reload sections to show new order
        await loadSections(currentPostId);
        
    } catch (error) {
        console.error('Error moving section:', error);
        alert(`Error moving section: ${error.message}`);
    }
} 