// Subtitle Panel JS
(function() {
  function toggleSubtitleAccordion() {
    const content = document.getElementById('subtitle-content');
    const icon = document.getElementById('subtitle-accordion-icon');
    if (!content || !icon) return;
    content.classList.toggle('collapsed');
    icon.classList.toggle('open');
  }

  function generateSubtitle() {
    console.log('[Subtitle Panel] Individual generate clicked');
    // TODO: Implement individual subtitle generation
    // For now, just show a placeholder
    const input = document.getElementById('subtitle-input');
    if (input) {
      input.value = 'Generated subtitle (individual)';
    }
  }

  function handleUberGeneration(event) {
    console.log('[Subtitle Panel] Received uber generation event:', event.detail);
    if (event.detail && event.detail.subtitle) {
      const input = document.getElementById('subtitle-input');
      if (input) {
        input.value = event.detail.subtitle;
      }
    }
  }

  // Initialize
  document.addEventListener('DOMContentLoaded', function() {
    // Initialize accordion as open by default
    const content = document.getElementById('subtitle-content');
    const icon = document.getElementById('subtitle-accordion-icon');
    if (content && icon) {
      content.classList.remove('collapsed');
      icon.classList.add('open');
    }
    
    const generateBtn = document.getElementById('generate-subtitle-btn');
    if (generateBtn) {
      generateBtn.addEventListener('click', generateSubtitle);
    }
    
    // Listen for uber generation events
    document.addEventListener('uberGenerateTitleSummary', handleUberGeneration);
  });

  // Expose to window for inline onclick
  window.toggleSubtitleAccordion = toggleSubtitleAccordion;
})();


