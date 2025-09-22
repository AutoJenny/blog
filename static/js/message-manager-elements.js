/**
 * Message Manager Elements Module
 * Handles message element creation and management
 */

// Individual elements configuration
const ELEMENT_CONFIGS = [
    // Prompts (Red)
    { id: 'system-prompt', title: 'System Prompt', content: 'System prompt content will be loaded here...', color: '#ffebee', borderColor: '#f44336', defaultEnabled: true },
    { id: 'task-prompt', title: 'Task Prompt', content: 'Task prompt content will be loaded here...', color: '#ffebee', borderColor: '#f44336', defaultEnabled: true },
    
    // Default Inputs (Orange)
    { id: 'basic-idea', title: 'Basic Idea', content: 'Basic idea content will be loaded here...', color: '#fff3e0', borderColor: '#ff9800', defaultEnabled: false },
    { id: 'expanded-idea', title: 'Expanded Idea', content: 'Expanded idea content will be loaded here...', color: '#fff3e0', borderColor: '#ff9800', defaultEnabled: false },
    { id: 'section-headings', title: 'Section Headings', content: 'Section headings will be loaded here...', color: '#fff3e0', borderColor: '#ff9800', defaultEnabled: false },
    
    // Selected Inputs (Yellow)
    { id: 'dynamic-inputs', title: 'Dynamic Inputs', content: 'Selected input fields will appear here...', color: '#fffde7', borderColor: '#ffc107', defaultEnabled: true },
    
    // Planning Stage Simple Input (Green)
    { id: 'planning-input', title: 'Selected Input', content: 'Content will be loaded from selected field...', color: '#e8f5e8', borderColor: '#4caf50', defaultEnabled: true }
];

// Message Manager Elements Class
class MessageManagerElements {
    constructor() {
        this.logger = window.LLM_STATE?.logger || console;
        this.elements = new Map();
        this.enabledElements = new Set();
    }

    /**
     * Initialize the elements module
     */
    async initialize() {
        try {
            this.logger.info('messageManagerElements', 'Initializing elements module...');
            
            await this.createElementGroups();
            this.setupEventListeners();
            this.setDefaultStates();
            this.loadAccordionStates();
            
            // Wait a bit for other modules to load their data, then refresh elements
            setTimeout(async () => {
                await this.refreshAllElements();
            }, 500);
            
            this.logger.info('messageManagerElements', 'Elements module initialized successfully');
            
            // Initial preview update
            setTimeout(() => {
                this.notifyPreviewUpdate();
            }, 1000);
        } catch (error) {
            this.logger.error('messageManagerElements', 'Failed to initialize elements module:', error);
            throw error;
        }
    }

    /**
     * Create individual elements with colored title zones
     */
    async createElementGroups() {
        const container = document.querySelector('.elements-container');
        if (!container) {
            this.logger.warn('messageManagerElements', 'Elements container not found');
            return;
        }

        // Make container accordion-enabled
        container.setAttribute('data-accordion-container', 'message-elements');

        // Clear existing content
        container.innerHTML = '';

        // Check if we're in planning stage OR a specific writing step that should use simple template
        const isPlanningStage = window.LLM_STATE?.context?.stage === 'planning' || 
                               (window.LLM_STATE?.context?.stage === 'writing' && 
                                window.LLM_STATE?.context?.step === 'header_montage_description');

        // Create each individual element
        for (const elementConfig of ELEMENT_CONFIGS) {
            // For planning stage: show planning-input, hide dynamic-inputs
            if (isPlanningStage) {
                if (elementConfig.id === 'dynamic-inputs') {
                    this.logger.debug('messageManagerElements', 'Skipping dynamic-inputs element for planning stage');
                    continue;
                }
                if (elementConfig.id === 'planning-input') {
                    // Create planning input element
                    const elementDiv = await this.createElementCard(elementConfig);
                    container.appendChild(elementDiv);
                    
                    // Store element reference
                    this.elements.set(elementConfig.id, {
                        element: elementDiv,
                        config: elementConfig
                    });
                    continue;
                }
            }
            
            // For writing stage: show dynamic-inputs, hide planning-input
            if (!isPlanningStage) {
                if (elementConfig.id === 'planning-input') {
                    this.logger.debug('messageManagerElements', 'Skipping planning-input element for writing stage');
                    continue;
                }
            }
            
            const elementDiv = await this.createElementCard(elementConfig);
            container.appendChild(elementDiv);
            
            // Store element reference
            this.elements.set(elementConfig.id, {
                element: elementDiv,
                config: elementConfig
            });
        }

        // Apply saved element order
        this.applyElementOrder();

        this.logger.debug('messageManagerElements', 'Created individual elements');
    }



