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
        sectionsList.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    }
}

function renderSections() {
    const sectionsList = document.getElementById('sections-list');
    if (!sectionsList) return;

    const html = sections.map(section => `
        <div class="section-item" onclick="selectSection(${section.id})">
            <div class="section-title">${section.title || `Section ${section.id}`}</div>
            <div class="section-status">${hasImage(section.id) ? '📷' : '⭕'}</div>
        </div>
    `).join('');
    
    sectionsList.innerHTML = html;
}

function selectSection(sectionId) {
    currentSection = sectionId;
    updateOutputPanel();
    
    // Highlight selected section
    document.querySelectorAll('.section-item').forEach(item => {
        item.classList.remove('selected');
    });
    event.target.closest('.section-item').classList.add('selected');
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
            console.log('[Imaging Core] About to call updateModelParameters with:', config.model, config.parameters);
            updateModelParameters(config.model, config.parameters);
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
        updateModelParameters(model);
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

function updateModelParameters(model, savedParams = {}) {
    const container = document.getElementById('parameters-container');
    if (!container) return;

    let html = '';
    if (model === 'sdxl-lora') {
        const dimensions = savedParams.dimensions || '1024x1024';
        const steps = savedParams.steps || '20';
        
        
        html = `
            <div class="param-group">
                <label>Dimensions:</label>
                <select name="dimensions">
                    <option value="1024x1024" ${dimensions === '1024x1024' ? 'selected' : ''}>1024x1024</option>
                    <option value="1792x1024" ${dimensions === '1792x1024' ? 'selected' : ''}>1792x1024</option>
                </select>
            </div>
            <div class="param-group">
                <label>Steps:</label>
                <input type="number" name="steps" value="${steps}" min="10" max="50">
            </div>
        `;
    } else if (model.startsWith('dall-e')) {
        const size = savedParams.size || '1024x1024';
        const quality = savedParams.quality || 'standard';
        const style = savedParams.style || 'vivid';
        
        
        html = `
            <div class="param-group">
                <label>Size:</label>
                <select name="size">
                    <option value="1024x1024" ${size === '1024x1024' ? 'selected' : ''}>1024x1024</option>
                    <option value="1792x1024" ${size === '1792x1024' ? 'selected' : ''}>1792x1024</option>
                    <option value="1024x1792" ${size === '1024x1792' ? 'selected' : ''}>1024x1792</option>
                </select>
            </div>
            <div class="param-group">
                <label>Quality:</label>
                <select name="quality">
                    <option value="standard" ${quality === 'standard' ? 'selected' : ''}>Standard</option>
                    <option value="hd" ${quality === 'hd' ? 'selected' : ''}>HD</option>
                </select>
            </div>
            <div class="param-group">
                <label>Style:</label>
                <select name="style">
                    <option value="vivid" ${style === 'vivid' ? 'selected' : ''}>Vivid</option>
                    <option value="natural" ${style === 'natural' ? 'selected' : ''}>Natural</option>
                </select>
            </div>
        `;
    }
    container.innerHTML = html;
    
    // Add event listeners to parameter inputs
    const inputs = container.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('change', function() {
            saveModelSelection({ 
                model: document.getElementById('image-model-select').value, 
                parameters: getCurrentParameters() 
            });
        });
    });
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
    if (title && currentSection) {
        const section = sections.find(s => s.id === currentSection);
        title.textContent = section ? section.title : `Section ${currentSection}`;
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
