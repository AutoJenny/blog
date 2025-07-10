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
                this.postSections = sectionsData || [];
                
                // Populate the post section selector
                const selector = document.getElementById('post-section-selector');
                if (selector) {
                    // Clear existing options except "All Sections"
                    selector.innerHTML = '<option value="">All Sections</option>';
                    
                    this.postSections.forEach(section => {
                        const option = document.createElement('option');
                        option.value = section.id;
                        option.textContent = section.section_heading || `Section ${section.id}`;
                        selector.appendChild(option);
                    });
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
                    
                    // Update the accordion content with real data
                    this.updateAccordionContent('system_prompt', 'You are a helpful assistant, expert in social media blogging and online marketing...');
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
                            this.updateAccordionContent('task_prompt', taskPrompt);
                        } else {
                            // Fallback to textarea if API fails
                            const taskPromptTextarea = document.getElementById('task_prompt');
                            const actualTaskPrompt = taskPromptTextarea ? taskPromptTextarea.value : 'No task prompt available';
                            this.updateAccordionContent('task_prompt', actualTaskPrompt);
                        }
                    } else {
                        // Fallback to textarea if no step ID
                        const taskPromptTextarea = document.getElementById('task_prompt');
                        const actualTaskPrompt = taskPromptTextarea ? taskPromptTextarea.value : 'No task prompt available';
                        this.updateAccordionContent('task_prompt', actualTaskPrompt);
                    }
                }
            }

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
                        fields.outputs.push({
                            id: field.field_name,
                            name: displayName,
                            content: '',
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
            
            // Detect available fields
            const availableFields = await this.detectAvailableFields();
            
            // Populate input and output sections with real data
            await this.populateSectionWithRealData('input', availableFields.inputs);
            await this.populateSectionWithRealData('output', availableFields.outputs);
            
            // Update preview and summary
            this.updatePreview();
            this.updateSummary();
            
            console.log('[ENHANCED_LLM] Context refresh complete');
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
                const content = accordion.querySelector('.element-content');
                if (content) {
                    enabledElements.push(content.textContent.trim());
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
            const toggles = accordion.querySelectorAll('.element-toggle');
            totalElements += toggles.length;
            toggles.forEach(toggle => {
                if (toggle.checked) totalEnabled++;
            });
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
}

// Export for ES6 modules
export default EnhancedLLMMessageManager; 