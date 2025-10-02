import { postJSON, getJSON } from './api.js';

export class ImageCaptionsOutputPanel {
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
    document.getElementById('save-btn')?.addEventListener('click', () => this.saveImageCaptions());
    document.getElementById('regenerate-btn')?.addEventListener('click', () => this.generateImageCaptions());

    window.addEventListener('sections:batch-generate', async (e) => {
      console.log('[DEBUG] ImageCaptionsOutputPanel received sections:batch-generate event:', e.detail);
      const ids = e.detail?.ids || [];
      console.log('[DEBUG] Processing batch generation for IDs:', ids);
      for (const id of ids) { 
        console.log(`[DEBUG] Generating image caption for section ${id}`);
        await this.generateImageCaptions(id); 
      }
      
      // Notify sections panel to reload data after batch generation
      console.log('[DEBUG] Batch generation complete, notifying sections panel to reload');
      const reloadEvent = new CustomEvent('sections:reload-data');
      window.dispatchEvent(reloadEvent);
    });
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

    // Display image captions (strict: no fallbacks)
    this.displayImageCaptions(section.image_captions || '');
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

    // Display prompts for all selected sections (strict: no fallbacks)
    this.displayMultipleSectionsPrompts(sections);
  }

  clearDisplay() {
    const promptsDisplay = document.getElementById('image-captions-display');
    if (promptsDisplay) promptsDisplay.style.display = 'none';
  }

  displayMultipleSectionsPrompts(sections) {
    const promptsDisplay = document.getElementById('image-captions-display');
    const promptsContainer = document.getElementById('captions-container');
    promptsContainer.innerHTML = '';

    sections.forEach((section) => {
      const promptsData = section.image_captions || '';
      if (promptsData.trim() === '') return;
      
      const sectionHeader = document.createElement('div');
      sectionHeader.className = 'section-prompts-header';
      sectionHeader.style.gridColumn = '1 / -1';
      sectionHeader.innerHTML = `
        <h6 style="color: #e2e8f0; margin: 1rem 0 0.5rem 0; padding-bottom: 0.5rem; border-bottom: 1px solid #334155;">
          Section ${section.order}: ${section.title}
        </h6>
      `;
      promptsContainer.appendChild(sectionHeader);
      
      const promptCard = document.createElement('div');
      promptCard.className = 'prompt-card';
      promptCard.dataset.sectionId = section.id;
      promptCard.innerHTML = `
        <div class="prompt-content">
          <div class="prompt-text">${promptsData}</div>
        </div>
      `;
      promptsContainer.appendChild(promptCard);
    });
    
    if (promptsContainer.children.length > 0) {
      promptsDisplay.style.display = 'block';
    } else {
      this.clearDisplay();
    }
  }

  displayImageCaptions(promptsData) {
    const promptsDisplay = document.getElementById('image-captions-display');
    const promptsContainer = document.getElementById('captions-container');
    
    if (!promptsData || promptsData.trim() === '') {
      promptsDisplay.style.display = 'none';
      return;
    }
    
    promptsContainer.innerHTML = `
      <div class="prompt-card">
        <div class="prompt-content">
          <div class="prompt-text">${promptsData}</div>
        </div>
      </div>
    `;
    promptsDisplay.style.display = 'block';
  }


  displayImageAltText(altTextData) {
    const altTextDisplay = document.getElementById('image-alt-text-display');
    const altTextContainer = document.getElementById('alt-text-container');
    
    if (!altTextData || altTextData.trim() === '') {
      if (altTextDisplay) altTextDisplay.style.display = 'none';
      return;
    }
    
    altTextContainer.innerHTML = `
      <div class="alt-text-card">
        <div class="alt-text-content">
          <div class="alt-text-text">${altTextData}</div>
        </div>
      </div>
    `;
    if (altTextDisplay) altTextDisplay.style.display = 'block';
  }

  updateWordCount() {
    // No-op in strict mode
  }

  async saveImageCaptions() {
    // Strict: implement when edit UI is added; no-op for now
  }

  async generateImageCaptions(sectionId = null) {
    const id = sectionId || (this.current?.id);
    if (!id) return;
    
    try {
      const res = await postJSON(`/authoring/api/posts/${this.postId}/sections/${id}/generate-image-captions`, {});
      this.displayImageCaptions(res.image_captions || '(no content)');
      this.displayImageAltText(res.image_alt_text || '(no content)');
    } catch (err) {
      console.error(err);
    }
  }
}
