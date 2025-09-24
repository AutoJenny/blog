/**
 * Post Section Selection Utilities
 * Helper functions for post and section management
 */

class PostSectionUtils {
    static formatDate(dateString) {
        return new Date(dateString).toLocaleDateString();
    }

    static formatDateTime(dateString) {
        return new Date(dateString).toLocaleString();
    }

    static createOption(value, text) {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = text;
        return option;
    }

    static createSectionElement(section) {
        const sectionDiv = document.createElement('div');
        sectionDiv.className = 'section-item mb-2 p-3 bg-dark border border-secondary rounded';
        sectionDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <strong class="text-white">${section.section_heading || 'Untitled Section'}</strong>
                    <small class="text-muted d-block">Order: ${section.section_order || 'N/A'}</small>
                </div>
                <div>
                    <span class="badge bg-info">${section.id}</span>
                </div>
            </div>
        `;
        return sectionDiv;
    }

    static showElement(elementId, show = true) {
        const element = document.getElementById(elementId);
        if (element) {
            if (show) {
                element.classList.remove('d-none');
            } else {
                element.classList.add('d-none');
            }
        }
    }

    static updateElementText(elementId, text) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text;
        }
    }

    static updateElementHTML(elementId, html) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = html;
        }
    }

    static setButtonState(buttonId, disabled, text = null) {
        const button = document.getElementById(buttonId);
        if (button) {
            button.disabled = disabled;
            if (text !== null) {
                button.innerHTML = text;
            }
        }
    }

    static showProgress(show = true) {
        const progressDiv = document.getElementById('generationProgress');
        if (progressDiv) {
            if (show) {
                progressDiv.classList.remove('d-none');
            } else {
                progressDiv.classList.add('d-none');
            }
        }
    }

    static updateProgress(percentage, text) {
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
        }
        
        if (progressText) {
            progressText.textContent = text;
        }
    }

    static dispatchEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, { detail });
        document.dispatchEvent(event);
    }

    static saveToLocalStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Error saving to localStorage:', error);
        }
    }

    static loadFromLocalStorage(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Error loading from localStorage:', error);
            return defaultValue;
        }
    }
}
