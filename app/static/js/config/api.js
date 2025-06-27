/**
 * API Configuration
 * Centralized configuration for API endpoints
 */

const API_CONFIG = {
    BASE_URL: '/api/workflow',
    ENDPOINTS: {
        POSTS: '/posts',
        FIELDS: '/fields',
        PROMPTS: '/prompts',
        LLM: '/llm',
        STAGES: '/stages',
        SECTIONS: '/sections'
    },
    buildUrl: function(endpoint, ...params) {
        const path = params.join('/');
        return `${this.BASE_URL}${endpoint}/${path}`.replace(/\/+$/, '');
    },
    buildPostUrl: function(postId, stage = null, substage = null) {
        let path = `${this.ENDPOINTS.POSTS}/${postId}`;
        if (stage) {
            path += `/${stage}`;
            if (substage) {
                path += `/${substage}`;
            }
        }
        return `${this.BASE_URL}${path}`;
    }
};

// Export for use in other modules
export default API_CONFIG;

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

// API Response handler
export function handleApiResponse(response) {
    if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
    }
    return response.json();
}

// Standard API request builder
export function buildApiUrl(endpoint, params = {}) {
    const url = new URL(`${API_CONFIG.BASE_URL}${endpoint}`, window.location.origin);
    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
            url.searchParams.append(key, value);
        }
    });
    return url.toString();
}

// API request helpers
export async function fetchPost(postId) {
    const response = await fetch(buildApiUrl(`${API_CONFIG.ENDPOINTS.POSTS}/${postId}`));
    return handleApiResponse(response);
}

export async function fetchPostDevelopment(postId) {
    const response = await fetch(buildApiUrl(`${API_CONFIG.ENDPOINTS.POSTS}/${postId}/development`));
    return handleApiResponse(response);
}

export async function updatePostDevelopment(postId, data) {
    const response = await fetch(buildApiUrl(`${API_CONFIG.ENDPOINTS.POSTS}/${postId}/development`), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    return handleApiResponse(response);
} 