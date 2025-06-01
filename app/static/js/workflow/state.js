// State management for workflow LLM modular UI

/** @type {number|null} */
export let postId = null;
/** @type {string|null} */
export let substage = null;
/** @type {HTMLElement|null} */
export let workflowRoot = null;

/** @type {Array} */
export let fieldMappings = [];
/** @type {Object} */
export let postDev = {};
/** @type {Array} */
export let llmActions = [];
/** @type {Object} */
export let actionDetails = {};

/** @type {boolean} */
export let isInitializing = true;
/** @type {string|null} */
export let lastActionOutput = null; 