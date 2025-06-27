// Workflow API Configuration
export const API_CONFIG = {
    BASE_URL: '/api/v1/workflow',
    ENDPOINTS: {
        FIELD_MAPPINGS: '/field-mappings',
        PROMPTS: '/prompts',
        POSTS: '/posts',
        LLM: '/llm'
    }
};

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
    return response.json().then(data => {
        if (!data.success) {
            throw new Error(data.error?.message || 'API request failed');
        }
        return data.data;
    });
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