// Imaging Sections Panel - Independent from authoring
import { getJSON } from './api.js';

export class ImagingSectionsPanel {
  constructor({ postId, onSelect, onSelectMultiple }) {
    this.postId = postId;
    this.onSelect = onSelect;
    this.onSelectMultiple = onSelectMultiple;
    this.sections = [];
    this.selectedSections = new Set();
    this.bind();
    this.loadSections();
  }

  bind() {
    const refreshBtn = document.getElementById('refresh-sections');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => this.loadSections());
    }
  }

  async loadSections() {
    const sectionsList = document.getElementById('sections-list');
    if (!sectionsList) return;

    try {
      sectionsList.innerHTML = `
        <div class="loading-state">
          <i class="fas fa-spinner fa-spin"></i>
          <span>Loading sections...</span>
        </div>
      `;

      const data = await getJSON(`/imaging/api/posts/${this.postId}/sections`);
      
      if (data.success) {
        this.sections = data.sections;
        this.renderSections();
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

  renderSections() {
    const sectionsList = document.getElementById('sections-list');
    if (!sectionsList) return;

    if (this.sections.length === 0) {
      sectionsList.innerHTML = `
        <div class="empty-state">
          <i class="fas fa-info-circle"></i>
          <span>No sections found</span>
        </div>
      `;
      return;
    }

    sectionsList.innerHTML = this.sections.map(section => `
      <div class="section-item" data-section-id="${section.id}">
        <h4>${section.section_heading || 'Untitled Section'}</h4>
        <p>${section.section_description || 'No description'}</p>
        <div class="section-meta">
          <span class="section-order">${section.section_order}</span>
          <span class="image-status ${this.hasImage(section) ? 'has-image' : 'no-image'}">
            <i class="fas fa-${this.hasImage(section) ? 'check-circle' : 'times-circle'}"></i>
            ${this.hasImage(section) ? 'Has Image' : 'No Image'}
          </span>
        </div>
      </div>
    `).join('');

    // Add click handlers
    sectionsList.querySelectorAll('.section-item').forEach(item => {
      item.addEventListener('click', () => this.selectSection(item));
    });
  }

  hasImage(section) {
    return section.image_prompts && section.image_prompts !== '{}' && section.image_prompts !== 'null';
  }

  selectSection(element) {
    const sectionId = parseInt(element.dataset.sectionId);
    const section = this.sections.find(s => s.id === sectionId);
    
    if (!section) return;

    // Toggle selection
    if (this.selectedSections.has(sectionId)) {
      this.selectedSections.delete(sectionId);
      element.classList.remove('selected');
    } else {
      this.selectedSections.add(sectionId);
      element.classList.add('selected');
    }

    // Notify parent
    if (this.selectedSections.size === 1) {
      this.onSelect?.(section);
    } else if (this.selectedSections.size > 1) {
      const selectedSections = this.sections.filter(s => this.selectedSections.has(s.id));
      this.onSelectMultiple?.(selectedSections);
    } else {
      this.onSelect?.(null);
    }
  }
}
