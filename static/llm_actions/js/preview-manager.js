/**
 * Preview Manager Module
 *
 * Responsibilities:
 * - Handle preview functionality for content
 * - Manage preview iframes and modes
 * - Coordinate with other modules for preview data
 * - Provide preview API for other modules
 *
 * Dependencies: logger.js, element-ordering.js
 * Dependents: ui-utils.js
 *
 * @version 1.0
 */

// Preview state
const PREVIEW_STATE = {
    // Preview modes
    currentMode: 'none', // 'none', 'live', 'static', 'fullscreen'
    availableModes: ['live', 'static', 'fullscreen'],
    
    // Preview containers
    previewContainers: {},
    
    // Preview data
    previewData: {},
    lastUpdate: null,
    
    // Iframe management
    iframes: {},
    iframeSettings: {
        width: '100%',
        height: '600px',
        border: '1px solid #ddd',
        borderRadius: '5px'
    },
    
    // Settings
    settings: {
        autoRefresh: true,
        refreshInterval: 5000,
        enableFullscreen: true,
        enableLivePreview: true,
        enableStaticPreview: true,
        maxPreviewSize: 10000 // characters
    },
    
    // UI state
    initialized: false,
    isFullscreen: false
};

/**
 * Preview Manager class
 */
class PreviewManager {
    constructor() {
        this.logger = window.logger;
        this.context = null;
        this.initialized = false;
        this.refreshInterval = null;
        this.fullscreenElement = null;
    }

    /**
     * Initialize the preview manager
     */
    async initialize(context) {
        this.logger.trace('previewManager', 'initialize', 'enter');
        this.context = context;
        
        try {
            // Initialize preview containers
            await this.initializePreviewContainers();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Create preview controls
            this.createPreviewControls();
            
            // Start auto-refresh if enabled
            if (PREVIEW_STATE.settings.autoRefresh) {
                this.startAutoRefresh();
            }
            
            this.initialized = true;
            PREVIEW_STATE.initialized = true;
            
            this.logger.info('previewManager', 'Preview manager initialized');
            
        } catch (error) {
            this.logger.error('previewManager', 'Failed to initialize preview manager:', error);
            throw error;
        }
        
        this.logger.trace('previewManager', 'initialize', 'exit');
    }

    /**
     * Initialize preview containers
     */
    async initializePreviewContainers() {
        this.logger.trace('previewManager', 'initializePreviewContainers', 'enter');
        
        // Find all preview containers
        const containers = document.querySelectorAll('.preview-container, [data-preview]');
        this.logger.debug('previewManager', `Found ${containers.length} preview containers`);
        
        for (const container of containers) {
            await this.initializeSingleContainer(container);
        }
        
        this.logger.trace('previewManager', 'initializePreviewContainers', 'exit');
    }

    /**
     * Initialize a single preview container
     */
    async initializeSingleContainer(container) {
        const containerId = container.id || container.getAttribute('data-preview');
        const previewType = container.getAttribute('data-preview-type') || 'content';
        
        this.logger.debug('previewManager', `Initializing preview container: ${containerId} (type: ${previewType})`);
        
        // Store container reference
        PREVIEW_STATE.previewContainers[containerId] = {
            element: container,
            type: previewType,
            currentMode: 'none',
            iframe: null,
            lastContent: null
        };
        
        // Add preview controls to container
        this.addPreviewControls(container, containerId, previewType);
        
        // Initialize preview area
        this.initializePreviewArea(container, containerId);
    }

    /**
     * Add preview controls to container
     */
    addPreviewControls(container, containerId, previewType) {
        // Create preview controls
        const controls = document.createElement('div');
        controls.className = 'preview-controls';
        controls.setAttribute('data-container-id', containerId);
        
        controls.innerHTML = `
            <div class="btn-group" role="group">
                <button class="btn btn-sm btn-outline-primary preview-live" title="Live Preview">
                    <i class="fas fa-eye"></i> Live
                </button>
                <button class="btn btn-sm btn-outline-secondary preview-static" title="Static Preview">
                    <i class="fas fa-file-alt"></i> Static
                </button>
                <button class="btn btn-sm btn-outline-info preview-fullscreen" title="Fullscreen Preview">
                    <i class="fas fa-expand"></i> Fullscreen
                </button>
            </div>
            <div class="preview-status">
                <span class="status-indicator"></span>
                <span class="status-text">Ready</span>
            </div>
        `;
        
        // Insert controls before container
        container.parentNode.insertBefore(controls, container);
        
        // Set up event listeners
        this.setupPreviewControlListeners(controls, containerId);
    }

