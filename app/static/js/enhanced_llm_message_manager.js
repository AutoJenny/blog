/**
 * Enhanced LLM Message Manager
 * Provides advanced message management with categorized sections, drag & drop, and live preview
 */

class EnhancedLLMMessageManager {
    constructor() {
        this.modal = null;
        this.currentSection = 'context';
        this.elements = new Map();
        this.instructionCounter = 1;
        this.fieldData = {};
        this.workflowContext = {};
        
        this.init();
    }

    init() {
        this.modal = document.getElementById('enhanced-llm-message-modal');
        if (!this.modal) {
            console.error('Enhanced LLM Message Modal not found');
            return;
        }

        this.setupEventListeners();
        this.initializeSortable();
        this.updatePreview();
    }

    setupEventListeners() {
        // Modal open/close
        document.getElementById('close-enhanced-modal')?.addEventListener('click', () => {
            this.closeModal();
        });

        // Section selector
        document.getElementById('section-selector')?.addEventListener('change', (e) => {
            this.switchSection(e.target.value);
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
                this.editElement(e.target.closest('.message-element'));
            }
            if (e.target.classList.contains('remove-element-btn')) {
                this.removeElement(e.target.closest('.message-element'));
            }
        });

        // Close modal on background click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });
    }

    openModal() {
        this.modal.classList.remove('hidden');
        this.loadWorkflowContext();
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

    async detectAvailableFields() {
        try {
            console.log('[ENHANCED_LLM] Detecting available fields...');
            
            const fields = {
                context: [],
                task: [],
                inputs: [],
                outputs: []
            };

            // Get post development fields (for Context and Task sections)
            if (this.workflowContext.postId) {
                const devResponse = await fetch(`/api/workflow/posts/${this.workflowContext.postId}/development`);
                if (devResponse.ok) {
                    const devData = await devResponse.json();
                    console.log('[ENHANCED_LLM] Development data loaded:', Object.keys(devData));
                    
                    // Map development fields to sections
                    for (const [fieldName, value] of Object.entries(devData)) {
                        if (value && typeof value === 'string' && value.trim()) {
                            const displayName = this.mapFieldToDisplayName(fieldName);
                            
                            // Categorize fields based on common patterns
                            if (fieldName.includes('idea') || fieldName.includes('scope') || fieldName.includes('seed')) {
                                fields.context.push({
                                    id: fieldName,
                                    name: displayName,
                                    content: value,
                                    type: 'field',
                                    source: 'post_development'
                                });
                            } else if (fieldName.includes('prompt') || fieldName.includes('task')) {
                                fields.task.push({
                                    id: fieldName,
                                    name: displayName,
                                    content: value,
                                    type: 'field',
                                    source: 'post_development'
                                });
                            }
                        }
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
                context: fields.context.length,
                task: fields.task.length,
                inputs: fields.inputs.length,
                outputs: fields.outputs.length
            });

            return fields;
        } catch (error) {
            console.error('[ENHANCED_LLM] Error detecting fields:', error);
            return { context: [], task: [], inputs: [], outputs: [] };
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
        const section = document.getElementById(`${sectionName}-section`);
        if (!section) return;

        // Clear existing content except header
        const header = section.querySelector('h4');
        section.innerHTML = '';
        if (header) section.appendChild(header);

        if (fields.length === 0) {
            const placeholder = document.createElement('div');
            placeholder.className = 'text-sm text-gray-400 italic';
            placeholder.textContent = `No ${sectionName} fields available for current workflow stage.`;
            section.appendChild(placeholder);
            return;
        }

        // Create field elements
        fields.forEach(field => {
            const fieldElement = this.createFieldElement(field);
            section.appendChild(fieldElement);
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

    switchSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.message-section').forEach(section => {
            section.classList.add('hidden');
        });

        // Show selected section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.remove('hidden');
            this.currentSection = sectionName;
            this.updateSummary();
        }
    }

    addInstruction() {
        const template = document.getElementById('instruction-element-template');
        if (!template) return;

        const instructionId = `instruction_${this.instructionCounter++}`;
        const instructionElement = template.content.cloneNode(true);
        const instructionDiv = instructionElement.querySelector('.message-element');
        
        instructionDiv.setAttribute('data-element-id', instructionId);
        instructionDiv.querySelector('.element-content').textContent = 'Enter your instruction here...';

        // Add to current section
        const currentSection = document.getElementById(`${this.currentSection}-section`);
        if (currentSection) {
            currentSection.appendChild(instructionDiv);
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
            
            // Populate each section with real data
            await this.populateSectionWithRealData('context', availableFields.context);
            await this.populateSectionWithRealData('task', availableFields.task);
            await this.populateSectionWithRealData('inputs', availableFields.inputs);
            await this.populateSectionWithRealData('outputs', availableFields.outputs);
            
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

        // Collect all enabled elements from current section
        const enabledElements = [];
        const currentSection = document.getElementById(`${this.currentSection}-section`);
        
        if (currentSection) {
            currentSection.querySelectorAll('.message-element').forEach(element => {
                const toggle = element.querySelector('.element-toggle');
                if (toggle && toggle.checked) {
                    const content = element.querySelector('.element-content');
                    if (content) {
                        enabledElements.push(content.textContent.trim());
                    }
                }
            });
        }

        // Assemble the message
        const message = enabledElements.join('\n\n');
        preview.textContent = message || 'No elements enabled in current section';
        
        // Update character count
        charCount.textContent = message.length;
    }

    updateSummary() {
        const summary = document.getElementById('enhanced-context-summary');
        if (!summary) return;

        const currentSection = document.getElementById(`${this.currentSection}-section`);
        if (!currentSection) return;

        const enabledCount = currentSection.querySelectorAll('.element-toggle:checked').length;
        const totalCount = currentSection.querySelectorAll('.element-toggle').length;
        
        summary.textContent = `${enabledCount} of ${totalCount} elements enabled (${this.currentSection} section)`;
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
            sections: {},
            timestamp: new Date().toISOString()
        };

        // Save each section's configuration
        ['context', 'task', 'inputs', 'outputs'].forEach(sectionName => {
            const section = document.getElementById(`${sectionName}-section`);
            if (section) {
                config.sections[sectionName] = {
                    elements: []
                };

                section.querySelectorAll('.message-element').forEach(element => {
                    const toggle = element.querySelector('.element-toggle');
                    const content = element.querySelector('.element-content');
                    
                    config.sections[sectionName].elements.push({
                        id: element.getAttribute('data-element-id'),
                        type: element.getAttribute('data-element-type'),
                        enabled: toggle ? toggle.checked : true,
                        content: content ? content.textContent : ''
                    });
                });
            }
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
        if (!message || message === 'No elements enabled in current section') {
            alert('Please enable some elements before running the LLM.');
            return;
        }

        // This would integrate with the existing LLM run functionality
        console.log('Running LLM with enhanced message:', message);
        
        // For now, just show an alert
        alert('LLM run functionality would be integrated here with the assembled message.');
    }

    initializeSortable() {
        // Initialize drag & drop for each section
        ['context', 'task', 'inputs', 'outputs'].forEach(sectionName => {
            const section = document.getElementById(`${sectionName}-section`);
            if (section) {
                // Simple drag & drop implementation
                this.setupDragAndDrop(section);
            }
        });
    }

    setupDragAndDrop(container) {
        let draggedElement = null;

        container.addEventListener('dragstart', (e) => {
            if (e.target.classList.contains('message-element')) {
                draggedElement = e.target;
                e.target.style.opacity = '0.5';
            }
        });

        container.addEventListener('dragend', (e) => {
            if (e.target.classList.contains('message-element')) {
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

        // Make elements draggable
        container.querySelectorAll('.message-element').forEach(element => {
            element.draggable = true;
            element.addEventListener('dragstart', () => {
                element.classList.add('dragging');
            });
            element.addEventListener('dragend', () => {
                element.classList.remove('dragging');
            });
        });
    }

    getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.message-element:not(.dragging)')];
        
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
}

// Export for ES6 modules
export default EnhancedLLMMessageManager; 