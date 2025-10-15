// Image Concepts Output Panel - Non-module global implementation
// Provides: window.ImageConceptsOutputPanel and window.selectConcept

(function(global){

async function getJSON(url) {
  const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
  if (!res.ok) throw new Error(`GET ${url} failed: ${res.status}`);
  return await res.json();
}

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {})
  });
  if (!res.ok) throw new Error(`POST ${url} failed: ${res.status}`);
  return await res.json();
}

async function saveSelectedConcept(postId, sectionId, conceptId) {
  return postJSON(`/authoring/api/posts/${postId}/sections/${sectionId}/select-concept`, { concept_id: conceptId });
}

class ImageConceptsOutputPanel {
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
    const editor = document.getElementById('content-editor');
    editor?.addEventListener('input', () => this.updateWordCount());
    document.getElementById('regenerate-btn')?.addEventListener('click', () => this.regenerate());
    document.getElementById('generate-concepts-btn')?.addEventListener('click', () => this.generateImageConcepts());

    window.addEventListener('sections:batch-generate', async (e) => {
      const ids = e.detail?.ids || [];
      console.log('[DEBUG] Batch generation started for sections:', ids);
      for (let i = 0; i < ids.length; i++) {
        const id = ids[i];
        console.log('[DEBUG] Generating concepts for section:', id);
        
        // Update progress modal
        this.updateBatchProgress(id, 'Generating...', (i + 1) / ids.length * 100);
        
        await this.generateImageConcepts(id); 
        console.log('[DEBUG] Completed generation for section:', id);
        
        // Update progress modal
        this.updateBatchProgress(id, 'Complete', (i + 1) / ids.length * 100);
      }
      console.log('[DEBUG] Batch generation completed for all sections');
      
      // Close progress modal after a short delay
      setTimeout(() => {
        this.closeBatchProgress();
      }, 1000);
    });

