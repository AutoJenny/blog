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
        batchGenerateBtn.addEventListener('click', function() {
            // Batch generate images logic
            console.log('[Imaging Core] Batch generate images for all sections');
        });
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

// Generate image
function generateImage() {
    if (!currentSection) {
        alert('Please select a section first');
        return;
    }
    
    const model = document.getElementById('image-model-select').value;
    const parameters = getCurrentParameters();
    
    console.log('Generating image for section', currentSection, 'with model', model, 'parameters', parameters);
    // Image generation logic would go here
}

// Make functions globally available
window.selectSection = selectSection;
window.generateImage = generateImage;
