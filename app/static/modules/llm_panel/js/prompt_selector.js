export class PromptSelector {
    constructor() {
        this.systemPromptSelect = document.getElementById('system_prompt_select');
        this.taskPromptSelect = document.getElementById('task_prompt_select');
        this.systemPromptText = document.getElementById('system_prompt');
        this.taskPromptText = document.getElementById('task_prompt');

        if (this.systemPromptSelect && this.taskPromptSelect) {
            this.loadPrompts();
            this.attachEventListeners();
        }
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

    attachEventListeners() {
        // Handle system prompt selection
        this.systemPromptSelect.addEventListener('change', () => {
            const selectedOption = this.systemPromptSelect.selectedOptions[0];
            this.systemPromptText.value = selectedOption?.dataset?.text || '';
        });

        // Handle task prompt selection
        this.taskPromptSelect.addEventListener('change', () => {
            const selectedOption = this.taskPromptSelect.selectedOptions[0];
            this.taskPromptText.value = selectedOption?.dataset?.text || '';
        });
    }
} 