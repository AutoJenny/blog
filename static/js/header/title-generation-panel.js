// Title Generation Panel JS
(function() {
  // Note: toggleTitleGenerationAccordion is now managed by HeaderAccordionManager

  function generateTitles() {
    console.log('[Title Generation Panel] Individual generate clicked');
    
    // Get content from Development tab
    const selectedIdea = document.getElementById('dev-selected-idea')?.textContent || '';
    const expandedIdea = document.getElementById('dev-expanded-idea')?.textContent || '';
    
    // Get section content
    const sectionsContainer = document.getElementById('sections-container');
    let sectionContent = '';
    if (sectionsContainer) {
      const sectionItems = sectionsContainer.querySelectorAll('.section-item');
      sectionItems.forEach((item, index) => {
        const title = item.querySelector('.section-title')?.textContent || `Section ${index + 1}`;
        const content = item.querySelector('.section-draft')?.textContent || 'No content';
        sectionContent += `${title}: ${content}\n\n`;
      });
    }
    
    // Check if week has a post scheduled
    if (!window.weekHasPost) {
      alert('Cannot generate titles: No post is scheduled for this week. Please schedule a post first.');
      return;
    }
    
    // Get year/week from URL or window context
    const urlParams = new URLSearchParams(window.location.search);
    const year = urlParams.get('year') || (window.weekYear && window.weekYear.year);
    const week = urlParams.get('week') || (window.weekYear && window.weekYear.week);
    
    if (!year || !week) {
      alert('Cannot generate titles: Week context (year and week) is required.');
      return;
    }
    
    // Make API call with Development tab content (with week context required)
    const url = `/header/api/posts/${window.postId}/generate-titles?year=${year}&week=${week}`;
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        idea_seed: selectedIdea,
        expanded_idea: expandedIdea,
        section_content: sectionContent
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success && data.title_options) {
        displayTitleOptions(data.title_options, data.selected_index || 0);
      } else {
        console.error('Failed to generate titles:', data.error);
        showTitleError(data.error || 'Failed to generate titles');
      }
    })
    .catch(error => {
      console.error('Error generating titles:', error);
      showTitleError('Error generating titles');
    });
  }

  function displayTitleOptions(titles, selectedIndex = 0) {
    const titleOptions = document.getElementById('title-options');
    if (!titleOptions) return;
    
    // Update button text to "Regenerate" since we have titles
    const generateBtn = document.getElementById('generate-titles-btn');
    if (generateBtn && titles.length > 0) {
      generateBtn.textContent = 'Regenerate';
    }
    
    titleOptions.innerHTML = '';
    
    titles.forEach((title, index) => {
      const optionDiv = document.createElement('div');
      optionDiv.className = 'title-option';
      optionDiv.innerHTML = `
        <input type="radio" name="title-selection" value="${index}" id="title-${index}" ${index === selectedIndex ? 'checked' : ''}>
        <label for="title-${index}">${title}</label>
      `;
      titleOptions.appendChild(optionDiv);
      
      // Add change listener
      const radio = optionDiv.querySelector('input[type="radio"]');
      radio.addEventListener('change', function() {
        if (this.checked) {
          saveSelectedTitle(title, index);
          updateTitleStatus(title);
        }
      });
    });
    
    // Save the initially selected title
    if (titles[selectedIndex]) {
      saveSelectedTitle(titles[selectedIndex], selectedIndex);
      updateTitleStatus(titles[selectedIndex]);
    }
  }

  function updateTitleStatus(selectedTitle) {
    const statusElement = document.getElementById('title-generation-status');
    if (statusElement && selectedTitle) {
      statusElement.textContent = selectedTitle;
    }
  }

  function saveSelectedTitle(title, index) {
    console.log(`[Title Generation Panel] Saving selected title: ${title} (index: ${index})`);
    
    // Save to database
    fetch(`/header/api/posts/${window.postId}/save-selected-title`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: title,
        title_index: index,
        title_options: Array.from(document.querySelectorAll('input[name="title-selection"]')).map(radio => 
          radio.nextElementSibling.textContent
        )
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        console.log('[Title Generation Panel] Title saved successfully');
        // Emit event to update other panels
        document.dispatchEvent(new CustomEvent('titleSelected', {
          detail: { title: title, index: index }
        }));
      } else {
        console.error('Failed to save title:', data.error);
      }
    })
    .catch(error => {
      console.error('Error saving title:', error);
    });
  }

  function showTitleError(error) {
    const titleOptions = document.getElementById('title-options');
    if (titleOptions) {
      titleOptions.innerHTML = `<div class="error-message">Error: ${error}</div>`;
    }
  }

  function handleUberGeneration(event) {
    console.log('[Title Generation Panel] Received uber generation event:', event.detail);
    if (event.detail && event.detail.title_options) {
      displayTitleOptions(event.detail.title_options, event.detail.selected_index || 0);
    }
  }

  function loadExistingTitles() {
    // Load any existing titles from database
    fetch(`/header/api/posts/${window.postId}/get-titles`)
    .then(response => response.json())
    .then(data => {
      if (data.success && data.title_options && data.title_options.length > 0) {
        displayTitleOptions(data.title_options, data.selected_index || 0);
        // Update button text to "Regenerate" since titles exist
        const generateBtn = document.getElementById('generate-titles-btn');
        if (generateBtn) {
          generateBtn.textContent = 'Regenerate';
        }
      }
    })
    .catch(error => {
      console.error('Error loading existing titles:', error);
    });
  }

  // Initialize
  document.addEventListener('DOMContentLoaded', async function() {
    // Initialize accordion with database-backed state persistence
    if (window.headerAccordionManager) {
      await window.headerAccordionManager.initializeAccordion(
        'title-generation',
        'title-generation-content',
        'title-generation-accordion-icon'
      );
    } else {
      // Fallback: Initialize accordion as open by default
      const content = document.getElementById('title-generation-content');
      const icon = document.getElementById('title-generation-accordion-icon');
      if (content && icon) {
        content.classList.remove('collapsed');
        icon.classList.add('open');
      }
    }
    
    const generateBtn = document.getElementById('generate-titles-btn');
    if (generateBtn) {
      generateBtn.addEventListener('click', generateTitles);
    }
    
    // Listen for uber generation events
    document.addEventListener('uberGenerateTitleSummary', handleUberGeneration);
    
    // Load existing titles on page load
    loadExistingTitles();
  });

  // Expose to window for inline onclick
  // window.toggleTitleGenerationAccordion = toggleTitleGenerationAccordion; // Now managed by HeaderAccordionManager
})();
