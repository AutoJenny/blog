// State management for workflow LLM modular UI

export const state = {
  /** @type {number|null} */
  postId: null,
  /** @type {string|null} */
  substage: null,
  /** @type {HTMLElement|null} */
  workflowRoot: null,
  /** @type {Array} */
  fieldMappings: [],
  /** @type {Object} */
  postDev: {},
  /** @type {Array} */
  llmActions: [],
  /** @type {Object} */
  actionDetails: {},
  /** @type {boolean} */
  isInitializing: true,
  /** @type {string|null} */
  lastActionOutput: null
}; 