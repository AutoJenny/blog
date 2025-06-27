/**
 * Workflow Navigation Utilities
 */

import API_CONFIG from './config/api.js';

/**
 * Navigate to a workflow stage/substage
 * @param {number} postId - The post ID
 * @param {string} stage - The stage name (optional)
 * @param {string} substage - The substage name (optional)
 * @param {string} step - The step name (optional)
 */
export function navigateToWorkflow(postId, stage = null, substage = null, step = null) {
    let url = `/workflow/posts/${postId}`;
    if (stage) {
        url += `/${stage}`;
        if (substage) {
            url += `/${substage}`;
            if (step) {
                url += `?step=${step}`;
            }
        }
    }
    window.location.href = url;
}

/**
 * Build an API URL for workflow operations
 * @param {string} endpoint - The endpoint from API_CONFIG.ENDPOINTS
 * @param {...string} params - Path parameters
 * @returns {string} The complete API URL
 */
export function buildApiUrl(endpoint, ...params) {
    return API_CONFIG.buildUrl(endpoint, ...params);
}

/**
 * Build a post-specific API URL
 * @param {number} postId - The post ID
 * @param {string} stage - The stage name (optional)
 * @param {string} substage - The substage name (optional)
 * @returns {string} The complete API URL
 */
export function buildPostApiUrl(postId, stage = null, substage = null) {
    return API_CONFIG.buildPostUrl(postId, stage, substage);
}

// Export all navigation utilities
export default {
    navigateToWorkflow,
    buildApiUrl,
    buildPostApiUrl
}; 