// app/static/js/workflow/structure_stage.js

// Remove static specimen data
delete window.sections;
let sections = [];

function renderSections(list, sections) {
  list.innerHTML = '';
  sections.forEach((section, idx) => {
    const li = document.createElement('li');
    li.className = 'bg-gray-700 rounded p-4 flex items-center justify-between cursor-move';
    li.setAttribute('data-id', section.id || idx + 1);
    li.innerHTML = `
      <div>
        <span class="font-bold text-gray-100">${idx + 1}. ${section.title || section.name}</span>
        <span class="ml-4 text-xs text-gray-300">Themes: ${(section.ideas || section.themes || []).join(', ')}</span>
        <span class="ml-4 text-xs text-gray-300">Facts: ${(section.facts || []).join(', ')}</span>
      </div>
      <span class="text-gray-400">&#x2630;</span>
    `;
    list.appendChild(li);
  });
}

async function planSectionsLLM(inputs) {
  const resp = await fetch('/blog/api/v1/structure/plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(inputs)
  });
  if (!resp.ok) throw new Error('Failed to plan sections');
  return await resp.json();
}

// Utility: get post_id from URL or data attribute
function getPostId() {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has('post_id')) return urlParams.get('post_id');
  // Try data attribute on root
  const root = document.getElementById('sections-list');
  if (root && root.dataset.postId) return root.dataset.postId;
  return null;
}

async function fetchPostDevelopment(postId) {
  const resp = await fetch(`/blog/api/v1/post/${postId}/development`);
  if (!resp.ok) return null;
  return await resp.json();
}

// Utility to parse multi-line text into array
function parseMultilineInput(input) {
  return input.split('\n').map(line => line.trim()).filter(line => line.length > 0);
}

// Render editable, draggable list for a given array and container
function renderEditableList(container, items, label) {
  container.innerHTML = '';
  items.forEach((item, idx) => {
    const div = document.createElement('div');
    div.className = 'flex items-center mb-1 bg-green-900 text-white rounded px-2 py-1';
    div.innerHTML = `
      <input type="text" value="${item}" style="background:#14532d;color:#fff;border:1px solid #166534;" class="input-sm flex-1 mr-2 rounded" data-idx="${idx}" />
      <button class="btn btn-xs btn-danger" data-action="remove" data-idx="${idx}">Remove</button>
    `;
    container.appendChild(div);
  });
  // Add button
  const addBtn = document.createElement('button');
  addBtn.className = 'btn btn-xs btn-success mt-1';
  addBtn.textContent = `Add ${label}`;
  addBtn.addEventListener('click', () => {
    items.push('');
    renderEditableList(container, items, label);
  });
  container.appendChild(addBtn);
  // Remove handler
  container.querySelectorAll('button[data-action="remove"]').forEach(btn => {
    btn.addEventListener('click', e => {
      const idx = parseInt(btn.getAttribute('data-idx'));
      items.splice(idx, 1);
      renderEditableList(container, items, label);
    });
  });
  // Edit handler
  container.querySelectorAll('input[type="text"]').forEach(input => {
    input.addEventListener('input', e => {
      const idx = parseInt(input.getAttribute('data-idx'));
      items[idx] = input.value;
    });
  });
}

