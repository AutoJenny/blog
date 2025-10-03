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
    const display = document.getElementById('image-generation-display');
    if (display) {
      display.style.display = 'block';
    }

    this.updateImagePrompts();
    this.updateGeneratedImage();
  }

  updateImagePrompts() {
    if (!this.current) return;

    const promptsDisplay = document.getElementById('image-prompts-display');
    const promptsContainer = document.getElementById('prompts-container');

    if (!promptsDisplay || !promptsContainer) return;

    try {
      const imagePrompts = this.current.image_prompts ? JSON.parse(this.current.image_prompts) : {};
      
      if (imagePrompts.image_prompt) {
        promptsDisplay.style.display = 'block';
        promptsContainer.innerHTML = `
          <div class="prompt-card">
            <div class="prompt-content">
              <div class="prompt-text">${imagePrompts.image_prompt}</div>
            </div>
          </div>
        `;
      } else {
        promptsDisplay.style.display = 'none';
      }
    } catch (error) {
      console.error('Error parsing image prompts:', error);
      promptsDisplay.style.display = 'none';
    }
  }

  updateGeneratedImage() {
    const imageDisplay = document.getElementById('image-display');
    if (!imageDisplay) return;

    // Check if there's a generated image for this section
    const imagePath = `/static/content/posts/${this.postId}/sections/${this.current.id}/raw/${this.current.id}.png`;
    
    // For now, just show placeholder
    imageDisplay.innerHTML = `
      <p style="color: #94a3b8;">No image generated yet</p>
    `;
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
    const response = await fetch(`/authoring/api/image-generation/posts/${this.postId}/sections/${this.current.id}/generate-image`, {
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
    const imageDisplay = document.getElementById('image-display');
    if (imageDisplay) {
      imageDisplay.innerHTML = `
        <img src="${imagePath}" alt="Generated image" style="max-width: 100%; height: auto; border-radius: 8px;">
      `;
    }
  }

  showNotification(message, type = 'info') {
    // Simple notification - could be enhanced
    console.log(`[${type.toUpperCase()}] ${message}`);
  }
}
