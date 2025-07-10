/**
 * Enhanced LLM Message Manager
 * Provides advanced message management with accordion sections, drag & drop, and live preview
 */

class EnhancedLLMMessageManager {
    constructor() {
        this.modal = null;
        this.workflowContext = {};
        this.fieldData = {};
        this.postSections = [];
        this.selectedPostSection = '';
        this.instructionCounter = 1;
        
        this.init();
    }

    init() {
        this.modal = document.getElementById('enhanced-llm-message-modal');
        if (!this.modal) {
            console.error('Enhanced LLM Message Modal not found');
            return;
        }

        this.setupEventListeners();
        this.initializeAccordions();
        this.initializeSortable();
        this.updatePreview();
    }

    setupEventListeners() {
        // Modal open/close
        document.getElementById('close-enhanced-modal')?.addEventListener('click', () => {
            this.closeModal();
        });

        // Post section selector
        document.getElementById('post-section-selector')?.addEventListener('change', (e) => {
            this.selectedPostSection = e.target.value;
            this.updateInputFieldsForSection(this.selectedPostSection);
            this.updatePreview();
        });

        // Add instruction button
        document.getElementById('add-instruction-btn')?.addEventListener('click', () => {
            this.addInstruction();
        });

        // Refresh button
        document.getElementById('refresh-enhanced-context')?.addEventListener('click', () => {
            this.refreshContext();
        });

        // Copy preview button
        document.getElementById('copy-preview-btn')?.addEventListener('click', () => {
            this.copyPreview();
        });

        // Save configuration button
        document.getElementById('save-enhanced-config')?.addEventListener('click', () => {
            this.saveConfiguration();
        });

        // Run LLM button
        document.getElementById('run-with-enhanced-context')?.addEventListener('click', () => {
            this.runLLM();
        });

        // Element toggles
        this.modal.addEventListener('change', (e) => {
            if (e.target.classList.contains('element-toggle')) {
                this.updatePreview();
                this.updateSummary();
            }
        });

        // Edit buttons
        this.modal.addEventListener('click', (e) => {
            if (e.target.classList.contains('edit-element-btn')) {
                this.editElement(e.target.closest('.message-accordion'));
            }
            if (e.target.classList.contains('remove-element-btn')) {
                this.removeElement(e.target.closest('.message-accordion'));
            }
        });

        // Close modal on background click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });
    }

    initializeAccordions() {
        // Add click handlers for accordion headers
        this.modal.addEventListener('click', (e) => {
            if (e.target.closest('.accordion-header')) {
                const accordion = e.target.closest('.message-accordion');
                this.toggleAccordion(accordion);
            }
        });
    }

    toggleAccordion(accordion) {
        const content = accordion.querySelector('.accordion-content');
        const toggle = accordion.querySelector('.accordion-toggle');
        
        if (content.classList.contains('hidden')) {
            content.classList.remove('hidden');
            toggle.textContent = '▲';
        } else {
            content.classList.add('hidden');
            toggle.textContent = '▼';
        }
    }

    openModal() {
        this.modal.classList.remove('hidden');
        this.loadWorkflowContext();
        this.loadPostSections();
        this.refreshContext();
        this.updateInputFieldsForSection(this.selectedPostSection);
        this.updatePreview();
        this.updateSummary();
    }

    closeModal() {
        this.modal.classList.add('hidden');
    }

    async loadWorkflowContext() {
        try {
            // Get current workflow context from URL
            const pathParts = window.location.pathname.split('/');
            this.workflowContext = {
                postId: pathParts[3],
                stage: pathParts[4],
                substage: pathParts[5]
            };

            // Get step from panel data attributes
            const panel = document.querySelector('[data-current-stage]');
            if (panel) {
                this.workflowContext.step = panel.dataset.currentStep;
                this.workflowContext.stepId = panel.dataset.stepId;
                this.workflowContext.stageId = panel.dataset.stageId;
                this.workflowContext.substageId = panel.dataset.substageId;
            }

            console.log('[ENHANCED_LLM] Workflow context loaded:', this.workflowContext);
        } catch (error) {
            console.error('[ENHANCED_LLM] Error loading workflow context:', error);
        }
    }

