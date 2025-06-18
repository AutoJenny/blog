// DEPRECATED: All test-related code is deprecated and must not be used. Test UI and endpoints are disabled for safety.

// Configuration
document.getElementById('config-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    try {
        const response = await fetch('/api/v1/llm/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(Object.fromEntries(formData)),
        });
        const result = await response.json();
        if (result.success) {
            // Update displayed values
            document.getElementById('current-provider').textContent = formData.get('provider_type');
            document.getElementById('current-model').textContent = formData.get('model_name');
            document.getElementById('current-api-base').textContent = formData.get('api_base');
            alert('Configuration updated successfully');
        } else {
            alert('Error updating configuration: ' + result.error);
        }
    } catch (error) {
        alert('Error updating configuration: ' + error.message);
    }
});

// Model List Management
document.addEventListener('DOMContentLoaded', function () {
    function renderModelList(models, loaded, selectedModel) {
        const listDiv = document.getElementById('llm-model-list');
        listDiv.innerHTML = '';
        if (!models.length) {
            listDiv.innerHTML = '<div style="color:#fbbf24;">No models found</div>';
            return;
        }
        models.forEach(m => {
            const isLoaded = loaded.includes(m);
            const wrapper = document.createElement('label');
            wrapper.style.display = 'flex';
            wrapper.style.alignItems = 'center';
            wrapper.style.marginBottom = '0.5em';
            wrapper.style.padding = '0.5em 1em';
            wrapper.style.borderRadius = '0.5em';
            wrapper.style.cursor = 'pointer';
            wrapper.style.background = isLoaded ? '#166534' : '#fbbf24';
            wrapper.style.color = isLoaded ? '#fff' : '#23272F';
            wrapper.style.fontWeight = isLoaded ? 'bold' : 'normal';
            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = 'llm_model';
            radio.value = m;
            radio.style.marginRight = '0.75em';
            if (selectedModel === m) radio.checked = true;
            
            // Add change event listener to save configuration when model is selected
            radio.addEventListener('change', function() {
                if (this.checked) {
                    fetch('/api/v1/llm/config', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            model_name: m,
                            provider_type: document.getElementById('llm-provider-select').value,
                            api_base: document.querySelector('input[name="api_base"]').value
                        })
                    })
                    .then(r => r.json())
                    .then(data => {
                        if (data.success) {
                            document.getElementById('current-model').textContent = m;
                        }
                    })
                    .catch(err => console.error('Error saving model selection:', err));
                }
            });
            
            wrapper.appendChild(radio);
            wrapper.appendChild(document.createTextNode(m + (isLoaded ? ' (loaded)' : '')));
            // Preload button
            const preloadBtn = document.createElement('button');
            preloadBtn.type = 'button';
            preloadBtn.textContent = isLoaded ? 'Loaded' : 'Preload';
            preloadBtn.disabled = isLoaded;
            preloadBtn.style.marginLeft = 'auto';
            preloadBtn.style.background = isLoaded ? '#22c55e' : '#6366F1';
            preloadBtn.style.color = '#fff';
            preloadBtn.style.border = 'none';
            preloadBtn.style.borderRadius = '0.375em';
            preloadBtn.style.padding = '0.25em 0.75em';
            preloadBtn.style.fontWeight = 'bold';
            preloadBtn.style.cursor = isLoaded ? 'default' : 'pointer';
            preloadBtn.addEventListener('click', function () {
                preloadBtn.textContent = 'Loading...';
                preloadBtn.disabled = true;
                fetch('/api/v1/llm/preload', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model: m })
                })
                    .then(r => r.json())
                    .then(() => {
                        setTimeout(() => loadOllamaModels(selectedModel), 1000);
                    });
            });
            wrapper.appendChild(preloadBtn);
            listDiv.appendChild(wrapper);
        });
    }

    function loadOllamaModels(selectedModel) {
        const note = document.getElementById('llm-model-note');
        fetch('/api/v1/llm/models/ollama')
            .then(r => r.json())
            .then(data => {
                renderModelList(data.models || [], data.loaded || [], selectedModel);
                note.textContent = 'Green = loaded in memory. Amber = downloaded and ready to use.';
            })
            .catch(() => {
                renderModelList([], [], null);
                note.textContent = '';
            });
    }

    function loadProviderModels() {
        const provider = document.getElementById('llm-provider-select').value;
        if (provider === 'ollama') {
            loadOllamaModels();
        } else {
            // Placeholder for OpenAI or other providers
            const listDiv = document.getElementById('llm-model-list');
            listDiv.innerHTML = '';
            ['gpt-3.5-turbo', 'gpt-4'].forEach(m => {
                const wrapper = document.createElement('label');
                wrapper.style.display = 'block';
                wrapper.style.marginBottom = '0.5em';
                wrapper.style.padding = '0.5em 1em';
                wrapper.style.borderRadius = '0.5em';
                wrapper.style.cursor = 'pointer';
                wrapper.style.background = '#fbbf24';
                wrapper.style.color = '#23272F';
                const radio = document.createElement('input');
                radio.type = 'radio';
                radio.name = 'llm_model';
                radio.value = m;
                radio.style.marginRight = '0.75em';
                wrapper.appendChild(radio);
                wrapper.appendChild(document.createTextNode(m));
                listDiv.appendChild(wrapper);
            });
            document.getElementById('llm-model-note').textContent = 'OpenAI models are selected from the API.';
        }
    }

    document.getElementById('llm-provider-select').addEventListener('change', loadProviderModels);
    loadProviderModels();

    // When a model is selected, update the test field below
    document.getElementById('llm-model-list').addEventListener('change', function (e) {
        if (e.target && e.target.name === 'llm_model') {
            document.getElementById('current-model').textContent = e.target.value;
        }
    });
});

