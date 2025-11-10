// Photo Harvesting Output Panel - Non-module global implementation
// Provides: window.PhotoHarvestingOutputPanel and window.selectConcept

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
  
  // Try to parse JSON even if status is not ok to get error message
  let jsonData;
  try {
    jsonData = await res.json();
  } catch (e) {
    // If JSON parsing fails, return error object
    if (!res.ok) {
      throw new Error(`POST ${url} failed: ${res.status} ${res.statusText}`);
    }
    throw new Error('Invalid JSON response');
  }
  
  // If response is not ok, return error object with message
  if (!res.ok) {
    return {
      success: false,
      error: jsonData.error || `HTTP ${res.status}: ${res.statusText}`
    };
  }
  
  return jsonData;
}

async function saveSelectedConcept(postId, sectionId, conceptId) {
  return postJSON(`/authoring/api/posts/${postId}/sections/${sectionId}/select-concept`, { concept_id: conceptId });
}

class PhotoHarvestingOutputPanel {
  constructor({ postId }) {
    console.log('[DEBUG] PhotoHarvestingOutputPanel: Constructor called with postId:', postId);
    this.postId = postId;
    this.current = null;
    this.cache = new Map();
    this.postData = null;
    this._batchEventListenerBound = false;
    this.bind();
    this.loadPostData();
    console.log('[DEBUG] PhotoHarvestingOutputPanel: Initialization complete');
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
    console.log('[DEBUG] PhotoHarvestingOutputPanel: bind() called');
    const editor = document.getElementById('content-editor');
    editor?.addEventListener('input', () => this.updateWordCount());
    document.getElementById('photo-regenerate-btn')?.addEventListener('click', () => this.regenerate());
    document.getElementById('photo-generate-concepts-btn')?.addEventListener('click', () => this.generateImageConcepts());

    // Only bind event listener once (use a global flag to prevent duplicates)
    if (!window._photoHarvestingBatchListenerBound) {
      window._photoHarvestingBatchListenerBound = true;
      console.log('[DEBUG] PhotoHarvestingOutputPanel: Binding batch event listener');
      const batchHandler = async (e) => {
        // Prevent duplicate processing
        if (this._batchProcessing) {
          console.log('[DEBUG] PhotoHarvestingOutputPanel: Batch already processing, ignoring duplicate event');
          return;
        }
        
        this._batchProcessing = true;
        const ids = e.detail?.ids || [];
        console.log('[DEBUG] PhotoHarvestingOutputPanel: Batch generation event received for sections:', ids);
        
        if (!ids || ids.length === 0) {
          console.warn('[DEBUG] PhotoHarvestingOutputPanel: No section IDs provided');
          this._batchProcessing = false;
          return;
        }
        
        try {
          for (let i = 0; i < ids.length; i++) {
            const id = ids[i];
            const sectionNum = i + 1;
            const totalSections = ids.length;
            const progressPercent = (sectionNum / totalSections) * 100;
            
            console.log(`[DEBUG] PhotoHarvestingOutputPanel: Generating concepts for section ${sectionNum}/${totalSections}:`, id);
            
            // Update progress - start generating
            this.updateBatchProgress(id, 'Generating...', progressPercent);
            
            try {
              // Add timeout to prevent hanging
              const timeoutPromise = new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Generation timeout after 60 seconds')), 60000)
              );
              
              await Promise.race([
                this.generateImageConcepts(id),
                timeoutPromise
              ]);
              
              console.log(`[DEBUG] PhotoHarvestingOutputPanel: Completed generation for section ${id}`);
              
              // Update progress - mark as complete
              this.updateBatchProgress(id, 'Complete', progressPercent);
            } catch (error) {
              console.error(`[DEBUG] PhotoHarvestingOutputPanel: Error generating concepts for section ${id}:`, error);
              this.updateBatchProgress(id, `Error: ${error.message}`, progressPercent);
            }
          }
          
          console.log('[DEBUG] PhotoHarvestingOutputPanel: Batch generation completed for all sections');
        } finally {
          this._batchProcessing = false;
          // Close progress modal after a short delay
          setTimeout(() => {
            this.closeBatchProgress();
          }, 1000);
        }
      };
      
      window.addEventListener('sections:batch-generate', batchHandler);
      console.log('[DEBUG] PhotoHarvestingOutputPanel: Batch event listener bound');
    } else {
      console.log('[DEBUG] PhotoHarvestingOutputPanel: Batch event listener already bound (global flag)');
    }

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

