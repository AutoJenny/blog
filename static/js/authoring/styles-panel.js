/**
 * Styles Panel - Self-contained module for managing post-wide image styles
 * Handles style loading, creation, activation, and JSON editing
 */

class StylesPanel {
    constructor() {
        this.postId = window.postId;
        this.init();
    }

    init() {
        console.log('[Styles Panel] Initializing...');
        this.setupEventListeners();
        this.setupButtonHandlers();
    }

    setupEventListeners() {
        // Listen for styles loaded event
        document.addEventListener('authoring:styles:loaded', (e) => {
            this.onStylesLoaded(e.detail);
        });
    }

    setupButtonHandlers() {
        document.addEventListener('DOMContentLoaded', () => {
            const createBtn = document.getElementById('create-style-btn');
            const activateBtn = document.getElementById('activate-style-btn');
            
            if (createBtn) {
                createBtn.addEventListener('click', () => this.createStyle());
            }
            
            if (activateBtn) {
                activateBtn.addEventListener('click', () => this.activateStyle());
            }
        });
    }

    onStylesLoaded(data) {
        console.log('[Styles Panel] Event received:', data);
        const activeIndex = data.activeIndex || 0;
        const styles = (data.styles || []).map((s, idx) => ({ 
            name: s.name, 
            style_json: s.style_json, 
            is_active: idx === activeIndex 
        }));
        
        this.renderStyles(styles);
        this.autoPopulateFirstStyle(styles);
        this.updateTitle(styles);
    }

    renderStyles(styles) {
        const list = document.getElementById('styles-list');
        if (!list) {
            console.error('[Styles Panel] styles-list element not found');
            return;
        }
        
        console.log('[Styles Panel] Rendering', styles.length, 'styles');
        list.innerHTML = '';
        
        styles.forEach((s, idx) => {
            const row = this.createStyleRow(s, idx);
            list.appendChild(row);
        });
    }

    createStyleRow(style, idx) {
        const row = document.createElement('div');
        row.className = 'style-row';
        row.style = 'display:flex; align-items:center; gap:0.5rem; padding:0.25rem 0;';
        
        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = 'style-select';
        radio.value = String(idx);
        if (style.is_active) radio.checked = true;
        
        const label = document.createElement('span');
        label.textContent = style.name || 'Unnamed Style';
        
        if (style.is_active) {
            const badge = document.createElement('span');
            badge.textContent = 'Active';
            badge.style = 'margin-left:0.5rem; color:#7bf; font-size:0.85rem;';
            label.appendChild(badge);
        }
        
        row.appendChild(radio);
        row.appendChild(label);
        
        row.addEventListener('click', async () => {
            console.log('[Styles Panel] Style clicked:', style.name);
            radio.checked = true;
            this.updateUIForSelectedStyle(style);
            
            // Auto-activate the selected style
            try {
                await window.AuthoringStyles.activateStyle(idx);
                console.log('[Styles Panel] Style activated:', style.name);
            } catch (e) {
                console.error('[Styles Panel] Error auto-activating style:', e);
            }
        });
        
        return row;
    }

    updateUIForSelectedStyle(style) {
        const activateBtn = document.getElementById('activate-style-btn');
        if (activateBtn) activateBtn.disabled = false;
        
        const editor = document.getElementById('style-json-editor');
        if (editor) {
            try {
                editor.value = JSON.stringify(style.style_json || {}, null, 2);
                console.log('[Styles Panel] JSON populated:', style.style_json);
            } catch (e) {
                console.error('[Styles Panel] JSON error:', e);
                editor.value = '{}';
            }
        }
        
        // Update the title with the selected style name
        this.updateTitleWithStyle(style.name);
    }

    autoPopulateFirstStyle(styles) {
        if (styles.length > 0) {
            const firstStyle = styles[0];
            const editor = document.getElementById('style-json-editor');
            if (editor && firstStyle.style_json) {
                try {
                    editor.value = JSON.stringify(firstStyle.style_json, null, 2);
                    console.log('[Styles Panel] Auto-populated first style JSON');
                } catch (e) {
                    console.error('[Styles Panel] Auto-populate error:', e);
                }
            }
        }
    }

    async createStyle() {
        const editor = document.getElementById('style-json-editor');
        if (!editor) return;
        
        let name = prompt('Name this style variant:', 'Default');
        if (name === null) return;
        
        let payload = {};
        try {
            payload = JSON.parse(editor.value || '{}');
        } catch (e) {
            alert('Invalid JSON');
            return;
        }
        
        try {
            await window.AuthoringStyles.createStyle(name, payload, true);
        } catch (e) {
            console.error('[Styles Panel] Error creating style:', e);
            alert('Failed to create style');
        }
    }

    async activateStyle() {
        const selected = document.querySelector('input[name="style-select"]:checked');
        if (!selected) return;
        
        try {
            await window.AuthoringStyles.activateStyle(Number(selected.value));
        } catch (e) {
            console.error('[Styles Panel] Error activating style:', e);
            alert('Failed to activate style');
        }
    }

    updateTitle(styles) {
        const activeStyle = styles.find(s => s.is_active);
        if (activeStyle) {
            this.updateTitleWithStyle(activeStyle.name);
        } else {
            this.updateTitleWithStyle('None');
        }
    }

    updateTitleWithStyle(styleName) {
        const titleElement = document.getElementById('styles-title');
        if (titleElement) {
            titleElement.textContent = styleName;
        }
    }
}

// Accordion function for styles panel
function toggleStylesAccordion() {
    const content = document.getElementById('styles-accordion-content');
    const icon = document.getElementById('styles-accordion-icon');
    
    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
    } else {
        content.style.display = 'none';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new StylesPanel();
});
