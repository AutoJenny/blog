// Event handler registration for workflow LLM modular UI

import { showStartOllamaButton } from '../llm_utils.js';
import { executeLLMAction } from './actions.js';

console.log('[workflow/events.js] Registering event handlers');

/**
 * Register all event handlers for the workflow modular LLM UI.
 * @param {Object} params - All required DOM elements and dependencies.
 * @param {HTMLElement} params.inputFieldSelect
 * @param {HTMLElement} params.inputFieldValue
 * @param {HTMLElement} params.actionSelect
 * @param {HTMLElement} params.actionPromptPanel
 * @param {HTMLElement} params.runActionBtn
 * @param {HTMLElement} params.outputFieldSelect
 * @param {HTMLElement} params.outputFieldValue
 * @param {HTMLElement} params.actionOutputPanel
 * @param {HTMLElement} params.saveOutputBtn
 * @param {HTMLElement} params.postDevFieldsPanel
 * @param {Function} params.savePostSubstageAction
 * @param {Function} params.fetchPostSubstageAction
 * @param {Function} params.fetchPostDevelopment
 * @param {Function} params.updatePostDevelopmentField
 * @param {Function} params.renderFieldDropdown
 * @param {Function} params.renderPostDevFields
 * @param {Function} params.showActionDetails
 * @param {Function} params.updatePanelVisibility
 * @param {Object} params.state - All state variables
 * @param {Function} params.runLLMAction - Added for the new event delegation handler
 */
