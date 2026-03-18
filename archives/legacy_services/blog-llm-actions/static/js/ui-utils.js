/**
 * UI Utils Module
 *
 * Responsibilities:
 * - Provide common UI utility functions
 * - Handle DOM manipulation helpers
 * - Manage UI state and animations
 * - Provide form validation utilities
 * - Handle responsive design helpers
 * - Manage accessibility features
 *
 * Dependencies: logger.js
 * Dependents: All other modules
 *
 * @version 1.0
 */

// UI Utils state
const UI_UTILS_STATE = {
    // UI state
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    screenSize: 'desktop',
    
    // Animation state
    animations: {
        enabled: true,
        duration: 300,
        easing: 'ease-in-out'
    },
    
    // Form validation
    validation: {
        enabled: true,
        showErrors: true,
        errorClass: 'is-invalid',
        successClass: 'is-valid'
    },
    
    // Accessibility
    accessibility: {
        enabled: true,
        focusVisible: true,
        keyboardNavigation: true,
        screenReaderSupport: true
    },
    
    // UI components
    components: {
        tooltips: {},
        modals: {},
        dropdowns: {},
        notifications: {}
    },
    
    // Settings
    settings: {
        enableAnimations: true,
        enableTooltips: true,
        enableNotifications: true,
        enableKeyboardShortcuts: true,
        enableResponsiveDesign: true
    },
    
    // UI state
    initialized: false
};

/**
 * UI Utils class
 */
class UIUtils {
    constructor() {
        this.logger = window.logger;
        this.context = null;
        this.initialized = false;
        this.resizeTimeout = null;
        this.keyboardShortcuts = new Map();
    }

    /**
     * Initialize the UI utils
     */
    async initialize(context) {
        this.logger.trace('uiUtils', 'initialize', 'enter');
        this.context = context;
        
        try {
            // Detect screen size
            this.detectScreenSize();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Initialize UI components
            this.initializeUIComponents();
            
            // Set up keyboard shortcuts
            this.setupKeyboardShortcuts();
            
            // Initialize accessibility features
            this.initializeAccessibility();
            
            this.initialized = true;
            UI_UTILS_STATE.initialized = true;
            
            this.logger.info('uiUtils', 'UI Utils initialized');
            
        } catch (error) {
            this.logger.error('uiUtils', 'Failed to initialize UI Utils:', error);
            throw error;
        }
        
        this.logger.trace('uiUtils', 'initialize', 'exit');
    }

    /**
     * Detect screen size
     */
    detectScreenSize() {
        const width = window.innerWidth;
        
        if (width < 768) {
            UI_UTILS_STATE.isMobile = true;
            UI_UTILS_STATE.isTablet = false;
            UI_UTILS_STATE.isDesktop = false;
            UI_UTILS_STATE.screenSize = 'mobile';
        } else if (width < 1024) {
            UI_UTILS_STATE.isMobile = false;
            UI_UTILS_STATE.isTablet = true;
            UI_UTILS_STATE.isDesktop = false;
            UI_UTILS_STATE.screenSize = 'tablet';
        } else {
            UI_UTILS_STATE.isMobile = false;
            UI_UTILS_STATE.isTablet = false;
            UI_UTILS_STATE.isDesktop = true;
            UI_UTILS_STATE.screenSize = 'desktop';
        }
        
        this.logger.debug('uiUtils', `Screen size detected: ${UI_UTILS_STATE.screenSize}`);
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Window resize
        window.addEventListener('resize', () => {
            clearTimeout(this.resizeTimeout);
            this.resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 250);
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (event) => {
            this.handleKeyboardShortcut(event);
        });
        
        // Focus management
        document.addEventListener('focusin', (event) => {
            this.handleFocusIn(event);
        });
        
        // Click outside
        document.addEventListener('click', (event) => {
            this.handleClickOutside(event);
        });
    }

