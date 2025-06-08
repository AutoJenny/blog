// app/static/js/workflow/structure_stage.js

// Remove static specimen data
delete window.sections;
let sections = [];

// Tab switching functionality
function initTabs() {
  const tabs = document.querySelectorAll('[data-tab]');
  const contents = document.querySelectorAll('.tab-content');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      // Update active tab
      tabs.forEach(t => {
        t.classList.remove('border-b-2', 'border-blue-500', 'active-tab');
        t.classList.add('text-gray-300');
      });
      tab.classList.add('border-b-2', 'border-blue-500', 'active-tab');
      tab.classList.remove('text-gray-300');

      // Show selected content
      const targetId = tab.getAttribute('data-tab');
      contents.forEach(content => {
        content.classList.add('hidden');
        if (content.id === targetId) {
          content.classList.remove('hidden');
        }
      });
    });
  });
}

function renderSections(list, sections) {
  list.innerHTML = '';
  sections.forEach((section, idx) => {
    const li = document.createElement('li');
    li.className = 'bg-gray-700 rounded p-4 flex items-center justify-between cursor-move';
    li.setAttribute('data-id', section.id || idx + 1);
    li.innerHTML = `
      <div class="flex-1">
        <div class="font-bold text-gray-100">${idx + 1}. ${section.heading}</div>
        <div class="text-sm text-gray-300 mt-1">${section.description}</div>
      </div>
      <span class="text-gray-400 ml-4">&#x2630;</span>
    `;
    list.appendChild(li);
  });
}

function renderAllocatedItems(container, sections) {
  container.innerHTML = '';
  sections.forEach((section, idx) => {
    const div = document.createElement('div');
    div.className = 'bg-gray-700 rounded p-4';
    div.innerHTML = `
      <h3 class="font-bold text-gray-100 mb-2">${idx + 1}. ${section.title || section.name || section.heading}</h3>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <h4 class="text-sm font-semibold text-gray-300 mb-1">Ideas</h4>
          <div class="flex flex-wrap gap-2">
            ${(section.ideas || []).map(idea => `
              <span class="bg-green-900 text-white px-2 py-1 rounded text-sm">${idea}</span>
            `).join('')}
          </div>
        </div>
        <div>
          <h4 class="text-sm font-semibold text-gray-300 mb-1">Facts</h4>
          <div class="flex flex-wrap gap-2">
            ${(section.facts || []).map(fact => `
              <span class="bg-blue-900 text-white px-2 py-1 rounded text-sm">${fact}</span>
            `).join('')}
          </div>
        </div>
      </div>
    `;
    container.appendChild(div);
  });
}

function renderUnassignedItems(ideasContainer, factsContainer, sections) {
  // Get all ideas and facts from sections
  const allIdeas = sections.flatMap(s => s.ideas || []);
  const allFacts = sections.flatMap(s => s.facts || []);

  // Render unassigned ideas
  ideasContainer.innerHTML = allIdeas.map(idea => `
    <span class="bg-green-900 text-white px-2 py-1 rounded text-sm">${idea}</span>
  `).join('');

  // Render unassigned facts
  factsContainer.innerHTML = allFacts.map(fact => `
    <span class="bg-blue-900 text-white px-2 py-1 rounded text-sm">${fact}</span>
  `).join('');
}

async function planSectionsLLM(inputs) {
  try {
    const resp = await fetch('/api/v1/structure/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: inputs.title,
        idea: inputs.idea,
        facts: inputs.facts
      })
    });

    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.error || 'Failed to generate structure');
    }

    const result = await resp.json();
    return {
      sections: result.sections.map(section => ({
        heading: section.heading,
        description: section.description,
        ideas: [],
        facts: []
      }))
    };
  } catch (error) {
    console.error('Error planning sections:', error);
    throw error;
  }
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
  const resp = await fetch(`/api/v1/posts/${postId}/development`);
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

  const resp = await fetch(`/blog/api/v1/structure/save/${postId}`, {
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

async function loadExistingSections(postId) {
  try {
    const resp = await fetch(`/api/v1/posts/${postId}/structure`);
    if (!resp.ok) throw new Error('Failed to load sections');
    const data = await resp.json();
    
    // Map DB fields to UI fields
    sections = data.sections.map(section => ({
      id: section.id,
      title: section.heading,
      description: section.description,
      ideas: JSON.parse(section.ideas_to_include || '[]'),
      facts: JSON.parse(section.facts_to_include || '[]')
    }));
    
    // Render sections in both tabs
    const list = document.getElementById('sections-list');
    const allocatedItems = document.getElementById('allocated-items');
    const unassignedIdeas = document.getElementById('unassigned-ideas');
    const unassignedFacts = document.getElementById('unassigned-facts');
    
    if (list) renderSections(list, sections);
    if (allocatedItems) renderAllocatedItems(allocatedItems, sections);
    if (unassignedIdeas && unassignedFacts) {
      renderUnassignedItems(unassignedIdeas, unassignedFacts, sections);
    }
  } catch (e) {
    console.error('Error loading sections:', e);
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  // Initialize tabs
  initTabs();

  const postId = getPostId();
  if (!postId) {
    console.error('No post ID found');
    return;
  }

  // Initialize editable lists for ideas and facts
  const ideasContainer = document.getElementById('ideas-list');
  const factsContainer = document.getElementById('facts-list');
  
  if (ideasContainer) {
    const ideas = parseMultilineInput(document.getElementById('basic_idea').value);
    renderEditableList(ideasContainer, ideas, 'Idea');
  }
  
  if (factsContainer) {
    const facts = parseMultilineInput(document.getElementById('interesting_facts').value);
    renderEditableList(factsContainer, facts, 'Fact');
  }

  // Load existing sections
  await loadExistingSections(postId);

  // Initialize Sortable for sections list
  const list = document.getElementById('sections-list');
  if (list) {
    new Sortable(list, {
      animation: 150,
      handle: '.text-gray-400',
      onEnd: function(evt) {
        const item = evt.item;
        const newIndex = evt.newIndex;
        const oldIndex = evt.oldIndex;
        
        // Update sections array
        const [movedSection] = sections.splice(oldIndex, 1);
        sections.splice(newIndex, 0, movedSection);
      }
    });
  }

  // Add event listeners for plan and save buttons
  const planButton = document.getElementById('plan-sections');
  if (planButton) {
    planButton.addEventListener('click', async () => {
      try {
        const inputs = {
          title: document.getElementById('provisional_title').value,
          idea: document.getElementById('basic_idea').value,
          facts: document.getElementById('interesting_facts').value
        };
        
        const result = await planSectionsLLM(inputs);
        sections = result.sections;
        
        // Render the new sections
        if (list) renderSections(list, sections);
        
        // Show success message
        alert('Sections planned successfully!');
      } catch (error) {
        console.error('Error planning sections:', error);
        alert('Failed to plan sections: ' + error.message);
      }
    });
  }

  const saveButton = document.getElementById('save-structure');
  if (saveButton) {
    saveButton.addEventListener('click', async () => {
      try {
        await saveStructure(sections);
        alert('Structure saved successfully!');
      } catch (error) {
        console.error('Error saving structure:', error);
        alert('Failed to save structure: ' + error.message);
      }
    });
  }
}); 