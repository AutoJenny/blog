// Header Accordion Manager
// Provides database-backed accordion state persistence for header panels

// Guard against duplicate definition when the script is included more than once
if (!window.HeaderAccordionManager) {
window.HeaderAccordionManager = class HeaderAccordionManager {
  constructor() {
    this.baseUrl = '/header/api/ui/preferences';
  }

  /**
   * Save accordion state to database
   * @param {string} accordionId - Unique identifier for the accordion
   * @param {boolean} isOpen - Whether the accordion is open or closed
   */
  async saveAccordionState(accordionId, isOpen) {
    try {
      const key = `header-accordion-${accordionId}`;
      const value = isOpen ? 'open' : 'closed';
      
      const response = await fetch(`${this.baseUrl}/${encodeURIComponent(key)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value })
      });
      
      if (!response.ok) {
        console.error(`[AccordionManager] Failed to save state for ${accordionId}:`, response.statusText);
      }
    } catch (error) {
      console.error(`[AccordionManager] Error saving accordion state for ${accordionId}:`, error);
    }
  }

  /**
   * Load accordion state from database
   * @param {string} accordionId - Unique identifier for the accordion
   * @returns {Promise<boolean>} - Whether the accordion should be open (default: false - closed)
   */
  async loadAccordionState(accordionId) {
    try {
      const key = `header-accordion-${accordionId}`;
      
      const response = await fetch(`${this.baseUrl}/${encodeURIComponent(key)}`);
      if (!response.ok) {
        console.error(`[AccordionManager] Failed to load state for ${accordionId}:`, response.statusText);
        return false; // Default to closed
      }
      
      const data = await response.json();
      if (data.success && data.value) {
        return data.value === 'open';
      }
      
      return false; // Default to closed if no saved state
    } catch (error) {
      console.error(`[AccordionManager] Error loading accordion state for ${accordionId}:`, error);
      return false; // Default to closed on error
    }
  }

  /**
   * Initialize accordion with database-backed state persistence
   * @param {string} accordionId - Unique identifier for the accordion
   * @param {string} contentId - ID of the content element
   * @param {string} iconId - ID of the icon element
   * @param {Function} toggleFunction - Function to call when accordion is toggled
   */
  async initializeAccordion(accordionId, contentId, iconId, toggleFunction) {
    // Load saved state
    const shouldBeOpen = await this.loadAccordionState(accordionId);
    
    // Apply saved state
    const content = document.getElementById(contentId);
    const icon = document.getElementById(iconId);
    
    if (content && icon) {
      if (shouldBeOpen) {
        content.classList.remove('collapsed');
        icon.classList.add('open');
      } else {
        content.classList.add('collapsed');
        icon.classList.remove('open');
      }
    }
    
    // Set up toggle handler
    const toggleHandler = async () => {
      if (content && icon) {
        const isCurrentlyOpen = !content.classList.contains('collapsed');
        const newState = !isCurrentlyOpen;
        
        // Toggle visual state
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
        
        // Save state to database
        await this.saveAccordionState(accordionId, newState);
        
        // Call custom toggle function if provided
        if (toggleFunction) {
          toggleFunction(newState);
        }
      }
    };
    
    // Store the toggle handler globally so onclick can access it
    const functionName = `toggle${accordionId.split('-').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join('')}Accordion`;
    window[functionName] = toggleHandler;
    
    return toggleHandler;
  }
};
}

// Create global instance (once)
if (!window.headerAccordionManager) {
  window.headerAccordionManager = new window.HeaderAccordionManager();
}
