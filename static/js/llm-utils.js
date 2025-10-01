/**
 * LLM Module Utilities
 * Common utility functions used across LLM modules
 */

/**
 * Escape HTML to prevent XSS attacks
 * @param {string} text - Text to escape
 * @returns {string} Escaped HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Global accordion toggle function
 * Toggles the LLM accordion open/closed state
 */
function toggleLLMAccordion() {
    const accordionContent = document.getElementById('llm-accordion-content');
    const accordionIcon = document.getElementById('accordion-icon');
    
    if (!accordionContent || !accordionIcon) return;
    
    const isOpen = accordionContent.style.display !== 'none';
    
    if (isOpen) {
        // Close accordion
        accordionContent.style.display = 'none';
        accordionIcon.style.transform = 'rotate(0deg)';
        accordionContent.classList.remove('open');
        accordionContent.classList.add('closed');
    } else {
        // Open accordion
        accordionContent.style.display = 'block';
        accordionIcon.style.transform = 'rotate(180deg)';
        accordionContent.classList.remove('closed');
        accordionContent.classList.add('open');
    }
}

/**
 * Global debug accordion toggle function
 * Toggles the LLM message debug accordion open/closed state
 */
function toggleDebugAccordion() {
    const debugContent = document.getElementById('debug-accordion-content');
    const debugIcon = document.getElementById('debug-accordion-icon');
    
    if (!debugContent || !debugIcon) return;
    
    const isOpen = debugContent.style.display !== 'none';
    
    if (isOpen) {
        // Close accordion
        debugContent.style.display = 'none';
        debugIcon.style.transform = 'rotate(0deg)';
        debugContent.classList.remove('open');
        debugContent.classList.add('closed');
    } else {
        // Open accordion
        debugContent.style.display = 'block';
        debugIcon.style.transform = 'rotate(180deg)';
        debugContent.classList.remove('closed');
        debugContent.classList.add('open');
    }
}

/**
 * Format word count for display
 * @param {string} text - Text to count words in
 * @returns {number} Word count
 */
function getWordCount(text) {
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
}

/**
 * Update word count display
 * @param {string} text - Text to count
 * @param {string} elementId - ID of element to update
 */
function updateWordCount(text, elementId = 'word-count') {
    const wordCountElement = document.getElementById(elementId);
    if (wordCountElement) {
        const count = getWordCount(text);
        wordCountElement.textContent = `${count} words`;
    }
}

/**
 * Enable/disable button
 * @param {string} buttonId - ID of button to toggle
 * @param {boolean} enabled - Whether button should be enabled
 */
function toggleButton(buttonId, enabled) {
    const button = document.getElementById(buttonId);
    if (button) {
        button.disabled = !enabled;
    }
}

/**
 * Show/hide element
 * @param {string} elementId - ID of element to toggle
 * @param {boolean} visible - Whether element should be visible
 */
function toggleElement(elementId, visible) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = visible ? 'block' : 'none';
    }
}

/**
 * Get element by ID safely
 * @param {string} id - Element ID
 * @returns {HTMLElement|null} Element or null if not found
 */
function getElement(id) {
    return document.getElementById(id);
}

/**
 * Create HTML element with attributes
 * @param {string} tag - HTML tag name
 * @param {Object} attributes - Element attributes
 * @param {string} content - Element content
 * @returns {string} HTML string
 */
function createElement(tag, attributes = {}, content = '') {
    const attrs = Object.entries(attributes)
        .map(([key, value]) => `${key}="${escapeHtml(value)}"`)
        .join(' ');
    
    return `<${tag}${attrs ? ' ' + attrs : ''}>${content}</${tag}>`;
}
