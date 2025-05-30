// Modular LLM Workflow logic for Input, Actions, Output, and Post Development Fields panels
// This script is designed to be reusable for all workflow stages
// The substage is now dynamically determined from a data-substage attribute on the main workflow container.

import { showStartOllamaButton } from './llm_utils.js';

// Robust Ollama status check
async function checkOllamaStatus() {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 1000); // 1s timeout
    const resp = await fetch('/api/v1/llm/providers/1/test', { method: 'POST', signal: controller.signal });
    clearTimeout(timeout);
    if (!resp.ok) return false;
    const data = await resp.json();
    return data.success === true;
  } catch (e) {
    return false;
  }
}

(async function() {
  // Utility: fetch field mappings from /api/settings/field-mapping
  async function fetchFieldMappings() {
    const resp = await fetch('/api/settings/field-mapping');
    return resp.ok ? await resp.json() : [];
  }

  // Utility: fetch post_development for a post
  async function fetchPostDevelopment(postId) {
    const resp = await fetch(`/api/v1/post/${postId}/development`);
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
    const resp = await fetch(`/api/v1/llm/actions/${actionId}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input_text: input, post_id: postId })
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
  // Dynamically determine substage from data attribute or fallback to 'idea'
  let substage = 'idea';
  const workflowRoot = document.getElementById('llm-workflow-root');
  if (workflowRoot && workflowRoot.dataset.substage) {
    substage = workflowRoot.dataset.substage;
  } else {
    // Try to infer from URL path (e.g., /workflow/planning/research/)
    const pathMatch = window.location.pathname.match(/\/workflow\/\w+\/(\w+)/);
    if (pathMatch && pathMatch[1]) substage = pathMatch[1];
  }
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
  let lastRequestToken = 0;
  let isInitializing = true;

  // Fetch all data and initialize UI
  async function init() {
    isInitializing = true;
    fieldMappings = await fetchFieldMappings();
    postDev = await fetchPostDevelopment(postId);
    llmActions = await fetchLLMActions();
    postSubstageAction = await fetchPostSubstageAction(postId, substage);
    // Robust: handle array or null
    const psa = Array.isArray(postSubstageAction) && postSubstageAction.length > 0 ? postSubstageAction[0] : null;
    renderFieldDropdown(inputFieldSelect, fieldMappings, psa ? psa.input_field : null);
    renderFieldDropdown(outputFieldSelect, fieldMappings, psa ? psa.output_field : null);
    renderActionDropdown(actionSelect, llmActions, psa ? psa.action_id : null);
    renderPostDevFields(postDevFieldsPanel, fieldMappings, postDev, substage);
    // Show initial field values
    if (inputFieldSelect.value) inputFieldValue.textContent = postDev[inputFieldSelect.value] || '(No value)';
    if (outputFieldSelect.value) outputFieldValue.textContent = postDev[outputFieldSelect.value] || '(No value)';
    // Debug: confirm value after rendering
    console.log('[Dropdown] After render, outputFieldSelect.value =', outputFieldSelect.value);
    isInitializing = false;
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
        substageLabel.textContent = m.substage_name;
        substageLabel.disabled = true;
        stageOptGroup.appendChild(substageLabel);
        lastSubstage = m.substage_name;
      }
      // Add the field option
      const opt = document.createElement('option');
      opt.value = m.field_name; // always DB field name
      opt.textContent = m.display_name || m.field_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
      stageOptGroup.appendChild(opt);
    }
    // Add dark theme classes
    select.classList.add('bg-gray-900', 'text-gray-100', 'border', 'border-gray-700');
    // Debug: print all option values
    const validOptions = Array.from(select.options).filter(o => !o.disabled).map(o => o.value);
    console.log('[Dropdown] Options:', validOptions);
    console.log('[Dropdown] Attempting to set value to:', selected);
    // Set value if present and not disabled, else default to first available
    if (selected && validOptions.includes(selected)) {
      select.value = selected;
      console.log('[Dropdown] Set value to:', selected);
    } else {
      // Find first non-disabled option
      const firstValid = Array.from(select.options).find(o => !o.disabled);
      if (firstValid) {
        select.value = firstValid.value;
        if (selected) {
          console.warn('[Dropdown] Value not found or is disabled:', selected, 'Defaulting to:', firstValid.value);
        }
      }
    }
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
  /**
   * Render post development fields for the current substage.
   * @param {HTMLElement} panel
   * @param {Array} mappings
   * @param {Object} postDev
   * @param {string} substage - current substage name
   */
  function renderPostDevFields(panel, mappings, postDev, substage) {
    // Find substage_id for the current substage name
    const substageEntry = mappings.find(m => m.substage_name === substage);
    const substageId = substageEntry ? substageEntry.substage_id : null;
    const fields = substageId ? mappings.filter(m => m.substage_id == substageId).map(m => m.field_name) : [];
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

  // Utility to show/hide input/output panels based on action selection
  function updatePanelVisibility() {
    const inputPanel = document.getElementById('inputPanel');
    const outputPanel = document.getElementById('outputPanel');
    if (actionSelect.value) {
      inputPanel.classList.remove('hidden');
      outputPanel.classList.remove('hidden');
    } else {
      inputPanel.classList.add('hidden');
      outputPanel.classList.add('hidden');
    }
  }

  // Field dropdown change handlers (persist selection)
  inputFieldSelect.addEventListener('change', async () => {
    if (isInitializing) return;
    const field = inputFieldSelect.value;
    inputFieldValue.textContent = postDev[field] || '(No value)';
    // Always POST current state
    await savePostSubstageAction(postId, substage, actionSelect.value, field, outputFieldSelect.value);
    // Re-fetch and update UI
    postSubstageAction = await fetchPostSubstageAction(postId, substage);
    const psa = Array.isArray(postSubstageAction) && postSubstageAction.length > 0 ? postSubstageAction[0] : null;
    if (psa && psa.input_field) inputFieldSelect.value = psa.input_field;
    if (psa && psa.output_field) outputFieldSelect.value = psa.output_field;
    if (psa && psa.output_field) outputFieldValue.textContent = postDev[psa.output_field] || '(No value)';
  });
  outputFieldSelect.addEventListener('change', async () => {
    if (isInitializing) return;
    const field = outputFieldSelect.value;
    outputFieldValue.textContent = postDev[field] || '(No value)';
    // Always POST current state
    await savePostSubstageAction(postId, substage, actionSelect.value, inputFieldSelect.value, field);
    // Re-fetch and update UI
    postSubstageAction = await fetchPostSubstageAction(postId, substage);
    const psa = Array.isArray(postSubstageAction) && postSubstageAction.length > 0 ? postSubstageAction[0] : null;
    if (psa && psa.input_field) inputFieldSelect.value = psa.input_field;
    if (psa && psa.output_field) outputFieldSelect.value = psa.output_field;
    if (psa && psa.output_field) outputFieldValue.textContent = postDev[psa.output_field] || '(No value)';
  });

  // Action dropdown change handler (persist selection)
  actionSelect.addEventListener('change', async () => {
    updatePanelVisibility();
    const actionId = actionSelect.value;
    await showActionDetails(actionId);
    // Always POST current state
    if (actionId) {
      await savePostSubstageAction(postId, substage, actionId, inputFieldSelect.value, outputFieldSelect.value);
      // Re-fetch and update UI
      postSubstageAction = await fetchPostSubstageAction(postId, substage);
      const psa = Array.isArray(postSubstageAction) && postSubstageAction.length > 0 ? postSubstageAction[0] : null;
      if (psa && psa.input_field) inputFieldSelect.value = psa.input_field;
      if (psa && psa.output_field) outputFieldSelect.value = psa.output_field;
      if (psa && psa.output_field) outputFieldValue.textContent = postDev[psa.output_field] || '(No value)';
    }
  });

  // Run Action button handler
  runActionBtn.addEventListener('click', async () => {
    try {
      if (!actionOutputPanel) {
        alert('Error: Output panel not found in DOM.');
        return;
      }
      // Generate a unique token for this request
      const requestToken = ++lastRequestToken;
      // Clear output and disable button
      actionOutputPanel.textContent = 'Running action...';
      runActionBtn.disabled = true;
      // Check Ollama status first
      console.log('[LLM] Checking Ollama status...');
      const ollamaOk = await checkOllamaStatus();
      if (!ollamaOk) {
        actionOutputPanel.textContent = 'Ollama is not running.';
        showStartOllamaButton(actionOutputPanel);
        runActionBtn.disabled = false;
        return;
      }
      const actionId = actionSelect.value;
      const inputField = inputFieldSelect.value;
      if (!actionId || !inputField) {
        actionOutputPanel.textContent = 'Please select both an action and an input field.';
        runActionBtn.disabled = false;
        return;
      }
      const inputValue = postDev[inputField] || '';
      let resp;
      try {
        resp = await fetch(`/api/v1/llm/actions/${actionId}/execute`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            post_id: postId,
            input_field: inputField,
            input_text: inputValue,
            debug: true
          })
        });
      } catch (err) {
        actionOutputPanel.textContent = 'Network error: Could not reach LLM backend.';
        showStartOllamaButton(actionOutputPanel);
        runActionBtn.disabled = false;
        lastActionOutput = '';
        return;
      }
      if (resp.status === 503) {
        actionOutputPanel.textContent = 'Ollama is not running (503 Service Unavailable).';
        showStartOllamaButton(actionOutputPanel);
        runActionBtn.disabled = false;
        lastActionOutput = '';
        return;
      }
      if (!resp.ok) {
        actionOutputPanel.textContent = `Error: ${resp.status} ${resp.statusText}`;
        runActionBtn.disabled = false;
        lastActionOutput = '';
        return;
      }
      let result;
      try {
        result = await resp.json();
      } catch (err) {
        actionOutputPanel.textContent = 'Error: Could not parse LLM response.';
        runActionBtn.disabled = false;
        lastActionOutput = '';
        return;
      }
      // Only show result if this is the latest request
      if (requestToken !== lastRequestToken) return;
      if (result && result.result && result.result.output) {
        actionOutputPanel.textContent = result.result.output;
        lastActionOutput = result.result.output;
        // Auto-save output to selected output field
        const outputField = outputFieldSelect.value;
        if (outputField && lastActionOutput) {
          const resp = await updatePostDevelopmentField(postId, outputField, lastActionOutput);
          if (resp.status === 'success') {
            // Refresh postDev and output panel
            postDev = await fetchPostDevelopment(postId);
            outputFieldValue.textContent = postDev[outputField] || '(No value)';
            renderPostDevFields(postDevFieldsPanel, fieldMappings, postDev, substage);
          }
        }
      } else if (result && result.output) {
        actionOutputPanel.textContent = result.output;
        lastActionOutput = result.output;
        // Auto-save output to selected output field
        const outputField = outputFieldSelect.value;
        if (outputField && lastActionOutput) {
          const resp = await updatePostDevelopmentField(postId, outputField, lastActionOutput);
          if (resp.status === 'success') {
            // Refresh postDev and output panel
            postDev = await fetchPostDevelopment(postId);
            outputFieldValue.textContent = postDev[outputField] || '(No value)';
            renderPostDevFields(postDevFieldsPanel, fieldMappings, postDev, substage);
          }
        }
      } else if (result && result.error) {
        actionOutputPanel.textContent = `Error: ${result.error}`;
        lastActionOutput = '';
      } else {
        actionOutputPanel.textContent = 'No output.';
        lastActionOutput = '';
      }
      runActionBtn.disabled = false;
    } catch (err) {
      actionOutputPanel.textContent = 'Unexpected error running LLM action.';
      showStartOllamaButton(actionOutputPanel);
      runActionBtn.disabled = false;
      lastActionOutput = '';
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
      renderPostDevFields(postDevFieldsPanel, fieldMappings, postDev, substage);
    } else {
      actionOutputPanel.textContent = 'Failed to save output.';
    }
  });

  // Initial load
  await init();
  updatePanelVisibility();
})(); 