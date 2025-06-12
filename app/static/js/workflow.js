// Workflow functionality
document.addEventListener('DOMContentLoaded', function() {
    // Run LLM button
    var runLlmBtn = document.getElementById('run-llm');
    if (runLlmBtn) {
        runLlmBtn.addEventListener('click', function() {
            var data = {
                post_id: parseInt(window.postId),
                step_name: window.currentStep,
                substage_name: window.currentSubstage,
                stage_name: window.currentStage
            };
            console.log('Sending data:', data);
            
            fetch('/workflow/api/run_llm/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                console.log('LLM processing result:', data);
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    }

    // Sections functionality
    var addSectionBtn = document.getElementById('add-section');
    var sectionsContainer = document.getElementById('sections-container');

    if (addSectionBtn && sectionsContainer) {
        // Load existing sections
        loadSections();

        // Add section button
        addSectionBtn.addEventListener('click', function() {
            var sectionId = 'section-' + Date.now();
            var sectionHtml = `
                <div class="section-item border border-dark-border rounded-lg p-4" data-section-id="${sectionId}">
                    <div class="flex justify-between items-center mb-4">
                        <input type="text" class="section-title bg-dark-bg border border-dark-border rounded p-2 text-dark-text w-full" placeholder="Section Title">
                        <div class="flex gap-2">
                            <button class="run-section-llm bg-dark-accent text-white px-4 py-2 rounded-lg hover:bg-dark-hover transition">
                                Run LLM
                            </button>
                            <button class="delete-section text-red-500 hover:text-red-700">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                                </svg>
                            </button>
                        </div>
                    </div>
                    <textarea class="section-content bg-dark-bg border border-dark-border rounded p-2 text-dark-text w-full h-32" placeholder="Section Content"></textarea>
                </div>
            `;
            sectionsContainer.insertAdjacentHTML('beforeend', sectionHtml);
            saveSections();
        });

        // Delete section
        sectionsContainer.addEventListener('click', function(e) {
            if (e.target.closest('.delete-section')) {
                var sectionItem = e.target.closest('.section-item');
                sectionItem.remove();
                saveSections();
            }
        });

        // Run LLM for section
        sectionsContainer.addEventListener('click', function(e) {
            if (e.target.closest('.run-section-llm')) {
                var sectionItem = e.target.closest('.section-item');
                var sectionId = sectionItem.dataset.sectionId;
                var sectionTitle = sectionItem.querySelector('.section-title').value;
                var sectionContent = sectionItem.querySelector('.section-content').value;

                var data = {
                    post_id: parseInt(window.postId),
                    step_name: window.currentStep,
                    substage_name: window.currentSubstage,
                    stage_name: window.currentStage,
                    sections: [sectionId]
                };

                fetch('/workflow/api/run_llm/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok: ' + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('LLM processing result:', data);
                    if (data.success && data.results && data.results.length > 0) {
                        var result = data.results[0];
                        if (result.status === 'success') {
                            sectionItem.querySelector('.section-content').value = result.response;
                            saveSections();
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            }
        });

        // Save sections on content change
        sectionsContainer.addEventListener('input', function(e) {
            if (e.target.matches('.section-title, .section-content')) {
                saveSections();
            }
        });
    }

    // Load sections from server
    function loadSections() {
        var data = {
            post_id: parseInt(window.postId),
            step_name: window.currentStep,
            substage_name: window.currentSubstage,
            stage_name: window.currentStage
        };

        fetch('/workflow/api/sections/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            if (data.sections) {
                sectionsContainer.innerHTML = '';
                data.sections.forEach(function(section) {
                    var sectionHtml = `
                        <div class="section-item border border-dark-border rounded-lg p-4" data-section-id="${section.id}">
                            <div class="flex justify-between items-center mb-4">
                                <input type="text" class="section-title bg-dark-bg border border-dark-border rounded p-2 text-dark-text w-full" value="${section.title || ''}" placeholder="Section Title">
                                <div class="flex gap-2">
                                    <button class="run-section-llm bg-dark-accent text-white px-4 py-2 rounded-lg hover:bg-dark-hover transition">
                                        Run LLM
                                    </button>
                                    <button class="delete-section text-red-500 hover:text-red-700">
                                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                                        </svg>
                                    </button>
                                </div>
                            </div>
                            <textarea class="section-content bg-dark-bg border border-dark-border rounded p-2 text-dark-text w-full h-32" placeholder="Section Content">${section.content || ''}</textarea>
                        </div>
                    `;
                    sectionsContainer.insertAdjacentHTML('beforeend', sectionHtml);
                });
            }
        })
        .catch(error => {
            console.error('Error loading sections:', error);
        });
    }

    // Save sections to server
    function saveSections() {
        var sections = [];
        document.querySelectorAll('.section-item').forEach(function(item) {
            sections.push({
                id: item.dataset.sectionId,
                title: item.querySelector('.section-title').value,
                content: item.querySelector('.section-content').value
            });
        });

        var data = {
            post_id: parseInt(window.postId),
            step_name: window.currentStep,
            substage_name: window.currentSubstage,
            stage_name: window.currentStage,
            sections: sections
        };

        fetch('/workflow/api/sections/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            console.log('Sections saved:', data);
        })
        .catch(error => {
            console.error('Error saving sections:', error);
        });
    }

    // Prompt editing
    var editPromptBtn = document.getElementById('edit-prompt');
    var savePromptBtn = document.getElementById('save-prompt');
    var promptDisplay = document.getElementById('prompt-display');
    var promptEditDiv = document.getElementById('prompt-edit');
    var promptEdit = promptEditDiv ? promptEditDiv.querySelector('textarea') : null;

    if (editPromptBtn && savePromptBtn && promptDisplay && promptEditDiv && promptEdit) {
        editPromptBtn.onclick = function() {
            promptDisplay.classList.add('hidden');
            promptEditDiv.classList.remove('hidden');
            editPromptBtn.classList.add('hidden');
            savePromptBtn.classList.remove('hidden');
            promptEdit.value = promptDisplay.textContent;
            // Focus the textarea and move cursor to end
            promptEdit.focus();
            promptEdit.setSelectionRange(promptEdit.value.length, promptEdit.value.length);
        };

        savePromptBtn.onclick = function() {
            // Validate required data
            if (!window.postId || !window.currentStep || !window.currentSubstage || !window.currentStage) {
                console.error('Missing required window variables:', {
                    postId: window.postId,
                    currentStep: window.currentStep,
                    currentSubstage: window.currentSubstage,
                    currentStage: window.currentStage
                });
                return;
            }

            var newPrompt = promptEdit.value;
            console.log('Original prompt:', window.originalPrompt);
            console.log('New prompt:', newPrompt);
            console.log('Window variables:', {
                postId: window.postId,
                currentStep: window.currentStep,
                currentSubstage: window.currentSubstage,
                currentStage: window.currentStage
            });
            
            // Update the display
            promptDisplay.textContent = newPrompt;
            promptDisplay.classList.remove('hidden');
            promptEditDiv.classList.add('hidden');
            editPromptBtn.classList.remove('hidden');
            savePromptBtn.classList.add('hidden');

            // Save to the server
            var data = {
                post_id: parseInt(window.postId),
                step_name: window.currentStep,
                substage_name: window.currentSubstage,
                stage_name: window.currentStage,
                prompt: newPrompt
            };
            console.log('Sending prompt data:', data);
            console.log('Request headers:', {
                'Content-Type': 'application/json'
            });

            fetch('/workflow/api/update_prompt/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => {
                console.log('Response status:', response.status);
                console.log('Response headers:', Object.fromEntries(response.headers.entries()));
                return response.json().then(data => {
                    if (!response.ok) {
                        throw new Error(data.error || 'Network response was not ok: ' + response.status);
                    }
                    return data;
                });
            })
            .then(data => {
                console.log('Server response:', data);
                if (data.success) {
                    console.log('Prompt updated successfully');
                    // Update the original prompt in case we need to revert
                    window.originalPrompt = newPrompt;
                } else {
                    console.error('Failed to update prompt:', data.error);
                    promptDisplay.textContent = window.originalPrompt;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                promptDisplay.textContent = window.originalPrompt;
            });
        };
    }
}); 