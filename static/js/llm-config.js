/**
 * LLM Module Configuration
 * Centralized configuration for all LLM module types
 */

const LLM_CONFIGS = {
    'ideas': {
        promptEndpoint: '/planning/api/llm/prompts/idea-expansion',
        generateEndpoint: '/planning/api/posts/{id}/expanded-idea',
        resultsField: 'expanded_idea',
        resultsTitle: 'Expanded Idea',
        allowEdit: false
    },
    'brainstorm': {
        promptEndpoint: '/planning/api/llm/prompts/topic-brainstorming',
        generateEndpoint: '/planning/api/brainstorm/topics',
        resultsField: 'idea_scope',
        resultsTitle: 'Generated Topics',
        allowEdit: true
    },
    'grouping': {
        promptEndpoint: '/planning/api/llm/prompts/section-planning', // Reusing prompt for now
        generateEndpoint: '/planning/api/sections/group',
        resultsField: 'groups',
        resultsTitle: 'Generated Groups',
        allowEdit: true
    },
    'titling': {
        promptEndpoint: '/planning/api/llm/prompts/section-titling', // Updated to use new prompt
        generateEndpoint: '/planning/api/sections/title',
        resultsField: 'sections',
        resultsTitle: 'Generated Sections',
        allowEdit: true
    },
    'sections': {
        promptEndpoint: '/planning/api/llm/prompts/section-planning',
        generateEndpoint: '/planning/api/sections/plan',
        resultsField: 'sections',
        resultsTitle: 'Generated Sections',
        allowEdit: true
    },
    'author_draft': { // New config for authoring section drafts
        promptEndpoint: '/authoring/api/llm/prompts/section-drafting',
        generateEndpoint: '/authoring/api/posts/{id}/sections/{section_id}/generate',
        resultsField: 'draft_content',
        resultsTitle: 'Generated Draft',
        allowEdit: true
    }
};

/**
 * Initialize LLM module with configuration
 * @param {string} pageType - Type of page (ideas, brainstorm, etc.)
 * @param {number} postId - Post ID
 * @param {number} sectionId - Section ID (optional, for authoring)
 * @returns {LLMModule|null} Initialized LLM module
 */
function initializeLLMModule(pageType, postId, sectionId = null) {
    const config = LLM_CONFIGS[pageType];
    if (!config) {
        console.error(`Unknown page type: ${pageType}`);
        return null;
    }
    
    // Replace {id} placeholder in generate endpoint
    config.generateEndpoint = config.generateEndpoint.replace('{id}', postId);
    
    // Replace {section_id} placeholder if present and sectionId provided
    if (sectionId && config.generateEndpoint.includes('{section_id}')) {
        config.generateEndpoint = config.generateEndpoint.replace('{section_id}', sectionId);
    }
    
    const module = new LLMModule(config);
    module.setPostId(postId);
    
    // Set results title
    const resultsTitle = document.getElementById('results-title');
    if (resultsTitle) {
        resultsTitle.textContent = config.resultsTitle;
    }
    
    return module;
}
