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
window.selectConcept = async function(conceptId, sectionId) {
  console.log(`[DEBUG] selectConcept called: conceptId=${conceptId}, sectionId=${sectionId}`);
  
  try {
    // Save selection to database
    console.log(`[DEBUG] Making API call to save selection`);
    const response = await fetch(`/authoring/api/posts/${window.postId}/sections/${sectionId}/select-concept`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ concept_id: conceptId })
    });
    
    console.log(`[DEBUG] API response status: ${response.status}`);
    
    if (!response.ok) {
      console.error('Failed to save concept selection');
      return;
    }
    
    const result = await response.json();
    console.log(`[DEBUG] API response:`, result);
    
    // Update UI
    console.log(`[DEBUG] Updating UI for section ${sectionId}`);
    // Remove previous selections for this section only
    const sectionCards = document.querySelectorAll(`[data-section-id="${sectionId}"]`);
    console.log(`[DEBUG] Found ${sectionCards.length} cards for section ${sectionId}`);
    
    // Debug: Let's also check all concept cards
    const allCards = document.querySelectorAll('.concept-card');
    console.log(`[DEBUG] Total concept cards found: ${allCards.length}`);
    allCards.forEach((card, index) => {
      console.log(`[DEBUG] Card ${index}:`, {
        conceptId: card.dataset.conceptId,
        sectionId: card.dataset.sectionId,
        hasBtnSelect: !!card.querySelector('.btn-select')
      });
    });
    
    sectionCards.forEach(card => {
      card.classList.remove('selected');
      const btn = card.querySelector('.btn-select');
      if (btn) {
        btn.textContent = 'Select';
        btn.classList.remove('selected');
      } else {
        console.warn(`[DEBUG] Could not find .btn-select button in card:`, card);
      }
    });
    
    // Select current concept
    const card = document.querySelector(`[data-concept-id="${conceptId}"][data-section-id="${sectionId}"]`);
    console.log(`[DEBUG] Found target card:`, card);
    
    if (card) {
      card.classList.add('selected');
      const btn = card.querySelector('.btn-select');
      if (btn) {
        btn.textContent = 'Selected';
        btn.classList.add('selected');
        console.log(`[DEBUG] Updated card ${conceptId} to selected state`);
      } else {
        console.warn(`[DEBUG] Could not find .btn-select button in target card:`, card);
      }
    } else {
      console.error(`[DEBUG] Could not find card with conceptId=${conceptId} and sectionId=${sectionId}`);
    }
  } catch (error) {
    console.error('Error selecting concept:', error);
  }
};

window.editConcept = function(conceptId, sectionId) {
  console.log(`[DEBUG] editConcept called: conceptId=${conceptId}, sectionId=${sectionId}`);
  // For now, just show an alert - can be expanded later
  alert(`Edit functionality for ${conceptId} in Section ${sectionId} will be implemented in future updates`);
};
