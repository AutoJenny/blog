// Imaging Core JavaScript - Streamlined Essential Functionality
// Consolidated from 6 files (1,477 lines) into 1 file (100 lines)

console.log('Imaging Core loaded');

// Core state
let currentPostId = null;
let currentSection = null;
let sections = [];

// Initialize core functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Imaging Core] Initializing');
    console.log('[Imaging Core] Post ID:', window.postId);
    
    currentPostId = window.postId;
    if (currentPostId) {
        console.log('[Imaging Core] Loading sections and setting up model selection');
        loadSections();
        setupModelSelection();
    } else {
        console.error('[Imaging Core] No post ID found');
    }
});

// Sections management
async function loadSections() {
    const sectionsList = document.getElementById('sections-list');
    if (!sectionsList) return;

    try {
        sectionsList.innerHTML = '<div class="loading">Loading sections...</div>';
        
        const response = await fetch(`/imaging/api/posts/${currentPostId}/sections`);
        const data = await response.json();
        
        if (data.success) {
            sections = data.sections;
            renderSections();
        } else {
            throw new Error(data.error || 'Failed to load sections');
        }
    } catch (error) {
        console.error('Error loading sections:', error);
        const sectionsList = document.getElementById('sections-list');
        if (sectionsList) {
            sectionsList.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        }
    }
}

