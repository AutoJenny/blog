// Main entry point for modular workflow LLM UI
import * as api from './api.js';
import { registerWorkflowEventHandlers } from './events.js';
import * as render from './render.js';
import { state } from './state.js';

(async function() {
  // Get DOM elements
  const workflowRoot = document.getElementById('llm-workflow-root');
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

  // Get postId and substage from URL/context
  const urlParams = new URLSearchParams(window.location.search);
  state.postId = urlParams.get('post_id');
  state.workflowRoot = workflowRoot;
  state.substage = (workflowRoot && workflowRoot.dataset.substage) || (() => {
    const pathMatch = window.location.pathname.match(/\/workflow\/\w+\/(\w+)/);
    return (pathMatch && pathMatch[1]) || 'idea';
  })();
  if (!state.postId) return;

  // Fetch all data and initialize UI
  state.isInitializing = true;
  state.fieldMappings = await api.fetchFieldMappings();
  state.postDev = await api.fetchPostDevelopment(state.postId);
  state.llmActions = await api.fetchLLMActions();
  state.postSubstageAction = await api.fetchPostSubstageAction(state.postId, state.substage);
  let psa = Array.isArray(state.postSubstageAction) && state.postSubstageAction.length > 0 ? state.postSubstageAction[0] : null;
  // If no psa, try to copy from previous post
  if (!psa) {
    const lastPsa = await api.fetchLastPostSubstageAction(state.substage, state.postId);
    if (lastPsa) {
      await api.savePostSubstageAction(state.postId, state.substage, lastPsa.action_id, lastPsa.input_field, lastPsa.output_field);
      state.postSubstageAction = await api.fetchPostSubstageAction(state.postId, state.substage);
      psa = Array.isArray(state.postSubstageAction) && state.postSubstageAction.length > 0 ? state.postSubstageAction[0] : null;
    }
  }
  render.renderFieldDropdown(inputFieldSelect, state.fieldMappings, psa ? psa.input_field : null, state.substage);
  render.renderFieldDropdown(outputFieldSelect, state.fieldMappings, psa ? psa.output_field : null, state.substage);
  render.renderActionDropdown(actionSelect, state.llmActions, psa ? psa.action_id : null);
  render.renderPostDevFields(postDevFieldsPanel, state.fieldMappings, state.postDev, state.substage);
  if (inputFieldSelect.value) inputFieldValue.textContent = state.postDev[inputFieldSelect.value] || '(No value)';
  if (outputFieldSelect.value) outputFieldValue.textContent = state.postDev[outputFieldSelect.value] || '(No value)';
  state.isInitializing = false;
  actionSelect.dispatchEvent(new Event('change'));
  render.updatePanelVisibility(actionSelect, document.getElementById('inputPanel'), document.getElementById('outputPanel'));

  // Register all event handlers
  registerWorkflowEventHandlers({
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
    savePostSubstageAction: api.savePostSubstageAction,
    fetchPostSubstageAction: api.fetchPostSubstageAction,
    fetchPostDevelopment: api.fetchPostDevelopment,
    updatePostDevelopmentField: api.updatePostDevelopmentField,
    renderFieldDropdown: render.renderFieldDropdown,
    renderPostDevFields: render.renderPostDevFields,
    showActionDetails: render.showActionDetails,
    updatePanelVisibility: render.updatePanelVisibility,
    state
  });
})(); 