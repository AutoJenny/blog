// Summary Generation Panel JS
(function() {
  // Note: toggleSummaryGenerationAccordion is now managed by HeaderAccordionManager

  async function generateSummary() {
    console.log('[Summary Generation Panel] Individual generate clicked');
    try {
      const generateBtn = document.getElementById('generate-summary-btn');
      const textarea = document.getElementById('summary-textarea');
      
      generateBtn.disabled = true;
      generateBtn.textContent = 'Generating...';
      
      // Get content from Mini-Preview Development tab
      const selectedIdea = document.getElementById('dev-selected-idea')?.textContent || '';
      const expandedIdea = document.getElementById('dev-expanded-idea')?.textContent || '';
      
      // Get section content directly from API instead of DOM (more reliable)
      let sectionsContent = '';
      try {
        const sectionsResponse = await fetch(`/authoring/api/posts/${window.postId}/sections`);
        const sectionsData = await sectionsResponse.json();
        
        if (sectionsData.success && sectionsData.sections) {
          sectionsData.sections.forEach((section, index) => {
            console.log(`Section ${index + 1}:`, { 
              title: section.title, 
              description: section.description, 
              draftLength: section.draft ? section.draft.length : 0 
            });
            
            if (section.title) {
              sectionsContent += `\n\n## ${section.title}\n`;
            }
            if (section.description) {
              sectionsContent += `Description: ${section.description}\n`;
            }
            if (section.draft) {
              sectionsContent += `Content: ${section.draft}\n`;
            } else if (section.polished) {
              sectionsContent += `Content: ${section.polished}\n`;
            }
          });
        }
      } catch (error) {
        console.error('Error fetching sections for summary:', error);
      }
      
      // Combine all content
      const fullContent = `Selected Idea: ${selectedIdea}\n\nExpanded Idea: ${expandedIdea}${sectionsContent}`;
      
      // Debug: Log the content being sent
      console.log('Content being sent to summary API:', fullContent);
      
      // Make API call to generate summary
      // Check if week has a post scheduled
      if (!window.weekHasPost) {
        alert('Cannot generate summary: No post is scheduled for this week. Please schedule a post first.');
        return;
      }
      
      // Get year/week from URL or window context
      const urlParams = new URLSearchParams(window.location.search);
      const year = urlParams.get('year') || (window.weekYear && window.weekYear.year);
      const week = urlParams.get('week') || (window.weekYear && window.weekYear.week);
      
      if (!year || !week) {
        alert('Cannot generate summary: Week context (year and week) is required.');
        return;
      }
      
      // Make API call with week context required
      const url = `/header/api/posts/${window.postId}/generate-summary?year=${year}&week=${week}`;
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: fullContent
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success && data.summary) {
        textarea.value = data.summary;
        updateWordCount();
        updateSummaryStatus(data.summary);
        
        // Save the summary to database
        await saveSummary(data.summary);
      } else {
        throw new Error(data.error || 'Failed to generate summary');
      }
      
      generateBtn.disabled = false;
      generateBtn.textContent = 'Generate';
      
    } catch (error) {
      console.error('Error generating summary:', error);
      const generateBtn = document.getElementById('generate-summary-btn');
      generateBtn.disabled = false;
      generateBtn.textContent = 'Generate';
      
      const textarea = document.getElementById('summary-textarea');
      if (textarea) {
        textarea.value = `Error generating summary: ${error.message}`;
        updateWordCount();
      }
    }
  }

  function updateSummaryStatus(summary) {
    const statusElement = document.getElementById('summary-generation-status');
    if (statusElement && summary) {
      // Show first line or two of summary in header (max 80 characters)
      const firstLine = summary.split('\n')[0].trim();
      let displayText = firstLine;
      
      // If first line is very short, try to include part of second line
      if (firstLine.length < 40 && summary.includes('\n')) {
        const lines = summary.split('\n');
        const secondLine = lines[1]?.trim() || '';
        if (secondLine) {
          const combined = `${firstLine} ${secondLine}`;
          displayText = combined.length <= 80 ? combined : firstLine;
        }
      }
      
      // Truncate if too long and add ellipsis
      if (displayText.length > 80) {
        displayText = displayText.substring(0, 77) + '...';
      }
      
      statusElement.textContent = displayText;
    }
  }

  async function saveSummary(summary) {
    try {
      const response = await fetch(`/header/api/posts/${window.postId}/save-summary`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          summary: summary
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || 'Failed to save summary');
      }
      
      console.log('Summary saved successfully');
    } catch (error) {
      console.error('Error saving summary:', error);
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
        updateSummaryStatus(event.detail.summary);
        // Persist summary immediately when generated via uber run
        try { saveSummary(event.detail.summary); } catch(_) {}
      }
    }
  }

  // Load existing summary from database
  async function loadExistingSummary() {
    try {
      const response = await fetch(`/header/api/posts/${window.postId}/get-summary`);
      const data = await response.json();
      
      if (data.success && data.summary) {
        const textarea = document.getElementById('summary-textarea');
        if (textarea) {
          textarea.value = data.summary;
          updateWordCount();
          updateSummaryStatus(data.summary);
        }
      }
    } catch (error) {
      console.error('Error loading existing summary:', error);
    }
  }

  // Initialize
  document.addEventListener('DOMContentLoaded', async function() {
    // Load existing summary
    await loadExistingSummary();
    
    // Initialize accordion with database-backed state persistence
    if (window.headerAccordionManager) {
      await window.headerAccordionManager.initializeAccordion(
        'summary-generation',
        'summary-generation-content',
        'summary-generation-accordion-icon'
      );
    } else {
      // Fallback: Initialize accordion as open by default
      const content = document.getElementById('summary-generation-content');
      const icon = document.getElementById('summary-generation-accordion-icon');
      if (content && icon) {
        content.classList.remove('collapsed');
        icon.classList.add('open');
      }
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
  // window.toggleSummaryGenerationAccordion = toggleSummaryGenerationAccordion; // Now managed by HeaderAccordionManager
})();
