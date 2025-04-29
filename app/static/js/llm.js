// Configuration
document.getElementById('config-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    try {
        const response = await fetch('/api/v1/llm/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(Object.fromEntries(formData)),
        });
        const result = await response.json();
        if (result.success) {
            // Update displayed values
            document.getElementById('current-provider').textContent = formData.get('provider_type');
            document.getElementById('current-model').textContent = formData.get('model_name');
            document.getElementById('current-api-base').textContent = formData.get('api_base');
            alert('Configuration updated successfully');
        } else {
            alert('Error updating configuration: ' + result.error);
        }
    } catch (error) {
        alert('Error updating configuration: ' + error.message);
    }
});

// Test Interface
document.getElementById('test-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const submitButton = e.target.querySelector('button[type="submit"]');
    const resultContainer = document.getElementById('test-result');
    const resultPre = resultContainer.querySelector('.result-pre');

    // Get selected model from radio buttons
    const modelRadio = document.querySelector('input[name="model"]:checked');
    const modelName = modelRadio ? modelRadio.value : null;

    if (!modelName) {
        alert('Please select a model to test with');
        return;
    }

    try {
        submitButton.disabled = true;
        submitButton.textContent = 'Testing...';

        const response = await fetch('/api/v1/llm/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: formData.get('prompt'),
                model_name: modelName
            }),
        });
        const result = await response.json();

        resultContainer.style.display = 'block';
        if (result.error) {
            resultPre.textContent = 'Error: ' + result.error;
            resultPre.style.color = 'var(--error-text)';
        } else {
            resultPre.textContent = result.result + (result.model_used ? `\n\n(Model used: ${result.model_used})` : '');
            resultPre.style.color = 'var(--dark-text-primary)';
        }
    } catch (error) {
        resultContainer.style.display = 'block';
        resultPre.textContent = 'Error: ' + error.message;
        resultPre.style.color = 'var(--error-text)';
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = 'Test LLM';
    }
});

// Model List Management
document.addEventListener('DOMContentLoaded', function () {
    function renderModelList(models, loaded, selectedModel) {
        const listDiv = document.getElementById('llm-model-list');
        listDiv.innerHTML = '';
        if (!models.length) {
            listDiv.innerHTML = '<div style="color:#fbbf24;">No models found</div>';
            return;
        }
        models.forEach(m => {
            const isLoaded = loaded.includes(m);
            const wrapper = document.createElement('label');
            wrapper.style.display = 'flex';
            wrapper.style.alignItems = 'center';
            wrapper.style.marginBottom = '0.5em';
            wrapper.style.padding = '0.5em 1em';
            wrapper.style.borderRadius = '0.5em';
            wrapper.style.cursor = 'pointer';
            wrapper.style.background = isLoaded ? '#166534' : '#fbbf24';
            wrapper.style.color = isLoaded ? '#fff' : '#23272F';
            wrapper.style.fontWeight = isLoaded ? 'bold' : 'normal';
            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = 'llm_model';
            radio.value = m;
            radio.style.marginRight = '0.75em';
            if (selectedModel === m) radio.checked = true;
            wrapper.appendChild(radio);
            wrapper.appendChild(document.createTextNode(m + (isLoaded ? ' (loaded)' : '')));
            // Preload button
            const preloadBtn = document.createElement('button');
            preloadBtn.type = 'button';
            preloadBtn.textContent = isLoaded ? 'Loaded' : 'Preload';
            preloadBtn.disabled = isLoaded;
            preloadBtn.style.marginLeft = 'auto';
            preloadBtn.style.background = isLoaded ? '#22c55e' : '#6366F1';
            preloadBtn.style.color = '#fff';
            preloadBtn.style.border = 'none';
            preloadBtn.style.borderRadius = '0.375em';
            preloadBtn.style.padding = '0.25em 0.75em';
            preloadBtn.style.fontWeight = 'bold';
            preloadBtn.style.cursor = isLoaded ? 'default' : 'pointer';
            preloadBtn.addEventListener('click', function () {
                preloadBtn.textContent = 'Loading...';
                preloadBtn.disabled = true;
                fetch('/api/v1/llm/preload', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model: m })
                })
                    .then(r => r.json())
                    .then(() => {
                        setTimeout(() => loadOllamaModels(selectedModel), 1000);
                    });
            });
            wrapper.appendChild(preloadBtn);
            listDiv.appendChild(wrapper);
        });
    }

    function loadOllamaModels(selectedModel) {
        const note = document.getElementById('llm-model-note');
        fetch('/api/v1/llm/models/ollama')
            .then(r => r.json())
            .then(data => {
                renderModelList(data.models || [], data.loaded || [], selectedModel);
                note.textContent = 'Green = loaded in memory. Amber = downloaded and ready to use.';
            })
            .catch(() => {
                renderModelList([], [], null);
                note.textContent = '';
            });
    }

    function loadProviderModels() {
        const provider = document.getElementById('llm-provider-select').value;
        if (provider === 'ollama') {
            loadOllamaModels();
        } else {
            // Placeholder for OpenAI or other providers
            const listDiv = document.getElementById('llm-model-list');
            listDiv.innerHTML = '';
            ['gpt-3.5-turbo', 'gpt-4'].forEach(m => {
                const wrapper = document.createElement('label');
                wrapper.style.display = 'block';
                wrapper.style.marginBottom = '0.5em';
                wrapper.style.padding = '0.5em 1em';
                wrapper.style.borderRadius = '0.5em';
                wrapper.style.cursor = 'pointer';
                wrapper.style.background = '#fbbf24';
                wrapper.style.color = '#23272F';
                const radio = document.createElement('input');
                radio.type = 'radio';
                radio.name = 'llm_model';
                radio.value = m;
                radio.style.marginRight = '0.75em';
                wrapper.appendChild(radio);
                wrapper.appendChild(document.createTextNode(m));
                listDiv.appendChild(wrapper);
            });
            document.getElementById('llm-model-note').textContent = 'OpenAI models are selected from the API.';
        }
    }

    document.getElementById('llm-provider-select').addEventListener('change', loadProviderModels);
    loadProviderModels();

    // When a model is selected, update the test field below
    document.getElementById('llm-model-list').addEventListener('change', function (e) {
        if (e.target && e.target.name === 'llm_model') {
            document.getElementById('current-model').textContent = e.target.value;
        }
    });
});

