/**
 * Mini-Preview Panel - Tab switching and content management
 */

// Tab switching functionality
function switchPreviewTab(tabName) {
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Remove active class from all tab panes
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    
    // Add active class to selected tab button
    const selectedButton = document.querySelector(`[data-tab="${tabName}"]`);
    if (selectedButton) {
        selectedButton.classList.add('active');
    }
    
    // Add active class to selected tab pane
    const selectedPane = document.getElementById(`${tabName}-tab`);
    if (selectedPane) {
        selectedPane.classList.add('active');
    }
    
    console.log(`[Mini-Preview Panel] Switched to ${tabName} tab`);
}

// Initialize the panel
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Mini-Preview Panel] Initialized');
    
    // Ensure development tab is active by default
    switchPreviewTab('development');
});

// Export functions for external use
window.switchPreviewTab = switchPreviewTab;
