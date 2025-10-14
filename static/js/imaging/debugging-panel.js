// Debugging Panel - Self-contained JavaScript module
class DebuggingPanel {
    constructor() {
        this.container = document.getElementById('debugging-panel');
        this.init();
    }

    init() {
        console.log('[Debugging Panel] Initializing debugging panel');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Listen for debugging events
        document.addEventListener('imaging:debug-info', (event) => {
            this.displayDebugInfo(event.detail);
        });
    }

    displayDebugInfo(debugData) {
        console.log('[Debugging Panel] Displaying debug info:', debugData);
        
        const debugContent = document.getElementById('debugging-content');
        if (debugContent) {
            debugContent.innerHTML = `
                <div class="debug-section">
                    <h6>Debug Information</h6>
                    <pre>${JSON.stringify(debugData, null, 2)}</pre>
                </div>
            `;
        }
    }

    log(message, data = null) {
        console.log('[Debugging Panel]', message, data);
        
        const debugContent = document.getElementById('debugging-content');
        if (debugContent) {
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.className = 'debug-log-entry';
            logEntry.innerHTML = `
                <span class="debug-timestamp">[${timestamp}]</span>
                <span class="debug-message">${message}</span>
                ${data ? `<pre class="debug-data">${JSON.stringify(data, null, 2)}</pre>` : ''}
            `;
            debugContent.appendChild(logEntry);
            debugContent.scrollTop = debugContent.scrollHeight;
        }
    }
}

// Make the panel globally accessible
window.DebuggingPanel = DebuggingPanel;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('debugging-panel')) {
        window.debuggingPanel = new DebuggingPanel();
        console.log('[Debugging Panel] Initialized');
    }
});