// Prompt Templates
document.addEventListener('DOMContentLoaded', function () {
    const promptsAccordion = document.getElementById('prompts-accordion');
    const addNewPromptBtn = document.getElementById('add-new-prompt-btn');
    const newPromptForm = document.getElementById('new-prompt-form');
    const saveNewPromptBtn = document.getElementById('save-new-prompt-btn');
    const cancelNewPromptBtn = document.getElementById('cancel-new-prompt-btn');

    function loadPrompts() {
        fetch('/api/v1/llm/prompts')
            .then(r => r.json())
            .then(templates => {
                promptsAccordion.innerHTML = '';
                templates.forEach(t => {
                    const template = document.createElement('div');
                    template.className = 'template-card mb-4';
                    template.innerHTML = `
                        <div class="template-header flex justify-between items-center p-4 bg-gray-800">
                            <h3 class="template-title text-lg font-semibold">${t.name}</h3>
                            <div class="flex gap-2">
                                <button class="edit-btn px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">Edit</button>
                                <button class="delete-btn px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700">Delete</button>
                            </div>
                        </div>
                        <div class="template-content p-4 bg-gray-900">
                            <div class="mb-4">
                                <div class="font-medium mb-1">Description:</div>
                                <p class="text-gray-300">${t.description || 'No description provided'}</p>
                            </div>
                            <div>
                                <div class="font-medium mb-1">Prompt Template:</div>
                                <pre class="bg-gray-800 p-3 rounded overflow-x-auto whitespace-pre-wrap">${t.prompt_text}</pre>
                            </div>
                        </div>
                        <div class="edit-form p-4 bg-gray-900" style="display: none;">
                            <form class="space-y-4">
                                <div class="form-group">
                                    <label class="block text-sm font-medium mb-1">Name</label>
                                    <input type="text" class="edit-name w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded" value="${t.name}">
                                </div>
                                <div class="form-group">
                                    <label class="block text-sm font-medium mb-1">Description</label>
                                    <input type="text" class="edit-description w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded" value="${t.description || ''}">
                                </div>
                                <div class="form-group">
                                    <label class="block text-sm font-medium mb-1">Prompt Template</label>
                                    <textarea class="edit-content w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded" rows="6">${t.prompt_text}</textarea>
                                </div>
                                <div class="flex gap-2 mt-4">
                                    <button type="button" class="save-edit-btn px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">Save Changes</button>
                                    <button type="button" class="cancel-edit-btn px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700">Cancel</button>
                                </div>
                            </form>
                        </div>
                    `;
                    promptsAccordion.appendChild(template);

                    const content = template.querySelector('.template-content');
                    const editForm = template.querySelector('.edit-form');
                    const editBtn = template.querySelector('.edit-btn');
                    const deleteBtn = template.querySelector('.delete-btn');
                    const saveEditBtn = template.querySelector('.save-edit-btn');
                    const cancelEditBtn = template.querySelector('.cancel-edit-btn');

                    editBtn.addEventListener('click', () => {
                        content.style.display = 'none';
                        editForm.style.display = 'block';
                    });

                    cancelEditBtn.addEventListener('click', () => {
                        content.style.display = 'block';
                        editForm.style.display = 'none';
                    });

                    deleteBtn.addEventListener('click', () => {
                        if (confirm('Are you sure you want to delete this prompt template?')) {
                            fetch(`/api/v1/llm/prompts/${t.id}`, {
                                method: 'DELETE',
                            })
                                .then(r => r.json())
                                .then(data => {
                                    if (data.success) {
                                        loadPrompts();
                                    } else {
                                        alert('Failed to delete prompt: ' + (data.error || 'Unknown error'));
                                    }
                                })
                                .catch(err => {
                                    alert('Error deleting prompt: ' + err);
                                });
                        }
                    });

                    saveEditBtn.addEventListener('click', () => {
                        const updatedPrompt = {
                            name: template.querySelector('.edit-name').value.trim(),
                            description: template.querySelector('.edit-description').value.trim(),
                            prompt_text: template.querySelector('.edit-content').value.trim()
                        };

                        if (!updatedPrompt.name || !updatedPrompt.prompt_text) {
                            alert('Name and prompt template are required');
                            return;
                        }

                        fetch(`/api/v1/llm/prompts/${t.id}`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(updatedPrompt)
                        })
                            .then(r => r.json())
                            .then(data => {
                                if (data.success) {
                                    content.style.display = 'block';
                                    editForm.style.display = 'none';
                                    loadPrompts();
                                } else {
                                    alert('Failed to update prompt: ' + (data.error || 'Unknown error'));
                                }
                            })
                            .catch(err => {
                                alert('Error updating prompt: ' + err);
                            });
                    });
                });
            });
    }

    // Load prompts on page load
    loadPrompts();

    // Add New Prompt handlers
    addNewPromptBtn.addEventListener('click', () => {
        newPromptForm.style.display = 'block';
        addNewPromptBtn.style.display = 'none';
    });

    cancelNewPromptBtn.addEventListener('click', () => {
        newPromptForm.style.display = 'none';
        addNewPromptBtn.style.display = 'block';
        // Clear form
        document.getElementById('new-prompt-name').value = '';
        document.getElementById('new-prompt-description').value = '';
        document.getElementById('new-prompt-content').value = '';
    });

    saveNewPromptBtn.addEventListener('click', () => {
        const name = document.getElementById('new-prompt-name').value.trim();
        const description = document.getElementById('new-prompt-description').value.trim();
        const content = document.getElementById('new-prompt-content').value.trim();

        if (!name || !content) {
            alert('Name and content are required');
            return;
        }

        fetch('/api/v1/llm/prompts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                description,
                prompt_text: content
            })
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    loadPrompts();
                    newPromptForm.style.display = 'none';
                    addNewPromptBtn.style.display = 'block';
                    // Clear form
                    document.getElementById('new-prompt-name').value = '';
                    document.getElementById('new-prompt-description').value = '';
                    document.getElementById('new-prompt-content').value = '';
                } else {
                    alert('Failed to save prompt: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(err => {
                alert('Error saving prompt: ' + err);
            });
    });
});

