// Subtitle Panel JS
(function() {
  // Note: toggleSubtitleAccordion is now managed by HeaderAccordionManager

  function generateSubtitle() {
    console.log('[Subtitle Panel] Individual generate clicked');
    
    // Get post ID from URL
    const urlMatch = window.location.pathname.match(/\/posts\/(\d+)/);
    if (!urlMatch) {
      console.error('[Subtitle Panel] Could not extract post ID from URL');
      return;
    }
    const postId = urlMatch[1];
    
    // Get content from Mini-Preview Development tab
    const ideaSeed = document.querySelector('#dev-selected-idea')?.textContent?.trim() || '';
    const expandedIdea = document.querySelector('#dev-expanded-idea')?.textContent?.trim() || '';
    const sectionContent = document.querySelector('#sections-container')?.textContent?.trim() || '';
    
    // Get selected title from Title Generation panel
    const selectedTitleRadio = document.querySelector('input[name="title-selection"]:checked');
    const selectedTitle = selectedTitleRadio ? selectedTitleRadio.nextElementSibling.textContent.trim() : '';
    
    console.log('[Subtitle Panel] Generating subtitle with:', {
      ideaSeed: ideaSeed.substring(0, 50) + '...',
      expandedIdea: expandedIdea.substring(0, 50) + '...',
      selectedTitle: selectedTitle.substring(0, 50) + '...',
      sectionContent: sectionContent.substring(0, 50) + '...'
    });
    
    // Show loading state
    const container = document.getElementById('subtitle-options');
    if (container) {
      container.innerHTML = '<div class="loading">Generating subtitles...</div>';
    }
    
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
      if (data.success && data.subtitle_options) {
        displaySubtitleOptions(data.subtitle_options, data.selected_index || 0);
        console.log('[Subtitle Panel] Generated subtitles:', data.subtitle_options);
      } else {
        console.error('[Subtitle Panel] Generation failed:', data.error);
        showSubtitleError('Error generating subtitles');
      }
    })
    .catch(error => {
      console.error('[Subtitle Panel] API error:', error);
      showSubtitleError('Error generating subtitles');
    });
  }

  function displaySubtitleOptions(subtitles, selectedIndex = 0) {
    const subtitleOptions = document.getElementById('subtitle-options');
    if (!subtitleOptions) return;
    
    subtitleOptions.innerHTML = '';
    
    subtitles.forEach((subtitle, index) => {
      const optionDiv = document.createElement('div');
      optionDiv.className = 'subtitle-option';
      optionDiv.innerHTML = `
        <input type="radio" name="subtitle-selection" value="${index}" id="subtitle-${index}" ${index === selectedIndex ? 'checked' : ''}>
        <label for="subtitle-${index}">${subtitle}</label>
      `;
      subtitleOptions.appendChild(optionDiv);
      
      // Add change listener
      const radio = optionDiv.querySelector('input[type="radio"]');
      radio.addEventListener('change', function() {
        if (this.checked) {
          saveSelectedSubtitle(subtitle, index);
          updateSubtitleStatus(subtitle);
        }
      });
    });
    
    // Save the initially selected subtitle
    if (subtitles[selectedIndex]) {
      saveSelectedSubtitle(subtitles[selectedIndex], selectedIndex);
      updateSubtitleStatus(subtitles[selectedIndex]);
    }
  }

  function updateSubtitleStatus(selectedSubtitle) {
    const statusElement = document.getElementById('subtitle-status');
    if (statusElement && selectedSubtitle) {
      statusElement.textContent = selectedSubtitle;
    }
  }

  function saveSelectedSubtitle(subtitle, index) {
    console.log(`[Subtitle Panel] Saving selected subtitle: ${subtitle} (index: ${index})`);
    
    // Save to database
    fetch(`/header/api/posts/${window.postId}/save-selected-subtitle`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        subtitle: subtitle,
        subtitle_index: index
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        console.log('[Subtitle Panel] Subtitle saved successfully');
      } else {
        console.error('[Subtitle Panel] Failed to save subtitle:', data.error);
      }
    })
    .catch(error => {
      console.error('[Subtitle Panel] Error saving subtitle:', error);
    });
  }

  function showSubtitleError(message) {
    const container = document.getElementById('subtitle-options');
    if (container) {
      container.innerHTML = `<div class="error">${message}</div>`;
    }
  }

  function loadExistingSubtitles() {
    // Load any existing subtitles from database
    fetch(`/header/api/posts/${window.postId}/get-subtitles`)
    .then(response => response.json())
    .then(data => {
      if (data.success && data.subtitle_options && data.subtitle_options.length > 0) {
        displaySubtitleOptions(data.subtitle_options, data.selected_index || 0);
      }
    })
    .catch(error => {
      console.error('Error loading existing subtitles:', error);
    });
  }

  function handleUberGeneration(event) {
    console.log('[Subtitle Panel] Received uber generation event:', event.detail);
    if (event.detail && event.detail.subtitle_options) {
      displaySubtitleOptions(event.detail.subtitle_options, event.detail.subtitle_selected_index || 0);
    }
  }

  // Initialize
  document.addEventListener('DOMContentLoaded', async function() {
    // Initialize accordion with database-backed state persistence
    if (window.headerAccordionManager) {
      await window.headerAccordionManager.initializeAccordion(
        'subtitle',
        'subtitle-content',
        'subtitle-accordion-icon'
      );
    } else {
      // Fallback: Initialize accordion as open by default
      const content = document.getElementById('subtitle-content');
      const icon = document.getElementById('subtitle-accordion-icon');
      if (content && icon) {
        content.classList.remove('collapsed');
        icon.classList.add('open');
      }
    }
    
    const generateBtn = document.getElementById('generate-subtitle-btn');
    if (generateBtn) {
      generateBtn.addEventListener('click', generateSubtitle);
    }
    
    // Listen for uber generation events
    document.addEventListener('uberGenerateTitleSummary', handleUberGeneration);
    
    // Load existing subtitles on page load
    loadExistingSubtitles();
  });

  // Expose to window for inline onclick
  // window.toggleSubtitleAccordion = toggleSubtitleAccordion; // Now managed by HeaderAccordionManager
})();