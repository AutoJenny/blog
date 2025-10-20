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
        const styles = (data.styles || []).map(s => ({ 
            name: s.name, 
            style_json: s.style_json, 
            is_active: s.is_active 
        }));
        
        this.renderStyles(styles);
        this.autoPopulateFirstStyle(styles);
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
        
        row.addEventListener('click', () => {
            console.log('[Styles Panel] Style clicked:', style.name);
            radio.checked = true;
            this.updateUIForSelectedStyle(style);
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
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new StylesPanel();
});
