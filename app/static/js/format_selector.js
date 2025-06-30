/**
 * Format Selector JavaScript
 * Handles format template selection and preview in LLM panels
 */

export class FormatSelector {
    constructor() {
        console.log('[DEBUG] FormatSelector constructor called');
        this.formatTemplates = [];
        this.currentFormats = {};
        this.initialize();
    }

    async initialize() {
        console.log('[DEBUG] FormatSelector.initialize() called');
        
        try {
            // Load format templates
            await this.loadFormatTemplates();
            
            // Initialize format selectors
            this.initializeFormatSelectors();
            
            // Load current format selections
            await this.loadCurrentFormats();
            
            console.log('[DEBUG] Format selector initialization complete');
        } catch (error) {
            console.error('Error initializing format selector:', error);
        }
    }

    async loadFormatTemplates() {
        try {
            console.log('[DEBUG] Loading format templates...');
            const response = await fetch('/api/workflow/formats/templates');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.formatTemplates = await response.json();
            console.log('[DEBUG] Loaded', this.formatTemplates.length, 'format templates');
        } catch (error) {
            console.error('Error loading format templates:', error);
            this.formatTemplates = [];
        }
    }

    async loadCurrentFormats() {
        try {
            const stepId = this.getStepId();
            if (!stepId) {
                console.warn('Step ID not found, cannot load current formats');
                return;
            }

            console.log('[DEBUG] Loading current formats for step:', stepId);
            const response = await fetch(`/api/workflow/steps/${stepId}/formats`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const currentFormats = await response.json();
            console.log('[DEBUG] Current formats loaded:', currentFormats);
            
            // Set current selections in dropdowns
            this.setCurrentSelections(currentFormats);
        } catch (error) {
            console.error('Error loading current formats:', error);
        }
    }

    setCurrentSelections(currentFormats) {
        const inputSelector = document.querySelector('.format-selector[data-section="input"]');
        const outputSelector = document.querySelector('.format-selector[data-section="output"]');
        
        if (inputSelector && currentFormats.input_format_id) {
            inputSelector.value = currentFormats.input_format_id;
            console.log('[DEBUG] Set input format selection:', currentFormats.input_format_id);
        }
        
        if (outputSelector && currentFormats.output_format_id) {
            outputSelector.value = currentFormats.output_format_id;
            console.log('[DEBUG] Set output format selection:', currentFormats.output_format_id);
        }
    }

    getStepId() {
        // Try multiple ways to get step ID
        const stepId = document.querySelector('[data-step-id]')?.dataset.stepId ||
                      document.querySelector('[data-current-step]')?.dataset.stepId ||
                      document.querySelector('[data-current-stage]')?.dataset.stepId;
        
        console.log('[DEBUG] Retrieved step ID:', stepId);
        return stepId;
    }

    initializeFormatSelectors() {
        console.log('[DEBUG] initializeFormatSelectors() called');
        
        // Get all format selectors
        const selectors = document.querySelectorAll('.format-selector');
        console.log('[DEBUG] Found', selectors.length, 'format selectors');
        
        selectors.forEach((selector, index) => {
            console.log(`[DEBUG] Processing format selector ${index}:`, selector.id || selector.className);
            
            if (!selector) {
                console.warn('Format selector element not found');
                return;
            }

            // Clear existing options
            selector.innerHTML = '<option value="">Select format...</option>';
            
            // Get section (input/output)
            const section = selector.dataset.section;
            
            console.log(`[DEBUG] Format selector ${index} section:`, section);
            
            // Add format options based on section
            this.formatTemplates.forEach(format => {
                if (format.format_type === section || format.format_type === 'bidirectional') {
                    const option = document.createElement('option');
                    option.value = format.id;
                    option.textContent = format.name;
                    selector.appendChild(option);
                }
            });
            
            console.log(`[DEBUG] Format selector ${index} now has ${selector.options.length} options`);
            
            // Add event listener for format selection
            this.addFormatSelectorEventListener(selector);
        });
    }

    addFormatSelectorEventListener(selector) {
        const handler = (event) => {
            const formatId = event.target.value;
            const section = selector.dataset.section;
            
            console.log(`[DEBUG] Format selected: ${formatId} for section: ${section}`);
            
            if (formatId) {
                this.showFormatPreview(formatId, section);
                this.saveFormatSelection(formatId, section);
            } else {
                this.hideFormatPreview(section);
            }
        };

        // Remove existing listener if any
        selector.removeEventListener('change', handler);
        selector.addEventListener('change', handler);
    }

    showFormatPreview(formatId, section) {
        const format = this.formatTemplates.find(f => f.id === parseInt(formatId));
        if (format) {
            try {
                const spec = JSON.parse(format.format_spec);
                const previewElement = document.getElementById(`${section}_format_preview`);
                if (previewElement) {
                    previewElement.innerHTML = `
                        <div class="mt-2 p-3 bg-dark-hover rounded text-sm">
                            <h4 class="font-medium text-dark-text mb-2">Format Preview</h4>
                            <pre class="bg-dark-bg p-2 rounded overflow-x-auto text-xs">${JSON.stringify(spec, null, 2)}</pre>
                        </div>
                    `;
                    previewElement.classList.remove('hidden');
                }
            } catch (error) {
                console.error('Error parsing format specification:', error);
            }
        }
    }

    hideFormatPreview(section) {
        const previewElement = document.getElementById(`${section}_format_preview`);
        if (previewElement) {
            previewElement.classList.add('hidden');
        }
    }

    async saveFormatSelection(formatId, section) {
        try {
            const stepId = this.getStepId();
            
            if (!stepId) {
                console.warn('Step ID not found in page context, cannot save format selection');
                return;
            }

            // Get current selections from both dropdowns
            const inputSelector = document.querySelector('.format-selector[data-section="input"]');
            const outputSelector = document.querySelector('.format-selector[data-section="output"]');
            
            const inputFormatId = inputSelector ? inputSelector.value || null : null;
            const outputFormatId = outputSelector ? outputSelector.value || null : null;

            // Save format selection to step-level endpoint
            const response = await fetch(`/api/workflow/steps/${stepId}/formats`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    input_format_id: inputFormatId,
                    output_format_id: outputFormatId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            console.log(`[DEBUG] Format selection saved for step ${stepId}:`, { inputFormatId, outputFormatId });
        } catch (error) {
            console.error('Error saving format selection:', error);
        }
    }

    // Public method to refresh format templates
    async refresh() {
        await this.loadFormatTemplates();
        this.initializeFormatSelectors();
        await this.loadCurrentFormats();
    }
} 