    /**
     * Create an individual element card with colored title zone
     */
    async createElementCard(elementConfig) {
        const elementDiv = document.createElement('div');
        elementDiv.className = 'element-card';
        elementDiv.setAttribute('data-element-id', elementConfig.id);
        elementDiv.setAttribute('data-accordion-section', elementConfig.id);
        elementDiv.style.cssText = `
            margin: 12px;
            background: white;
            border: 2px solid ${elementConfig.borderColor};
            border-radius: 8px;
            overflow: hidden;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        `;

        // Create colored title zone (accordion header)
        const titleDiv = document.createElement('div');
        titleDiv.className = 'element-title-zone accordion-header';
        titleDiv.setAttribute('data-accordion-header', elementConfig.id);
        titleDiv.style.cssText = `
            padding: 12px 16px;
            background: ${elementConfig.color};
            border-bottom: 2px solid ${elementConfig.borderColor};
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            user-select: none;
        `;

        // Create checkbox
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'element-toggle';
        checkbox.checked = elementConfig.defaultEnabled;
        checkbox.style.cssText = `
            margin-right: 12px;
            transform: scale(1.2);
        `;

        // Create title with prompt name if available
        const titleSpan = document.createElement('span');
        titleSpan.className = 'element-title';
        
        // Get the actual prompt name and content
        let promptName = '';
        let promptContent = elementConfig.content;
        
        if (elementConfig.id === 'system-prompt') {
            const systemPromptSelect = document.getElementById('system-prompt-select');
            const systemPromptDisplay = document.getElementById('system-prompt-display');
            if (systemPromptSelect && systemPromptSelect.value) {
                promptName = systemPromptSelect.options[systemPromptSelect.selectedIndex].text;
            }
            if (systemPromptDisplay && systemPromptDisplay.textContent !== 'Select a system prompt to view its content...') {
                promptContent = systemPromptDisplay.textContent;
            }
        } else if (elementConfig.id === 'task-prompt') {
            const taskPromptSelect = document.getElementById('action-select');
            const taskPromptDisplay = document.getElementById('prompt-display');
            if (taskPromptSelect && taskPromptSelect.value) {
                promptName = taskPromptSelect.options[taskPromptSelect.selectedIndex].text;
            }
            if (taskPromptDisplay && taskPromptDisplay.textContent !== 'Select a task prompt to view its content...') {
                promptContent = taskPromptDisplay.textContent;
            }
        } else if (elementConfig.id === 'basic-idea') {
            // Get content from post_development table
            const fieldValues = window.FIELD_SELECTOR_STATE?.fieldValues || {};
            const basicIdeaContent = fieldValues.basic_idea || fieldValues.basic_idea_text || fieldValues.basic_idea_content || '';
            if (basicIdeaContent) {
                promptContent = basicIdeaContent;
                promptName = 'Basic Idea';
            }
        } else if (elementConfig.id === 'expanded-idea') {
            // Get content from post_development table
            const fieldValues = window.FIELD_SELECTOR_STATE?.fieldValues || {};
            const expandedIdeaContent = fieldValues.expanded_idea || fieldValues.expanded_idea_text || fieldValues.expanded_idea_content || '';
            if (expandedIdeaContent) {
                promptContent = expandedIdeaContent;
                promptName = 'Expanded Idea';
            } else {
                // Fallback: try to fetch directly if field selector state is empty
                const postId = this.getPostId();
                if (postId) {
                    try {
                        const response = await fetch(`/api/workflow/posts/${postId}/development`);
                        if (response.ok) {
                            const data = await response.json();
                            if (data.expanded_idea) {
                                promptContent = data.expanded_idea;
                                promptName = 'Expanded Idea';
                            }
                        }
                    } catch (error) {
                        this.logger.warn('messageManagerElements', 'Failed to fetch expanded idea directly:', error);
                    }
                }
            }
        } else if (elementConfig.id === 'section-headings') {
            // Get content from post_development table
            const fieldValues = window.FIELD_SELECTOR_STATE?.fieldValues || {};
            const sectionHeadingsContent = fieldValues.section_headings || fieldValues.section_headings_text || fieldValues.section_headings_content || '';
            if (sectionHeadingsContent) {
                promptContent = sectionHeadingsContent;
                
                // Get the field name from the Inputs dropdown selection
                const inputFieldSelect = document.getElementById('input-field-select');
                if (inputFieldSelect && inputFieldSelect.value) {
                    // Get the selected option text (field name)
                    const selectedOption = inputFieldSelect.options[inputFieldSelect.selectedIndex];
                    if (selectedOption) {
                        promptName = selectedOption.textContent;
                    } else {
                        promptName = 'Section Headings'; // fallback
                    }
                } else {
                    // Fallback to saved mapping or default
                    const savedMapping = window.FIELD_SELECTOR_STATE?.mappings?.['input-content'];
                    if (savedMapping) {
                        // Extract field name from mapping (e.g., "post_development.section_headings" -> "Section Headings")
                        const fieldName = savedMapping.split('.').pop();
                        // Convert snake_case to Title Case
                        promptName = fieldName.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
                    } else {
                        promptName = 'Section Headings'; // default fallback
                    }
                }
            }
        } else if (elementConfig.id === 'dynamic-inputs') {
            // Dynamic inputs will be populated with section data
            promptName = 'Dynamic Inputs';
            promptContent = 'Select a section to view its content...';
        }
        
        // Set the title with prompt name if available
        if (promptName && elementConfig.id !== 'dynamic-inputs') {
            titleSpan.textContent = `${elementConfig.title}: ${promptName}`;
        } else {
            titleSpan.textContent = elementConfig.title;
        }
        
        titleSpan.style.cssText = `
            font-weight: 600;
            color: #333;
            flex: 1;
            font-size: 14px;
        `;

        // Add reorder buttons
        const reorderButtons = document.createElement('div');
        reorderButtons.className = 'reorder-buttons';
        reorderButtons.style.cssText = `
            display: flex;
            gap: 4px;
            margin-left: 8px;
        `;

        const upButton = document.createElement('button');
        upButton.innerHTML = '↑';
        upButton.className = 'reorder-btn up-btn';
        upButton.setAttribute('data-element-id', elementConfig.id);
        upButton.style.cssText = `
            background: rgba(255,255,255,0.2);
            border: none;
            border-radius: 3px;
            width: 24px;
            height: 24px;
            cursor: pointer;
            font-size: 12px;
            color: #333;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        `;

        const downButton = document.createElement('button');
        downButton.innerHTML = '↓';
        downButton.className = 'reorder-btn down-btn';
        downButton.setAttribute('data-element-id', elementConfig.id);
        downButton.style.cssText = `
            background: rgba(255,255,255,0.2);
            border: none;
            border-radius: 3px;
            width: 24px;
            height: 24px;
            cursor: pointer;
            font-size: 12px;
            color: #333;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        `;

        // Add accordion toggle icon
        const toggleIcon = document.createElement('span');
        toggleIcon.className = 'accordion-toggle-icon';
        toggleIcon.innerHTML = '▼'; // Down arrow for collapsed state
        toggleIcon.style.cssText = `
            font-size: 12px;
            color: #333;
            transition: transform 0.2s ease;
            margin-left: 8px;
        `;

        reorderButtons.appendChild(upButton);
        reorderButtons.appendChild(downButton);

        titleDiv.appendChild(checkbox);
        titleDiv.appendChild(titleSpan);
        titleDiv.appendChild(reorderButtons);
        titleDiv.appendChild(toggleIcon);

                        // Add section dropdown for dynamic inputs
                if (elementConfig.id === 'dynamic-inputs') {
                    const dropdownDiv = document.createElement('div');
                    dropdownDiv.className = 'section-dropdown-container';
                    dropdownDiv.style.cssText = `
                        margin-top: 8px;
                        width: 100%;
                    `;

                    const dropdown = document.createElement('select');
                    dropdown.className = 'section-dropdown';
                    dropdown.setAttribute('data-element-id', 'dynamic-inputs');
                    dropdown.style.cssText = `
                        width: 100%;
                        padding: 8px 12px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        background: white;
                        font-size: 13px;
                        color: #333;
                    `;

                    dropdownDiv.appendChild(dropdown);
                    titleDiv.appendChild(dropdownDiv);

                    // Store dropdown reference for later use
                    elementConfig.dropdown = dropdown;
                }

        // Create content area (accordion content)
        const contentDiv = document.createElement('div');
        contentDiv.className = 'element-content accordion-content';
        contentDiv.setAttribute('data-accordion-content', elementConfig.id);
        contentDiv.style.cssText = `
            padding: 16px;
            background: white;
            color: #666;
            font-size: 14px;
            line-height: 1.5;
            min-height: 60px;
            max-height: 200px;
            overflow-y: auto;
            display: none; /* Start collapsed */
        `;
        contentDiv.textContent = promptContent;

        elementDiv.appendChild(titleDiv);
        elementDiv.appendChild(contentDiv);

        // Set initial enabled state
        if (elementConfig.defaultEnabled) {
            this.enabledElements.add(elementConfig.id);
        }

        return elementDiv;
    }

