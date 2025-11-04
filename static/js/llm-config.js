/**
 * LLM Module Configuration
 * Centralized configuration for all LLM module types
 */

const LLM_CONFIGS = {
    'ideas': {
        promptEndpoint: '/planning/api/posts/{id}/expanded-idea-prompt',
        generateEndpoint: '/planning/api/posts/{id}/expanded-idea',
        resultsField: 'expanded_idea',
        resultsTitle: 'Expanded Idea',
        allowEdit: true
    },
    'brainstorm': {
        promptEndpoint: '/planning/api/posts/{id}/brainstorm-prompt',
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
        promptEndpoint: '/planning/api/posts/{id}/section-titling-prompt',
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
    },
    'section_structure': { // New config for section structure design
        promptEndpoint: '/planning/api/posts/{id}/section-structure-prompt',
        generateEndpoint: '/planning/api/sections/design-structure',
        resultsField: 'section_structure',
        resultsTitle: 'Generated Section Structure',
        allowEdit: true
    },
    'topic_allocation': { // New config for topic allocation
        promptEndpoint: '/planning/api/posts/{id}/topic-allocation-prompt',
        generateEndpoint: '/planning/api/sections/allocate-topics',
        resultsField: 'results',
        resultsTitle: 'Generated Topic Allocation',
        allowEdit: true
    },
    'topic_refinement': { // New config for topic refinement
        promptEndpoint: '/planning/api/llm/prompts/topic-refinement',
        generateEndpoint: '/planning/api/sections/refine-topics',
        resultsField: 'refined_topics',
        resultsTitle: 'Generated Topic Refinement',
        allowEdit: true
    },
                'image_concepts': { // New config for image concepts generation
                    promptEndpoint: '/authoring/api/llm/prompts/image-concepts',
                    generateEndpoint: '/authoring/api/posts/{id}/sections/{section_id}/generate-image-concepts',
                    resultsField: 'image_concepts',
                    resultsTitle: 'Generated Image Concepts',
                    allowEdit: true
                },
                'image_prompts': { // New config for image prompts generation
                    promptEndpoint: '/authoring/api/llm/prompts/image-prompts',
                    generateEndpoint: '/authoring/api/posts/{id}/sections/{section_id}/generate-image-prompts',
                    resultsField: 'image_prompts',
                    resultsTitle: 'Generated Image Prompt',
                    allowEdit: true
                },
                'image_captions': { // New config for image captions generation
                    promptEndpoint: '/authoring/api/llm/prompts/image-captions',
                    generateEndpoint: '/authoring/api/posts/{id}/sections/{section_id}/generate-image-captions',
                    resultsField: 'image_captions',
                    resultsTitle: 'Generated Image Captions',
                    allowEdit: true
                },
                'image_generation': { // New config for image generation
                    promptEndpoint: '/authoring/api/llm/prompts/image-generation',
                    generateEndpoint: '/authoring/api/posts/{id}/sections/{section_id}/generate-image',
                    resultsField: 'generated_image',
                    resultsTitle: 'Generated Image',
                    allowEdit: false
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
    
    // Replace {id} placeholder in endpoints
    if (config.promptEndpoint && config.promptEndpoint.includes('{id}')) {
        config.promptEndpoint = config.promptEndpoint.replace('{id}', postId);
    }
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

// Make initializeLLMModule available globally
window.initializeLLMModule = initializeLLMModule;