async function saveStructure(sections) {
  const postId = getPostId();
  if (!postId) {
    throw new Error('No post ID found');
  }

  const resp = await fetch(`/api/v1/structure/save/${postId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sections })
  });

  if (!resp.ok) {
    const error = await resp.json();
    throw new Error(error.error || 'Failed to save structure');
  }

  return await resp.json();
}

async function planStructure(title, idea, facts) {
  const resp = await fetch('/api/v1/structure/plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, idea, facts })
  });

  if (!resp.ok) {
    const error = await resp.json();
    throw new Error(error.error || 'Failed to plan structure');
  }

  return await resp.json();
}

async function getStructure(postId) {
  const resp = await fetch(`/api/v1/posts/${postId}/structure`);
  
  if (!resp.ok) {
    const error = await resp.json();
    throw new Error(error.error || 'Failed to get structure');
  }

  return await resp.json();
}

async function loadExistingSections(postId) {
  try {
    const resp = await fetch(`/blog/api/v1/post/${postId}/sections`);
    if (!resp.ok) throw new Error('Failed to load sections');
    const data = await resp.json();
    // Map DB fields to UI fields
    sections = data.map(section => ({
      id: section.id,
      title: section.section_heading,
      description: section.section_description,
      ideas: JSON.parse(section.ideas_to_include || '[]'),
      facts: JSON.parse(section.facts_to_include || '[]')
    }));
    const list = document.getElementById('sections-list');
    if (list) renderSections(list, sections);
  } catch (e) {
    console.error('Error loading sections:', e);
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  const list = document.getElementById('sections-list');
  if (!list) return;
  const postId = getPostId();
  if (postId) {
    // Load and render sections
    await loadExistingSections(postId);
    // Load and set input fields
    try {
      const dev = await fetchPostDevelopment(postId);
      if (dev) {
        const titleInput = document.querySelector('input[type="text"]');
        const ideaTextarea = document.querySelectorAll('textarea')[0];
        const factsTextarea = document.querySelectorAll('textarea')[1];
        if (titleInput && dev.provisional_title) titleInput.value = dev.provisional_title;
        if (ideaTextarea && dev.basic_idea) ideaTextarea.value = dev.basic_idea;
        if (factsTextarea && dev.interesting_facts) factsTextarea.value = dev.interesting_facts;
      }
    } catch (e) {
      console.error('Error loading post development:', e);
    }
  }

  // Initialize SortableJS
  new window.Sortable(list, {
    animation: 150,
    handle: '.cursor-move',
    onEnd: function (evt) {
      // Update sections array to reflect new order
      const newOrder = Array.from(list.children).map(li => parseInt(li.getAttribute('data-id')));
      sections.sort((a, b) => newOrder.indexOf(a.id) - newOrder.indexOf(b.id));
      renderSections(list, sections); // Re-render to update indices
    }
  });

  // Wire up Plan Sections (LLM) button
  const planBtn = document.querySelector('.btn-primary');
  if (planBtn) {
    planBtn.addEventListener('click', async () => {
      planBtn.disabled = true;
      planBtn.textContent = 'Planning...';
      try {
        // Get input values
        const title = document.querySelector('input[type="text"]')?.value || '';
        const idea = document.querySelectorAll('textarea')[0]?.value || '';
        const facts = parseMultilineInput(document.querySelectorAll('textarea')[1]?.value || '');
        const inputs = { title, idea, facts };
        const result = await planSectionsLLM(inputs);
        // Expect result.sections as array
        if (Array.isArray(result.sections)) {
          sections = result.sections;
          renderSections(list, sections);
          
          // Auto-save the sections
          try {
            const formattedSections = sections.map(section => ({
              title: section.name,
              description: section.description || '',
              ideas: section.themes || [],
              facts: section.facts || []
            }));
            await saveStructure(formattedSections);
            console.log('Sections auto-saved successfully');
          } catch (e) {
            console.error('Error auto-saving sections:', e);
            alert('Error auto-saving sections: ' + e.message);
          }
        } else {
          alert('LLM did not return a valid section plan.');
        }
      } catch (e) {
        alert('Error planning sections: ' + e.message);
      } finally {
        planBtn.disabled = false;
        planBtn.textContent = 'Plan Sections (LLM)';
      }
    });
  }

  // Add containers for editable lists
  const ideaTextarea = document.querySelectorAll('textarea')[0];
  const factsTextarea = document.querySelectorAll('textarea')[1];
  let ideaList = parseMultilineInput(ideaTextarea.value || '');
  let factsList = parseMultilineInput(factsTextarea.value || '');
  // Create containers
  const ideaListContainer = document.createElement('div');
  ideaTextarea.parentNode.appendChild(ideaListContainer);
  renderEditableList(ideaListContainer, ideaList, 'Idea');
  const factsListContainer = document.createElement('div');
  factsTextarea.parentNode.appendChild(factsListContainer);
  renderEditableList(factsListContainer, factsList, 'Fact');

  // Wire up Accept Structure button for manual saves
  const acceptBtn = document.querySelector('.btn-success');
  if (acceptBtn) {
    acceptBtn.addEventListener('click', async () => {
      acceptBtn.disabled = true;
      acceptBtn.textContent = 'Saving...';
      try {
        // Transform sections to match backend format
        const formattedSections = sections.map(section => ({
          title: section.name,
          description: section.description || '',
          ideas: section.themes || [],
          facts: section.facts || []
        }));

        await saveStructure(formattedSections);
        alert('Changes saved successfully!');
      } catch (e) {
        alert('Error saving changes: ' + e.message);
      } finally {
        acceptBtn.disabled = false;
        acceptBtn.textContent = 'Save Changes';
      }
    });
  }
}); 