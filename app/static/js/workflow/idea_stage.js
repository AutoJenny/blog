import { initTabs } from './tab_manager.js';

// Initialize tabs and event handlers
document.addEventListener('DOMContentLoaded', async () => {
  // Initialize tabs
  initTabs('idea');

  // Get post ID from URL
  const postId = new URLSearchParams(window.location.search).get('post_id');
  if (!postId) {
    console.error('No post ID found');
    return;
  }

  // Generate Idea
  const generateIdeaButton = document.getElementById('generate-idea');
  if (generateIdeaButton) {
    generateIdeaButton.addEventListener('click', async () => {
      generateIdeaButton.disabled = true;
      generateIdeaButton.textContent = 'Generating...';
      try {
        // TODO: Implement generate idea
        console.log('Generate idea clicked');
      } catch (e) {
        alert('Error generating idea: ' + e.message);
      } finally {
        generateIdeaButton.disabled = false;
        generateIdeaButton.textContent = 'Generate Idea';
      }
    });
  }

  // Generate Themes
  const generateThemesButton = document.getElementById('generate-themes');
  if (generateThemesButton) {
    generateThemesButton.addEventListener('click', async () => {
      generateThemesButton.disabled = true;
      generateThemesButton.textContent = 'Generating...';
      try {
        // TODO: Implement generate themes
        console.log('Generate themes clicked');
      } catch (e) {
        alert('Error generating themes: ' + e.message);
      } finally {
        generateThemesButton.disabled = false;
        generateThemesButton.textContent = 'Generate Themes';
      }
    });
  }

  // Save Idea
  const saveIdeaButton = document.getElementById('save-idea');
  if (saveIdeaButton) {
    saveIdeaButton.addEventListener('click', async () => {
      saveIdeaButton.disabled = true;
      saveIdeaButton.textContent = 'Saving...';
      try {
        // TODO: Implement save idea
        console.log('Save idea clicked');
      } catch (e) {
        alert('Error saving idea: ' + e.message);
      } finally {
        saveIdeaButton.disabled = false;
        saveIdeaButton.textContent = 'Save Idea';
      }
    });
  }

  // Save Themes
  const saveThemesButton = document.getElementById('save-themes');
  if (saveThemesButton) {
    saveThemesButton.addEventListener('click', async () => {
      saveThemesButton.disabled = true;
      saveThemesButton.textContent = 'Saving...';
      try {
        // TODO: Implement save themes
        console.log('Save themes clicked');
      } catch (e) {
        alert('Error saving themes: ' + e.message);
      } finally {
        saveThemesButton.disabled = false;
        saveThemesButton.textContent = 'Save Themes';
      }
    });
  }
});

// Generate basic idea using LLM
async function generateIdea() {
  const title = document.getElementById('provisional_title').value;
  const idea = document.getElementById('basic_idea').value;
  const scope = document.getElementById('idea_scope').value;

  const response = await fetch('/api/v1/idea/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, idea, scope })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to generate idea');
  }

  const result = await response.json();
  
  // Update form fields with generated content
  document.getElementById('basic_idea').value = result.basic_idea;
  document.getElementById('idea_scope').value = result.idea_scope;
}

// Generate themes and audience analysis using LLM
async function generateThemes() {
  const title = document.getElementById('provisional_title').value;
  const idea = document.getElementById('basic_idea').value;
  const scope = document.getElementById('idea_scope').value;

  const response = await fetch('/api/v1/idea/generate_themes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, idea, scope })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to generate themes');
  }

  const result = await response.json();
  
  // Update form fields with generated content
  document.getElementById('target_audience').value = result.target_audience;
  document.getElementById('key_themes').value = result.key_themes;
  document.getElementById('value_proposition').value = result.value_proposition;
}

// Save basic idea
async function saveIdea() {
  const postId = new URLSearchParams(window.location.search).get('post_id');
  const title = document.getElementById('provisional_title').value;
  const idea = document.getElementById('basic_idea').value;
  const scope = document.getElementById('idea_scope').value;

  const response = await fetch(`/api/v1/idea/save/${postId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, idea, scope })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to save idea');
  }
}

// Save themes and audience
async function saveThemes() {
  const postId = new URLSearchParams(window.location.search).get('post_id');
  const audience = document.getElementById('target_audience').value;
  const themes = document.getElementById('key_themes').value;
  const value = document.getElementById('value_proposition').value;

  const response = await fetch(`/api/v1/idea/save_themes/${postId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ audience, themes, value })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to save themes');
  }
} 