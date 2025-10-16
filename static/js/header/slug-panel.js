// Slug Panel JS
(function() {
  // Note: toggleSlugAccordion is now managed by HeaderAccordionManager

  async function generateSlug() {
    console.log('[Slug Panel] Individual generate clicked');
    
    const generateBtn = document.getElementById('generate-slug-btn');
    const input = document.getElementById('slug-input');
    
    if (!generateBtn || !input) return;
    
    generateBtn.disabled = true;
    generateBtn.textContent = 'Generating...';
    
    try {
      const response = await fetch(`/header/api/posts/${window.postId}/generate-slug`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const data = await response.json();
      
      if (data.success) {
        input.value = data.slug;
        updateSlugPreview();
        updateSlugStatus(data.slug);
        
        // Save the generated slug
        await saveSlug(data.slug);
        
        // Disable the generate button since slug is now generated
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generated';
        generateBtn.style.opacity = '0.6';
      } else {
        console.error('Error generating slug:', data.error);
        updateSlugStatus('Error generating slug');
      }
    } catch (error) {
      console.error('Error generating slug:', error);
      updateSlugStatus('Error generating slug');
    } finally {
      generateBtn.disabled = false;
      if (generateBtn.textContent === 'Generating...') {
        generateBtn.textContent = 'Generate';
      }
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
      
      // Auto-save when user manually edits
      if (input.value) {
        saveSlug(input.value);
      }
    }
  }

  async function saveSlug(slug) {
    try {
      const response = await fetch(`/header/api/posts/${window.postId}/save-slug`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ slug: slug })
      });
      
      const data = await response.json();
      if (data.success) {
        console.log('[Slug Panel] Slug saved successfully');
      } else {
        console.error('Error saving slug:', data.error);
      }
    } catch (error) {
      console.error('Error saving slug:', error);
    }
  }

  async function loadExistingSlug() {
    try {
      const response = await fetch(`/header/api/posts/${window.postId}/get-slug`);
      const data = await response.json();
      
      if (data.success && data.slug) {
        const input = document.getElementById('slug-input');
        const generateBtn = document.getElementById('generate-slug-btn');
        
        if (input) {
          input.value = data.slug;
          updateSlugPreview();
          updateSlugStatus(data.slug);
          
          // If slug exists, disable the generate button
          if (generateBtn) {
            generateBtn.disabled = true;
            generateBtn.textContent = 'Generated';
            generateBtn.style.opacity = '0.6';
          }
        }
      }
    } catch (error) {
      console.error('Error loading existing slug:', error);
    }
  }

  function handleUberGeneration(event) {
    console.log('[Slug Panel] Received uber generation event:', event.detail);
    if (event.detail && event.detail.slug) {
      const input = document.getElementById('slug-input');
      const generateBtn = document.getElementById('generate-slug-btn');
      
      if (input) {
        input.value = event.detail.slug;
        updateSlugPreview();
        updateSlugStatus(event.detail.slug);
        
        // Save the slug and disable generate button
        saveSlug(event.detail.slug);
        
        if (generateBtn) {
          generateBtn.disabled = true;
          generateBtn.textContent = 'Generated';
          generateBtn.style.opacity = '0.6';
        }
      }
    }
  }

  // Initialize
  document.addEventListener('DOMContentLoaded', async function() {
    // Load existing slug first
    await loadExistingSlug();
    
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
