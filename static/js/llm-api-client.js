/**
 * LLM API Client
 * Handles all HTTP requests and API interactions for LLM module
 */

class LLMAPIClient {
    constructor() {
        // No initialization needed - all methods are stateless
    }

    /**
     * Load prompt from API
     * @param {string} promptEndpoint - API endpoint for prompt
     * @returns {Promise<Object>} API response with prompt data
     */
    async loadPrompt(promptEndpoint) {
        try {
            const response = await fetch(promptEndpoint);
            const data = await response.json();
            
            if (data.success) {
                return {
                    success: true,
                    prompt: data.prompt,
                    llm_config: data.llm_config
                };
            } else {
                return {
                    success: false,
                    error: 'Failed to load prompt'
                };
            }
        } catch (error) {
            console.error('Error loading prompt:', error);
            return {
                success: false,
                error: 'Failed to load prompt'
            };
        }
    }

    /**
     * Save prompt to API
     * @param {string} promptEndpoint - API endpoint for prompt
     * @param {Object} promptData - Prompt data to save
     * @returns {Promise<Object>} API response
     */
    async savePrompt(promptEndpoint, promptData) {
        try {
            const response = await fetch(promptEndpoint, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(promptData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                return {
                    success: true,
                    prompt: data.prompt
                };
            } else {
                return {
                    success: false,
                    error: 'Failed to save prompt'
                };
            }
        } catch (error) {
            console.error('Error saving prompt:', error);
            return {
                success: false,
                error: 'Failed to save prompt'
            };
        }
    }

    /**
     * Generate content using API
     * @param {string} generateEndpoint - API endpoint for generation
     * @param {Object} requestData - Data to send with request
     * @returns {Promise<Object>} API response with generated content
     */
    async generateContent(generateEndpoint, requestData) {
        try {
            // Display the actual message being sent to LLM for debugging
            this.displayLLMMessage(requestData);
            
            const response = await fetch(generateEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Display the actual LLM message if provided
                if (data.llm_message) {
                    this.displayLLMMessageFromResponse(data.llm_message);
                }
                
                return {
                    success: true,
                    results: data.results || data,
                    draft_content: data.draft_content,
                    error: null
                };
            } else {
                return {
                    success: false,
                    error: data.error || 'Generation failed'
                };
            }
        } catch (error) {
            console.error('Error generating content:', error);
            return {
                success: false,
                error: 'Generation failed'
            };
        }
    }

    /**
     * Display the actual message being sent to LLM for debugging
     * @param {Object} requestData - The request data being sent
     */
    displayLLMMessage(requestData) {
        const debugElement = document.getElementById('llm-message-debug');
        if (!debugElement) return;

        // Format the message for display
        let debugMessage = '';
        
        if (requestData.system_prompt) {
            debugMessage += '=== SYSTEM PROMPT ===\n';
            debugMessage += requestData.system_prompt + '\n\n';
        }
        
        if (requestData.user_prompt) {
            debugMessage += '=== USER PROMPT ===\n';
            debugMessage += requestData.user_prompt + '\n\n';
        }
        
        if (requestData.messages) {
            debugMessage += '=== MESSAGES ===\n';
            requestData.messages.forEach((msg, index) => {
                debugMessage += `Message ${index + 1} (${msg.role}):\n`;
                debugMessage += msg.content + '\n\n';
            });
        }
        
        if (requestData.model) {
            debugMessage += '=== MODEL ===\n';
            debugMessage += requestData.model + '\n\n';
        }
        
        if (requestData.temperature !== undefined) {
            debugMessage += '=== TEMPERATURE ===\n';
            debugMessage += requestData.temperature + '\n\n';
        }
        
        if (requestData.max_tokens) {
            debugMessage += '=== MAX TOKENS ===\n';
            debugMessage += requestData.max_tokens + '\n\n';
        }

        debugElement.textContent = debugMessage || 'No message data available';
    }

    /**
     * Display the actual constructed LLM message from API response
     * @param {string} llmMessage - The full constructed message from the API
     */
    displayLLMMessageFromResponse(llmMessage) {
        const debugElement = document.getElementById('llm-message-debug');
        if (!debugElement) return;

        debugElement.textContent = llmMessage;
    }

    /**
     * Auto-save content to API (for authoring)
     * @param {string} content - Content to save
     * @param {number} postId - Post ID
     * @param {number} sectionId - Section ID
     * @returns {Promise<Object>} API response
     */
    async autoSaveContent(content, postId, sectionId) {
        try {
            const response = await fetch(`/authoring/api/posts/${postId}/sections/${sectionId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    draft_content: content,
                    status: 'complete'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                return {
                    success: true,
                    message: 'Content auto-saved successfully'
                };
            } else {
                return {
                    success: false,
                    error: data.error || 'Auto-save failed'
                };
            }
        } catch (error) {
            console.error('Error auto-saving content:', error);
            return {
                success: false,
                error: 'Error auto-saving content'
            };
        }
    }

    /**
     * Generic API request method
     * @param {string} url - API endpoint
     * @param {Object} options - Fetch options
     * @returns {Promise<Object>} API response
     */
    async request(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            const data = await response.json();
            return {
                success: response.ok,
                data: data,
                error: response.ok ? null : (data.error || 'Request failed')
            };
        } catch (error) {
            console.error('API request error:', error);
            return {
                success: false,
                error: error.message || 'Request failed'
            };
        }
    }
}