export function registerWorkflowEventHandlers({
  inputFieldSelect,
  inputFieldValue,
  actionSelect,
  actionPromptPanel,
  runActionBtn,
  outputFieldSelect,
  outputFieldValue,
  actionOutputPanel,
  saveOutputBtn,
  postDevFieldsPanel,
  savePostSubstageAction,
  fetchPostSubstageAction,
  fetchPostDevelopment,
  updatePostDevelopmentField,
  renderFieldDropdown,
  renderPostDevFields,
  showActionDetails,
  updatePanelVisibility,
  runLLMAction,
  state
}) {
  // Diagnostic: check if runActionBtn exists at registration
  console.log('[workflow/events.js] runActionBtn:', runActionBtn);
  if (!runActionBtn) {
    console.error('[workflow/events.js] runActionBtn is null or undefined at registration!');
  }

  // Field dropdown change handler
  inputFieldSelect.addEventListener('change', async () => {
    if (state.isInitializing) return;
    const field = inputFieldSelect.value;
    inputFieldValue.textContent = state.postDev[field] || '(No value)';
    if (!state.postId || !state.substage || !actionSelect.value) {
      console.warn('Not saving: missing required keys', { postId: state.postId, substage: state.substage, actionId: actionSelect.value });
      return;
    }
    console.log('Saving post_substage_action (input change):', { postId: state.postId, substage: state.substage, actionId: actionSelect.value, inputField: inputFieldSelect.value, outputField: outputFieldSelect.value });
    await savePostSubstageAction(state.postId, state.substage, actionSelect.value, inputFieldSelect.value, outputFieldSelect.value);
    state.postSubstageAction = await fetchPostSubstageAction(state.postId, state.substage);
    const psa = Array.isArray(state.postSubstageAction) && state.postSubstageAction.length > 0 ? state.postSubstageAction[0] : null;
    renderFieldDropdown(inputFieldSelect, state.fieldMappings, inputFieldSelect.value, state.substage);
    if (psa && psa.output_field) outputFieldSelect.value = psa.output_field;
    if (psa && psa.output_field) outputFieldValue.textContent = state.postDev[psa.output_field] || '(No value)';
  });

  // Output field dropdown change handler
  outputFieldSelect.addEventListener('change', async () => {
    if (state.isInitializing) return;
    const field = outputFieldSelect.value;
    outputFieldValue.textContent = state.postDev[field] || '(No value)';
    if (!state.postId || !state.substage || !actionSelect.value) {
      console.warn('Not saving: missing required keys', { postId: state.postId, substage: state.substage, actionId: actionSelect.value });
      return;
    }
    console.log('Saving post_substage_action (output change):', { postId: state.postId, substage: state.substage, actionId: actionSelect.value, inputField: inputFieldSelect.value, outputField: outputFieldSelect.value });
    await savePostSubstageAction(state.postId, state.substage, actionSelect.value, inputFieldSelect.value, outputFieldSelect.value);
    state.postSubstageAction = await fetchPostSubstageAction(state.postId, state.substage);
    const psa = Array.isArray(state.postSubstageAction) && state.postSubstageAction.length > 0 ? state.postSubstageAction[0] : null;
    if (psa && psa.input_field) inputFieldSelect.value = psa.input_field;
    if (psa && psa.output_field) outputFieldSelect.value = psa.output_field;
    if (psa && psa.output_field) outputFieldValue.textContent = state.postDev[psa.output_field] || '(No value)';
  });

  // Action dropdown change handler
  actionSelect.addEventListener('change', async () => {
    updatePanelVisibility(actionSelect, document.getElementById('inputPanel'), document.getElementById('outputPanel'));
    const actionId = actionSelect.value;
    await showActionDetails(actionId, actionPromptPanel, state.fetchLLMActionDetails);
    if (!actionId || !state.postId || !state.substage) {
      console.warn('Not saving: missing required keys', { postId: state.postId, substage: state.substage, actionId });
      return;
    }
    console.log('Saving post_substage_action (action change):', { postId: state.postId, substage: state.substage, actionId, inputField: inputFieldSelect.value, outputField: outputFieldSelect.value });
    await savePostSubstageAction(state.postId, state.substage, actionId, inputFieldSelect.value, outputFieldSelect.value);
    state.postSubstageAction = await fetchPostSubstageAction(state.postId, state.substage);
    const psa = Array.isArray(state.postSubstageAction) && state.postSubstageAction.length > 0 ? state.postSubstageAction[0] : null;
    if (psa && psa.input_field) inputFieldSelect.value = psa.input_field;
    if (psa && psa.output_field) outputFieldSelect.value = psa.output_field;
    if (psa && psa.output_field) outputFieldValue.textContent = state.postDev[psa.output_field] || '(No value)';
  });

  // Run Action button handler logic as a function
  async function handleRunActionClick({
    inputFieldSelect,
    actionSelect,
    actionOutputPanel,
    runActionBtn,
    state,
    executeLLMAction,
    runLLMAction,
    updatePostDevelopmentField,
    fetchPostDevelopment,
    renderPostDevFields,
    outputFieldSelect,
    outputFieldValue,
    postDevFieldsPanel,
    showStartOllamaButton
  }) {
    try {
      console.log('[handleRunActionClick] ENTRY');
      if (!actionOutputPanel) {
        alert('Error: Output panel not found in DOM.');
        return;
      }
      const requestToken = ++state.lastRequestToken;
      actionOutputPanel.textContent = 'Running action...';
      runActionBtn.disabled = true;
      console.log('[handleRunActionClick] Checking Ollama status...');
      const ollamaOk = await state.checkOllamaStatus();
      if (!ollamaOk) {
        actionOutputPanel.textContent = 'Ollama is not running.';
        showStartOllamaButton(actionOutputPanel);
        runActionBtn.disabled = false;
        return;
      }
      const actionId = actionSelect.value;
      const inputField = inputFieldSelect.value;
      console.log('[handleRunActionClick] actionId:', actionId, 'inputField:', inputField);
      if (!actionId || !inputField) {
        actionOutputPanel.textContent = 'Please select both an action and an input field.';
        runActionBtn.disabled = false;
        return;
      }
      const inputValue = state.postDev[inputField] || '';
      console.log('[handleRunActionClick] inputValue:', inputValue);
      if (!inputValue) {
        actionOutputPanel.textContent = `No value found for input field: ${inputField}. Please enter a value before running the action.`;
        runActionBtn.disabled = false;
        return;
      }
      console.log('[handleRunActionClick] Calling executeLLMAction...');
      await executeLLMAction({
        actionId,
        inputValue,
        postId: state.postId,
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
      console.log('[handleRunActionClick] EXIT');
    } catch (err) {
      console.error('[handleRunActionClick] ERROR:', err);
      actionOutputPanel.textContent = 'Unexpected error running LLM action.';
      showStartOllamaButton(actionOutputPanel);
      runActionBtn.disabled = false;
      state.lastActionOutput = '';
    }
  }

  // Remove direct addEventListener from runActionBtn
  // Instead, use event delegation

  document.addEventListener('click', async (e) => {
    if (e.target && e.target.id === 'runActionBtn') {
      console.log('[DELEGATED] Run Action button handler fired');
      await handleRunActionClick({
        inputFieldSelect,
        actionSelect,
        actionOutputPanel,
        runActionBtn: e.target,
        state,
        executeLLMAction,
        runLLMAction,
        updatePostDevelopmentField,
        fetchPostDevelopment,
        renderPostDevFields,
        outputFieldSelect,
        outputFieldValue,
        postDevFieldsPanel,
        showStartOllamaButton
      });
    }
  });

  // Save Output button handler
  saveOutputBtn.addEventListener('click', async () => {
    const outputField = outputFieldSelect.value;
    if (!outputField) {
      actionOutputPanel.textContent = 'Please select an output field.';
      return;
    }
    if (!state.lastActionOutput) {
      actionOutputPanel.textContent = 'No output to save.';
      return;
    }
    const resp = await updatePostDevelopmentField(state.postId, outputField, state.lastActionOutput);
    if (resp.status === 'success') {
      actionOutputPanel.textContent = 'Output saved!';
      state.postDev = await fetchPostDevelopment(state.postId);
      outputFieldValue.textContent = state.postDev[outputField] || '(No value)';
      renderPostDevFields(postDevFieldsPanel, state.fieldMappings, state.postDev, state.substage);
    } else {
      actionOutputPanel.textContent = 'Failed to save output.';
    }
  });
} 