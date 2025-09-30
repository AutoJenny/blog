/**
 * LLM UI Manager
 * Handles all DOM manipulation and display logic for LLM module
 */

class LLMUIManager {
    constructor() {
        // No initialization needed - all methods are stateless
    }

    /**
     * Display prompt information in the UI
     * @param {Object} prompt - Prompt object with name, system_prompt, prompt_text
     */
    displayPrompt(prompt) {
        const promptDisplay = document.getElementById('llm-prompt-display');
        if (!promptDisplay) return;

        let promptHTML = '';

        // Display prompt title
        const promptTitle = document.getElementById('prompt-title');
        if (promptTitle && prompt.name) {
            promptTitle.textContent = `Prompt: ${prompt.name}`;
        }

        // Display system prompt
        if (prompt.system_prompt) {
            promptHTML += `<div class="system-prompt">${this.escapeHtml(prompt.system_prompt)}</div>`;
        }

        // Display user prompt with placeholder highlighting
        if (prompt.prompt_text) {
            // Highlight placeholders like [EXPANDED_IDEA]
            let highlightedText = prompt.prompt_text.replace(/\[([^\]]+)\]/g, '<span class="placeholder">[$1]</span>');
            promptHTML += `<div class="prompt-text">${this.escapeHtml(highlightedText)}</div>`;
        }

