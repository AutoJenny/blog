// Image Concepts Output Panel - specialized renderer
import { ImageConceptsOutputPanel } from './image-concepts-output-panel.js';

(function(){
  document.addEventListener('DOMContentLoaded', () => {
    if (window.currentSubstage !== 'image-concepts') return;
    const postId = window.postId;
    window.imageConceptsOutputPanel = new ImageConceptsOutputPanel({ postId });
  });
})();