    document.getElementById('photo-current-section-title').textContent = section.title || 'Untitled';
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
    
    const regenerateBtn = document.getElementById('photo-regenerate-btn');
    if (regenerateBtn) regenerateBtn.disabled = false;

    const generateBtn = document.getElementById('photo-generate-concepts-btn');
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
    document.getElementById('photo-current-section-title').textContent = `${sections.length} sections selected`;
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
      console.log('[DEBUG] No concepts data, showing placeholder');
      // Clear any existing concepts
      if (conceptsContainer) {
        conceptsContainer.innerHTML = '<p style="color: #94a3b8; font-style: italic; padding: 1rem;">No image concepts generated yet. Click the "Generate" button to create concepts for this section.</p>';
      }
      // Show the concepts display with placeholder message
      if (conceptsDisplay) {
        conceptsDisplay.style.display = 'block';
      }
      if (fallbackEditor) {
        fallbackEditor.style.display = 'none';
      }
      if (editor) {
        editor.value = '';
      }
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
    if (!container) {
      console.error('[DEBUG] concepts-container element not found!');
      return;
    }
    container.innerHTML = '';

    const selectedConceptId = this.current?.selected_image_concept;
    const sectionId = this.current?.id;
    const defaultConceptId = conceptsData.concepts[0]?.concept_id; // First concept as default
    console.log('[DEBUG] Selected concept ID:', selectedConceptId, 'Default concept ID:', defaultConceptId, 'Section ID:', sectionId);

    conceptsData.concepts.forEach((concept, index) => {
      console.log(`[DEBUG] Processing concept ${index}:`, concept.concept_id);
      const card = document.createElement('div');
      card.className = 'concept-card';
      card.dataset.conceptId = concept.concept_id;
      card.dataset.sectionId = sectionId || this.current?.id || 'unknown'; // Associate with current section
      
      // Determine if this concept should be selected
      const isSelected = selectedConceptId === concept.concept_id || 
                        (!selectedConceptId && concept.concept_id === defaultConceptId);
      
      if (isSelected) {
        card.classList.add('selected');
      }
      
      const currentSectionId = sectionId || this.current?.id || 'unknown';
      card.innerHTML = `
        <div class="concept-header">
          <span class="concept-id">${concept.concept_id}</span>
          <button class="btn-concept btn-select ${isSelected ? 'selected' : ''}" onclick="selectConcept('${concept.concept_id}', '${currentSectionId}')">
            ${isSelected ? 'Selected' : 'Select'}
          </button>
        </div>
        <div class="concept-title">${concept.concept_title}</div>
        <div class="concept-description">${concept.concept_description}</div>
        <div class="concept-mood">Mood: ${concept.concept_mood}</div>
        <div class="concept-elements">Key Elements: ${concept.key_visual_elements}</div>
        <div class="concept-actions">
          <button class="btn-concept btn-edit" onclick="editConcept('${concept.concept_id}', '${currentSectionId}')">Edit</button>
        </div>
      `;
      
      container.appendChild(card);
    });

