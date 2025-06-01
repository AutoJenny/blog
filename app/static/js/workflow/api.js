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
 * Fetch post_substage_action for a post/substage.
 */
export async function fetchPostSubstageAction(postId, substage) {
  const resp = await fetch(`/api/v1/llm/post_substage_actions?post_id=${postId}&substage=${substage}`);
  return resp.ok ? await resp.json() : null;
}

/**
 * Save post_substage_action (action, input, output selections).
 */
export async function savePostSubstageAction(postId, substage, actionId, inputField, outputField) {
  const payload = { post_id: postId, substage, action_id: actionId, input_field: inputField, output_field: outputField };
  const resp = await fetch('/api/v1/llm/post_substage_actions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return resp.ok ? await resp.json() : null;
}

/**
 * Fetch the most recent post_substage_action for a given substage (excluding current post).
 */
export async function fetchLastPostSubstageAction(substage, excludePostId) {
  const resp = await fetch(`/api/v1/llm/post_substage_actions/list?page=1&page_size=50`);
  if (!resp.ok) return null;
  const data = await resp.json();
  if (!data.actions) return null;
  // Find the most recent action for this substage, not for the current post
  return data.actions.find(a => a.substage === substage && a.post_id != excludePostId) || null;
} 