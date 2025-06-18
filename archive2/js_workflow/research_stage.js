import { initTabs } from './tab_manager.js';

// Initialize tabs and event handlers
document.addEventListener('DOMContentLoaded', async () => {
  // Initialize tabs
  initTabs('research');

  // Get post ID from URL
  const postId = new URLSearchParams(window.location.search).get('post_id');
  if (!postId) {
    console.error('No post ID found');
    return;
  }

  // Generate Ideas
  const generateIdeasButton = document.getElementById('generate-ideas');
  if (generateIdeasButton) {
    generateIdeasButton.addEventListener('click', async () => {
      generateIdeasButton.disabled = true;
      generateIdeasButton.textContent = 'Generating...';
      try {
        // TODO: Implement generate ideas
        console.log('Generate ideas clicked');
      } catch (e) {
        alert('Error generating ideas: ' + e.message);
      } finally {
        generateIdeasButton.disabled = false;
        generateIdeasButton.textContent = 'Generate Ideas';
      }
    });
  }

  // Generate Facts
  const generateFactsButton = document.getElementById('generate-facts');
  if (generateFactsButton) {
    generateFactsButton.addEventListener('click', async () => {
      generateFactsButton.disabled = true;
      generateFactsButton.textContent = 'Generating...';
      try {
        // TODO: Implement generate facts
        console.log('Generate facts clicked');
      } catch (e) {
        alert('Error generating facts: ' + e.message);
      } finally {
        generateFactsButton.disabled = false;
        generateFactsButton.textContent = 'Generate Facts';
      }
    });
  }

  // Save Ideas
  const saveIdeasButton = document.getElementById('save-ideas');
  if (saveIdeasButton) {
    saveIdeasButton.addEventListener('click', async () => {
      saveIdeasButton.disabled = true;
      saveIdeasButton.textContent = 'Saving...';
      try {
        // TODO: Implement save ideas
        console.log('Save ideas clicked');
      } catch (e) {
        alert('Error saving ideas: ' + e.message);
      } finally {
        saveIdeasButton.disabled = false;
        saveIdeasButton.textContent = 'Save Ideas';
      }
    });
  }

  // Save Facts
  const saveFactsButton = document.getElementById('save-facts');
  if (saveFactsButton) {
    saveFactsButton.addEventListener('click', async () => {
      saveFactsButton.disabled = true;
      saveFactsButton.textContent = 'Saving...';
      try {
        // TODO: Implement save facts
        console.log('Save facts clicked');
      } catch (e) {
        alert('Error saving facts: ' + e.message);
      } finally {
        saveFactsButton.disabled = false;
        saveFactsButton.textContent = 'Save Facts';
      }
    });
  }
});

// Placeholder async functions for LLM and save actions
async function generateIdeas() { /* ... */ }
async function generateFacts() { /* ... */ }
async function saveIdeas() { /* ... */ }
async function saveFacts() { /* ... */ } 