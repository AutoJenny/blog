// workflow-nav.js - Workflow Navigation JavaScript for BlogForge
// This file provides navigation functionality for workflow pages

console.log('BlogForge workflow-nav.js loaded');

// Workflow navigation functionality
class WorkflowNavigation {
    constructor() {
        this.currentPostId = null;
        this.currentStage = null;
        this.currentSubstage = null;
        this.currentStep = null;
        this.init();
    }
    
    init() {
        this.parseCurrentLocation();
        this.initializeNavigation();
        this.setupEventListeners();
    }
    
    parseCurrentLocation() {
        const path = window.location.pathname;
        const pathParts = path.split('/').filter(part => part);
        
        // Parse URL structure: /workflow/posts/{id}/{stage}/{substage}/{step}
        if (pathParts.length >= 2 && pathParts[0] === 'workflow') {
            if (pathParts[1] === 'posts' && pathParts.length >= 3) {
                this.currentPostId = pathParts[2];
                this.currentStage = pathParts[3] || null;
                this.currentSubstage = pathParts[4] || null;
                this.currentStep = pathParts[5] || null;
            }
        }
    }
    
    initializeNavigation() {
        // Highlight current navigation item
        this.highlightCurrentNavItem();
        
        // Update breadcrumbs if they exist
        this.updateBreadcrumbs();
    }
    
    highlightCurrentNavItem() {
        // Remove active class from all nav items
        document.querySelectorAll('.nav-item, .workflow-nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to current stage/substage/step
        if (this.currentStage) {
            const stageElement = document.querySelector(`[data-stage="${this.currentStage}"]`);
            if (stageElement) {
                stageElement.classList.add('active');
            }
        }
        
        if (this.currentSubstage) {
            const substageElement = document.querySelector(`[data-substage="${this.currentSubstage}"]`);
            if (substageElement) {
                substageElement.classList.add('active');
            }
        }
        
        if (this.currentStep) {
            const stepElement = document.querySelector(`[data-step="${this.currentStep}"]`);
            if (stepElement) {
                stepElement.classList.add('active');
            }
        }
    }
    
    updateBreadcrumbs() {
        const breadcrumbContainer = document.querySelector('.breadcrumb, .workflow-breadcrumb');
        if (!breadcrumbContainer) return;
        
        const breadcrumbs = [];
        
        // Add home
        breadcrumbs.push({
            text: 'Home',
            url: '/'
        });
        
        // Add workflow
        breadcrumbs.push({
            text: 'Workflow',
            url: '/workflow/'
        });
        
        // Add post
        if (this.currentPostId) {
            breadcrumbs.push({
                text: `Post ${this.currentPostId}`,
                url: `/workflow/posts/${this.currentPostId}`
            });
        }
        
        // Add stage
        if (this.currentStage) {
            breadcrumbs.push({
                text: this.currentStage.charAt(0).toUpperCase() + this.currentStage.slice(1),
                url: `/workflow/posts/${this.currentPostId}/${this.currentStage}`
            });
        }
        
        // Add substage
        if (this.currentSubstage) {
            breadcrumbs.push({
                text: this.currentSubstage.charAt(0).toUpperCase() + this.currentSubstage.slice(1),
                url: `/workflow/posts/${this.currentPostId}/${this.currentStage}/${this.currentSubstage}`
            });
        }
        
        // Add step
        if (this.currentStep) {
            breadcrumbs.push({
                text: this.currentStep.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                url: window.location.pathname
            });
        }
        
        // Update breadcrumb HTML
        breadcrumbContainer.innerHTML = breadcrumbs.map((crumb, index) => {
            const isLast = index === breadcrumbs.length - 1;
            return `
                <li class="breadcrumb-item ${isLast ? 'active' : ''}">
                    ${isLast ? crumb.text : `<a href="${crumb.url}">${crumb.text}</a>`}
                </li>
            `;
        }).join('');
    }
    
    setupEventListeners() {
        // Handle navigation clicks
        document.addEventListener('click', (e) => {
            const navLink = e.target.closest('.workflow-nav-link, .nav-link');
            if (navLink) {
                this.handleNavigationClick(navLink, e);
            }
        });
        
        // Handle keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                this.handleKeyboardNavigation(e);
            }
        });
    }
    
    handleNavigationClick(link, event) {
        // Add loading state
        link.classList.add('loading');
        
        // Remove loading state after a short delay
        setTimeout(() => {
            link.classList.remove('loading');
        }, 500);
    }
    
    handleKeyboardNavigation(event) {
        const currentElement = document.activeElement;
        const navItems = Array.from(document.querySelectorAll('.workflow-nav-link, .nav-link'));
        const currentIndex = navItems.indexOf(currentElement);
        
        if (currentIndex === -1) return;
        
        let targetIndex;
        if (event.key === 'ArrowLeft') {
            targetIndex = Math.max(0, currentIndex - 1);
        } else if (event.key === 'ArrowRight') {
            targetIndex = Math.min(navItems.length - 1, currentIndex + 1);
        }
        
        if (targetIndex !== currentIndex) {
            navItems[targetIndex].focus();
            event.preventDefault();
        }
    }
    
    // Public methods
    navigateTo(stage, substage = null, step = null) {
        let url = `/workflow/posts/${this.currentPostId}/${stage}`;
        if (substage) {
            url += `/${substage}`;
        }
        if (step) {
            url += `/${step}`;
        }
        window.location.href = url;
    }
    
    getCurrentLocation() {
        return {
            postId: this.currentPostId,
            stage: this.currentStage,
            substage: this.currentSubstage,
            step: this.currentStep
        };
    }
}

// Initialize workflow navigation when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('BlogForge workflow-nav.js initialized');
    
    // Initialize workflow navigation
    window.workflowNav = new WorkflowNavigation();
});

// Export for use in other scripts
window.WorkflowNavigation = WorkflowNavigation;