    async loadPostSections() {
        try {
            if (!this.workflowContext.postId) return;

            // Get post sections
            const response = await fetch(`/api/workflow/posts/${this.workflowContext.postId}/sections`);
            if (response.ok) {
                const sectionsData = await response.json();
                this.postSections = sectionsData.sections || [];
                
                // Populate the post section selector
                const selector = document.getElementById('post-section-selector');
                if (selector) {
                    // Clear existing options except "All Sections"
                    selector.innerHTML = '<option value="">All Sections</option>';
                    
                    this.postSections.forEach(section => {
                        const option = document.createElement('option');
                        option.value = section.id;
                        option.textContent = section.title || section.section_heading || `Section ${section.id}`;
                        selector.appendChild(option);
                    });
                    
                    // Set default to first section if available
                    if (this.postSections.length > 0) {
                        selector.value = this.postSections[0].id;
                        this.selectedPostSection = this.postSections[0].id;
                    }
                }
                
                console.log('[ENHANCED_LLM] Post sections loaded:', this.postSections.length);
            }
        } catch (error) {
            console.error('[ENHANCED_LLM] Error loading post sections:', error);
        }
    }

    async detectAvailableFields() {
        try {
            console.log('[ENHANCED_LLM] Detecting available fields...');
            
            const fields = {
                inputs: [],
                outputs: []
            };

            // Get post development fields (for Context and Task sections)
            if (this.workflowContext.postId) {
                const devResponse = await fetch(`/api/workflow/posts/${this.workflowContext.postId}/development`);
                if (devResponse.ok) {
                    const devData = await devResponse.json();
                    console.log('[ENHANCED_LLM] Development data loaded:', Object.keys(devData));
                    
                    // Update the accordion content with real data from post_development
                    this.updateAccordionContent('system_prompt', this.getSystemPromptContent());
                    this.updateAccordionContent('basic_idea', devData.basic_idea || 'No basic idea available');
                    this.updateAccordionContent('section_headings', devData.section_headings || 'No section headings available');
                    this.updateAccordionContent('idea_scope', devData.idea_scope || 'No idea scope available');
                    
                    // Get the actual task prompt from the saved prompts API
                    const stepId = this.getCurrentStepId();
                    if (stepId) {
                        const promptsResponse = await fetch(`/api/workflow/steps/${stepId}/prompts`);
                        if (promptsResponse.ok) {
                            const promptsData = await promptsResponse.json();
                            const taskPrompt = promptsData.task_prompt_content || 'No task prompt available';
                            const systemPrompt = promptsData.system_prompt_content || this.getSystemPromptContent();
                            this.updateAccordionContent('task_prompt', taskPrompt);
                            this.updateAccordionContent('system_prompt', systemPrompt);
                        } else {
                            // Fallback to textarea if API fails
                            const taskPromptTextarea = document.getElementById('task_prompt');
                            const actualTaskPrompt = taskPromptTextarea ? taskPromptTextarea.value : 'No task prompt available';
                            this.updateAccordionContent('task_prompt', actualTaskPrompt);
                            this.updateAccordionContent('system_prompt', this.getSystemPromptContent());
                        }
                    } else {
                        // Fallback to textarea if no step ID
                        const taskPromptTextarea = document.getElementById('task_prompt');
                        const actualTaskPrompt = taskPromptTextarea ? taskPromptTextarea.value : 'No task prompt available';
                        this.updateAccordionContent('task_prompt', actualTaskPrompt);
                        this.updateAccordionContent('system_prompt', this.getSystemPromptContent());
                    }
                }
            }

            // Get LLM settings from the purple panel
            this.updateAccordionContent('settings', this.getLLMSettingsContent());

            // Get available field mappings (for Inputs and Outputs sections)
            const fieldsResponse = await fetch('/api/workflow/fields/available');
            if (fieldsResponse.ok) {
                const fieldsData = await fieldsResponse.json();
                console.log('[ENHANCED_LLM] Available fields loaded:', fieldsData.fields.length);
                
                // Categorize mapped fields
                fieldsData.fields.forEach(field => {
                    if (field.mappings && field.mappings.length > 0) {
                        const mapping = field.mappings[0];
                        const displayName = field.display_name || this.mapFieldToDisplayName(field.field_name);
                        
                        const fieldElement = {
                            id: field.field_name,
                            name: displayName,
                            content: this.fieldData[field.field_name] || '',
                            type: 'field',
                            source: field.db_table,
                            mapping: mapping
                        };

                        // Categorize based on mapping
                        if (mapping.section === 'inputs') {
                            fields.inputs.push(fieldElement);
                        } else if (mapping.section === 'outputs') {
                            fields.outputs.push(fieldElement);
                        }
                    }
                });
            }

            // For Writing stage, get post_section fields
            if (this.workflowContext.stage === 'writing') {
                const sectionFieldsResponse = await fetch('/api/workflow/post_section_fields');
                if (sectionFieldsResponse.ok) {
                    const sectionFieldsData = await sectionFieldsResponse.json();
                    console.log('[ENHANCED_LLM] Post section fields loaded:', sectionFieldsData.fields.length);
                    
                    sectionFieldsData.fields.forEach(field => {
                        const displayName = this.mapFieldToDisplayName(field.field_name);
                        // For Writing stage, post_section fields are used as inputs (purple dropdown)
                        // Don't set content here - it will be loaded when section-specific data is available
                        fields.inputs.push({
                            id: field.field_name,
                            name: displayName,
                            content: null, // Will be populated when section data is loaded
                            type: 'field',
                            source: 'post_section',
                            isSectionField: true
                        });
                    });
                }
            }

            console.log('[ENHANCED_LLM] Field detection complete:', {
                inputs: fields.inputs.length,
                outputs: fields.outputs.length
            });

            return fields;
        } catch (error) {
            console.error('[ENHANCED_LLM] Error detecting fields:', error);
            return { inputs: [], outputs: [] };
        }
    }

