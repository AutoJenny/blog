// Image Concepts Output Panel - specialized renderer (non-module)
(function(){
  document.addEventListener('DOMContentLoaded', () => {
    // Check for both hyphenated and underscored variants
    const currentSubstage = window.currentSubstage;
    if (currentSubstage !== 'image-concepts' && currentSubstage !== 'image_concepts') return;
    const postId = window.postId;
    window.imageConceptsOutputPanel = new ImageConceptsOutputPanel({ postId });
    
    // Listen for sectionSelected events (dispatched when sections are selected)
    window.addEventListener('sectionSelected', (event) => {
      if (event.detail && event.detail.section) {
        const section = event.detail.section;
        window.imageConceptsOutputPanel.show({
          id: section.id,
          title: section.section_heading || section.title || `Section ${section.id}`,
          subtitle: section.section_description || section.subtitle || '',
          order: section.section_order || section.order || section.id,
          topics: section.topics || [],
          image_concepts: section.image_concepts || '',
          selected_image_concept: section.selected_image_concept || ''
        });
      }
    });
  });
})();

