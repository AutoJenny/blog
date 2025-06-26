export class PromptSelector {
    constructor(postId, stepId) {
        this.postId = postId;
        this.stepId = stepId;
        this.systemPromptSelect = document.getElementById('system_prompt_select');
        this.taskPromptSelect = document.getElementById('task_prompt_select');
        this.systemPromptTextarea = document.getElementById('system_prompt');
        this.taskPromptTextarea = document.getElementById('task_prompt');

        // Initialize
        this.loadPrompts();
        this.loadSavedPrompts();

        // Add event listeners
        this.systemPromptSelect.addEventListener('change', () => this.handleSystemPromptChange());
        this.taskPromptSelect.addEventListener('change', () => this.handleTaskPromptChange());
        this.systemPromptTextarea.addEventListener('change', () => this.savePrompts());
        this.taskPromptTextarea.addEventListener('change', () => this.savePrompts());
    }

    async loadPrompts() {
        try {
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
        }
    }

    async loadSavedPrompts() {
        try {
            const response = await fetch(`/workflow/api/step_prompts/${this.postId}/${this.stepId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            if (data.system_prompt_id) {
                this.systemPromptSelect.value = data.system_prompt_id;
                this.systemPromptTextarea.value = data.system_prompt_text || '';
            }
            
            if (data.task_prompt_id) {
                this.taskPromptSelect.value = data.task_prompt_id;
                this.taskPromptTextarea.value = data.task_prompt_text || '';
            }
        } catch (error) {
            console.error('Error loading saved prompts:', error);
        }
    }

    async savePrompts() {
        try {
            const response = await fetch(`/workflow/api/step_prompts/${this.postId}/${this.stepId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    system_prompt_id: this.systemPromptSelect.value || null,
                    task_prompt_id: this.taskPromptSelect.value || null
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        } catch (error) {
            console.error('Error saving prompts:', error);
        }
    }

    handleSystemPromptChange() {
        const selectedOption = this.systemPromptSelect.selectedOptions[0];
        if (selectedOption) {
            this.systemPromptTextarea.value = selectedOption.dataset.text || '';
        }
        this.savePrompts();
    }

    handleTaskPromptChange() {
        const selectedOption = this.taskPromptSelect.selectedOptions[0];
        if (selectedOption) {
            this.taskPromptTextarea.value = selectedOption.dataset.text || '';
        }
        this.savePrompts();
    }
} 