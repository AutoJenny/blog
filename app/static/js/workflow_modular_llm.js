// Modular LLM Workflow logic for Input, Actions, Output, and Post Development Fields panels
// This script is designed to be reusable for all workflow stages

(async function() {
  // Utility: fetch field mappings from /api/settings/field-mapping
  async function fetchFieldMappings() {
    const resp = await fetch('/api/settings/field-mapping');
    return resp.ok ? await resp.json() : [];
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

  // Utility: fetch post_substage_action for this post/substage
  async function fetchPostSubstageAction(postId, substage) {
    const resp = await fetch(`/api/v1/llm/post_substage_actions?post_id=${postId}&substage=${substage}`);
    return resp.ok ? await resp.json() : null;
  }

  // Utility: save post_substage_action (for action, input, output selections)
  async function savePostSubstageAction(postId, substage, actionId, inputField, outputField) {
    const payload = { post_id: postId, substage, action_id: actionId, input_field: inputField, output_field: outputField };
    const resp = await fetch('/api/v1/llm/post_substage_actions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return resp.ok ? await resp.json() : null;
  }

  // Get postId and substage from URL/context
  const urlParams = new URLSearchParams(window.location.search);
  const postId = urlParams.get('post_id');
  const substage = 'idea'; // TODO: make dynamic for other stages
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
  let postDev = {};
  let llmActions = [];
  let actionDetails = {};
  let lastActionOutput = '';
  let postSubstageAction = null;

  // Fetch all data and initialize UI
  async function init() {
    fieldMappings = await fetchFieldMappings();
    postDev = await fetchPostDevelopment(postId);
    llmActions = await fetchLLMActions();
    postSubstageAction = await fetchPostSubstageAction(postId, substage);
    renderFieldDropdown(inputFieldSelect, fieldMappings, postSubstageAction ? postSubstageAction.input_field : null);
    renderFieldDropdown(outputFieldSelect, fieldMappings, postSubstageAction ? postSubstageAction.output_field : null);
    renderActionDropdown(actionSelect, llmActions, postSubstageAction ? postSubstageAction.action_id : null);
    renderPostDevFields(postDevFieldsPanel, fieldMappings, postDev);
    // Show initial field values
    if (inputFieldSelect.value) inputFieldValue.textContent = postDev[inputFieldSelect.value] || '(No value)';
    if (outputFieldSelect.value) outputFieldValue.textContent = postDev[outputFieldSelect.value] || '(No value)';
    // Always trigger change event to sync details panel
    actionSelect.dispatchEvent(new Event('change'));
  }

  // Render dropdown for fields (grouped by stage and substage, matching /settings)
  function renderFieldDropdown(select, mappings, selected) {
    select.innerHTML = '';
    let lastStage = null;
    let lastSubstage = null;
    let stageOptGroup = null;
    for (const m of mappings) {
      // New stage: create a new optgroup
      if (m.stage_name !== lastStage) {
        stageOptGroup = document.createElement('optgroup');
        stageOptGroup.label = m.stage_name;
        select.appendChild(stageOptGroup);
        lastStage = m.stage_name;
        lastSubstage = null; // Reset substage for new stage
      }
      // New substage: add a disabled label option
      if (m.substage_name !== lastSubstage) {
        const substageLabel = document.createElement('option');
        substageLabel.disabled = true;
        substageLabel.textContent = `  ${m.substage_name}`;
        substageLabel.style.fontStyle = 'italic';
        stageOptGroup.appendChild(substageLabel);
        lastSubstage = m.substage_name;
      }
      // Add the field option
      const opt = document.createElement('option');
      opt.value = m.field_name;
      opt.textContent = `    ${m.field_name.replace(/_/g, ' ')}`;
      if (selected && selected === m.field_name) opt.selected = true;
      stageOptGroup.appendChild(opt);
    }
    // Dark theme classes
    select.classList.add('bg-gray-900', 'text-gray-100', 'border', 'border-gray-700');
  }

  // Render action dropdown
  function renderActionDropdown(select, actions, selected) {
    select.innerHTML = '<option value="">Select Action...</option>';
    for (const action of actions) {
      const opt = document.createElement('option');
      opt.value = action.id;
      opt.textContent = action.field_name;
      if (selected && String(selected) === String(action.id)) opt.selected = true;
      select.appendChild(opt);
    }
    // Dark theme classes
    select.classList.add('bg-gray-900', 'text-gray-100', 'border', 'border-gray-700');
    // Explicitly set value to ensure sync
    if (selected) select.value = String(selected);
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

  // Show action details (prompt/template, model, etc)
  async function showActionDetails(actionId) {
    if (!actionId) {
      actionPromptPanel.innerHTML = '(No action selected)';
      return;
    }
    const details = await fetchLLMActionDetails(actionId);
    // Robust: support both {action: {...}} and flat
    const action = details.action || details;
    let html = '';
    if (action.prompt_template) {
      html += `<div><b>Prompt Template:</b><pre class='bg-gray-800 text-gray-100 rounded p-2 mt-1 mb-2'>${action.prompt_template}</pre></div>`;
    }
    if (action.llm_model) {
      html += `<div><b>LLM Model:</b> <span class='text-green-300'>${action.llm_model}</span></div>`;
    }
    if (!html) html = '(No details)';
    actionPromptPanel.innerHTML = html;
  }

  // Field dropdown change handlers (persist selection)
  inputFieldSelect.addEventListener('change', async () => {
    const field = inputFieldSelect.value;
    inputFieldValue.textContent = postDev[field] || '(No value)';
    if (!actionSelect.value) return; // Only POST if action is selected
    await savePostSubstageAction(postId, substage, actionSelect.value, field, outputFieldSelect.value);
  });
  outputFieldSelect.addEventListener('change', async () => {
    const field = outputFieldSelect.value;
    outputFieldValue.textContent = postDev[field] || '(No value)';
    if (!actionSelect.value) return; // Only POST if action is selected
    await savePostSubstageAction(postId, substage, actionSelect.value, inputFieldSelect.value, field);
  });

  // Action dropdown change handler (persist selection)
  actionSelect.addEventListener('change', async () => {
    const actionId = actionSelect.value;
    await showActionDetails(actionId);
    if (!actionId) return; // Only POST if action is selected
    await savePostSubstageAction(postId, substage, actionId, inputFieldSelect.value, outputFieldSelect.value);
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