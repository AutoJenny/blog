// Summary Generation Panel JS
(function() {
  function toggleSummaryGenerationAccordion() {
    const content = document.getElementById('summary-generation-content');
    const icon = document.getElementById('summary-generation-accordion-icon');
    if (!content || !icon) return;
    content.classList.toggle('collapsed');
    icon.classList.toggle('open');
  }

  function generateSummary() {
    console.log('[Summary Generation Panel] Individual generate clicked');
    // TODO: Implement individual summary generation
    // For now, just show a placeholder
    const textarea = document.getElementById('summary-textarea');
    if (textarea) {
      textarea.value = 'Generated summary (individual)';
      updateWordCount();
    }
  }

  function updateWordCount() {
    const textarea = document.getElementById('summary-textarea');
    const wordCount = document.getElementById('summary-word-count');
    if (textarea && wordCount) {
      const words = textarea.value.trim().split(/\s+/).filter(word => word.length > 0).length;
      wordCount.textContent = `${words} words`;
    }
  }

  function handleUberGeneration(event) {
    console.log('[Summary Generation Panel] Received uber generation event:', event.detail);
    if (event.detail && event.detail.summary) {
      const textarea = document.getElementById('summary-textarea');
      if (textarea) {
        textarea.value = event.detail.summary;
        updateWordCount();
      }
    }
  }

  // Initialize
  document.addEventListener('DOMContentLoaded', function() {
    // Initialize accordion as open by default
    const content = document.getElementById('summary-generation-content');
    const icon = document.getElementById('summary-generation-accordion-icon');
    if (content && icon) {
      content.classList.remove('collapsed');
      icon.classList.add('open');
    }
    
    const generateBtn = document.getElementById('generate-summary-btn');
    if (generateBtn) {
      generateBtn.addEventListener('click', generateSummary);
    }
    
    const textarea = document.getElementById('summary-textarea');
    if (textarea) {
      textarea.addEventListener('input', updateWordCount);
    }
    
    // Listen for uber generation events
    document.addEventListener('uberGenerateTitleSummary', handleUberGeneration);
  });

  // Expose to window for inline onclick
  window.toggleSummaryGenerationAccordion = toggleSummaryGenerationAccordion;
})();
