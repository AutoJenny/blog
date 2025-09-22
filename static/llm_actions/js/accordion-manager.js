/**
 * Accordion Manager Module
 *
 * Responsibilities:
 * - Manage accordion functionality (expand/collapse)
 * - Handle accordion state and animations
 * - Coordinate accordion interactions
 * - Provide accordion API for other modules
 *
 * Dependencies: logger.js
 * Dependents: None
 *
 * @version 1.0
 */

// Accordion state
const ACCORDION_STATE = {
    // Accordion sections
    sections: {},
    
    // Active section
    activeSection: null,
    
    // Animation settings
    animationDuration: 300,
    easing: 'ease-in-out',
    
    // UI state
    initialized: false,
    animating: false
};

/**
 * Accordion Manager class
 */
class AccordionManager {
    constructor() {
        this.logger = window.logger;
        this.context = null;
        this.initialized = false;
    }

    /**
     * Initialize the accordion manager
     */
    async initialize(context) {
        this.logger.trace('accordionManager', 'initialize', 'enter');
        this.context = context;
        
        try {
            // Initialize accordion sections
            await this.initializeAccordionSections();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Set initial state
            this.setInitialState();
            
            this.initialized = true;
            ACCORDION_STATE.initialized = true;
            
            this.logger.info('accordionManager', 'Accordion manager initialized');
            
        } catch (error) {
            this.logger.error('accordionManager', 'Failed to initialize accordion manager:', error);
            throw error;
        }
        
        this.logger.trace('accordionManager', 'initialize', 'exit');
    }

    /**
     * Initialize accordion sections
     */
    async initializeAccordionSections() {
        this.logger.trace('accordionManager', 'initializeAccordionSections', 'enter');
        
        // Find all accordion sections
        const accordionSections = document.querySelectorAll('.accordion-section, [data-accordion-section]');
        this.logger.debug('accordionManager', `Found ${accordionSections.length} accordion sections`);
        
        for (const section of accordionSections) {
            await this.initializeSingleSection(section);
        }
        
        this.logger.trace('accordionManager', 'initializeAccordionSections', 'exit');
    }

    /**
     * Initialize a single accordion section
     */
    async initializeSingleSection(section) {
        const sectionId = section.id || section.getAttribute('data-accordion-section');
        const sectionTitle = section.getAttribute('data-accordion-title') || 'Section';
        const isInitiallyOpen = section.hasAttribute('data-accordion-open');
        
        this.logger.debug('accordionManager', `Initializing accordion section: ${sectionId}`);
        
        // Find header and content elements
        const header = section.querySelector('.accordion-header, [data-accordion-header]');
        const content = section.querySelector('.accordion-content, [data-accordion-content]');
        
        if (!header || !content) {
            this.logger.warn('accordionManager', `Missing header or content for section: ${sectionId}`);
            return;
        }
        
        // Store section reference
        ACCORDION_STATE.sections[sectionId] = {
            element: section,
            header: header,
            content: content,
            title: sectionTitle,
            isOpen: isInitiallyOpen,
            height: content.scrollHeight
        };
        
        // Set up section-specific event listeners
        this.setupSectionEventListeners(section, sectionId);
        
        // Set initial state
        this.setSectionState(sectionId, isInitiallyOpen);
    }