    /**
     * Initialize preview area
     */
    initializePreviewArea(container, containerId) {
        // Create preview area
        const previewArea = document.createElement('div');
        previewArea.className = 'preview-area';
        previewArea.setAttribute('data-container-id', containerId);
        
        // Add placeholder content
        previewArea.innerHTML = `
            <div class="preview-placeholder">
                <i class="fas fa-eye-slash"></i>
                <p>No preview available</p>
                <p class="text-muted">Select a preview mode to view content</p>
            </div>
        `;
        
        container.appendChild(previewArea);
    }

    /**
     * Set up preview control listeners
     */
    setupPreviewControlListeners(controls, containerId) {
        // Live preview
        controls.querySelector('.preview-live').addEventListener('click', () => {
            this.setPreviewMode(containerId, 'live');
        });
        
        // Static preview
        controls.querySelector('.preview-static').addEventListener('click', () => {
            this.setPreviewMode(containerId, 'static');
        });
        
        // Fullscreen preview
        controls.querySelector('.preview-fullscreen').addEventListener('click', () => {
            this.setPreviewMode(containerId, 'fullscreen');
        });
    }

    /**
     * Set preview mode
     */
    setPreviewMode(containerId, mode) {
        this.logger.debug('previewManager', `Setting preview mode: ${mode} for container ${containerId}`);
        
        const container = PREVIEW_STATE.previewContainers[containerId];
        if (!container) return;
        
        // Update current mode
        container.currentMode = mode;
        PREVIEW_STATE.currentMode = mode;
        
        // Update UI
        this.updatePreviewModeUI(containerId, mode);
        
        // Handle mode-specific actions
        switch (mode) {
            case 'live':
                this.enableLivePreview(containerId);
                break;
            case 'static':
                this.enableStaticPreview(containerId);
                break;
            case 'fullscreen':
                this.enableFullscreenPreview(containerId);
                break;
            case 'none':
                this.disablePreview(containerId);
                break;
        }
        
        // Emit mode change event
        this.emitPreviewEvent('modeChange', { containerId, mode });
    }

    /**
     * Update preview mode UI
     */
    updatePreviewModeUI(containerId, mode) {
        const container = PREVIEW_STATE.previewContainers[containerId];
        if (!container) return;
        
        // Find controls
        const controls = document.querySelector(`.preview-controls[data-container-id="${containerId}"]`);
        if (!controls) return;
        
        // Remove active class from all buttons
        controls.querySelectorAll('button').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Add active class to current mode button
        const activeButton = controls.querySelector(`.preview-${mode}`);
        if (activeButton) {
            activeButton.classList.add('active');
        }
        
        // Update status
        const statusText = controls.querySelector('.status-text');
        if (statusText) {
            statusText.textContent = `${mode.charAt(0).toUpperCase() + mode.slice(1)} Preview`;
        }
    }

    /**
     * Enable live preview
     */
    enableLivePreview(containerId) {
        this.logger.debug('previewManager', `Enabling live preview for container ${containerId}`);
        
        const container = PREVIEW_STATE.previewContainers[containerId];
        if (!container) return;
        
        // Create iframe for live preview
        const iframe = this.createPreviewIframe(containerId, 'live');
        container.iframe = iframe;
        
        // Update preview area
        const previewArea = container.element.querySelector('.preview-area');
        if (previewArea) {
            previewArea.innerHTML = '';
            previewArea.appendChild(iframe);
        }
        
        // Load initial content
        this.loadPreviewContent(containerId);
        
        // Start live updates
        this.startLiveUpdates(containerId);
    }

