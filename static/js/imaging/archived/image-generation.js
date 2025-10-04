// Imaging Image Generation - Independent from authoring
// Note: Using global functions instead of ES6 modules for better compatibility

function initTabs() {
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanels = document.querySelectorAll('.tab-panel');
  tabButtons.forEach(btn => btn.addEventListener('click', () => {
    const t = btn.getAttribute('data-tab');
    tabButtons.forEach(b => b.classList.remove('active'));
    tabPanels.forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`${t}-tab`)?.classList.add('active');
    localStorage.setItem('imaging-active-tab', t);
  }));
  const saved = localStorage.getItem('imaging-active-tab');
  if (saved) document.querySelector(`.tab-btn[data-tab="${saved}"]`)?.click();
}

document.addEventListener('DOMContentLoaded', () => {
  console.log('[Imaging] DOM loaded, initializing...');
  
  initTabs();

  const postId = window.postId;
  console.log('[Imaging] Post ID:', postId);
  
  // Simple initialization without modules
  initializeImagingComponents(postId);

  // Initialize LLM module immediately on page load
  // Note: LLM module initialization will be handled by the template's JavaScript
  
  // Function to initialize LLM module for current section
  function initializeLLMForSection(sectionId) {
      // LLM module initialization will be handled by the template's JavaScript
      console.log('LLM module initialization for section:', sectionId);
  }
});

// Simple initialization function
function initializeImagingComponents(postId) {
  console.log('[Imaging] Initializing components for post:', postId);
  
  // Initialize sections panel
  initializeSectionsPanel(postId);
  
  // Initialize output panel
  initializeOutputPanel(postId);
}

function initializeSectionsPanel(postId) {
  console.log('[Imaging] Initializing sections panel...');
  
  const refreshBtn = document.getElementById('refresh-sections');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => loadSections(postId));
  }
  
  // Load sections immediately
  loadSections(postId);
}

function initializeOutputPanel(postId) {
  console.log('[Imaging] Initializing output panel...');
  
  // Simple output panel functionality
  window.imagingOutputPanel = {
    show: function(section) {
      console.log('[Output Panel] show() called with:', section);
      updateOutputPanel(section);
    },
    showMultiple: function(sections) {
      console.log('[Output Panel] showMultiple() called with:', sections);
    }
  };
}

function updateOutputPanel(section) {
  const titleEl = document.getElementById('current-section-title');
  const imageDisplayArea = document.getElementById('image-display-area');
  
  if (!titleEl || !imageDisplayArea) {
    console.log('[Output Panel] Required elements not found!');
    return;
  }
  
  if (!section) {
    titleEl.textContent = 'Select a section to view images';
    imageDisplayArea.innerHTML = `
      <div class="no-selection-message">
        <i class="fas fa-image" style="font-size: 3rem; color: #64748b; margin-bottom: 1rem;"></i>
        <p style="color: #94a3b8; font-size: 1.1rem;">Select a section to view its generated images</p>
      </div>
    `;
    return;
  }
  
  // Update title
  titleEl.textContent = section.section_heading || `Section ${section.id}`;
  
  // Check for image
  const imagePath = `/static/content/posts/${window.postId}/sections/${section.id}/raw/${section.id}.png`;
  
  const img = new Image();
  img.onload = () => {
    imageDisplayArea.innerHTML = `
      <div style="text-align: center;">
        <img src="${imagePath}" alt="Generated image" class="section-image">
        <div class="image-info">
          <div><strong>Section:</strong> ${section.section_heading || `Section ${section.id}`}</div>
          <div class="image-path">${imagePath}</div>
        </div>
      </div>
    `;
  };
  img.onerror = () => {
    imageDisplayArea.innerHTML = `
      <div class="no-selection-message">
        <i class="fas fa-image" style="font-size: 3rem; color: #64748b; margin-bottom: 1rem;"></i>
        <p style="color: #94a3b8; font-size: 1.1rem;">No image generated for this section yet</p>
        <p style="color: #64748b; font-size: 0.9rem;">Generate an image using the controls on the left</p>
      </div>
    `;
  };
  img.src = imagePath;
}

async function loadSections(postId) {
  const sectionsList = document.getElementById('sections-list');
  if (!sectionsList) return;

  try {
    sectionsList.innerHTML = `
      <div class="loading-state">
        <i class="fas fa-spinner fa-spin"></i>
        <span>Loading sections...</span>
      </div>
    `;

    const response = await fetch(`/imaging/api/posts/${postId}/sections`);
    const data = await response.json();
    
    if (data.success) {
      renderSections(data.sections);
    } else {
      throw new Error(data.error || 'Failed to load sections');
    }
  } catch (error) {
    console.error('Error loading sections:', error);
    sectionsList.innerHTML = `
      <div class="error-state">
        <i class="fas fa-exclamation-triangle"></i>
        <span>Error loading sections: ${error.message}</span>
      </div>
    `;
  }
}

function renderSections(sections) {
  const sectionsList = document.getElementById('sections-list');
  if (!sectionsList) return;

  if (sections.length === 0) {
    sectionsList.innerHTML = `
      <div class="empty-state">
        <i class="fas fa-info-circle"></i>
        <span>No sections found</span>
      </div>
    `;
    return;
  }

  sectionsList.innerHTML = sections.map(section => `
    <div class="section-item" data-section-id="${section.id}">
      <h4>${section.section_heading || 'Untitled Section'}</h4>
      <p>${section.section_description || 'No description'}</p>
      <div class="section-meta">
        <span class="section-order">${section.section_order}</span>
        <span class="image-status ${hasImage(section) ? 'has-image' : 'no-image'}">
          <i class="fas fa-${hasImage(section) ? 'check-circle' : 'times-circle'}"></i>
          ${hasImage(section) ? 'Has Image' : 'No Image'}
        </span>
      </div>
    </div>
  `).join('');

  // Add click handlers
  sectionsList.querySelectorAll('.section-item').forEach(item => {
    item.addEventListener('click', () => selectSection(item, sections));
  });
}

function hasImage(section) {
  return section.image_prompts && section.image_prompts !== '{}' && section.image_prompts !== 'null';
}

function selectSection(element, sections) {
  console.log('[Sections Panel] Section clicked:', element);
  const sectionId = parseInt(element.dataset.sectionId);
  const section = sections.find(s => s.id === sectionId);
  
  console.log('[Sections Panel] Section ID:', sectionId, 'Section data:', section);
  
  if (!section) {
    console.log('[Sections Panel] Section not found!');
    return;
  }

  // Remove previous selection
  document.querySelectorAll('.section-item').forEach(item => item.classList.remove('selected'));
  
  // Add selection to clicked item
  element.classList.add('selected');
  
  console.log('[Sections Panel] Selected section:', sectionId);
  console.log('[Sections Panel] Calling output panel show with:', section);
  
  // Call output panel
  if (window.imagingOutputPanel) {
    window.imagingOutputPanel.show(section);
  }
}

// Imaging-specific global functions
window.imagingSelectSection = function(sectionId) {
  console.log(`[Imaging] Section selected: ${sectionId}`);
  // This function can be used for section-specific actions in imaging
};

window.imagingGenerateImage = function(sectionId) {
  console.log(`[Imaging] Generate image for section: ${sectionId}`);
  // This function can be used for image generation actions
};
