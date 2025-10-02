import { postJSON, getJSON } from './api.js';

export class ImageConceptsOutputPanel {
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

    document.getElementById('save-btn')?.addEventListener('click', () => this.save());
    document.getElementById('regenerate-btn')?.addEventListener('click', () => this.regenerate());

    window.addEventListener('sections:batch-generate', async (e) => {
      const ids = e.detail?.ids || [];
      for (const id of ids) { await this.generateImageConcepts(id); }
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
          parsed.concepts.forEach((concept, index) => {
            const card = document.createElement('div');
            card.className = 'concept-card';
            card.dataset.conceptId = concept.concept_id;
            card.dataset.sectionId = section.id;
            
            card.innerHTML = `
              <div class="concept-header">
                <span class="concept-id">${concept.concept_id}</span>
                <button class="btn-concept btn-select" onclick="selectConcept('${concept.concept_id}', '${section.id}')">Select</button>
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
    const conceptsDisplay = document.getElementById('image-concepts-display');
    const conceptsContainer = document.getElementById('concepts-container');
    const fallbackEditor = document.getElementById('content-editor-fallback');
    const editor = document.getElementById('content-editor');

    if (!conceptsData || conceptsData.trim() === '') {
      conceptsDisplay.style.display = 'none';
      fallbackEditor.style.display = 'none';
      return;
    }

    try {
      // Try to parse as JSON
      const parsed = JSON.parse(conceptsData);
      if (parsed.concepts && Array.isArray(parsed.concepts)) {
        // Display structured concepts
        this.renderConceptCards(parsed);
        conceptsDisplay.style.display = 'block';
        fallbackEditor.style.display = 'none';
        return;
      }
    } catch (e) {
      // Not valid JSON, fall back to textarea
    }

    // Fallback to textarea display
    editor.value = conceptsData;
    conceptsDisplay.style.display = 'none';
    fallbackEditor.style.display = 'block';
  }

  renderConceptCards(conceptsData) {
    const container = document.getElementById('concepts-container');
    container.innerHTML = '';

    conceptsData.concepts.forEach((concept, index) => {
      const card = document.createElement('div');
      card.className = 'concept-card';
      card.dataset.conceptId = concept.concept_id;
      
      card.innerHTML = `
        <div class="concept-header">
          <span class="concept-id">${concept.concept_id}</span>
          <button class="btn-concept btn-select" onclick="selectConcept('${concept.concept_id}')">Select</button>
        </div>
        <div class="concept-title">${concept.concept_title}</div>
        <div class="concept-description">${concept.concept_description}</div>
        <div class="concept-mood">Mood: ${concept.concept_mood}</div>
        <div class="concept-elements">Key Elements: ${concept.key_visual_elements}</div>
        <div class="concept-actions">
          <button class="btn-concept btn-edit" onclick="editConcept('${concept.concept_id}')">Edit</button>
        </div>
      `;
      
      container.appendChild(card);
    });

    // No summary needed - concepts are self-contained
  }

  updateWordCount() {
    const text = (document.getElementById('content-editor')?.value || '').trim();
    const n = text ? text.split(/\s+/).filter(Boolean).length : 0;
    const wc = document.getElementById('word-count');
    if (wc) wc.textContent = `${n} words`;
  }

  async save() {
    if (!this.current) return;
    const content = document.getElementById('content-editor').value;
    await postJSON(`/authoring/api/posts/${this.postId}/sections/${this.current.id}/save-image-concepts`, { image_concepts: content });
    document.getElementById('last-saved').textContent = `Saved ${new Date().toLocaleTimeString()}`;
  }

  async generateImageConcepts(sectionId = null) {
    const id = sectionId || (this.current?.id);
    if (!id) return;
    const editor = document.getElementById('content-editor');
    editor.value = 'Generating image concepts…';
    editor.disabled = true;

    try {
      const res = await postJSON(`/authoring/api/posts/${this.postId}/sections/${id}/generate-image-concepts`, {});
      editor.value = res.image_concepts || '(no concepts generated)';
    } catch (err) {
      editor.value = 'Error generating image concepts';
      console.error(err);
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