    // Auto-select default concept if no selection exists
    if (!selectedConceptId && defaultConceptId && sectionId) {
      setTimeout(() => {
        if (window.selectConcept) {
          window.selectConcept(defaultConceptId, sectionId);
        }
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
    // Update via BatchProgressPanel if available
    if (window.batchProgressPanel && typeof window.batchProgressPanel.updateSectionProgress === 'function') {
      const statusMap = {
        'Generating...': 'processing',
        'Complete': 'completed',
        'Error': 'error'
      };
      const normalizedStatus = statusMap[status] || status.toLowerCase();
      window.batchProgressPanel.updateSectionProgress(sectionId, percentage, normalizedStatus);
      console.log(`[DEBUG] PhotoHarvestingOutputPanel: Updated batch progress for section ${sectionId}: ${status} (${percentage}%)`);
    } else {
      // Fallback: Update progress bar directly if BatchProgressPanel not available
      const progressFill = document.getElementById('progress-fill');
      const progressPercent = document.getElementById('progress-percent');
      if (progressFill) {
        progressFill.style.width = `${percentage}%`;
      }
      if (progressPercent) {
        progressPercent.textContent = `${Math.round(percentage)}%`;
      }
      
      // Also try to update section items in batch progress modal if it exists
      const sectionItem = document.querySelector(`#batch-progress-modal .section-item[data-section-id="${sectionId}"]`);
      if (sectionItem) {
        const statusElement = sectionItem.querySelector('.section-status');
        if (statusElement) {
          statusElement.textContent = status;
          statusElement.className = `section-status ${status.toLowerCase().replace(' ', '-')}`;
        }
      }
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
    if (!id) {
      console.warn('[DEBUG] No section ID provided for generateImageConcepts');
      return;
    }
    console.log('[DEBUG] generateImageConcepts called for section:', id);
    
    // Disable buttons during generation
    const generateBtn = document.getElementById('photo-generate-concepts-btn');
    const regenerateBtn = document.getElementById('photo-regenerate-btn');
    if (generateBtn) generateBtn.disabled = true;
    if (regenerateBtn) regenerateBtn.disabled = true;
    
    // Show loading state in concepts display
    const conceptsContainer = document.getElementById('concepts-container');
    const conceptsDisplay = document.getElementById('image-concepts-display');
    if (conceptsContainer && conceptsDisplay) {
      conceptsContainer.innerHTML = '<p style="color: #94a3b8; padding: 1rem;">Generating concepts...</p>';
      conceptsDisplay.style.display = 'block';
    }

    try {
      console.log('[DEBUG] Making API call to generate concepts for section:', id);
      // Include week context if available (from WeekContext module or URL params)
      let apiUrl = `/authoring/api/posts/${this.postId}/sections/${id}/generate-image-concepts`;
      
      // Try to get week context from WeekContext module
      let weekContext = null;
      if (window.WeekContext) {
        weekContext = window.WeekContext.getWeekContext();
      }
      
      // Fallback to URL parameters if WeekContext not available
      if (!weekContext) {
        const urlParams = new URLSearchParams(window.location.search);
        const year = urlParams.get('year');
        const week = urlParams.get('week');
        if (year && week) {
          weekContext = { year: parseInt(year), week: parseInt(week) };
        }
      }
      
      // Add week context to API URL if available
      if (weekContext) {
        const separator = apiUrl.includes('?') ? '&' : '?';
        apiUrl = `${apiUrl}${separator}year=${weekContext.year}&week=${weekContext.week}`;
        console.log('[DEBUG] Added week context to API URL:', weekContext);
      } else {
        console.warn('[DEBUG] No week context available for image concepts generation');
      }
      
      console.log('[DEBUG] Calling API:', apiUrl);
      
      // Add timeout to fetch request
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout
      
      let res;
      try {
        const fetchRes = await fetch(apiUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({}),
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        // Parse response
        let jsonData;
        try {
          jsonData = await fetchRes.json();
        } catch (e) {
          if (!fetchRes.ok) {
            throw new Error(`POST ${apiUrl} failed: ${fetchRes.status} ${fetchRes.statusText}`);
          }
          throw new Error('Invalid JSON response');
        }
        
        if (!fetchRes.ok) {
          res = {
            success: false,
            error: jsonData.error || `HTTP ${fetchRes.status}: ${fetchRes.statusText}`
          };
        } else {
          res = jsonData;
        }
      } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
          throw new Error('Request timeout: API call took too long');
        }
        throw error;
      }
      
      console.log('[DEBUG] API response received:', res);
      console.log('[DEBUG] Response success:', res.success);
      console.log('[DEBUG] Response error:', res.error);
      console.log('[DEBUG] Response image_concepts type:', typeof res.image_concepts);
      console.log('[DEBUG] Response image_concepts length:', res.image_concepts?.length);
      
      // Check for error in response
      if (res.error) {
        console.error('[DEBUG] API returned error:', res.error);
        if (conceptsContainer) {
          conceptsContainer.innerHTML = '<p style="color: #ef4444; padding: 1rem;">Error: ' + res.error + '</p>';
        }
        return;
      }
      
      if (res.success && res.image_concepts) {
        // Update the current section data
        if (this.current && this.current.id === id) {
          this.current.image_concepts = res.image_concepts;
        } else if (!this.current) {
          // If no current section, set it to ensure display works
          const section = this.getSectionData(id);
          if (section) {
            section.image_concepts = res.image_concepts;
            this.current = section;
          }
        }
        
        // Update the visual concept cards (this should replace the loading message)
        console.log('[DEBUG] Calling displayImageConcepts with:', res.image_concepts.substring(0, 100) + '...');
        this.displayImageConcepts(res.image_concepts);
        
        console.log('[DEBUG] Image concepts generated and displayed successfully');
      } else {
        console.error('[DEBUG] API returned error or no concepts:', res.error || res);
        if (conceptsContainer) {
          conceptsContainer.innerHTML = '<p style="color: #ef4444; padding: 1rem;">Error: ' + (res.error || 'No concepts generated') + '</p>';
        }
      }
    } catch (err) {
      console.error('[DEBUG] Error generating image concepts:', err);
      if (conceptsContainer) {
        conceptsContainer.innerHTML = '<p style="color: #ef4444; padding: 1rem;">Error generating image concepts: ' + err.message + '</p>';
      }
    } finally {
      // Re-enable buttons
      if (generateBtn) generateBtn.disabled = false;
      if (regenerateBtn) regenerateBtn.disabled = false;
      this.updateWordCount();
    }
  }
  
  getSectionData(sectionId) {
    // Try to get section data from sections panel or make API call
    if (window.sectionsPanel && window.sectionsPanel.sections) {
      return window.sectionsPanel.sections.find(s => s.id == sectionId);
    }
    return null;
  }

  async regenerate(sectionId = null) {
    // For image concepts, regenerate means generate new concepts
    return this.generateImageConcepts(sectionId);
  }
}

// Expose globally
global.PhotoHarvestingOutputPanel = PhotoHarvestingOutputPanel;

// Accordion function for photo output panel
function togglePhotoOutputAccordion() {
    const content = document.getElementById('photo-output-accordion-content');
    const icon = document.getElementById('photo-output-accordion-icon');
    
    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
    } else {
        content.style.display = 'none';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
    }
}

// Expose globally
window.togglePhotoOutputAccordion = togglePhotoOutputAccordion;
window.PhotoHarvestingOutputPanel = PhotoHarvestingOutputPanel;

// Auto-initialize if on image-concepts page
document.addEventListener('DOMContentLoaded', () => {
    if (window.currentSubstage === 'image-concepts' && 
        (window.illustrationMethod === 'Photo-harvesting') &&
        typeof window.photoHarvestingOutputPanel === 'undefined') {
        const postId = window.postId;
        if (postId) {
            window.photoHarvestingOutputPanel = new PhotoHarvestingOutputPanel({ postId });
        }
    }
});

})(window);
