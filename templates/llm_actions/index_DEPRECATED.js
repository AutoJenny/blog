<script>
        let actions = [];
        let selectedAction = null;
        let systemPrompts = [];
        let selectedSystemPrompt = null;
        
        // Detect if running in integrated context and set base URL
        const isIntegrated = window.location.hostname === 'localhost' && window.location.port === '5001';
        const baseUrl = isIntegrated ? '' : '';
        console.log('Running in integrated context:', isIntegrated, 'Base URL:', baseUrl);
        
        // Get context from injected workflowContext or URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const context = window.workflowContext || {
            stage: urlParams.get('stage') || 'planning',
            substage: urlParams.get('substage') || 'idea',
            step: urlParams.get('step') || 'initial_concept',
            post_id: urlParams.get('post_id') || '1',
            step_id: urlParams.get('step_id') || ''
        };
        console.log('Context:', context);

        // Function to initialize the LLM actions
        async function initializeLLMActions() {
            console.log('Initializing LLM actions...');
            
            // Get workflow context from URL parameters or injected data
            const urlParams = new URLSearchParams(window.location.search);
            const stage = urlParams.get('stage') || context.stage || 'planning';
            const substage = urlParams.get('substage') || context.substage || 'idea';
            const step = urlParams.get('step') || context.step || 'initial_concept';
            const postId = urlParams.get('post_id') || context.post_id;
            const stepId = urlParams.get('step_id') || context.step_id;
            
            // Store workflow context globally
            window.workflowContext = {
                stage: stage,
                substage: substage,
                step: step,
                postId: postId,
                step_id: stepId
            };
            
            // Handle special case for section_illustrations step
            if (step === 'section_illustrations') {
                console.log('[LLM-ACTIONS] Detected section_illustrations step, showing image generation interface');
                showImageGenerationInterface(postId);
            } else {
                // Show LLM Message Management section for other steps
                const messageManagementSection = document.getElementById('llm-message-management-section');
                if (messageManagementSection) {
                    messageManagementSection.style.display = 'block';
                }
            }
            
            // Initialize simple input field system
            console.log('[LLM-ACTIONS] Initializing simple input field system...');
            await initializeSimpleInputFields(postId, stage, substage);
            
            // Initialize simple output field system (skip for section_illustrations)
            if (step !== 'section_illustrations') {
                console.log('[LLM-ACTIONS] Initializing simple output field system...');
                await initializeSimpleOutputFields(postId, stage, substage);
            }
            
            // Initialize other components
            loadConfig();
            loadActions();
            loadSystemPrompts();
            loadSavedData();
            
            // Load step settings from database (after other components are loaded)
            await loadStepSettings();
            
            // Add event listener for task prompt dropdown change
            const actionSelect = document.getElementById('action-select');
            if (actionSelect) {
                actionSelect.addEventListener('change', function() {
                    console.log('Task prompt dropdown changed, calling loadActionInfo');
                    
                    // Save selection to localStorage for persistence
                    const selectedId = this.value;
                    if (selectedId) {
                        const storageKey = `selected_prompt_${context.stage}_${context.substage}_${context.step}`;
                        localStorage.setItem(storageKey, selectedId);
                        console.log('Saved task prompt selection to localStorage:', selectedId);
                    }
                    
                    // Persist to database
                    persistStepSettings();
                    
                    loadActionInfo();
                });
            }
            
            // Add event listener for system prompt dropdown change
            const systemPromptSelect = document.getElementById('system-prompt-select');
            if (systemPromptSelect) {
                systemPromptSelect.addEventListener('change', function() {
                    console.log('System prompt dropdown changed, calling loadSystemPromptInfo');
                    
                    // Save selection to localStorage for persistence
                    const selectedId = this.value;
                    if (selectedId) {
                        const storageKey = `selected_system_prompt_${context.stage}_${context.substage}_${context.step}`;
                        localStorage.setItem(storageKey, selectedId);
                        console.log('Saved system prompt selection to localStorage:', selectedId);
                    }
                    
                    // Persist to database
                    persistStepSettings();
                    
                    loadSystemPromptInfo();
                });
            }
        }

        // Function to show image generation interface
        function showImageGenerationInterface(postId) {
            console.log('[ImageGeneration] Showing image generation interface for post:', postId);
            
            // Hide LLM Message Management section for section_illustrations
            const messageManagementSection = document.getElementById('llm-message-management-section');
            if (messageManagementSection) {
                messageManagementSection.style.display = 'none';
            }
            
            // Hide standard output section
            const standardOutputSection = document.getElementById('standard-output-section');
            if (standardOutputSection) {
                standardOutputSection.style.display = 'none';
            }
            
            // Show image output section
            const imageOutputSection = document.getElementById('image-output-section');
            if (imageOutputSection) {
                imageOutputSection.style.display = 'block';
            }
            
            // Update post ID in the display
            const imagePostIdSpan = document.getElementById('image-post-id');
            if (imagePostIdSpan) {
                imagePostIdSpan.textContent = postId;
            }
            
            console.log('[ImageGeneration] Image generation interface activated');
        }
        
        // Function to run simple detection only
        async function runImageGeneration() {
            console.log('[Processing] Starting section processing...');
            
            // Show loading state
            const runButton = document.querySelector('.btn-run-llm');
            const originalButtonText = runButton ? runButton.innerHTML : 'Run LLM';
                            if (runButton) {
                    runButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                    runButton.disabled = true;
                }
            
            try {
                // Get selected section IDs
                const selectedSectionIds = await getSelectedSectionIds();
                console.log('[Processing] Received section IDs:', selectedSectionIds);
                
                if (selectedSectionIds.length === 0) {
                    alert('Please select at least one section in the green panel.');
                    return;
                }
                
                console.log('[Processing] Processing', selectedSectionIds.length, 'sections');
                
                // Call the blog-core execute-step endpoint with ALL selected sections
                const postId = urlParams.get('post_id') || context.post_id;
                const stepId = urlParams.get('step_id') || context.step_id;
                const taskPrompt = 'Section processing - gathering prompting data and sending to LLM';
                
                const response = await fetch('http://localhost:5000/api/workflow/execute-step', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        post_id: postId,
                        step_id: stepId,
                        section_ids: selectedSectionIds, // ALL selected sections
                        task_prompt: taskPrompt
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                console.log('[Processing] Result:', result);
                
                // Show success message
                alert(`Processing complete! Processed ${selectedSectionIds.length} sections. Check the log file for details.`);
                
            } catch (error) {
                console.error('[Processing] Error:', error);
                alert('Error during processing. Check console for details.');
            } finally {
                // Restore button state
                if (runButton) {
                    runButton.innerHTML = originalButtonText;
                    runButton.disabled = false;
                }
            }
        }
        
        // Function to generate image for a specific section
        async function generateImageForSection(sectionId, taskPrompt) {
            console.log(`[ImageGeneration] Generating image for section ${sectionId}`);
            
            const postId = urlParams.get('post_id') || context.post_id;
            const stepId = urlParams.get('step_id') || context.step_id;
            
            try {
                // Call the blog-core execute-step endpoint
                const response = await fetch('http://localhost:5000/api/workflow/execute-step', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        post_id: postId,
                        step_id: stepId,
                        section_ids: [sectionId],
                        task_prompt: taskPrompt
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                console.log(`[ImageGeneration] Result for section ${sectionId}:`, result);
                
                if (result.status === 'success') {
                    console.log(`[ImageGeneration] Successfully generated image for section ${sectionId}`);
                } else {
                    throw new Error(result.message || 'Unknown error');
                }
                
            } catch (error) {
                console.error(`[ImageGeneration] Error generating image for section ${sectionId}:`, error);
                throw error;
            }
        }
        
        // Load configuration on page load (for direct access)
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded, loading actions...');
            initializeLLMActions().catch(console.error);
        });

        // Also initialize immediately if DOM is already loaded (for integrated context)
        if (document.readyState === 'loading') {
            // DOM is still loading, wait for DOMContentLoaded
        } else {
            // DOM is already loaded, initialize immediately
            console.log('DOM already loaded, initializing immediately...');
            initializeLLMActions().catch(console.error);
        }

        // For integrated context (when loaded via fetch), initialize when script loads
        if (typeof window.workflowContext !== 'undefined') {
            console.log('Detected integrated context, initializing...');
            // Wait a bit for all scripts to load
            setTimeout(() => {
                initializeLLMActions().catch(console.error);
            }, 50);
        }
        
        // Debug function to clear localStorage for testing
        function clearPromptSelections() {
            const keys = Object.keys(localStorage);
            keys.forEach(key => {
                if (key.startsWith('selected_prompt_')) {
                    localStorage.removeItem(key);
                    console.log('Cleared:', key);
                }
            });
            console.log('All prompt selections cleared');
        }
        
        // Debug function to show current localStorage state
        function showPromptSelections() {
            const keys = Object.keys(localStorage);
            const promptKeys = keys.filter(key => key.startsWith('selected_prompt_'));
            console.log('Current prompt selections in localStorage:');
            promptKeys.forEach(key => {
                console.log(`${key}: ${localStorage.getItem(key)}`);
            });
        }
        
        // Make them available globally for debugging
        window.clearPromptSelections = clearPromptSelections;
        window.showPromptSelections = showPromptSelections;
        
        // Function to clear saved input field selection
        function clearInputFieldSelection() {
            const keys = Object.keys(localStorage).filter(key => key.startsWith('simpleInputField_'));
            keys.forEach(key => {
                localStorage.removeItem(key);
                console.log(`Cleared: ${key}`);
            });
            console.log('All input field selections cleared');
        }
        
        // Function to show saved input field selections
        function showInputFieldSelections() {
            const keys = Object.keys(localStorage).filter(key => key.startsWith('simpleInputField_'));
            console.log('Saved input field selections:');
            keys.forEach(key => {
                console.log(`${key}: ${localStorage.getItem(key)}`);
            });
        }
        
        // Make them available globally for debugging
        window.clearInputFieldSelection = clearInputFieldSelection;
        window.showInputFieldSelections = showInputFieldSelections;

        // Simple Input Field System
        async function initializeSimpleInputFields(postId, stage, substage) {
            console.log('[SimpleInput] Initializing for post:', postId, 'stage:', stage, 'substage:', substage);
            
            try {
                // Load available fields
                const fieldsResponse = await fetch(`/api/available-fields/${stage}?substage=${substage}`);
                if (!fieldsResponse.ok) {
                    throw new Error(`HTTP error! status: ${fieldsResponse.status}`);
                }
                const fieldsData = await fieldsResponse.json();
                
                // Populate field selector
                const fieldSelect = document.getElementById('input-field-select');
                fieldSelect.innerHTML = '<option value="">Select a field...</option>';
                
                fieldsData.fields.forEach(field => {
                    const option = document.createElement('option');
                    option.value = field.field_name;
                    option.textContent = field.display_name;
                    fieldSelect.appendChild(option);
                });
                
                // Restore saved selection
                const storageKey = `simpleInputField_${stage}_${substage}`;
                const savedField = localStorage.getItem(storageKey);
                if (savedField) {
                    fieldSelect.value = savedField;
                    console.log('[SimpleInput] Restored saved field selection:', savedField);
                    
                    // Load content for the saved field
                    try {
                        const contentResponse = await fetch(`/api/workflow/posts/${postId}/development`);
                        if (contentResponse.ok) {
                            const contentData = await contentResponse.json();
                            const fieldContent = contentData[savedField] || '';
                            document.getElementById('input-content').value = fieldContent;
                            console.log('[SimpleInput] Loaded content for restored field:', savedField);
                            
                            // Trigger sync with message management system
                            if (window.messageManagementSystem) {
                                console.log('[SimpleInput] Calling sync after loading content for restored field');
                                // Add a small delay to ensure MessageManagementSystem is fully initialized
                                setTimeout(() => {
                                    window.messageManagementSystem.syncInputFieldsContent();
                                }, 100);
                            } else {
                                console.log('[SimpleInput] MessageManagementSystem not available for sync');
                            }
                        }
                    } catch (error) {
                        console.error('[SimpleInput] Error loading content for restored field:', error);
                    }
                }
                
                // Add change event listener
                fieldSelect.addEventListener('change', async function() {
                    const selectedField = this.value;
                    
                    // Save selection to localStorage
                    if (selectedField) {
                        localStorage.setItem(storageKey, selectedField);
                        console.log('[SimpleInput] Saved field selection:', selectedField);
                    } else {
                        localStorage.removeItem(storageKey);
                        console.log('[SimpleInput] Cleared field selection');
                    }
                    
                    if (!selectedField) {
                        document.getElementById('input-content').value = '';
                        return;
                    }
                    
                    console.log('[SimpleInput] Field selected:', selectedField);
                    
                    try {
                        // Load field content
                        const contentResponse = await fetch(`/api/workflow/posts/${postId}/development`);
                        if (contentResponse.ok) {
                            const contentData = await contentResponse.json();
                            const fieldContent = contentData[selectedField] || '';
                            document.getElementById('input-content').value = fieldContent;
                            console.log('[SimpleInput] Loaded field content:', selectedField);
                            
                            // Trigger sync with message management system
                            if (window.messageManagementSystem) {
                                console.log('[SimpleInput] Calling sync after loading content for new field selection');
                                // Add a small delay to ensure MessageManagementSystem is fully initialized
                                setTimeout(() => {
                                    window.messageManagementSystem.syncInputFieldsContent();
                                }, 100);
                            } else {
                                console.log('[SimpleInput] MessageManagementSystem not available for sync');
                            }
                        }
                    } catch (error) {
                        console.error('[SimpleInput] Error loading field content:', error);
                    }
                });
                
                console.log('[SimpleInput] Initialization complete');
                
            } catch (error) {
                console.error('[SimpleInput] Error during initialization:', error);
                // Show error in field selector
                const fieldSelect = document.getElementById('input-field-select');
                fieldSelect.innerHTML = '<option value="">Error loading fields</option>';
            }
        }

        // Simple Output Field System
        async function initializeSimpleOutputFields(postId, stage, substage) {
            console.log('[SimpleOutput] Initializing for post:', postId, 'stage:', stage, 'substage:', substage);
            
            try {
                // Load available fields - use the same API as inputs
                const fieldsResponse = await fetch(`/api/available-fields/${stage}?substage=${substage}`);
                if (!fieldsResponse.ok) {
                    throw new Error(`HTTP error! status: ${fieldsResponse.status}`);
                }
                const fieldsData = await fieldsResponse.json();
                
                // Populate field selector
                const fieldSelect = document.getElementById('output-field-select');
                fieldSelect.innerHTML = '<option value="">Select a field...</option>';
                
                fieldsData.fields.forEach(field => {
                    const option = document.createElement('option');
                    option.value = field.field_name;
                    option.textContent = field.display_name;
                    fieldSelect.appendChild(option);
                });
                
                // Restore saved selection - check both stage-specific and post-specific storage
                const stageStorageKey = `simpleOutputField_${stage}_${substage}`;
                const postStorageKey = `outputField_post_${postId}`;
                const savedField = localStorage.getItem(stageStorageKey) || localStorage.getItem(postStorageKey);
                
                if (savedField) {
                    fieldSelect.value = savedField;
                    console.log('[SimpleOutput] Restored saved field selection:', savedField);
                    
                    // Load content for the saved field
                    try {
                        // Determine which endpoint to use based on stage/substage and field
                        let endpoint = `/api/workflow/posts/${postId}/development`;
                        
                        // Check if this is a post_info stage field that should come from post table
                        if (stage === 'writing' && substage === 'post_info') {
                            const postFields = ['title', 'subtitle', 'title_choices', 'summary'];
                            if (postFields.includes(savedField)) {
                                endpoint = `/api/workflow/posts/${postId}/post`;
                                console.log('[SimpleOutput] Using post table endpoint for restored field:', savedField);
                            }
                        }
                        
                        const contentResponse = await fetch(endpoint);
                        if (contentResponse.ok) {
                            const contentData = await contentResponse.json();
                            const fieldContent = contentData[savedField] || '';
                            document.getElementById('output-content').value = fieldContent;
                            console.log('[SimpleOutput] Loaded content for restored field:', savedField);
                        }
                    } catch (error) {
                        console.error('[SimpleOutput] Error loading content for restored field:', error);
                    }
                }
                
                // Add change event listener
                fieldSelect.addEventListener('change', async function() {
                    const selectedField = this.value;
                    
                    // Save selection to localStorage
                    if (selectedField) {
                        localStorage.setItem(stageStorageKey, selectedField);
                        console.log('[SimpleOutput] Saved field selection:', selectedField);
                        
                        // Also save the last used field for this post
                        const postStorageKey = `outputField_post_${postId}`;
                        localStorage.setItem(postStorageKey, selectedField);
                        console.log('[SimpleOutput] Saved post field selection:', selectedField);
                    } else {
                        localStorage.removeItem(stageStorageKey);
                        console.log('[SimpleOutput] Cleared field selection');
                    }
                    
                    if (!selectedField) {
                        document.getElementById('output-content').value = '';
                        return;
                    }
                    
                    console.log('[SimpleOutput] Field selected:', selectedField);
                    
                    try {
                        // Determine which endpoint to use based on stage/substage and field
                        let endpoint = `/api/workflow/posts/${postId}/development`;
                        
                        // Check if this is a post_info stage field that should come from post table
                        const stage = context.stage || '';
                        const substage = context.substage || '';
                        
                        if (stage === 'writing' && substage === 'post_info') {
                            const postFields = ['title', 'subtitle', 'title_choices', 'summary'];
                            if (postFields.includes(selectedField)) {
                                endpoint = `/api/workflow/posts/${postId}/post`;
                                console.log('[SimpleOutput] Using post table endpoint for field:', selectedField);
                            }
                        }
                        
                        // Load field content from the appropriate endpoint
                        const contentResponse = await fetch(endpoint);
                        if (contentResponse.ok) {
                            const contentData = await contentResponse.json();
                            const fieldContent = contentData[selectedField] || '';
                            document.getElementById('output-content').value = fieldContent;
                            console.log('[SimpleOutput] Loaded field content from', endpoint, ':', selectedField);
                        }
                    } catch (error) {
                        console.error('[SimpleOutput] Error loading field content:', error);
                    }
                });
                
                console.log('[SimpleOutput] Initialization complete');
                
            } catch (error) {
                console.error('[SimpleOutput] Error during initialization:', error);
                // Show error in field selector
                const fieldSelect = document.getElementById('output-field-select');
                fieldSelect.innerHTML = '<option value="">Error loading fields</option>';
            }
        }

        // MultiInputManager Class
        class MultiInputManager {
            constructor(containerId, stage, substage) {
                this.container = document.getElementById(containerId);
                this.stage = stage;
                this.substage = substage;
                this.inputCounter = 1;
                this.localStorageKey = `multiInputConfig_${stage}_${substage}`;
                this.persistTimeout = null;
                this.init();
            }

            init() {
                console.log('[MultiInputManager] Initializing for', this.stage, this.substage);
                this.restoreInputsFromStorage();
                this.bindEvents();
            }

            bindEvents() {
                // Add input button
                const addInputBtn = document.getElementById('add-input-btn');
                if (addInputBtn) {
                    addInputBtn.addEventListener('click', () => this.addInputField());
                }

                // Remove input buttons (delegated)
                this.container.addEventListener('click', (e) => {
                    if (e.target.classList.contains('remove-input-btn') || e.target.closest('.remove-input-btn')) {
                        const removeBtn = e.target.classList.contains('remove-input-btn') ?
                            e.target : e.target.closest('.remove-input-btn');
                        const inputGroup = removeBtn.closest('.input-field-group');
                        if (inputGroup) {
                            this.removeInputField(inputGroup);
                        }
                    }
                });

                // Persist textarea changes
                this.container.addEventListener('input', (e) => {
                    if (e.target.tagName === 'TEXTAREA') {
                        // Debounce the persistence to avoid too many localStorage writes
                        clearTimeout(this.persistTimeout);
                        this.persistTimeout = setTimeout(() => {
                            this.persistInputsToStorage();
                            console.log('[MultiInputManager] Persisted textarea change');
                        }, 500);
                    }
                });
            }

            getInitialInputCounter() {
                const config = JSON.parse(localStorage.getItem(this.localStorageKey) || '[]');
                return Math.max(1, config.length);
            }

            restoreInputsFromStorage() {
                try {
                    const config = JSON.parse(localStorage.getItem(this.localStorageKey) || '[]');
                    console.log('[MultiInputManager] Restoring config from', this.localStorageKey, config);
                    
                    if (config.length > 0) {
                        // Add inputs as per config
                        for (let i = 0; i < config.length; i++) {
                            this.addInputField();
                        }
                        
                        // Set dropdown values and trigger fieldSelectorInit
                        this.container.querySelectorAll('.input-field-group').forEach((group, idx) => {
                            if (!config[idx]) return;
                            
                            const select = group.querySelector('select.field-selector');
                            const textarea = group.querySelector('textarea');
                            
                            if (select) {
                                select.value = config[idx].selectedField || '';
                                // Trigger field selector initialization
                                const event = new CustomEvent('fieldSelectorInit', {
                                    detail: { 
                                        target: group.dataset.inputId,
                                        element: select,
                                        value: config[idx].selectedField
                                    }
                                });
                                document.dispatchEvent(event);
                            }
                            
                            if (textarea && config[idx].value) {
                                textarea.value = config[idx].value;
                            }
                        });
                    } else {
                        // No saved config, add default input
                        this.addInputField();
                    }
                } catch (error) {
                    console.error('[MultiInputManager] Error restoring config:', error);
                    // Fallback to default input
                    this.addInputField();
                }
            }

            addInputField() {
                this.inputCounter++;
                const inputId = `input${this.inputCounter}`;
                
                const inputHtml = `
                    <div class="input-field-group mb-4 p-3 border border-gray-600 rounded" data-input-id="${inputId}">
                        <div class="flex justify-between items-center mb-2">
                            <label for="input_${inputId}" class="block text-sm font-medium text-blue-500">
                                [${inputId}]
                            </label>
                            <button type="button" class="remove-input-btn text-red-500 hover:text-red-400 text-sm">
                                <i class="fas fa-trash"></i> Remove
                            </button>
                        </div>
                        <div class="flex gap-2 mb-2">
                            <select class="field-selector bg-dark-bg text-dark-text border border-dark-border rounded p-2 flex-1"
                                data-target="input_${inputId}" data-section="inputs" data-current-substage="${this.substage}">
                                <option value="">Select field...</option>
                            </select>
                            <select class="format-selector bg-dark-bg text-dark-text border border-dark-border rounded p-2 w-48">
                                <option value="">Input Format</option>
                            </select>
                        </div>
                        <textarea id="input_${inputId}" name="${inputId}"
                            class="w-full bg-dark-bg border border-dark-border text-dark-text rounded p-4" rows="4" 
                            data-db-field="" data-db-table="post_development" 
                            placeholder="Enter text..."></textarea>
                    </div>
                `;
                
                this.container.insertAdjacentHTML('beforeend', inputHtml);
                
                // Initialize field selector for the new input
                this.initializeFieldSelector(inputId);
                
                this.persistInputsToStorage();
                console.log('[MultiInputManager] Added input field:', inputId);
            }

            removeInputField(element) {
                if (!element) return;
                
                const inputId = element.dataset.inputId;
                const totalInputs = this.container.querySelectorAll('.input-field-group').length;
                
                if (totalInputs <= 1) {
                    alert('At least one input field is required.');
                    return;
                }
                
                element.remove();
                this.persistInputsToStorage();
                console.log('[MultiInputManager] Removed input field:', inputId);
            }

            persistInputsToStorage() {
                const config = [];
                this.container.querySelectorAll('.input-field-group').forEach(group => {
                    const inputId = group.dataset.inputId;
                    const textarea = group.querySelector('textarea');
                    const select = group.querySelector('select.field-selector');
                    
                    config.push({
                        inputId: inputId,
                        selectedField: select ? select.value : '',
                        value: textarea ? textarea.value : ''
                    });
                });
                
                localStorage.setItem(this.localStorageKey, JSON.stringify(config));
                console.log('[MultiInputManager] Persisted config:', config);
            }

            initializeFieldSelector(inputId) {
                // This will be called by FieldSelector when it initializes
                console.log('[MultiInputManager] Field selector initialized for:', inputId);
            }

            updateTextareaValue(inputId, value) {
                const textarea = document.getElementById(`input_${inputId}`);
                if (textarea) {
                    textarea.value = value;
                    this.persistInputsToStorage();
                }
            }

            getAllInputs() {
                const inputs = {};
                this.container.querySelectorAll('.input-field-group').forEach(group => {
                    const inputId = group.dataset.inputId;
                    const textarea = group.querySelector('textarea');
                    const select = group.querySelector('select.field-selector');
                    
                    if (textarea && select) {
                        inputs[inputId] = {
                            field: select.value || '',
                            value: textarea.value || '',
                            db_field: textarea.dataset.dbField || '',
                            db_table: textarea.dataset.dbTable || 'post_development'
                        };
                    }
                });
                return inputs;
            }
        }

        // FieldSelector Class
        class FieldSelector {
            constructor(postId, stage, substage) {
                this.postId = postId;
                this.stage = stage;
                this.substage = substage;
                this.fields = {};
                this.fieldValues = {};
                this.isInitializing = false;
                this.initialized = false;
                this.init();
            }

            async init() {
                console.log('[FieldSelector] Initializing for post:', this.postId, 'stage:', this.stage);
                if (this.isInitializing || this.initialized) {
                    console.log('[FieldSelector] Already initializing or initialized, returning');
                    return;
                }
                this.isInitializing = true;
                
                try {
                    // Show loading state
                    this.showLoadingState();
                    
                    // Fetch current field values
                    console.log('[FieldSelector] Fetching field values for post:', this.postId);
                    const response = await fetch(baseUrl + `/api/workflow/posts/${this.postId}/development`);
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const data = await response.json();
                    this.fieldValues = data;
                    console.log('[FieldSelector] Field values loaded:', Object.keys(this.fieldValues));
                    
                    // Get available fields
                    console.log('[FieldSelector] Fetching available fields...');
                    const fieldsApiEndpoint = isIntegrated ? `/api/workflow/fields/available?stage_id=1&substage_id=1` : baseUrl + `/api/available-fields/${this.stage}`;
                    const fieldsResponse = await fetch(fieldsApiEndpoint);
                    if (!fieldsResponse.ok) {
                        throw new Error(`HTTP error! status: ${fieldsResponse.status}`);
                    }
                    const fieldsData = await fieldsResponse.json();
                    this.fields = {};
                    fieldsData.fields.forEach(field => {
                        this.fields[field.field_name] = field;
                    });
                    console.log('[FieldSelector] Available fields loaded:', Object.keys(this.fields));
                    
                    // Initialize all field selectors
                    this.initializeAllFieldSelectors();
                    
                    this.initialized = true;
                    console.log('[FieldSelector] Initialization complete');
                    
                    // Hide loading state
                    this.hideLoadingState();
                    
                } catch (error) {
                    console.error('[FieldSelector] Error during initialization:', error);
                    this.showErrorState(error.message);
                } finally {
                    this.isInitializing = false;
                }
            }

            showLoadingState() {
                const container = document.getElementById('inputs-container');
                if (container) {
                    container.innerHTML = '<div class="loading-state">Loading input fields...</div>';
                }
            }

            hideLoadingState() {
                // Loading state will be replaced by MultiInputManager content
            }

            showErrorState(errorMessage) {
                const container = document.getElementById('inputs-container');
                if (container) {
                    container.innerHTML = `
                        <div class="error-state">
                            <div class="error-message">
                                <i class="fas fa-exclamation-triangle"></i>
                                Error loading input fields: ${errorMessage}
                            </div>
                            <button onclick="location.reload()" class="retry-btn">
                                <i class="fas fa-redo"></i> Retry
                            </button>
                        </div>
                    `;
                }
            }

            initializeAllFieldSelectors() {
                console.log('[FieldSelector] Initializing all field selectors');
                const selectors = document.querySelectorAll('select.field-selector');
                selectors.forEach(selector => {
                    this.initializeSingleFieldSelector(selector);
                });
            }

            initializeSingleFieldSelector(selector) {
                const target = selector.dataset.target;
                const section = selector.dataset.section;
                
                if (!target || !section) {
                    console.warn('[FieldSelector] Missing target or section for selector:', selector);
                    return;
                }
                
                console.log('[FieldSelector] Initializing selector for target:', target, 'section:', section);
                
                // Clear existing options
                selector.innerHTML = '<option value="">Select field...</option>';
                
                // Add field options
                Object.keys(this.fields).forEach(fieldName => {
                    const field = this.fields[fieldName];
                    const option = document.createElement('option');
                    option.value = fieldName;
                    option.textContent = field.display_name;
                    selector.appendChild(option);
                });
                
                // Add change event listener
                selector.addEventListener('change', (e) => {
                    this.handleFieldSelectionChange(e.target);
                });
                
                console.log('[FieldSelector] Selector initialized for:', target);
            }

            async handleFieldSelectionChange(selector) {
                const selectedField = selector.value;
                const target = selector.dataset.target;
                
                if (!selectedField) {
                    console.log('[FieldSelector] No field selected, clearing content');
                    return;
                }
                
                console.log('[FieldSelector] Field selection changed:', selectedField, 'for target:', target);
                
                try {
                    await this.loadFieldContent(selectedField, selector);
                    await this.saveFieldMapping(selectedField, selector);
                } catch (error) {
                    console.error('[FieldSelector] Error handling field selection change:', error);
                }
            }

            async loadFieldContent(selectedField, selector) {
                console.log('[FieldSelector] Loading field content for:', selectedField);
                const targetId = selector.dataset.target;
                if (!targetId) return;

                const targetElement = document.getElementById(targetId);
                if (!targetElement || targetElement.tagName !== 'TEXTAREA') return;

                const fieldInfo = this.fields[selectedField];
                if (!fieldInfo) return;

                // Set data attributes
                targetElement.dataset.dbField = fieldInfo.db_field || selectedField;
                targetElement.dataset.dbTable = fieldInfo.db_table || 'post_development';
                
                try {
                    // Use cached values if available
                    if (selectedField in this.fieldValues) {
                        targetElement.value = this.fieldValues[selectedField] || '';
                        console.log('[FieldSelector] Loaded field content from cache:', selectedField);
                    } else {
                        // Fetch the latest value
                        const response = await fetch(baseUrl + `/api/workflow/posts/${this.postId}/development`);
                        if (response.ok) {
                            const data = await response.json();
                            this.fieldValues = data;
                            targetElement.value = this.fieldValues[selectedField] || '';
                            console.log('[FieldSelector] Loaded field content from API:', selectedField);
                        }
                    }
                    
                    // Update MultiInputManager's textarea value for persistence
                    if (targetId.startsWith('input_')) {
                        const inputId = targetId.replace('input_', '');
                        const multiInputManager = window.multiInputManager;
                        if (multiInputManager) {
                            multiInputManager.updateTextareaValue(inputId, targetElement.value);
                        }
                    }
                    
                    console.log('[FieldSelector] Field content loaded successfully');
                } catch (error) {
                    console.error('[FieldSelector] Error loading field content:', error);
                }
            }

            async saveFieldMapping(fieldName, selector) {
                try {
                    const target = selector.dataset.target;
                    const section = selector.dataset.section;
                    
                    if (section === 'inputs') {
                        // Save input field selection to backend database
                        const stepId = this.getCurrentStepId();
                        if (!stepId) {
                            console.warn('[FieldSelector] Could not determine current step ID for input field persistence');
                            this.showUserFeedback('Warning: Could not save field selection (no step ID)', 'warning');
                            return;
                        }
                        
                        const inputId = target.replace('input_', '');
                        const fieldInfo = this.fields[fieldName];
                        
                        // Save to backend using the same pattern as other dropdowns
                        const fieldSelectionApiEndpoint = isIntegrated ? `/api/workflow/steps/${stepId}/field-selection` : baseUrl + `/api/step/${stepId}/field-selection`;
                        const response = await fetch(fieldSelectionApiEndpoint, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                input_field: fieldName,
                                input_table: fieldInfo?.db_table || 'post_development',
                                input_id: inputId
                            })
                        });
                        
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        
                        console.log('[FieldSelector] Saved input field selection to backend:', { inputId, fieldName });
                        this.showUserFeedback(`Field selection saved: ${fieldInfo?.display_name || fieldName}`, 'success');
                    }
                } catch (error) {
                    console.error('[FieldSelector] Error saving field mapping:', error);
                    this.showUserFeedback(`Error saving field selection: ${error.message}`, 'error');
                }
            }

            showUserFeedback(message, type = 'info') {
                // Create feedback element
                const feedback = document.createElement('div');
                feedback.className = `user-feedback user-feedback-${type}`;
                feedback.innerHTML = `
                    <div class="feedback-content">
                        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                        <span>${message}</span>
                    </div>
                `;
                
                // Add to page
                document.body.appendChild(feedback);
                
                // Remove after 3 seconds
                setTimeout(() => {
                    if (feedback.parentNode) {
                        feedback.parentNode.removeChild(feedback);
                    }
                }, 3000);
            }

            getCurrentStepId() {
                // Try to get step ID from URL parameters or injected context
                const urlParams = new URLSearchParams(window.location.search);
                const stepId = urlParams.get('step_id');
                if (stepId) return stepId;
                
                // Try to get from injected context
                if (window.workflowContext && window.workflowContext.step_id) {
                    return window.workflowContext.step_id;
                }
                
                return null;
            }
        }

        async function loadConfig() {
            try {
                const apiEndpoint = isIntegrated ? '/api/llm-actions/config' : baseUrl + '/api/llm/config';
                const response = await fetch(apiEndpoint);
                const config = await response.json();
                
                // Update UI elements safely
                const providerEl = document.getElementById('config-provider');
                const modelEl = document.getElementById('config-model');
                const apiBaseEl = document.getElementById('config-api-base');
                const statusEl = document.getElementById('config-status');
                const tempEl = document.getElementById('config-temperature');
                const tokensEl = document.getElementById('config-max-tokens');
                const timeoutEl = document.getElementById('config-timeout');
                
                if (providerEl) providerEl.textContent = config.provider_type || 'Unknown';
                if (modelEl) modelEl.textContent = config.model_name || 'Unknown';
                if (apiBaseEl) apiBaseEl.textContent = config.api_base || 'Unknown';
                if (statusEl) statusEl.textContent = config.is_active ? 'Active' : 'Inactive';
                
                // Set default values for LLM parameters
                if (tempEl) tempEl.textContent = '0.7';
                if (tokensEl) tokensEl.textContent = '1000';
                if (timeoutEl) timeoutEl.textContent = '60s';
            } catch (error) {
                console.error('Error loading config:', error);
                const providerEl = document.getElementById('config-provider');
                const modelEl = document.getElementById('config-model');
                const apiBaseEl = document.getElementById('config-api-base');
                const statusEl = document.getElementById('config-status');
                const tempEl = document.getElementById('config-temperature');
                const tokensEl = document.getElementById('config-max-tokens');
                const timeoutEl = document.getElementById('config-timeout');
                
                if (providerEl) providerEl.textContent = 'Error';
                if (modelEl) modelEl.textContent = 'Error';
                if (apiBaseEl) apiBaseEl.textContent = 'Error';
                if (statusEl) statusEl.textContent = 'Error';
                if (tempEl) tempEl.textContent = 'Error';
                if (tokensEl) tokensEl.textContent = 'Error';
                if (timeoutEl) timeoutEl.textContent = 'Error';
            }
        }

        async function loadActions() {
            console.log('loadActions called');
            try {
                const apiEndpoint = isIntegrated ? '/api/llm-actions/actions' : baseUrl + '/api/llm/actions';
                const response = await fetch(apiEndpoint);
                actions = await response.json();
                console.log('Loaded', actions.length, 'actions');
                
                const select = document.getElementById('action-select');
                console.log('Found select element:', select);
                if (select) {
                    select.innerHTML = '<option value="">Choose an action...</option>';
                    
                    // Group prompts by their group field (same structure as workflow_prompts)
                    const groupedPrompts = {};
                    actions.forEach(action => {
                        const group = action.group || 'Unassigned';
                        if (!groupedPrompts[group]) {
                            groupedPrompts[group] = [];
                        }
                        groupedPrompts[group].push(action);
                    });
                    
                    // Add prompts organized by groups (EXACT same order as workflow_prompts - NO SORTING)
                    Object.keys(groupedPrompts).forEach(group => {
                        // Add group header
                        const groupOption = document.createElement('option');
                        groupOption.value = '';
                        groupOption.textContent = `── ${group} ──`;
                        groupOption.disabled = true;
                        groupOption.style.fontWeight = 'bold';
                        groupOption.style.backgroundColor = '#374151';
                        select.appendChild(groupOption);
                        
                        // Add prompts in this group
                        groupedPrompts[group].forEach(action => {
                            const option = document.createElement('option');
                            option.value = action.id;
                            option.textContent = `  ${action.field_name}`;
                            option.style.paddingLeft = '20px';
                            select.appendChild(option);
                            console.log('Added task prompt:', action.field_name, 'in group:', group);
                        });
                    });
                
                // Try to set default selection based on context
                let defaultAction = null;
                
                // First, try to get from localStorage for this specific context
                const storageKey = `selected_prompt_${context.stage}_${context.substage}_${context.step}`;
                const savedPromptId = localStorage.getItem(storageKey);
                if (savedPromptId) {
                    defaultAction = actions.find(action => action.id == savedPromptId);
                    console.log('Found saved prompt selection:', defaultAction?.field_name);
                }
                
                // If no saved selection, try to find a prompt that matches the step name
                if (!defaultAction) {
                    const stepName = context.step.replace('_', ' ').toLowerCase();
                    defaultAction = actions.find(action => 
                        action.field_name && action.field_name.toLowerCase().includes(stepName)
                    );
                    console.log('Found step-matching prompt:', defaultAction?.field_name);
                }
                
                // If still no match, select the first prompt
                if (!defaultAction && actions.length > 0) {
                    defaultAction = actions[0];
                    console.log('Selected first prompt as default:', defaultAction.field_name);
                }
                
                if (defaultAction) {
                    select.value = defaultAction.id;
                    loadActionInfo(); // Load the action info and prompt content
                    
                    // Sync the loaded content to the Message Management System
                    setTimeout(() => {
                        if (window.messageManagementSystem) {
                            window.messageManagementSystem.syncTaskPromptContent();
                        }
                    }, 100);
                }
                }
            } catch (error) {
                console.error('Error loading actions:', error);
            }
        }

        async function loadSystemPrompts() {
            console.log('loadSystemPrompts called');
            try {
                const apiEndpoint = isIntegrated ? '/api/llm/system-prompts' : baseUrl + '/api/llm/system-prompts';
                const response = await fetch(apiEndpoint);
                systemPrompts = await response.json();
                console.log('Loaded', systemPrompts.length, 'system prompts');
                
                const select = document.getElementById('system-prompt-select');
                console.log('Found system prompt select element:', select);
                if (select) {
                    select.innerHTML = '<option value="">Choose a system prompt...</option>';
                    
                    systemPrompts.forEach(prompt => {
                        const option = document.createElement('option');
                        option.value = prompt.id;
                        option.textContent = prompt.name;
                        select.appendChild(option);
                        console.log('Added system prompt:', prompt.name);
                    });
                
                // Try to set default selection based on context
                let defaultSystemPrompt = null;
                
                // First, try to get from localStorage for this specific context
                const storageKey = `selected_system_prompt_${context.stage}_${context.substage}_${context.step}`;
                const savedSystemPromptId = localStorage.getItem(storageKey);
                if (savedSystemPromptId) {
                    defaultSystemPrompt = systemPrompts.find(prompt => prompt.id == savedSystemPromptId);
                    console.log('Found saved system prompt selection:', defaultSystemPrompt?.name);
                }
                
                // If no saved selection, select the first prompt
                if (!defaultSystemPrompt && systemPrompts.length > 0) {
                    defaultSystemPrompt = systemPrompts[0];
                    console.log('Selected first system prompt as default:', defaultSystemPrompt.name);
                }
                
                if (defaultSystemPrompt) {
                    select.value = defaultSystemPrompt.id;
                    loadSystemPromptInfo(); // Load the system prompt content
                    
                    // Sync the loaded content to the Message Management System
                    setTimeout(() => {
                        if (window.messageManagementSystem) {
                            window.messageManagementSystem.syncSystemPromptContent();
                        }
                    }, 100);
                }
                }
            } catch (error) {
                console.error('Error loading system prompts:', error);
            }
        }

        function loadSystemPromptInfo() {
            console.log('loadSystemPromptInfo called');
            const systemPromptSelect = document.getElementById('system-prompt-select');
            const systemPromptDisplay = document.getElementById('system-prompt-display');
            
            console.log('DOM elements found:', { systemPromptSelect: !!systemPromptSelect, systemPromptDisplay: !!systemPromptDisplay });
            
            if (!systemPromptSelect || !systemPromptDisplay) {
                console.warn('Required DOM elements not found for loadSystemPromptInfo');
                return;
            }
            
            const promptId = systemPromptSelect.value;
            console.log('Selected system prompt ID:', promptId);
            console.log('Available system prompts:', systemPrompts);
            
            if (!promptId) {
                systemPromptDisplay.textContent = 'Select a system prompt to view its content...';
                selectedSystemPrompt = null;
                return;
            }
            
            selectedSystemPrompt = systemPrompts.find(p => p.id == promptId);
            console.log('Found selected system prompt:', selectedSystemPrompt);
            if (selectedSystemPrompt) {
                console.log('Selected system prompt content:', selectedSystemPrompt.system_prompt);
                
                // Show system prompt content
                const promptContent = selectedSystemPrompt.system_prompt || 'No system prompt available';
                console.log('Setting system prompt display to:', promptContent);
                systemPromptDisplay.textContent = promptContent;
            } else {
                console.log('No system prompt found for ID:', promptId);
            }
        }

        function loadActionInfo() {
            console.log('loadActionInfo called');
            const actionSelect = document.getElementById('action-select');
            const promptDisplay = document.getElementById('prompt-display');
            
            console.log('DOM elements found:', { actionSelect: !!actionSelect, promptDisplay: !!promptDisplay });
            
            if (!actionSelect || !promptDisplay) {
                console.warn('Required DOM elements not found for loadActionInfo');
                return;
            }
            
            const actionId = actionSelect.value;
            console.log('Selected action ID:', actionId);
            console.log('Available actions:', actions);
            
            if (!actionId) {
                promptDisplay.textContent = 'Select a task prompt to view its content...';
                selectedAction = null;
                return;
            }
            
            selectedAction = actions.find(a => a.id == actionId);
            console.log('Found selected task prompt:', selectedAction);
            if (selectedAction) {
                console.log('Selected task prompt template:', selectedAction.prompt_template);
                
                // Show prompt content
                const promptContent = selectedAction.prompt_template || 'No prompt template available';
                console.log('Setting prompt display to:', promptContent);
                promptDisplay.textContent = promptContent;
            } else {
                console.log('No task prompt found for ID:', actionId);
            }
        }

        async function testLLM() {
            const outputContent = document.getElementById('output-content');
            const statusIndicator = document.getElementById('status-indicator');
            
            outputContent.textContent = 'Testing LLM connection...';
            statusIndicator.className = 'status-indicator loading';
            
            try {
                const apiEndpoint = isIntegrated ? '/api/llm-actions/test' : baseUrl + '/api/llm/test';
                const response = await fetch(apiEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        prompt: 'Hello, this is a test message. Please respond with a brief greeting.',
                        model: 'mistral'
                    })
                });

                const result = await response.json();
                
                if (result.status === 'success') {
                    outputContent.textContent = `Test successful!\n\nResponse: ${result.response}`;
                    statusIndicator.className = 'status-indicator';
                } else {
                    outputContent.textContent = `Test failed: ${result.error}`;
                    statusIndicator.className = 'status-indicator error';
                }
            } catch (error) {
                outputContent.textContent = 'Error: ' + error.message;
                statusIndicator.className = 'status-indicator error';
            }
        }

        async function startOllama() {
            console.log('[StartOllama] Attempting to start Ollama...');
            
            const startButton = document.querySelector('.btn-start-ollama');
            const originalButtonText = startButton.innerHTML;
            startButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
            startButton.disabled = true;
            
            try {
                // Try to start Ollama using the system command
                const response = await fetch('/api/start-ollama', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                if (response.ok) {
                    const result = await response.json();
                    if (result.status === 'success') {
                        alert('Ollama started successfully! You can now use the Run LLM button.');
                        // Update status in config grid
                        const statusElement = document.getElementById('config-status');
                        if (statusElement) {
                            statusElement.textContent = 'Running';
                            statusElement.style.color = '#10b981';
                        }
                    } else {
                        throw new Error(result.error || 'Failed to start Ollama');
                    }
                } else {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
            } catch (error) {
                console.error('[StartOllama] Error:', error);
                alert(`Failed to start Ollama: ${error.message}\n\nPlease start Ollama manually by running 'ollama serve' in your terminal.`);
            } finally {
                // Restore button state
                startButton.innerHTML = originalButtonText;
                startButton.disabled = false;
            }
        }

        // Iframe Communication Functions for Sections Integration
        async function getSelectedSectionIds() {
            console.log('[IframeComm] Requesting selected section IDs from green panel...');
            return new Promise((resolve) => {
                const messageHandler = (event) => {
                    if (event.data.type === 'SELECTED_SECTIONS_RESPONSE') {
                        console.log('[IframeComm] Received selected section IDs:', event.data.sectionIds);
                        console.log('[IframeComm] Section IDs type:', typeof event.data.sectionIds);
                        console.log('[IframeComm] Section IDs length:', event.data.sectionIds.length);
                        window.removeEventListener('message', messageHandler);
                        resolve(event.data.sectionIds);
                    }
                };
                
                window.addEventListener('message', messageHandler);
                
                // Send message to parent (main workflow) which will relay to sections iframe
                console.log('[IframeComm] Sending GET_SELECTED_SECTIONS to parent workflow');
                window.parent.postMessage({
                    type: 'GET_SELECTED_SECTIONS',
                    source: 'llm-actions'
                }, '*');
                
                // Timeout fallback
                setTimeout(async () => {
                    console.log('[IframeComm] Timeout reached, iframe communication failed');
                    window.removeEventListener('message', messageHandler);
                    resolve([]);
                }, 5000);
            });
        }

        async function runLLM() {
            console.log('[RunLLM] Starting LLM execution...');
            
            // Check if this is the section_illustrations step
            const step = urlParams.get('step') || context.step || 'initial_concept';
            const stepId = urlParams.get('step_id');
            
            // Check if this is the section_illustrations step (either by step name or step_id=55)
            if (step === 'section_illustrations' || stepId === '55') {
                console.log('[RunLLM] Detected section_illustrations step, calling image generation');
                await runImageGeneration();
                return;
            }
            
            // Check if this is the image_concepts step (either by step name or step_id=53)
            if (step === 'image_concepts' || stepId === '53') {
                console.log('[RunLLM] Detected image_concepts step, calling backend script directly');
                
                // Call the backend script directly without checking sections
                const postId = urlParams.get('post_id') || context.post_id;
                const stepId = urlParams.get('step_id') || context.step_id;
                
                try {
                    const response = await fetch('http://localhost:5000/api/workflow/execute-step', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            post_id: postId,
                            step_id: stepId
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    const result = await response.json();
                    console.log('[RunLLM] Backend script result:', result);
                    
                } catch (error) {
                    console.error('[RunLLM] Error calling backend script:', error);
                }
                
                return;
            }
            
            // Get the Live Preview content
            const previewElement = document.getElementById('enhanced-prompt-preview');
            if (!previewElement || !previewElement.textContent.trim()) {
                alert('No content in Live Preview. Please add some content to the message elements.');
                return;
            }
            
            const messageContent = previewElement.textContent.trim();
            console.log('[RunLLM] Message content:', messageContent.substring(0, 100) + '...');
            
            // Get the selected output field
            const outputFieldSelect = document.getElementById('output-field-select');
            if (!outputFieldSelect || !outputFieldSelect.value) {
                alert('Please select an output field to save the LLM response.');
                return;
            }
            
            const selectedField = outputFieldSelect.value;
            console.log('[RunLLM] Selected output field:', selectedField);
            
            // Check if this is sections substage
            if (context.substage === 'sections') {
                console.log('[RunLLM] Detected sections substage, processing sections individually');
                await processSectionsWithLLM(selectedField, messageContent);
            } else {
                console.log('[RunLLM] Processing as individual action for substage:', context.substage);
                await processIndividualAction(selectedField, messageContent);
            }
        }

        // Section Processing Functions
        async function processSectionsWithLLM(outputField, messageContent) {
            console.log('[ProcessSections] Starting section processing...');
            
            // Show loading state
            const runButton = document.querySelector('.btn-run-llm');
            const originalButtonText = runButton ? runButton.innerHTML : 'Run LLM';
            if (runButton) {
                runButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing Sections...';
                runButton.disabled = true;
            }
            
            try {
                // Get selected section IDs
                const selectedSectionIds = await getSelectedSectionIds();
                console.log('[ProcessSections] Received section IDs:', selectedSectionIds);
                
                if (selectedSectionIds.length === 0) {
                    alert('Please select at least one section in the green panel.');
                    return;
                }
                
                console.log('[ProcessSections] Processing', selectedSectionIds.length, 'sections');
                
                // Show progress indicator
                showProgressIndicator(`Processing ${selectedSectionIds.length} sections...`);
                
                let successCount = 0;
                let errorCount = 0;
                
                // Process each section individually
                for (let i = 0; i < selectedSectionIds.length; i++) {
                    const sectionId = selectedSectionIds[i];
                    updateProgressIndicator(`Processing section ${i + 1} of ${selectedSectionIds.length}...`);
                    
                    try {
                        const stepId = urlParams.get('step_id') || '53'; // Default to image_concepts if not specified
                        await processSectionWithLLM(sectionId, outputField, messageContent, stepId);
                        successCount++;
                        console.log(`[ProcessSections] Successfully processed section ${sectionId}`);
                    } catch (error) {
                        errorCount++;
                        console.error(`[ProcessSections] Failed to process section ${sectionId}:`, error);
                    }
                }
                
                hideProgressIndicator();
                
                // Show final results
                if (errorCount === 0) {
                    alert(`Successfully processed all ${successCount} sections!`);
                } else {
                    alert(`Processed ${successCount} sections successfully, ${errorCount} failed. Check console for details.`);
                }
                
            } catch (error) {
                hideProgressIndicator();
                console.error('[ProcessSections] Error:', error);
                alert('Error processing sections. Check console for details.');
            } finally {
                // Restore button state
                if (runButton) {
                    runButton.innerHTML = originalButtonText;
                    runButton.disabled = false;
                }
            }
        }

        async function processIndividualAction(outputField, messageContent) {
            console.log('[ProcessIndividual] Processing individual action...');
            
            // Show loading state
            const runButton = document.querySelector('.btn-run-llm');
            const originalButtonText = runButton.innerHTML;
            runButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
            runButton.disabled = true;
            
            try {
                // Get correct post_id from URL parameters
                const urlParams = new URLSearchParams(window.location.search);
                const postId = urlParams.get('post_id') || context.post_id;
                
                console.log('[ProcessIndividual] Using post_id:', postId, 'output_field:', outputField);
                
                // Send to LLM using the existing /api/run-llm endpoint
                const response = await fetch('/api/run-llm', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        system_prompt: '',
                        persona: '',
                        task: messageContent,
                        post_id: postId,
                        output_field: outputField,
                        stage: context.stage || '',
                        substage: context.substage || ''
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                console.log('[ProcessIndividual] LLM Response:', result);
                
                if (result.status === 'success' && result.output) {
                    const llmResponse = result.output;
                    
                    // Update the output content display
                    const outputContent = document.getElementById('output-content');
                    if (outputContent) {
                        outputContent.value = llmResponse;
                    }
                    
                    // Show success
                    alert(`LLM response saved to ${outputField} successfully!`);
                } else {
                    throw new Error(result.error || 'Invalid response format from LLM');
                }
                
            } catch (error) {
                console.error('[ProcessIndividual] Error:', error);
                
                // Check if it's a connection error and provide helpful guidance
                if (error.message.includes('Connection refused') || error.message.includes('LLM service is not available')) {
                    const shouldStartOllama = confirm(
                        'Ollama is not running. Would you like to start it now?\n\n' +
                        'Click "OK" to start Ollama automatically, or "Cancel" to start it manually.'
                    );
                    
                    if (shouldStartOllama) {
                        await startOllama();
                    } else {
                        alert(
                            'To start Ollama manually:\n\n' +
                            '1. Open Terminal\n' +
                            '2. Run: ollama serve\n' +
                            '3. Wait for it to start\n' +
                            '4. Try the Run LLM button again'
                        );
                    }
                } else {
                    alert(`Error running LLM: ${error.message}`);
                }
            } finally {
                // Restore button state
                runButton.innerHTML = originalButtonText;
                runButton.disabled = false;
            }
        }

        async function processSectionWithLLM(sectionId, outputField, messageContent, stepId) {
            console.log(`[ProcessSection] Processing section ${sectionId} with step_id ${stepId}...`);
            
            try {
                // Get section context
                const sectionContext = await getSectionContext(sectionId);
                
                // Build section-specific prompt
                const prompt = `${messageContent}\n\nSection Context:\n${sectionContext}`;
                
                console.log(`[ProcessSection] Section ${sectionId} prompt:`, prompt.substring(0, 200) + '...');
                
                // Call the blog-core execute-step endpoint instead of local LLM
                const postId = urlParams.get('post_id') || context.post_id;
                const response = await fetch('http://localhost:5000/api/workflow/execute-step', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        post_id: postId,
                        step_id: stepId,
                        section_ids: [sectionId],
                        context: {
                            'step_id': stepId,
                            'output_field': outputField,
                            'message_content': messageContent
                        }
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                
                if (result.status === 'success' && result.output) {
                    console.log(`[ProcessSection] Successfully processed section ${sectionId}`);
                } else {
                    throw new Error(result.error || 'Invalid response from LLM');
                }
                
            } catch (error) {
                console.error(`[ProcessSection] Error processing section ${sectionId}:`, error);
                throw error;
            }
        }

        async function getSectionContext(sectionId) {
            console.log(`[GetSectionContext] Fetching context for section ${sectionId}...`);
            
            try {
                const response = await fetch(`http://localhost:5003/api/sections/${sectionId}`);
                if (!response.ok) {
                    throw new Error(`Failed to fetch section ${sectionId}`);
                }
                
                const section = await response.json();
                console.log(`[GetSectionContext] Section data:`, section);
                
                // Build context string from relevant fields
                const contextParts = [];
                if (section.section_heading) contextParts.push(`Section: ${section.section_heading}`);
                if (section.section_description) contextParts.push(`Description: ${section.section_description}`);
                if (section.draft) contextParts.push(`Current Draft: ${section.draft}`);
                if (section.ideas_to_include) contextParts.push(`Ideas to Include: ${section.ideas_to_include}`);
                if (section.facts_to_include) contextParts.push(`Facts to Include: ${section.facts_to_include}`);
                
                const context = contextParts.join('\n');
                console.log(`[GetSectionContext] Built context:`, context);
                return context;
                
            } catch (error) {
                console.error(`[GetSectionContext] Error fetching section context for ${sectionId}:`, error);
                return `Section ID: ${sectionId}`;
            }
        }

        // Progress Indicator Functions
        function showProgressIndicator(message) {
            console.log('[Progress] Showing indicator:', message);
            let indicator = document.getElementById('progress-indicator');
            if (!indicator) {
                indicator = document.createElement('div');
                indicator.id = 'progress-indicator';
                indicator.style.cssText = `
                    position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
                    background: rgba(0,0,0,0.8); color: white; padding: 20px; border-radius: 8px;
                    z-index: 10000; text-align: center; font-family: Arial, sans-serif;
                `;
                document.body.appendChild(indicator);
            }
            indicator.textContent = message;
            indicator.style.display = 'block';
        }

        function updateProgressIndicator(message) {
            const indicator = document.getElementById('progress-indicator');
            if (indicator) {
                indicator.textContent = message;
            }
        }

        function hideProgressIndicator() {
            const indicator = document.getElementById('progress-indicator');
            if (indicator) {
                indicator.style.display = 'none';
            }
        }
        
        async function saveToOutputField(fieldName, content) {
            console.log('[SaveToOutput] Saving content to field:', fieldName);
            
            // Get post ID from URL parameters or context
            const urlParams = new URLSearchParams(window.location.search);
            const postId = urlParams.get('post_id') || context.post_id;
            
            // Determine which endpoint to use based on field mapping
            let endpoint = `/api/workflow/posts/${postId}/development`;
            
            // Check if this is a post_info stage field that should go to post table
            const stage = context.stage || '';
            const substage = context.substage || '';
            
            if (stage === 'writing' && substage === 'post_info') {
                // For post_info stage, check if field belongs to post table
                const postFields = ['title', 'subtitle', 'title_choices', 'summary'];
                if (postFields.includes(fieldName)) {
                    endpoint = `/api/workflow/posts/${postId}/post`;
                    console.log('[SaveToOutput] Using post table endpoint for field:', fieldName);
                }
            }
            
            try {
                const response = await fetch(endpoint, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        [fieldName]: content
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                console.log('[SaveToOutput] Save result:', result);
                
                // Update the output content display
                const outputContent = document.getElementById('output-content');
                if (outputContent) {
                    outputContent.value = content;
                }
                
            } catch (error) {
                console.error('[SaveToOutput] Error:', error);
                throw error;
            }
        }



        function addContextField() {
            const contextSection = document.querySelector('.llm-section');
            const addButton = document.querySelector('.add-context-btn');

            const newField = document.createElement('div');
            newField.className = 'context-field';
            newField.innerHTML = `
                <label class="field-label">Additional Context</label>
                <input type="text" class="field-input" placeholder="Enter additional context...">
            `;

            contextSection.insertBefore(newField, addButton);
        }

        // Auto-save context and task
        function autoSave() {
            const systemPromptSelect = document.getElementById('system-prompt-select');
            const taskInput = document.getElementById('task-input');
            
            const systemPrompt = systemPromptSelect ? systemPromptSelect.value : '';
            const task = taskInput ? taskInput.value : '';

            // Save to localStorage for now
            localStorage.setItem('llm-context', JSON.stringify({
                system_prompt: systemPrompt,
                task: task
            }));
        }

        // Persist step settings to database
        async function persistStepSettings() {
            try {
                // Get step_id from URL parameters
                const urlParams = new URLSearchParams(window.location.search);
                const stepId = urlParams.get('step_id') || context.step_id;
                const taskPromptId = document.getElementById('action-select')?.value || null;
                const systemPromptId = document.getElementById('system-prompt-select')?.value || null;
                
                console.log('Persisting step settings:', { stepId, taskPromptId, systemPromptId });
                
                const response = await fetch('http://localhost:5000/api/workflow/persist-step-settings', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        step_id: stepId,
                        task_prompt_id: taskPromptId,
                        system_prompt_id: systemPromptId
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                console.log('Step settings persisted successfully:', result);
                
            } catch (error) {
                console.error('Error persisting step settings:', error);
            }
        }

        // Load saved data
        function loadSavedData() {
            const saved = localStorage.getItem('llm-context');
            if (saved) {
                const data = JSON.parse(saved);
                const systemPromptSelect = document.getElementById('system-prompt-select');
                const taskInput = document.getElementById('task-input');
                
                if (systemPromptSelect) {
                    systemPromptSelect.value = data.system_prompt || '';
                }
                
                if (taskInput) {
                    taskInput.value = data.task || '';
                }
            }
        }

        // Load step settings from database
        async function loadStepSettings() {
            try {
                // Get step_id from URL parameters
                const urlParams = new URLSearchParams(window.location.search);
                const stepId = urlParams.get('step_id') || context.step_id;
                
                if (!stepId) {
                    console.log('No step_id found, skipping step settings load');
                    return;
                }
                
                console.log('Loading step settings for step_id:', stepId);
                
                const response = await fetch(`http://localhost:5000/api/workflow/persist-step-settings?step_id=${stepId}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                console.log('Step settings loaded:', result);
                
                if (result.success) {
                    // Set task prompt dropdown
                    const actionSelect = document.getElementById('action-select');
                    if (actionSelect && result.task_prompt_id) {
                        actionSelect.value = result.task_prompt_id;
                        console.log('Set task prompt dropdown to:', result.task_prompt_id);
                    }
                    
                    // Set system prompt dropdown
                    const systemPromptSelect = document.getElementById('system-prompt-select');
                    if (systemPromptSelect && result.system_prompt_id) {
                        systemPromptSelect.value = result.system_prompt_id;
                        console.log('Set system prompt dropdown to:', result.system_prompt_id);
                    }
                }
                
            } catch (error) {
                console.error('Error loading step settings:', error);
            }
        }

        // Event listeners with null checks
        const systemPromptSelect = document.getElementById('system-prompt-select');
        const taskInput = document.getElementById('task-input');
        
        if (systemPromptSelect) {
            systemPromptSelect.addEventListener('input', autoSave);
        }
        
        if (taskInput) {
            taskInput.addEventListener('input', autoSave);
        }

        // Message Management System
        class MessageManagementSystem {
            constructor() {
                this.instructionCounter = 1;
                this.currentStepId = document.querySelector('.llm-container').getAttribute('data-step-id') || 'default';
                this.init();
            }

            init() {
                console.log('[MessageManagement] Initializing...');
                this.setupEventListeners();
                this.initializeAccordions();
                this.initializeSortable();
                
                // Sync any existing content on initialization
                setTimeout(async () => {
                    this.syncSystemPromptContent();
                    this.syncTaskPromptContent();
                    await this.syncPostDevelopmentContent();
                    // Input fields sync is handled by the simple input field system
                    this.loadElementOrder();
                }, 500);
            }

            setupEventListeners() {

                // Add instruction button
                const addInstructionBtn = document.getElementById('add-instruction-btn');
                if (addInstructionBtn) {
                    addInstructionBtn.addEventListener('click', () => this.addInstruction());
                }

                // Clear instructions button
                const clearInstructionsBtn = document.getElementById('clear-instructions-btn');
                if (clearInstructionsBtn) {
                    clearInstructionsBtn.addEventListener('click', () => this.clearAllInstructions());
                }

                // Copy preview button
                const copyPreviewBtn = document.getElementById('copy-preview-btn');
                if (copyPreviewBtn) {
                    copyPreviewBtn.addEventListener('click', () => this.copyPreview());
                }

                // Save config button
                const saveConfigBtn = document.getElementById('save-config-btn');
                if (saveConfigBtn) {
                    saveConfigBtn.addEventListener('click', () => this.saveConfiguration());
                }

                // Element toggles and edit buttons
                const container = document.getElementById('all-elements-container');
                if (container) {
                    container.addEventListener('change', (e) => {
                        if (e.target.classList.contains('element-toggle')) {
                            this.updatePreview();
                            this.saveElementOrder();
                        }
                    });

                    container.addEventListener('click', (e) => {
                        if (e.target.classList.contains('edit-element-btn')) {
                            this.editElement(e.target.closest('.message-accordion'));
                        }
                    });
                }

                // Sync system prompt content
                const systemPromptSelect = document.getElementById('system-prompt-select');
                if (systemPromptSelect) {
                    systemPromptSelect.addEventListener('change', () => {
                        this.syncSystemPromptContent();
                    });
                }

                // Sync task prompt content
                const actionSelect = document.getElementById('action-select');
                if (actionSelect) {
                    actionSelect.addEventListener('change', () => {
                        this.syncTaskPromptContent();
                    });
                }

                // Note: Input fields sync is handled by the simple input field system
                // to avoid duplicate event listeners and timing conflicts
            }

            syncSystemPromptContent() {
                const systemPromptDisplay = document.getElementById('system-prompt-display');
                const systemPromptElement = document.querySelector('[data-element-type="system_prompt"] .element-content');
                
                if (systemPromptDisplay && systemPromptElement) {
                    const content = systemPromptDisplay.textContent.trim();
                    if (content && content !== 'Select a system prompt to view its content...') {
                        systemPromptElement.textContent = content;
                        this.updatePreview();
                    }
                }
            }

            syncTaskPromptContent() {
                const promptDisplay = document.getElementById('prompt-display');
                const taskPromptElement = document.querySelector('[data-element-type="task_prompt"] .element-content');
                
                if (promptDisplay && taskPromptElement) {
                    const content = promptDisplay.textContent.trim();
                    if (content && content !== 'Select a task prompt to view its content...') {
                        taskPromptElement.textContent = content;
                        this.updatePreview();
                    }
                }
            }

            async syncPostDevelopmentContent() {
                const postId = document.querySelector('.llm-container').getAttribute('data-post-id');
                if (!postId) {
                    console.log('[MessageManagement] No post ID found, skipping post development sync');
                    return;
                }

                try {
                    const response = await fetch(`/api/workflow/posts/${postId}/development`);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const postData = await response.json();
                    console.log('[MessageManagement] Post development data:', postData);

                    // Sync Basic Idea
                    this.syncElementContent('basic_idea', postData.basic_idea);
                    
                    // Sync Section Headings
                    this.syncElementContent('section_headings', postData.section_headings);
                    
                    // Sync Idea Scope
                    this.syncElementContent('idea_scope', postData.idea_scope);

                } catch (error) {
                    console.error('[MessageManagement] Error syncing post development content:', error);
                }
            }

            syncElementContent(elementType, content) {
                const element = document.querySelector(`[data-element-type="${elementType}"] .element-content`);
                if (element) {
                    if (content) {
                        element.textContent = content;
                        console.log(`[MessageManagement] Synced ${elementType} content:`, content.substring(0, 50) + '...');
                    } else {
                        element.textContent = '[No content available]';
                        console.log(`[MessageManagement] No content found for ${elementType}`);
                    }
                    // Update preview after syncing content
                    this.updatePreview();
                }
            }

            syncInputFieldsContent() {
                const inputFieldSelect = document.getElementById('input-field-select');
                const inputContent = document.getElementById('input-content');
                const inputFieldsElement = document.querySelector('[data-element-type="inputs"] .placeholder-text');
                
                if (inputFieldSelect && inputContent && inputFieldsElement) {
                    const selectedField = inputFieldSelect.value;
                    const fieldContent = inputContent.value.trim();
                    
                    // Only sync if we have both a selected field and content
                    if (selectedField && fieldContent) {
                        // Just show the content without the field title
                        inputFieldsElement.textContent = fieldContent;
                        console.log('[MessageManagement] Synced input fields content (content only)');
                        // Update preview after syncing content
                        this.updatePreview();
                    } else if (!selectedField && !fieldContent) {
                        // Only show "no content" if both field and content are empty
                        inputFieldsElement.textContent = '[No content available]';
                        this.updatePreview();
                    }
                    // If we have a selected field but no content yet, don't overwrite existing content
                }
            }

            initializeAccordions() {
                const container = document.getElementById('all-elements-container');
                if (!container) return;

                container.addEventListener('click', (e) => {
                    if (e.target.closest('.accordion-header') || e.target.classList.contains('accordion-toggle')) {
                        const accordion = e.target.closest('.message-accordion');
                        if (accordion) {
                            this.toggleAccordion(accordion);
                        }
                    }
                });
            }

            toggleAccordion(accordion) {
                const content = accordion.querySelector('.accordion-content');
                const toggle = accordion.querySelector('.accordion-toggle');
                
                if (content && toggle) {
                    content.classList.toggle('hidden');
                    toggle.classList.toggle('expanded');
                }
            }

            initializeSortable() {
                console.log('Initializing sortable with reorder buttons...');
                const container = document.getElementById('all-elements-container');
                if (!container) {
                    console.log('No all-elements-container found');
                    return;
                }

                // Add re-order buttons to all accordions
                this.addReorderButtonsToAllElements();
            }

            addReorderButtonsToAllElements() {
                console.log('Adding reorder buttons to all elements...');
                const container = document.getElementById('all-elements-container');
                if (!container) {
                    console.log('No container found for reorder buttons');
                    return;
                }

                const accordions = container.querySelectorAll('.message-accordion');
                console.log('Found', accordions.length, 'accordions to add reorder buttons to');
                
                accordions.forEach((accordion, index) => {
                    this.addReorderButtonsToElement(accordion, index, accordions.length);
                });
            }

            addReorderButtonsToElement(element, index, totalElements) {
                console.log('Adding reorder buttons to element:', element.getAttribute('data-element-type'), 'index:', index, 'total:', totalElements);
                
                // Remove existing reorder buttons if any
                const existingButtons = element.querySelectorAll('.reorder-btn');
                existingButtons.forEach(btn => btn.remove());

                // Find the accordion-actions div
                const actionsDiv = element.querySelector('.accordion-actions');
                if (!actionsDiv) {
                    console.log('No accordion-actions div found');
                    return;
                }

                // Create reorder buttons container
                const reorderContainer = document.createElement('div');
                reorderContainer.className = 'reorder-buttons';
                reorderContainer.style.display = 'flex';
                reorderContainer.style.gap = '2px';
                reorderContainer.style.marginLeft = '8px';

                // Create up button
                const upBtn = document.createElement('button');
                upBtn.className = 'reorder-btn reorder-up';
                upBtn.innerHTML = '↑';
                upBtn.title = 'Move up';
                upBtn.disabled = index === 0;
                upBtn.style.cssText = `
                    background: var(--llm-surface);
                    border: 1px solid var(--llm-border);
                    color: var(--llm-purple-light);
                    cursor: pointer;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-size: 10px;
                    width: 20px;
                    height: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                `;

                // Create down button
                const downBtn = document.createElement('button');
                downBtn.className = 'reorder-btn reorder-down';
                downBtn.innerHTML = '↓';
                downBtn.title = 'Move down';
                downBtn.disabled = index === totalElements - 1;
                downBtn.style.cssText = upBtn.style.cssText;

                // Add hover effects
                [upBtn, downBtn].forEach(btn => {
                    btn.addEventListener('mouseenter', () => {
                        if (!btn.disabled) {
                            btn.style.background = 'var(--llm-purple)';
                            btn.style.color = 'white';
                        }
                    });
                    btn.addEventListener('mouseleave', () => {
                        if (!btn.disabled) {
                            btn.style.background = 'var(--llm-surface)';
                            btn.style.color = 'var(--llm-purple-light)';
                        }
                    });
                });

                // Add click handlers
                upBtn.addEventListener('click', () => {
                    console.log('Up button clicked for element:', element.getAttribute('data-element-type'));
                    if (index > 0) {
                        this.moveElementUp(element);
                    }
                });

                downBtn.addEventListener('click', () => {
                    console.log('Down button clicked for element:', element.getAttribute('data-element-type'));
                    if (index < totalElements - 1) {
                        this.moveElementDown(element);
                    }
                });

                // Add buttons to container
                reorderContainer.appendChild(upBtn);
                reorderContainer.appendChild(downBtn);

                // Insert before the accordion toggle
                const accordionToggle = actionsDiv.querySelector('.accordion-toggle');
                if (accordionToggle) {
                    actionsDiv.insertBefore(reorderContainer, accordionToggle);
                } else {
                    actionsDiv.appendChild(reorderContainer);
                }
                
                console.log('Reorder buttons added successfully');
            }

            moveElementUp(element) {
                const container = document.getElementById('all-elements-container');
                if (!container) return;

                const previousElement = element.previousElementSibling;
                if (previousElement) {
                    container.insertBefore(element, previousElement);
                    this.updateReorderButtons();
                    this.updatePreview();
                    this.saveElementOrder();
                }
            }

            moveElementDown(element) {
                const container = document.getElementById('all-elements-container');
                if (!container) return;

                const nextElement = element.nextElementSibling;
                if (nextElement) {
                    container.insertBefore(nextElement, element);
                    this.updateReorderButtons();
                    this.updatePreview();
                    this.saveElementOrder();
                }
            }

            updateReorderButtons() {
                const container = document.getElementById('all-elements-container');
                if (!container) return;

                const accordions = container.querySelectorAll('.message-accordion');
                accordions.forEach((accordion, index) => {
                    this.addReorderButtonsToElement(accordion, index, accordions.length);
                });
            }

            setupDragAndDrop(container) {
                // Old drag and drop functionality removed - now using reorder buttons
                console.log('Drag and drop disabled - using reorder buttons instead');
            }

            addInstruction() {
                const container = document.getElementById('all-elements-container');
                if (!container) return;

                const instructionDiv = document.createElement('div');
                instructionDiv.className = 'message-accordion instruction-element';
                instructionDiv.setAttribute('data-element-type', 'instruction');
                instructionDiv.setAttribute('data-element-id', `instruction_${this.instructionCounter}`);

                instructionDiv.innerHTML = `
                    <div class="accordion-header">
                        <div class="accordion-controls">
                            <input type="checkbox" class="element-toggle" checked>
                            <span class="element-label" style="color: #10b981;">Instruction ${this.instructionCounter}</span>
                        </div>
                        <div class="accordion-actions">
                            <button class="edit-element-btn">Edit</button>
                            <button class="remove-element-btn">Remove</button>
                            <span class="accordion-toggle">▼</span>
                        </div>
                    </div>
                    <div class="accordion-content">
                        <div class="element-content">
                            <textarea class="instruction-textarea" placeholder="Enter instruction text..." rows="3"></textarea>
                        </div>
                    </div>
                `;

                container.appendChild(instructionDiv);
                this.instructionCounter++;
                
                // Add reorder buttons to the new instruction
                const accordions = container.querySelectorAll('.message-accordion');
                this.addReorderButtonsToElement(instructionDiv, accordions.length - 1, accordions.length);
                
                this.updatePreview();
                this.saveElementOrder();

                // Add event listeners for the new instruction
                const removeBtn = instructionDiv.querySelector('.remove-element-btn');
                if (removeBtn) {
                    removeBtn.addEventListener('click', () => {
                        instructionDiv.remove();
                        this.updateReorderButtons();
                        this.updatePreview();
                        this.saveElementOrder();
                    });
                }
            }

            clearAllInstructions() {
                const container = document.getElementById('all-elements-container');
                if (!container) return;

                const instructions = container.querySelectorAll('.instruction-element');
                instructions.forEach(instruction => instruction.remove());
                this.instructionCounter = 1;
                this.updateReorderButtons();
                this.updatePreview();
                this.saveElementOrder();
            }

            editElement(element) {
                if (!element) return;

                const content = element.querySelector('.element-content');
                if (!content) return;

                const currentText = content.textContent.trim();
                const textarea = document.createElement('textarea');
                textarea.value = currentText;
                textarea.className = 'edit-textarea';
                textarea.rows = 4;

                const saveBtn = document.createElement('button');
                saveBtn.textContent = 'Save';
                saveBtn.className = 'btn-action';
                saveBtn.style.marginTop = '8px';

                const cancelBtn = document.createElement('button');
                cancelBtn.textContent = 'Cancel';
                cancelBtn.className = 'btn-action';
                cancelBtn.style.marginTop = '8px';
                cancelBtn.style.marginLeft = '8px';

                content.innerHTML = '';
                content.appendChild(textarea);
                content.appendChild(saveBtn);
                content.appendChild(cancelBtn);

                saveBtn.addEventListener('click', () => {
                    content.textContent = textarea.value;
                    this.updatePreview();
                });

                cancelBtn.addEventListener('click', () => {
                    content.textContent = currentText;
                });
            }

            updatePreview() {
                const preview = document.getElementById('enhanced-prompt-preview');
                const charCount = document.getElementById('preview-char-count');
                const elementCount = document.getElementById('preview-element-count');
                
                if (!preview) return;

                const enabledElements = [];
                const container = document.getElementById('all-elements-container');
                if (!container) return;

                const allElements = container.querySelectorAll('.message-accordion');
                
                allElements.forEach(element => {
                    const toggle = element.querySelector('.element-toggle');
                    if (toggle && toggle.checked) {
                        const elementType = element.getAttribute('data-element-type');
                        let text = '';

                        if (elementType === 'instruction') {
                            const content = element.querySelector('.element-content');
                            const textarea = content ? content.querySelector('.instruction-textarea') : null;
                            text = textarea ? textarea.value : '';
                        } else if (elementType === 'inputs') {
                            // Special handling for Input Fields element
                            const placeholderText = element.querySelector('.placeholder-text');
                            text = placeholderText ? placeholderText.textContent.trim() : '';
                        } else {
                            const content = element.querySelector('.element-content');
                            text = content ? content.textContent.trim() : '';
                        }

                        enabledElements.push({
                            type: elementType,
                            label: element.querySelector('.element-label').textContent,
                            content: text || '[No content available]'
                        });
                    }
                });

                // Assemble preview
                const previewText = enabledElements.map(element => {
                    return `${element.label}:\n${element.content}\n`;
                }).join('\n');

                preview.textContent = previewText;
                
                if (charCount) {
                    charCount.textContent = `${previewText.length} characters`;
                }
                
                if (elementCount) {
                    elementCount.textContent = `${enabledElements.length} elements`;
                }
            }

            copyPreview() {
                const preview = document.getElementById('enhanced-prompt-preview');
                if (!preview || !preview.textContent) return;

                navigator.clipboard.writeText(preview.textContent).then(() => {
                    // Show feedback
                    const copyBtn = document.getElementById('copy-preview-btn');
                    if (copyBtn) {
                        const originalText = copyBtn.innerHTML;
                        copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                        setTimeout(() => {
                            copyBtn.innerHTML = originalText;
                        }, 2000);
                    }
                }).catch(err => {
                    console.error('Failed to copy: ', err);
                });
            }

            saveElementOrder() {
                const container = document.getElementById('all-elements-container');
                if (!container) return;

                const elements = container.querySelectorAll('.message-accordion');
                const order = Array.from(elements).map(element => {
                    const toggle = element.querySelector('.element-toggle');
                    return {
                        type: element.getAttribute('data-element-type'),
                        id: element.getAttribute('data-element-id') || null,
                        enabled: toggle ? toggle.checked : true
                    };
                });

                const storageKey = `messageOrder_${this.currentStepId}`;
                localStorage.setItem(storageKey, JSON.stringify(order));
                console.log('[MessageManagement] Element order and states saved for step:', this.currentStepId);
            }

            loadElementOrder() {
                const container = document.getElementById('all-elements-container');
                if (!container) return;

                const storageKey = `messageOrder_${this.currentStepId}`;
                const savedOrder = localStorage.getItem(storageKey);
                
                if (!savedOrder) {
                    console.log('[MessageManagement] No saved order found for step:', this.currentStepId);
                    return;
                }

                try {
                    const order = JSON.parse(savedOrder);
                    const elements = Array.from(container.querySelectorAll('.message-accordion'));
                    
                    // Create a map of element types to elements
                    const elementMap = new Map();
                    elements.forEach(element => {
                        const type = element.getAttribute('data-element-type');
                        const id = element.getAttribute('data-element-id');
                        const key = id ? `${type}_${id}` : type;
                        elementMap.set(key, element);
                    });

                    // Reorder elements based on saved order and restore checkbox states
                    order.forEach(item => {
                        const key = item.id ? `${item.type}_${item.id}` : item.type;
                        const element = elementMap.get(key);
                        if (element) {
                            container.appendChild(element);
                            
                            // Restore checkbox state
                            const toggle = element.querySelector('.element-toggle');
                            if (toggle && typeof item.enabled === 'boolean') {
                                toggle.checked = item.enabled;
                            }
                        }
                    });

                    console.log('[MessageManagement] Element order and states restored for step:', this.currentStepId);
                    this.updatePreview();
                } catch (error) {
                    console.error('[MessageManagement] Error loading element order:', error);
                }
            }

            saveConfiguration() {
                // Placeholder for configuration saving
                const saveBtn = document.getElementById('save-config-btn');
                if (saveBtn) {
                    const originalText = saveBtn.innerHTML;
                    saveBtn.innerHTML = '<i class="fas fa-check"></i> Saved!';
                    setTimeout(() => {
                        saveBtn.innerHTML = originalText;
                    }, 2000);
                }
                console.log('[MessageManagement] Configuration saved (placeholder)');
            }
        }



        // Initialize message management system
        let messageManagementSystem;
        
        // Theme detection and application
        function applyTheme() {
            const urlParams = new URLSearchParams(window.location.search);
            const step = urlParams.get('step');
            
            if (step === 'section_illustrations') {
                document.body.classList.add('dark-maroon-theme');
                console.log('Applied dark maroon theme for section_illustrations step');
            }
        }
        
        // Initialize immediately if DOM is already loaded
        if (document.readyState === 'loading') {
            // DOM is still loading, wait for DOMContentLoaded
            document.addEventListener('DOMContentLoaded', function() {
                applyTheme();
                messageManagementSystem = new MessageManagementSystem();
                // Make it available globally for other systems to access
                window.messageManagementSystem = messageManagementSystem;
            });
        } else {
            // DOM is already loaded, initialize immediately
            applyTheme();
            messageManagementSystem = new MessageManagementSystem();
            // Make it available globally for other systems to access
            window.messageManagementSystem = messageManagementSystem;
        }
    </script>