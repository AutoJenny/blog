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
    const data = await getJSON(`/authoring/api/posts/${this.postId}/sections`);
    this.sections = data.success ? (data.sections || []) : [];
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
      // Generate for ALL sections, not just selected ones
      const ids = this.sections.map(s => String(s.id));
      console.log(`[DEBUG] Generate All clicked - generating for ${ids.length} sections:`, ids);
      const evt = new CustomEvent('sections:batch-generate', { detail: { ids }});
      window.dispatchEvent(evt);
    });
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
    
    // Parse selected image concept title from JSON if available
    let selectedConceptDisplay = '';
    let selectedConceptId = section.selected_image_concept || '';
    
    if (section.image_concepts && section.image_concepts.trim()) {
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