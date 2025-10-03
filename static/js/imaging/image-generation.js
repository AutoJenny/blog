// Imaging Image Generation - Independent from authoring
import { ImagingSectionsPanel } from './sections-panel.js';
import { ImagingOutputPanel } from './image-generation-output-panel.js';

function initTabs() {
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanels = document.querySelectorAll('.tab-panel');
  tabButtons.forEach(btn => btn.addEventListener('click', () => {
    const t = btn.getAttribute('data-tab');
    tabButtons.forEach(b => b.classList.remove('active'));
    tabPanels.forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`${t}-tab`)?.classList.add('active');
    localStorage.setItem('imaging-active-tab', t);
  }));
  const saved = localStorage.getItem('imaging-active-tab');
  if (saved) document.querySelector(`.tab-btn[data-tab="${saved}"]`)?.click();
}

document.addEventListener('DOMContentLoaded', () => {
  initTabs();

  const postId = window.postId;
  const output = new ImagingOutputPanel({ postId });
  
  // Make output panel available globally for LLM module
  window.imagingOutputPanel = output;

  const sectionsPanel = new ImagingSectionsPanel({
    postId,
    onSelect: (section) => {
      output.show(section);
      console.log('Section selected:', section);
    },
    onSelectMultiple: (sections) => {
      output.showMultiple(sections);
      console.log('Multiple sections selected:', sections);
    }
  });

  // Initialize LLM module immediately on page load
  // Note: LLM module initialization will be handled by the template's JavaScript
  
  // Function to initialize LLM module for current section
  function initializeLLMForSection(sectionId) {
      // LLM module initialization will be handled by the template's JavaScript
      console.log('LLM module initialization for section:', sectionId);
  }
});

// Imaging-specific global functions
window.imagingSelectSection = function(sectionId) {
  console.log(`[Imaging] Section selected: ${sectionId}`);
  // This function can be used for section-specific actions in imaging
};

window.imagingGenerateImage = function(sectionId) {
  console.log(`[Imaging] Generate image for section: ${sectionId}`);
  // This function can be used for image generation actions
};
