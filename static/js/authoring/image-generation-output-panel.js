import { postJSON, getJSON } from './api.js';

export class ImageGenerationOutputPanel {
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
      const data = await getJSON(`/planning/api/posts/${this.postId}`);
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
    document.getElementById('save-btn')?.addEventListener('click', () => this.saveImageGeneration());
    document.getElementById('regenerate-btn')?.addEventListener('click', () => this.generateImage());

    // Override the Generate button to call our direct image generation
    document.getElementById('generate-btn')?.addEventListener('click', () => {
      this.handleGenerateButton();
    });

    window.addEventListener('sections:batch-generate', async (e) => {
      console.log('[DEBUG] ImageGenerationOutputPanel received sections:batch-generate event:', e.detail);
      const ids = e.detail?.ids || [];
      console.log('[DEBUG] Processing batch generation for IDs:', ids);
      for (const id of ids) { 
        console.log(`[DEBUG] Generating image for section ${id}`);
        await this.generateImage(id); 
      }
      
      // Notify sections panel to reload data after batch generation
      console.log('[DEBUG] Batch generation complete, notifying sections panel to reload');
      const reloadEvent = new CustomEvent('sections:reload-data');
      window.dispatchEvent(reloadEvent);
    });
  }

  async handleGenerateButton() {
    const generateBtn = document.getElementById('generate-btn');
    if (!generateBtn) return;

    // Show loading state
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';

    try {
      // Get current section
      const currentSection = this.current;
      if (!currentSection || !currentSection.id) {
        throw new Error('No section selected');
      }

      console.log(`[Image Generation] Generating image for section ${currentSection.id}`);
      
      // Call the image generation API directly
      const response = await fetch(`/authoring/api/posts/${this.postId}/sections/${currentSection.id}/generate-image`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('[Image Generation] API response:', result);

      if (result.success) {
        console.log('[Image Generation] Image generated successfully:', result.message);
        
        // Update raw response display
        const rawResponseElement = document.getElementById('raw-llm-response');
        if (rawResponseElement) {
          rawResponseElement.textContent = result.message || 'Image generated successfully';
        }
        
        // Refresh the image display after a short delay
        setTimeout(() => {
          this.displayGeneratedImage(currentSection.id);
        }, 1000);
        
      } else {
        throw new Error(result.error || 'Image generation failed');
      }

    } catch (error) {
      console.error('[Image Generation] Error:', error);
      
      // Update raw response display with error
      const rawResponseElement = document.getElementById('raw-llm-response');
      if (rawResponseElement) {
        rawResponseElement.textContent = `Error: ${error.message}`;
      }
      
    } finally {
      // Reset button state
      generateBtn.disabled = false;
      generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate';
    }
  }

  show(section) {
    this.current = section || null;
    if (!section) return;

    document.getElementById('current-section-title').textContent = section.title || 'Untitled';
    document.getElementById('section-title-display').textContent = section.title || '';
    document.getElementById('section-subtitle-display').textContent = section.subtitle || '';
    document.getElementById('section-topics-display').innerHTML = (section.topics||[]).map(t=>`<span class="topic-tag">${t}</span>`).join('');

    document.getElementById('preview-btn').disabled = false;
    document.getElementById('save-btn').disabled = false;
    document.getElementById('regenerate-btn').disabled = false;

    // Display generated image for the section
    this.displayGeneratedImage(section.id);
  }

  showMultiple(sections) {
    if (!sections || sections.length === 0) {
      this.clearDisplay();
      return;
    }

    if (sections.length === 1) {
      this.show(sections[0]);
      return;
    }

    // Display multiple sections
    document.getElementById('current-section-title').textContent = `${sections.length} sections selected`;
    document.getElementById('section-title-display').textContent = '';
    document.getElementById('section-subtitle-display').textContent = '';
    document.getElementById('section-topics-display').innerHTML = '';

    document.getElementById('preview-btn').disabled = false;
    document.getElementById('save-btn').disabled = false;
    document.getElementById('regenerate-btn').disabled = false;

    // Display images for all selected sections
    this.displayMultipleSectionsImages(sections);
  }

  clearDisplay() {
    const imageDisplay = document.getElementById('image-generation-display');
    if (imageDisplay) imageDisplay.style.display = 'none';
  }

  displayGeneratedImage(sectionId) {
    const imageDisplay = document.getElementById('image-generation-display');
    const imageContainer = document.getElementById('generated-image-container');
    
    if (!imageDisplay || !imageContainer) return;
    
    // Construct the image path
    const imagePath = `/static/content/posts/${this.postId}/sections/${sectionId}/raw/${sectionId}.png`;
    
    // Check if image exists by trying to load it
    const img = new Image();
    img.onload = () => {
      // Image exists, display it
      imageContainer.innerHTML = `
        <img src="${imagePath}" alt="Generated image for section ${sectionId}" />
      `;
      imageDisplay.style.display = 'block';
    };
    img.onerror = () => {
      // Image doesn't exist, show message
      imageContainer.innerHTML = `
        <div class="no-image-message">
          No generated image found for this section.<br>
          Click "Regenerate" to generate an image.
        </div>
      `;
      imageDisplay.style.display = 'block';
    };
    img.src = imagePath;
  }

  displayMultipleSectionsImages(sections) {
    const imageDisplay = document.getElementById('image-generation-display');
    const imageContainer = document.getElementById('generated-image-container');
    
    if (!imageDisplay || !imageContainer) return;
    
    imageContainer.innerHTML = '';
    
    sections.forEach((section) => {
      const imagePath = `/static/content/posts/${this.postId}/sections/${section.id}/raw/${section.id}.png`;
      
      const sectionDiv = document.createElement('div');
      sectionDiv.className = 'section-image-container';
      sectionDiv.style.marginBottom = '1rem';
      sectionDiv.style.padding = '1rem';
      sectionDiv.style.border = '1px solid #334155';
      sectionDiv.style.borderRadius = '8px';
      
      const sectionHeader = document.createElement('h6');
      sectionHeader.style.color = '#e2e8f0';
      sectionHeader.style.margin = '0 0 0.5rem 0';
      sectionHeader.style.paddingBottom = '0.5rem';
      sectionHeader.style.borderBottom = '1px solid #334155';
      sectionHeader.textContent = `Section ${section.order}: ${section.title}`;
      sectionDiv.appendChild(sectionHeader);
      
      const img = new Image();
      img.onload = () => {
        const imgElement = document.createElement('img');
        imgElement.src = imagePath;
        imgElement.alt = `Generated image for section ${section.id}`;
        imgElement.style.maxWidth = '100%';
        imgElement.style.maxHeight = '300px';
        imgElement.style.borderRadius = '8px';
        imgElement.style.border = '1px solid #334155';
        sectionDiv.appendChild(imgElement);
      };
      img.onerror = () => {
        const noImageDiv = document.createElement('div');
        noImageDiv.className = 'no-image-message';
        noImageDiv.style.padding = '1rem';
        noImageDiv.style.textAlign = 'center';
        noImageDiv.style.color = '#94a3b8';
        noImageDiv.style.fontStyle = 'italic';
        noImageDiv.textContent = 'No generated image found for this section';
        sectionDiv.appendChild(noImageDiv);
      };
      img.src = imagePath;
      
      imageContainer.appendChild(sectionDiv);
    });
    
    imageDisplay.style.display = 'block';
  }

  updateWordCount() {
    // No-op in strict mode
  }

  async saveImageGeneration() {
    // No-op for now - images are automatically saved
  }

  async generateImage(sectionId = null) {
    const id = sectionId || (this.current?.id);
    if (!id) return;
    
    try {
      console.log(`Generating image for section ${id}`);
      const res = await postJSON(`/authoring/api/posts/${this.postId}/sections/${id}/generate-image`, {});
      
      if (res.success) {
        // Refresh the display to show the newly generated image
        this.displayGeneratedImage(id);
        console.log('Image generated successfully:', res.message);
      } else {
        console.error('Image generation failed:', res.error);
      }
    } catch (err) {
      console.error('Error generating image:', err);
    }
  }
}
