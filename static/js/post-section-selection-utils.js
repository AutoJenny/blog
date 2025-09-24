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
        sectionDiv.className = 'section-item mb-3 p-3 bg-dark border border-secondary rounded';
        
        // Create image thumbnail if available
        const imageThumbnail = section.image_filename ? 
            `<div class="col-md-3">
                <a href="/static/images/content/posts/${section.post_id || 'unknown'}/sections/${section.id}/optimized/${this.getProcessedImageFilename(section.image_filename, section.id)}" 
                   target="_blank" 
                   class="d-block text-decoration-none">
                    <img src="/static/images/content/posts/${section.post_id || 'unknown'}/sections/${section.id}/optimized/${this.getProcessedImageFilename(section.image_filename, section.id)}" 
                         class="img-thumbnail" 
                         style="width: 120px; height: 90px; object-fit: cover; cursor: pointer;"
                         alt="Section illustration"
                         onerror="this.style.display='none'"
                         title="Click to view full size">
                </a>
            </div>` : '';
        
        // Create full content display (not truncated)
        const contentDisplay = section.polished ? 
            section.polished : 
            'No polished content available';
        
        sectionDiv.innerHTML = `
            <div class="row">
                ${imageThumbnail}
                <div class="${section.image_filename ? 'col-md-9' : 'col-12'}">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <strong class="text-white">${section.section_heading || 'Untitled Section'}</strong>
                            <small class="text-muted d-block">Order: ${section.section_order || 'N/A'}</small>
                        </div>
                        <div>
                            <span class="badge bg-info">${section.id}</span>
                        </div>
                    </div>
                    <div class="text-light small">
                        <strong>Content:</strong><br>
                        <div class="text-muted" style="max-height: 200px; overflow-y: auto; white-space: pre-wrap;">${contentDisplay}</div>
                    </div>
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

    static getProcessedImageFilename(originalFilename, sectionId) {
        if (!originalFilename || !sectionId) return '';
        
        // Try different naming patterns based on the original filename and section ID
        if (originalFilename.includes('d59ac061-0b2a-4a06-a3a6-c15d13dc35e2')) {
            // Section 710 uses the complex filename from database
            return originalFilename.endsWith('_processed.png') ? 
                originalFilename : 
                originalFilename.replace('.png', '_processed.png');
        } else if (sectionId === 711 && (originalFilename.includes('live_preview_content') || originalFilename.includes('generated_image'))) {
            // Section 711 specifically uses generated_image pattern
            return 'generated_image_20250727_145859_processed.png';
        } else {
            // Default pattern: section ID + _processed.png (for sections 712-716)
            return `${sectionId}_processed.png`;
        }
    }
}
