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

  async function loadExistingData() {
    try {
      const postId = window.postId || window.originalPostId;
      if (!postId) {
        console.warn('[Output Panel] No postId available, skipping data load');
        return;
      }
      
      const response = await fetch(`/header/api/posts/${postId}/get-title-summary`);
      const data = await response.json();
      
      if (data && !data.error) {
        // Update display with loaded data
        const titleDisplay = document.getElementById('selected-title');
        const subtitleDisplay = document.getElementById('selected-subtitle');
        const summaryDisplay = document.getElementById('generated-summary');
        const slugDisplay = document.getElementById('generated-slug');
        
        if (titleDisplay && data.title) {
          titleDisplay.textContent = data.title;
        }
        if (subtitleDisplay && data.subtitle) {
          subtitleDisplay.textContent = data.subtitle;
        }
        if (summaryDisplay && data.summary) {
          summaryDisplay.textContent = data.summary;
        }
        if (slugDisplay && data.slug) {
          slugDisplay.textContent = data.slug;
        }
        
        // Also check if there's a selected title in the title panel
        // The title panel might have loaded titles, so check for selected one
        setTimeout(updateOutputDisplay, 500);
      }
    } catch (error) {
      console.error('[Output Panel] Error loading existing data:', error);
    }
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
    
    // Load existing data from database
    loadExistingData();
    
    // Listen for changes in other panels
    document.addEventListener('change', updateOutputDisplay);
    document.addEventListener('input', updateOutputDisplay);
    
    // Listen for uber generation events
    document.addEventListener('uberGenerateTitleSummary', handleUberGeneration);
  });

  // Expose to window for inline onclick
  // window.toggleTitleSummaryOutputAccordion = toggleTitleSummaryOutputAccordion; // Now managed by HeaderAccordionManager
})();
