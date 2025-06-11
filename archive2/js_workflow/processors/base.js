export class BaseProcessor {
    constructor(config) {
        this.inputFields = config.inputFields;
        this.outputFields = config.outputFields;
        this.llmAction = config.llmAction;
        this.postId = config.postId;
    }

    async process() {
        try {
            // Get input values
            const inputs = {};
            for (const field of this.inputFields) {
                const element = document.getElementById(field);
                if (element) {
                    inputs[field] = element.value;
                }
            }

            // Call LLM action
            const response = await fetch(`/api/v1/llm/actions/${this.llmAction}/test`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ input: inputs })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to process action');
            }

            const result = await response.json();
            
            // Update output fields
            for (const field of this.outputFields) {
                const element = document.getElementById(field);
                if (element && result.result) {
                    element.value = result.result;
                    // Trigger change event to ensure any listeners are notified
                    element.dispatchEvent(new Event('change'));
                }
            }

            return result;
        } catch (error) {
            console.error('Error in processor:', error);
            throw error;
        }
    }

    async save() {
        try {
            const data = {};
            for (const field of this.outputFields) {
                const element = document.getElementById(field);
                if (element) {
                    data[field] = element.value;
                }
            }

            const response = await fetch(`/blog/api/v1/post/${this.postId}/development`, {
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