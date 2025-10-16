// Prompt View Panel JavaScript
(function() {
  // Global functions for accordion toggle
  // Note: togglePromptViewAccordion is now managed by HeaderAccordionManager

  // Initialize prompt view panel
  function initPromptViewPanel(panelType, stepId) {
    console.log(`[Prompt View Panel] Initializing for ${panelType}, step ID: ${stepId}`);
    
    // Load prompts from database
    loadPrompts(panelType, stepId);
    
    // Set up edit functionality
    setupEditMode(panelType, stepId);
  }

  // Load prompts from database
  async function loadPrompts(panelType, stepId) {
    try {
      console.log(`[Prompt View Panel] Loading prompts for step ${stepId}`);
      
      // Fetch prompts from workflow_step_prompt table
      const response = await fetch(`/header/api/prompts/${stepId}`);
      const data = await response.json();
      
      if (data.success) {
        // Update system prompt
        const systemPromptElement = document.getElementById(`system-prompt-${panelType}`);
        if (systemPromptElement) {
          const promptText = systemPromptElement.querySelector('.prompt-text');
          if (promptText) {
            promptText.textContent = data.system_prompt || 'No system prompt found';
          }
        }
        
        // Update task prompt
        const taskPromptElement = document.getElementById(`task-prompt-${panelType}`);
        if (taskPromptElement) {
          const promptText = taskPromptElement.querySelector('.prompt-text');
          if (promptText) {
            promptText.textContent = data.task_prompt || 'No task prompt found';
          }
        }
        
        console.log(`[Prompt View Panel] Prompts loaded successfully for ${panelType}`);
      } else {
        console.error(`[Prompt View Panel] Failed to load prompts:`, data.error);
        showPromptError(panelType, data.error);
      }
    } catch (error) {
      console.error(`[Prompt View Panel] Error loading prompts:`, error);
      showPromptError(panelType, 'Failed to load prompts');
    }
  }

  // Show error state
  function showPromptError(panelType, error) {
    const systemPromptElement = document.getElementById(`system-prompt-${panelType}`);
    const taskPromptElement = document.getElementById(`task-prompt-${panelType}`);
    
    if (systemPromptElement) {
      const promptText = systemPromptElement.querySelector('.prompt-text');
      if (promptText) {
        promptText.textContent = `Error: ${error}`;
        promptText.style.color = '#ef4444';
      }
    }
    
    if (taskPromptElement) {
      const promptText = taskPromptElement.querySelector('.prompt-text');
      if (promptText) {
        promptText.textContent = `Error: ${error}`;
        promptText.style.color = '#ef4444';
      }
    }
  }

  // Set up edit mode functionality
  function setupEditMode(panelType, stepId) {
    const editBtn = document.getElementById(`edit-prompts-btn-${panelType}`);
    const saveBtn = document.getElementById(`save-prompts-btn-${panelType}`);
    const cancelBtn = document.getElementById(`cancel-edit-btn-${panelType}`);
    const editMode = document.getElementById(`prompt-edit-mode-${panelType}`);
    
    if (!editBtn || !saveBtn || !cancelBtn || !editMode) return;
    
    // Edit button click
    editBtn.addEventListener('click', function() {
      console.log(`[Prompt View Panel] Entering edit mode for ${panelType}`);
      
      // Populate edit fields with current values
      const systemPromptText = document.querySelector(`#system-prompt-${panelType} .prompt-text`).textContent;
      const taskPromptText = document.querySelector(`#task-prompt-${panelType} .prompt-text`).textContent;
      
      document.getElementById(`system-prompt-edit-${panelType}`).value = systemPromptText;
      document.getElementById(`task-prompt-edit-${panelType}`).value = taskPromptText;
      
      // Show edit mode
      editMode.style.display = 'block';
      editBtn.style.display = 'none';
    });
    
    // Save button click
    saveBtn.addEventListener('click', async function() {
      console.log(`[Prompt View Panel] Saving prompts for ${panelType}`);
      
      const systemPrompt = document.getElementById(`system-prompt-edit-${panelType}`).value;
      const taskPrompt = document.getElementById(`task-prompt-edit-${panelType}`).value;
      
      try {
        const response = await fetch(`/header/api/prompts/${stepId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            system_prompt: systemPrompt,
            task_prompt: taskPrompt
          })
        });
        
        const data = await response.json();
        
        if (data.success) {
          console.log(`[Prompt View Panel] Prompts saved successfully for ${panelType}`);
          
          // Update display with new values
          document.querySelector(`#system-prompt-${panelType} .prompt-text`).textContent = systemPrompt;
          document.querySelector(`#task-prompt-${panelType} .prompt-text`).textContent = taskPrompt;
          
          // Hide edit mode
          editMode.style.display = 'none';
          editBtn.style.display = 'inline-block';
        } else {
          console.error(`[Prompt View Panel] Failed to save prompts:`, data.error);
          alert(`Failed to save prompts: ${data.error}`);
        }
      } catch (error) {
        console.error(`[Prompt View Panel] Error saving prompts:`, error);
        alert(`Error saving prompts: ${error.message}`);
      }
    });
    
    // Cancel button click
    cancelBtn.addEventListener('click', function() {
      console.log(`[Prompt View Panel] Cancelling edit for ${panelType}`);
      
      // Hide edit mode
      editMode.style.display = 'none';
      editBtn.style.display = 'inline-block';
    });
  }

  // Initialize panels when DOM is ready
  document.addEventListener('DOMContentLoaded', function() {
    // Initialize each panel type with its corresponding step ID
    // Title Generation (step 60)
    if (document.getElementById('prompt-view-panel-title')) {
      initPromptViewPanel('title', 60);
    }
    
    // Subtitle Generation (step 61)
    if (document.getElementById('prompt-view-panel-subtitle')) {
      initPromptViewPanel('subtitle', 61);
    }
    
    // Summary Generation (step 62)
    if (document.getElementById('prompt-view-panel-summary')) {
      initPromptViewPanel('summary', 62);
    }
  });
})();