    updateAccordionContent(elementType, content) {
        const accordion = this.modal.querySelector(`[data-element-type="${elementType}"]`);
        if (accordion) {
            const contentDiv = accordion.querySelector('.element-content');
            if (contentDiv) {
                contentDiv.textContent = content;
            }
        }
    }

    mapFieldToDisplayName(fieldName) {
        // Convert field names to user-friendly display names
        const nameMappings = {
            'basic_idea': 'Basic Idea',
            'idea_seed': 'Idea Seed',
            'idea_scope': 'Idea Scope',
            'expanded_idea': 'Expanded Idea',
            'provisional_title': 'Provisional Title',
            'topics_to_cover': 'Topics to Cover',
            'section_headings': 'Section Headings',
            'system_prompt': 'System Prompt',
            'task_prompt': 'Task Prompt',
            'section_heading': 'Section Heading',
            'section_description': 'Section Description',
            'draft': 'Draft Content',
            'polished': 'Polished Content',
            'facts_to_include': 'Facts to Include',
            'ideas_to_include': 'Ideas to Include',
            'highlighting': 'Highlighting',
            'image_concepts': 'Image Concepts',
            'image_prompts': 'Image Prompts',
            'watermarking': 'Watermarking',
            'image_meta_descriptions': 'Image Meta Descriptions',
            'image_captions': 'Image Captions',
            'generated_image_url': 'Generated Image URL',
            'status': 'Status',
            'polished': 'Polished'
        };

        return nameMappings[fieldName] || fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    async populateSectionWithRealData(sectionName, fields) {
        const container = document.getElementById(`${sectionName}-elements-list`);
        if (!container) return;

        // Clear existing content
        container.innerHTML = '';

        if (fields.length === 0) {
            const placeholder = document.createElement('div');
            placeholder.className = 'text-sm text-gray-400 italic';
            placeholder.textContent = `No ${sectionName} fields available for current workflow stage.`;
            container.appendChild(placeholder);
            return;
        }

        // Create field elements
        fields.forEach(field => {
            const fieldElement = this.createFieldElement(field);
            container.appendChild(fieldElement);
        });
    }

    createFieldElement(field) {
        const template = document.getElementById('enhanced-message-element-template');
        const element = template.content.cloneNode(true);
        const fieldDiv = element.querySelector('.message-element');
        
        fieldDiv.setAttribute('data-element-id', field.id);
        fieldDiv.setAttribute('data-element-type', field.type);
        fieldDiv.setAttribute('data-field-source', field.source);
        
        const label = fieldDiv.querySelector('.element-label');
        label.textContent = field.name;
        
        const content = fieldDiv.querySelector('.element-content');
        content.textContent = field.content || 'No content available';
        
        // Show remove button for instructional text only
        const removeBtn = fieldDiv.querySelector('.remove-element-btn');
        if (removeBtn && field.type !== 'instruction') {
            removeBtn.classList.add('hidden');
        }
        
        return fieldDiv;
    }

    addInstruction() {
        const template = document.getElementById('instruction-element-template');
        if (!template) return;

        const instructionId = `instruction_${this.instructionCounter++}`;
        const instructionElement = template.content.cloneNode(true);
        const instructionDiv = instructionElement.querySelector('.message-element');
        
        instructionDiv.setAttribute('data-element-id', instructionId);
        instructionDiv.querySelector('.element-content').textContent = 'Enter your instruction here...';

        // Add to the all-elements-container (default location)
        const container = document.getElementById('all-elements-container');
        if (container) {
            container.appendChild(instructionDiv);
            this.updatePreview();
            this.updateSummary();
        }
    }

    editElement(element) {
        const content = element.querySelector('.element-content');
        const currentText = content.textContent;
        
        // Create textarea for editing
        const textarea = document.createElement('textarea');
        textarea.value = currentText;
        textarea.className = 'w-full bg-gray-800 text-gray-300 text-xs p-2 rounded border border-gray-600';
        textarea.rows = 3;
        
        // Replace content with textarea
        content.style.display = 'none';
        content.parentNode.insertBefore(textarea, content);
        textarea.focus();

        // Handle save on blur or enter
        const saveEdit = () => {
            content.textContent = textarea.value;
            content.style.display = 'block';
            textarea.remove();
            this.updatePreview();
        };

        textarea.addEventListener('blur', saveEdit);
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                saveEdit();
            }
        });
    }

    removeElement(element) {
        if (element.getAttribute('data-element-type') === 'instruction') {
            element.remove();
            this.updatePreview();
            this.updateSummary();
        }
    }

    async refreshContext() {
        try {
            console.log('[ENHANCED_LLM] Refreshing context...');
            
            // Reload workflow context
            await this.loadWorkflowContext();
            
            // Reload post sections
            await this.loadPostSections();
            
            // Update input fields for current section
            await this.updateInputFieldsForSection(this.selectedPostSection);
            
            // Update preview and summary
            this.updatePreview();
            this.updateSummary();
            
            console.log('[ENHANCED_LLM] Context refreshed successfully');
        } catch (error) {
            console.error('[ENHANCED_LLM] Error refreshing context:', error);
        }
    }

    updatePreview() {
        const preview = document.getElementById('enhanced-prompt-preview');
        const charCount = document.getElementById('preview-char-count');
        
        if (!preview || !charCount) return;

        // Collect all enabled elements from all accordions
        const enabledElements = [];
        const allAccordions = this.modal.querySelectorAll('.message-accordion');
        
        allAccordions.forEach(accordion => {
            const toggle = accordion.querySelector('.element-toggle');
            if (toggle && toggle.checked) {
                // Check if this accordion has individual field elements (like inputs/outputs)
                const fieldElements = accordion.querySelectorAll('.message-element');
                if (fieldElements.length > 0) {
                    // This accordion contains individual field elements
                    fieldElements.forEach(fieldElement => {
                        const fieldToggle = fieldElement.querySelector('.element-toggle');
                        if (fieldToggle && fieldToggle.checked) {
                            const fieldContent = fieldElement.querySelector('.element-content');
                            if (fieldContent && fieldContent.textContent.trim()) {
                                const fieldLabel = fieldElement.querySelector('.element-label');
                                const label = fieldLabel ? fieldLabel.textContent : 'Field';
                                enabledElements.push(`${label}: ${fieldContent.textContent.trim()}`);
                            }
                        }
                    });
                } else {
                    // This accordion has direct content
                    const content = accordion.querySelector('.element-content');
                    if (content && content.textContent.trim()) {
                        enabledElements.push(content.textContent.trim());
                    }
                }
            }
        });

        // Assemble the message
        const message = enabledElements.join('\n\n');
        preview.textContent = message || 'No elements enabled';
        
        // Update character count
        charCount.textContent = message.length;
    }

    updateSummary() {
        const summary = document.getElementById('enhanced-context-summary');
        if (!summary) return;

        // Count all enabled elements across all accordions
        let totalEnabled = 0;
        let totalElements = 0;
        
        const allAccordions = this.modal.querySelectorAll('.message-accordion');
        
        allAccordions.forEach(accordion => {
            const accordionToggle = accordion.querySelector('.element-toggle');
            if (accordionToggle && accordionToggle.checked) {
                // Check if this accordion has individual field elements
                const fieldElements = accordion.querySelectorAll('.message-element');
                if (fieldElements.length > 0) {
                    // Count individual field elements
                    fieldElements.forEach(fieldElement => {
                        const fieldToggle = fieldElement.querySelector('.element-toggle');
                        if (fieldToggle) {
                            totalElements++;
                            if (fieldToggle.checked) totalEnabled++;
                        }
                    });
                } else {
                    // Count the accordion itself
                    totalElements++;
                    totalEnabled++;
                }
            }
        });
        
        summary.textContent = `${totalEnabled} of ${totalElements} elements enabled`;
    }

    copyPreview() {
        const preview = document.getElementById('enhanced-prompt-preview');
        if (!preview) return;

        navigator.clipboard.writeText(preview.textContent).then(() => {
            // Show feedback
            const copyBtn = document.getElementById('copy-preview-btn');
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="fas fa-check mr-1"></i>Copied!';
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
            }, 2000);
        });
    }

    saveConfiguration() {
        // Collect all configuration data
        const config = {
            accordions: {},
            timestamp: new Date().toISOString()
        };

        // Save each accordion's configuration
        const allAccordions = this.modal.querySelectorAll('.message-accordion');
        allAccordions.forEach(accordion => {
            const elementType = accordion.getAttribute('data-element-type');
            const toggle = accordion.querySelector('.element-toggle');
            const content = accordion.querySelector('.element-content');
            
            config.accordions[elementType] = {
                enabled: toggle ? toggle.checked : true,
                content: content ? content.textContent : ''
            };
        });

        // Save to localStorage for now
        localStorage.setItem('enhanced-llm-config', JSON.stringify(config));
        
        // Show feedback
        const saveBtn = document.getElementById('save-enhanced-config');
        const originalText = saveBtn.textContent;
        saveBtn.textContent = 'Saved!';
        setTimeout(() => {
            saveBtn.textContent = originalText;
        }, 2000);
    }

    runLLM() {
        const preview = document.getElementById('enhanced-prompt-preview');
        if (!preview) return;

        const message = preview.textContent;
        if (!message || message === 'No elements enabled') {
            alert('Please enable some elements before running the LLM.');
            return;
        }

        // This would integrate with the existing LLM run functionality
        console.log('Running LLM with enhanced message:', message);
        
        // For now, just show an alert
        alert('LLM run functionality would be integrated here with the assembled message.');
    }

    initializeSortable() {
        // Initialize drag & drop for the unified container
        const container = document.getElementById('all-elements-container');
        if (container) {
            this.setupDragAndDrop(container);
        }
    }

    setupDragAndDrop(container) {
        let draggedElement = null;

        container.addEventListener('dragstart', (e) => {
            if (e.target.classList.contains('message-accordion')) {
                draggedElement = e.target;
                e.target.style.opacity = '0.5';
            }
        });

        container.addEventListener('dragend', (e) => {
            if (e.target.classList.contains('message-accordion')) {
                e.target.style.opacity = '1';
                draggedElement = null;
            }
        });

        container.addEventListener('dragover', (e) => {
            e.preventDefault();
            const afterElement = this.getDragAfterElement(container, e.clientY);
            const draggable = document.querySelector('.dragging');
            if (draggable) {
                if (afterElement == null) {
                    container.appendChild(draggable);
                } else {
                    container.insertBefore(draggable, afterElement);
                }
            }
        });

        // Make accordions draggable
        container.querySelectorAll('.message-accordion').forEach(accordion => {
            accordion.draggable = true;
            accordion.addEventListener('dragstart', () => {
                accordion.classList.add('dragging');
            });
            accordion.addEventListener('dragend', () => {
                accordion.classList.remove('dragging');
            });
        });
    }

    getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.message-accordion:not(.dragging)')];
        
        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    getCurrentStepId() {
        // Try to get step ID from URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const stepParam = urlParams.get('step');
        
        if (stepParam) {
            // Map step names to IDs based on the workflow structure
            const stepMap = {
                'ideas_to_include': 43,
                'author_first_drafts': 16,
                'fix_language': 49,
                'main': 18,
                'images_section_concept': 44,
                'images_section_llm_prompt': 45
            };
            
            return stepMap[stepParam] || null;
        }
        
        // If no step parameter, try to get from panel data
        const panel = document.querySelector('[data-current-stage]');
        if (panel && panel.dataset.currentStep) {
            const stepName = panel.dataset.currentStep;
            const stepMap = {
                'Ideas to include': 43,
                'Author First Drafts': 16,
                'FIX language': 49,
                'Main': 18,
                'IMAGES section concept': 44,
                'IMAGES section LLM prompt': 45
            };
            
            return stepMap[stepName] || null;
        }
        
        return null;
    }

    getSystemPromptContent() {
        // Try to get system prompt from saved prompts API first
        const stepId = this.getCurrentStepId();
        if (stepId) {
            // This will be handled asynchronously in detectAvailableFields
            return 'Loading system prompt...';
        }
        
        // Fallback to textarea
        const systemPromptTextarea = document.getElementById('system_prompt');
        return systemPromptTextarea ? systemPromptTextarea.value : 'No system prompt available';
    }

    getLLMSettingsContent() {
        // Get actual LLM settings from the purple panel
        const modelSelect = document.getElementById('llm-model-select');
        const temperatureInput = document.querySelector('input[name="temperature"]');
        const maxTokensInput = document.querySelector('input[name="max_tokens"]');
        const timeoutInput = document.getElementById('llm-timeout');
        
        const model = modelSelect ? modelSelect.value : 'Not selected';
        const temperature = temperatureInput ? temperatureInput.value : '0.7';
        const maxTokens = maxTokensInput ? maxTokensInput.value : '1000';
        const timeout = timeoutInput ? timeoutInput.value : '60';
        
        return `Model: ${model}, Temperature: ${temperature}, Max Tokens: ${maxTokens}, Timeout: ${timeout}s`;
    }

    async getSectionSpecificContent(sectionId) {
        try {
            if (!sectionId || !this.workflowContext.postId) return {};
            
            // Get specific section data
            const response = await fetch(`/api/workflow/posts/${this.workflowContext.postId}/sections/${sectionId}`);
            if (response.ok) {
                const sectionData = await response.json();
                console.log('[ENHANCED_LLM] Section data loaded for section', sectionId, ':', Object.keys(sectionData));
                return sectionData;
            }
        } catch (error) {
            console.error('[ENHANCED_LLM] Error loading section data:', error);
        }
        return {};
    }

    async updateInputFieldsForSection(sectionId) {
        try {
            console.log('[ENHANCED_LLM] updateInputFieldsForSection called with sectionId:', sectionId);
            
            if (!sectionId || sectionId === '') {
                console.log('[ENHANCED_LLM] No section selected, showing all sections data');
                // Show all sections data
                this.populateInputFieldsWithAllSections();
                return;
            }
            
            console.log('[ENHANCED_LLM] Getting section-specific content for section:', sectionId);
            const sectionData = await this.getSectionSpecificContent(sectionId);
            console.log('[ENHANCED_LLM] Section data received:', Object.keys(sectionData));
            
            if (!sectionData || Object.keys(sectionData).length === 0) {
                console.log('[ENHANCED_LLM] No section data found, showing all sections data');
                this.populateInputFieldsWithAllSections();
                return;
            }
            
            // Update input fields with section-specific content
            const inputContainer = document.getElementById('input-elements-list');
            if (!inputContainer) {
                console.error('[ENHANCED_LLM] Input container not found');
                return;
            }
            
            // Clear existing content
            inputContainer.innerHTML = '';
            
            // Get available input fields
            const fields = await this.detectAvailableFields();
            console.log('[ENHANCED_LLM] Available fields:', {
                inputs: fields.inputs.length,
                outputs: fields.outputs.length
            });
            
            // Filter to only show section-specific fields
            const sectionFields = fields.inputs.filter(field => 
                field.source === 'post_section' || 
                field.isSectionField === true
            );
            
            console.log('[ENHANCED_LLM] Section fields found:', sectionFields.length);
            
            // Create field elements with section-specific content
            sectionFields.forEach(field => {
                console.log('[ENHANCED_LLM] Creating field element for:', field.name, 'with content from:', field.id);
                
                // Get content from section data, with fallbacks
                let fieldContent = 'No content available';
                if (sectionData[field.id]) {
                    fieldContent = sectionData[field.id];
                } else if (sectionData[field.db_field]) {
                    fieldContent = sectionData[field.db_field];
                } else if (field.content && field.content !== null) {
                    fieldContent = field.content;
                }
                
                console.log('[ENHANCED_LLM] Field content:', fieldContent.substring(0, 50) + '...');
                
                const fieldElement = this.createFieldElement({
                    ...field,
                    content: fieldContent
                });
                inputContainer.appendChild(fieldElement);
            });
            
            if (sectionFields.length === 0) {
                console.log('[ENHANCED_LLM] No section fields found, showing placeholder');
                const placeholder = document.createElement('div');
                placeholder.className = 'text-sm text-gray-400 italic';
                placeholder.textContent = 'No section-specific input fields available.';
                inputContainer.appendChild(placeholder);
            }
            
            console.log('[ENHANCED_LLM] Updated input fields for section', sectionId);
            
            // Update preview and summary after updating input fields
            this.updatePreview();
            this.updateSummary();
        } catch (error) {
            console.error('[ENHANCED_LLM] Error updating input fields for section:', error);
        }
    }

    async populateInputFieldsWithAllSections() {
        try {
            console.log('[ENHANCED_LLM] populateInputFieldsWithAllSections called');
            
            const inputContainer = document.getElementById('input-elements-list');
            if (!inputContainer) {
                console.error('[ENHANCED_LLM] Input container not found in populateInputFieldsWithAllSections');
                return;
            }
            
            // Clear existing content
            inputContainer.innerHTML = '';
            
            // Get available input fields
            const fields = await this.detectAvailableFields();
            console.log('[ENHANCED_LLM] All available fields:', {
                inputs: fields.inputs.length,
                outputs: fields.outputs.length
            });
            
            // Show all input fields
            fields.inputs.forEach(field => {
                console.log('[ENHANCED_LLM] Creating field element for:', field.name, 'with content:', field.content?.substring(0, 50) + '...');
                const fieldElement = this.createFieldElement(field);
                inputContainer.appendChild(fieldElement);
            });
            
            if (fields.inputs.length === 0) {
                console.log('[ENHANCED_LLM] No input fields found, showing placeholder');
                const placeholder = document.createElement('div');
                placeholder.className = 'text-sm text-gray-400 italic';
                placeholder.textContent = 'No input fields available for current workflow stage.';
                inputContainer.appendChild(placeholder);
            }
            
            console.log('[ENHANCED_LLM] Populated input fields with all sections data');
            
            // Update preview and summary after populating input fields
            this.updatePreview();
            this.updateSummary();
        } catch (error) {
            console.error('[ENHANCED_LLM] Error populating input fields with all sections:', error);
        }
    }
}

// Export for ES6 modules
export default EnhancedLLMMessageManager; 