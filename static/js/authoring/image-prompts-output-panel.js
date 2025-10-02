import { postJSON, getJSON } from './api.js';

export class ImagePromptsOutputPanel {
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
    document.getElementById('save-btn')?.addEventListener('click', () => this.saveImagePrompts());
    document.getElementById('regenerate-btn')?.addEventListener('click', () => this.generateImagePrompts());

    window.addEventListener('sections:batch-generate', async (e) => {
      console.log('[DEBUG] ImagePromptsOutputPanel received sections:batch-generate event:', e.detail);
      const ids = e.detail?.ids || [];
      console.log('[DEBUG] Processing batch generation for IDs:', ids);
      for (const id of ids) { 
        console.log(`[DEBUG] Generating image prompt for section ${id}`);
        await this.generateImagePrompts(id); 
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

    const editor = document.getElementById('content-editor');
    editor.disabled = false;
    document.getElementById('preview-btn').disabled = false;
    document.getElementById('save-btn').disabled = false;
    document.getElementById('regenerate-btn').disabled = false;

    // Display image prompts - try structured display first, fallback to textarea
    this.displayImagePrompts(section.image_prompts || '');
    this.updateWordCount();
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

    const editor = document.getElementById('content-editor');
    editor.disabled = false;
    document.getElementById('preview-btn').disabled = false;
    document.getElementById('save-btn').disabled = false;
    document.getElementById('regenerate-btn').disabled = false;

    // Display prompts for all selected sections
    this.displayMultipleSectionsPrompts(sections);
    this.updateWordCount();
  }

  clearDisplay() {
    const promptsDisplay = document.getElementById('image-prompts-display');
    const fallbackEditor = document.getElementById('content-editor-fallback');
    
    promptsDisplay.style.display = 'none';
    fallbackEditor.style.display = 'none';
  }

  displayMultipleSectionsPrompts(sections) {
    console.log('[DEBUG] displayMultipleSectionsPrompts called with data length:', sections?.length || 0);
    const promptsDisplay = document.getElementById('image-prompts-display');
    const promptsContainer = document.getElementById('prompts-container');
    const fallbackEditor = document.getElementById('content-editor-fallback');

    promptsContainer.innerHTML = '';

    let hasAnyPrompts = false;
    let allPromptsText = '';

    sections.forEach((section, sectionIndex) => {
      const promptsData = section.image_prompts || '';
      
      if (promptsData.trim() === '') return;

      try {
        // Try to parse as JSON
        const parsed = JSON.parse(promptsData);
        
        if (parsed.image_prompt) {
          // Add section header
          const sectionHeader = document.createElement('div');
          sectionHeader.className = 'section-prompts-header';
          sectionHeader.style.gridColumn = '1 / -1'; // Span full width
          sectionHeader.innerHTML = `
            <h6 style="color: #e2e8f0; margin: 1rem 0 0.5rem 0; padding-bottom: 0.5rem; border-bottom: 1px solid #334155;">
              Section ${section.order}: ${section.title}
            </h6>
          `;
          promptsContainer.appendChild(sectionHeader);

          // Add prompt display for this section
          const promptCard = document.createElement('div');
          promptCard.className = 'prompt-card';
          promptCard.dataset.sectionId = section.id;
          
          // Display the full image_prompt (which includes style guidelines and dimensions)
          const fullPrompt = parsed.image_prompt || parsed.base_concept || 'No prompt available';
          
          promptCard.innerHTML = `
            <div class="prompt-content">
              <div class="prompt-text">${fullPrompt}</div>
            </div>
          `;
          
          promptsContainer.appendChild(promptCard);
          hasAnyPrompts = true;
        } else {
          // Not structured JSON, add to text
          allPromptsText += `\n\n--- Section ${section.order}: ${section.title} ---\n${promptsData}`;
        }
      } catch (e) {
        // Not valid JSON, add to text
        allPromptsText += `\n\n--- Section ${section.order}: ${section.title} ---\n${promptsData}`;
      }
    });

    if (hasAnyPrompts) {
      promptsDisplay.style.display = 'block';
      fallbackEditor.style.display = 'none';
    } else if (allPromptsText) {
      // Fallback to textarea display
      const editor = document.getElementById('content-editor');
      editor.value = allPromptsText;
      promptsDisplay.style.display = 'none';
      fallbackEditor.style.display = 'block';
    } else {
      this.clearDisplay();
    }
  }

  displayImagePrompts(promptsData) {
    console.log('[DEBUG] displayImagePrompts called with data length:', promptsData?.length || 0);
    const promptsDisplay = document.getElementById('image-prompts-display');
    const promptsContainer = document.getElementById('prompts-container');
    const fallbackEditor = document.getElementById('content-editor-fallback');
    const editor = document.getElementById('content-editor');

    if (!promptsData || promptsData.trim() === '') {
      console.log('[DEBUG] No prompts data, hiding displays');
      promptsDisplay.style.display = 'none';
      fallbackEditor.style.display = 'none';
      return;
    }

    try {
      // Try to parse as JSON
      console.log('[DEBUG] Attempting to parse JSON');
      const parsed = JSON.parse(promptsData);
      console.log('[DEBUG] Parsed JSON:', parsed);
      
      if (parsed.image_prompt) {
        console.log('[DEBUG] Valid image_prompt found, rendering display');
        // Display structured prompt
        this.renderPromptCard(parsed);
        promptsDisplay.style.display = 'block';
        fallbackEditor.style.display = 'none';
        return;
      } else {
        console.log('[DEBUG] No image_prompt found in JSON');
      }
    } catch (e) {
      console.log('[DEBUG] JSON parse error:', e);
      // Not valid JSON, fall back to textarea
    }

    // Fallback to textarea display
    console.log('[DEBUG] Falling back to textarea display');
    editor.value = promptsData;
    promptsDisplay.style.display = 'none';
    fallbackEditor.style.display = 'block';
  }

  renderPromptCard(promptData) {
    console.log('[DEBUG] renderPromptCard called with:', promptData);
    const container = document.getElementById('prompts-container');
    console.log('[DEBUG] Container element:', container);
    container.innerHTML = '';

    const promptCard = document.createElement('div');
    promptCard.className = 'prompt-card';
    if (this.current && this.current.id) {
      promptCard.dataset.sectionId = this.current.id;
    }
    
    // Display the full image_prompt (which includes style guidelines and dimensions)
    const fullPrompt = promptData.image_prompt || promptData.base_concept || 'No prompt available';
    
    promptCard.innerHTML = `
      <div class="prompt-content">
        <div class="prompt-text">${fullPrompt}</div>
      </div>
    `;
    
    container.appendChild(promptCard);
  }

  updateWordCount() {
    // This function is primarily for the fallback textarea
    const text = (document.getElementById('content-editor')?.value || '').trim();
    const n = text ? text.split(/\s+/).filter(Boolean).length : 0;
    const wc = document.getElementById('word-count');
    if (wc) wc.textContent = `${n} words`;
  }

  async saveImagePrompts() {
    if (!this.current) return;
    // For now, save the raw content from the fallback editor if visible
    // In future, this would save selected/edited prompts
    const contentEditor = document.getElementById('content-editor');
    const content = contentEditor.value;

    await postJSON(`/authoring/api/posts/${this.postId}/sections/${this.current.id}/save-image-prompts`, { image_prompts: content });
    document.getElementById('last-saved').textContent = `Saved ${new Date().toLocaleTimeString()}`;
  }

  async generateImagePrompts(sectionId = null) {
    const id = sectionId || (this.current?.id);
    if (!id) return;
    const editor = document.getElementById('content-editor');
    editor.value = 'Generating image prompt…';
    editor.disabled = true;

    try {
      const res = await postJSON(`/authoring/api/posts/${this.postId}/sections/${id}/generate-image-prompts`, {});
      this.displayImagePrompts(res.image_prompt || '(no content)');
    } catch (err) {
      this.displayImagePrompts(`Error generating content: ${err.message || err}`);
      console.error(err);
    } finally {
      editor.disabled = false;
      this.updateWordCount();
    }
  }
}
