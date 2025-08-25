/**
 * Section Gatherer Module
 *
 * Responsibilities:
 * - Gather sections from the post-sections iframe
 * - Handle section selection and filtering
 * - Provide section data to LLM processor
 * - Manage section state and UI
 *
 * Dependencies: logger.js
 * Dependents: llm-processor.js
 *
 * @version 1.0
 */

// Section state
const SECTION_STATE = {
    // All available sections
    allSections: [],
    
    // Selected sections for processing
    selectedSections: [],
    
    // Section loading state
    loading: false,
    loaded: false,
    
    // UI state
    selectionMode: 'all', // 'all', 'selected', 'custom'
    customSectionIds: []
};

/**
 * Section Gatherer class
 */
class SectionGatherer {
    constructor() {
        this.logger = window.logger;
        this.context = null;
        this.initialized = false;
        this.iframe = null;
    }

    /**
     * Initialize the section gatherer
     */
    async initialize(context) {
        this.logger.trace('sectionGatherer', 'initialize', 'enter');
        this.context = context;
        
        try {
            // Find the post-sections iframe
            this.findPostSectionsIframe();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Load initial sections
            await this.loadSections();
            
            this.initialized = true;
            this.logger.info('sectionGatherer', 'Section gatherer initialized');
            
        } catch (error) {
            this.logger.error('sectionGatherer', 'Failed to initialize section gatherer:', error);
            throw error;
        }
        
        this.logger.trace('sectionGatherer', 'initialize', 'exit');
    }

    /**
     * Find the post-sections iframe
     */
    findPostSectionsIframe() {
        // Look for iframe with post-sections
        const iframes = document.querySelectorAll('iframe');
        for (const iframe of iframes) {
            if (iframe.src && iframe.src.includes('post-sections')) {
                this.iframe = iframe;
                this.logger.debug('sectionGatherer', 'Found post-sections iframe');
                break;
            }
        }
        
        if (!this.iframe) {
            this.logger.warn('sectionGatherer', 'Post-sections iframe not found');
        }
    }

    /**
     * Load sections from the post-sections iframe
     */
    async loadSections() {
        this.logger.trace('sectionGatherer', 'loadSections', 'enter');
        
        if (!this.iframe) {
            this.logger.warn('sectionGatherer', 'No iframe available for loading sections');
            return;
        }
        
        SECTION_STATE.loading = true;
        
        try {
            // Wait for iframe to be ready
            await this.waitForIframeReady();
            
            // Get sections from iframe
            const sections = await this.getSectionsFromIframe();
            
            SECTION_STATE.allSections = sections;
            SECTION_STATE.loaded = true;
            
            this.logger.debug('sectionGatherer', `Loaded ${sections.length} sections`);
            
            // Update selected sections based on current mode
            this.updateSelectedSections();
            
        } catch (error) {
            this.logger.error('sectionGatherer', 'Failed to load sections:', error);
            SECTION_STATE.allSections = [];
        } finally {
            SECTION_STATE.loading = false;
        }
        
        this.logger.trace('sectionGatherer', 'loadSections', 'exit');
    }