    /**
     * Handle window resize
     */
    handleResize() {
        const oldSize = UI_UTILS_STATE.screenSize;
        this.detectScreenSize();
        
        if (oldSize !== UI_UTILS_STATE.screenSize) {
            this.logger.debug('uiUtils', `Screen size changed from ${oldSize} to ${UI_UTILS_STATE.screenSize}`);
            
            // Emit resize event
            this.emitUIEvent('screenSizeChange', {
                oldSize: oldSize,
                newSize: UI_UTILS_STATE.screenSize
            });
        }
    }

    /**
     * Initialize UI components
     */
    initializeUIComponents() {
        // Initialize tooltips
        this.initializeTooltips();
        
        // Initialize modals
        this.initializeModals();
        
        // Initialize dropdowns
        this.initializeDropdowns();
        
        // Initialize notifications
        this.initializeNotifications();
    }

    /**
     * Initialize tooltips
     */
    initializeTooltips() {
        if (!UI_UTILS_STATE.settings.enableTooltips) return;
        
        // Find all tooltip elements
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        
        tooltipElements.forEach(element => {
            this.createTooltip(element);
        });
        
        this.logger.debug('uiUtils', `Initialized ${tooltipElements.length} tooltips`);
    }

    /**
     * Create tooltip
     */
    createTooltip(element) {
        const tooltipText = element.getAttribute('data-tooltip');
        const tooltipId = `tooltip-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        // Create tooltip element
        const tooltip = document.createElement('div');
        tooltip.className = 'ui-tooltip';
        tooltip.id = tooltipId;
        tooltip.textContent = tooltipText;
        tooltip.style.display = 'none';
        
        document.body.appendChild(tooltip);
        
        // Store reference
        UI_UTILS_STATE.components.tooltips[tooltipId] = {
            element: tooltip,
            target: element,
            text: tooltipText
        };
        
        // Add event listeners
        element.addEventListener('mouseenter', () => {
            this.showTooltip(tooltipId);
        });
        
        element.addEventListener('mouseleave', () => {
            this.hideTooltip(tooltipId);
        });
    }

    /**
     * Show tooltip
     */
    showTooltip(tooltipId) {
        const tooltip = UI_UTILS_STATE.components.tooltips[tooltipId];
        if (!tooltip) return;
        
        const rect = tooltip.target.getBoundingClientRect();
        
        tooltip.element.style.left = `${rect.left + rect.width / 2}px`;
        tooltip.element.style.top = `${rect.top - 10}px`;
        tooltip.element.style.display = 'block';
        
        // Add animation
        if (UI_UTILS_STATE.animations.enabled) {
            tooltip.element.style.opacity = '0';
            tooltip.element.style.transform = 'translateY(10px)';
            
            setTimeout(() => {
                tooltip.element.style.opacity = '1';
                tooltip.element.style.transform = 'translateY(0)';
            }, 10);
        }
    }

    /**
     * Hide tooltip
     */
    hideTooltip(tooltipId) {
        const tooltip = UI_UTILS_STATE.components.tooltips[tooltipId];
        if (!tooltip) return;
        
        tooltip.element.style.display = 'none';
    }

    /**
     * Initialize modals
     */
    initializeModals() {
        // Find all modal triggers
        const modalTriggers = document.querySelectorAll('[data-modal]');
        
        modalTriggers.forEach(trigger => {
            const modalId = trigger.getAttribute('data-modal');
            this.createModal(modalId, trigger);
        });
        
        this.logger.debug('uiUtils', `Initialized ${modalTriggers.length} modals`);
    }

    /**
     * Create modal
     */
    createModal(modalId, trigger) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        
        // Store reference
        UI_UTILS_STATE.components.modals[modalId] = {
            element: modal,
            trigger: trigger,
            isOpen: false
        };
        
        // Add event listeners
        trigger.addEventListener('click', () => {
            this.openModal(modalId);
        });
        
        // Close button
        const closeBtn = modal.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.closeModal(modalId);
            });
        }
        
        // Backdrop click
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                this.closeModal(modalId);
            }
        });
    }

    /**
     * Open modal
     */
    openModal(modalId) {
        const modal = UI_UTILS_STATE.components.modals[modalId];
        if (!modal || modal.isOpen) return;
        
        modal.isOpen = true;
        modal.element.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        // Focus first focusable element
        const firstFocusable = modal.element.querySelector('input, button, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (firstFocusable) {
            firstFocusable.focus();
        }
        
        this.logger.debug('uiUtils', `Modal opened: ${modalId}`);
    }

    /**
     * Close modal
     */
    closeModal(modalId) {
        const modal = UI_UTILS_STATE.components.modals[modalId];
        if (!modal || !modal.isOpen) return;
        
        modal.isOpen = false;
        modal.element.style.display = 'none';
        document.body.style.overflow = '';
        
        // Return focus to trigger
        if (modal.trigger) {
            modal.trigger.focus();
        }
        
        this.logger.debug('uiUtils', `Modal closed: ${modalId}`);
    }

    /**
     * Initialize dropdowns
     */
    initializeDropdowns() {
        // Find all dropdown triggers
        const dropdownTriggers = document.querySelectorAll('[data-dropdown]');
        
        dropdownTriggers.forEach(trigger => {
            const dropdownId = trigger.getAttribute('data-dropdown');
            this.createDropdown(dropdownId, trigger);
        });
        
        this.logger.debug('uiUtils', `Initialized ${dropdownTriggers.length} dropdowns`);
    }

    /**
     * Create dropdown
     */
    createDropdown(dropdownId, trigger) {
        const dropdown = document.getElementById(dropdownId);
        if (!dropdown) return;
        
        // Store reference
        UI_UTILS_STATE.components.dropdowns[dropdownId] = {
            element: dropdown,
            trigger: trigger,
            isOpen: false
        };
        
        // Add event listeners
        trigger.addEventListener('click', (event) => {
            event.preventDefault();
            this.toggleDropdown(dropdownId);
        });
    }

    /**
     * Toggle dropdown
     */
    toggleDropdown(dropdownId) {
        const dropdown = UI_UTILS_STATE.components.dropdowns[dropdownId];
        if (!dropdown) return;
        
        if (dropdown.isOpen) {
            this.closeDropdown(dropdownId);
        } else {
            this.openDropdown(dropdownId);
        }
    }

    /**
     * Open dropdown
     */
    openDropdown(dropdownId) {
        const dropdown = UI_UTILS_STATE.components.dropdowns[dropdownId];
        if (!dropdown || dropdown.isOpen) return;
        
        // Close other dropdowns
        Object.keys(UI_UTILS_STATE.components.dropdowns).forEach(id => {
            if (id !== dropdownId) {
                this.closeDropdown(id);
            }
        });
        
        dropdown.isOpen = true;
        dropdown.element.style.display = 'block';
        
        this.logger.debug('uiUtils', `Dropdown opened: ${dropdownId}`);
    }

    /**
     * Close dropdown
     */
    closeDropdown(dropdownId) {
        const dropdown = UI_UTILS_STATE.components.dropdowns[dropdownId];
        if (!dropdown || !dropdown.isOpen) return;
        
        dropdown.isOpen = false;
        dropdown.element.style.display = 'none';
        
        this.logger.debug('uiUtils', `Dropdown closed: ${dropdownId}`);
    }

    /**
     * Initialize notifications
     */
    initializeNotifications() {
        if (!UI_UTILS_STATE.settings.enableNotifications) return;
        
        // Create notification container
        const container = document.createElement('div');
        container.className = 'notification-container';
        container.id = 'notification-container';
        document.body.appendChild(container);
        
        this.logger.debug('uiUtils', 'Notification system initialized');
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info', duration = 5000) {
        if (!UI_UTILS_STATE.settings.enableNotifications) return;
        
        const container = document.getElementById('notification-container');
        if (!container) return;
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;
        
        container.appendChild(notification);
        
        // Add event listeners
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            this.hideNotification(notification);
        });
        
        // Auto hide
        if (duration > 0) {
            setTimeout(() => {
                this.hideNotification(notification);
            }, duration);
        }
        
        // Show animation
        if (UI_UTILS_STATE.animations.enabled) {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            
            setTimeout(() => {
                notification.style.opacity = '1';
                notification.style.transform = 'translateX(0)';
            }, 10);
        }
        
        this.logger.debug('uiUtils', `Notification shown: ${type} - ${message}`);
    }

    /**
     * Hide notification
     */
    hideNotification(notification) {
        if (UI_UTILS_STATE.animations.enabled) {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            
            setTimeout(() => {
                notification.remove();
            }, UI_UTILS_STATE.animations.duration);
        } else {
            notification.remove();
        }
    }

    /**
     * Set up keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        if (!UI_UTILS_STATE.settings.enableKeyboardShortcuts) return;
        
        // Register default shortcuts
        this.registerKeyboardShortcut('Escape', 'Close all modals and dropdowns', () => {
            this.closeAllModals();
            this.closeAllDropdowns();
        });
        
        this.registerKeyboardShortcut('Ctrl+S', 'Save', () => {
            this.emitUIEvent('saveRequested');
        });
        
        this.registerKeyboardShortcut('Ctrl+Z', 'Undo', () => {
            this.emitUIEvent('undoRequested');
        });
        
        this.logger.debug('uiUtils', 'Keyboard shortcuts initialized');
    }

    /**
     * Register keyboard shortcut
     */
    registerKeyboardShortcut(key, description, callback) {
        this.keyboardShortcuts.set(key, {
            description: description,
            callback: callback
        });
        
        this.logger.debug('uiUtils', `Keyboard shortcut registered: ${key} - ${description}`);
    }

    /**
     * Handle keyboard shortcut
     */
    handleKeyboardShortcut(event) {
        const key = this.getKeyCombo(event);
        const shortcut = this.keyboardShortcuts.get(key);
        
        if (shortcut) {
            event.preventDefault();
            shortcut.callback();
        }
    }

    /**
     * Get key combination
     */
    getKeyCombo(event) {
        const keys = [];
        
        if (event.ctrlKey) keys.push('Ctrl');
        if (event.altKey) keys.push('Alt');
        if (event.shiftKey) keys.push('Shift');
        if (event.metaKey) keys.push('Meta');
        
        if (event.key !== 'Control' && event.key !== 'Alt' && event.key !== 'Shift' && event.key !== 'Meta') {
            keys.push(event.key);
        }
        
        return keys.join('+');
    }

    /**
     * Initialize accessibility features
     */
    initializeAccessibility() {
        if (!UI_UTILS_STATE.accessibility.enabled) return;
        
        // Add focus visible styles
        if (UI_UTILS_STATE.accessibility.focusVisible) {
            this.addFocusVisibleStyles();
        }
        
        // Enable keyboard navigation
        if (UI_UTILS_STATE.accessibility.keyboardNavigation) {
            this.enableKeyboardNavigation();
        }
        
        // Add ARIA attributes
        if (UI_UTILS_STATE.accessibility.screenReaderSupport) {
            this.addARIAAttributes();
        }
        
        this.logger.debug('uiUtils', 'Accessibility features initialized');
    }

    /**
     * Add focus visible styles
     */
    addFocusVisibleStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .focus-visible {
                outline: 2px solid #007bff;
                outline-offset: 2px;
            }
            .focus-visible:not(:focus-visible) {
                outline: none;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Enable keyboard navigation
     */
    enableKeyboardNavigation() {
        // Add focus management to interactive elements
        const interactiveElements = document.querySelectorAll('button, input, select, textarea, a, [tabindex]');
        
        interactiveElements.forEach(element => {
            element.addEventListener('keydown', (event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    element.click();
                }
            });
        });
    }

    /**
     * Add ARIA attributes
     */
    addARIAAttributes() {
        // Add ARIA labels to form elements
        const formElements = document.querySelectorAll('input, select, textarea');
        
        formElements.forEach(element => {
            if (!element.getAttribute('aria-label') && !element.getAttribute('aria-labelledby')) {
                const label = element.closest('label');
                if (label) {
                    element.setAttribute('aria-labelledby', label.id || `label-${Date.now()}`);
                }
            }
        });
    }

    /**
     * Handle focus in
     */
    handleFocusIn(event) {
        if (UI_UTILS_STATE.accessibility.focusVisible) {
            event.target.classList.add('focus-visible');
        }
    }

    /**
     * Handle click outside
     */
    handleClickOutside(event) {
        // Close dropdowns when clicking outside
        Object.keys(UI_UTILS_STATE.components.dropdowns).forEach(dropdownId => {
            const dropdown = UI_UTILS_STATE.components.dropdowns[dropdownId];
            if (dropdown.isOpen && !dropdown.element.contains(event.target) && !dropdown.trigger.contains(event.target)) {
                this.closeDropdown(dropdownId);
            }
        });
    }

    /**
     * Close all modals
     */
    closeAllModals() {
        Object.keys(UI_UTILS_STATE.components.modals).forEach(modalId => {
            this.closeModal(modalId);
        });
    }

    /**
     * Close all dropdowns
     */
    closeAllDropdowns() {
        Object.keys(UI_UTILS_STATE.components.dropdowns).forEach(dropdownId => {
            this.closeDropdown(dropdownId);
        });
    }

    /**
     * Form validation utilities
     */
    validateForm(form) {
        const errors = [];
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            const validation = this.validateInput(input);
            if (validation.isValid === false) {
                errors.push(validation);
            }
        });
        
        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Validate input
     */
    validateInput(input) {
        const value = input.value.trim();
        const type = input.type;
        const required = input.hasAttribute('required');
        const minLength = input.getAttribute('minlength');
        const maxLength = input.getAttribute('maxlength');
        const pattern = input.getAttribute('pattern');
        
        // Required validation
        if (required && !value) {
            return {
                input: input,
                isValid: false,
                message: 'This field is required'
            };
        }
        
        // Length validation
        if (minLength && value.length < parseInt(minLength)) {
            return {
                input: input,
                isValid: false,
                message: `Minimum length is ${minLength} characters`
            };
        }
        
        if (maxLength && value.length > parseInt(maxLength)) {
            return {
                input: input,
                isValid: false,
                message: `Maximum length is ${maxLength} characters`
            };
        }
        
        // Pattern validation
        if (pattern && value && !new RegExp(pattern).test(value)) {
            return {
                input: input,
                isValid: false,
                message: 'Invalid format'
            };
        }
        
        // Type-specific validation
        switch (type) {
            case 'email':
                if (value && !this.isValidEmail(value)) {
                    return {
                        input: input,
                        isValid: false,
                        message: 'Invalid email address'
                    };
                }
                break;
            case 'url':
                if (value && !this.isValidUrl(value)) {
                    return {
                        input: input,
                        isValid: false,
                        message: 'Invalid URL'
                    };
                }
                break;
        }
        
        return {
            input: input,
            isValid: true
        };
    }

    /**
     * Show validation errors
     */
    showValidationErrors(errors) {
        if (!UI_UTILS_STATE.validation.showErrors) return;
        
        errors.forEach(error => {
            const input = error.input;
            const message = error.message;
            
            // Add error class
            input.classList.add(UI_UTILS_STATE.validation.errorClass);
            input.classList.remove(UI_UTILS_STATE.validation.successClass);
            
            // Show error message
            this.showInputError(input, message);
        });
    }

    /**
     * Show input error
     */
    showInputError(input, message) {
        // Remove existing error message
        const existingError = input.parentNode.querySelector('.input-error');
        if (existingError) {
            existingError.remove();
        }
        
        // Create error message
        const errorElement = document.createElement('div');
        errorElement.className = 'input-error text-danger';
        errorElement.textContent = message;
        
        input.parentNode.appendChild(errorElement);
    }

    /**
     * Clear validation errors
     */
    clearValidationErrors(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            input.classList.remove(UI_UTILS_STATE.validation.errorClass);
            input.classList.remove(UI_UTILS_STATE.validation.successClass);
            
            const errorElement = input.parentNode.querySelector('.input-error');
            if (errorElement) {
                errorElement.remove();
            }
        });
    }

    /**
     * Validation helpers
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    isValidUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }

    /**
     * DOM manipulation helpers
     */
    createElement(tag, className, attributes = {}) {
        const element = document.createElement(tag);
        
        if (className) {
            element.className = className;
        }
        
        Object.entries(attributes).forEach(([key, value]) => {
            element.setAttribute(key, value);
        });
        
        return element;
    }

    addClass(element, className) {
        if (element && className) {
            element.classList.add(className);
        }
    }

    removeClass(element, className) {
        if (element && className) {
            element.classList.remove(className);
        }
    }

    toggleClass(element, className) {
        if (element && className) {
            element.classList.toggle(className);
        }
    }

    hasClass(element, className) {
        return element && element.classList.contains(className);
    }

    /**
     * Animation helpers
     */
    animate(element, properties, duration = UI_UTILS_STATE.animations.duration) {
        if (!UI_UTILS_STATE.animations.enabled) {
            Object.assign(element.style, properties);
            return Promise.resolve();
        }
        
        return new Promise((resolve) => {
            const startTime = performance.now();
            const startProperties = {};
            
            // Get starting values
            Object.keys(properties).forEach(prop => {
                startProperties[prop] = parseFloat(getComputedStyle(element)[prop]) || 0;
            });
            
            const animate = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                // Apply easing
                const easedProgress = this.easeInOut(progress);
                
                // Update properties
                Object.entries(properties).forEach(([prop, endValue]) => {
                    const startValue = startProperties[prop];
                    const currentValue = startValue + (endValue - startValue) * easedProgress;
                    element.style[prop] = currentValue + (prop === 'opacity' ? '' : 'px');
                });
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
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
     * Responsive design helpers
     */
    isMobile() {
        return UI_UTILS_STATE.isMobile;
    }

    isTablet() {
        return UI_UTILS_STATE.isTablet;
    }

    isDesktop() {
        return UI_UTILS_STATE.isDesktop;
    }

    getScreenSize() {
        return UI_UTILS_STATE.screenSize;
    }

    /**
     * Utility functions
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * Emit UI event
     */
    emitUIEvent(type, data) {
        const event = new CustomEvent('uiEvent', {
            detail: {
                type: type,
                data: data,
                timestamp: Date.now()
            }
        });
        document.dispatchEvent(event);
        
        this.logger.debug('uiUtils', `UI event emitted: ${type}`, data);
    }

    /**
     * Get current state
     */
    getState() {
        return { ...UI_UTILS_STATE };
    }

    /**
     * Update settings
     */
    updateSettings(newSettings) {
        UI_UTILS_STATE.settings = { ...UI_UTILS_STATE.settings, ...newSettings };
        this.logger.debug('uiUtils', 'Settings updated:', UI_UTILS_STATE.settings);
    }

    /**
     * Cleanup
     */
    destroy() {
        this.logger.info('uiUtils', 'Destroying UI Utils');
        
        // Clear timeouts
        if (this.resizeTimeout) {
            clearTimeout(this.resizeTimeout);
        }
        
        // Remove all tooltips
        Object.values(UI_UTILS_STATE.components.tooltips).forEach(tooltip => {
            tooltip.element.remove();
        });
        
        // Close all modals
        this.closeAllModals();
        
        // Close all dropdowns
        this.closeAllDropdowns();
        
        this.initialized = false;
        UI_UTILS_STATE.initialized = false;
    }
}

// Create and export global instance
const uiUtils = new UIUtils();
window.uiUtils = uiUtils;
window.UI_UTILS_STATE = UI_UTILS_STATE;

// Log initialization
if (window.logger) {
    window.logger.info('uiUtils', 'UI Utils Module loaded');
} 