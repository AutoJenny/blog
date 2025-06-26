export class PromptSelector {
    constructor(postId, stepId) {
        this.postId = postId;
        this.stepId = stepId;
        this.isLoading = false;

        // Get DOM elements
        this.systemPromptSelect = document.getElementById('system_prompt_select');
        this.taskPromptSelect = document.getElementById('task_prompt_select');
        this.systemPromptTextarea = document.getElementById('system_prompt');
        this.taskPromptTextarea = document.getElementById('task_prompt');

        // Initialize
        this.loadPrompts().then(() => {
            // Only load saved prompts after dropdowns are populated
            this.loadSavedPrompts();
        });

        // Add event listeners
        this.systemPromptSelect.addEventListener('change', () => this.handleSystemPromptChange());
        this.taskPromptSelect.addEventListener('change', () => this.handleTaskPromptChange());
    }

    async loadPrompts() {
        try {
            this.setLoadingState(true);

            // Get system prompts
            const systemResponse = await fetch('/workflow/api/prompts/?prompt_type=system');
            if (!systemResponse.ok) {
                throw new Error(`HTTP error! status: ${systemResponse.status}`);
            }
            const systemPrompts = await systemResponse.json();

            // Get task prompts
            const taskResponse = await fetch('/workflow/api/prompts/?prompt_type=task');
            if (!taskResponse.ok) {
                throw new Error(`HTTP error! status: ${taskResponse.status}`);
            }
            const taskPrompts = await taskResponse.json();

            // Populate system prompts dropdown
            this.systemPromptSelect.innerHTML = '<option value="">Select system prompt...</option>';
            systemPrompts.forEach(prompt => {
                const option = document.createElement('option');
                option.value = prompt.id;
                option.textContent = prompt.name;
                option.dataset.text = prompt.prompt_text;
                this.systemPromptSelect.appendChild(option);
            });

            // Populate task prompts dropdown
            this.taskPromptSelect.innerHTML = '<option value="">Select task prompt...</option>';
            taskPrompts.forEach(prompt => {
                const option = document.createElement('option');
                option.value = prompt.id;
                option.textContent = `${prompt.name} (${prompt.stage}/${prompt.substage}/${prompt.step})`;
                option.dataset.text = prompt.prompt_text;
                this.taskPromptSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading prompts:', error);
            this.showFeedback('error', 'Failed to load prompts');
        } finally {
            this.setLoadingState(false);
        }
    }

    async loadSavedPrompts() {
        try {
            this.setLoadingState(true);
            const response = await fetch(`/workflow/api/step_prompts/${this.postId}/${this.stepId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            if (data.system_prompt_id) {
                this.systemPromptSelect.value = data.system_prompt_id.toString();
                this.systemPromptTextarea.value = data.system_prompt_text || '';
            }
            
            if (data.task_prompt_id) {
                this.taskPromptSelect.value = data.task_prompt_id.toString();
                this.taskPromptTextarea.value = data.task_prompt_text || '';
            }
        } catch (error) {
            console.error('Error loading saved prompts:', error);
            this.showFeedback('error', 'Failed to load saved prompts');
        } finally {
            this.setLoadingState(false);
        }
    }

    async handleSystemPromptChange() {
        if (this.isLoading) return;
        
        // Update textarea with selected prompt text
        const selectedOption = this.systemPromptSelect.selectedOptions[0];
        this.systemPromptTextarea.value = selectedOption?.dataset?.text || '';
        
        // Save only the system prompt
        await this.savePrompt('system');
    }

    async handleTaskPromptChange() {
        if (this.isLoading) return;
        
        // Update textarea with selected prompt text
        const selectedOption = this.taskPromptSelect.selectedOptions[0];
        this.taskPromptTextarea.value = selectedOption?.dataset?.text || '';
        
        // Save only the task prompt
        await this.savePrompt('task');
    }

    async savePrompt(type) {
        if (this.isLoading) return;
        
        try {
            this.isLoading = true;
            this.setLoadingState(true);
            
            // Only send the prompt type that changed
            const data = {};
            if (type === 'system') {
                data.system_prompt_id = this.systemPromptSelect.value ? parseInt(this.systemPromptSelect.value) : null;
            } else {
                data.task_prompt_id = this.taskPromptSelect.value ? parseInt(this.taskPromptSelect.value) : null;
            }
            
            const response = await fetch(`/workflow/api/step_prompts/${this.postId}/${this.stepId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // Show success feedback
            this.showFeedback('success', `${type === 'system' ? 'System' : 'Task'} prompt saved successfully`);
            
        } catch (error) {
            console.error('Error saving prompt:', error);
            this.showFeedback('error', `Failed to save ${type} prompt`);
        } finally {
            this.isLoading = false;
            this.setLoadingState(false);
        }
    }

    setLoadingState(isLoading) {
        // Disable dropdowns during loading
        this.systemPromptSelect.disabled = isLoading;
        this.taskPromptSelect.disabled = isLoading;
        
        // Add visual loading indicator
        this.systemPromptSelect.classList.toggle('opacity-50', isLoading);
        this.taskPromptSelect.classList.toggle('opacity-50', isLoading);
    }

    showFeedback(type, message) {
        // Remove any existing feedback
        const existingFeedback = document.querySelector('.prompt-feedback');
        if (existingFeedback) {
            existingFeedback.remove();
        }

        // Add temporary feedback message
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = `prompt-feedback text-sm ${type === 'success' ? 'text-green-500' : 'text-red-500'} mt-2`;
        feedbackDiv.textContent = message;
        
        this.taskPromptSelect.parentNode.appendChild(feedbackDiv);
        
        // Remove feedback after 3 seconds
        setTimeout(() => feedbackDiv.remove(), 3000);
    }
} 