    /**
     * Enable static preview
     */
    enableStaticPreview(containerId) {
        this.logger.debug('previewManager', `Enabling static preview for container ${containerId}`);
        
        const container = PREVIEW_STATE.previewContainers[containerId];
        if (!container) return;
        
        // Create iframe for static preview
        const iframe = this.createPreviewIframe(containerId, 'static');
        container.iframe = iframe;
        
        // Update preview area
        const previewArea = container.element.querySelector('.preview-area');
        if (previewArea) {
            previewArea.innerHTML = '';
            previewArea.appendChild(iframe);
        }
        
        // Load static content
        this.loadPreviewContent(containerId);
    }

    /**
     * Enable fullscreen preview
     */
    enableFullscreenPreview(containerId) {
        this.logger.debug('previewManager', `Enabling fullscreen preview for container ${containerId}`);
        
        const container = PREVIEW_STATE.previewContainers[containerId];
        if (!container) return;
        
        // Create fullscreen overlay
        const overlay = this.createFullscreenOverlay(containerId);
        document.body.appendChild(overlay);
        
        // Store reference
        PREVIEW_STATE.fullscreenElement = overlay;
        PREVIEW_STATE.isFullscreen = true;
        
        // Load content into fullscreen
        this.loadPreviewContent(containerId, true);
        
        // Add escape key listener
        this.addFullscreenEscapeListener();
    }

    /**
     * Disable preview
     */
    disablePreview(containerId) {
        this.logger.debug('previewManager', `Disabling preview for container ${containerId}`);
        
        const container = PREVIEW_STATE.previewContainers[containerId];
        if (!container) return;
        
        // Remove iframe
        if (container.iframe) {
            container.iframe.remove();
            container.iframe = null;
        }
        
        // Reset preview area
        const previewArea = container.element.querySelector('.preview-area');
        if (previewArea) {
            previewArea.innerHTML = `
                <div class="preview-placeholder">
                    <i class="fas fa-eye-slash"></i>
                    <p>No preview available</p>
                    <p class="text-muted">Select a preview mode to view content</p>
                </div>
            `;
        }
        
        // Stop live updates
        this.stopLiveUpdates(containerId);
    }

    /**
     * Create preview iframe
     */
    createPreviewIframe(containerId, mode) {
        const iframe = document.createElement('iframe');
        iframe.className = `preview-iframe preview-${mode}`;
        iframe.setAttribute('data-container-id', containerId);
        iframe.setAttribute('data-mode', mode);
        
        // Apply iframe settings
        Object.assign(iframe.style, PREVIEW_STATE.iframeSettings);
        
        // Add loading indicator
        iframe.addEventListener('load', () => {
            this.onIframeLoad(containerId, mode);
        });
        
        iframe.addEventListener('error', () => {
            this.onIframeError(containerId, mode);
        });
        
        return iframe;
    }

    /**
     * Create fullscreen overlay
     */
    createFullscreenOverlay(containerId) {
        const overlay = document.createElement('div');
        overlay.className = 'preview-fullscreen-overlay';
        overlay.setAttribute('data-container-id', containerId);
        
        overlay.innerHTML = `
            <div class="fullscreen-header">
                <h3>Fullscreen Preview</h3>
                <button class="btn btn-sm btn-outline-secondary close-fullscreen">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="fullscreen-content">
                <iframe class="preview-iframe preview-fullscreen" data-container-id="${containerId}" data-mode="fullscreen"></iframe>
            </div>
        `;
        
        // Set up close button
        overlay.querySelector('.close-fullscreen').addEventListener('click', () => {
            this.closeFullscreen();
        });
        
        return overlay;
    }

