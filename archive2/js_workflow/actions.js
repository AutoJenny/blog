// LLM action execution and result handling for workflow LLM modular UI

import { showStartOllamaButton } from '../llm_utils.js';

console.log('[workflow/actions.js] Loaded');

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
  console.log('[executeLLMAction] ENTRY', {
    actionId, inputValue, postId, runLLMAction, state, actionOutputPanel, outputFieldSelect, outputFieldValue, postDevFieldsPanel
  });
  try {
    if (!actionOutputPanel) {
      alert('Error: Output panel not found in DOM.');
      return;
    }
    const requestToken = ++state.lastRequestToken;
    actionOutputPanel.textContent = 'Running action...';
    state.runActionBtn && (state.runActionBtn.disabled = true);
    let resp;
    try {
      console.log('[executeLLMAction] Calling runLLMAction...');
      resp = await runLLMAction?.(actionId, inputValue, postId);
      console.log('[executeLLMAction] runLLMAction response:', resp);
    } catch (err) {
      console.error('[executeLLMAction] runLLMAction error:', err);
      console.warn('[executeLLMAction] Triggering Start Ollama button due to network error');
      showStartOllamaButton(actionOutputPanel, async () => {
        actionOutputPanel.textContent = 'Retrying action...';
        await executeLLMAction({
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
        });
      });
      state.runActionBtn && (state.runActionBtn.disabled = false);
      state.lastActionOutput = '';
      return;
    }
    if (resp?.status === 503) {
      console.warn('[executeLLMAction] Triggering Start Ollama button due to 503 response', resp);
      showStartOllamaButton(actionOutputPanel, async () => {
        actionOutputPanel.textContent = 'Retrying action...';
        await executeLLMAction({
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
        });
      });
      state.runActionBtn && (state.runActionBtn.disabled = false);
      state.lastActionOutput = '';
      return;
    }
    if (resp && resp.ok === false) {
      console.warn('[executeLLMAction] LLM action returned error response', resp);
      actionOutputPanel.textContent = `Error: ${resp.status} ${resp.statusText}`;
      state.runActionBtn && (state.runActionBtn.disabled = false);
      state.lastActionOutput = '';
      return;
    }
    let result = resp;
    console.log('[executeLLMAction] handleLLMResult input:', result);
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
    state.runActionBtn && (state.runActionBtn.disabled = false);
    console.log('[executeLLMAction] EXIT');
  } catch (err) {
    console.error('LLM action error:', err);
    actionOutputPanel.textContent = 'Unexpected error running LLM action.';
    showStartOllamaButton(actionOutputPanel);
    state.runActionBtn && (state.runActionBtn.disabled = false);
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