// Imaging Output Panel - Independent from authoring
import { postJSON, getJSON } from './api.js';

export class ImagingOutputPanel {
  constructor({ postId }) {
    this.postId = postId;
    this.current = null;
    this.cache = new Map();
    this.postData = null;
    this.bind();
    this.loadPostData();
  }

  async loadPostData() {
    try {
      const data = await getJSON(`/imaging/api/posts/${this.postId}`);
      this.postData = data;
      this.updatePostContext();
    } catch (error) {
      console.error('Error loading post data:', error);
    }
  }

  updatePostContext() {
    if (!this.postData || !this.postData.post) return;
    
    const ideaSeedEl = document.getElementById('selected-idea-display');
    const expandedIdeaEl = document.getElementById('expanded-idea-display');
    
    if (ideaSeedEl) {
      ideaSeedEl.textContent = this.postData.post.idea_seed || '-';
    }
    
    if (expandedIdeaEl) {
      expandedIdeaEl.textContent = this.postData.post.expanded_idea || '-';
    }
  }

  bind() {
    // Bind any necessary event listeners
  }

  show(section) {
    console.log('[Output Panel] show() called with:', section);
    this.current = section;
    this.updateSectionContext(section);
    this.showImageGenerationDisplay();
  }

  showMultiple(sections) {
    // Handle multiple section selection if needed
    console.log('Multiple sections selected:', sections);
  }

  updateSectionContext(section) {
    if (!section) return;

    const titleEl = document.getElementById('section-title-display');
    const subtitleEl = document.getElementById('section-subtitle-display');
    const groupEl = document.getElementById('section-group-display');
    const groupSummaryEl = document.getElementById('section-group-summary-display');
    const topicsEl = document.getElementById('section-topics-display');
    const avoidTopicsEl = document.getElementById('avoid-topics-display');

    if (titleEl) titleEl.textContent = section.section_heading || '-';
    if (subtitleEl) subtitleEl.textContent = section.section_description || '-';
    if (groupEl) groupEl.textContent = '-'; // Not available in imaging
    if (groupSummaryEl) groupSummaryEl.textContent = '-'; // Not available in imaging
    if (topicsEl) topicsEl.textContent = '-'; // Not available in imaging
    if (avoidTopicsEl) avoidTopicsEl.textContent = '-'; // Not available in imaging
  }

  showImageGenerationDisplay() {
    this.updateSectionTitle();
    this.updateImageDisplay();
  }

  updateSectionTitle() {
    const titleEl = document.getElementById('current-section-title');
    if (titleEl && this.current) {
      titleEl.textContent = this.current.section_heading || `Section ${this.current.id}`;
    }
  }

  updateImageDisplay() {
    const imageDisplayArea = document.getElementById('image-display-area');
    if (!imageDisplayArea) return;

    if (!this.current) {
      // Show no selection message
      imageDisplayArea.innerHTML = `
        <div class="no-selection-message">
          <i class="fas fa-image" style="font-size: 3rem; color: #64748b; margin-bottom: 1rem;"></i>
          <p style="color: #94a3b8; font-size: 1.1rem;">Select a section to view its generated images</p>
        </div>
      `;
      return;
    }

    // Check if there's a generated image for this section
    const imagePath = `/static/content/posts/${this.postId}/sections/${this.current.id}/raw/${this.current.id}.png`;
    
    // Try to load the image
    const img = new Image();
    img.onload = () => {
      // Image exists, display it
      imageDisplayArea.innerHTML = `
        <div style="text-align: center;">
          <img src="${imagePath}" alt="Generated image" class="section-image">
          <div class="image-info">
            <div><strong>Section:</strong> ${this.current.section_heading || `Section ${this.current.id}`}</div>
            <div class="image-path">${imagePath}</div>
          </div>
        </div>
      `;
    };
    img.onerror = () => {
      // Image doesn't exist, show no image message
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

  async handleGenerateButton() {
    if (!this.current) {
      throw new Error('No section selected');
    }

    console.log(`[Image Generation] Generating image for section ${this.current.id}`);
    
    // Get selected model and parameters
    const modelSelect = document.getElementById('image-model-select');
    const selectedModel = modelSelect ? modelSelect.value : 'sdxl-lora';
    
    // Collect model parameters
    const parameters = {};
    const paramInputs = document.querySelectorAll('#parameters-container select, #parameters-container input');
    paramInputs.forEach(input => {
      if (input.value) {
        parameters[input.name] = input.value;
      }
    });
    
    // Call the image generation API directly
    const response = await fetch(`/imaging/api/image-generation/posts/${this.postId}/sections/${this.current.id}/generate-image`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model_name: selectedModel,
        parameters: parameters
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log('[Image Generation] API response:', result);

    if (result.success) {
      console.log('[Image Generation] Image generated successfully:', result.message);
      
      // Update raw response display
      this.updateDebugDisplay(result);
      
      // Update image display
      this.updateImageDisplay(result.image_path);
      
      // Show success notification
      this.showNotification('Image generated successfully!', 'success');
      
      return result;
    } else {
      throw new Error(result.error || 'Image generation failed');
    }
  }

  updateDebugDisplay(result) {
    const debugEl = document.getElementById('image-generation-debug');
    if (debugEl) {
      debugEl.textContent = JSON.stringify(result, null, 2);
    }
  }

  updateImageDisplay(imagePath) {
    // Refresh the entire image display
    this.updateImageDisplay();
  }

  showNotification(message, type = 'info') {
    // Simple notification - could be enhanced
    console.log(`[${type.toUpperCase()}] ${message}`);
  }
}