    /**
     * Set up section-specific event listeners
     */
    setupSectionEventListeners(section, sectionId) {
        const header = ACCORDION_STATE.sections[sectionId].header;
        
        // Click event for toggle
        header.addEventListener('click', (event) => {
            event.preventDefault();
            this.toggleSection(sectionId);
        });
        
        // Keyboard support
        header.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                this.toggleSection(sectionId);
            }
        });
        
        // Make header focusable
        header.setAttribute('tabindex', '0');
        header.setAttribute('role', 'button');
        header.setAttribute('aria-expanded', 'false');
        header.setAttribute('aria-controls', `${sectionId}-content`);
        
        // Set content attributes
        const content = ACCORDION_STATE.sections[sectionId].content;
        content.setAttribute('id', `${sectionId}-content`);
        content.setAttribute('role', 'region');
        content.setAttribute('aria-labelledby', `${sectionId}-header`);
    }

    /**
     * Set initial accordion state
     */
    setInitialState() {
        // Find first open section or default to first section
        let firstOpenSection = null;
        
        for (const [sectionId, section] of Object.entries(ACCORDION_STATE.sections)) {
            if (section.isOpen) {
                firstOpenSection = sectionId;
                break;
            }
        }
        
        if (!firstOpenSection && Object.keys(ACCORDION_STATE.sections).length > 0) {
            firstOpenSection = Object.keys(ACCORDION_STATE.sections)[0];
        }
        
        if (firstOpenSection) {
            ACCORDION_STATE.activeSection = firstOpenSection;
            this.logger.debug('accordionManager', `Initial active section: ${firstOpenSection}`);
        }
    }

    /**
     * Toggle accordion section
     */
    async toggleSection(sectionId) {
        this.logger.debug('accordionManager', `Toggling section: ${sectionId}`);
        
        const section = ACCORDION_STATE.sections[sectionId];
        if (!section) {
            this.logger.warn('accordionManager', `Section not found: ${sectionId}`);
            return;
        }
        
        if (section.isOpen) {
            await this.closeSection(sectionId);
        } else {
            await this.openSection(sectionId);
        }
    }

    /**
     * Open accordion section
     */
    async openSection(sectionId) {
        this.logger.debug('accordionManager', `Opening section: ${sectionId}`);
        
        if (ACCORDION_STATE.animating) {
            this.logger.warn('accordionManager', 'Animation in progress, ignoring open request');
            return;
        }
        
        const section = ACCORDION_STATE.sections[sectionId];
        if (!section) return;
        
        // Close other sections if accordion mode
        if (this.isAccordionMode()) {
            await this.closeAllSections();
        }
        
        // Update state
        section.isOpen = true;
        ACCORDION_STATE.activeSection = sectionId;
        
        // Update UI
        this.updateSectionUI(sectionId, true);
        
        // Animate open
        await this.animateSection(sectionId, true);
        
        // Emit event
        this.emitSectionEvent(sectionId, 'opened');
    }

    /**
     * Close accordion section
     */
    async closeSection(sectionId) {
        this.logger.debug('accordionManager', `Closing section: ${sectionId}`);
        
        if (ACCORDION_STATE.animating) {
            this.logger.warn('accordionManager', 'Animation in progress, ignoring close request');
            return;
        }
        
        const section = ACCORDION_STATE.sections[sectionId];
        if (!section) return;
        
        // Update state
        section.isOpen = false;
        if (ACCORDION_STATE.activeSection === sectionId) {
            ACCORDION_STATE.activeSection = null;
        }
        
        // Update UI
        this.updateSectionUI(sectionId, false);
        
        // Animate close
        await this.animateSection(sectionId, false);
        
        // Emit event
        this.emitSectionEvent(sectionId, 'closed');
    }

    /**
     * Close all sections
     */
    async closeAllSections() {
        this.logger.debug('accordionManager', 'Closing all sections');
        
        for (const sectionId of Object.keys(ACCORDION_STATE.sections)) {
            const section = ACCORDION_STATE.sections[sectionId];
            if (section.isOpen) {
                await this.closeSection(sectionId);
            }
        }
    }

    /**
     * Open all sections
     */
    async openAllSections() {
        this.logger.debug('accordionManager', 'Opening all sections');
        
        for (const sectionId of Object.keys(ACCORDION_STATE.sections)) {
            const section = ACCORDION_STATE.sections[sectionId];
            if (!section.isOpen) {
                await this.openSection(sectionId);
            }
        }
    }

    /**
     * Animate section
     */
    async animateSection(sectionId, isOpening) {
        const section = ACCORDION_STATE.sections[sectionId];
        if (!section) return;
        
        ACCORDION_STATE.animating = true;
        
        const content = section.content;
        const targetHeight = isOpening ? section.height : 0;
        
        // Set initial state
        if (isOpening) {
            content.style.height = '0px';
            content.style.overflow = 'hidden';
            content.style.display = 'block';
        }
        
        // Animate
        return new Promise((resolve) => {
            const startTime = performance.now();
            const startHeight = isOpening ? 0 : section.height;
            
            const animate = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / ACCORDION_STATE.animationDuration, 1);
                
                // Easing function
                const easedProgress = this.easeInOut(progress);
                
                const currentHeight = startHeight + (targetHeight - startHeight) * easedProgress;
                content.style.height = `${currentHeight}px`;
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    // Animation complete
                    if (isOpening) {
                        content.style.height = 'auto';
                        content.style.overflow = 'visible';
                    } else {
                        content.style.display = 'none';
                    }
                    
                    ACCORDION_STATE.animating = false;
                    resolve();
                }
            };
            
            requestAnimationFrame(animate);
        });
    }

    /**
     * Easing function
     */
    easeInOut(t) {
        return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    }

    /**
     * Update section UI
     */
    updateSectionUI(sectionId, isOpen) {
        const section = ACCORDION_STATE.sections[sectionId];
        if (!section) return;
        
        const { header, content, element } = section;
        
        // Update classes
        element.classList.toggle('accordion-open', isOpen);
        element.classList.toggle('accordion-closed', !isOpen);
        
        // Update header
        header.classList.toggle('accordion-header-open', isOpen);
        header.classList.toggle('accordion-header-closed', !isOpen);
        
        // Update content
        content.classList.toggle('accordion-content-open', isOpen);
        content.classList.toggle('accordion-content-closed', !isOpen);
        
        // Update ARIA attributes
        header.setAttribute('aria-expanded', isOpen.toString());
        
        // Update icon if present
        this.updateSectionIcon(sectionId, isOpen);
    }

    /**
     * Update section icon
     */
    updateSectionIcon(sectionId, isOpen) {
        const section = ACCORDION_STATE.sections[sectionId];
        if (!section) return;
        
        const icon = section.header.querySelector('.accordion-icon, [data-accordion-icon]');
        if (!icon) return;
        
        // Update icon class or content
        if (icon.classList.contains('accordion-icon')) {
            icon.classList.toggle('accordion-icon-open', isOpen);
            icon.classList.toggle('accordion-icon-closed', !isOpen);
        } else {
            icon.textContent = isOpen ? '−' : '+';
        }
    }

    /**
     * Set section state without animation
     */
    setSectionState(sectionId, isOpen) {
        const section = ACCORDION_STATE.sections[sectionId];
        if (!section) return;
        
        section.isOpen = isOpen;
        
        if (isOpen) {
            section.content.style.display = 'block';
            section.content.style.height = 'auto';
            section.content.style.overflow = 'visible';
            ACCORDION_STATE.activeSection = sectionId;
        } else {
            section.content.style.display = 'none';
            section.content.style.height = '0px';
            section.content.style.overflow = 'hidden';
        }
        
        this.updateSectionUI(sectionId, isOpen);
    }

    /**
     * Check if accordion mode is enabled
     */
    isAccordionMode() {
        const container = document.querySelector('.accordion-container, [data-accordion-mode]');
        if (!container) return true; // Default to accordion mode
        
        const mode = container.getAttribute('data-accordion-mode');
        return mode !== 'independent';
    }

    /**
     * Get section state
     */
    getSectionState(sectionId) {
        const section = ACCORDION_STATE.sections[sectionId];
        return section ? {
            isOpen: section.isOpen,
            title: section.title,
            height: section.height
        } : null;
    }

    /**
     * Get all section states
     */
    getAllSectionStates() {
        const states = {};
        for (const [sectionId, section] of Object.entries(ACCORDION_STATE.sections)) {
            states[sectionId] = {
                isOpen: section.isOpen,
                title: section.title,
                height: section.height
            };
        }
        return states;
    }

    /**
     * Get active section
     */
    getActiveSection() {
        return ACCORDION_STATE.activeSection;
    }

    /**
     * Set animation duration
     */
    setAnimationDuration(duration) {
        ACCORDION_STATE.animationDuration = duration;
        this.logger.debug('accordionManager', `Animation duration set to: ${duration}ms`);
    }

    /**
     * Emit section event
     */
    emitSectionEvent(sectionId, action) {
        const event = new CustomEvent('accordionSectionChanged', {
            detail: {
                sectionId: sectionId,
                action: action,
                timestamp: Date.now()
            }
        });
        document.dispatchEvent(event);
        
        this.logger.debug('accordionManager', `Section event emitted: ${sectionId} ${action}`);
    }

    /**
     * Set up global event listeners
     */
    setupEventListeners() {
        // Listen for external toggle requests
        document.addEventListener('toggleAccordionSection', (event) => {
            const { sectionId } = event.detail;
            this.toggleSection(sectionId);
        });
        
        // Listen for open all requests
        document.addEventListener('openAllAccordionSections', () => {
            this.openAllSections();
        });
        
        // Listen for close all requests
        document.addEventListener('closeAllAccordionSections', () => {
            this.closeAllSections();
        });
        
        // Listen for animation duration changes
        document.addEventListener('setAccordionAnimationDuration', (event) => {
            const { duration } = event.detail;
            this.setAnimationDuration(duration);
        });
    }

    /**
     * Get current state
     */
    getState() {
        return { ...ACCORDION_STATE };
    }

    /**
     * Refresh accordion
     */
    refresh() {
        this.logger.info('accordionManager', 'Refreshing accordion');
        
        // Recalculate heights
        for (const [sectionId, section] of Object.entries(ACCORDION_STATE.sections)) {
            if (section.isOpen) {
                section.height = section.content.scrollHeight;
            }
        }
    }

    /**
     * Cleanup
     */
    destroy() {
        this.logger.info('accordionManager', 'Destroying accordion manager');
        this.initialized = false;
        ACCORDION_STATE.initialized = false;
    }
}

// Create and register the module instance
const accordionManager = new AccordionManager();
window.accordionManager = accordionManager;
window.ACCORDION_STATE = ACCORDION_STATE;
window.registerLLMModule('accordionManager', accordionManager);

// Log initialization
if (window.logger) {
    window.logger.info('accordionManager', 'Accordion Manager Module loaded');
} 