    /**
     * Load preview content
     */
    async loadPreviewContent(containerId, isFullscreen = false) {
        this.logger.debug('previewManager', `Loading preview content for container ${containerId}`);
        
        const container = PREVIEW_STATE.previewContainers[containerId];
        if (!container) return;
        
        try {
            // Get content from other modules
            const content = await this.getPreviewContent(containerId);
            
            if (!content) {
                this.showPreviewError(containerId, 'No content available for preview');
                return;
            }
            
            // Update preview data
            PREVIEW_STATE.previewData[containerId] = content;
            PREVIEW_STATE.lastUpdate = Date.now();
            
            // Determine target iframe
            let targetIframe;
            if (isFullscreen && PREVIEW_STATE.fullscreenElement) {
                targetIframe = PREVIEW_STATE.fullscreenElement.querySelector('.preview-iframe');
            } else {
                targetIframe = container.iframe;
            }
            
            if (!targetIframe) {
                this.logger.warn('previewManager', 'No target iframe found for preview');
                return;
            }
            
            // Load content into iframe
            this.loadContentIntoIframe(targetIframe, content, container.type);
            
            // Update status
            this.updatePreviewStatus(containerId, 'success', 'Preview loaded successfully');
            
        } catch (error) {
            this.logger.error('previewManager', 'Failed to load preview content:', error);
            this.showPreviewError(containerId, 'Failed to load preview content');
        }
    }

    /**
     * Get preview content from other modules
     */
    async getPreviewContent(containerId) {
        // Emit event to get content from other modules
        const event = new CustomEvent('getPreviewContent', {
            detail: { containerId }
        });
        document.dispatchEvent(event);
        
        // Wait for response (simplified - in real implementation, you'd use a promise-based approach)
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // For now, return mock content based on container type
        const container = PREVIEW_STATE.previewContainers[containerId];
        if (!container) return null;
        
        switch (container.type) {
            case 'content':
                return this.getContentPreview();
            case 'sections':
                return this.getSectionsPreview();
            case 'output':
                return this.getOutputPreview();
            default:
                return this.getDefaultPreview();
        }
    }

    /**
     * Get content preview
     */
    getContentPreview() {
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Content Preview</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .content { max-width: 800px; margin: 0 auto; }
                </style>
            </head>
            <body>
                <div class="content">
                    <h1>Content Preview</h1>
                    <p>This is a preview of the current content.</p>
                    <p>Content will be loaded from the LLM processing results.</p>
                </div>
            </body>
            </html>
        `;
    }

    /**
     * Get sections preview
     */
    getSectionsPreview() {
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Sections Preview</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .section { margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                    .section-title { font-weight: bold; margin-bottom: 10px; }
                </style>
            </head>
            <body>
                <h1>Sections Preview</h1>
                <div class="section">
                    <div class="section-title">Section 1</div>
                    <p>Section content will be displayed here.</p>
                </div>
                <div class="section">
                    <div class="section-title">Section 2</div>
                    <p>More section content will be displayed here.</p>
                </div>
            </body>
            </html>
        `;
    }

