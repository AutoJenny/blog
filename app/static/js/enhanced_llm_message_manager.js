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
        
        // Debug: Check if modal and accordions are properly set up
        setTimeout(() => {
            if (this.modal) {
                const accordions = this.modal.querySelectorAll('.message-accordion');
                const headers = this.modal.querySelectorAll('.accordion-header');
                console.log('[ENHANCED_LLM] Debug: Modal setup complete');
                console.log('[ENHANCED_LLM] Debug: Found', accordions.length, 'accordions');
                console.log('[ENHANCED_LLM] Debug: Found', headers.length, 'accordion headers');
            }
        }, 200);
    }

    setupEventListeners() {
        // Modal open/close
        document.getElementById('close-enhanced-modal')?.addEventListener('click', () => {
            this.closeModal();
        });

        // ESC key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal && !this.modal.classList.contains('hidden')) {
                this.closeModal();
            }
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

        // Test accordions button
        document.getElementById('test-accordions-btn')?.addEventListener('click', () => {
            this.testAccordions();
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
            // Check if click is on accordion header or its children
            if (e.target.closest('.accordion-header') || e.target.classList.contains('accordion-toggle')) {
                const accordion = e.target.closest('.message-accordion');
                if (accordion) {
                    console.log('[ENHANCED_LLM] Accordion clicked:', accordion.dataset.elementType);
                    this.toggleAccordion(accordion);
                }
            }
        });
        
        // Also add direct click handlers to accordion headers for better reliability
        setTimeout(() => {
            const accordionHeaders = this.modal.querySelectorAll('.accordion-header');
            accordionHeaders.forEach(header => {
                header.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const accordion = header.closest('.message-accordion');
                    if (accordion) {
                        console.log('[ENHANCED_LLM] Direct accordion header click:', accordion.dataset.elementType);
                        this.toggleAccordion(accordion);
                    }
                });
            });
            console.log('[ENHANCED_LLM] Added direct click handlers to', accordionHeaders.length, 'accordion headers');
        }, 100);
    }

    toggleAccordion(accordion) {
        const content = accordion.querySelector('.accordion-content');
        const toggle = accordion.querySelector('.accordion-toggle');
        
        if (!content || !toggle) {
            console.error('[ENHANCED_LLM] Missing content or toggle element for accordion');
            return;
        }
        
        const isHidden = content.classList.contains('hidden');
        console.log('[ENHANCED_LLM] Toggling accordion:', accordion.dataset.elementType, 'isHidden:', isHidden);
        
        if (isHidden) {
            content.classList.remove('hidden');
            toggle.textContent = '▲';
            // Fix: Ensure the content is visible by setting proper opacity
            content.style.opacity = '1';
            console.log('[ENHANCED_LLM] Accordion expanded:', accordion.dataset.elementType);
        } else {
            content.classList.add('hidden');
            toggle.textContent = '▼';
            console.log('[ENHANCED_LLM] Accordion collapsed:', accordion.dataset.elementType);
        }
    }

    async openModal() {
        console.log('[ENHANCED_LLM] openModal called!');
        this.modal.classList.remove('hidden');
        
        console.log('[ENHANCED_LLM] Loading workflow context...');
        await this.loadWorkflowContext();
        
        console.log('[ENHANCED_LLM] Loading post sections...');
        await this.loadPostSections();
        
        // Wait for field selectors to be initialized before reading content
        console.log('[ENHANCED_LLM] Waiting for field selectors to be ready...');
        await this.waitForFieldSelectorsReady();
        
        console.log('[ENHANCED_LLM] Refreshing context...');
        await this.refreshContext();
        
        // Add a small delay to ensure field selectors are populated
        setTimeout(async () => {
            console.log('[ENHANCED_LLM] Updating input fields for section:', this.selectedPostSection);
            await this.updateInputFieldsForSection(this.selectedPostSection);
            
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

    async waitForFieldSelectorsReady() {
        console.log('[ENHANCED_LLM] Waiting for field selectors to be ready...');
        
        // Wait for the FieldSelector to be initialized
        let attempts = 0;
        const maxAttempts = 50; // 5 seconds max wait
        
        while (attempts < maxAttempts) {
            // Check if field selectors have been populated
            const fieldSelectors = document.querySelectorAll('.field-selector');
            const hasPopulatedSelectors = Array.from(fieldSelectors).some(selector => {
                return selector.options.length > 1; // More than just the default "Select field..." option
            });
            
            if (hasPopulatedSelectors) {
                console.log('[ENHANCED_LLM] Field selectors are ready!');
                return;
            }
            
            // Check if FieldSelector is initialized
            if (window.fieldSelector && window.fieldSelector.initialized) {
                console.log('[ENHANCED_LLM] FieldSelector is initialized, waiting for content...');
                // Give a bit more time for content to load
                await new Promise(resolve => setTimeout(resolve, 200));
                return;
            }
            
            console.log(`[ENHANCED_LLM] Waiting for field selectors... (attempt ${attempts + 1}/${maxAttempts})`);
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        console.warn('[ENHANCED_LLM] Field selectors not ready after timeout, proceeding anyway...');
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

    // Test method to manually test accordion functionality
    testAccordions() {
        console.log('[ENHANCED_LLM] Testing accordion functionality...');
        
        const accordions = this.modal.querySelectorAll('.message-accordion');
        console.log('[ENHANCED_LLM] Found', accordions.length, 'accordions');
        
        accordions.forEach((accordion, index) => {
            const elementType = accordion.dataset.elementType;
            const content = accordion.querySelector('.accordion-content');
            const toggle = accordion.querySelector('.accordion-toggle');
            const header = accordion.querySelector('.accordion-header');
            const elementContent = accordion.querySelector('.element-content');
            
            console.log(`[ENHANCED_LLM] Accordion ${index}:`, {
                elementType,
                hasContent: !!content,
                hasToggle: !!toggle,
                hasHeader: !!header,
                hasElementContent: !!elementContent,
                isHidden: content ? content.classList.contains('hidden') : 'N/A',
                toggleText: toggle ? toggle.textContent : 'N/A',
                contentText: elementContent ? elementContent.textContent.substring(0, 100) + '...' : 'N/A'
            });
            
            // Test clicking the first accordion
            if (index === 0 && header) {
                console.log('[ENHANCED_LLM] Testing click on first accordion...');
                header.click();
            }
        });
        
        // Also test field selector status
        console.log('[ENHANCED_LLM] Field selector status:');
        console.log('[ENHANCED_LLM] - window.fieldSelector exists:', !!window.fieldSelector);
        console.log('[ENHANCED_LLM] - window.fieldSelector.initialized:', window.fieldSelector ? window.fieldSelector.initialized : 'N/A');
        
        const fieldSelectors = document.querySelectorAll('.field-selector');
        console.log('[ENHANCED_LLM] - Field selectors found:', fieldSelectors.length);
        fieldSelectors.forEach((selector, index) => {
            console.log(`[ENHANCED_LLM] - Selector ${index}:`, {
                options: selector.options.length,
                value: selector.value,
                section: selector.dataset.section,
                target: selector.dataset.target
            });
        });
    }

    async detectAvailableFields() {
        const fields = {
            inputs: [],
            outputs: []
        };

        console.log('[ENHANCED_LLM] Starting field detection...');

        // Get post_development data from API for context fields
        const postId = this.getCurrentPostId();
        let postDevelopmentData = null;
        
        try {
            const response = await fetch(`/api/workflow/posts/${postId}/fields`);
            if (response.ok) {
                postDevelopmentData = await response.json();
                console.log('[ENHANCED_LLM] Post development data loaded:', Object.keys(postDevelopmentData));
            } else {
                console.log('[ENHANCED_LLM] Failed to load post development data:', response.status);
            }
        } catch (error) {
            console.error('[ENHANCED_LLM] Error loading post development data:', error);
        }

        // Handle basic_idea from post_development API
        if (postDevelopmentData && postDevelopmentData.basic_idea) {
            const basicIdeaContent = postDevelopmentData.basic_idea;
            console.log('[ENHANCED_LLM] Basic idea content length:', basicIdeaContent.length);
            this.updateAccordionContent('basic_idea', basicIdeaContent || 'No content available');
            if (basicIdeaContent.trim()) {
                fields.inputs.push({
                    id: 'basic_idea',
                    name: this.mapFieldToDisplayName('basic_idea'),
                    content: basicIdeaContent,
                    source: 'post_development'
                });
            }
        } else {
            console.log('[ENHANCED_LLM] Basic idea not found in post_development data');
            this.updateAccordionContent('basic_idea', 'Field not available');
        }

        // Handle idea_scope from post_development API
        console.log('[ENHANCED_LLM] Checking idea_scope:', {
            hasPostData: !!postDevelopmentData,
            hasIdeaScope: !!(postDevelopmentData && postDevelopmentData.idea_scope),
            ideaScopeValue: postDevelopmentData ? postDevelopmentData.idea_scope : 'undefined',
            ideaScopeType: postDevelopmentData ? typeof postDevelopmentData.idea_scope : 'undefined'
        });
        
        if (postDevelopmentData && postDevelopmentData.idea_scope !== null && postDevelopmentData.idea_scope !== undefined) {
            const ideaScopeContent = postDevelopmentData.idea_scope;
            console.log('[ENHANCED_LLM] Idea scope content length:', ideaScopeContent.length);
            console.log('[ENHANCED_LLM] Idea scope content preview:', ideaScopeContent.substring(0, 100));
            this.updateAccordionContent('idea_scope', ideaScopeContent || 'No content available');
            if (ideaScopeContent.trim()) {
                fields.inputs.push({
                    id: 'idea_scope',
                    name: this.mapFieldToDisplayName('idea_scope'),
                    content: ideaScopeContent,
                    source: 'post_development'
                });
            }
        } else {
            console.log('[ENHANCED_LLM] Idea scope not found in post_development data');
            this.updateAccordionContent('idea_scope', 'Field not available');
        }

        // Handle section_headings from post_development API
        console.log('[ENHANCED_LLM] Checking section_headings:', {
            hasPostData: !!postDevelopmentData,
            hasSectionHeadings: !!(postDevelopmentData && postDevelopmentData.section_headings),
            sectionHeadingsValue: postDevelopmentData ? postDevelopmentData.section_headings : 'undefined',
            sectionHeadingsType: postDevelopmentData ? typeof postDevelopmentData.section_headings : 'undefined'
        });
        
        if (postDevelopmentData && postDevelopmentData.section_headings !== null && postDevelopmentData.section_headings !== undefined) {
            const sectionHeadingsContent = postDevelopmentData.section_headings;
            console.log('[ENHANCED_LLM] Section headings content length:', sectionHeadingsContent.length);
            console.log('[ENHANCED_LLM] Section headings content preview:', sectionHeadingsContent.substring(0, 100));
            this.updateAccordionContent('section_headings', sectionHeadingsContent || 'No content available');
            if (sectionHeadingsContent.trim()) {
                fields.inputs.push({
                    id: 'section_headings',
                    name: this.mapFieldToDisplayName('section_headings'),
                    content: sectionHeadingsContent,
                    source: 'post_development'
                });
            }
        } else {
            console.log('[ENHANCED_LLM] Section headings not found in post_development data');
            this.updateAccordionContent('section_headings', 'Field not available');
        }

        // Get LLM settings from the purple panel
        const settingsContent = this.getLLMSettingsContent();
        console.log('[ENHANCED_LLM] Settings content:', settingsContent);
        this.updateAccordionContent('settings', settingsContent);

        // Get system prompt and task prompt using the EXACT SAME API call as PromptSelector
        const systemContent = await this.getSystemPromptContent();
        console.log('[ENHANCED_LLM] System prompt content length:', systemContent.length);
        this.updateAccordionContent('system_prompt', systemContent || 'No system prompt set');
        
        const taskContent = await this.getTaskPromptContent();
        console.log('[ENHANCED_LLM] Task prompt content length:', taskContent.length);
        this.updateAccordionContent('task_prompt', taskContent || 'No task prompt set');

        // Find all input field groups in the purple module
        const inputFieldGroups = document.querySelectorAll('.input-field-group');
        console.log('[ENHANCED_LLM] Found input field groups:', inputFieldGroups.length);
        
        if (inputFieldGroups.length === 0) {
            console.log('[ENHANCED_LLM] No input field groups found, checking for alternative selectors...');
            // Try alternative selectors
            const alternativeInputs = document.querySelectorAll('[data-section="inputs"]');
            console.log('[ENHANCED_LLM] Alternative inputs found:', alternativeInputs.length);
        }
        
        inputFieldGroups.forEach((group, index) => {
            console.log(`[ENHANCED_LLM] Processing input field group ${index}:`, group);
            
            const fieldSelector = group.querySelector('.field-selector[data-section="inputs"]');
            const textarea = group.querySelector('textarea');
            
            console.log(`[ENHANCED_LLM] Field selector found:`, !!fieldSelector);
            console.log(`[ENHANCED_LLM] Textarea found:`, !!textarea);
            
            if (fieldSelector && textarea) {
                const selectedField = fieldSelector.value;
                const fieldContent = textarea.value;
                const fieldId = textarea.id;
                const dataTarget = fieldSelector.getAttribute('data-target');
                
                console.log('[ENHANCED_LLM] Input field details:', {
                    id: fieldId,
                    dataTarget: dataTarget,
                    selectedField: selectedField,
                    contentLength: fieldContent ? fieldContent.length : 0,
                    hasContent: fieldContent && fieldContent.trim() !== '',
                    optionsCount: fieldSelector.options.length,
                    textareaId: textarea.id
                });
                
                // Use the selected field name if available, otherwise fall back to data-target or fieldId
                const fieldName = selectedField || dataTarget || fieldId;
                
                if (fieldName) {
                    // Get the display name for the selected field
                    const displayName = this.mapFieldToDisplayName(fieldName);
                    
                    // Show content or placeholder
                    let content = fieldContent;
                    if (!content || content.trim() === '') {
                        content = selectedField ? `Field "${displayName}" selected but no content available` : 'No field selected';
                    }
                    
                    fields.inputs.push({
                        id: fieldName,
                        name: displayName,
                        content: content,
                        type: 'field',
                        source: 'purple_module',
                        fieldId: fieldId,
                        selectedField: selectedField
                    });
                }
            } else {
                console.log(`[ENHANCED_LLM] Input field group ${index} missing required elements`);
            }
        });

        // Find all output field groups in the purple module
        const outputFieldGroups = document.querySelectorAll('[data-section="outputs"]');
        console.log('[ENHANCED_LLM] Found output field groups:', outputFieldGroups.length);
        
        outputFieldGroups.forEach((group, index) => {
            console.log(`[ENHANCED_LLM] Processing output field group ${index}:`, group);
            
            const fieldSelector = group.querySelector('.field-selector[data-section="outputs"]');
            const textarea = group.querySelector('textarea');
            
            console.log(`[ENHANCED_LLM] Output field selector found:`, !!fieldSelector);
            console.log(`[ENHANCED_LLM] Output textarea found:`, !!textarea);
            
            if (fieldSelector && textarea) {
                const selectedField = fieldSelector.value;
                const fieldContent = textarea.value;
                const fieldId = textarea.id;
                const dataTarget = fieldSelector.getAttribute('data-target');
                
                console.log('[ENHANCED_LLM] Output field details:', {
                    id: fieldId,
                    dataTarget: dataTarget,
                    selectedField: selectedField,
                    contentLength: fieldContent ? fieldContent.length : 0,
                    hasContent: fieldContent && fieldContent.trim() !== '',
                    optionsCount: fieldSelector.options.length
                });
                
                // If no field is selected but we have a data-target, use that as the field name
                const fieldName = selectedField || dataTarget || fieldId;
                
                if (fieldName) {
                    // Show content or placeholder
                    let content = fieldContent;
                    if (!content || content.trim() === '') {
                        content = selectedField ? `Field "${this.mapFieldToDisplayName(fieldName)}" selected but no content available` : 'No field selected';
                    }
                    
                    fields.outputs.push({
                        id: fieldName,
                        name: this.mapFieldToDisplayName(fieldName),
                        content: content,
                        type: 'field',
                        source: 'purple_module',
                        fieldId: fieldId
                    });
                }
            } else {
                console.log(`[ENHANCED_LLM] Output field group ${index} missing required elements`);
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
    }

    updateAccordionContent(elementType, content) {
        console.log(`[ENHANCED_LLM] updateAccordionContent called for ${elementType} with content length:`, content ? content.length : 0);
        console.log(`[ENHANCED_LLM] Content preview:`, content ? content.substring(0, 100) + '...' : 'null');
        
        const accordion = this.modal.querySelector(`[data-element-type="${elementType}"]`);
        if (accordion) {
            console.log(`[ENHANCED_LLM] Found accordion for ${elementType}`);
            const contentDiv = accordion.querySelector('.element-content');
            if (contentDiv) {
                console.log(`[ENHANCED_LLM] Found content div for ${elementType}, setting content`);
                console.log(`[ENHANCED_LLM] Content div before setting:`, contentDiv.textContent.substring(0, 50) + '...');
                contentDiv.textContent = content;
                console.log(`[ENHANCED_LLM] Content set for ${elementType}, new content length:`, contentDiv.textContent.length);
                console.log(`[ENHANCED_LLM] Content div after setting:`, contentDiv.textContent.substring(0, 100) + '...');
                
                // Verify the content was actually set
                setTimeout(() => {
                    console.log(`[ENHANCED_LLM] Content verification for ${elementType}:`, contentDiv.textContent.substring(0, 100) + '...');
                }, 100);
            } else {
                console.log(`[ENHANCED_LLM] Content div not found for ${elementType}`);
                console.log(`[ENHANCED_LLM] Accordion HTML:`, accordion.innerHTML.substring(0, 200) + '...');
            }
        } else {
            console.log(`[ENHANCED_LLM] Accordion not found for ${elementType}`);
            console.log(`[ENHANCED_LLM] Available accordions:`, Array.from(this.modal.querySelectorAll('.message-accordion')).map(a => a.dataset.elementType));
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
                        let fieldCount = 0;
                        fieldElements.forEach(fieldElement => {
                            const fieldToggle = fieldElement.querySelector('.element-toggle');
                            if (fieldToggle && fieldToggle.checked) {
                                const fieldContent = fieldElement.querySelector('.element-content');
                                if (fieldContent && fieldContent.textContent.trim()) {
                                    const fieldLabel = fieldElement.querySelector('.element-label');
                                    const label = fieldLabel ? fieldLabel.textContent : 'Field';
                                    
                                    // Add line break before each field (except the first one)
                                    if (fieldCount > 0) {
                                        sectionContent += '\n';
                                    }
                                    
                                    sectionContent += `${label}: ${fieldContent.textContent.trim()}`;
                                    fieldCount++;
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
                        let fieldCount = 0;
                        fieldElements.forEach(fieldElement => {
                            const fieldToggle = fieldElement.querySelector('.element-toggle');
                            if (fieldToggle && fieldToggle.checked) {
                                const fieldContent = fieldElement.querySelector('.element-content');
                                if (fieldContent && fieldContent.textContent.trim()) {
                                    const fieldLabel = fieldElement.querySelector('.element-label');
                                    const label = fieldLabel ? fieldLabel.textContent : 'Field';
                                    
                                    // Add line break before each field (except the first one)
                                    if (fieldCount > 0) {
                                        sectionContent += '\n';
                                    }
                                    
                                    sectionContent += `${label}: ${fieldContent.textContent.trim()}`;
                                    fieldCount++;
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

    async runLLM() {
        console.log('[ENHANCED_LLM] Run LLM called');
        
        // First, ensure we have the necessary context loaded
        if (!this.workflowContext.postId) {
            console.log('[ENHANCED_LLM] Loading workflow context for LLM run...');
            await this.loadWorkflowContext();
        }
        
        if (!this.postSections.length) {
            console.log('[ENHANCED_LLM] Loading post sections for LLM run...');
            await this.loadPostSections();
        }
        
        // Check if modal elements exist, if not, we need to run without modal
        const container = document.getElementById('all-elements-container');
        if (!container) {
            console.log('[ENHANCED_LLM] Modal not open, running LLM with direct context assembly...');
            return this.runLLMWithoutModal();
        }

        // Use the same content assembly logic as updatePreview() but get content from current workflow context
        const enabledElements = [];
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
                        let fieldCount = 0;
                        fieldElements.forEach(fieldElement => {
                            const fieldToggle = fieldElement.querySelector('.element-toggle');
                            if (fieldToggle && fieldToggle.checked) {
                                const fieldContent = fieldElement.querySelector('.element-content');
                                if (fieldContent && fieldContent.textContent.trim()) {
                                    const fieldLabel = fieldElement.querySelector('.element-label');
                                    const label = fieldLabel ? fieldLabel.textContent : 'Field';
                                    
                                    // Add line break before each field (except the first one)
                                    if (fieldCount > 0) {
                                        sectionContent += '\n';
                                    }
                                    
                                    sectionContent += `${label}: ${fieldContent.textContent.trim()}`;
                                    fieldCount++;
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
            return { success: false, error: 'No content to send to LLM' };
        }

        return this.executeLLMRequest(message);
    }

    async runLLMWithoutModal() {
        console.log('[ENHANCED_LLM] Running LLM without modal - opening modal to get content...');
        
        // Get current workflow context
        const pathParts = window.location.pathname.split('/');
        const postId = pathParts[3];
        const stage = pathParts[4];
        const substage = pathParts[5];
        
        // Get current step from panel data
        const panel = document.querySelector('[data-current-stage]');
        const step = panel ? panel.dataset.currentStep : 'section_headings';
        
        console.log('[ENHANCED_LLM] Running LLM with context:', { postId, stage, substage, step });
        
        // Always open the modal to get the correct content
        try {
            console.log('[ENHANCED_LLM] Opening modal to get content...');
            
            // Open the modal to load content
            this.openModal();
            
            // Wait for the modal to fully load content
            await this.waitForModalContent();
            
            // Get the content from the modal
            const message = this.getAssembledContent();
            
            console.log('[ENHANCED_LLM] Got content from modal:', message ? message.substring(0, 200) + '...' : 'empty');
            
            // Close the modal
            this.closeModal();
            
            if (!message || message.trim() === '') {
                alert('No content available to send to LLM. Please configure content in the LLM Message Manager.');
                return { success: false, error: 'No content available' };
            }
            
            console.log('[ENHANCED_LLM] Final assembled content for LLM:', message.substring(0, 200) + '...');
            
            return this.executeLLMRequest(message);
            
        } catch (error) {
            console.error('[ENHANCED_LLM] Error loading modal content:', error);
            alert('Failed to load LLM content. Please open the LLM Message Manager manually and try again.');
            return { success: false, error: 'Failed to load modal content: ' + error.message };
        }
    }

    async waitForModalContent() {
        console.log('[ENHANCED_LLM] Waiting for modal content to load...');
        
        // Wait for the modal to be visible
        let attempts = 0;
        const maxAttempts = 20; // 2 seconds total
        
        while (attempts < maxAttempts) {
            const modal = document.getElementById('enhanced-llm-message-modal');
            if (modal && !modal.classList.contains('hidden')) {
                console.log('[ENHANCED_LLM] Modal is visible, waiting for content...');
                break;
            }
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        if (attempts >= maxAttempts) {
            throw new Error('Modal failed to open');
        }
        
        // Wait for content to be loaded
        attempts = 0;
        while (attempts < maxAttempts) {
            const container = document.getElementById('all-elements-container');
            if (container && container.children.length > 0) {
                console.log('[ENHANCED_LLM] Modal content loaded');
                return;
            }
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        throw new Error('Modal content failed to load');
    }

    getDefaultContentFromWorkflow() {
        console.log('[ENHANCED_LLM] Getting default content from workflow context...');
        
        // Create a basic prompt based on the current workflow context
        const pathParts = window.location.pathname.split('/');
        const postId = pathParts[3];
        const stage = pathParts[4];
        const substage = pathParts[5];
        
        // Get current step from panel data
        const panel = document.querySelector('[data-current-stage]');
        const step = panel ? panel.dataset.currentStep : 'section_headings';
        
        // Create a basic system prompt and task prompt based on the step
        let systemPrompt = "You are an expert in Scottish history, culture, and traditions. You have deep knowledge of clan history, tartans, kilts, quaichs, and other aspects of Scottish heritage. You write in a clear, engaging style that balances historical accuracy with accessibility for a general audience.";
        
        let taskPrompt = "";
        switch (step) {
            case 'section_headings':
                taskPrompt = "Review all the content in the inputs above, and consider how to structure this into a blog article with around 5-8 sections. The sections should flow logically and build upon each other to tell a complete story. Create a structured outline for a blog post with the following details:\nPlease provide a JSON array of sections, where each section has:\n- title: A clear, engaging section heading\n- description: The main theme or focus of this section\nDO NOT include any introduction or conclusions, or comment at all. ONLY title and describe the sections for the article.";
                break;
            case 'basic_idea':
                taskPrompt = "Create a compelling basic idea for a Scottish heritage blog post based on the available context.";
                break;
            case 'idea_scope':
                taskPrompt = "Define the scope and structure for a Scottish heritage blog post based on the available context.";
                break;
            default:
                taskPrompt = "Create content for the current workflow step based on the available context.";
        }
        
        const settings = "Model: llama3.2:latest, Temperature: 0.7, Max Tokens: 1000, Timeout: 360s";
        
        const message = `=== SYSTEM PROMPT ===\n${systemPrompt}\n\n=== TASK PROMPT ===\n${taskPrompt}\n\n=== SETTINGS ===\n${settings}`;
        
        console.log('[ENHANCED_LLM] Created default content:', message.substring(0, 200) + '...');
        return message;
    }

    getSelectedSectionIds() {
        const checkboxes = Array.from(document.querySelectorAll('.section-select-checkbox'));
        return checkboxes
            .filter(cb => cb.checked)
            .map(cb => parseInt(cb.dataset.sectionId))
            .filter(id => !isNaN(id));
    }

    getOutputFieldMapping() {
        // Get output field selection from purple panel
        const outputSelector = document.querySelector('select[data-section="outputs"]');
        if (!outputSelector || !outputSelector.value) {
            throw new Error('No output field selected');
        }
        
        // Get field info from field selector
        const fieldInfo = window.fieldSelector?.fields?.[outputSelector.value];
        if (!fieldInfo) {
            throw new Error('Output field not found in field mapping');
        }
        
        return {
            field: fieldInfo.db_field,
            table: fieldInfo.db_table,
            display_name: fieldInfo.display_name
        };
    }

    async executeLLMRequest(message) {
        const pathParts = window.location.pathname.split('/');
        const postId = pathParts[3];
        const stage = pathParts[4];
        const substage = pathParts[5];
        
        const panel = document.querySelector('[data-current-stage]');
        const step = panel ? panel.dataset.currentStep : 'section_headings';
        
        // Get selected sections and output field mapping
        const selectedSectionIds = this.getSelectedSectionIds();
        const outputMapping = this.getOutputFieldMapping();
        
        if (selectedSectionIds.length === 0) {
            throw new Error('No sections selected for processing');
        }
        
        console.log('[ENHANCED_LLM] Processing sections:', selectedSectionIds);
        console.log('[ENHANCED_LLM] Output mapping:', outputMapping);
        
        // Show loading state
        const runBtn = document.getElementById('run-llm-btn');
        if (runBtn) {
            runBtn.textContent = `Processing ${selectedSectionIds.length} sections...`;
            runBtn.disabled = true;
        }
        
        try {
            // Use Writing stage endpoint for section-specific processing
            const response = await fetch(`/api/workflow/posts/${postId}/${stage}/${substage}/writing_llm`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    step: step,
                    selected_section_ids: selectedSectionIds,
                    inputs: {
                        prompt: message,
                        output_field: outputMapping.field,
                        output_table: outputMapping.table
                    }
                })
            });

            const data = await response.json();
            
            if (data.success) {
                alert(`LLM processing completed! Processed ${data.parameters.sections_processed.length} sections.`);
            } else {
                throw new Error(data.error || 'Unknown error');
            }
            
            return data;
        } catch (error) {
            console.error('[ENHANCED_LLM] LLM run error:', error);
            alert('LLM run failed: ' + error.message);
            throw error;
        } finally {
            if (runBtn) {
                runBtn.textContent = 'Run LLM';
                runBtn.disabled = false;
            }
        }
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

    getCurrentPostId() {
        // Extract post ID from URL path: /workflow/posts/{post_id}/...
        const pathParts = window.location.pathname.split('/');
        if (pathParts.length >= 4 && pathParts[1] === 'workflow' && pathParts[2] === 'posts') {
            const postId = pathParts[3];
            console.log('[ENHANCED_LLM] Extracted post ID from URL:', postId);
            return postId;
        }
        
        // Fallback: try to get from panel data
        const panel = document.querySelector('[data-current-stage]');
        if (panel && panel.dataset.postId) {
            console.log('[ENHANCED_LLM] Got post ID from panel data:', panel.dataset.postId);
            return panel.dataset.postId;
        }
        
        console.warn('[ENHANCED_LLM] Could not determine post ID from URL or panel data');
        return null;
    }

    async getSystemPromptContent() {
        // Use the EXACT SAME API call as PromptSelector
        try {
            const stepId = this.getCurrentStepId();
            if (!stepId) {
                console.log('[ENHANCED_LLM] No step ID available for system prompt');
                return '';
            }
            
            console.log('[ENHANCED_LLM] Fetching system prompt from API for step:', stepId);
            const response = await fetch(`/api/workflow/steps/${stepId}/prompts`);
            console.log('[ENHANCED_LLM] API response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const prompts = await response.json();
            console.log('[ENHANCED_LLM] API response keys:', Object.keys(prompts));
            
            const content = prompts.system_prompt_content || '';
            console.log('[ENHANCED_LLM] System prompt content from API length:', content.length);
            console.log('[ENHANCED_LLM] System prompt content preview:', content.substring(0, 100) + '...');
            return content;
        } catch (error) {
            console.error('[ENHANCED_LLM] Error fetching system prompt from API:', error);
            return '';
        }
    }

    async getTaskPromptContent() {
        // Use the EXACT SAME API call as PromptSelector
        try {
            const stepId = this.getCurrentStepId();
            if (!stepId) {
                console.log('[ENHANCED_LLM] No step ID available for task prompt');
                return '';
            }
            
            console.log('[ENHANCED_LLM] Fetching task prompt from API for step:', stepId);
            const response = await fetch(`/api/workflow/steps/${stepId}/prompts`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const prompts = await response.json();
            
            const content = prompts.task_prompt_content || '';
            console.log('[ENHANCED_LLM] Task prompt content from API length:', content.length);
            return content;
        } catch (error) {
            console.error('[ENHANCED_LLM] Error fetching task prompt from API:', error);
            return '';
        }
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
            
            if (!sectionId) {
                console.log('[ENHANCED_LLM] No section ID provided, using purple module data');
                await this.populateInputFieldsWithAllSections();
                return;
            }
            
            // Load section-specific data
            const sectionData = await this.getSectionSpecificContent(sectionId);
            console.log('[ENHANCED_LLM] Loaded section data:', Object.keys(sectionData));
            
            // Update input fields with section-specific data
            await this.populateInputFieldsWithSectionData(sectionData);
            
        } catch (error) {
            console.error('[ENHANCED_LLM] Error updating input fields for section:', error);
        }
    }

    mapFieldNameToApiField(fieldName) {
        // Map purple module field names to API response field names
        const fieldMapping = {
            'section_heading': 'title',
            'section_description': 'description',
            'ideas_to_include': 'ideas_to_include',
            'facts_to_include': 'facts_to_include',
            'image_prompts': 'image_prompts',
            'image_captions': 'image_captions',
            'image_concepts': 'image_concepts',
            'image_meta_descriptions': 'image_meta_descriptions',
            'draft': 'draft',
            'polished': 'polished',
            'content': 'content',
            'highlighting': 'highlighting',
            'watermarking': 'watermarking'
        };
        
        return fieldMapping[fieldName] || fieldName;
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
            
            // Don't call detectAvailableFields again - it's already been called in refreshContext
            // and the accordion content has already been set
            console.log('[ENHANCED_LLM] Skipping detectAvailableFields call to preserve accordion content');
            
            // Instead, just populate the input fields from the purple module directly
            const inputFieldGroups = document.querySelectorAll('.input-field-group');
            console.log('[ENHANCED_LLM] Found input field groups:', inputFieldGroups.length);
            
            inputFieldGroups.forEach((group, index) => {
                console.log(`[ENHANCED_LLM] Processing input field group ${index}:`, group);
                
                const fieldSelector = group.querySelector('.field-selector[data-section="inputs"]');
                const textarea = group.querySelector('textarea');
                
                if (fieldSelector && textarea) {
                    const selectedField = fieldSelector.value;
                    const fieldContent = textarea.value;
                    const fieldId = textarea.id;
                    const dataTarget = fieldSelector.getAttribute('data-target');
                    
                    // Use the selected field name if available, otherwise fall back to data-target or fieldId
                    const fieldName = selectedField || dataTarget || fieldId;
                    
                    if (fieldName) {
                        // Get the display name for the selected field
                        const displayName = this.mapFieldToDisplayName(fieldName);
                        
                        // Show content or placeholder
                        let content = fieldContent;
                        if (!content || content.trim() === '') {
                            content = selectedField ? `Field "${displayName}" selected but no content available` : 'No field selected';
                        }
                        
                        const field = {
                            id: fieldName,
                            name: displayName,
                            content: content,
                            type: 'field',
                            source: 'purple_module',
                            fieldId: fieldId,
                            selectedField: selectedField
                        };
                        
                        console.log('[ENHANCED_LLM] Creating field element for:', field.name, 'with content:', field.content?.substring(0, 50) + '...');
                        const fieldElement = this.createFieldElement(field);
                        inputContainer.appendChild(fieldElement);
                    }
                }
            });
            
            console.log('[ENHANCED_LLM] Populated input fields with purple module data');
            
            // Update preview and summary after populating input fields
            this.updatePreview();
            this.updateSummary();
        } catch (error) {
            console.error('[ENHANCED_LLM] Error populating input fields with purple module data:', error);
        }
    }

    async populateInputFieldsWithSectionData(sectionData) {
        try {
            console.log('[ENHANCED_LLM] populateInputFieldsWithSectionData called with section data:', Object.keys(sectionData));
            
            const inputContainer = document.getElementById('input-elements-list');
            if (!inputContainer) {
                console.error('[ENHANCED_LLM] Input container not found in populateInputFieldsWithSectionData');
                return;
            }
            
            // Clear existing content
            inputContainer.innerHTML = '';
            
            // Get input field mappings from purple module
            const inputFieldGroups = document.querySelectorAll('.input-field-group');
            console.log('[ENHANCED_LLM] Found input field groups:', inputFieldGroups.length);
            
            inputFieldGroups.forEach((group, index) => {
                console.log(`[ENHANCED_LLM] Processing input field group ${index}:`, group);
                
                const fieldSelector = group.querySelector('.field-selector[data-section="inputs"]');
                const textarea = group.querySelector('textarea');
                
                if (fieldSelector && textarea) {
                    const selectedField = fieldSelector.value;
                    const fieldId = textarea.id;
                    const dataTarget = fieldSelector.getAttribute('data-target');
                    
                    // Use the selected field name if available, otherwise fall back to data-target or fieldId
                    const fieldName = selectedField || dataTarget || fieldId;
                    
                    if (fieldName) {
                        // Get the display name for the selected field
                        const displayName = this.mapFieldToDisplayName(fieldName);
                        
                        // Map the field name to API field name
                        const apiFieldName = this.mapFieldNameToApiField(fieldName);
                        console.log('[ENHANCED_LLM] Field mapping:', fieldName, '->', apiFieldName);
                        
                        // Get content from section data using mapped field name
                        let content = '';
                        if (sectionData && sectionData[apiFieldName]) {
                            content = sectionData[apiFieldName];
                        } else if (sectionData && sectionData.section && sectionData.section[apiFieldName]) {
                            content = sectionData.section[apiFieldName];
                        }
                        
                        // Show content or placeholder
                        if (!content || content.trim() === '') {
                            content = selectedField ? `Field "${displayName}" selected but no content available for this section` : 'No field selected';
                        }
                        
                        const field = {
                            id: fieldName,
                            name: displayName,
                            content: content,
                            type: 'field',
                            source: 'section_data',
                            fieldId: fieldId,
                            selectedField: selectedField
                        };
                        
                        console.log('[ENHANCED_LLM] Creating field element for:', field.name, 'with content:', field.content?.substring(0, 50) + '...');
                        const fieldElement = this.createFieldElement(field);
                        inputContainer.appendChild(fieldElement);
                    }
                }
            });
            
            console.log('[ENHANCED_LLM] Populated input fields with section-specific data');
            
            // Update preview and summary after populating input fields
            this.updatePreview();
            this.updateSummary();
        } catch (error) {
            console.error('[ENHANCED_LLM] Error populating input fields with section data:', error);
        }
    }

    // Method to get assembled content for external use (like llm_utils.js)
    getAssembledContent() {
        console.log('[ENHANCED_LLM] getAssembledContent called');
        
        const enabledElements = [];
        const container = document.getElementById('all-elements-container');
        if (!container) {
            console.error('[ENHANCED_LLM] Container not found for content assembly');
            return '';
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
                    // Handle accordion elements
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
                        let fieldCount = 0;
                        fieldElements.forEach(fieldElement => {
                            const fieldToggle = fieldElement.querySelector('.element-toggle');
                            if (fieldToggle && fieldToggle.checked) {
                                const fieldContent = fieldElement.querySelector('.element-content');
                                if (fieldContent && fieldContent.textContent.trim()) {
                                    const fieldLabel = fieldElement.querySelector('.element-label');
                                    const label = fieldLabel ? fieldLabel.textContent : 'Field';
                                    
                                    // Add line break before each field (except the first one)
                                    if (fieldCount > 0) {
                                        sectionContent += '\n';
                                    }
                                    
                                    sectionContent += `${label}: ${fieldContent.textContent.trim()}`;
                                    fieldCount++;
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
                        // This accordion has direct content
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
        
        console.log('[ENHANCED_LLM] Assembled content:', message ? message.substring(0, 200) + '...' : 'empty');
        return message;
    }
}

// Export for ES6 modules
export default EnhancedLLMMessageManager;

// Make it available globally for llm_utils.js to access
if (typeof window !== 'undefined') {
    window.enhancedLLMMessageManager = null;
    
    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', () => {
        const manager = new EnhancedLLMMessageManager();
        window.enhancedLLMMessageManager = manager;
        manager.init();
    });
} 
