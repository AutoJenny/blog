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
    
    const input = document.getElementById('subtitle-input');
    if (!input) return;
    
    // Get post ID from URL
    const urlMatch = window.location.pathname.match(/\/posts\/(\d+)/);
    if (!urlMatch) {
      console.error('[Subtitle Panel] Could not extract post ID from URL');
      return;
    }
    const postId = urlMatch[1];
    
    // Get content from Mini-Preview Development tab
    const ideaSeed = document.querySelector('#idea-seed-content')?.textContent?.trim() || '';
    const expandedIdea = document.querySelector('#expanded-idea-content')?.textContent?.trim() || '';
    const sectionContent = document.querySelector('#section-content')?.textContent?.trim() || '';
    
    // Get selected title from Title Generation panel
    const selectedTitleRadio = document.querySelector('input[name="title-option"]:checked');
    const selectedTitle = selectedTitleRadio ? selectedTitleRadio.nextElementSibling.textContent.trim() : '';
    
    console.log('[Subtitle Panel] Generating subtitle with:', {
      ideaSeed: ideaSeed.substring(0, 50) + '...',
      expandedIdea: expandedIdea.substring(0, 50) + '...',
      selectedTitle: selectedTitle.substring(0, 50) + '...',
      sectionContent: sectionContent.substring(0, 50) + '...'
    });
    
    // Show loading state
    input.value = 'Generating subtitle...';
    input.disabled = true;
    
    // Make API call
    fetch(`/header/api/posts/${postId}/generate-subtitle`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        idea_seed: ideaSeed,
        expanded_idea: expandedIdea,
        selected_title: selectedTitle,
        section_content: sectionContent
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        input.value = data.subtitle;
        console.log('[Subtitle Panel] Generated subtitle:', data.subtitle);
      } else {
        console.error('[Subtitle Panel] Generation failed:', data.error);
        input.value = 'Error generating subtitle';
      }
    })
    .catch(error => {
      console.error('[Subtitle Panel] API error:', error);
      input.value = 'Error generating subtitle';
    })
    .finally(() => {
      input.disabled = false;
    });
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


