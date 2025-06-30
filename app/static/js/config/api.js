/**
 * API Configuration
 * Centralized configuration for API endpoints
 */

// API Configuration
export const API_CONFIG = {
    ENDPOINTS: {
        LLM: '/api/llm',
        BLOG: '/api/blog',
        WORKFLOW: '/api/workflow',
    },
    PATHS: {
        PROMPTS: '/prompts',
        ACTIONS: '/actions',
        PROMPT_PARTS: '/prompt_parts',
        POSTS: '/posts',
        DEVELOPMENT: '/development',
        FIELDS: '/fields',
        SECTIONS: '/sections',
        IMAGES: '/images',
        GENERATE: '/generate',
    }
};

export function buildApiUrl(endpoint, path = '') {
    return `${endpoint}${path}`;
}

export function buildPostApiUrl(postId, path = '') {
    return buildApiUrl(API_CONFIG.ENDPOINTS.BLOG, `${API_CONFIG.PATHS.POSTS}/${postId}${path}`);
}

export function buildLLMApiUrl(path = '') {
    return buildApiUrl(API_CONFIG.ENDPOINTS.LLM, path);
}

export function buildWorkflowApiUrl(path = '') {
    return buildApiUrl(API_CONFIG.ENDPOINTS.WORKFLOW, path);
}

export async function handleApiResponse(response) {
    if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(error.error || `HTTP error! status: ${response.status}`);
    }
    return response.json();
}

// Navigation utilities
export function buildWorkflowUrl(postId, stage, substage) {
    if (!postId || !stage) {
        throw new Error('postId and stage are required for workflow navigation');
    }
    const base = `/workflow/posts/${postId}/${stage}`;
    return substage ? `${base}/${substage}` : base;
}

export function navigateToWorkflow(postId, stage, substage) {
    window.location.href = buildWorkflowUrl(postId, stage, substage);
}

// API request helpers
export async function fetchPost(postId) {
    const response = await fetch(buildPostApiUrl(postId));
    return handleApiResponse(response);
}

export async function fetchPostDevelopment(postId) {
    const response = await fetch(buildPostApiUrl(postId, `/${API_CONFIG.PATHS.DEVELOPMENT}`));
    return handleApiResponse(response);
}

export async function updatePostDevelopment(postId, data) {
    const response = await fetch(buildPostApiUrl(postId, `/${API_CONFIG.PATHS.DEVELOPMENT}`), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    return handleApiResponse(response);
}

// Export API_CONFIG as default as well
export default API_CONFIG; 