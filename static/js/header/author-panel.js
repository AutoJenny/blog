class AuthorPanel {
    constructor() {
        this.postId = window.postId;
        this.initializeElements();
        this.loadCurrentAuthor();
        this.setupEventListeners();
    }
    
    initializeElements() {
        this.authorSelect = document.getElementById('author-select');
        this.saveBtn = document.getElementById('save-author-btn');
        this.statusSpan = document.getElementById('author-status');
        this.accordionContent = document.getElementById('author-content');
        this.accordionIcon = document.getElementById('author-accordion-icon');
    }
    
    setupEventListeners() {
        if (this.saveBtn) {
            this.saveBtn.addEventListener('click', () => this.saveAuthor());
        }
        
        if (this.authorSelect) {
            this.authorSelect.addEventListener('change', () => this.updateStatus());
        }
    }
    
    loadCurrentAuthor() {
        if (!this.postId) return;
        
        fetch(`/header/api/posts/${this.postId}/get-title-summary`)
            .then(response => response.json())
            .then(data => {
                if (data.author_name) {
                    this.authorSelect.value = data.author_name;
                    this.updateStatus();
                }
            })
            .catch(error => {
                console.error('Error loading current author:', error);
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
            alert('Please select an author');
            return;
        }
        
        if (!this.postId) return;
        
        // Show saving state
        this.saveBtn.disabled = true;
        this.saveBtn.textContent = 'Saving...';
        
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
                this.saveBtn.textContent = 'Saved!';
                this.updateStatus();
                setTimeout(() => {
                    this.saveBtn.textContent = 'Save';
                    this.saveBtn.disabled = false;
                }, 2000);
            } else {
                alert('Error saving author: ' + (data.error || 'Unknown error'));
                this.saveBtn.disabled = false;
                this.saveBtn.textContent = 'Save';
            }
        })
        .catch(error => {
            console.error('Error saving author:', error);
            alert('Error saving author: ' + error.message);
            this.saveBtn.disabled = false;
            this.saveBtn.textContent = 'Save';
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