// Prompt Templates
document.addEventListener('DOMContentLoaded', function () {
    const promptsAccordion = document.getElementById('prompts-accordion');
    const addNewPromptBtn = document.getElementById('add-new-prompt-btn');
    const newPromptForm = document.getElementById('new-prompt-form');
    const saveNewPromptBtn = document.getElementById('save-new-prompt-btn');
    const cancelNewPromptBtn = document.getElementById('cancel-new-prompt-btn');

    function loadPrompts() {
        fetch('/api/v1/llm/prompts')
            .then(r => r.json())
            .then(templates => {
                promptsAccordion.innerHTML = '';
                templates.forEach(t => {
                    const template = document.createElement('div');
                    template.className = 'template-card mb-4';
                    template.innerHTML = `
                        <div class="template-header flex justify-between items-center p-4 bg-gray-800">
                            <h3 class="template-title text-lg font-semibold">${t.name}</h3>
                            <div class="flex gap-2">
                                <button class="edit-btn px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">Edit</button>
                                <button class="delete-btn px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700">Delete</button>
                            </div>
                        </div>
                        <div class="template-content p-4 bg-gray-900">
                            <div class="mb-4">
                                <div class="font-medium mb-1">Description:</div>
                                <p class="text-gray-300">${t.description || 'No description provided'}</p>
                            </div>
                            <div>
                                <div class="font-medium mb-1">Prompt Template:</div>
                                <pre class="bg-gray-800 p-3 rounded overflow-x-auto whitespace-pre-wrap">${t.prompt_text}</pre>
                            </div>
                        </div>
                        <div class="edit-form p-4 bg-gray-900" style="display: none;">
                            <form class="space-y-4">
                                <div class="form-group">
                                    <label class="block text-sm font-medium mb-1">Name</label>
                                    <input type="text" class="edit-name w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded" value="${t.name}">
                                </div>
                                <div class="form-group">
                                    <label class="block text-sm font-medium mb-1">Description</label>
                                    <input type="text" class="edit-description w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded" value="${t.description || ''}">
                                </div>
                                <div class="form-group">
                                    <label class="block text-sm font-medium mb-1">Prompt Template</label>
                                    <textarea class="edit-content w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded" rows="6">${t.prompt_text}</textarea>
                                </div>
                                <div class="flex gap-2 mt-4">
                                    <button type="button" class="save-edit-btn px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">Save Changes</button>
                                    <button type="button" class="cancel-edit-btn px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700">Cancel</button>
                                </div>
                            </form>
                        </div>
                    `;
                    promptsAccordion.appendChild(template);

                    const content = template.querySelector('.template-content');
                    const editForm = template.querySelector('.edit-form');
                    const editBtn = template.querySelector('.edit-btn');
                    const deleteBtn = template.querySelector('.delete-btn');
                    const saveEditBtn = template.querySelector('.save-edit-btn');
                    const cancelEditBtn = template.querySelector('.cancel-edit-btn');

                    editBtn.addEventListener('click', () => {
                        content.style.display = 'none';
                        editForm.style.display = 'block';
                    });

                    cancelEditBtn.addEventListener('click', () => {
                        content.style.display = 'block';
                        editForm.style.display = 'none';
                    });

                    deleteBtn.addEventListener('click', () => {
                        if (confirm('Are you sure you want to delete this prompt template?')) {
                            fetch(`/api/v1/llm/prompts/${t.id}`, {
                                method: 'DELETE',
                            })
                                .then(r => r.json())
                                .then(data => {
                                    if (data.success) {
                                        loadPrompts();
                                    } else {
                                        alert('Failed to delete prompt: ' + (data.error || 'Unknown error'));
                                    }
                                })
                                .catch(err => {
                                    alert('Error deleting prompt: ' + err);
                                });
                        }
                    });

                    saveEditBtn.addEventListener('click', () => {
                        const updatedPrompt = {
                            name: template.querySelector('.edit-name').value.trim(),
                            description: template.querySelector('.edit-description').value.trim(),
                            prompt_text: template.querySelector('.edit-content').value.trim()
                        };

                        if (!updatedPrompt.name || !updatedPrompt.prompt_text) {
                            alert('Name and prompt template are required');
                            return;
                        }

                        fetch(`/api/v1/llm/prompts/${t.id}`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(updatedPrompt)
                        })
                            .then(r => r.json())
                            .then(data => {
                                if (data.success) {
                                    content.style.display = 'block';
                                    editForm.style.display = 'none';
                                    loadPrompts();
                                } else {
                                    alert('Failed to update prompt: ' + (data.error || 'Unknown error'));
                                }
                            })
                            .catch(err => {
                                alert('Error updating prompt: ' + err);
                            });
                    });
                });
            });
    }

    // Load prompts on page load
    loadPrompts();

    // Add New Prompt handlers
    addNewPromptBtn.addEventListener('click', () => {
        newPromptForm.style.display = 'block';
        addNewPromptBtn.style.display = 'none';
    });

    cancelNewPromptBtn.addEventListener('click', () => {
        newPromptForm.style.display = 'none';
        addNewPromptBtn.style.display = 'block';
        // Clear form
        document.getElementById('new-prompt-name').value = '';
        document.getElementById('new-prompt-description').value = '';
        document.getElementById('new-prompt-content').value = '';
    });

    saveNewPromptBtn.addEventListener('click', () => {
        const name = document.getElementById('new-prompt-name').value.trim();
        const description = document.getElementById('new-prompt-description').value.trim();
        const content = document.getElementById('new-prompt-content').value.trim();

        if (!name || !content) {
            alert('Name and content are required');
            return;
        }

        fetch('/api/v1/llm/prompts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                description,
                prompt_text: content
            })
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    loadPrompts();
                    newPromptForm.style.display = 'none';
                    addNewPromptBtn.style.display = 'block';
                    // Clear form
                    document.getElementById('new-prompt-name').value = '';
                    document.getElementById('new-prompt-description').value = '';
                    document.getElementById('new-prompt-content').value = '';
                } else {
                    alert('Failed to save prompt: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(err => {
                alert('Error saving prompt: ' + err);
            });
    });
}); 