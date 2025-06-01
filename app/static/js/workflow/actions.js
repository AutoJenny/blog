// LLM action execution and result handling for workflow LLM modular UI

import { showStartOllamaButton } from '../llm_utils.js';

/**
 * Execute an LLM action and handle the result.
 * @param {Object} params - All required arguments and dependencies.
 * @param {number} params.actionId
 * @param {string} params.inputValue
 * @param {number} params.postId
 * @param {Function} params.runLLMAction
 * @param {Function} params.updatePostDevelopmentField
 * @param {Function} params.fetchPostDevelopment
 * @param {Function} params.renderPostDevFields
 * @param {Object} params.state
 * @param {HTMLElement} params.actionOutputPanel
 * @param {HTMLElement} params.outputFieldSelect
 * @param {HTMLElement} params.outputFieldValue
 * @param {HTMLElement} params.postDevFieldsPanel
 */
export async function executeLLMAction({
  actionId,
  inputValue,
  postId,
  runLLMAction,
  updatePostDevelopmentField,
  fetchPostDevelopment,
  renderPostDevFields,
  state,
  actionOutputPanel,
  outputFieldSelect,
  outputFieldValue,
  postDevFieldsPanel
}) {
  try {
    if (!actionOutputPanel) {
      alert('Error: Output panel not found in DOM.');
      return;
    }
    const requestToken = ++state.lastRequestToken;
    actionOutputPanel.textContent = 'Running action...';
    state.runActionBtn.disabled = true;
    const ollamaOk = await state.checkOllamaStatus();
    if (!ollamaOk) {
      actionOutputPanel.textContent = 'Ollama is not running.';
      showStartOllamaButton(actionOutputPanel);
      state.runActionBtn.disabled = false;
      return;
    }
    if (!actionId || !inputValue) {
      actionOutputPanel.textContent = 'Please select both an action and an input field.';
      state.runActionBtn.disabled = false;
      return;
    }
    if (!inputValue) {
      actionOutputPanel.textContent = `No value found for input field. Please enter a value before running the action.`;
      state.runActionBtn.disabled = false;
      return;
    }
    let resp;
    try {
      resp = await runLLMAction(actionId, inputValue, postId);
    } catch (err) {
      actionOutputPanel.textContent = 'Network error: Could not reach LLM backend.';
      showStartOllamaButton(actionOutputPanel);
      state.runActionBtn.disabled = false;
      state.lastActionOutput = '';
      return;
    }
    if (resp.status === 503) {
      actionOutputPanel.textContent = 'Ollama is not running (503 Service Unavailable).';
      showStartOllamaButton(actionOutputPanel);
      state.runActionBtn.disabled = false;
      state.lastActionOutput = '';
      return;
    }
    if (!resp.ok) {
      actionOutputPanel.textContent = `Error: ${resp.status} ${resp.statusText}`;
      state.runActionBtn.disabled = false;
      state.lastActionOutput = '';
      return;
    }
    let result = resp;
    handleLLMResult({
      result,
      state,
      actionOutputPanel,
      outputFieldSelect,
      outputFieldValue,
      postDevFieldsPanel,
      updatePostDevelopmentField,
      fetchPostDevelopment,
      renderPostDevFields
    });
    state.runActionBtn.disabled = false;
  } catch (err) {
    console.error('LLM action error:', err);
    actionOutputPanel.textContent = 'Unexpected error running LLM action.';
    showStartOllamaButton(actionOutputPanel);
    state.runActionBtn.disabled = false;
    state.lastActionOutput = '';
  }
}

/**
 * Handle the result of an LLM action.
 * @param {Object} params - All required arguments and dependencies.
 */
export function handleLLMResult({
  result,
  state,
  actionOutputPanel,
  outputFieldSelect,
  outputFieldValue,
  postDevFieldsPanel,
  updatePostDevelopmentField,
  fetchPostDevelopment,
  renderPostDevFields
}) {
  if (result && result.result && result.result.output) {
    actionOutputPanel.textContent = result.result.output;
    state.lastActionOutput = result.result.output;
    const outputField = outputFieldSelect.value;
    if (outputField && state.lastActionOutput) {
      updatePostDevelopmentField(state.postId, outputField, state.lastActionOutput).then(resp => {
        if (resp.status === 'success') {
          fetchPostDevelopment(state.postId).then(postDev => {
            state.postDev = postDev;
            outputFieldValue.textContent = state.postDev[outputField] || '(No value)';
            renderPostDevFields(postDevFieldsPanel, state.fieldMappings, state.postDev, state.substage);
          });
        }
      });
    }
  } else if (result && result.output) {
    actionOutputPanel.textContent = result.output;
    state.lastActionOutput = result.output;
    const outputField = outputFieldSelect.value;
    if (outputField && state.lastActionOutput) {
      updatePostDevelopmentField(state.postId, outputField, state.lastActionOutput).then(resp => {
        if (resp.status === 'success') {
          fetchPostDevelopment(state.postId).then(postDev => {
            state.postDev = postDev;
            outputFieldValue.textContent = state.postDev[outputField] || '(No value)';
            renderPostDevFields(postDevFieldsPanel, state.fieldMappings, state.postDev, state.substage);
          });
        }
      });
    }
  } else if (result && result.error) {
    actionOutputPanel.textContent = `Error: ${result.error}`;
    state.lastActionOutput = '';
  } else {
    actionOutputPanel.textContent = 'No output.';
    state.lastActionOutput = '';
  }
} 