function renderSections() {
    const sectionsList = document.getElementById('sections-list');
    if (!sectionsList) return;

    const html = sections.map(section => {
        // Determine effective status
        const effectiveStatus = (section.section_text && section.section_text.trim()) ? 'complete' : 'draft';
        
        // Get topics array
        const topics = section.topics || [];
        
        // Get progress (simplified for imaging)
        const progress = effectiveStatus === 'complete' ? 100 : 0;
        
        // Parse selected image concept
        let selectedConceptDisplay = '';
        let selectedConceptId = section.selected_image_concept || '';
        
        if (section.image_concepts && section.image_concepts.trim()) {
            try {
                const conceptsData = JSON.parse(section.image_concepts);
                if (conceptsData.concepts && Array.isArray(conceptsData.concepts)) {
                    // If no concept is selected, auto-select the first one
                    if (!selectedConceptId && conceptsData.concepts.length > 0) {
                        selectedConceptId = conceptsData.concepts[0].concept_id;
                    }
                    
                    // Find the selected concept and build full display
                    const selectedConcept = conceptsData.concepts.find(c => c.concept_id === selectedConceptId);
                    if (selectedConcept) {
                        selectedConceptDisplay = `${selectedConcept.concept_title}
${selectedConcept.concept_description}
Mood: ${selectedConcept.concept_mood}
Key Elements: ${selectedConcept.key_visual_elements}`;
                    }
                }
            } catch (e) {
                // If JSON parsing fails, keep the original selected_image_concept value
                selectedConceptDisplay = selectedConceptId;
            }
        }
        
        return `
            <div class="section-item accordion" data-section-id="${section.id}" data-status="${effectiveStatus}">
                <div class="section-header accordion-header">
                    <input type="checkbox" class="section-checkbox" data-section-id="${section.id}">
                    <span class="section-number">${section.section_order || section.order}</span>
                    <span class="section-title">${section.section_heading || section.title || 'Section'}</span>
                    <span class="section-status ${effectiveStatus}">${effectiveStatus.charAt(0).toUpperCase() + effectiveStatus.slice(1)}</span>
                    <span class="accordion-toggle">▼</span>
                </div>
                <div class="section-content accordion-content">
                    ${section.section_description ? `<div class="section-subtitle">${section.section_description}</div>` : ''}
                    ${section.section_text ? `<div class="section-text-preview">${section.section_text}</div>` : ''}
                    <div class="section-topics">${topics.map(topic => `<span class="topic-tag">${topic}</span>`).join('')}</div>
                    ${selectedConceptDisplay ? `<div class="section-selected-concept"><div class="concept-label">Selected Concept:</div><div class="concept-details">${selectedConceptDisplay}</div></div>` : ''}
                    <div class="section-progress">
                        <div class="progress-bar"><div class="progress-fill" style="width:${progress}%"></div></div>
                        <span class="progress-text">${progress}% complete</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    sectionsList.innerHTML = html;
    
    // Add event listeners for accordion functionality
    setupAccordionListeners();
    setupSectionControls();
}

function setupAccordionListeners() {
    const sectionsList = document.getElementById('sections-list');
    if (!sectionsList) return;

    // Accordion toggle functionality
    sectionsList.addEventListener('click', (e) => {
        if (e.target.classList.contains('accordion-toggle')) {
            const accordion = e.target.closest('.accordion');
            const content = accordion.querySelector('.accordion-content');
            const toggle = e.target;
            
            if (content.style.display === 'none' || content.style.display === '') {
                content.style.display = 'block';
                toggle.textContent = '▲';
                accordion.classList.add('expanded');
            } else {
                content.style.display = 'none';
                toggle.textContent = '▼';
                accordion.classList.remove('expanded');
            }
        }
    });

    // Section selection functionality
    sectionsList.addEventListener('click', (e) => {
        const row = e.target.closest('.section-item');
        if (row && e.target.type !== 'checkbox' && !e.target.classList.contains('accordion-toggle')) {
            selectSection(row.dataset.sectionId);
        }
    });

    // Checkbox functionality
    sectionsList.addEventListener('change', (e) => {
        if (e.target.classList.contains('section-checkbox')) {
            const sectionId = e.target.dataset.sectionId;
            if (e.target.checked) {
                selectSection(sectionId);
            }
        }
    });
}

function setupSectionControls() {
    // Filter buttons
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all buttons
            filterButtons.forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            
            const filter = this.getAttribute('data-filter');
            filterSections(filter);
        });
    });
    
    // Control buttons
    const selectAllBtn = document.getElementById('select-all-btn');
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function() {
            // Select all sections logic
            console.log('[Imaging Core] Select all sections');
        });
    }
    
    const batchGenerateBtn = document.getElementById('batch-generate-btn');
    if (batchGenerateBtn) {
        batchGenerateBtn.addEventListener('click', () => startBatchImageGeneration());
    }
}

function filterSections(filter) {
    const sectionItems = document.querySelectorAll('.section-item');
    sectionItems.forEach(item => {
        // For now, show all sections regardless of filter
        // This can be enhanced later with actual filtering logic
        item.style.display = 'block';
    });
}

function selectSection(sectionId) {
    console.log('[Imaging Core] Section selected:', sectionId);
    currentSection = sectionId;
    
    // Highlight selected section
    document.querySelectorAll('.section-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    const selectedSection = document.querySelector(`[data-section-id="${sectionId}"]`);
    if (selectedSection) {
        selectedSection.classList.add('selected');
    }
    
    updateOutputPanel();
    
    // Dispatch custom event for other components to listen to
    const event = new CustomEvent('sectionSelected', {
        detail: { sectionId: sectionId }
    });
    document.dispatchEvent(event);
    console.log('[Imaging Core] Dispatched sectionSelected event for:', sectionId);
}

function hasImage(sectionId) {
    // Check if section has an image in its raw directory
    return false; // Simplified for now
}

// Model selection with database persistence
function setupModelSelection() {
    const dropdown = document.getElementById('image-model-select');
    if (!dropdown) {
        console.error('[Imaging Core] Model selection dropdown not found');
        return;
    }

    console.log('[Imaging Core] Setting up model selection');

    // Load saved model selection
    loadModelSelection().then(config => {
        console.log('[Imaging Core] Loaded model config:', config);
        if (config.model) {
            dropdown.value = config.model;
            console.log('[Imaging Core] Model config loaded:', config.model, config.parameters);
            // updateModelParameters removed - using template HTML with LoRA controls
            updateTitle(config.model);
            console.log('[Imaging Core] Set dropdown to:', config.model);
            console.log('[Imaging Core] Dropdown value after setting:', dropdown.value);
            
            // Check if something is changing it
            setTimeout(() => {
                console.log('[Imaging Core] Dropdown value after 1 second:', dropdown.value);
            }, 1000);
        }
    });

    // Save on change
    dropdown.addEventListener('change', function() {
        const model = this.value;
        console.log('[Imaging Core] Model changed to:', model);
        // updateModelParameters removed - using template HTML with LoRA controls
        updateTitle(model);
        saveModelSelection({ model, parameters: getCurrentParameters() });
    });
}

async function loadModelSelection() {
    try {
        const response = await fetch('/imaging/api/model-selection');
        const data = await response.json();
        return data.success ? data : { model: 'sdxl-lora', parameters: {} };
    } catch (error) {
        console.error('Error loading model selection:', error);
        return { model: 'sdxl-lora', parameters: {} };
    }
}

async function saveModelSelection(config) {
    try {
        await fetch('/imaging/api/model-selection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        console.log('[Model Selection] Saved:', config);
    } catch (error) {
        console.error('Error saving model selection:', error);
    }
}


function updateTitle(model) {
    const titleElement = document.getElementById('model-title');
    if (titleElement) {
        const modelNames = {
            'sdxl-lora': 'SDXL LoRA',
            'dall-e-3': 'DALL-E 3',
            'dall-e-2': 'DALL-E 2'
        };
        titleElement.textContent = `Model Selection: ${modelNames[model] || model}`;
    }
}

function getCurrentParameters() {
    const params = {};
    const inputs = document.querySelectorAll('#parameters-container input, #parameters-container select');
    inputs.forEach(input => {
        if (input.name && input.value) {
            params[input.name] = input.value;
        }
    });
    return params;
}

// =========================
// Batch Image Generation
// =========================
let batchCancelRequested = false;

async function startBatchImageGeneration() {
    try {
        const batchBtn = document.getElementById('batch-generate-btn');
        if (batchBtn) {
            batchBtn.disabled = true;
            batchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        }

        // Determine the list of sections to process (all sections in this stage)
        const ids = (sections || []).map(s => s.id);
        if (!ids.length) {
            console.warn('[Imaging Core] No sections to batch generate');
            if (batchBtn) {
                batchBtn.disabled = false;
                batchBtn.innerHTML = '<i class="fas fa-magic"></i> Generate All';
            }
            return;
        }

        showBatchProgressModal(ids.length);
        batchCancelRequested = false;

        let successCount = 0;
        let errorCount = 0;

        // Load current model and parameters once
        const modelSelect = document.getElementById('image-model-select');
        const modelName = modelSelect ? modelSelect.value : 'sdxl-lora';
        const parameters = getCurrentParameters();

        // Fetch fresh section data (to get latest prompts)
        const fresh = await fetch(`/imaging/api/posts/${currentPostId}/sections`).then(r => r.json());
        const byId = new Map();
        if (fresh && fresh.success && Array.isArray(fresh.sections)) {
            fresh.sections.forEach(s => byId.set(s.id, s));
        }

        for (let i = 0; i < ids.length; i++) {
            if (batchCancelRequested) break;
            const id = ids[i];
            const section = byId.get(id) || (sections || []).find(s => s.id === id);

            updateBatchProgress(i + 1, ids.length, id, 'generating');

            try {
                // Resolve prompt for this section
                let imagePrompt = '';
                if (section && section.image_prompts) {
                    try {
                        const parsed = JSON.parse(section.image_prompts);
                        imagePrompt = parsed.image_prompt || '';
                    } catch (_) { /* ignore */ }
                }

                if (!imagePrompt) {
                    throw new Error('No image prompt found for section');
                }

                // Call imaging generation API sequentially
                const resp = await fetch(`/imaging/api/image-generation/posts/${currentPostId}/sections/${id}/generate-image`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model_name: modelName,
                        parameters,
                        image_prompt: imagePrompt
                    })
                });

                if (!resp.ok) {
                    throw new Error('HTTP ' + resp.status);
                }
                const data = await resp.json();
                if (!data.success) {
                    throw new Error(data.error || 'Unknown error');
                }

                successCount++;
                updateBatchProgress(i + 1, ids.length, id, 'completed');
            } catch (err) {
                console.error('[Imaging Core] Batch generation error for section', id, err);
                errorCount++;
                updateBatchProgress(i + 1, ids.length, id, 'error', err?.message || String(err));
            }
        }

        completeBatchGeneration(successCount, errorCount);
    } finally {
        const batchBtn = document.getElementById('batch-generate-btn');
        if (batchBtn) {
            batchBtn.disabled = false;
            batchBtn.innerHTML = '<i class="fas fa-magic"></i> Generate All';
        }
    }
}

function showBatchProgressModal(total) {
    // Create or reuse modal
    let modal = document.getElementById('imaging-batch-progress-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'imaging-batch-progress-modal';
        modal.innerHTML = `
            <div class="batch-progress-modal">
              <div class="batch-progress-content">
                <div class="batch-progress-header">
                  <h3>Generating Images</h3>
                  <button id="imaging-cancel-batch-btn" class="btn btn-secondary btn-sm">Cancel</button>
                </div>
                <div class="batch-progress-body">
                  <div class="progress-row">
                    <span id="imaging-progress-text">Starting...</span>
                  </div>
                  <div id="imaging-progress-list" class="progress-list"></div>
                </div>
              </div>
            </div>`;
        document.body.appendChild(modal);

        // Minimal styles (scoped)
        if (!document.getElementById('imaging-batch-progress-styles')) {
            const style = document.createElement('style');
            style.id = 'imaging-batch-progress-styles';
            style.textContent = `
              .batch-progress-modal{position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;z-index:9999}
              .batch-progress-content{background:#0f172a;border:1px solid #334155;border-radius:8px;max-width:700px;width:90%;padding:1rem}
              .batch-progress-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:.5rem}
              .batch-progress-header h3{color:#e2e8f0;margin:0}
              .batch-progress-body{color:#94a3b8;font-size:.9rem}
              .progress-row{margin:.5rem 0}
              .progress-list{max-height:300px;overflow:auto;border-top:1px solid #334155;margin-top:.5rem;padding-top:.5rem}
              .progress-item{display:flex;justify-content:space-between;padding:.25rem 0;border-bottom:1px dashed #334155}
              .status-ok{color:#10b981}
              .status-err{color:#ef4444}
            `;
            document.head.appendChild(style);
        }

        document.getElementById('imaging-cancel-batch-btn').addEventListener('click', () => {
            batchCancelRequested = true;
            document.getElementById('imaging-progress-text').textContent = 'Cancelling...';
        });
    }

    document.getElementById('imaging-progress-text').textContent = `Generating for ${total} sections...`;
    document.getElementById('imaging-progress-list').innerHTML = '';
}

function updateBatchProgress(currentIndex, total, sectionId, status, error = null) {
    const list = document.getElementById('imaging-progress-list');
    const row = document.createElement('div');
    row.className = 'progress-item';
    const label = `Section ${sectionId} (${currentIndex}/${total})`;
    const statusHtml = status === 'completed' ? `<span class="status-ok">done</span>`
                    : status === 'generating' ? `<span>generating...</span>`
                    : `<span class="status-err">error: ${error || ''}</span>`;
    row.innerHTML = `<span>${label}</span>${statusHtml}`;
    list.appendChild(row);
    document.getElementById('imaging-progress-text').textContent = `${currentIndex}/${total} processed`;
}

function completeBatchGeneration(successCount, errorCount) {
    document.getElementById('imaging-progress-text').textContent = `Batch complete: ${successCount} successful, ${errorCount} errors`;
    // Auto-close modal after short delay
    setTimeout(() => {
        const modal = document.getElementById('imaging-batch-progress-modal');
        if (modal && modal.parentNode) modal.parentNode.removeChild(modal);
    }, 1500);
}

// Output panel
function updateOutputPanel() {
    const title = document.getElementById('current-section-title');
    const imageDisplayArea = document.getElementById('image-display-area');
    
    if (title && currentSection) {
        const section = sections.find(s => s.id === currentSection);
        title.textContent = section ? (section.section_heading || section.title || `Section ${currentSection}`) : `Section ${currentSection}`;
        
        // Check for images in the section's raw directory
        if (imageDisplayArea) {
            const imagePath = `/static/content/posts/${window.postId}/sections/${currentSection}/raw/${currentSection}.png`;
            
            // Create image element to test if it exists
            const img = new Image();
            img.onload = function() {
                // Image exists, display it
                imageDisplayArea.innerHTML = `
                    <div style="text-align: center;">
                        <img src="${imagePath}" alt="Section ${currentSection} image" class="section-image">
                        <div class="image-info">
                            <p><strong>Image Path:</strong> ${imagePath}</p>
                            <p><strong>Section:</strong> ${currentSection}</p>
                        </div>
                    </div>
                `;
            };
            img.onerror = function() {
                // Image doesn't exist, show no image message
                imageDisplayArea.innerHTML = `
                    <div class="no-selection-message">
                        <i class="fas fa-image" style="font-size: 3rem; color: #64748b; margin-bottom: 1rem;"></i>
                        <p style="color: #94a3b8; font-size: 1.1rem;">No image generated yet for this section</p>
                        <p style="color: #64748b; font-size: 0.9rem;">Expected path: ${imagePath}</p>
                    </div>
                `;
            };
            img.src = imagePath;
        }
    }
}

// Generate image - handled by ImageGenerationHandler
// function generateImage() {
//     if (!currentSection) {
//         alert('Please select a section first');
//         return;
//     }
//     
//     const model = document.getElementById('image-model-select').value;
//     const parameters = getCurrentParameters();
//     
//     console.log('Generating image for section', currentSection, 'with model', model, 'parameters', parameters);
//     // Image generation logic would go here
// }

// Make functions globally available
window.selectSection = selectSection;
// window.generateImage = generateImage; // Handled by ImageGenerationHandler
