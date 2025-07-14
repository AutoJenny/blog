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
        console.log('[ENHANCED_LLM] Initializing EnhancedLLMMessageManager...');
        this.modal = document.getElementById('enhanced-llm-message-modal');
        if (!this.modal) {
            console.error('[ENHANCED_LLM] Enhanced LLM Message Modal not found!');
            return;
        }
        console.log('[ENHANCED_LLM] Modal found, setting up event listeners...');

        this.setupEventListeners();
        this.initializeAccordions();
        this.initializeSortable();
        this.loadInstructionsFromStorage();
        this.updatePreview();
        console.log('[ENHANCED_LLM] Initialization complete');
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

        // Test field detection button
        document.getElementById('test-field-detection')?.addEventListener('click', () => {
            this.testFieldDetection();
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

        // Element toggles and field selector changes
        this.modal.addEventListener('change', (e) => {
            if (e.target.classList.contains('element-toggle')) {
                this.updatePreview();
                this.updateSummary();
                this.saveConfiguration();
            }
            
            // Field selector changes - refresh input fields and preview
            if (e.target.classList.contains('field-selector')) {
                console.log('[ENHANCED_LLM] Field selector changed, refreshing input fields...');
                console.log('[ENHANCED_LLM] Selected value:', e.target.value);
                
                // Get the target textarea for this field selector
                const targetId = e.target.getAttribute('data-target');
                const textarea = document.getElementById(targetId);
                
                if (textarea && e.target.value) {
                    console.log('[ENHANCED_LLM] Found target textarea:', targetId);
                    
                    // If this is a section field, get the content directly from section data
                    if (e.target.value === 'ideas_to_include' && this.postSections.length > 0) {
                        const firstSection = this.postSections[0];
                        if (firstSection.ideas_to_include) {
                            console.log('[ENHANCED_LLM] Setting ideas_to_include content directly:', firstSection.ideas_to_include.substring(0, 50) + '...');
                            textarea.value = firstSection.ideas_to_include;
                        }
                    } else if (e.target.value === 'draft' && this.postSections.length > 0) {
                        const firstSection = this.postSections[0];
                        if (firstSection.draft) {
                            console.log('[ENHANCED_LLM] Setting draft content directly:', firstSection.draft.substring(0, 50) + '...');
                            textarea.value = firstSection.draft;
                        }
                    } else if (e.target.value === 'content' && this.postSections.length > 0) {
                        const firstSection = this.postSections[0];
                        if (firstSection.content) {
                            console.log('[ENHANCED_LLM] Setting content directly:', firstSection.content.substring(0, 50) + '...');
                            textarea.value = firstSection.content;
                        }
                    }
                }
                
                // Wait for field selector to update the textarea, then refresh
                setTimeout(() => {
                    console.log('[ENHANCED_LLM] Refreshing after field selector change...');
                    this.updateInputFieldsForSection(this.selectedPostSection);
                    this.updatePreview();
                }, 200); // Longer delay to ensure field selector has updated the textarea
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
        console.log('[ENHANCED_LLM] openModal called!');
        this.modal.classList.remove('hidden');
        
        console.log('[ENHANCED_LLM] Loading workflow context...');
        this.loadWorkflowContext();
        
        console.log('[ENHANCED_LLM] Loading post sections...');
        this.loadPostSections();
        
        console.log('[ENHANCED_LLM] Refreshing context...');
        this.refreshContext();
        
        // Add a small delay to ensure field selectors are populated
        setTimeout(() => {
            console.log('[ENHANCED_LLM] Updating input fields for section:', this.selectedPostSection);
            this.updateInputFieldsForSection(this.selectedPostSection);
            
            console.log('[ENHANCED_LLM] Loading element order...');
            this.loadElementOrder();
            
            console.log('[ENHANCED_LLM] Loading configuration...');
            this.loadConfiguration();
            
            console.log('[ENHANCED_LLM] Updating preview...');
            this.updatePreview();
            
            console.log('[ENHANCED_LLM] Updating summary...');
            this.updateSummary();
        }, 500);
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
                
                // Debug: Show section details
                this.postSections.forEach((section, index) => {
                    console.log(`[ENHANCED_LLM] Section ${index}:`, {
                        id: section.id,
                        title: section.title,
                        hasDraft: !!section.draft,
                        hasContent: !!section.content,
                        hasIdeas: !!section.ideas_to_include,
                        draftLength: section.draft ? section.draft.length : 0,
                        contentLength: section.content ? section.content.length : 0
                    });
                });
            }
        } catch (error) {
            console.error('[ENHANCED_LLM] Error loading post sections:', error);
        }
    }

    // Test method to manually trigger field detection
    async testFieldDetection() {
        console.log('[ENHANCED_LLM] Testing field detection...');
        const fields = await this.detectAvailableFields();
        console.log('[ENHANCED_LLM] Test results:', fields);
        return fields;
    }

    async detectAvailableFields() {
        try {
            console.log('[ENHANCED_LLM] Detecting available fields from purple module dropdowns...');
            
            const fields = {
                inputs: [],
                outputs: []
            };

            // Get LLM settings from the purple panel
            const settingsContent = this.getLLMSettingsContent();
            console.log('[ENHANCED_LLM] Settings content:', settingsContent);
            this.updateAccordionContent('settings', settingsContent);

            // Get system prompt and task prompt from purple module
            const systemPromptTextarea = document.getElementById('system_prompt');
            const taskPromptTextarea = document.getElementById('task_prompt');
            
            if (systemPromptTextarea) {
                const systemContent = systemPromptTextarea.value || '';
                console.log('[ENHANCED_LLM] System prompt content:', systemContent);
                this.updateAccordionContent('system_prompt', systemContent);
            } else {
                console.log('[ENHANCED_LLM] System prompt textarea not found');
            }
            
            if (taskPromptTextarea) {
                const taskContent = taskPromptTextarea.value || '';
                console.log('[ENHANCED_LLM] Task prompt content:', taskContent);
                this.updateAccordionContent('task_prompt', taskContent);
            } else {
                console.log('[ENHANCED_LLM] Task prompt textarea not found');
            }

            // Get basic idea and other context fields from purple module
            const basicIdeaTextarea = document.getElementById('context_basic_idea');
            const sectionHeadingsTextarea = document.getElementById('context_section_headings');
            const ideaScopeTextarea = document.getElementById('context_idea_scope');
            
            if (basicIdeaTextarea) {
                const basicIdeaContent = basicIdeaTextarea.value || '';
                console.log('[ENHANCED_LLM] Basic idea content:', basicIdeaContent);
                this.updateAccordionContent('basic_idea', basicIdeaContent);
            } else {
                console.log('[ENHANCED_LLM] Basic idea textarea not found');
            }
            
            if (sectionHeadingsTextarea) {
                const sectionHeadingsContent = sectionHeadingsTextarea.value || '';
                console.log('[ENHANCED_LLM] Section headings content:', sectionHeadingsContent);
                this.updateAccordionContent('section_headings', sectionHeadingsContent);
            } else {
                console.log('[ENHANCED_LLM] Section headings textarea not found');
            }
            
            if (ideaScopeTextarea) {
                const ideaScopeContent = ideaScopeTextarea.value || '';
                console.log('[ENHANCED_LLM] Idea scope content:', ideaScopeContent);
                this.updateAccordionContent('idea_scope', ideaScopeContent);
            } else {
                console.log('[ENHANCED_LLM] Idea scope textarea not found');
            }

            // Find all input field groups in the purple module
            const inputFieldGroups = document.querySelectorAll('.input-field-group');
            console.log('[ENHANCED_LLM] Found input field groups:', inputFieldGroups.length);
            
            inputFieldGroups.forEach((group, index) => {
                console.log(`[ENHANCED_LLM] Processing input field group ${index}:`, group);
                
                const fieldSelector = group.querySelector('.field-selector[data-section="inputs"]');
                const textarea = group.querySelector('textarea');
                
                console.log(`[ENHANCED_LLM] Field selector found:`, fieldSelector);
                console.log(`[ENHANCED_LLM] Textarea found:`, textarea);
                
                if (fieldSelector && textarea) {
                    const selectedField = fieldSelector.value;
                    const fieldContent = textarea.value;
                    const fieldId = textarea.id;
                    const dataTarget = fieldSelector.getAttribute('data-target');
                    
                    console.log('[ENHANCED_LLM] Input field details:', {
                        id: fieldId,
                        dataTarget: dataTarget,
                        selectedField: selectedField,
                        content: fieldContent ? fieldContent.substring(0, 50) + '...' : 'empty',
                        contentLength: fieldContent ? fieldContent.length : 0,
                        options: Array.from(fieldSelector.options).map(opt => opt.value),
                        textareaId: textarea.id,
                        textareaValue: textarea.value ? textarea.value.substring(0, 50) + '...' : 'empty'
                    });
                    
                    // Use the selected field name if available, otherwise fall back to data-target or fieldId
                    const fieldName = selectedField || dataTarget || fieldId;
                    
                    if (fieldName) {
                        // Get the display name for the selected field
                        const displayName = this.mapFieldToDisplayName(fieldName);
                        
                        // NO FALLBACK CONTENT - ONLY USE TEXTAREA CONTENT
                        let content = fieldContent;
                        
                        fields.inputs.push({
                            id: fieldName,
                            name: displayName,
                            content: content || '',
                            type: 'field',
                            source: 'purple_module',
                            fieldId: fieldId,
                            selectedField: selectedField
                        });
                    }
                }
            });

            // Find all output field groups in the purple module
            const outputFieldGroups = document.querySelectorAll('[data-section="outputs"]');
            console.log('[ENHANCED_LLM] Found output field groups:', outputFieldGroups.length);
            
            outputFieldGroups.forEach((group, index) => {
                console.log(`[ENHANCED_LLM] Processing output field group ${index}:`, group);
                
                const fieldSelector = group.querySelector('.field-selector[data-section="outputs"]');
                const textarea = group.querySelector('textarea');
                
                console.log(`[ENHANCED_LLM] Output field selector found:`, fieldSelector);
                console.log(`[ENHANCED_LLM] Output textarea found:`, textarea);
                
                if (fieldSelector && textarea) {
                    const selectedField = fieldSelector.value;
                    const fieldContent = textarea.value;
                    const fieldId = textarea.id;
                    const dataTarget = fieldSelector.getAttribute('data-target');
                    
                    console.log('[ENHANCED_LLM] Output field details:', {
                        id: fieldId,
                        dataTarget: dataTarget,
                        selectedField: selectedField,
                        content: fieldContent ? fieldContent.substring(0, 50) + '...' : 'empty',
                        options: Array.from(fieldSelector.options).map(opt => opt.value)
                    });
                    
                    // If no field is selected but we have a data-target, use that as the field name
                    const fieldName = selectedField || dataTarget || fieldId;
                    
                    if (fieldName) {
                        fields.outputs.push({
                            id: fieldName,
                            name: this.mapFieldToDisplayName(fieldName),
                            content: fieldContent || '',
                            type: 'field',
                            source: 'purple_module',
                            fieldId: fieldId
                        });
                    }
                }
            });

            // NO FALLBACK CONTENT - ONLY USE SOURCE TEXTAREA ELEMENTS
            console.log('[ENHANCED_LLM] Content check:', {
                totalInputs: fields.inputs.length,
                inputFields: fields.inputs.map(f => ({
                    id: f.id,
                    content: f.content ? f.content.substring(0, 30) + '...' : 'empty',
                    hasContent: f.content && f.content.trim() !== ''
                }))
            });

            console.log('[ENHANCED_LLM] Field detection complete from purple module:', {
                inputs: fields.inputs.length,
                outputs: fields.outputs.length,
                inputFields: fields.inputs.map(f => ({ 
                    id: f.id, 
                    content: f.content ? f.content.substring(0, 50) + '...' : 'empty',
                    source: f.source,
                    hasContent: f.content && f.content.trim() !== ''
                })),
                outputFields: fields.outputs.map(f => ({ 
                    id: f.id, 
                    content: f.content ? f.content.substring(0, 50) + '...' : 'empty',
                    source: f.source,
                    hasContent: f.content && f.content.trim() !== ''
                })),

                postSectionsAvailable: this.postSections.length
            });

            return fields;
        } catch (error) {
            console.error('[ENHANCED_LLM] Error detecting fields from purple module:', error);
            return { inputs: [], outputs: [] };
        }
    }

    updateAccordionContent(elementType, content) {
        console.log(`[ENHANCED_LLM] updateAccordionContent called for ${elementType} with content:`, content ? content.substring(0, 100) + '...' : 'empty');
        
        const accordion = this.modal.querySelector(`[data-element-type="${elementType}"]`);
        if (accordion) {
            console.log(`[ENHANCED_LLM] Found accordion for ${elementType}`);
            const contentDiv = accordion.querySelector('.element-content');
            if (contentDiv) {
                console.log(`[ENHANCED_LLM] Found content div for ${elementType}, setting content`);
                contentDiv.textContent = content;
            } else {
                console.log(`[ENHANCED_LLM] Content div not found for ${elementType}`);
            }
        } else {
            console.log(`[ENHANCED_LLM] Accordion not found for ${elementType}`);
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
        content.textContent = field.content || '';
        
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

        const instructionId = `instruction_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const instructionElement = template.content.cloneNode(true);
        const instructionDiv = instructionElement.querySelector('.message-element');
        
        instructionDiv.setAttribute('data-element-id', instructionId);
        instructionDiv.querySelector('.element-content').textContent = 'Click to edit your instruction...';

        // Add to the all-elements-container (default location)
        const container = document.getElementById('all-elements-container');
        if (container) {
            container.appendChild(instructionDiv);
            
            // Make the new instruction element draggable
            instructionDiv.draggable = true;
            instructionDiv.addEventListener('dragstart', () => {
                instructionDiv.classList.add('dragging');
            });
            instructionDiv.addEventListener('dragend', () => {
                instructionDiv.classList.remove('dragging');
            });
            
            // Immediately start editing the new instruction
            setTimeout(() => {
                this.editElement(instructionDiv);
            }, 100);
            
            this.updatePreview();
            this.updateSummary();
            this.saveInstructionsToStorage();
            this.saveElementOrder();
        }
    }

    editElement(element) {
        const content = element.querySelector('.element-content');
        const currentText = content.textContent;
        
        // Don't edit if already editing
        if (content.parentNode.querySelector('textarea')) return;
        
        // Create textarea for editing
        const textarea = document.createElement('textarea');
        textarea.value = currentText;
        textarea.className = 'w-full bg-gray-800 text-gray-300 text-xs p-2 rounded border border-gray-600 resize-none';
        textarea.rows = 4;
        textarea.placeholder = 'Enter your instruction here...';
        
        // Create character count display
        const charCount = document.createElement('div');
        charCount.className = 'text-xs text-gray-500 mt-1';
        charCount.textContent = `${currentText.length} characters`;
        
        // Create save/cancel buttons
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'flex gap-2 mt-2';
        
        const saveBtn = document.createElement('button');
        saveBtn.className = 'bg-green-600 hover:bg-green-700 text-white px-2 py-1 rounded text-xs';
        saveBtn.textContent = 'Save';
        
        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'bg-gray-600 hover:bg-gray-700 text-white px-2 py-1 rounded text-xs';
        cancelBtn.textContent = 'Cancel';
        
        buttonContainer.appendChild(saveBtn);
        buttonContainer.appendChild(cancelBtn);
        
        // Replace content with editing interface
        content.style.display = 'none';
        content.parentNode.insertBefore(textarea, content);
        content.parentNode.insertBefore(charCount, content.nextSibling);
        content.parentNode.insertBefore(buttonContainer, charCount.nextSibling);
        
        textarea.focus();
        textarea.select();

        // Update character count as user types
        textarea.addEventListener('input', () => {
            charCount.textContent = `${textarea.value.length} characters`;
        });

        // Handle save
        const saveEdit = () => {
            const newText = textarea.value.trim();
            content.textContent = newText || 'Click to edit your instruction...';
            content.style.display = 'block';
            textarea.remove();
            charCount.remove();
            buttonContainer.remove();
            this.updatePreview();
            
            // Save to storage if this is an instruction
            if (element.getAttribute('data-element-type') === 'instruction') {
                this.saveInstructionsToStorage();
            }
        };

        // Handle cancel
        const cancelEdit = () => {
            content.style.display = 'block';
            textarea.remove();
            charCount.remove();
            buttonContainer.remove();
        };

        saveBtn.addEventListener('click', saveEdit);
        cancelBtn.addEventListener('click', cancelEdit);
        
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                e.preventDefault();
                saveEdit();
            } else if (e.key === 'Escape') {
                cancelEdit();
            }
        });
        
        // Auto-save on blur (but only if content changed)
        textarea.addEventListener('blur', () => {
            setTimeout(() => {
                if (textarea.parentNode) { // Still editing
                    if (textarea.value.trim() !== currentText.trim()) {
                        saveEdit();
                    } else {
                        cancelEdit();
                    }
                }
            }, 100);
        });
    }

    removeElement(element) {
        if (element.getAttribute('data-element-type') === 'instruction') {
            element.remove();
            this.updatePreview();
            this.updateSummary();
            this.saveInstructionsToStorage();
            this.saveElementOrder();
        }
    }

    saveInstructionsToStorage() {
        try {
            const instructions = [];
            const instructionElements = this.modal.querySelectorAll('.message-element[data-element-type="instruction"]');
            
            instructionElements.forEach(element => {
                const id = element.getAttribute('data-element-id');
                const content = element.querySelector('.element-content').textContent;
                const isEnabled = element.querySelector('.element-toggle').checked;
                
                instructions.push({
                    id: id,
                    content: content,
                    enabled: isEnabled,
                    timestamp: Date.now()
                });
            });
            
            const storageKey = `llm_instructions_${this.getCurrentStepId()}`;
            localStorage.setItem(storageKey, JSON.stringify(instructions));
            console.log('[ENHANCED_LLM] Saved instructions to storage:', instructions.length);
        } catch (error) {
            console.error('[ENHANCED_LLM] Error saving instructions:', error);
        }
    }

    loadInstructionsFromStorage() {
        try {
            const storageKey = `llm_instructions_${this.getCurrentStepId()}`;
            const stored = localStorage.getItem(storageKey);
            
            if (stored) {
                const instructions = JSON.parse(stored);
                console.log('[ENHANCED_LLM] Loading instructions from storage:', instructions.length);
                
                instructions.forEach(instruction => {
                    this.createInstructionFromStorage(instruction);
                });
            }
        } catch (error) {
            console.error('[ENHANCED_LLM] Error loading instructions:', error);
        }
    }

    createInstructionFromStorage(instructionData) {
        const template = document.getElementById('instruction-element-template');
        if (!template) return;

        const instructionElement = template.content.cloneNode(true);
        const instructionDiv = instructionElement.querySelector('.message-element');
        
        instructionDiv.setAttribute('data-element-id', instructionData.id);
        instructionDiv.querySelector('.element-content').textContent = instructionData.content || 'Click to edit your instruction...';
        instructionDiv.querySelector('.element-toggle').checked = instructionData.enabled !== false;
        
        // Add to the all-elements-container
        const container = document.getElementById('all-elements-container');
        if (container) {
            container.appendChild(instructionDiv);
            
            // Make the loaded instruction element draggable
            instructionDiv.draggable = true;
            instructionDiv.addEventListener('dragstart', () => {
                instructionDiv.classList.add('dragging');
            });
            instructionDiv.addEventListener('dragend', () => {
                instructionDiv.classList.remove('dragging');
            });
        }
    }

    async refreshContext() {
        try {
            console.log('[ENHANCED_LLM] Refreshing context...');
            
            // Reload workflow context
            console.log('[ENHANCED_LLM] Reloading workflow context...');
            await this.loadWorkflowContext();
            
            // Reload post sections
            console.log('[ENHANCED_LLM] Reloading post sections...');
            await this.loadPostSections();
            
            // Detect available fields and populate accordion content
            console.log('[ENHANCED_LLM] Detecting available fields...');
            await this.detectAvailableFields();
            
            // Update input fields for current section
            console.log('[ENHANCED_LLM] Updating input fields for current section:', this.selectedPostSection);
            await this.updateInputFieldsForSection(this.selectedPostSection);
            
            // Update preview and summary
            console.log('[ENHANCED_LLM] Updating preview...');
            this.updatePreview();
            
            console.log('[ENHANCED_LLM] Updating summary...');
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

        // Collect all enabled elements in DOM order (respecting drag & drop positioning)
        const enabledElements = [];
        const container = document.getElementById('all-elements-container');
        if (!container) return;

        // Get all draggable elements in their current order
        const allElements = container.querySelectorAll('.message-accordion, .message-element[data-element-type="instruction"]');
        
        allElements.forEach(element => {
            const toggle = element.querySelector('.element-toggle');
            if (toggle && toggle.checked) {
                const elementType = element.getAttribute('data-element-type');
                
                if (elementType === 'instruction') {
                    // Handle instruction elements
                    const content = element.querySelector('.element-content');
                    if (content && content.textContent.trim() && content.textContent !== 'Click to edit your instruction...') {
                        enabledElements.push({
                            label: 'INSTRUCTION',
                            color: '#10b981', // Green
                            content: content.textContent.trim()
                        });
                    }
                } else {
                    // Handle accordion elements
                    let color = '#60a5fa'; // Default blue
                    let label = elementType.replace('_', ' ').toUpperCase();
                    
                    switch (elementType) {
                        case 'system_prompt':
                            color = '#60a5fa'; // Blue
                            label = 'SYSTEM PROMPT';
                            break;
                        case 'basic_idea':
                            color = '#60a5fa'; // Blue
                            label = 'BASIC IDEA';
                            break;
                        case 'section_headings':
                            color = '#60a5fa'; // Blue
                            label = 'SECTION HEADINGS';
                            break;
                        case 'idea_scope':
                            color = '#60a5fa'; // Blue
                            label = 'IDEA SCOPE';
                            break;
                        case 'task_prompt':
                            color = '#10b981'; // Green
                            label = 'TASK PROMPT';
                            break;
                        case 'inputs':
                            color = '#f59e0b'; // Yellow
                            label = 'INPUT FIELDS';
                            break;
                        case 'settings':
                            color = '#8b5cf6'; // Purple
                            label = 'SETTINGS';
                            break;
                    }
                    
                    // Check if this accordion has individual field elements (like inputs/outputs)
                    const fieldElements = element.querySelectorAll('.message-element');
                    if (fieldElements.length > 0) {
                        // This accordion contains individual field elements
                        let sectionContent = '';
                        fieldElements.forEach(fieldElement => {
                            const fieldToggle = fieldElement.querySelector('.element-toggle');
                            if (fieldToggle && fieldToggle.checked) {
                                const fieldContent = fieldElement.querySelector('.element-content');
                                if (fieldContent && fieldContent.textContent.trim()) {
                                    const fieldLabel = fieldElement.querySelector('.element-label');
                                    const label = fieldLabel ? fieldLabel.textContent : 'Field';
                                    sectionContent += `${label}: ${fieldContent.textContent.trim()}\n`;
                                }
                            }
                        });
                        
                        if (sectionContent.trim()) {
                            enabledElements.push({
                                label: label,
                                color: color,
                                content: sectionContent.trim()
                            });
                        }
                    } else {
                        // This accordion has direct content
                        const content = element.querySelector('.element-content');
                        if (content && content.textContent.trim()) {
                            enabledElements.push({
                                label: label,
                                color: color,
                                content: content.textContent.trim()
                            });
                        }
                    }
                }
            }
        });

        // Assemble the message with colored labels and line returns
        let message = '';
        enabledElements.forEach((element, index) => {
            if (index > 0) {
                message += '<br><br>'; // Add visible line returns before each part
            }
            message += `<span style="color: ${element.color}; font-weight: bold;">=== ${element.label} ===</span><br>${element.content}`;
        });
        
        // If no elements enabled, show empty
        if (enabledElements.length === 0) {
            message = '';
        }
        
        preview.innerHTML = message;
        
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
        
        // Count instruction elements
        const instructionElements = this.modal.querySelectorAll('.message-element[data-element-type="instruction"]');
        instructionElements.forEach(instructionElement => {
            const toggle = instructionElement.querySelector('.element-toggle');
            if (toggle) {
                totalElements++;
                if (toggle.checked) totalEnabled++;
            }
        });
        
        summary.textContent = `${totalEnabled} of ${totalElements} elements enabled`;
    }

    copyPreview() {
        console.log('[ENHANCED_LLM] Copy preview called - using same logic as updatePreview()');
        
        // Use the same content assembly logic as updatePreview() but get content from current workflow context
        const enabledElements = [];
        const container = document.getElementById('all-elements-container');
        if (!container) {
            console.error('[ENHANCED_LLM] Container not found for copy');
            return;
        }

        // Get all draggable elements in their current order
        const allElements = container.querySelectorAll('.message-accordion, .message-element[data-element-type="instruction"]');
        
        allElements.forEach(element => {
            const toggle = element.querySelector('.element-toggle');
            if (toggle && toggle.checked) {
                const elementType = element.getAttribute('data-element-type');
                
                if (elementType === 'instruction') {
                    // Handle instruction elements
                    const content = element.querySelector('.element-content');
                    if (content && content.textContent.trim() && content.textContent !== 'Click to edit your instruction...') {
                        enabledElements.push({
                            label: 'INSTRUCTION',
                            content: content.textContent.trim()
                        });
                    }
                } else {
                    // Handle accordion elements - get content from current workflow context instead of textarea
                    let label = elementType.replace('_', ' ').toUpperCase();
                    
                    switch (elementType) {
                        case 'system_prompt':
                            label = 'SYSTEM PROMPT';
                            break;
                        case 'basic_idea':
                            label = 'BASIC IDEA';
                            break;
                        case 'section_headings':
                            label = 'SECTION HEADINGS';
                            break;
                        case 'idea_scope':
                            label = 'IDEA SCOPE';
                            break;
                        case 'task_prompt':
                            label = 'TASK PROMPT';
                            break;
                        case 'inputs':
                            label = 'INPUT FIELDS';
                            break;
                        case 'settings':
                            label = 'SETTINGS';
                            break;
                    }
                    
                    // Check if this accordion has individual field elements (like inputs/outputs)
                    const fieldElements = element.querySelectorAll('.message-element');
                    if (fieldElements.length > 0) {
                        // This accordion contains individual field elements
                        let sectionContent = '';
                        fieldElements.forEach(fieldElement => {
                            const fieldToggle = fieldElement.querySelector('.element-toggle');
                            if (fieldToggle && fieldToggle.checked) {
                                const fieldContent = fieldElement.querySelector('.element-content');
                                if (fieldContent && fieldContent.textContent.trim()) {
                                    const fieldLabel = fieldElement.querySelector('.element-label');
                                    const label = fieldLabel ? fieldLabel.textContent : 'Field';
                                    sectionContent += `${label}: ${fieldContent.textContent.trim()}\n`;
                                }
                            }
                        });
                        
                        if (sectionContent.trim()) {
                            enabledElements.push({
                                label: label,
                                content: sectionContent.trim()
                            });
                        }
                    } else {
                        // This accordion has direct content - get from current workflow context
                        const content = element.querySelector('.element-content');
                        if (content && content.textContent.trim()) {
                            enabledElements.push({
                                label: label,
                                content: content.textContent.trim()
                            });
                        }
                    }
                }
            }
        });

        // Assemble the message with labels and line returns (plain text version)
        let message = '';
        enabledElements.forEach((element, index) => {
            if (index > 0) {
                message += '\n\n'; // Add line returns before each part
            }
            message += `=== ${element.label} ===\n${element.content}`;
        });
        
        // If no elements enabled, show empty
        if (enabledElements.length === 0) {
            message = '';
        }
        
        console.log('[ENHANCED_LLM] Assembled content for copy:', message ? message.substring(0, 200) + '...' : 'empty');
        
        if (!message || message.trim() === '') {
            alert('No content to copy. Please enable some elements first.');
            return;
        }

        navigator.clipboard.writeText(message).then(() => {
            // Show feedback
            const copyBtn = document.getElementById('copy-preview-btn');
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="fas fa-check mr-1"></i>Copied!';
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
            }, 2000);
            console.log('[ENHANCED_LLM] Content copied to clipboard successfully');
        }).catch(error => {
            console.error('[ENHANCED_LLM] Copy failed:', error);
            alert('Failed to copy content: ' + error.message);
        });
    }

    saveConfiguration() {
        console.log('[ENHANCED_LLM] saveConfiguration called');
        
        // Collect all configuration data
        const config = {
            accordions: {},
            timestamp: new Date().toISOString()
        };

        // Save each accordion's configuration
        const allAccordions = this.modal.querySelectorAll('.message-accordion');
        console.log('[ENHANCED_LLM] Found accordions:', allAccordions.length);
        
        allAccordions.forEach(accordion => {
            const elementType = accordion.getAttribute('data-element-type');
            const toggle = accordion.querySelector('.element-toggle');
            const content = accordion.querySelector('.element-content');
            
            config.accordions[elementType] = {
                enabled: toggle ? toggle.checked : true,
                content: content ? content.textContent : ''
            };
            
            console.log('[ENHANCED_LLM] Saved accordion:', elementType, 'enabled:', config.accordions[elementType].enabled);
        });

        // Save to localStorage for now
        localStorage.setItem('enhanced-llm-config', JSON.stringify(config));
        console.log('[ENHANCED_LLM] Saved config to localStorage');
        
        // Also save the current element order
        console.log('[ENHANCED_LLM] Calling saveElementOrder...');
        this.saveElementOrder();
        
        // Show feedback
        const saveBtn = document.getElementById('save-enhanced-config');
        const originalText = saveBtn.textContent;
        saveBtn.textContent = 'Saved!';
        setTimeout(() => {
            saveBtn.textContent = originalText;
        }, 2000);
        
        console.log('[ENHANCED_LLM] saveConfiguration completed');
    }

    loadConfiguration() {
        console.log('[ENHANCED_LLM] loadConfiguration called');
        try {
            const stored = localStorage.getItem('enhanced-llm-config');
            if (!stored) {
                console.log('[ENHANCED_LLM] No stored configuration found');
                return;
            }

            const config = JSON.parse(stored);
            console.log('[ENHANCED_LLM] Loading configuration:', config);

            // Restore accordion checkbox states
            const allAccordions = this.modal.querySelectorAll('.message-accordion');
            allAccordions.forEach(accordion => {
                const elementType = accordion.getAttribute('data-element-type');
                const toggle = accordion.querySelector('.element-toggle');
                
                if (toggle && config.accordions && config.accordions[elementType]) {
                    const savedState = config.accordions[elementType].enabled;
                    toggle.checked = savedState;
                    console.log('[ENHANCED_LLM] Restored accordion:', elementType, 'enabled:', savedState);
                }
            });

            console.log('[ENHANCED_LLM] Configuration loaded successfully');
        } catch (error) {
            console.error('[ENHANCED_LLM] Error loading configuration:', error);
        }
    }

    runLLM() {
        console.log('[ENHANCED_LLM] Run LLM called - using same logic as updatePreview()');
        
        // Use the same content assembly logic as updatePreview() but get content from current workflow context
        const enabledElements = [];
        const container = document.getElementById('all-elements-container');
        if (!container) {
            console.error('[ENHANCED_LLM] Container not found for LLM run');
            return;
        }

        // Get all draggable elements in their current order
        const allElements = container.querySelectorAll('.message-accordion, .message-element[data-element-type="instruction"]');
        
        allElements.forEach(element => {
            const toggle = element.querySelector('.element-toggle');
            if (toggle && toggle.checked) {
                const elementType = element.getAttribute('data-element-type');
                
                if (elementType === 'instruction') {
                    // Handle instruction elements
                    const content = element.querySelector('.element-content');
                    if (content && content.textContent.trim() && content.textContent !== 'Click to edit your instruction...') {
                        enabledElements.push({
                            label: 'INSTRUCTION',
                            content: content.textContent.trim()
                        });
                    }
                } else {
                    // Handle accordion elements - get content from current workflow context instead of textarea
                    let label = elementType.replace('_', ' ').toUpperCase();
                    
                    switch (elementType) {
                        case 'system_prompt':
                            label = 'SYSTEM PROMPT';
                            break;
                        case 'basic_idea':
                            label = 'BASIC IDEA';
                            break;
                        case 'section_headings':
                            label = 'SECTION HEADINGS';
                            break;
                        case 'idea_scope':
                            label = 'IDEA SCOPE';
                            break;
                        case 'task_prompt':
                            label = 'TASK PROMPT';
                            break;
                        case 'inputs':
                            label = 'INPUT FIELDS';
                            break;
                        case 'settings':
                            label = 'SETTINGS';
                            break;
                    }
                    
                    // Check if this accordion has individual field elements (like inputs/outputs)
                    const fieldElements = element.querySelectorAll('.message-element');
                    if (fieldElements.length > 0) {
                        // This accordion contains individual field elements
                        let sectionContent = '';
                        fieldElements.forEach(fieldElement => {
                            const fieldToggle = fieldElement.querySelector('.element-toggle');
                            if (fieldToggle && fieldToggle.checked) {
                                const fieldContent = fieldElement.querySelector('.element-content');
                                if (fieldContent && fieldContent.textContent.trim()) {
                                    const fieldLabel = fieldElement.querySelector('.element-label');
                                    const label = fieldLabel ? fieldLabel.textContent : 'Field';
                                    sectionContent += `${label}: ${fieldContent.textContent.trim()}\n`;
                                }
                            }
                        });
                        
                        if (sectionContent.trim()) {
                            enabledElements.push({
                                label: label,
                                content: sectionContent.trim()
                            });
                        }
                    } else {
                        // This accordion has direct content - get from current workflow context
                        const content = element.querySelector('.element-content');
                        if (content && content.textContent.trim()) {
                            enabledElements.push({
                                label: label,
                                content: content.textContent.trim()
                            });
                        }
                    }
                }
            }
        });

        // Assemble the message with labels and line returns (plain text version)
        let message = '';
        enabledElements.forEach((element, index) => {
            if (index > 0) {
                message += '\n\n'; // Add line returns before each part
            }
            message += `=== ${element.label} ===\n${element.content}`;
        });
        
        // If no elements enabled, show empty
        if (enabledElements.length === 0) {
            message = '';
        }
        
        console.log('[ENHANCED_LLM] Assembled content for LLM:', message ? message.substring(0, 200) + '...' : 'empty');
        
        if (!message || message.trim() === '') {
            alert('Please enable some elements before running the LLM.');
            return;
        }

        // Get current workflow context
        const pathParts = window.location.pathname.split('/');
        const postId = pathParts[3];
        const stage = pathParts[4];
        const substage = pathParts[5];
        
        // Get current step from panel data
        const panel = document.querySelector('[data-current-stage]');
        const step = panel ? panel.dataset.currentStep : 'section_headings';
        
        console.log('[ENHANCED_LLM] Running LLM with context:', { postId, stage, substage, step });
        
        // Use the existing LLM direct endpoint
        fetch('/api/workflow/llm/direct', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: message,
                post_id: postId,
                step: step
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('[ENHANCED_LLM] LLM response:', data);
            if (data.success) {
                alert('LLM run completed successfully!');
            } else {
                alert('LLM run failed: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('[ENHANCED_LLM] LLM run error:', error);
            alert('LLM run failed: ' + error.message);
        });
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
            if (e.target.classList.contains('message-accordion') || e.target.classList.contains('message-element')) {
                draggedElement = e.target;
                e.target.style.opacity = '0.5';
            }
        });

        container.addEventListener('dragend', (e) => {
            if (e.target.classList.contains('message-accordion') || e.target.classList.contains('message-element')) {
                e.target.style.opacity = '1';
                draggedElement = null;
                
                // Update preview and save order after drag ends
                this.updatePreview();
                this.saveElementOrder();
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

        // Make instruction elements draggable
        this.makeInstructionElementsDraggable();
    }

    makeInstructionElementsDraggable() {
        const container = document.getElementById('all-elements-container');
        if (!container) return;

        // Make existing instruction elements draggable
        container.querySelectorAll('.message-element[data-element-type="instruction"]').forEach(element => {
            element.draggable = true;
            element.addEventListener('dragstart', () => {
                element.classList.add('dragging');
            });
            element.addEventListener('dragend', () => {
                element.classList.remove('dragging');
            });
        });
    }

    saveElementOrder() {
        console.log('[ENHANCED_LLM] saveElementOrder called');
        try {
            const container = document.getElementById('all-elements-container');
            if (!container) {
                console.error('[ENHANCED_LLM] Container not found');
                return;
            }
            console.log('[ENHANCED_LLM] Found container');

            const order = [];
            const allElements = container.querySelectorAll('.message-accordion, .message-element[data-element-type="instruction"]');
            console.log('[ENHANCED_LLM] Found elements:', allElements.length);
            
            allElements.forEach((element, index) => {
                const elementType = element.getAttribute('data-element-type');
                const elementId = element.getAttribute('data-element-id');
                
                order.push({
                    type: elementType,
                    id: elementId,
                    index: index
                });
                
                console.log('[ENHANCED_LLM] Element', index, ':', elementType, 'ID:', elementId);
            });

            const stepId = this.getCurrentStepId();
            const storageKey = `llm_element_order_${stepId}`;
            localStorage.setItem(storageKey, JSON.stringify(order));
            console.log('[ENHANCED_LLM] Saved element order:', order.length, 'elements');
            console.log('[ENHANCED_LLM] Step ID:', stepId);
            console.log('[ENHANCED_LLM] Storage key:', storageKey);
            console.log('[ENHANCED_LLM] Order data:', order);
            console.log('[ENHANCED_LLM] saveElementOrder completed successfully');
        } catch (error) {
            console.error('[ENHANCED_LLM] Error saving element order:', error);
        }
    }

    loadElementOrder() {
        console.log('[ENHANCED_LLM] loadElementOrder called');
        try {
            const stepId = this.getCurrentStepId();
            const storageKey = `llm_element_order_${stepId}`;
            console.log('[ENHANCED_LLM] Looking for storage key:', storageKey);
            const stored = localStorage.getItem(storageKey);
            
            if (stored) {
                const order = JSON.parse(stored);
                console.log('[ENHANCED_LLM] Loading element order:', order.length, 'elements');
                console.log('[ENHANCED_LLM] Step ID:', stepId);
                console.log('[ENHANCED_LLM] Storage key:', storageKey);
                console.log('[ENHANCED_LLM] Order data:', order);
                
                const container = document.getElementById('all-elements-container');
                if (!container) {
                    console.error('[ENHANCED_LLM] Container not found during load');
                    return;
                }
                console.log('[ENHANCED_LLM] Found container for loading');

                // Create a temporary container to hold elements while reordering
                const tempContainer = document.createElement('div');
                
                // Move all elements to temp container first
                const allElements = container.querySelectorAll('.message-accordion, .message-element[data-element-type="instruction"]');
                console.log('[ENHANCED_LLM] Found elements to reorder:', allElements.length);
                allElements.forEach(element => {
                    tempContainer.appendChild(element);
                });
                
                // Reorder elements based on saved order
                order.forEach(item => {
                    let element;
                    if (item.id) {
                        // For elements with IDs (like instructions)
                        element = tempContainer.querySelector(`[data-element-type="${item.type}"][data-element-id="${item.id}"]`);
                    } else {
                        // For elements without IDs (like accordions)
                        element = tempContainer.querySelector(`[data-element-type="${item.type}"]`);
                    }
                    
                    if (element) {
                        container.appendChild(element);
                        console.log('[ENHANCED_LLM] Moved element:', item.type, 'ID:', item.id);
                    } else {
                        console.log('[ENHANCED_LLM] Element not found:', item.type, 'ID:', item.id);
                        // Additional debugging: show what elements are actually available
                        const availableElements = tempContainer.querySelectorAll(`[data-element-type="${item.type}"]`);
                        console.log('[ENHANCED_LLM] Available elements of type', item.type, ':', availableElements.length);
                        availableElements.forEach((el, idx) => {
                            console.log('[ENHANCED_LLM] Available element', idx, ':', el.getAttribute('data-element-type'), 'ID:', el.getAttribute('data-element-id'));
                        });
                    }
                });
                
                // Add any remaining elements that weren't in the saved order
                const remainingElements = tempContainer.querySelectorAll('.message-accordion, .message-element[data-element-type="instruction"]');
                remainingElements.forEach(element => {
                    container.appendChild(element);
                    console.log('[ENHANCED_LLM] Added remaining element:', element.getAttribute('data-element-type'));
                });
                
                console.log('[ENHANCED_LLM] Element order restored');
            } else {
                console.log('[ENHANCED_LLM] No stored order found for key:', storageKey);
            }
        } catch (error) {
            console.error('[ENHANCED_LLM] Error loading element order:', error);
        }
    }

    getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.message-accordion:not(.dragging), .message-element:not(.dragging)')];
        
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
        
        // If no step ID found, use the step name as a fallback
        // This ensures we have a unique storage key even without numeric IDs
        if (panel && panel.dataset.currentStep) {
            return panel.dataset.currentStep;
        }
        
        // Final fallback: use the URL path to create a unique identifier
        const pathParts = window.location.pathname.split('/');
        if (pathParts.length >= 5) {
            return `${pathParts[3]}_${pathParts[4]}_${pathParts[5]}`;
        }
        
        return 'default';
    }

    getSystemPromptContent() {
        // Get system prompt from textarea
        const systemPromptTextarea = document.getElementById('system_prompt');
        if (systemPromptTextarea && systemPromptTextarea.value) {
            console.log('[ENHANCED_LLM] Found system prompt in textarea:', systemPromptTextarea.value.substring(0, 100) + '...');
            return systemPromptTextarea.value;
        }
        
        console.log('[ENHANCED_LLM] No system prompt found in textarea');
        return '';
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
            
            // Since we're now reading directly from the purple module, we don't need section-specific loading
            // Just populate with all input fields from the purple module
            await this.populateInputFieldsWithAllSections();
            
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
            
            // Get available input fields from purple module
            const fields = await this.detectAvailableFields();
            console.log('[ENHANCED_LLM] All available fields from purple module:', {
                inputs: fields.inputs.length,
                outputs: fields.outputs.length
            });
            
            // Show all input fields from purple module
            fields.inputs.forEach(field => {
                console.log('[ENHANCED_LLM] Creating field element for:', field.name, 'with content:', field.content?.substring(0, 50) + '...');
                const fieldElement = this.createFieldElement(field);
                inputContainer.appendChild(fieldElement);
            });
            
            if (fields.inputs.length === 0) {
                console.log('[ENHANCED_LLM] No input fields found in purple module');
            }
            
            console.log('[ENHANCED_LLM] Populated input fields with purple module data');
            
            // Update preview and summary after populating input fields
            this.updatePreview();
            this.updateSummary();
        } catch (error) {
            console.error('[ENHANCED_LLM] Error populating input fields with purple module data:', error);
        }
    }
}

// Export for ES6 modules
export default EnhancedLLMMessageManager; 
