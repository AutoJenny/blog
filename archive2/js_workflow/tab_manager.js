/**
 * Manages tab switching functionality for workflow stages
 * @param {string} stageId - The ID of the stage (e.g., 'structure', 'idea')
 */
function initTabs(stageId) {
  const tabs = document.querySelectorAll(`[data-tab]`);
  const contents = document.querySelectorAll('.tab-content');

  // Set initial active tab
  let activeTab = document.querySelector('.active-tab');
  if (!activeTab && tabs.length > 0) {
    activeTab = tabs[0];
    activeTab.classList.add('active-tab');
  }

  // Show initial content
  if (activeTab) {
    const tabId = activeTab.getAttribute('data-tab');
    contents.forEach(content => {
      if (content.id === tabId) {
        content.classList.remove('hidden');
      } else {
        content.classList.add('hidden');
      }
    });
  }

  // Add click handlers
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      // Update active tab
      tabs.forEach(t => t.classList.remove('active-tab'));
      tab.classList.add('active-tab');

      // Show corresponding content
      const tabId = tab.getAttribute('data-tab');
      contents.forEach(content => {
        if (content.id === tabId) {
          content.classList.remove('hidden');
        } else {
          content.classList.add('hidden');
        }
      });
    });
  });
}

// Make initTabs available globally
window.initTabs = initTabs; 