// Prompt Parts
document.addEventListener('DOMContentLoaded', function () {
    // Only run on Action Details page
    const promptPartsList = document.getElementById('prompt-parts-list');
    if (!promptPartsList) return;

    const actionId = document.body.dataset.actionId || document.getElementById('llm-action-form').dataset.actionId;

    // Helper to fetch and render prompt parts
    async function loadPromptParts() {
        const resp = await fetch(`/api/v1/llm/actions/${actionId}`);
        const data = await resp.json();
        promptPartsList.innerHTML = '';
        (data.prompt_parts || []).forEach(part => {
            const div = document.createElement('div');
            div.className = 'flex items-center gap-2 bg-dark-bg border border-dark-border rounded p-3';
            div.innerHTML = `
                <span class="font-mono text-xs px-2 py-1 rounded bg-gray-800 text-gray-300">${part.type}</span>
                <span class="flex-1 text-sm text-gray-200">${part.content.slice(0,80)}</span>
                <button type="button" class="btn btn-xs btn-danger" data-remove-part="${part.id}"><i class="fa fa-trash"></i></button>
                <button type="button" class="btn btn-xs btn-secondary" data-move-up="${part.id}"><i class="fa fa-arrow-up"></i></button>
                <button type="button" class="btn btn-xs btn-secondary" data-move-down="${part.id}"><i class="fa fa-arrow-down"></i></button>
                <button type="button" class="btn btn-xs btn-secondary" data-edit-part="${part.id}"><i class="fa fa-edit"></i></button>
            `;
            promptPartsList.appendChild(div);
        });
    }

    // Add Prompt Part
    document.getElementById('add-prompt-part-btn').addEventListener('click', function() {
        // Simple prompt for now; replace with modal for full UX
        const type = prompt('Prompt part type (system, user, assistant, etc):');
        if (!type) return;
        const content = prompt('Prompt part content:');
        if (!content) return;
        fetch(`/api/v1/llm/prompt_parts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type, content })
        })
        .then(r => r.json())
        .then(data => {
            if (data.id) {
                // Link to action
                fetch(`/api/v1/llm/actions/${actionId}/prompt_parts`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt_part_id: data.id })
                }).then(() => loadPromptParts());
            } else {
                alert('Failed to create prompt part');
            }
        });
    });

    // Delegate remove/move/edit events
    promptPartsList.addEventListener('click', function(e) {
        const removeBtn = e.target.closest('[data-remove-part]');
        const moveUpBtn = e.target.closest('[data-move-up]');
        const moveDownBtn = e.target.closest('[data-move-down]');
        const editBtn = e.target.closest('[data-edit-part]');
        if (removeBtn) {
            const partId = removeBtn.dataset.removePart;
            fetch(`/api/v1/llm/actions/${actionId}/prompt_parts/${partId}`, { method: 'DELETE' })
                .then(() => loadPromptParts());
        } else if (moveUpBtn) {
            const partId = moveUpBtn.dataset.moveUp;
            fetch(`/api/v1/llm/actions/${actionId}/prompt_parts/${partId}/move`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ direction: 'up' })
            }).then(() => loadPromptParts());
        } else if (moveDownBtn) {
            const partId = moveDownBtn.dataset.moveDown;
            fetch(`/api/v1/llm/actions/${actionId}/prompt_parts/${partId}/move`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ direction: 'down' })
            }).then(() => loadPromptParts());
        } else if (editBtn) {
            const partId = editBtn.dataset.editPart;
            const newContent = prompt('Edit prompt part content:');
            if (newContent) {
                fetch(`/api/v1/llm/prompt_parts/${partId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: newContent })
                }).then(() => loadPromptParts());
            }
        }
    });

    // --- LLM Message Preview ---
    async function updateMessagePreview() {
        // Fetch current prompt parts for the action
        const resp = await fetch(`/api/v1/llm/actions/${actionId}`);
        const data = await resp.json();
        // Compose preview string (simple join for now)
        const preview = (data.prompt_parts || []).map(p => `[${p.type}]\n${p.content}`).join('\n---\n');
        document.getElementById('llm-message-preview').textContent = preview || '{ ... message preview ... }';
    }

    // Patch loadPromptParts to also update preview
    const origLoadPromptParts = loadPromptParts;
    loadPromptParts = async function() {
        await origLoadPromptParts();
        await updateMessagePreview();
    };

    // Initial preview
    updateMessagePreview();

    // --- Test Action Button ---
    const runBtn = document.getElementById('run-llm-action-btn');
    if (runBtn) {
        runBtn.addEventListener('click', async function() {
            const testInput = document.querySelector('textarea[name="test_input"]').value;
            runBtn.disabled = true;
            runBtn.textContent = 'Running...';
            try {
                const resp = await fetch(`/api/v1/llm/actions/${actionId}/test`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ input: testInput })
                });
                const data = await resp.json();
                document.getElementById('llm-output').textContent = data.output || '[No output]';
                document.querySelector('#diagnostics-panel pre').textContent = JSON.stringify(data.diagnostics || data, null, 2);
            } catch (err) {
                document.getElementById('llm-output').textContent = '[Error running action]';
                document.querySelector('#diagnostics-panel pre').textContent = err.message;
            } finally {
                runBtn.disabled = false;
                runBtn.textContent = 'Run Action';
            }
        });
    }
});