    /**
     * Wait for iframe to be ready
     */
    async waitForIframeReady() {
        let attempts = 0;
        const maxAttempts = 50; // 5 seconds max
        
        while (attempts < maxAttempts) {
            try {
                if (this.iframe.contentDocument && this.iframe.contentWindow) {
                    return;
                }
            } catch (error) {
                // Cross-origin iframe, try different approach
                break;
            }
            
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        this.logger.warn('sectionGatherer', 'Iframe not ready after 5 seconds');
    }

    /**
     * Get sections from iframe
     */
    async getSectionsFromIframe() {
        try {
            // Try to access iframe content directly
            if (this.iframe.contentWindow && this.iframe.contentWindow.getSections) {
                return await this.iframe.contentWindow.getSections();
            }
            
            // Fallback: try to communicate via postMessage
            return await this.getSectionsViaPostMessage();
            
        } catch (error) {
            this.logger.error('sectionGatherer', 'Failed to get sections from iframe:', error);
            return [];
        }
    }

    /**
     * Get sections via postMessage
     */
    async getSectionsViaPostMessage() {
        return new Promise((resolve) => {
            const timeout = setTimeout(() => {
                this.logger.warn('sectionGatherer', 'PostMessage timeout, using empty sections');
                resolve([]);
            }, 3000);
            
            const handler = (event) => {
                if (event.data && event.data.type === 'sections-response') {
                    clearTimeout(timeout);
                    window.removeEventListener('message', handler);
                    resolve(event.data.sections || []);
                }
            };
            
            window.addEventListener('message', handler);
            
            // Send request to iframe
            this.iframe.contentWindow.postMessage({
                type: 'get-sections',
                postId: this.context.post_id
            }, '*');
        });
    }

    /**
     * Update selected sections based on current mode
     */
    updateSelectedSections() {
        switch (SECTION_STATE.selectionMode) {
            case 'all':
                SECTION_STATE.selectedSections = [...SECTION_STATE.allSections];
                break;
                
            case 'selected':
                SECTION_STATE.selectedSections = SECTION_STATE.allSections.filter(section => 
                    section.selected || section.checked
                );
                break;
                
            case 'custom':
                SECTION_STATE.selectedSections = SECTION_STATE.allSections.filter(section =>
                    SECTION_STATE.customSectionIds.includes(section.id)
                );
                break;
        }
        
        this.logger.debug('sectionGatherer', `Selected ${SECTION_STATE.selectedSections.length} sections`);
    }

    /**
     * Set selection mode
     */
    setSelectionMode(mode) {
        this.logger.debug('sectionGatherer', `Setting selection mode to: ${mode}`);
        SECTION_STATE.selectionMode = mode;
        this.updateSelectedSections();
        this.updateUI();
    }

    /**
     * Set custom section IDs
     */
    setCustomSectionIds(sectionIds) {
        this.logger.debug('sectionGatherer', 'Setting custom section IDs:', sectionIds);
        SECTION_STATE.customSectionIds = sectionIds;
        if (SECTION_STATE.selectionMode === 'custom') {
            this.updateSelectedSections();
            this.updateUI();
        }
    }

    /**
     * Get sections for processing
     */
    getSectionsForProcessing() {
        return SECTION_STATE.selectedSections;
    }

    /**
     * Get section by ID
     */
    getSectionById(sectionId) {
        return SECTION_STATE.allSections.find(section => section.id == sectionId);
    }

    /**
     * Refresh sections
     */
    async refresh() {
        this.logger.info('sectionGatherer', 'Refreshing sections');
        await this.loadSections();
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Listen for section selection changes
        const allRadio = document.getElementById('section-mode-all');
        const selectedRadio = document.getElementById('section-mode-selected');
        const customRadio = document.getElementById('section-mode-custom');
        
        if (allRadio) {
            allRadio.addEventListener('change', () => this.setSelectionMode('all'));
        }
        
        if (selectedRadio) {
            selectedRadio.addEventListener('change', () => this.setSelectionMode('selected'));
        }
        
        if (customRadio) {
            customRadio.addEventListener('change', () => this.setSelectionMode('custom'));
        }
        
        // Listen for custom section input
        const customInput = document.getElementById('custom-section-ids');
        if (customInput) {
            customInput.addEventListener('change', (event) => {
                const ids = event.target.value.split(',').map(id => id.trim()).filter(id => id);
                this.setCustomSectionIds(ids);
            });
        }
        
        this.logger.debug('sectionGatherer', 'Event listeners set up');
    }

    /**
     * Update UI elements
     */
    updateUI() {
        // Update selection mode radio buttons
        const allRadio = document.getElementById('section-mode-all');
        const selectedRadio = document.getElementById('section-mode-selected');
        const customRadio = document.getElementById('section-mode-custom');
        
        if (allRadio) allRadio.checked = SECTION_STATE.selectionMode === 'all';
        if (selectedRadio) selectedRadio.checked = SECTION_STATE.selectionMode === 'selected';
        if (customRadio) customRadio.checked = SECTION_STATE.selectionMode === 'custom';
        
        // Update section count display
        const countDisplay = document.getElementById('section-count');
        if (countDisplay) {
            countDisplay.textContent = `${SECTION_STATE.selectedSections.length} of ${SECTION_STATE.allSections.length} sections`;
        }
        
        // Update section list display
        this.updateSectionListDisplay();
    }

    /**
     * Update section list display
     */
    updateSectionListDisplay() {
        const listContainer = document.getElementById('section-list');
        if (!listContainer) return;
        
        listContainer.innerHTML = '';
        
        SECTION_STATE.selectedSections.forEach(section => {
            const item = document.createElement('div');
            item.className = 'section-item';
            item.innerHTML = `
                <span class="section-id">${section.id}</span>
                <span class="section-title">${section.title || 'Untitled'}</span>
                <span class="section-type">${section.type || 'text'}</span>
            `;
            listContainer.appendChild(item);
        });
    }

    /**
     * Get current state
     */
    getState() {
        return { ...SECTION_STATE };
    }

    /**
     * Check if sections are ready
     */
    isReady() {
        return SECTION_STATE.loaded && SECTION_STATE.selectedSections.length > 0;
    }

    /**
     * Cleanup
     */
    destroy() {
        this.logger.info('sectionGatherer', 'Destroying section gatherer');
        this.initialized = false;
        this.iframe = null;
    }
}

// Create and export global instance
const sectionGatherer = new SectionGatherer();
window.sectionGatherer = sectionGatherer;
window.SECTION_STATE = SECTION_STATE;

// Log initialization
if (window.logger) {
    window.logger.info('sectionGatherer', 'Section Gatherer Module loaded');
} 