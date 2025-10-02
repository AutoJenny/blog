import { SectionsPanel } from './sections-panel.js';
import { ImageConceptsOutputPanel } from './image-concepts-output-panel.js';

function initTabs() {
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanels  = document.querySelectorAll('.tab-panel');
  tabButtons.forEach(btn => btn.addEventListener('click', () => {
    const t = btn.getAttribute('data-tab');
    tabButtons.forEach(b => b.classList.remove('active'));
    tabPanels.forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`${t}-tab`)?.classList.add('active');
    localStorage.setItem('planning-active-tab', t);
  }));
  const saved = localStorage.getItem('planning-active-tab');
  if (saved) document.querySelector(`.tab-btn[data-tab="${saved}"]`)?.click();
}

document.addEventListener('DOMContentLoaded', () => {
  initTabs();

  const postId = window.postId;
  const output = new ImageConceptsOutputPanel({ postId });

  const sectionsPanel = new SectionsPanel({
    postId,
    onSelect: (section) => {
      output.show(section);
      // Initialize LLM module for the selected section
      if (section && section.id) {
        initializeLLMForSection(section.id);
      }
    },
    onSelectMultiple: (sections) => {
      output.showMultiple(sections);
      // Initialize LLM module for the first selected section
      if (sections && sections.length > 0 && sections[0].id) {
        initializeLLMForSection(sections[0].id);
      }
    }
  });

  // Function to initialize LLM module for current section
  function initializeLLMForSection(sectionId) {
    // Initialize LLM module with image_concepts configuration
    const llmModule = initializeLLMModule('image_concepts', postId, sectionId);
    if (llmModule) {
      window.llmModule = llmModule;
    }
  }
});

// Global functions for concept selection
window.selectConcept = function(conceptId, sectionId) {
  // Remove previous selections for this section only
  const sectionCards = document.querySelectorAll(`[data-section-id="${sectionId}"]`);
  sectionCards.forEach(card => {
    card.classList.remove('selected');
    const btn = card.querySelector('.btn-select');
    btn.textContent = 'Select';
    btn.classList.remove('selected');
  });
  
  // Select current concept
  const card = document.querySelector(`[data-concept-id="${conceptId}"][data-section-id="${sectionId}"]`);
  if (card) {
    card.classList.add('selected');
    const btn = card.querySelector('.btn-select');
    btn.textContent = 'Selected';
    btn.classList.add('selected');
  }
};

window.editConcept = function(conceptId, sectionId) {
  // For now, just show an alert - can be expanded later
  alert(`Edit functionality for ${conceptId} in Section ${sectionId} will be implemented in future updates`);
};
