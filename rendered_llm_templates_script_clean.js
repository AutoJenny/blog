    // Initialize variables
    let draggedField = null;
    const workflow_fields = JSON.parse(document.getElementById('workflow-fields-json').textContent);

    // Modal management functions
    function showNewTemplateModal() {
        const modal = document.getElementById('templateModal');
        const form = document.getElementById('templateForm');
        const modalTitle = document.getElementById('modalTitle');

        modalTitle.textContent = 'New Template';
        form.reset();
        document.getElementById('templateId').value = '';

        // Clear the selected fields area
        const selectedFields = document.getElementById('selectedFields');
        while (selectedFields.firstChild) {
            if (!selectedFields.firstChild.classList.contains('placeholder')) {
                selectedFields.removeChild(selectedFields.firstChild);
            }
        }

        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function hideTemplateModal() {
        const modal = document.getElementById('templateModal');
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }

    async function editTemplate(id) {
        try {
            const response = await fetch(`/api/v1/llm/prompts/${id}`);
            if (!response.ok) throw new Error('Failed to fetch template');

            const template = await response.json();

            document.getElementById('modalTitle').textContent = 'Edit Template';
            document.getElementById('templateId').value = template.id;
            document.getElementById('templateName').value = template.name;
            document.getElementById('templateDescription').value = template.description || '';
            document.getElementById('templateText').value = template.prompt_text;

            // Show the modal
            document.getElementById('templateModal').classList.add('active');
            document.body.style.overflow = 'hidden';
        } catch (error) {
            console.error('Error fetching template:', error);
            alert('Failed to load template');
        }
    }

    async function deleteTemplate(id) {
        if (!confirm('Are you sure you want to delete this template?')) return;

        try {
            const response = await fetch(`/api/v1/llm/prompts/${id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                window.location.reload();
            } else {
                throw new Error('Failed to delete template');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error deleting template');
        }
    }

    function initFieldSelector() {
        const stageSelect = document.getElementById('stageSelect');
        const fieldSelect = document.getElementById('fieldSelect');
        const selectedFields = document.getElementById('selectedFields');
        const placeholder = selectedFields.querySelector('.placeholder');

        // Update fields dropdown when stage changes
        stageSelect.addEventListener('change', () => {
            const stage = stageSelect.value;
            fieldSelect.innerHTML = '<option value="">Select a Field...</option>';
            fieldSelect.disabled = !stage;

            if (stage && workflow_fields[stage]) {
                workflow_fields[stage].forEach(field => {
                    const option = document.createElement('option');
                    option.value = field;
                    option.textContent = field.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                    fieldSelect.appendChild(option);
                });
            }
        });

        // Create draggable field when field is selected
        fieldSelect.addEventListener('change', () => {
            const field = fieldSelect.value;
            if (!field) return;

            // Create the draggable field tag
            const fieldTag = document.createElement('div');
            fieldTag.className = 'field-tag';
            fieldTag.draggable = true;
            fieldTag.dataset.field = field;
            fieldTag.innerHTML = '<i class="fas fa-grip-lines"></i> ' +
                field.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

            // Add drag event listeners
            fieldTag.addEventListener('dragstart', handleDragStart);
            fieldTag.addEventListener('dragend', handleDragEnd);

            // Add to selected fields area
            placeholder.style.display = 'none';
            selectedFields.appendChild(fieldTag);

            // Reset field select
            fieldSelect.value = '';
        });
    }

    function handleDragStart(e) {
        draggedField = e.target.dataset.field;
        e.target.classList.add('dragging');
    }

    function handleDragEnd(e) {
        e.target.classList.remove('dragging');
        draggedField = null;
    }

    function setupTemplateEditor() {
        const editor = document.querySelector('.template-editor');
        const textarea = document.getElementById('templateText');

        editor.addEventListener('dragover', (e) => {
            e.preventDefault();
            editor.classList.add('drag-over');
        });

        editor.addEventListener('dragleave', () => {
            editor.classList.remove('drag-over');
        });

        editor.addEventListener('drop', function (e) {
            e.preventDefault();
            editor.classList.remove('drag-over');

            if (draggedField) {
                const cursorPos = textarea.selectionStart || textarea.value.length;
                const currentValue = textarea.value;
                const formattedField = draggedField.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

                // Create the field text by concatenating parts separately
                const openBrace = ';
                const closeBrace = ';
                const fieldText = openBrace + formattedField + closeBrace;

                // Insert the field text at the cursor position
                textarea.value = currentValue.slice(0, cursorPos) + fieldText + currentValue.slice(cursorPos);
                textarea.focus();
                textarea.setSelectionRange(cursorPos + fieldText.length, cursorPos + fieldText.length);
            }
        });

        // Hide placeholder when typing
        textarea.addEventListener('input', () => {
            const placeholder = editor.querySelector('.placeholder');
            placeholder.style.display = textarea.value ? 'none' : 'block';
        });
    }

    // Initialize everything when the page loads
    document.addEventListener('DOMContentLoaded', () => {
        console.log('Initializing template page...');

        // Initialize field selector and template editor
        initFieldSelector();
        setupTemplateEditor();

        // Add event listeners for buttons
        document.getElementById('newTemplateBtn').addEventListener('click', showNewTemplateModal);
        document.getElementById('modalCloseBtn').addEventListener('click', hideTemplateModal);
        document.getElementById('cancelBtn').addEventListener('click', hideTemplateModal);

        // Add event listeners for edit and delete buttons
        document.querySelectorAll('.edit-template-btn').forEach(btn => {
            btn.addEventListener('click', () => editTemplate(btn.dataset.id));
        });

        document.querySelectorAll('.delete-template-btn').forEach(btn => {
            btn.addEventListener('click', () => deleteTemplate(btn.dataset.id));
        });

        // Add form submission handler
        document.getElementById('templateForm').addEventListener('submit', async function (e) {
            e.preventDefault();
            const templateId = document.getElementById('templateId').value;
            const method = templateId ? 'PUT' : 'POST';
            const url = templateId ? `/api/v1/llm/prompts/${templateId}` : '/api/v1/llm/prompts';

            try {
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        name: document.getElementById('templateName').value,
                        description: document.getElementById('templateDescription').value,
                        prompt_text: document.getElementById('templateText').value
                    })
                });

                if (response.ok) {
                    window.location.reload();
                } else {
                    throw new Error('Failed to save template');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error saving template');
            }
        });

        // Close modal when clicking outside
        document.getElementById('templateModal').addEventListener('click', function (e) {
            if (e.target === this) {
                hideTemplateModal();
            }
        });
    });
        document.addEventListener('DOMContentLoaded', function () {
            var newPostBtn = document.getElementById('newPostBtn');
            if (newPostBtn) {
                newPostBtn.addEventListener('click', async () => {
                    const basicIdea = prompt('Enter your basic idea for the post:');
                    if (!basicIdea) return;
                    try {
                        const response = await fetch("/blog/new", {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ basic_idea: basicIdea })
                        });
                        const data = await response.json();
                        if (response.ok) {
                            window.location.href = `/blog/${data.id}/develop`;
                        } else {
                            alert(data.error || 'Failed to create post');
                        }
                    } catch (error) {
                        console.error('Error:', error);
                        alert('Failed to create post');
                    }
                });
            }
        });
