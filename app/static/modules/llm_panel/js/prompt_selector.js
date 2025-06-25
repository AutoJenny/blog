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
            const response = await fetch('/api/v1/llm/prompts');
            const prompts = await response.json();

            // Filter prompts by type and populate dropdowns
            const systemPrompts = prompts.filter(p => p.prompt_json?.some(part => part.type === 'system'));
            const taskPrompts = prompts.filter(p => p.prompt_json?.some(part => part.type === 'user' || part.type === 'task'));

            // Populate system prompts dropdown
            this.systemPromptSelect.innerHTML = '<option value="">Select system prompt...</option>' +
                systemPrompts.map(p => `<option value="${p.id}">${p.name}</option>`).join('');

            // Populate task prompts dropdown
            this.taskPromptSelect.innerHTML = '<option value="">Select task prompt...</option>' +
                taskPrompts.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
        } catch (error) {
            console.error('Error loading prompts:', error);
        }
    }

    attachEventListeners() {
        this.systemPromptSelect.addEventListener('change', async () => {
            const promptId = this.systemPromptSelect.value;
            if (promptId) {
                try {
                    const response = await fetch(`/api/v1/llm/prompts/${promptId}`);
                    const prompt = await response.json();
                    const systemPart = prompt.prompt_json.find(part => part.type === 'system');
                    if (systemPart) {
                        this.systemPromptText.value = systemPart.content;
                    }
                } catch (error) {
                    console.error('Error loading system prompt:', error);
                }
            }
        });

        this.taskPromptSelect.addEventListener('change', async () => {
            const promptId = this.taskPromptSelect.value;
            if (promptId) {
                try {
                    const response = await fetch(`/api/v1/llm/prompts/${promptId}`);
                    const prompt = await response.json();
                    const taskPart = prompt.prompt_json.find(part => part.type === 'user' || part.type === 'task');
                    if (taskPart) {
                        this.taskPromptText.value = taskPart.content;
                    }
                } catch (error) {
                    console.error('Error loading task prompt:', error);
                }
            }
        });
    }
} 