    /**
     * Set up event listeners for element interactions
     */
    setupEventListeners() {
        // Handle checkbox toggles
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('element-toggle')) {
                this.handleElementToggle(e.target);
            }
        });

        // Handle prompt dropdown changes to update element content
        document.addEventListener('change', (e) => {
            if (e.target.id === 'system-prompt-select' || e.target.id === 'action-select') {
                // Wait a bit for the content to update, then refresh our elements
                setTimeout(() => {
                    this.refreshPromptElements();
                }, 100);
            }
        });

        // Handle field mapping changes to update default input elements
        document.addEventListener('fieldMappingsChanged', (e) => {
            // Wait a bit for the field values to update, then refresh our elements
            setTimeout(async () => {
                await this.refreshDefaultInputElements();
            }, 100);
        });

        // Handle field selector dropdown changes to update planning-input element
        document.addEventListener('change', (e) => {
            if (e.target.id === 'field-select' || e.target.classList.contains('field-selector-dropdown')) {
                // Wait a bit for the field selector to update its state, then refresh our elements
                setTimeout(async () => {
                    await this.refreshDefaultInputElements();
                }, 200);
            }
        });

        // Handle section dropdown changes
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('section-dropdown')) {
                this.handleSectionSelection(e.target);
            }
        });

        // Handle input field selection changes in purple panel
        document.addEventListener('change', (e) => {
            if (e.target.id === 'input-field-select') {
                // Refresh dynamic inputs content when input field changes
                const dynamicElement = this.elements.get('dynamic-inputs');
                if (dynamicElement) {
                    const dropdown = dynamicElement.element.querySelector('.section-dropdown');
                    if (dropdown && dropdown.value) {
                        this.handleSectionSelection(dropdown);
                    }
                }
                
                // Refresh section-headings element title when input field changes
                setTimeout(async () => {
                    await this.refreshDefaultInputElements();
                }, 100);
            }
        });

        // Handle accordion toggle clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.accordion-header')) {
                const header = e.target.closest('.accordion-header');
                const sectionId = header.getAttribute('data-accordion-header');
                this.toggleAccordionSection(sectionId);
            }
        });

        // Handle reorder button clicks
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('reorder-btn')) {
                e.stopPropagation(); // Prevent accordion toggle
                const elementId = e.target.getAttribute('data-element-id');
                const isUp = e.target.classList.contains('up-btn');
                this.reorderElement(elementId, isUp ? 'up' : 'down');
            }
        });

        // Handle element card hover effects
        document.addEventListener('mouseenter', (e) => {
            if (e.target.closest('.element-card')) {
                const card = e.target.closest('.element-card');
                card.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
                card.style.transform = 'translateY(-1px)';
            }
        });

        document.addEventListener('mouseleave', (e) => {
            if (e.target.closest('.element-card')) {
                const card = e.target.closest('.element-card');
                card.style.boxShadow = '';
                card.style.transform = '';
            }
        });

        // Handle reorder button hover effects
        document.addEventListener('mouseenter', (e) => {
            if (e.target.classList.contains('reorder-btn')) {
                e.target.style.background = 'rgba(255,255,255,0.4)';
                e.target.style.transform = 'scale(1.1)';
            }
        });

        document.addEventListener('mouseleave', (e) => {
            if (e.target.classList.contains('reorder-btn')) {
                e.target.style.background = 'rgba(255,255,255,0.2)';
                e.target.style.transform = 'scale(1)';
            }
        });

        this.logger.debug('messageManagerElements', 'Event listeners set up');
    }

    /**
     * Handle element toggle (enable/disable)
     */
    handleElementToggle(checkbox) {
        const elementCard = checkbox.closest('.element-card');
        const elementId = elementCard.getAttribute('data-element-id');
        
        if (checkbox.checked) {
            this.enabledElements.add(elementId);
            elementCard.style.opacity = '1';
            this.logger.debug('messageManagerElements', `Enabled element: ${elementId}`);
        } else {
            this.enabledElements.delete(elementId);
            elementCard.style.opacity = '0.6';
            this.logger.debug('messageManagerElements', `Disabled element: ${elementId}`);
        }

        // Notify preview module to update
        this.notifyPreviewUpdate();
    }

    /**
     * Set default enabled/disabled states
     */
    setDefaultStates() {
        this.elements.forEach((elementData, elementId) => {
            const element = elementData.element;
            const checkbox = element.querySelector('.element-toggle');
            const config = elementData.config;
            
            if (checkbox) {
                checkbox.checked = config.defaultEnabled;
                if (!config.defaultEnabled) {
                    element.style.opacity = '0.6';
                }
            }
        });

        this.logger.debug('messageManagerElements', 'Default states set');
    }

    /**
     * Notify preview module to update
     */
    notifyPreviewUpdate() {
        if (window.MessageManagerPreview) {
            window.MessageManagerPreview.updatePreview();
        }
    }

    /**
     * Get all enabled elements
     */
    getEnabledElements() {
        const enabledElements = [];
        for (const elementId of this.enabledElements) {
            const elementData = this.elements.get(elementId);
            if (elementData) {
                const titleSpan = elementData.element.querySelector('.element-title');
                const contentDiv = elementData.element.querySelector('.element-content');
                
                enabledElements.push({
                    id: elementId,
                    title: titleSpan ? titleSpan.textContent : '',
                    content: contentDiv ? contentDiv.textContent : '',
                    enabled: true
                });
            }
        }
        return enabledElements;
    }

    /**
     * Get element content by ID
     */
    getElementContent(elementId) {
        const elementData = this.elements.get(elementId);
        if (elementData) {
            const contentDiv = elementData.element.querySelector('.element-content');
            return contentDiv ? contentDiv.textContent : '';
        }
        return '';
    }

    /**
     * Refresh prompt elements with current content
     */
    refreshPromptElements() {
        // Update system prompt element
        const systemElement = this.elements.get('system-prompt');
        if (systemElement) {
            const systemPromptSelect = document.getElementById('system-prompt-select');
            const systemPromptDisplay = document.getElementById('system-prompt-display');
            const titleSpan = systemElement.element.querySelector('.element-title');
            const contentDiv = systemElement.element.querySelector('.element-content');
            
            if (systemPromptSelect && systemPromptSelect.value) {
                const promptName = systemPromptSelect.options[systemPromptSelect.selectedIndex].text;
                titleSpan.textContent = `System Prompt: ${promptName}`;
            } else {
                titleSpan.textContent = 'System Prompt';
            }
            
            if (systemPromptDisplay && systemPromptDisplay.textContent !== 'Select a system prompt to view its content...') {
                contentDiv.textContent = systemPromptDisplay.textContent;
            } else {
                contentDiv.textContent = 'System prompt content will be loaded here...';
            }
        }

        // Update task prompt element
        const taskElement = this.elements.get('task-prompt');
        if (taskElement) {
            const taskPromptSelect = document.getElementById('action-select');
            const taskPromptDisplay = document.getElementById('prompt-display');
            const titleSpan = taskElement.element.querySelector('.element-title');
            const contentDiv = taskElement.element.querySelector('.element-content');
            
            if (taskPromptSelect && taskPromptSelect.value) {
                const promptName = taskPromptSelect.options[taskPromptSelect.selectedIndex].text;
                titleSpan.textContent = `Task Prompt: ${promptName}`;
            } else {
                titleSpan.textContent = 'Task Prompt';
            }
            
            if (taskPromptDisplay && taskPromptDisplay.textContent !== 'Select a task prompt to view its content...') {
                contentDiv.textContent = taskPromptDisplay.textContent;
            } else {
                contentDiv.textContent = 'Task prompt content will be loaded here...';
            }
        }

        // Update default input elements
        this.refreshDefaultInputElements();

        this.logger.debug('messageManagerElements', 'Refreshed prompt elements');
    }

    /**
     * Refresh default input elements with current content
     */
    async refreshDefaultInputElements() {
        // Check if we're in planning stage OR a specific writing step that should use simple template
        const isPlanningStage = window.LLM_STATE?.context?.stage === 'planning' || 
                               (window.LLM_STATE?.context?.stage === 'writing' && 
                                window.LLM_STATE?.context?.step === 'header_montage_description');
        
        if (isPlanningStage) {
            // For planning stage: use planning input textarea
            if (window.LLM_STATE?.context?.stage === 'planning') {
                const planningInput = document.getElementById('planning-input');
                if (planningInput && planningInput.value) {
                    const selectedField = window.FIELD_SELECTOR_STATE?.selectedField;
                    if (selectedField) {
                        const fieldName = selectedField.split('.').pop(); // e.g., "idea_seed"
                        
                        // Update planning-input element with planning input
                        const planningInputElement = this.elements.get('planning-input');
                        if (planningInputElement) {
                            const titleSpan = planningInputElement.element.querySelector('.element-title');
                            const contentDiv = planningInputElement.element.querySelector('.element-content');
                            
                            titleSpan.textContent = fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                            contentDiv.textContent = planningInput.value;
                        }
                    }
                    
                    this.logger.debug('messageManagerElements', 'Refreshed planning stage input elements');
                    return;
                }
            }
            
            // For header_montage_description step: use selected field from dropdown
            if (window.LLM_STATE?.context?.stage === 'writing' && 
                window.LLM_STATE?.context?.step === 'header_montage_description') {
                
                // Get the content from the planning-input textarea (which is populated by field selector)
                const planningInput = document.getElementById('planning-input');
                if (planningInput && planningInput.value) {
                    const selectedField = window.FIELD_SELECTOR_STATE?.selectedField;
                    if (selectedField) {
                        const fieldName = selectedField.split('.').pop(); // e.g., "section_headings"
                        
                        // Update the planning-input element with the textarea content
                        const planningInputElement = this.elements.get('planning-input');
                        if (planningInputElement) {
                            const titleSpan = planningInputElement.element.querySelector('.element-title');
                            const contentDiv = planningInputElement.element.querySelector('.element-content');
                            
                            titleSpan.textContent = fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                            contentDiv.textContent = planningInput.value;
                            this.logger.debug('messageManagerElements', `Updated planning-input element with ${fieldName} content from textarea`);
                        }
                    }
                }
                
                this.logger.debug('messageManagerElements', 'Refreshed header_montage_description step elements');
                return;
            }
        }
        
        // Try to get field values from field selector state first
        let fieldValues = window.FIELD_SELECTOR_STATE?.fieldValues || {};
        
        // If no field values, try to fetch them directly
        if (Object.keys(fieldValues).length === 0) {
            fieldValues = await this.fetchPostDevelopmentData();
        }

        // Helper function to get field content with table-aware support
        const getFieldContent = (fieldNames) => {
            for (const fieldName of fieldNames) {
                // Check for table-aware field IDs first (e.g., "post_development.basic_idea")
                for (const [key, value] of Object.entries(fieldValues)) {
                    if (key.endsWith(`.${fieldName}`) || key === fieldName) {
                        if (value && value.trim()) {
                            return value;
                        }
                    }
                }
            }
            return '';
        };

        // Update basic idea element
        const basicIdeaElement = this.elements.get('basic-idea');
        if (basicIdeaElement) {
            const titleSpan = basicIdeaElement.element.querySelector('.element-title');
            const contentDiv = basicIdeaElement.element.querySelector('.element-content');
            const basicIdeaContent = getFieldContent(['basic_idea', 'basic_idea_text', 'basic_idea_content']);
            
            titleSpan.textContent = 'Basic Idea';
            if (basicIdeaContent) {
                contentDiv.textContent = basicIdeaContent;
            } else {
                contentDiv.textContent = 'Basic idea content will be loaded here...';
            }
        }

        // Update expanded idea element
        const expandedIdeaElement = this.elements.get('expanded-idea');
        if (expandedIdeaElement) {
            const titleSpan = expandedIdeaElement.element.querySelector('.element-title');
            const contentDiv = expandedIdeaElement.element.querySelector('.element-content');
            const expandedIdeaContent = getFieldContent(['expanded_idea', 'expanded_idea_text', 'expanded_idea_content']);
            
            titleSpan.textContent = 'Expanded Idea';
            if (expandedIdeaContent) {
                contentDiv.textContent = expandedIdeaContent;
            } else {
                contentDiv.textContent = 'Expanded idea content will be loaded here...';
            }
        }

        // Update section headings element
        const sectionHeadingsElement = this.elements.get('section-headings');
        if (sectionHeadingsElement) {
            const titleSpan = sectionHeadingsElement.element.querySelector('.element-title');
            const contentDiv = sectionHeadingsElement.element.querySelector('.element-content');
            const sectionHeadingsContent = getFieldContent(['section_headings', 'section_headings_text', 'section_headings_content']);
            
            titleSpan.textContent = 'Section Headings';
            if (sectionHeadingsContent) {
                contentDiv.textContent = sectionHeadingsContent;
            } else {
                contentDiv.textContent = 'Section headings will be loaded here...';
            }
        }

        // Special handling for header_montage_description step: use selected field content
        if (window.LLM_STATE?.context?.stage === 'writing' && 
            window.LLM_STATE?.context?.step === 'header_montage_description') {
            
            const selectedField = window.FIELD_SELECTOR_STATE?.selectedField;
            if (selectedField) {
                const fieldName = selectedField.split('.').pop(); // e.g., "section_headings"
                const selectedContent = fieldValues[fieldName];
                
                if (selectedContent) {
                    // Update the planning-input element with selected field content
                    const planningInputElement = this.elements.get('planning-input');
                    if (planningInputElement) {
                        const titleSpan = planningInputElement.element.querySelector('.element-title');
                        const contentDiv = planningInputElement.element.querySelector('.element-content');
                        
                        titleSpan.textContent = fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        contentDiv.textContent = selectedContent;
                    }
                }
            }
        }
        
        this.logger.debug('messageManagerElements', 'Refreshed default input elements with table-aware support');
    }

    /**
     * Refresh dynamic input elements with sections data
     */
    async refreshDynamicInputElements() {
        const dynamicElement = this.elements.get('dynamic-inputs');
        if (dynamicElement) {
            // Get section IDs from iframe communication
            const sectionIds = await this.getCurrentSectionIds();
            
            if (sectionIds && sectionIds.length > 0) {
                // Populate dropdown with section IDs
                this.populateSectionDropdown(dynamicElement, sectionIds);
                this.logger.debug('messageManagerElements', `Refreshed dynamic input elements with ${sectionIds.length} sections`);
            } else {
                this.logger.warn('messageManagerElements', 'No section IDs available for dynamic inputs');
            }
        }
    }

    /**
     * Get current section IDs from iframe communication
     */
    async getCurrentSectionIds() {
        try {
            // Use the orchestrator's method to get selected section IDs
            if (window.llmOrchestrator) {
                const sectionIds = await window.llmOrchestrator.getCurrentSectionIds();
                this.logger.debug('messageManagerElements', `Got ${sectionIds ? sectionIds.length : 0} selected section IDs from orchestrator`);
                return sectionIds || [];
            } else {
                this.logger.warn('messageManagerElements', 'llmOrchestrator not available, using fallback');
                // Fallback to hardcoded IDs if orchestrator not available
                return ['710', '711', '712', '714', '713', '715', '716'];
            }
        } catch (error) {
            this.logger.warn('messageManagerElements', 'Failed to get section IDs from orchestrator:', error);
            // Fallback to hardcoded IDs
            return ['710', '711', '712', '714', '713', '715', '716'];
        }
    }

    /**
     * Populate section dropdown
     */
    populateSectionDropdown(elementData, sectionIds) {
        this.logger.debug('messageManagerElements', `populateSectionDropdown called with sectionIds:`, sectionIds);
        
        const dropdown = elementData.element.querySelector('.section-dropdown');
        if (!dropdown) return;

        // Clear existing options
        dropdown.innerHTML = '';

        // Add options for each section ID - simple and direct!
        sectionIds.forEach(sectionId => {
            const option = document.createElement('option');
            option.value = sectionId;
            option.textContent = `Section ${sectionId}`;
            dropdown.appendChild(option);
        });

        // Set first section as default and trigger content load
        if (sectionIds.length > 0) {
            dropdown.value = sectionIds[0];
            this.logger.debug('messageManagerElements', `Set dropdown value to: ${sectionIds[0]}`);
            // Trigger the section selection to load initial content
            this.handleSectionSelection(dropdown);
        }

        this.logger.debug('messageManagerElements', `Populated dropdown with ${sectionIds.length} sections`);
    }

    /**
     * Handle section selection
     */
    async handleSectionSelection(dropdown) {
        const sectionId = dropdown.value;
        this.logger.debug('messageManagerElements', `handleSectionSelection called with sectionId: ${sectionId}`);
        
        if (!sectionId) {
            // Clear content if no section selected
            const elementData = this.elements.get('dynamic-inputs');
            if (elementData) {
                const contentDiv = elementData.element.querySelector('.element-content');
                contentDiv.textContent = 'Select a section to view its content...';
            }
            return;
        }

        // Get the selected input field from the purple panel
        const inputFieldSelect = document.getElementById('input-field-select');
        const selectedField = inputFieldSelect ? inputFieldSelect.value : null;
        this.logger.debug('messageManagerElements', `Selected field: ${selectedField}`);
        
        if (!selectedField) {
            this.logger.warn('messageManagerElements', 'No input field selected in purple panel');
            const elementData = this.elements.get('dynamic-inputs');
            if (elementData) {
                const contentDiv = elementData.element.querySelector('.element-content');
                contentDiv.textContent = 'Please select an input field in the purple panel above';
            }
            return;
        }

        // Fetch specific field content for the selected section
        this.logger.debug('messageManagerElements', `Fetching ${selectedField} content for section ${sectionId}`);
        const fieldContent = await this.fetchSectionFieldContent(sectionId, selectedField);
        this.logger.debug('messageManagerElements', `Received field content: ${fieldContent ? 'Content found' : 'No content'}`);
        
        // Update content
        const elementData = this.elements.get('dynamic-inputs');
        if (elementData) {
            const contentDiv = elementData.element.querySelector('.element-content');
            contentDiv.textContent = fieldContent || `No ${selectedField} content available for Section ${sectionId}`;
            
            // Update preview after content changes
            this.notifyPreviewUpdate();
        }
    }

    /**
     * Fetch content for a specific section
     */
    async fetchSectionContent(sectionId) {
        try {
            const postId = this.getPostId();
            if (!postId) {
                this.logger.warn('messageManagerElements', 'No post ID found for fetching section content');
                return '';
            }

            // Use the blog-post-sections service API endpoint
            const response = await fetch(`http://localhost:5003/api/sections/${postId}`);
            
            if (!response.ok) {
                this.logger.warn('messageManagerElements', `Failed to fetch sections data (${response.status}): ${response.statusText}`);
                return '';
            }

            const data = await response.json();
            this.logger.debug('messageManagerElements', 'Fetched sections data:', data);
            
            // Find the specific section by ID
            const sections = data.sections || [];
            const section = sections.find(s => s.id == sectionId);
            
            if (section) {
                // Extract relevant content fields
                const content = [];
                if (section.section_heading) content.unshift(`Section: ${section.section_heading}`);
                if (section.section_description) content.push(`Description: ${section.section_description}`);
                if (section.draft) content.push(`Draft: ${section.draft}`);
                if (section.polished) content.push(`Polished: ${section.polished}`);
                if (section.ideas_to_include) content.push(`Ideas to Include: ${section.ideas_to_include}`);
                
                return content.join('\n\n') || 'No content available';
            } else {
                this.logger.warn('messageManagerElements', `Section ${sectionId} not found in sections data`);
                return `Section ${sectionId} not found`;
            }
            
        } catch (error) {
            this.logger.error('messageManagerElements', 'Failed to fetch section content:', error);
            return '';
        }
    }

    /**
     * Fetch specific field content for a section
     */
    async fetchSectionFieldContent(sectionId, fieldName) {
        try {
            const postId = this.getPostId();
            this.logger.debug('messageManagerElements', `fetchSectionFieldContent using postId: ${postId}, sectionId: ${sectionId}, fieldName: ${fieldName}`);
            
            if (!postId) {
                this.logger.warn('messageManagerElements', 'No post ID found for fetching section field content');
                return '';
            }

            // Use the blog-post-sections service API endpoint
            const response = await fetch(`http://localhost:5003/api/sections/${postId}`);
            
            if (!response.ok) {
                this.logger.warn('messageManagerElements', `Failed to fetch sections data (${response.status}): ${response.statusText}`);
                return '';
            }

            const data = await response.json();
            this.logger.debug('messageManagerElements', 'Fetched sections data for field content:', data);
            
            // Find the specific section by ID
            const sections = data.sections || [];
            const section = sections.find(s => s.id == sectionId);
            
            if (section) {
                // Get the specific field content
                const fieldContent = section[fieldName];
                if (fieldContent) {
                    this.logger.debug('messageManagerElements', `Found ${fieldName} content for section ${sectionId}:`, fieldContent);
                    return fieldContent;
                } else {
                    this.logger.warn('messageManagerElements', `Field ${fieldName} not found in section ${sectionId}`);
                    return `No ${fieldName} content available for Section ${sectionId}`;
                }
            } else {
                this.logger.warn('messageManagerElements', `Section ${sectionId} not found in sections data`);
                return `Section ${sectionId} not found`;
            }
            
        } catch (error) {
            this.logger.error('messageManagerElements', 'Failed to fetch section field content:', error);
            return '';
        }
    }

    /**
     * Fetch post development data directly
     */
    async fetchPostDevelopmentData() {
        try {
            // Get post ID from the page
            const postId = this.getPostId();
            if (!postId) {
                this.logger.warn('messageManagerElements', 'No post ID found');
                return {};
            }

            // Get base URL (same logic as field-selector)
            const isIntegrated = window.location.hostname === 'localhost' && window.location.port === '5001';
            const baseUrl = isIntegrated ? 'http://localhost:5002' : '';

            const response = await fetch(`${baseUrl}/api/workflow/posts/${postId}/development`);
            
            if (!response.ok) {
                this.logger.warn('messageManagerElements', `Failed to fetch post development data (${response.status}): ${response.statusText}`);
                return {};
            }

            const data = await response.json();
            this.logger.debug('messageManagerElements', 'Fetched post development data:', data);
            return data || {};
            
        } catch (error) {
            this.logger.error('messageManagerElements', 'Failed to fetch post development data:', error);
            return {};
        }
    }

    /**
     * Get post ID from the page
     */
    getPostId() {
        // Try multiple ways to get the post ID
        const container = document.querySelector('.llm-container');
        if (container) {
            const postId = container.getAttribute('data-post-id');
            this.logger.debug('messageManagerElements', `Found post ID from container: ${postId}`);
            return postId;
        }
        
        // Fallback: try to get from URL
        const urlParams = new URLSearchParams(window.location.search);
        const postId = urlParams.get('post_id') || urlParams.get('id');
        this.logger.debug('messageManagerElements', `Found post ID from URL: ${postId}`);
        return postId;
    }

    /**
     * Refresh all elements with current content
     */
    async refreshAllElements() {
        this.refreshPromptElements();
        await this.refreshDefaultInputElements();
        await this.refreshDynamicInputElements();
        this.logger.debug('messageManagerElements', 'Refreshed all elements');
        
        // Update preview after refreshing all elements
        this.notifyPreviewUpdate();
    }

    /**
     * Update element content
     */
    updateElementContent(elementId, content) {
        const elementData = this.elements.get(elementId);
        if (elementData) {
            const contentDiv = elementData.element.querySelector('.element-content');
            if (contentDiv) {
                contentDiv.textContent = content;
                this.logger.debug('messageManagerElements', `Updated content for element: ${elementId}`);
            }
        }
    }

    /**
     * Toggle accordion section
     */
    toggleAccordionSection(sectionId) {
        const elementData = this.elements.get(sectionId);
        if (!elementData) return;

        const contentDiv = elementData.element.querySelector('.accordion-content');
        const toggleIcon = elementData.element.querySelector('.accordion-toggle-icon');
        
        if (!contentDiv || !toggleIcon) return;

        const isCurrentlyOpen = contentDiv.style.display !== 'none';
        
        if (isCurrentlyOpen) {
            // Close section
            contentDiv.style.display = 'none';
            toggleIcon.innerHTML = '▼';
            toggleIcon.style.transform = 'rotate(0deg)';
        } else {
            // Open section
            contentDiv.style.display = 'block';
            toggleIcon.innerHTML = '▲';
            toggleIcon.style.transform = 'rotate(0deg)';
        }

        // Save state to localStorage
        this.saveAccordionState(sectionId, !isCurrentlyOpen);
        
        this.logger.debug('messageManagerElements', `Toggled accordion section ${sectionId}: ${!isCurrentlyOpen ? 'open' : 'closed'}`);
    }

    /**
     * Save accordion state to localStorage
     */
    saveAccordionState(sectionId, isOpen) {
        try {
            const postId = this.getPostId();
            const key = `accordion_state_${postId}_${sectionId}`;
            localStorage.setItem(key, isOpen ? 'open' : 'closed');
        } catch (error) {
            this.logger.warn('messageManagerElements', 'Failed to save accordion state:', error);
        }
    }

    /**
     * Load accordion state from localStorage
     */
    loadAccordionState(sectionId) {
        try {
            const postId = this.getPostId();
            const key = `accordion_state_${postId}_${sectionId}`;
            const state = localStorage.getItem(key);
            return state === 'open';
        } catch (error) {
            this.logger.warn('messageManagerElements', 'Failed to load accordion state:', error);
            return false; // Default to closed
        }
    }

    /**
     * Reorder element up or down
     */
    reorderElement(elementId, direction) {
        const container = document.querySelector('.elements-container');
        if (!container) return;

        const currentElement = container.querySelector(`[data-element-id="${elementId}"]`);
        if (!currentElement) return;

        const allElements = Array.from(container.children);
        const currentIndex = allElements.indexOf(currentElement);

        if (direction === 'up' && currentIndex > 0) {
            // Move up
            const previousElement = allElements[currentIndex - 1];
            container.insertBefore(currentElement, previousElement);
            this.saveElementOrder();
            this.logger.debug('messageManagerElements', `Moved element ${elementId} up`);
        } else if (direction === 'down' && currentIndex < allElements.length - 1) {
            // Move down
            const nextElement = allElements[currentIndex + 1];
            container.insertBefore(currentElement, nextElement.nextSibling);
            this.saveElementOrder();
            this.logger.debug('messageManagerElements', `Moved element ${elementId} down`);
        }
    }

    /**
     * Save element order to localStorage
     */
    saveElementOrder() {
        try {
            const container = document.querySelector('.elements-container');
            if (!container) return;

            const elementOrder = Array.from(container.children).map(element => 
                element.getAttribute('data-element-id')
            );

            const postId = this.getPostId();
            const key = `element_order_${postId}`;
            localStorage.setItem(key, JSON.stringify(elementOrder));
            
            this.logger.debug('messageManagerElements', 'Saved element order:', elementOrder);
        } catch (error) {
            this.logger.warn('messageManagerElements', 'Failed to save element order:', error);
        }
    }

    /**
     * Load element order from localStorage
     */
    loadElementOrder() {
        try {
            const postId = this.getPostId();
            const key = `element_order_${postId}`;
            const savedOrder = localStorage.getItem(key);
            
            if (savedOrder) {
                return JSON.parse(savedOrder);
            }
        } catch (error) {
            this.logger.warn('messageManagerElements', 'Failed to load element order:', error);
        }
        
        // Return default order if no saved order
        return ELEMENT_CONFIGS.map(config => config.id);
    }

    /**
     * Apply saved element order
     */
    applyElementOrder() {
        const container = document.querySelector('.elements-container');
        if (!container) return;

        const savedOrder = this.loadElementOrder();
        const currentElements = Array.from(container.children);

        // Create a map of current elements by ID
        const elementMap = new Map();
        currentElements.forEach(element => {
            const id = element.getAttribute('data-element-id');
            elementMap.set(id, element);
        });

        // Reorder elements according to saved order
        savedOrder.forEach(elementId => {
            const element = elementMap.get(elementId);
            if (element) {
                container.appendChild(element);
            }
        });

        this.logger.debug('messageManagerElements', 'Applied saved element order:', savedOrder);
    }

    /**
     * Load all accordion states and apply them
     */
    loadAccordionStates() {
        for (const [elementId, elementData] of this.elements) {
            const isOpen = this.loadAccordionState(elementId);
            const contentDiv = elementData.element.querySelector('.accordion-content');
            const toggleIcon = elementData.element.querySelector('.accordion-toggle-icon');
            
            if (contentDiv && toggleIcon) {
                if (isOpen) {
                    contentDiv.style.display = 'block';
                    toggleIcon.innerHTML = '▲';
                } else {
                    contentDiv.style.display = 'none';
                    toggleIcon.innerHTML = '▼';
                }
            }
        }
        this.logger.debug('messageManagerElements', 'Loaded accordion states');
    }



    /**
     * Update context
     */
    updateContext(context) {
        this.context = context;
        this.logger.debug('messageManagerElements', 'Context updated:', context);
    }
}

// Create and export the elements module
const messageManagerElements = new MessageManagerElements();

// Make it globally available
window.MessageManagerElements = messageManagerElements; 