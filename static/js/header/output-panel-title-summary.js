// Output Panel Title Summary JS
(function() {
  // Note: toggleTitleSummaryOutputAccordion is now managed by HeaderAccordionManager

  function saveTitleSummary() {
    console.log('[Output Panel] Save clicked');
    
    // Collect data from all panels
    const selectedTitle = document.querySelector('input[name="title-selection"]:checked');
    const subtitle = document.getElementById('subtitle-input')?.value || '';
    const summary = document.getElementById('summary-textarea')?.value || '';
    const slug = document.getElementById('slug-input')?.value || '';
    
    const data = {
      title: selectedTitle ? selectedTitle.nextElementSibling.textContent : '',
      subtitle: subtitle,
      summary: summary,
      slug: slug
    };
    
    console.log('[Output Panel] Saving data:', data);
    
    // TODO: Implement actual save API call
    // For now, just show success message
    const saveBtn = document.getElementById('save-title-summary-btn');
    if (saveBtn) {
      saveBtn.innerHTML = '<i class="fas fa-check"></i> Saved!';
      setTimeout(() => {
        saveBtn.innerHTML = 'Save';
      }, 2000);
    }
  }

  function updateOutputDisplay() {
    const selectedTitle = document.querySelector('input[name="title-selection"]:checked');
    const subtitle = document.getElementById('subtitle-input')?.value || '';
    const summary = document.getElementById('summary-textarea')?.value || '';
    const slug = document.getElementById('slug-input')?.value || '';
    
    // Update display elements
    const titleDisplay = document.getElementById('selected-title');
    const subtitleDisplay = document.getElementById('selected-subtitle');
    const summaryDisplay = document.getElementById('generated-summary');
    const slugDisplay = document.getElementById('generated-slug');
    
    if (titleDisplay) {
      titleDisplay.textContent = selectedTitle ? selectedTitle.nextElementSibling.textContent : 'No title selected';
    }
    if (subtitleDisplay) {
      subtitleDisplay.textContent = subtitle || 'No subtitle generated';
    }
    if (summaryDisplay) {
      summaryDisplay.textContent = summary || 'No summary generated';
    }
    if (slugDisplay) {
      slugDisplay.textContent = slug || 'no-slug-generated';
    }
  }

  function handleUberGeneration(event) {
    console.log('[Output Panel] Received uber generation event:', event.detail);
    // Update display after a short delay to allow other panels to update first
    setTimeout(updateOutputDisplay, 100);
  }

  // Initialize
  document.addEventListener('DOMContentLoaded', async function() {
    // Initialize accordion with database-backed state persistence
    if (window.headerAccordionManager) {
      await window.headerAccordionManager.initializeAccordion(
        'title-summary-output',
        'title-summary-output-content',
        'title-summary-output-accordion-icon'
      );
    }
    
    const saveBtn = document.getElementById('save-title-summary-btn');
    if (saveBtn) {
      saveBtn.addEventListener('click', saveTitleSummary);
    }
    
    // Listen for changes in other panels
    document.addEventListener('change', updateOutputDisplay);
    document.addEventListener('input', updateOutputDisplay);
    
    // Listen for uber generation events
    document.addEventListener('uberGenerateTitleSummary', handleUberGeneration);
  });

  // Expose to window for inline onclick
  // window.toggleTitleSummaryOutputAccordion = toggleTitleSummaryOutputAccordion; // Now managed by HeaderAccordionManager
})();