// New file: workflow_modular_llm.js
// Modular LLM Workflow logic for Input, Actions, Output, and Post Development Fields panels
// This script is designed to be reusable for all workflow stages

(async function() {
  // Utility: fetch field mappings from /api/settings/field-mapping
  async function fetchFieldMappings() {
    const resp = await fetch('/api/settings/field-mapping');
    return resp.ok ? await resp.json() : [];
  }

  // Utility: group fields by stage/substage
  function groupFieldsByStage(mappings) {
    const grouped = {};
    for (const m of mappings) {
      if (!grouped[m.stage_name]) grouped[m.stage_name] = {};
      if (!grouped[m.stage_name][m.substage_name]) grouped[m.stage_name][m.substage_name] = [];
      grouped[m.stage_name][m.substage_name].push(m.field_name);
    }
    return grouped;
  }

  // Utility: fetch post_development for a post
  async function fetchPostDevelopment(postId) {
    const resp = await fetch(`/blog/api/v1/post/${postId}/development`);
    return resp.ok ? await resp.json() : {};
  }

  // Utility: update a post_development field
  async function updatePostDevelopmentField(postId, field, value) {
    // Use the main update endpoint for post_development
    const resp = await fetch(`/blog/api/v1/post/${postId}/development`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ [field]: value })
    });
    return resp.ok ? await resp.json() : { status: 'error' };
  }

  // Utility: fetch LLM actions
  async function fetchLLMActions() {
    const resp = await fetch('/api/v1/llm/actions');
    return resp.ok ? await resp.json() : [];
  }

  // Utility: fetch LLM action details
  async function fetchLLMActionDetails(actionId) {
    const resp = await fetch(`/api/v1/llm/actions/${actionId}`);
    return resp.ok ? await resp.json() : {};
  }

  // Utility: run LLM action
  async function runLLMAction(actionId, input) {
    const resp = await fetch(`/api/v1/llm/actions/${actionId}/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input })
    });
    return resp.ok ? await resp.json() : { error: 'Failed to run action' };
  }

  // Get postId from URL
  const urlParams = new URLSearchParams(window.location.search);
  const postId = urlParams.get('post_id');
  if (!postId) return;

  // DOM elements
  const inputFieldSelect = document.getElementById('inputFieldSelect');
  const inputFieldValue = document.getElementById('inputFieldValue');
  const actionSelect = document.getElementById('actionSelect');
  const actionPromptPanel = document.getElementById('actionPromptPanel');
  const runActionBtn = document.getElementById('runActionBtn');
  const outputFieldSelect = document.getElementById('outputFieldSelect');
  const outputFieldValue = document.getElementById('outputFieldValue');
  const actionOutputPanel = document.getElementById('actionOutputPanel');
  const saveOutputBtn = document.getElementById('saveOutputBtn');
  const postDevFieldsPanel = document.getElementById('postDevFieldsPanel');

  // State
  let fieldMappings = [];
  let groupedFields = {};
  let postDev = {};
  let llmActions = [];
  let actionDetails = {};
  let lastActionOutput = '';

  // Fetch all data
  async function init() {
    fieldMappings = await fetchFieldMappings();
    groupedFields = groupFieldsByStage(fieldMappings);
    postDev = await fetchPostDevelopment(postId);
    llmActions = await fetchLLMActions();
    renderFieldDropdown(inputFieldSelect, groupedFields);
    renderFieldDropdown(outputFieldSelect, groupedFields);
    renderActionDropdown(actionSelect, llmActions);
    renderPostDevFields(postDevFieldsPanel, fieldMappings, postDev);
  }

  // Render dropdown for fields
  function renderFieldDropdown(select, grouped) {
    select.innerHTML = '';
    for (const stage in grouped) {
      const stageOptGroup = document.createElement('optgroup');
      stageOptGroup.label = stage;
      for (const substage in grouped[stage]) {
        const substageOptGroup = document.createElement('optgroup');
        substageOptGroup.label = `  ${substage}`;
        for (const field of grouped[stage][substage]) {
          const opt = document.createElement('option');
          opt.value = field;
          opt.textContent = field.replace(/_/g, ' ');
          substageOptGroup.appendChild(opt);
        }
        stageOptGroup.appendChild(substageOptGroup);
      }
      select.appendChild(stageOptGroup);
    }
  }

  // Render action dropdown
  function renderActionDropdown(select, actions) {
    select.innerHTML = '<option value="">Select Action...</option>';
    for (const action of actions) {
      const opt = document.createElement('option');
      opt.value = action.id;
      opt.textContent = action.field_name;
      select.appendChild(opt);
    }
  }

  // Render post development fields table
  function renderPostDevFields(panel, mappings, postDev) {
    // Only show fields mapped to this substage (e.g., idea)
    const substageId = 1; // For Idea stage; make dynamic for other stages
    const fields = mappings.filter(m => m.substage_id == substageId).map(m => m.field_name);
    let html = '<table class="min-w-full bg-dark-card border border-gray-700 rounded-lg text-sm"><thead><tr>';
    for (const field of fields) {
      html += `<th class="px-3 py-2">${field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</th>`;
    }
    html += '</tr></thead><tbody><tr>';
    for (const field of fields) {
      html += `<td class="px-3 py-2">${postDev[field] || ''}</td>`;
    }
    html += '</tr></tbody></table>';
    panel.innerHTML = html;
  }

  // Field dropdown change handlers
  inputFieldSelect.addEventListener('change', () => {
    const field = inputFieldSelect.value;
    inputFieldValue.textContent = postDev[field] || '(No value)';
  });
  outputFieldSelect.addEventListener('change', () => {
    const field = outputFieldSelect.value;
    outputFieldValue.textContent = postDev[field] || '(No value)';
  });

  // Action dropdown change handler
  actionSelect.addEventListener('change', async () => {
    const actionId = actionSelect.value;
    if (!actionId) {
      actionPromptPanel.textContent = 'Select an action to view its prompt/template.';
      return;
    }
    actionDetails = await fetchLLMActionDetails(actionId);
    actionPromptPanel.textContent = actionDetails.prompt_template || '(No prompt template)';
  });

  // Run Action button handler
  runActionBtn.addEventListener('click', async () => {
    const actionId = actionSelect.value;
    const inputField = inputFieldSelect.value;
    if (!actionId || !inputField) {
      actionOutputPanel.textContent = 'Please select both an action and an input field.';
      return;
    }
    const inputValue = postDev[inputField] || '';
    actionOutputPanel.textContent = 'Running action...';
    const result = await runLLMAction(actionId, inputValue);
    if (result && result.result && result.result.output) {
      lastActionOutput = result.result.output;
      actionOutputPanel.textContent = lastActionOutput;
    } else if (result.response) {
      lastActionOutput = result.response;
      actionOutputPanel.textContent = lastActionOutput;
    } else {
      actionOutputPanel.textContent = result.error || 'No output.';
    }
  });

  // Save Output button handler
  saveOutputBtn.addEventListener('click', async () => {
    const outputField = outputFieldSelect.value;
    if (!outputField) {
      actionOutputPanel.textContent = 'Please select an output field.';
      return;
    }
    if (!lastActionOutput) {
      actionOutputPanel.textContent = 'No output to save.';
      return;
    }
    const resp = await updatePostDevelopmentField(postId, outputField, lastActionOutput);
    if (resp.status === 'success') {
      actionOutputPanel.textContent = 'Output saved!';
      // Refresh postDev and output panel
      postDev = await fetchPostDevelopment(postId);
      outputFieldValue.textContent = postDev[outputField] || '(No value)';
      renderPostDevFields(postDevFieldsPanel, fieldMappings, postDev);
    } else {
      actionOutputPanel.textContent = 'Failed to save output.';
    }
  });

  // Initial load
  await init();
})(); 