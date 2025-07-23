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
            // Fallback to id=22 if endpoint fails
            window.location.href = '/sections?post_id=22';
            return;
        } catch (err) {
            // Fallback to id=22 if fetch fails
            window.location.href = '/sections?post_id=22';
            return;
        }
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
        <div id="sections-sortable-container" class="sections" style="display: flex; flex-direction: column; gap: 2.5rem;">
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
    const heading = section.section_heading || section.title || `Section ${index + 1}`;
    const description = section.section_description || section.description || '';
    const draft = section.draft || '';
    const polished = section.polished || '';
    const ideas = section.ideas_to_include || '';
    const facts = section.facts_to_include || '';
    const highlighting = section.highlighting || '';
    const imageConcepts = section.image_concepts || '';
    const imagePrompts = section.image_prompts || '';
    const watermarking = section.watermarking || '';
    const imageMetaDescriptions = section.image_meta_descriptions || '';
    const imageCaptions = section.image_captions || '';
    const generatedImageUrl = section.generated_image_url || '';
    const status = section.status || 'draft';
    
    // Thumbnail if available
    const thumbnail = generatedImageUrl 
        ? `<img src="${generatedImageUrl}" alt="Section Image" style="width: 32px; height: 32px; object-fit: cover; border-radius: 0.3em; margin-right: 0.75em; border: 2px solid #4ade80; vertical-align: middle;">`
        : '';
    
    return `
        <div class="section" data-section-id="${sectionId}">
            <!-- Section Header Row -->
            <div class="section-header-row" style="display: flex; align-items: flex-start; gap: 1.5rem; padding: 1.5rem 2rem 0 2rem;">
                <!-- Reorder Controls -->
                <div class="section-reorder-controls" style="display: flex; flex-direction: column; gap: 0.5rem; flex-shrink: 0;">
                    <button class="reorder-btn reorder-up" data-section-id="${sectionId}" title="Move Up" 
                            style="background: #059669; color: white; border: none; border-radius: 0.25rem; width: 28px; height: 28px; cursor: pointer; font-size: 12px; ${index === 0 ? 'opacity: 0.5; cursor: not-allowed;' : ''}">
                        ▲
                    </button>
                    <button class="reorder-btn reorder-down" data-section-id="${sectionId}" title="Move Down" 
                            style="background: #059669; color: white; border: none; border-radius: 0.25rem; width: 28px; height: 28px; cursor: pointer; font-size: 12px; ${index === totalSections - 1 ? 'opacity: 0.5; cursor: not-allowed;' : ''}">
                        ▼
                    </button>
                </div>
                
                <!-- Section Number and Thumbnail -->
                <div style="display: flex; align-items: center; flex-shrink: 0; min-width: 3rem;">
                    ${thumbnail}
                    <span style="color: #4ade80; font-weight: bold; font-size: 1.5rem; text-align: center; min-width: 2.5rem;">${index + 1}</span>
                </div>
                
                <!-- Section Checkbox -->
                <div style="flex-shrink: 0; margin: 0 1rem;">
                    <input type="checkbox" class="section-select-checkbox" data-section-id="${sectionId}" style="width: 1.3em; height: 1.3em; cursor: pointer;">
                </div>
                
                <!-- Section Title and Description - CLICKABLE FOR ACCORDION -->
                <div class="section-title-area" style="flex: 1; margin: 0 1.5rem; cursor: pointer;" data-accordion-id="${accordionId}">
                    <h2 style="margin: 0 0 0.75rem 0; color: #7dd3fc; font-size: 1.5rem; font-weight: bold; line-height: 1.3;">${heading}</h2>
                    ${description ? `<p style="margin: 0; color: #b9e0ff; font-size: 1.1rem; line-height: 1.5;">${description}</p>` : ''}
                </div>
                
                <!-- Accordion Toggle -->
                <div style="flex-shrink: 0; margin-left: auto;">
                    <button class="section-accordion-trigger" aria-controls="${accordionId}" aria-expanded="false" 
                            style="background: none; border: none; color: #b9e0ff; cursor: pointer; font-size: 1.5rem; user-select: none; transition: transform 0.2s; padding: 0.5rem;">
                        <span class="section-arrow">▼</span>
                    </button>
                </div>
            </div>
            
            <!-- Section Content (Accordion) -->
            <div id="${accordionId}" class="section-content" style="display: none; padding: 0 2rem 2rem 2rem;">
                <!-- Content Tabs -->
                <div class="section-tabs" style="display: flex; border-bottom: 1px solid #065f46; margin-bottom: 1rem;">
                    <button class="tab-btn active" data-tab="content" style="background: #059669; color: white; border: none; padding: 0.5rem 1rem; cursor: pointer; border-radius: 0.25rem 0.25rem 0 0;">Content</button>
                    <button class="tab-btn" data-tab="ideas" style="background: #374151; color: #9ca3af; border: none; padding: 0.5rem 1rem; cursor: pointer; border-radius: 0.25rem 0.25rem 0 0;">Ideas</button>
                    <button class="tab-btn" data-tab="facts" style="background: #374151; color: #9ca3af; border: none; padding: 0.5rem 1rem; cursor: pointer; border-radius: 0.25rem 0.25rem 0 0;">Facts</button>
                    <button class="tab-btn" data-tab="images" style="background: #374151; color: #9ca3af; border: none; padding: 0.5rem 1rem; cursor: pointer; border-radius: 0.25rem 0.25rem 0 0;">Images</button>
                </div>
                
                <!-- Tab Content -->
                <div class="tab-content active" data-tab="content" style="color: #e5e7eb; line-height: 1.6;">
                    <div style="margin-bottom: 1rem;">
                        <h4 style="color: #7dd3fc; margin-bottom: 0.5rem;">Draft Content:</h4>
                        <div style="background: #1f2937; padding: 1rem; border-radius: 0.5rem; border: 1px solid #374151;">
                            ${draft ? draft.replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No draft content available</em>'}
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <h4 style="color: #7dd3fc; margin-bottom: 0.5rem;">Polished Content:</h4>
                        <div style="background: #1f2937; padding: 1rem; border-radius: 0.5rem; border: 1px solid #374151;">
                            ${polished ? polished.replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No polished content available</em>'}
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <h4 style="color: #7dd3fc; margin-bottom: 0.5rem;">Highlighting:</h4>
                        <div style="background: #1f2937; padding: 1rem; border-radius: 0.5rem; border: 1px solid #374151;">
                            ${highlighting ? highlighting.replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No highlighting available</em>'}
                        </div>
                    </div>
                </div>
                
                <div class="tab-content" data-tab="ideas" style="display: none; color: #e5e7eb; line-height: 1.6;">
                    <div style="margin-bottom: 1rem;">
                        <h4 style="color: #7dd3fc; margin-bottom: 0.5rem;">Ideas to Include:</h4>
                        <div style="background: #1f2937; padding: 1rem; border-radius: 0.5rem; border: 1px solid #374151;">
                            ${ideas ? ideas.replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No ideas specified</em>'}
                        </div>
                    </div>
                </div>
                
                <div class="tab-content" data-tab="facts" style="display: none; color: #e5e7eb; line-height: 1.6;">
                    <div style="margin-bottom: 1rem;">
                        <h4 style="color: #7dd3fc; margin-bottom: 0.5rem;">Facts to Include:</h4>
                        <div style="background: #1f2937; padding: 1rem; border-radius: 0.5rem; border: 1px solid #374151;">
                            ${facts ? facts.replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No facts specified</em>'}
                        </div>
                    </div>
                </div>
                
                <div class="tab-content" data-tab="images" style="display: none; color: #e5e7eb; line-height: 1.6;">
                    <div style="margin-bottom: 1rem;">
                        <h4 style="color: #7dd3fc; margin-bottom: 0.5rem;">Image Concepts:</h4>
                        <div style="background: #1f2937; padding: 1rem; border-radius: 0.5rem; border: 1px solid #374151;">
                            ${imageConcepts ? imageConcepts.replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No image concepts available</em>'}
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <h4 style="color: #7dd3fc; margin-bottom: 0.5rem;">Image Prompts:</h4>
                        <div style="background: #1f2937; padding: 1rem; border-radius: 0.5rem; border: 1px solid #374151;">
                            ${imagePrompts ? imagePrompts.replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No image prompts available</em>'}
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <h4 style="color: #7dd3fc; margin-bottom: 0.5rem;">Watermarking:</h4>
                        <div style="background: #1f2937; padding: 1rem; border-radius: 0.5rem; border: 1px solid #374151;">
                            ${watermarking ? watermarking.replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No watermarking info available</em>'}
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <h4 style="color: #7dd3fc; margin-bottom: 0.5rem;">Image Meta Descriptions:</h4>
                        <div style="background: #1f2937; padding: 1rem; border-radius: 0.5rem; border: 1px solid #374151;">
                            ${imageMetaDescriptions ? imageMetaDescriptions.replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No meta descriptions available</em>'}
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <h4 style="color: #7dd3fc; margin-bottom: 0.5rem;">Image Captions:</h4>
                        <div style="background: #1f2937; padding: 1rem; border-radius: 0.5rem; border: 1px solid #374151;">
                            ${imageCaptions ? imageCaptions.replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No image captions available</em>'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Initialize accordion functionality
function initAccordions() {
    console.log('Initializing accordions...');
    
    // Handle clicks on the title area
    const titleAreas = document.querySelectorAll('.section-title-area');
    console.log('Found title areas:', titleAreas.length);
    
    titleAreas.forEach((titleArea, index) => {
        console.log(`Setting up title area ${index + 1}:`, titleArea);
        titleArea.addEventListener('click', function(e) {
            e.stopPropagation();
            console.log('Title area clicked:', this);
            
            const accordionId = this.getAttribute('data-accordion-id');
            const content = document.getElementById(accordionId);
            const arrow = this.closest('.section').querySelector('.section-arrow');
            const trigger = this.closest('.section').querySelector('.section-accordion-trigger');
            const expanded = trigger.getAttribute('aria-expanded') === 'true';
            
            console.log('Accordion state from title click:', { accordionId, expanded, content: !!content, arrow: !!arrow });
            
            // Toggle state
            trigger.setAttribute('aria-expanded', !expanded);
            
            // Toggle content visibility
            if (content) {
                content.style.display = expanded ? 'none' : 'block';
                console.log('Content display set to:', content.style.display);
            }
            
            // Update arrow
            if (arrow) {
                arrow.innerHTML = expanded ? '▼' : '▲';
                console.log('Arrow updated to:', arrow.innerHTML);
            }
        });
    });
    
    // Handle clicks on the arrow button
    const accordionTriggers = document.querySelectorAll('.section-accordion-trigger');
    console.log('Found accordion triggers:', accordionTriggers.length);
    
    accordionTriggers.forEach((btn, index) => {
        console.log(`Setting up accordion trigger ${index + 1}:`, btn);
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            console.log('Accordion trigger clicked:', this);
            
            const section = btn.closest('.section');
            const accordionId = btn.getAttribute('aria-controls');
            const content = document.getElementById(accordionId);
            const arrow = btn.querySelector('.section-arrow');
            const expanded = btn.getAttribute('aria-expanded') === 'true';
            
            console.log('Accordion state from trigger click:', { accordionId, expanded, content: !!content, arrow: !!arrow });
            
            // Toggle state
            btn.setAttribute('aria-expanded', !expanded);
            
            // Toggle content visibility
            if (content) {
                content.style.display = expanded ? 'none' : 'block';
                console.log('Content display set to:', content.style.display);
            }
            
            // Update arrow
            if (arrow) {
                arrow.innerHTML = expanded ? '▼' : '▲';
                console.log('Arrow updated to:', arrow.innerHTML);
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

// Initialize tab functionality and checkbox selection
function initSectionSelection() {
    // Initialize tab functionality
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
    
    // Initialize checkbox selection
    document.querySelectorAll('.section-select-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSelectedCount();
        });
    });
    
    // Initialize select all checkbox if it exists
    const selectAllCheckbox = document.getElementById('select-all-sections');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            document.querySelectorAll('.section-select-checkbox').forEach(checkbox => {
                checkbox.checked = isChecked;
            });
            updateSelectedCount();
        });
    }
}

// Update the selected count display
function updateSelectedCount() {
    const selectedCheckboxes = document.querySelectorAll('.section-select-checkbox:checked');
    const countElement = document.getElementById('selected-section-count');
    
    if (countElement) {
        countElement.textContent = `${selectedCheckboxes.length} selected`;
    }
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