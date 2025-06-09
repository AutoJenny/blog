import { BaseProcessor } from '/static/js/workflow/processors/base.js';

class IdeaProcessor extends BaseProcessor {
    constructor(postId) {
        super({
            inputFields: ['idea_seed'],
            outputFields: ['basic_idea'],
            llmAction: 48,  // idea_generation action ID
            postId: postId
        });
    }

    async process() {
        try {
            // Get idea seed from post table
            const ideaSeed = document.getElementById('idea_seed').value;
            if (!ideaSeed) {
                throw new Error('Idea seed is required');
            }

            const requestData = { input: { idea_seed: ideaSeed } };
            console.log('Sending request data:', requestData);

            // Call LLM action
            const response = await fetch(`/api/v1/llm/actions/${this.llmAction}/test`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                const error = await response.json();
                console.error('Server error:', error);
                throw new Error(error.error || 'Failed to generate idea');
            }

            const result = await response.json();
            console.log('Received result:', result);
            
            // Update basic_idea field in post_development
            const basicIdeaElement = document.getElementById('basic_idea');
            if (basicIdeaElement && result.result) {
                basicIdeaElement.value = result.result;
                // Trigger change event to ensure any listeners are notified
                basicIdeaElement.dispatchEvent(new Event('change'));
            } else {
                console.error('Could not find basic_idea element or result is undefined:', result);
            }

            return result;
        } catch (error) {
            console.error('Error in idea processor:', error);
            throw error;
        }
    }

    async save() {
        try {
            const data = {
                idea_seed: document.getElementById('idea_seed').value,
                basic_idea: document.getElementById('basic_idea').value
            };

            const response = await fetch(`/api/v1/post/${this.postId}/development`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to save');
            }

            return await response.json();
        } catch (error) {
            console.error('Error saving:', error);
            throw error;
        }
    }
}

export { IdeaProcessor };