        promptDisplay.innerHTML = promptHTML;
    }

    /**
     * Display LLM configuration information
     * @param {Object} config - Configuration object
     */
    displayConfig(config) {
        const providerInfo = document.getElementById('llm-provider-info');
        if (!providerInfo) return;

        let configHTML = '';

        if (config.provider) {
            configHTML += `<div class="provider-info">
                <strong>Provider:</strong> ${this.escapeHtml(config.provider)}
            </div>`;
        }

        if (config.model) {
            configHTML += `<div class="model-info">
                <strong>Model:</strong> ${this.escapeHtml(config.model)}
            </div>`;
        }

        if (config.temperature !== undefined) {
            configHTML += `<div class="temperature-info">
                <strong>Temperature:</strong> ${config.temperature}
            </div>`;
        }

        if (config.max_tokens) {
            configHTML += `<div class="tokens-info">
                <strong>Max Tokens:</strong> ${config.max_tokens}
            </div>`;
        }

        providerInfo.innerHTML = configHTML;
    }

    /**
     * Display error message in the UI
     * @param {string} message - Error message to display
     */
    displayError(message) {
        const promptDisplay = document.getElementById('llm-prompt-display');
        if (promptDisplay) {
            promptDisplay.innerHTML = `<div class="error-message">${this.escapeHtml(message)}</div>`;
        }

        const resultsDisplay = document.getElementById('llm-results-display');
        if (resultsDisplay) {
            resultsDisplay.innerHTML = `<div class="error-message">${this.escapeHtml(message)}</div>`;
        }
    }

    /**
     * Display results data in the UI
     * @param {*} data - Results data to display
     */
    displayResults(data) {
        const resultsDisplay = document.getElementById('llm-results-display');
        if (!resultsDisplay) return;
        
        // Handle different types of results based on the data structure
        if (Array.isArray(data)) {
            // Handle array results (topics, sections, etc.)
            this.displayArrayResults(data, resultsDisplay);
        } else if (typeof data === 'object' && data !== null) {
            // Handle object results
            this.displayObjectResults(data, resultsDisplay);
        } else if (typeof data === 'string') {
            // Handle string results
            resultsDisplay.innerHTML = `<div class="generated-content">${this.escapeHtml(data)}</div>`;
        } else {
            this.displayError('No valid results to display');
        }
    }

    /**
     * Display array results
     * @param {Array} data - Array data to display
     * @param {HTMLElement} resultsDisplay - DOM element to display in
     */
    displayArrayResults(data, resultsDisplay) {
        if (data.length === 0) {
            resultsDisplay.innerHTML = '<div class="no-results">No results generated. Try again with different settings.</div>';
            return;
        }
        
        // Check if it's topics (has title property)
        if (data[0] && data[0].title) {
            this.displayTopics(data, resultsDisplay);
        } else if (data[0] && data[0].theme) {
            // Check if it's groups (has theme property)
            this.displayGroups(data, resultsDisplay);
        } else if (data[0] && data[0].section_title) {
            // Check if it's sections (has section_title property)
            this.displaySections(data, resultsDisplay);
        } else {
            // Generic array display
            let html = '<div class="results-list">';
            data.forEach((item, index) => {
                html += `<div class="result-item" data-index="${index}">${this.escapeHtml(item)}</div>`;
            });
            html += '</div>';
            resultsDisplay.innerHTML = html;
        }
    }

    /**
     * Display object results
     * @param {Object} data - Object data to display
     * @param {HTMLElement} resultsDisplay - DOM element to display in
     */
    displayObjectResults(data, resultsDisplay) {
        // Handle nested results structure
        if (data.sections) {
            this.displaySections(data.sections, resultsDisplay);
        } else if (data.groups) {
            this.displayGroups(data.groups, resultsDisplay);
        } else if (data.topics) {
            this.displayTopics(data.topics, resultsDisplay);
        } else {
            // Generic object display
            resultsDisplay.innerHTML = `<div class="generated-content">${this.escapeHtml(JSON.stringify(data, null, 2))}</div>`;
        }
    }

    /**
     * Display topics
     * @param {Array} topics - Topics array to display
     * @param {HTMLElement} resultsDisplay - DOM element to display in
     */
    displayTopics(topics, resultsDisplay) {
        let topicsHTML = '<div class="topics-list">';
        
        topics.forEach((topic, index) => {
            const topicText = typeof topic === 'string' ? topic : (topic.title || topic);
            const category = topic.category || 'general';
            
            topicsHTML += `
                <div class="topic-item" data-topic-id="${index}" data-category="${category}">
                    <div class="topic-content">${this.escapeHtml(topicText)}</div>
                </div>
            `;
        });
        
        topicsHTML += '</div>';
        resultsDisplay.innerHTML = topicsHTML;
    }

    /**
     * Display groups
     * @param {Array} groups - Groups array to display
     * @param {HTMLElement} resultsDisplay - DOM element to display in
     */
    displayGroups(groups, resultsDisplay) {
        let groupsHTML = '<div class="groups-list">';
        
        groups.forEach((group, index) => {
            groupsHTML += `
                <div class="group-item" data-group-id="${group.id || group.order || index}">
                    <h5 class="group-theme">${this.escapeHtml(group.theme || `Group ${index + 1}`)}</h5>
                    <p class="group-explanation">${this.escapeHtml(group.explanation || 'No explanation provided.')}</p>
                    <div class="group-topics">
                        ${(group.topics || []).map(topic => 
                            `<div class="group-topic-item">${this.escapeHtml(topic)}</div>`
                        ).join('')}
                    </div>
                </div>
            `;
        });
        
        groupsHTML += '</div>';
        resultsDisplay.innerHTML = groupsHTML;
    }

    /**
     * Display sections
     * @param {Array} sections - Sections array to display
     * @param {HTMLElement} resultsDisplay - DOM element to display in
     */
    displaySections(sections, resultsDisplay) {
        let sectionsHTML = '<div class="sections-list">';
        
        sections.forEach((section, index) => {
            const topicCount = section.topics ? section.topics.length : 0;
            
            sectionsHTML += `
                <div class="section-item" data-section-id="${section.id || index}">
                    <div class="section-header">
                        <h4 class="section-title">${this.escapeHtml(section.title || section.section_title || `Section ${index + 1}`)}</h4>
                        <div class="section-meta">
                            <span class="topic-count">${topicCount} topics</span>
                            <span class="section-order">${section.order || index + 1}</span>
                        </div>
                    </div>
                    ${section.subtitle ? `<div class="section-subtitle">${this.escapeHtml(section.subtitle)}</div>` : ''}
                    ${section.description ? `<div class="section-description">${this.escapeHtml(section.description)}</div>` : ''}
                    <div class="section-topics">
                        ${(section.topics || []).map(topic => 
                            `<div class="section-topic-item" data-topic="${this.escapeHtml(topic)}">
                                <span class="topic-text">${this.escapeHtml(topic)}</span>
                            </div>`
                        ).join('')}
                    </div>
                </div>
            `;
        });
        
        sectionsHTML += '</div>';
        resultsDisplay.innerHTML = sectionsHTML;
    }

    /**
     * Display authoring results (specialized for authoring workflow)
     * @param {Object} data - Authoring data with draft_content
     * @param {Object} module - Reference to the LLM module
     */
    displayAuthoringResults(data, module) {
        const resultsDisplay = document.getElementById('llm-results-display');
        const contentEditor = document.getElementById('content-editor');
        
        if (data.draft_content) {
            // Display in results area
            if (resultsDisplay) {
                resultsDisplay.innerHTML = `<div class="generated-content">${data.draft_content}</div>`;
            }
            
            // Only update content editor if this is the currently selected section
            if (contentEditor && this.isCurrentSection(module)) {
                contentEditor.value = data.draft_content;
                contentEditor.disabled = false;
                
                // Update word count
                const wordCount = data.draft_content.trim().split(/\s+/).filter(word => word.length > 0).length;
                const wordCountElement = document.getElementById('word-count');
                if (wordCountElement) {
                    wordCountElement.textContent = `${wordCount} words`;
                }
                
                // Enable save button
                const saveBtn = document.getElementById('save-btn');
                if (saveBtn) {
                    saveBtn.disabled = false;
                }
                
                // Auto-save the generated content
                this.autoSaveContent(data.draft_content, module);
            }
        } else {
            this.displayError('No content generated');
        }
    }

    /**
     * Check if this is the currently selected section (for authoring)
     * @param {Object} module - Reference to the LLM module
     * @returns {boolean} True if current section
     */
    isCurrentSection(module) {
        if (!module) return true; // Fallback if no module reference
        
        const currentSectionId = window.currentSelectedSectionId;
        if (!currentSectionId) return false;
        
        // Extract section ID from the generate endpoint
        const endpointMatch = module.config.generateEndpoint.match(/\/sections\/(\d+)\/generate/);
        if (!endpointMatch) return false;
        
        const moduleSectionId = parseInt(endpointMatch[1]);
        return moduleSectionId === currentSectionId;
    }

    /**
     * Auto-save content (for authoring)
     * @param {string} content - Content to save
     * @param {Object} module - Reference to the LLM module
     */
    async autoSaveContent(content, module) {
        if (!module) {
            console.log('Auto-save not available - no module reference');
            return;
        }
        
        const currentSectionId = window.currentSelectedSectionId;
        if (!currentSectionId) return;
        
        const result = await module.apiClient.autoSaveContent(content, module.postId, currentSectionId);
        
        if (result.success) {
            // Update last saved indicator
            const lastSavedElement = document.getElementById('last-saved');
            if (lastSavedElement) {
                lastSavedElement.textContent = 'Auto-saved just now';
            }
            
            // Update section status in UI
            const sectionItem = document.querySelector(`[data-section-id="${currentSectionId}"]`);
            if (sectionItem) {
                sectionItem.setAttribute('data-status', 'complete');
                const statusElement = sectionItem.querySelector('.section-status');
                if (statusElement) {
                    statusElement.textContent = 'Complete';
                    statusElement.className = 'section-status complete';
                }
            }
            
            console.log('Content auto-saved successfully');
        } else {
            console.error('Auto-save failed:', result.error);
        }
    }

    /**
     * Escape HTML to prevent XSS attacks
     * @param {string} text - Text to escape
     * @returns {string} Escaped HTML
     */
    escapeHtml(text) {
        return window.escapeHtml ? window.escapeHtml(text) : escapeHtml(text);
    }
}
