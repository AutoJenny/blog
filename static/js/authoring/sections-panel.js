import { getJSON } from './api.js';

export class SectionsPanel {
  constructor({ postId, onSelect }) {
    this.postId = postId;
    this.onSelect = onSelect;
    this.sections = [];
    this.selected = new Set();
    this.bindStaticControls();
    this.load();
  }

  async load() {
    console.log('[DEBUG] SectionsPanel.load() called - fetching fresh data');
    const data = await getJSON(`/authoring/api/posts/${this.postId}/sections`);
    this.sections = data.success ? (data.sections || []) : [];
    console.log(`[DEBUG] SectionsPanel.load() - loaded ${this.sections.length} sections`);
    this.render();
  }

  bindStaticControls() {
    const list = document.getElementById('sections-list');
    list?.addEventListener('click', (e) => {
      const row = e.target.closest('.section-item');
      if (row && e.target.type !== 'checkbox' && !e.target.classList.contains('accordion-toggle')) {
        this.select(row.dataset.sectionId);
      }
    });

    // Accordion toggle functionality
    list?.addEventListener('click', (e) => {
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

    document.querySelector('.section-filters')?.addEventListener('click', (e) => {
      const btn = e.target.closest('.filter-btn'); if (!btn) return;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      this.applyFilter(btn.dataset.filter);
    });

    document.getElementById('select-all-btn')?.addEventListener('click', () => {
      this.selected = new Set(this.sections.map(s => String(s.id)));
      this.syncSelectionUI();
    });

    document.getElementById('batch-generate-btn')?.addEventListener('click', () => {
      this.startBatchGeneration();
    });

    // Listen for reload events after batch generation
    window.addEventListener('sections:reload-data', () => {
      console.log('[DEBUG] Sections panel received reload event, refreshing data');
      console.log('[DEBUG] Current sections before reload:', this.sections.length);
      this.load();
    });
  }

  startBatchGeneration() {
    // Generate for ALL sections, not just selected ones
    const sections = this.sections.map(s => ({ id: String(s.id), title: s.section_heading || `Section ${s.id}` }));
    
    // Show progress UI
    this.showBatchProgress(sections);
    
    // Dispatch batch generation event
    const ids = sections.map(s => s.id);
    console.log(`[DEBUG] Generate All clicked - generating for ${ids.length} sections:`, ids);
    console.log('[DEBUG] Dispatching sections:batch-generate event');
    const evt = new CustomEvent('sections:batch-generate', { detail: { ids, sections }});
    window.dispatchEvent(evt);
    console.log('[DEBUG] Event dispatched successfully');
  }

  showBatchProgress(sections) {
    // Disable Generate All button
    const batchBtn = document.getElementById('batch-generate-btn');
    if (batchBtn) {
      batchBtn.disabled = true;
      batchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    }

    // Create progress modal/overlay
    const progressHTML = `
      <div id="batch-progress-modal" class="batch-progress-modal">
        <div class="batch-progress-content">
          <div class="batch-progress-header">
            <h3>Batch Generation Progress</h3>
            <button id="cancel-batch-btn" class="btn btn-secondary btn-sm">
              <i class="fas fa-times"></i> Cancel
            </button>
          </div>
          <div class="batch-progress-body">
            <div class="progress-summary">
              <span id="progress-text">Starting batch generation for ${sections.length} sections...</span>
            </div>
            <div class="progress-bar-container">
              <div class="progress-bar">
                <div id="progress-fill" class="progress-fill" style="width: 0%"></div>
              </div>
              <span id="progress-percent">0%</span>
            </div>
            <div class="section-list">
              ${sections.map(s => `
                <div class="section-item" data-section-id="${s.id}">
                  <span class="section-name">${s.title}</span>
                  <span class="section-status">Pending</span>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      </div>
    `;

    // Remove existing modal if any
    const existingModal = document.getElementById('batch-progress-modal');
    if (existingModal) existingModal.remove();

    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', progressHTML);

    // Add cancel handler
    document.getElementById('cancel-batch-btn')?.addEventListener('click', () => {
      this.cancelBatchGeneration();
    });

    // Add CSS if not already present
    if (!document.getElementById('batch-progress-styles')) {
      const styles = `
        <style id="batch-progress-styles">
          .batch-progress-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
          }
          .batch-progress-content {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 1.5rem;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
          }
          .batch-progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #334155;
          }
          .batch-progress-header h3 {
            margin: 0;
            color: #e2e8f0;
          }
          .progress-summary {
            margin-bottom: 1rem;
            color: #e2e8f0;
          }
          .progress-bar-container {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
          }
          .progress-bar {
            flex: 1;
            height: 20px;
            background: #334155;
            border-radius: 10px;
            overflow: hidden;
          }
          .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #3b82f6, #1d4ed8);
            transition: width 0.3s ease;
          }
          .section-list {
            max-height: 300px;
            overflow-y: auto;
          }
          .section-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem;
            margin-bottom: 0.25rem;
            background: #334155;
            border-radius: 4px;
          }
          .section-name {
            color: #e2e8f0;
            font-weight: 500;
          }
          .section-status {
            font-size: 0.875rem;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
          }
          .section-status.pending { color: #94a3b8; }
          .section-status.generating { color: #fbbf24; }
          .section-status.completed { color: #10b981; }
          .section-status.error { color: #ef4444; }
        </style>
      `;
      document.head.insertAdjacentHTML('beforeend', styles);
    }
  }

  updateBatchProgress(currentIndex, totalSections, sectionId, status, error = null) {
    const progressFill = document.getElementById('progress-fill');
    const progressPercent = document.getElementById('progress-percent');
    const progressText = document.getElementById('progress-text');
    const sectionItem = document.querySelector(`[data-section-id="${sectionId}"]`);
    const sectionStatus = sectionItem?.querySelector('.section-status');

    if (progressFill && progressPercent) {
      const percent = Math.round((currentIndex / totalSections) * 100);
      progressFill.style.width = `${percent}%`;
      progressPercent.textContent = `${percent}%`;
    }

    if (progressText) {
      progressText.textContent = `Processing section ${currentIndex} of ${totalSections}...`;
    }

    if (sectionStatus) {
      sectionStatus.textContent = status;
      sectionStatus.className = `section-status ${status}`;
      
      if (error) {
        sectionStatus.textContent = `Error: ${error}`;
        sectionStatus.className = 'section-status error';
      }
    }
  }

  completeBatchGeneration(successCount, errorCount) {
    const progressText = document.getElementById('progress-text');
    const batchBtn = document.getElementById('batch-generate-btn');

    if (progressText) {
      progressText.textContent = `Batch complete: ${successCount} successful, ${errorCount} errors`;
    }

    if (batchBtn) {
      batchBtn.disabled = false;
      batchBtn.innerHTML = '<i class="fas fa-magic"></i> Generate All';
    }

    // Auto-close modal after 3 seconds
    setTimeout(() => {
      const modal = document.getElementById('batch-progress-modal');
      if (modal) modal.remove();
    }, 3000);
  }

  cancelBatchGeneration() {
    // Dispatch cancel event
    const cancelEvent = new CustomEvent('sections:batch-cancel');
    window.dispatchEvent(cancelEvent);

    // Reset UI
    const batchBtn = document.getElementById('batch-generate-btn');
    if (batchBtn) {
      batchBtn.disabled = false;
      batchBtn.innerHTML = '<i class="fas fa-magic"></i> Generate All';
    }

    // Remove modal
    const modal = document.getElementById('batch-progress-modal');
    if (modal) modal.remove();
  }

  render() {
    const list = document.getElementById('sections-list');
    if (!list) return;
    list.innerHTML = '';
    if (this.sections.length === 0) {
      list.innerHTML = '<div class="loading">No sections found</div>';
      return;
    }
    
    // Use template for each section
    this.sections.forEach(section => {
      const sectionElement = this.createSectionFromTemplate(section);
      list.appendChild(sectionElement);
    });
    this.syncSelectionUI();
  }

  createSectionFromTemplate(section) {
    // Create a template element with the section data
    const template = document.createElement('template');
    
    // Convert section data to template format
    const effectiveStatus = (section.section_text && section.section_text.trim()) ? 'complete' : 'draft';
    
    // Parse selected image concept or image prompts based on current page
    let selectedConceptDisplay = '';
    let selectedConceptId = section.selected_image_concept || '';
    
    // Check if we're on the image prompts page
    const isImagePromptsPage = window.currentSubstage === 'image-prompts';
    console.log(`[DEBUG] Section ${section.id}: isImagePromptsPage=${isImagePromptsPage}, currentSubstage=${window.currentSubstage}`);
    
    if (isImagePromptsPage && section.image_prompts && section.image_prompts.trim()) {
      console.log(`[DEBUG] Section ${section.id}: Processing image_prompts for image-prompts page`);
      // For image prompts page, show the generated image prompt
      try {
        const promptsData = JSON.parse(section.image_prompts);
        if (promptsData.base_concept) {
          selectedConceptDisplay = promptsData.base_concept;
          console.log(`[DEBUG] Section ${section.id}: Using base_concept: ${selectedConceptDisplay.substring(0, 50)}...`);
        } else if (promptsData.image_prompt) {
          // Extract base concept from full prompt (remove style guidelines)
          const fullPrompt = promptsData.image_prompt;
          const styleIndex = fullPrompt.indexOf(', Generate an intricately detailed scene');
          if (styleIndex > 0) {
            selectedConceptDisplay = fullPrompt.substring(0, styleIndex);
          } else {
            selectedConceptDisplay = fullPrompt;
          }
          console.log(`[DEBUG] Section ${section.id}: Extracted from image_prompt: ${selectedConceptDisplay.substring(0, 50)}...`);
        }
      } catch (e) {
        // If JSON parsing fails, show raw content
        selectedConceptDisplay = section.image_prompts;
      }
    } else if (section.image_concepts && section.image_concepts.trim()) {
      // For other pages, show selected image concept
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
    
    const templateData = {
      id: section.id,
      order: section.order,
      title: section.title,
      subtitle: section.subtitle,
      section_text: section.section_text || '',
      status: effectiveStatus,
      progress: section.progress || 0,
      topics: section.topics || [],
      selected_image_concept: selectedConceptDisplay || selectedConceptId || ''
    };
    
    // Generate HTML using template structure
    template.innerHTML = `
      <div class="section-item accordion" data-section-id="${templateData.id}" data-status="${templateData.status}">
        <div class="section-header accordion-header">
          <input type="checkbox" class="section-checkbox" data-section-id="${templateData.id}">
          <span class="section-number">${templateData.order}</span>
          <span class="section-title">${templateData.title}</span>
          <span class="section-status ${templateData.status}">${templateData.status.charAt(0).toUpperCase() + templateData.status.slice(1)}</span>
          <span class="accordion-toggle">▼</span>
        </div>
        <div class="section-content accordion-content">
          ${templateData.subtitle ? `<div class="section-subtitle">${templateData.subtitle}</div>` : ''}
          ${templateData.section_text ? `<div class="section-text-preview">${templateData.section_text}</div>` : ''}
          <div class="section-topics">${templateData.topics.map(topic => `<span class="topic-tag">${topic}</span>`).join('')}</div>
          ${templateData.selected_image_concept ? `<div class="section-selected-concept"><div class="concept-label">Selected Concept:</div><div class="concept-details">${templateData.selected_image_concept}</div></div>` : ''}
          <div class="section-progress">
            <div class="progress-bar"><div class="progress-fill" style="width:${templateData.progress}%"></div></div>
            <span class="progress-text">${templateData.progress}% complete</span>
          </div>
        </div>
      </div>
    `;
    
    return template.content.firstElementChild;
  }

  select(id) {
    this.selected = new Set([String(id)]);
    this.syncSelectionUI();
    const s = this.sections.find(x => String(x.id) === String(id));
    this.onSelect?.(s);
  }

  selectMultiple(ids) {
    this.selected = new Set(ids.map(String));
    this.syncSelectionUI();
    const selectedSections = this.sections.filter(s => this.selected.has(String(s.id)));
    this.onSelectMultiple?.(selectedSections);
  }

  syncSelectionUI() {
    document.querySelectorAll('.section-item').forEach(el => {
      const id = el.dataset.sectionId;
      el.classList.toggle('selected', this.selected.has(id));
      const cb = el.querySelector('.section-checkbox');
      if (cb) {
        cb.checked = this.selected.has(id);
        // Only add event listener if not already added
        if (!cb.dataset.listenerAdded) {
          cb.addEventListener('change', () => {
            if (cb.checked) {
              this.selected.add(id);
            } else {
              this.selected.delete(id);
            }
            // Notify about multiple selection changes
            const selectedSections = this.sections.filter(s => this.selected.has(String(s.id)));
            if (this.onSelectMultiple) {
              this.onSelectMultiple(selectedSections);
            } else if (selectedSections.length === 1) {
              this.onSelect?.(selectedSections[0]);
            }
          });
          cb.dataset.listenerAdded = 'true';
        }
      }
    });
  }

  applyFilter(kind) {
    document.querySelectorAll('.section-item').forEach(el => {
      const status = el.dataset.status || 'draft';
      el.style.display = (kind === 'all' || status === kind) ? '' : 'none';
    });
  }
}