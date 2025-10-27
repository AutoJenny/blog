class AuthorPanel {
    constructor() {
        this.postId = window.postId;
        this.initializeElements();
        this.loadCurrentAuthor();
        this.setupEventListeners();
    }
    
    initializeElements() {
        this.authorSelect = document.getElementById('author-select');
        this.statusSpan = document.getElementById('author-status');
        this.accordionContent = document.getElementById('author-content');
        this.accordionIcon = document.getElementById('author-accordion-icon');
    }
    
    setupEventListeners() {
        if (this.authorSelect) {
            this.authorSelect.addEventListener('change', () => {
                this.updateStatus();
                this.saveAuthor(); // Auto-save on change
            });
        }
    }
    
    loadCurrentAuthor() {
        if (!this.postId) return;
        
        fetch(`/header/api/posts/${this.postId}/get-title-summary`)
            .then(response => response.json())
            .then(data => {
                if (data.author_name) {
                    this.authorSelect.value = data.author_name;
                } else {
                    // Default to Caitrin Stewart if no author set
                    this.authorSelect.value = 'Caitrin Stewart';
                    this.saveAuthor(); // Auto-save the default
                }
                this.updateStatus();
            })
            .catch(error => {
                console.error('Error loading current author:', error);
                // Default to Caitrin Stewart on error
                this.authorSelect.value = 'Caitrin Stewart';
                this.updateStatus();
            });
    }
    
    updateStatus() {
        const authorName = this.authorSelect.value;
        if (authorName) {
            this.statusSpan.textContent = authorName;
            this.statusSpan.style.color = '#4ade80';
        } else {
            this.statusSpan.textContent = 'Not Set';
            this.statusSpan.style.color = '#ef4444';
        }
    }
    
    saveAuthor() {
        const authorName = this.authorSelect.value;
        if (!authorName) {
            return; // Don't save if no author selected
        }
        
        if (!this.postId) return;
        
        // Show saving state
        const oldStatus = this.statusSpan.textContent;
        this.statusSpan.textContent = 'Saving...';
        this.statusSpan.style.color = '#fbbf24';
        
        fetch(`/header/api/posts/${this.postId}/save-author`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ author_name: authorName })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.statusSpan.textContent = 'Saved!';
                this.statusSpan.style.color = '#4ade80';
                setTimeout(() => {
                    this.updateStatus();
                }, 1500);
            } else {
                console.error('Error saving author:', data.error);
                this.statusSpan.textContent = oldStatus;
                this.statusSpan.style.color = '#ef4444';
            }
        })
        .catch(error => {
            console.error('Error saving author:', error);
            this.statusSpan.textContent = oldStatus;
            this.statusSpan.style.color = '#ef4444';
        });
    }
}

// Accordion functionality
function toggleAuthorAccordion() {
    const content = document.getElementById('author-content');
    const icon = document.getElementById('author-accordion-icon');
    
    if (content.classList.contains('active')) {
        content.classList.remove('active');
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
    } else {
        content.classList.add('active');
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
    }
}

// Initialize on page load
let authorPanel;
document.addEventListener('DOMContentLoaded', function() {
    authorPanel = new AuthorPanel();
});

