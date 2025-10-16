// Slug Panel JS
(function() {
  // Note: toggleSlugAccordion is now managed by HeaderAccordionManager

  function generateSlug() {
    console.log('[Slug Panel] Individual generate clicked');
    // TODO: Implement individual slug generation
    // For now, just show a placeholder
    const input = document.getElementById('slug-input');
    if (input) {
      input.value = 'generated-slug-individual';
      updateSlugPreview();
      updateSlugStatus('generated-slug-individual');
    }
  }

  function updateSlugStatus(slug) {
    const statusElement = document.getElementById('slug-status');
    if (statusElement && slug) {
      statusElement.textContent = slug;
    }
  }

  function updateSlugPreview() {
    const input = document.getElementById('slug-input');
    const preview = document.getElementById('slug-preview');
    if (input && preview) {
      preview.textContent = input.value || 'no-slug-generated';
      updateSlugStatus(input.value || 'no-slug-generated');
    }
  }

  function handleUberGeneration(event) {
    console.log('[Slug Panel] Received uber generation event:', event.detail);
    if (event.detail && event.detail.slug) {
      const input = document.getElementById('slug-input');
      if (input) {
        input.value = event.detail.slug;
        updateSlugPreview();
        updateSlugStatus(event.detail.slug);
      }
    }
  }

  // Initialize
  document.addEventListener('DOMContentLoaded', async function() {
    // Initialize accordion with database-backed state persistence
    if (window.headerAccordionManager) {
      await window.headerAccordionManager.initializeAccordion(
        'slug',
        'slug-content',
        'slug-accordion-icon'
      );
    } else {
      // Fallback: Initialize accordion as open by default
      const content = document.getElementById('slug-content');
      const icon = document.getElementById('slug-accordion-icon');
      if (content && icon) {
        content.classList.remove('collapsed');
        icon.classList.add('open');
      }
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
  // window.toggleSlugAccordion = toggleSlugAccordion; // Now managed by HeaderAccordionManager
})();
