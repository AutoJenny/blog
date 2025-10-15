// Slug Panel JS
(function() {
  function toggleSlugAccordion() {
    const content = document.getElementById('slug-content');
    const icon = document.getElementById('slug-accordion-icon');
    if (!content || !icon) return;
    content.classList.toggle('collapsed');
    icon.classList.toggle('open');
  }

  function generateSlug() {
    console.log('[Slug Panel] Individual generate clicked');
    // TODO: Implement individual slug generation
    // For now, just show a placeholder
    const input = document.getElementById('slug-input');
    if (input) {
      input.value = 'generated-slug-individual';
      updateSlugPreview();
    }
  }

  function updateSlugPreview() {
    const input = document.getElementById('slug-input');
    const preview = document.getElementById('slug-preview');
    if (input && preview) {
      preview.textContent = input.value || 'no-slug-generated';
    }
  }

  function handleUberGeneration(event) {
    console.log('[Slug Panel] Received uber generation event:', event.detail);
    if (event.detail && event.detail.slug) {
      const input = document.getElementById('slug-input');
      if (input) {
        input.value = event.detail.slug;
        updateSlugPreview();
      }
    }
  }

  // Initialize
  document.addEventListener('DOMContentLoaded', function() {
    // Initialize accordion as open by default
    const content = document.getElementById('slug-content');
    const icon = document.getElementById('slug-accordion-icon');
    if (content && icon) {
      content.classList.remove('collapsed');
      icon.classList.add('open');
    }
    
    const generateBtn = document.getElementById('generate-slug-btn');
    if (generateBtn) {
      generateBtn.addEventListener('click', generateSlug);
    }
    
    const input = document.getElementById('slug-input');
    if (input) {
      input.addEventListener('input', updateSlugPreview);
    }
    
    // Listen for uber generation events
    document.addEventListener('uberGenerateTitleSummary', handleUberGeneration);
  });

  // Expose to window for inline onclick
  window.toggleSlugAccordion = toggleSlugAccordion;
})();
