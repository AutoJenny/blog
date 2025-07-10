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
        this.refreshContext();
        this.updatePreview();
        this.updateSummary();
    }

    closeModal() {
        this.modal.classList.add('hidden');
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

    refreshContext() {
        // This would populate fields from the actual panels
        // For now, we'll just update the preview
        this.updatePreview();
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