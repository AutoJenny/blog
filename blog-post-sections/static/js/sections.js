// sections.js - Main sections rendering and interaction logic

// Global variables
let currentPostId = null;
let sectionsData = null;

// Iframe Communication Setup for LLM Actions Integration
// Listen for requests from purple panel (LLM Actions)
window.addEventListener('message', (event) => {
    if (event.data.type === 'GET_SELECTED_SECTIONS') {
        console.log('Received GET_SELECTED_SECTIONS request from LLM Actions');
        const selectedIds = getSelectedSectionIds();
        console.log('Sending selected section IDs:', selectedIds);
        event.source.postMessage({
            type: 'SELECTED_SECTIONS_RESPONSE',
            sectionIds: selectedIds
        }, '*');
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
    console.log('Sections.js loaded - DOM Content Loaded event fired');
    
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
        console.log('About to render sections...');
        renderSections(data);
        console.log('Sections rendered');
        
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
        panel.innerHTML = '<p>No sections found for this post.</p>';
        return;
    }
    
    // Add Select All checkbox and selection count
    let selectAllHtml = `
        <div style="display:flex;align-items:center;gap:1em;margin-bottom:1.5em;">
            <input type="checkbox" id="select-all-sections" checked style="width:1.2em;height:1.2em;">
            <label for="select-all-sections" style="color:#7dd3fc;font-size:1.1rem;font-weight:bold;cursor:pointer;">Select All Sections</label>
            <span id="selected-section-count" style="color:#b9e0ff;font-size:1rem;margin-left:1em;">All selected</span>
        </div>
    `;
    
    const containerId = 'sections-sortable-container';
    let sectionsHtml = selectAllHtml + `
        <div id="${containerId}" class="sections" style="display:flex;flex-direction:column;gap:2rem;">
    `;
    
    data.sections.forEach((section, index) => {
        const sectionHtml = renderSection(section, index, data.sections.length);
        sectionsHtml += sectionHtml;
        
        // DEBUG: Check each section as it's added
        console.log(`=== SECTION ${index + 1} ADDED DEBUG ===`);
        console.log('Section ID:', section.id);
        console.log('Section heading:', section.section_heading || section.title);
        console.log('Current sectionsHtml length:', sectionsHtml.length);
        console.log('Current opening <div class="section":', (sectionsHtml.match(/<div class="section"/g) || []).length);
        console.log('Current closing </div>:', (sectionsHtml.match(/<\/div>/g) || []).length);
        console.log('Current opening divs total:', (sectionsHtml.match(/<div/g) || []).length);
        console.log('Current closing divs total:', (sectionsHtml.match(/<\/div>/g) || []).length);
        console.log('=== END SECTION ${index + 1} ADDED DEBUG ===');
    });
    
    sectionsHtml += '</div>';
    
    // DEBUG: Log the final generated HTML to see if there's malformed structure
    console.log('=== FINAL SECTIONS HTML DEBUG ===');
    console.log('Generated HTML length:', sectionsHtml.length);
    console.log('Number of opening <div class="section":', (sectionsHtml.match(/<div class="section"/g) || []).length);
    console.log('Number of closing </div>:', (sectionsHtml.match(/<\/div>/g) || []).length);
    console.log('Opening divs total:', (sectionsHtml.match(/<div/g) || []).length);
    console.log('Closing divs total:', (sectionsHtml.match(/<\/div>/g) || []).length);
    
    // Check for potential HTML structure issues
    const sectionDivs = sectionsHtml.match(/<div class="section"/g) || [];
    const sectionClosingDivs = sectionsHtml.match(/<\/div>/g) || [];
    const totalOpeningDivs = sectionsHtml.match(/<div/g) || [];
    
    console.log('Section divs count:', sectionDivs.length);
    console.log('Total closing divs:', sectionClosingDivs.length);
    console.log('Total opening divs:', totalOpeningDivs.length);
    
    if (sectionDivs.length !== sectionClosingDivs.length) {
        console.error('WARNING: Mismatch between section divs and closing divs!');
    }
    
    if (totalOpeningDivs.length !== sectionClosingDivs.length) {
        console.error('WARNING: Mismatch between total opening divs and closing divs!');
        console.error('This indicates malformed HTML structure!');
    }
    
    console.log('Full HTML:', sectionsHtml);
    console.log('=== END FINAL DEBUG ===');
    
    panel.innerHTML = sectionsHtml;
    
    // Initialize interactive elements
    initAccordions();
    initReorderButtons();
    initSectionSelection();
    
    // Initialize drag and drop if available
    if (window.sectionDragDrop && data.sections) {
        window.sectionDragDrop.init('sections-sortable-container', currentPostId, data.sections);
    } else {
        // Fallback: initialize drag and drop after a short delay
        setTimeout(() => {
            if (window.sectionDragDrop && data.sections) {
                window.sectionDragDrop.init('sections-sortable-container', currentPostId, data.sections);
            }
        }, 500);
    }
}

// Helper function to escape HTML content
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Render individual section
function renderSection(section, index, totalSections) {
    const sectionId = section.id;
    const accordionId = `section-accordion-${index}`;
    const heading = escapeHtml(section.section_heading || section.title || `Section ${index + 1}`);
    const description = escapeHtml(section.section_description || section.description || '');
    const draft = section.draft || '';
    const polished = section.polished || '';
    const ideas = section.ideas_to_include || '';
    const facts = section.facts_to_include || '';
    const imageConcepts = section.image_concepts || '';
    const imagePrompts = section.image_prompts || '';
    const imageMetaDescriptions = section.image_meta_descriptions || '';
    const imageCaptions = section.image_captions || '';
    const generatedImageUrl = section.generated_image_url || '';
    
    // Add thumbnail if available
    const thumbnail = generatedImageUrl
        ? `<img src="${generatedImageUrl}" alt="Section Image" style="width:32px;height:32px;object-fit:cover;border-radius:0.3em;margin-right:0.75em;border:2px solid #4ade80;vertical-align:middle;">`
        : '';
    
    const sectionHtml = `
        <div class="section" data-section-id="${sectionId}" style="background:#14342b;border-radius:1rem;box-shadow:0 2px 12px #0004;">
            <div style="display:flex;align-items:center;gap:1em;padding:1.2rem 2rem 0 2rem;">
                <input type="checkbox" class="section-select-checkbox" data-section-id="${sectionId}" checked style="width:1.2em;height:1.2em;">
                <button class="section-accordion-trigger" type="button" aria-expanded="false" aria-controls="${accordionId}" style="display:flex;align-items:center;width:100%;background:none;border:none;cursor:pointer;padding:0;text-align:left;">
                    <span class="section-drag-handle" style="cursor:grab;margin-right:1rem;color:#b9e0ff;font-size:1.5rem;user-select:none;">&#x2630;</span>
                    ${thumbnail}
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
            <div id="${accordionId}" style="display:none;padding:0 2rem 2rem 2rem;">
                <div style="color: #e5e7eb;">
                    <!-- Tab Navigation -->
                    <div style="display: flex; border-bottom: 1px solid #374151; margin-bottom: 20px;">
                        <button class="section-tab-btn active" data-tab="research" style="background: #1f2937; color: #7dd3fc; border: none; padding: 10px 20px; cursor: pointer; border-radius: 6px 6px 0 0; margin-right: 2px; font-weight: bold;">Research</button>
                        <button class="section-tab-btn" data-tab="content" style="background: #374151; color: #9ca3af; border: none; padding: 10px 20px; cursor: pointer; border-radius: 6px 6px 0 0; margin-right: 2px;">Content</button>
                        <button class="section-tab-btn" data-tab="image-texts" style="background: #374151; color: #9ca3af; border: none; padding: 10px 20px; cursor: pointer; border-radius: 6px 6px 0 0;">Image Texts</button>
                    </div>
                    
                    <!-- Research Tab -->
                    <div class="section-tab-content active" data-tab="research">
                        <div style="margin-bottom: 20px;">
                            <h4 style="color: #7dd3fc; margin-bottom: 10px;">Ideas to Include:</h4>
                            <div style="background: #1f2937; padding: 15px; border-radius: 6px; border: 1px solid #374151;">
                                ${ideas ? escapeHtml(ideas).replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No ideas specified</em>'}
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 20px;">
                            <h4 style="color: #7dd3fc; margin-bottom: 10px;">Facts to Include:</h4>
                            <div style="background: #1f2937; padding: 15px; border-radius: 6px; border: 1px solid #374151;">
                                ${facts ? escapeHtml(facts).replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No facts specified</em>'}
                            </div>
                        </div>
                    </div>
                    
                    <!-- Content Tab -->
                    <div class="section-tab-content" data-tab="content" style="display: none;">
                        <div style="margin-bottom: 20px;">
                            <h4 style="color: #7dd3fc; margin-bottom: 10px;">Draft Content:</h4>
                            <div style="background: #1f2937; padding: 15px; border-radius: 6px; border: 1px solid #374151;">
                                ${draft ? escapeHtml(draft).replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No draft content available</em>'}
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 20px;">
                            <h4 style="color: #7dd3fc; margin-bottom: 10px;">Polished Content:</h4>
                            <div style="background: #1f2937; padding: 15px; border-radius: 6px; border: 1px solid #374151;">
                                ${polished ? escapeHtml(polished).replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No polished content available</em>'}
                            </div>
                        </div>
                    </div>
                    
                    <!-- Image Texts Tab -->
                    <div class="section-tab-content" data-tab="image-texts" style="display: none;">
                        <div style="margin-bottom: 20px;">
                            <h4 style="color: #7dd3fc; margin-bottom: 10px;">Image Concepts:</h4>
                            <div style="background: #1f2937; padding: 15px; border-radius: 6px; border: 1px solid #374151;">
                                ${imageConcepts ? escapeHtml(imageConcepts).replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No image concepts available</em>'}
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 20px;">
                            <h4 style="color: #7dd3fc; margin-bottom: 10px;">Image Prompts:</h4>
                            <div style="background: #1f2937; padding: 15px; border-radius: 6px; border: 1px solid #374151;">
                                ${imagePrompts ? escapeHtml(imagePrompts).replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No image prompts available</em>'}
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 20px;">
                            <h4 style="color: #7dd3fc; margin-bottom: 10px;">Image Meta Descriptions:</h4>
                            <div style="background: #1f2937; padding: 15px; border-radius: 6px; border: 1px solid #374151;">
                                ${imageMetaDescriptions ? escapeHtml(imageMetaDescriptions).replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No meta descriptions available</em>'}
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 20px;">
                            <h4 style="color: #7dd3fc; margin-bottom: 10px;">Image Captions:</h4>
                            <div style="background: #1f2937; padding: 15px; border-radius: 6px; border: 1px solid #374151;">
                                ${imageCaptions ? escapeHtml(imageCaptions).replace(/\n/g, '<br>') : '<em style="color: #9ca3af;">No image captions available</em>'}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // DEBUG: Log each section's HTML to check for malformed structure
    console.log(`=== SECTION ${index + 1} DEBUG ===`);
    console.log('Section ID:', sectionId);
    console.log('Section HTML length:', sectionHtml.length);
    console.log('Opening divs:', (sectionHtml.match(/<div/g) || []).length);
    console.log('Closing divs:', (sectionHtml.match(/<\/div>/g) || []).length);
    console.log('Section HTML:', sectionHtml);
    console.log(`=== END SECTION ${index + 1} DEBUG ===`);
    
    return sectionHtml;
}

// Initialize accordion functionality
function initAccordions() {
    console.log('Initializing accordions...');
    
    // Load saved accordion states from localStorage
    const storageKey = `sections_accordion_post_${currentPostId}`;
    const savedAccordion = JSON.parse(localStorage.getItem(storageKey) || '{}');
    
    // Section accordions
    document.querySelectorAll('.section-accordion-trigger').forEach(btn => {
        const accId = btn.getAttribute('aria-controls');
        const content = document.getElementById(accId);
        const arrow = btn.querySelector('.section-arrow');
        
        // Apply saved state
        if (savedAccordion[accId] === true) {
            btn.setAttribute('aria-expanded', 'true');
            if (content) content.style.display = 'block';
            if (arrow) arrow.innerHTML = '&#x25B2;'; // ▲
        }
        
        btn.addEventListener('click', function() {
            const expanded = btn.getAttribute('aria-expanded') === 'true';
            btn.setAttribute('aria-expanded', !expanded);
            if (content) {
                content.style.display = expanded ? 'none' : 'block';
            }
            if (arrow) {
                arrow.innerHTML = expanded ? '&#x25BC;' : '&#x25B2;'; // ▼/▲
            }
            
            // Save accordion state
            const currentAccordion = JSON.parse(localStorage.getItem(storageKey) || '{}');
            currentAccordion[accId] = !expanded;
            localStorage.setItem(storageKey, JSON.stringify(currentAccordion));
        });
    });
    
    // Initialize tab functionality
    initTabs();
}

// Initialize tab functionality
function initTabs() {
    console.log('Initializing tabs...');
    
    // Load saved tab states from localStorage
    const storageKey = `sections_tabs_post_${currentPostId}`;
    const savedTabs = JSON.parse(localStorage.getItem(storageKey) || '{}');
    
    // Use event delegation for better performance and to handle dynamically created elements
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('section-tab-btn')) {
            const btn = e.target;
            const tabName = btn.getAttribute('data-tab');
            const accordionId = btn.closest('[id^="section-accordion-"]').id;
            
            console.log('Tab clicked:', tabName, 'in accordion:', accordionId);
            
            switchTab(btn, tabName, accordionId);
            
            // Save tab state
            const currentTabs = JSON.parse(localStorage.getItem(storageKey) || '{}');
            currentTabs[accordionId] = tabName;
            localStorage.setItem(storageKey, JSON.stringify(currentTabs));
        }
    });
    
    // Apply saved states after a short delay to ensure DOM is ready
    setTimeout(() => {
        document.querySelectorAll('.section-tab-btn').forEach(btn => {
            const tabName = btn.getAttribute('data-tab');
            const accordionId = btn.closest('[id^="section-accordion-"]').id;
            
            if (savedTabs[accordionId] === tabName) {
                switchTab(btn, tabName, accordionId);
            }
        });
    }, 100);
}

// Switch tab function
function switchTab(clickedBtn, tabName, accordionId) {
    console.log('Switching to tab:', tabName, 'in accordion:', accordionId);
    
    // Reset all tabs in this accordion
    const accordion = document.getElementById(accordionId);
    if (!accordion) {
        console.error('Accordion not found:', accordionId);
        return;
    }
    
    // Reset all tab buttons in this accordion
    accordion.querySelectorAll('.section-tab-btn').forEach(btn => {
        btn.style.background = '#374151';
        btn.style.color = '#9ca3af';
        btn.classList.remove('active');
    });
    
    // Reset all tab contents in this accordion
    accordion.querySelectorAll('.section-tab-content').forEach(content => {
        content.style.display = 'none';
        content.classList.remove('active');
    });
    
    // Activate clicked tab
    clickedBtn.style.background = '#1f2937';
    clickedBtn.style.color = '#7dd3fc';
    clickedBtn.classList.add('active');
    
    // Show corresponding content
    const content = accordion.querySelector(`.section-tab-content[data-tab="${tabName}"]`);
    if (content) {
        content.style.display = 'block';
        content.classList.add('active');
        console.log('Tab content shown:', tabName);
    } else {
        console.error('Tab content not found for:', tabName);
    }
}

// Initialize reorder buttons (for up/down arrows)
function initReorderButtons() {
    console.log('Initializing reorder buttons...');
    
    document.querySelectorAll('.section-reorder-btn').forEach(btn => {
        btn.addEventListener('click', async function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const sectionId = btn.getAttribute('data-section-id');
            const direction = btn.getAttribute('data-direction');
            
            if (btn.disabled) return;
            
            try {
                await moveSection(sectionId, direction);
                // Reload sections to reflect the new order
                if (currentPostId) {
                    await loadSections(currentPostId);
                }
            } catch (error) {
                console.error('Error reordering section:', error);
            }
        });
    });
}

// Initialize section selection functionality
function initSectionSelection() {
    const selectAll = document.getElementById('select-all-sections');
    const checkboxes = Array.from(document.querySelectorAll('.section-select-checkbox'));
    const countSpan = document.getElementById('selected-section-count');
    
    // Load saved checkbox states from localStorage
    const storageKey = `sections_selection_post_${currentPostId}`;
    const savedSelection = JSON.parse(localStorage.getItem(storageKey) || '{}');
    
    // Apply saved states to checkboxes
    checkboxes.forEach(cb => {
        const sectionId = cb.getAttribute('data-section-id');
        if (savedSelection[sectionId] !== undefined) {
            cb.checked = savedSelection[sectionId];
        }
    });
    
    function updateCount() {
        const selected = checkboxes.filter(cb => cb.checked).length;
        if (selected === checkboxes.length) {
            countSpan.textContent = 'All selected';
        } else if (selected === 0) {
            countSpan.textContent = 'None selected';
        } else {
            countSpan.textContent = `${selected} selected`;
        }
    }
    
    function saveSelection() {
        const selection = {};
        checkboxes.forEach(cb => {
            const sectionId = cb.getAttribute('data-section-id');
            selection[sectionId] = cb.checked;
        });
        localStorage.setItem(storageKey, JSON.stringify(selection));
    }
    
    if (selectAll) {
        selectAll.addEventListener('change', function() {
            checkboxes.forEach(cb => { cb.checked = selectAll.checked; });
            updateCount();
            saveSelection();
        });
    }
    
    checkboxes.forEach(cb => {
        cb.addEventListener('change', function() {
            if (!cb.checked) selectAll.checked = false;
            else if (checkboxes.every(c => c.checked)) selectAll.checked = true;
            updateCount();
            saveSelection();
        });
    });
    
    updateCount();
}

// Move section up or down (legacy function for up/down buttons)
async function moveSection(sectionId, direction) {
    try {
        console.log(`Moving section ${sectionId} ${direction}`);
        
        const response = await fetch(`/api/sections/reorder`, {
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