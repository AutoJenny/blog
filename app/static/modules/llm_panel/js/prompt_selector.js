import { buildWorkflowApiUrl } from '/static/js/config/api.js';

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
        this.inputFieldSelect = document.getElementById('input_field_select');
        this.outputFieldSelect = document.getElementById('output_field_select');

        // Initialize
        this.loadPrompts().then(() => {
            // Only load saved prompts after dropdowns are populated
            this.loadSavedPrompts();
        });

        // Add event listeners
        if (this.systemPromptSelect) {
            this.systemPromptSelect.addEventListener('change', () => this.handleSystemPromptChange());
        }
        if (this.taskPromptSelect) {
            this.taskPromptSelect.addEventListener('change', () => this.handleTaskPromptChange());
        }
        if (this.systemPromptTextarea) {
            this.systemPromptTextarea.addEventListener('change', () => this.handlePromptChange());
        }
        if (this.taskPromptTextarea) {
            this.taskPromptTextarea.addEventListener('change', () => this.handlePromptChange());
        }
        if (this.inputFieldSelect) {
            this.inputFieldSelect.addEventListener('change', () => this.handleFieldChange());
        }
        if (this.outputFieldSelect) {
            this.outputFieldSelect.addEventListener('change', () => this.handleFieldChange());
        }
    }

    async loadPrompts() {
        try {
            // Load all prompts
            const response = await fetch(buildWorkflowApiUrl('/prompts/all'));
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const prompts = await response.json();
            
            // Separate system and task prompts
            const systemPrompts = prompts.filter(p => p.type === 'system');
            const taskPrompts = prompts.filter(p => p.type === 'task');
            
            this.populatePromptSelect(this.systemPromptSelect, systemPrompts);
            this.populatePromptSelect(this.taskPromptSelect, taskPrompts);
        } catch (error) {
            console.error('Error loading prompts:', error);
            throw error;
        }
    }

    async loadSavedPrompts() {
        try {
            const response = await fetch(buildWorkflowApiUrl(`/steps/${this.stepId}/prompts`));
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const prompts = await response.json();

            // Set values in textareas and dropdowns
            if (prompts.system_prompt_id) {
                this.systemPromptTextarea.value = prompts.system_prompt_content || '';
                this.systemPromptSelect.value = prompts.system_prompt_id;
            }
            if (prompts.task_prompt_id) {
                this.taskPromptTextarea.value = prompts.task_prompt_content || '';
                this.taskPromptSelect.value = prompts.task_prompt_id;
            }
        } catch (error) {
            console.error('Error loading saved prompts:', error);
            throw error;
        }
    }

    populatePromptSelect(select, prompts) {
        // Clear existing options
        select.innerHTML = '<option value="">Select a prompt...</option>';

        // Add new options
        prompts.forEach(prompt => {
            const option = document.createElement('option');
            option.value = prompt.id;
            option.textContent = prompt.name;
            // Store the prompt content as a data attribute for easy access
            option.dataset.content = prompt.prompt_text || '';
            select.appendChild(option);
        });
    }

    handleSystemPromptChange() {
        const selectedOption = this.systemPromptSelect.selectedOptions[0];
        if (selectedOption && selectedOption.value) {
            this.systemPromptTextarea.value = selectedOption.dataset.content || '';
            this.handlePromptChange();
        }
    }

    handleTaskPromptChange() {
        const selectedOption = this.taskPromptSelect.selectedOptions[0];
        if (selectedOption && selectedOption.value) {
            this.taskPromptTextarea.value = selectedOption.dataset.content || '';
            this.handlePromptChange();
        }
    }

    handleFieldChange() {
        this.handlePromptChange();
    }

    async handlePromptChange() {
        if (this.isLoading) return;
        this.isLoading = true;

        try {
            const response = await fetch(buildWorkflowApiUrl(`/steps/${this.stepId}/prompts`), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
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
        } finally {
            this.isLoading = false;
        }
    }
} 