    // Global selection handler
    global.selectConcept = async (conceptId, sectionId) => {
      try {
        const container = document.getElementById('concepts-container');
        if (!container) return;
        container.querySelectorAll('.concept-card').forEach(card => {
          const isSelected = card.dataset.conceptId === conceptId && card.dataset.sectionId === sectionId;
          card.classList.toggle('selected', isSelected);
          const btn = card.querySelector('.btn-select');
          if (btn) {
            btn.classList.toggle('selected', isSelected);
            btn.textContent = isSelected ? 'Selected' : 'Select';
          }
        });
        await saveSelectedConcept(this.postId, sectionId, conceptId);
        if (this.current && this.current.id === sectionId) {
          this.current.selected_image_concept = conceptId;
        }
      } catch (e) {
        console.error('Error saving selected concept:', e);
      }
    };
  }

  show(section) {
    console.log('[DEBUG] ImageConceptsOutputPanel.show() called with section:', section);
    console.log('[DEBUG] Section image_concepts:', section?.image_concepts);
    this.current = section || null;
    if (!section) return;

    document.getElementById('current-section-title').textContent = section.title || 'Untitled';
    document.getElementById('section-title-display').textContent = section.title || '';
    document.getElementById('section-subtitle-display').textContent = section.subtitle || '';
    document.getElementById('section-topics-display').innerHTML = (section.topics||[]).map(t=>`<span class="topic-tag">${t}</span>`).join('');

    const editor = document.getElementById('content-editor');
    if (editor) editor.disabled = false;
    
    // Optional buttons that may not exist on all pages
    const previewBtn = document.getElementById('preview-btn');
    if (previewBtn) previewBtn.disabled = false;
    
    const saveBtn = document.getElementById('save-btn');
    if (saveBtn) saveBtn.disabled = false;
    
    const regenerateBtn = document.getElementById('regenerate-btn');
    if (regenerateBtn) regenerateBtn.disabled = false;

    const generateBtn = document.getElementById('generate-concepts-btn');
    if (generateBtn) generateBtn.disabled = false;

    // Display image concepts - try structured display first, fallback to textarea
    this.displayImageConcepts(section.image_concepts || '');
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

    // Display concepts for all selected sections
    this.displayMultipleSectionsConcepts(sections);
    this.updateWordCount();
  }

  clearDisplay() {
    const conceptsDisplay = document.getElementById('image-concepts-display');
    const fallbackEditor = document.getElementById('content-editor-fallback');
    
    conceptsDisplay.style.display = 'none';
    fallbackEditor.style.display = 'none';
  }

  displayMultipleSectionsConcepts(sections) {
    const conceptsDisplay = document.getElementById('image-concepts-display');
    const conceptsContainer = document.getElementById('concepts-container');
    const fallbackEditor = document.getElementById('content-editor-fallback');

    conceptsContainer.innerHTML = '';

    let hasAnyConcepts = false;
    let allConceptsText = '';

    sections.forEach((section, sectionIndex) => {
      const conceptsData = section.image_concepts || '';
      
      if (conceptsData.trim() === '') return;

      try {
        // Try to parse as JSON
        const parsed = JSON.parse(conceptsData);
        
        if (parsed.concepts && Array.isArray(parsed.concepts)) {
          // Add section header
          const sectionHeader = document.createElement('div');
          sectionHeader.className = 'section-concepts-header';
          sectionHeader.style.gridColumn = '1 / -1'; // Span full width
          sectionHeader.innerHTML = `
            <h6 style="color: #e2e8f0; margin: 1rem 0 0.5rem 0; padding-bottom: 0.5rem; border-bottom: 1px solid #334155;">
              Section ${section.order}: ${section.title}
            </h6>
          `;
          conceptsContainer.appendChild(sectionHeader);

          // Add concept cards for this section
          const selectedConceptId = section.selected_image_concept;
          const defaultConceptId = parsed.concepts[0]?.concept_id;
          
          console.log(`[DEBUG] Multiple sections - Section ${section.order}: selectedConceptId=${selectedConceptId}, defaultConceptId=${defaultConceptId}`);
          
          parsed.concepts.forEach((concept, index) => {
            const card = document.createElement('div');
            card.className = 'concept-card';
            card.dataset.conceptId = concept.concept_id;
            card.dataset.sectionId = section.id;
            
            // Determine if this concept should be selected
            const isSelected = selectedConceptId === concept.concept_id || 
                              (!selectedConceptId && concept.concept_id === defaultConceptId);
            
            if (isSelected) {
              card.classList.add('selected');
            }
            
            card.innerHTML = `
              <div class="concept-header">
                <span class="concept-id">${concept.concept_id}</span>
                <button class="btn-concept btn-select ${isSelected ? 'selected' : ''}" onclick="selectConcept('${concept.concept_id}', '${section.id}')">
                  ${isSelected ? 'Selected' : 'Select'}
                </button>
              </div>
              <div class="concept-title">${concept.concept_title}</div>
              <div class="concept-description">${concept.concept_description}</div>
              <div class="concept-mood">Mood: ${concept.concept_mood}</div>
              <div class="concept-elements">Key Elements: ${concept.key_visual_elements}</div>
              <div class="concept-actions">
                <button class="btn-concept btn-edit" onclick="editConcept('${concept.concept_id}', '${section.id}')">Edit</button>
              </div>
            `;
            
            conceptsContainer.appendChild(card);
          });
          
          // Auto-select default concept if no selection exists
          if (!selectedConceptId && defaultConceptId) {
            setTimeout(() => {
              window.selectConcept(defaultConceptId, section.id);
            }, 500);
          }

          hasAnyConcepts = true;
        } else {
          // Not structured JSON, add to text
          allConceptsText += `\n\n--- Section ${section.order}: ${section.title} ---\n${conceptsData}`;
        }
      } catch (e) {
        // Not valid JSON, add to text
        allConceptsText += `\n\n--- Section ${section.order}: ${section.title} ---\n${conceptsData}`;
      }
    });

    if (hasAnyConcepts) {
      conceptsDisplay.style.display = 'block';
      fallbackEditor.style.display = 'none';
    } else if (allConceptsText) {
      // Fallback to textarea display
      const editor = document.getElementById('content-editor');
      editor.value = allConceptsText;
      conceptsDisplay.style.display = 'none';
      fallbackEditor.style.display = 'block';
    } else {
      this.clearDisplay();
    }
  }

  displayImageConcepts(conceptsData) {
    console.log('[DEBUG] displayImageConcepts called with data length:', conceptsData?.length || 0);
    const conceptsDisplay = document.getElementById('image-concepts-display');
    const conceptsContainer = document.getElementById('concepts-container');
    const fallbackEditor = document.getElementById('content-editor-fallback');
    const editor = document.getElementById('content-editor');

    if (!conceptsData || conceptsData.trim() === '') {
      console.log('[DEBUG] No concepts data, hiding displays');
      conceptsDisplay.style.display = 'none';
      fallbackEditor.style.display = 'none';
      return;
    }

    try {
      // Try to parse as JSON
      console.log('[DEBUG] Attempting to parse JSON');
      const parsed = JSON.parse(conceptsData);
      console.log('[DEBUG] Parsed JSON:', parsed);
      
      if (parsed.concepts && Array.isArray(parsed.concepts)) {
        console.log('[DEBUG] Valid concepts array found, rendering cards');
        // Display structured concepts
        this.renderConceptCards(parsed);
        conceptsDisplay.style.display = 'block';
        fallbackEditor.style.display = 'none';
        return;
      } else {
        console.log('[DEBUG] No concepts array found in JSON');
      }
    } catch (e) {
      console.log('[DEBUG] JSON parse error:', e);
      // Not valid JSON, fall back to textarea
    }

    // Fallback to textarea display
    console.log('[DEBUG] Falling back to textarea display');
    editor.value = conceptsData;
    conceptsDisplay.style.display = 'none';
    fallbackEditor.style.display = 'block';
  }

  renderConceptCards(conceptsData) {
    console.log('[DEBUG] renderConceptCards called with:', conceptsData);
    const container = document.getElementById('concepts-container');
    console.log('[DEBUG] Container element:', container);
    container.innerHTML = '';

    const selectedConceptId = this.current.selected_image_concept;
    const defaultConceptId = conceptsData.concepts[0]?.concept_id; // First concept as default
    console.log('[DEBUG] Selected concept ID:', selectedConceptId, 'Default concept ID:', defaultConceptId);

    conceptsData.concepts.forEach((concept, index) => {
      console.log(`[DEBUG] Processing concept ${index}:`, concept.concept_id);
      const card = document.createElement('div');
      card.className = 'concept-card';
      card.dataset.conceptId = concept.concept_id;
      card.dataset.sectionId = this.current.id; // Associate with current section
      
      // Determine if this concept should be selected
      const isSelected = selectedConceptId === concept.concept_id || 
                        (!selectedConceptId && concept.concept_id === defaultConceptId);
      
      if (isSelected) {
        card.classList.add('selected');
      }
      
      card.innerHTML = `
        <div class="concept-header">
          <span class="concept-id">${concept.concept_id}</span>
          <button class="btn-concept btn-select ${isSelected ? 'selected' : ''}" onclick="selectConcept('${concept.concept_id}', '${this.current.id}')">
            ${isSelected ? 'Selected' : 'Select'}
          </button>
        </div>
        <div class="concept-title">${concept.concept_title}</div>
        <div class="concept-description">${concept.concept_description}</div>
        <div class="concept-mood">Mood: ${concept.concept_mood}</div>
        <div class="concept-elements">Key Elements: ${concept.key_visual_elements}</div>
        <div class="concept-actions">
          <button class="btn-concept btn-edit" onclick="editConcept('${concept.concept_id}', '${this.current.id}')">Edit</button>
        </div>
      `;
      
      container.appendChild(card);
    });

    // Auto-select default concept if no selection exists
    if (!selectedConceptId && defaultConceptId) {
      setTimeout(() => {
        window.selectConcept(defaultConceptId, this.current.id);
      }, 500);
    }
  }

  updateWordCount() {
    const text = (document.getElementById('content-editor')?.value || '').trim();
    const n = text ? text.split(/\s+/).filter(Boolean).length : 0;
    const wc = document.getElementById('word-count');
    if (wc) wc.textContent = `${n} words`;
  }

  // Optional raw save (not used in cards mode)
  async save() {
    if (!this.current) return;
    const content = document.getElementById('content-editor')?.value || '';
    await postJSON(`/authoring/api/posts/${this.postId}/sections/${this.current.id}/save-image-concepts`, { image_concepts: content });
    const last = document.getElementById('last-saved');
    if (last) last.textContent = `Saved ${new Date().toLocaleTimeString()}`;
  }

  updateBatchProgress(sectionId, status, percentage) {
    // Update section status in progress modal
    const sectionItem = document.querySelector(`#batch-progress-modal .section-item[data-section-id="${sectionId}"]`);
    if (sectionItem) {
      const statusElement = sectionItem.querySelector('.section-status');
      if (statusElement) {
        statusElement.textContent = status;
        statusElement.className = `section-status ${status.toLowerCase().replace(' ', '-')}`;
      }
    }
    
    // Update progress bar
    const progressFill = document.getElementById('progress-fill');
    const progressPercent = document.getElementById('progress-percent');
    if (progressFill) {
      progressFill.style.width = `${percentage}%`;
    }
    if (progressPercent) {
      progressPercent.textContent = `${Math.round(percentage)}%`;
    }
  }
  
  closeBatchProgress() {
    // Remove progress modal
    const modal = document.getElementById('batch-progress-modal');
    if (modal) {
      modal.remove();
    }
    
    // Re-enable Generate All button
    const batchBtn = document.getElementById('batch-generate-btn');
    if (batchBtn) {
      batchBtn.disabled = false;
      batchBtn.innerHTML = '<i class="fas fa-magic"></i> Generate All';
    }
  }

  async generateImageConcepts(sectionId = null) {
    const id = sectionId || (this.current?.id);
    if (!id) return;
    console.log('[DEBUG] generateImageConcepts called for section:', id);
    const editor = document.getElementById('content-editor');
    editor.value = 'Generating image concepts…';
    editor.disabled = true;

    try {
      console.log('[DEBUG] Making API call to generate concepts for section:', id);
      const res = await postJSON(`/authoring/api/posts/${this.postId}/sections/${id}/generate-image-concepts`, {});
      console.log('[DEBUG] API response received:', res);
      
      if (res.success && res.image_concepts) {
        // Update the textarea
        editor.value = res.image_concepts;
        
        // Update the visual concept cards
        this.displayImageConcepts(res.image_concepts);
        
        // Update the current section data if this is the currently displayed section
        if (this.current && this.current.id === id) {
          this.current.image_concepts = res.image_concepts;
        }
        
        console.log('[DEBUG] Image concepts generated and displayed successfully');
      } else {
        editor.value = res.error || '(no concepts generated)';
        console.error('[DEBUG] API returned error:', res.error);
      }
    } catch (err) {
      console.error('[DEBUG] Error generating image concepts:', err);
      editor.value = 'Error generating image concepts';
    } finally {
      editor.disabled = false;
      this.updateWordCount();
    }
  }

  async regenerate(sectionId = null) {
    // For image concepts, regenerate means generate new concepts
    return this.generateImageConcepts(sectionId);
  }
}

// Expose globally
global.ImageConceptsOutputPanel = ImageConceptsOutputPanel;

})(window);
