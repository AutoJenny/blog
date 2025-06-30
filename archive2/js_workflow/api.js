// API utility functions for workflow LLM modular UI

/**
 * Fetch field mappings from the backend.
 */
export async function fetchFieldMappings() {
  const resp = await fetch('/api/settings/field-mapping');
  return resp.ok ? await resp.json() : [];
}

/**
 * Fetch post_development for a post.
 */
export async function fetchPostDevelopment(postId) {
  const resp = await fetch(`/api/v1/post/${postId}/development`);
  return resp.ok ? await resp.json() : {};
}

/**
 * Update a post_development field.
 */
export async function updatePostDevelopmentField(postId, field, value) {
  const resp = await fetch(`/blog/api/v1/post/${postId}/development`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ [field]: value })
  });
  return resp.ok ? await resp.json() : { status: 'error' };
}

/**
 * Fetch all LLM actions.
 */
export async function fetchLLMActions() {
  const resp = await fetch('/api/v1/llm/actions');
  return resp.ok ? await resp.json() : [];
}

/**
 * Fetch details for a specific LLM action.
 */
export async function fetchLLMActionDetails(actionId) {
  const resp = await fetch(`/api/v1/llm/actions/${actionId}`);
  return resp.ok ? await resp.json() : {};
}

/**
 * Run an LLM action.
 */
export async function runLLMAction(actionId, input, postId) {
  const resp = await fetch(`/api/v1/llm/actions/${actionId}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ input_text: input, post_id: postId })
  });
  return resp.ok ? await resp.json() : { error: 'Failed to run action' };
}

/**
 * Fetch post_workflow_step_action for a post/step.
 */
export async function fetchPostWorkflowStepAction(postId, stepId) {
  const resp = await fetch(`/api/v1/llm/post_workflow_step_actions?post_id=${postId}&step_id=${stepId}`);
  return resp.ok ? await resp.json() : null;
}

/**
 * Save post_workflow_step_action (action, input, output selections).
 */
export async function savePostWorkflowStepAction(postId, stepId, actionId, inputField, outputField) {
  const payload = { post_id: postId, step_id: stepId, action_id: actionId, input_field: inputField, output_field: outputField };
  const resp = await fetch('/api/v1/llm/post_workflow_step_actions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return resp.ok ? await resp.json() : null;
}

/**
 * Fetch the most recent post_workflow_step_action for a given step (excluding current post).
 */
export async function fetchLastPostWorkflowStepAction(stepId, excludePostId) {
  const resp = await fetch(`/api/v1/llm/post_workflow_step_actions/list?page=1&page_size=50`);
  if (!resp.ok) return null;
  const data = await resp.json();
  if (!data.actions) return null;
  // Find the most recent action for this step, not for the current post
  return data.actions.find(a => a.step_id === stepId && a.post_id != excludePostId) || null;
}

/**
 * Check if Ollama is running (returns true/false)
 */
export async function checkOllamaStatus() {
  try {
    const resp = await fetch('/api/v1/llm/ollama/status');
    if (!resp.ok) return false;
    const data = await resp.json();
    return !!(data && data.status === 'running');
  } catch (e) {
    return false;
  }
} 