    /**
     * Get output preview
     */
    getOutputPreview() {
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Output Preview</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .output { background: #f8f9fa; padding: 20px; border-radius: 5px; }
                    .output-item { margin-bottom: 15px; padding: 10px; background: white; border-radius: 3px; }
                </style>
            </head>
            <body>
                <h1>Output Preview</h1>
                <div class="output">
                    <div class="output-item">
                        <strong>Generated Content:</strong>
                        <p>LLM generated content will appear here.</p>
                    </div>
                </div>
            </body>
            </html>
        `;
    }

    /**
     * Get default preview
     */
    getDefaultPreview() {
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Preview</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; text-align: center; }
                    .placeholder { color: #666; }
                </style>
            </head>
            <body>
                <div class="placeholder">
                    <h2>Preview</h2>
                    <p>Select content to preview</p>
                </div>
            </body>
            </html>
        `;
    }

    /**
     * Load content into iframe
     */
    loadContentIntoIframe(iframe, content, type) {
        try {
            // Write content to iframe
            const doc = iframe.contentDocument || iframe.contentWindow.document;
            doc.open();
            doc.write(content);
            doc.close();
        } catch (error) {
            this.logger.error('previewManager', 'Failed to load content into iframe:', error);
            
            // Fallback: use srcdoc attribute
            iframe.srcdoc = content;
        }
    }

    /**
     * Show preview error
     */
    showPreviewError(containerId, message) {
        this.logger.error('previewManager', `Preview error for container ${containerId}: ${message}`);
        
        const container = PREVIEW_STATE.previewContainers[containerId];
        if (!container) return;
        
        const previewArea = container.element.querySelector('.preview-area');
        if (previewArea) {
            previewArea.innerHTML = `
                <div class="preview-error">
                    <i class="fas fa-exclamation-triangle text-warning"></i>
                    <p>${message}</p>
                </div>
            `;
        }
        
        this.updatePreviewStatus(containerId, 'error', message);
    }

    /**
     * Update preview status
     */
    updatePreviewStatus(containerId, status, message) {
        const controls = document.querySelector(`.preview-controls[data-container-id="${containerId}"]`);
        if (!controls) return;
        
        const statusIndicator = controls.querySelector('.status-indicator');
        const statusText = controls.querySelector('.status-text');
        
        if (statusIndicator) {
            statusIndicator.className = `status-indicator status-${status}`;
        }
        
        if (statusText) {
            statusText.textContent = message;
        }
    }

    /**
     * Start live updates
     */
    startLiveUpdates(containerId) {
        this.logger.debug('previewManager', `Starting live updates for container ${containerId}`);
        
        // Set up interval for live updates
        this.refreshInterval = setInterval(() => {
            this.loadPreviewContent(containerId);
        }, PREVIEW_STATE.settings.refreshInterval);
    }

    /**
     * Stop live updates
     */
    stopLiveUpdates(containerId) {
        this.logger.debug('previewManager', `Stopping live updates for container ${containerId}`);
        
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Start auto refresh
     */
    startAutoRefresh() {
        if (PREVIEW_STATE.settings.autoRefresh) {
            this.logger.debug('previewManager', 'Starting auto refresh');
            // Auto refresh logic would go here
        }
    }

    /**
     * Stop auto refresh
     */
    stopAutoRefresh() {
        this.logger.debug('previewManager', 'Stopping auto refresh');
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Close fullscreen
     */
    closeFullscreen() {
        if (PREVIEW_STATE.fullscreenElement) {
            PREVIEW_STATE.fullscreenElement.remove();
            PREVIEW_STATE.fullscreenElement = null;
            PREVIEW_STATE.isFullscreen = false;
        }
        
        this.removeFullscreenEscapeListener();
    }

    /**
     * Add fullscreen escape listener
     */
    addFullscreenEscapeListener() {
        this.escapeListener = (event) => {
            if (event.key === 'Escape') {
                this.closeFullscreen();
            }
        };
        document.addEventListener('keydown', this.escapeListener);
    }

    /**
     * Remove fullscreen escape listener
     */
    removeFullscreenEscapeListener() {
        if (this.escapeListener) {
            document.removeEventListener('keydown', this.escapeListener);
            this.escapeListener = null;
        }
    }

    /**
     * On iframe load
     */
    onIframeLoad(containerId, mode) {
        this.logger.debug('previewManager', `Iframe loaded for container ${containerId} (mode: ${mode})`);
        this.updatePreviewStatus(containerId, 'success', `${mode.charAt(0).toUpperCase() + mode.slice(1)} preview loaded`);
    }

    /**
     * On iframe error
     */
    onIframeError(containerId, mode) {
        this.logger.error('previewManager', `Iframe error for container ${containerId} (mode: ${mode})`);
        this.updatePreviewStatus(containerId, 'error', 'Failed to load preview');
    }

    /**
     * Create preview controls
     */
    createPreviewControls() {
        // Add CSS for preview controls
        const style = document.createElement('style');
        style.textContent = `
            .preview-controls {
                margin-bottom: 10px;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #dee2e6;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .preview-controls .btn-group {
                margin-right: 10px;
            }
            .preview-controls .btn.active {
                background-color: #007bff;
                color: white;
            }
            .preview-area {
                min-height: 200px;
                border: 1px solid #ddd;
                border-radius: 5px;
                overflow: hidden;
            }
            .preview-placeholder {
                text-align: center;
                padding: 40px;
                color: #666;
            }
            .preview-placeholder i {
                font-size: 3em;
                margin-bottom: 10px;
            }
            .preview-error {
                text-align: center;
                padding: 40px;
                color: #dc3545;
            }
            .preview-iframe {
                width: 100%;
                height: 100%;
                border: none;
            }
            .preview-fullscreen-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: white;
                z-index: 10000;
                display: flex;
                flex-direction: column;
            }
            .fullscreen-header {
                padding: 15px;
                border-bottom: 1px solid #ddd;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .fullscreen-content {
                flex: 1;
                overflow: hidden;
            }
            .preview-status {
                display: flex;
                align-items: center;
                gap: 5px;
            }
            .status-indicator {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #6c757d;
            }
            .status-indicator.status-success {
                background: #28a745;
            }
            .status-indicator.status-error {
                background: #dc3545;
            }
            .status-indicator.status-loading {
                background: #ffc107;
                animation: pulse 1s infinite;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Emit preview event
     */
    emitPreviewEvent(type, data) {
        const event = new CustomEvent('previewEvent', {
            detail: {
                type: type,
                data: data,
                timestamp: Date.now()
            }
        });
        document.dispatchEvent(event);
        
        this.logger.debug('previewManager', `Preview event emitted: ${type}`, data);
    }

    /**
     * Set up global event listeners
     */
    setupEventListeners() {
        // Listen for content updates
        document.addEventListener('contentUpdate', (event) => {
            const { containerId } = event.detail;
            this.refreshPreview(containerId);
        });
        
        // Listen for preview requests
        document.addEventListener('requestPreview', (event) => {
            const { containerId, mode } = event.detail;
            this.setPreviewMode(containerId, mode);
        });
        
        // Listen for settings changes
        document.addEventListener('updatePreviewSettings', (event) => {
            const { settings } = event.detail;
            this.updateSettings(settings);
        });
    }

    /**
     * Refresh preview
     */
    refreshPreview(containerId) {
        this.logger.debug('previewManager', `Refreshing preview for container ${containerId}`);
        
        const container = PREVIEW_STATE.previewContainers[containerId];
        if (!container || container.currentMode === 'none') return;
        
        this.loadPreviewContent(containerId);
    }

    /**
     * Update settings
     */
    updateSettings(newSettings) {
        PREVIEW_STATE.settings = { ...PREVIEW_STATE.settings, ...newSettings };
        this.logger.debug('previewManager', 'Settings updated:', PREVIEW_STATE.settings);
        
        // Restart auto refresh if needed
        if (PREVIEW_STATE.settings.autoRefresh) {
            this.startAutoRefresh();
        } else {
            this.stopAutoRefresh();
        }
    }

    /**
     * Get current state
     */
    getState() {
        return { ...PREVIEW_STATE };
    }

    /**
     * Get preview data
     */
    getPreviewData(containerId) {
        return PREVIEW_STATE.previewData[containerId] || null;
    }

    /**
     * Check if preview is active
     */
    isPreviewActive(containerId) {
        const container = PREVIEW_STATE.previewContainers[containerId];
        return container && container.currentMode !== 'none';
    }

    /**
     * Check if fullscreen is active
     */
    isFullscreenActive() {
        return PREVIEW_STATE.isFullscreen;
    }

    /**
     * Cleanup
     */
    destroy() {
        this.logger.info('previewManager', 'Destroying preview manager');
        
        // Stop auto refresh
        this.stopAutoRefresh();
        
        // Close fullscreen if active
        if (PREVIEW_STATE.isFullscreen) {
            this.closeFullscreen();
        }
        
        // Remove all iframes
        Object.values(PREVIEW_STATE.previewContainers).forEach(container => {
            if (container.iframe) {
                container.iframe.remove();
            }
        });
        
        this.initialized = false;
        PREVIEW_STATE.initialized = false;
    }
}

// Create and export global instance
const previewManager = new PreviewManager();
window.previewManager = previewManager;
window.PREVIEW_STATE = PREVIEW_STATE;

// Log initialization
if (window.logger) {
    window.logger.info('previewManager', 'Preview Manager Module loaded');
} 