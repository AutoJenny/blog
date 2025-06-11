// Settings persistence, auto-cloning, and defaults for workflow LLM modular UI

/**
 * Persist workflow settings (action, input, output selections).
 * @param {Object} params - All required arguments and dependencies.
 */
export async function persistSettings({ postId, substage, actionId, inputField, outputField, savePostSubstageAction }) {
  if (!postId || !substage || !actionId) {
    console.warn('Not saving: missing required keys', { postId, substage, actionId });
    return;
  }
  await savePostSubstageAction(postId, substage, actionId, inputField, outputField);
}

/**
 * Clone settings from the previous post for a given substage.
 * @param {Object} params - All required arguments and dependencies.
 */
export async function clonePreviousSettings({ postId, substage, fetchLastPostSubstageAction, savePostSubstageAction, fetchPostSubstageAction }) {
  const lastPsa = await fetchLastPostSubstageAction(substage, postId);
  if (lastPsa) {
    await savePostSubstageAction(postId, substage, lastPsa.action_id, lastPsa.input_field, lastPsa.output_field);
    return await fetchPostSubstageAction(postId, substage);
  }
  return null;
}

/**
 * Apply default settings if no previous or persisted settings exist.
 * @param {Object} params - All required arguments and dependencies.
 */
export function applyDefaultSettings({ select, mappings, substage }) {
  // Find the first field for the current substage
  const substageField = mappings.find(m => m.substage_name === substage);
  const substageDefault = substageField ? substageField.field_name : (mappings[0] ? mappings[0].field_name : '');
  select.value = substageDefault;
} 