// Modular LLM Workflow logic for Input, Actions, Output, and Post Development Fields panels
// This script is designed to be reusable for all workflow stages
// The substage is now dynamically determined from a data-substage attribute on the main workflow container.

import { showStartOllamaButton } from './llm_utils.js';
import {
    renderActionDropdown,
    renderFieldDropdown,
    renderPostDevFields,
    showActionDetails,
    updatePanelVisibility
} from './workflow/render.js';

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

  // Utility: fetch the most recent post_substage_action for a given substage (excluding current post)
  async function fetchLastPostSubstageAction(substage, excludePostId) {
    const resp = await fetch(`/api/v1/llm/post_substage_actions/list?page=1&page_size=50`);
    if (!resp.ok) return null;
    const data = await resp.json();
    if (!data.actions) return null;
    // Find the most recent action for this substage, not for the current post
    return data.actions.find(a => a.substage === substage && a.post_id != excludePostId) || null;
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
    let psa = Array.isArray(postSubstageAction) && postSubstageAction.length > 0 ? postSubstageAction[0] : null;
    // If no psa, try to copy from previous post
    if (!psa) {
      const lastPsa = await fetchLastPostSubstageAction(substage, postId);
      if (lastPsa) {
        // POST to create a new psa for this post using lastPsa's settings
        await savePostSubstageAction(postId, substage, lastPsa.action_id, lastPsa.input_field, lastPsa.output_field);
        // Re-fetch
        postSubstageAction = await fetchPostSubstageAction(postId, substage);
        psa = Array.isArray(postSubstageAction) && postSubstageAction.length > 0 ? postSubstageAction[0] : null;
      }
    }
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

  // Field dropdown change handlers (persist selection)
  inputFieldSelect.addEventListener('change', async () => {
    if (isInitializing) return;
    const field = inputFieldSelect.value;
    inputFieldValue.textContent = postDev[field] || '(No value)';
    // Only POST if postId, substage, and actionId are present
    if (!postId || !substage || !actionSelect.value) {
      console.warn('Not saving: missing required keys', { postId, substage, actionId: actionSelect.value });
      return;
    }
    console.log('Saving post_substage_action (input change):', { postId, substage, actionId: actionSelect.value, inputField: inputFieldSelect.value, outputField: outputFieldSelect.value });
    await savePostSubstageAction(postId, substage, actionSelect.value, inputFieldSelect.value, outputFieldSelect.value);
    // Re-fetch and update UI
    postSubstageAction = await fetchPostSubstageAction(postId, substage);
    const psa = Array.isArray(postSubstageAction) && postSubstageAction.length > 0 ? postSubstageAction[0] : null;
    // Always re-render dropdown with the just-selected value, even if not mapped to this substage
    renderFieldDropdown(inputFieldSelect, fieldMappings, inputFieldSelect.value);
    if (psa && psa.output_field) outputFieldSelect.value = psa.output_field;
    if (psa && psa.output_field) outputFieldValue.textContent = postDev[psa.output_field] || '(No value)';
  });
  outputFieldSelect.addEventListener('change', async () => {
    if (isInitializing) return;
    const field = outputFieldSelect.value;
    outputFieldValue.textContent = postDev[field] || '(No value)';
    // Only POST if postId, substage, and actionId are present
    if (!postId || !substage || !actionSelect.value) {
      console.warn('Not saving: missing required keys', { postId, substage, actionId: actionSelect.value });
      return;
    }
    console.log('Saving post_substage_action (output change):', { postId, substage, actionId: actionSelect.value, inputField: inputFieldSelect.value, outputField: outputFieldSelect.value });
    await savePostSubstageAction(postId, substage, actionSelect.value, inputFieldSelect.value, outputFieldSelect.value);
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
    // Only POST if postId, substage, and actionId are present
    if (!actionId || !postId || !substage) {
      console.warn('Not saving: missing required keys', { postId, substage, actionId });
      return;
    }
    console.log('Saving post_substage_action (action change):', { postId, substage, actionId, inputField: inputFieldSelect.value, outputField: outputFieldSelect.value });
    await savePostSubstageAction(postId, substage, actionId, inputFieldSelect.value, outputFieldSelect.value);
    // Re-fetch and update UI
    postSubstageAction = await fetchPostSubstageAction(postId, substage);
    const psa = Array.isArray(postSubstageAction) && postSubstageAction.length > 0 ? postSubstageAction[0] : null;
    if (psa && psa.input_field) inputFieldSelect.value = psa.input_field;
    if (psa && psa.output_field) outputFieldSelect.value = psa.output_field;
    if (psa && psa.output_field) outputFieldValue.textContent = postDev[psa.output_field] || '(No value)';
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
      if (!inputValue) {
        actionOutputPanel.textContent = `No value found for input field: ${inputField}. Please enter a value before running the action.`;
        runActionBtn.disabled = false;
        return;
      }
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