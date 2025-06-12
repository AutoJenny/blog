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