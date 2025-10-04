// imaging-navigation.js - Imaging Navigation JavaScript for BlogForge
// This file provides navigation functionality for imaging pages

console.log('BlogForge imaging-navigation.js loaded');

// Imaging navigation functionality
class ImagingNavigation {
    constructor() {
        this.currentPostId = null;
        this.currentStage = 'imaging';
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
        
        // Parse URL structure: /imaging/posts/{id}/sections/{substage}
        if (pathParts.length >= 2 && pathParts[0] === 'imaging') {
            if (pathParts[1] === 'posts' && pathParts.length >= 3) {
                this.currentPostId = pathParts[2];
                this.currentStage = 'imaging';
                this.currentSubstage = pathParts[4] || null; // sections/image-generation
                this.currentStep = null; // No steps in imaging
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
        document.querySelectorAll('.nav-item, .imaging-nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to current stage/substage
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
    }
    
    updateBreadcrumbs() {
        const breadcrumbContainer = document.querySelector('.breadcrumb, .imaging-breadcrumb');
        if (!breadcrumbContainer) return;
        
        const breadcrumbs = [];
        
        // Add home
        breadcrumbs.push({
            text: 'Home',
            url: '/'
        });
        
        // Add imaging
        breadcrumbs.push({
            text: 'Imaging',
            url: '/imaging/'
        });
        
        // Add post
        if (this.currentPostId) {
            breadcrumbs.push({
                text: `Post ${this.currentPostId}`,
                url: `/imaging/posts/${this.currentPostId}`
            });
        }
        
        // Add substage
        if (this.currentSubstage) {
            breadcrumbs.push({
                text: this.currentSubstage.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                url: `/imaging/posts/${this.currentPostId}/sections/${this.currentSubstage}`
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
            const navLink = e.target.closest('.imaging-nav-link, .nav-link');
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
        const navItems = Array.from(document.querySelectorAll('.imaging-nav-link, .nav-link'));
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
    navigateTo(substage = null) {
        let url = `/imaging/posts/${this.currentPostId}`;
        if (substage) {
            url += `/sections/${substage}`;
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
    
    // Imaging-specific methods
    navigateToImageGeneration() {
        this.navigateTo('image-generation');
    }
    
    navigateToImageConcepts() {
        this.navigateTo('image-concepts');
    }
    
    navigateToImagePrompts() {
        this.navigateTo('image-prompts');
    }
    
    navigateToImageCaptions() {
        this.navigateTo('image-captions');
    }
}

// Initialize imaging navigation when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('BlogForge imaging-navigation.js initialized');
    
    // Initialize imaging navigation
    window.imagingNav = new ImagingNavigation();
});

// Export for use in other scripts
window.ImagingNavigation = ImagingNavigation;
