// Image Concepts Output Panel - specialized renderer (non-module)
(function(){
  document.addEventListener('DOMContentLoaded', () => {
    if (window.currentSubstage !== 'image-concepts') return;
    const postId = window.postId;
    window.imageConceptsOutputPanel = new ImageConceptsOutputPanel({ postId });
  });
})();

