/**
 * Next Up Panel Micro-Module
 * Handles the Next Up panel functionality for One-Click Blog
 */

class NextUpPanel {
    constructor() {
        this.currentWeek = null;
        this.selectedIdea = null;
        this.alternativeIdeas = [];
        this.currentPostId = null;
        this.init();
    }

    init() {
        console.log('[Next Up Panel] Initialized');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Listen for schedule updates
        document.addEventListener('scheduleUpdated', (event) => {
            this.updateScheduleDisplay(event.detail.schedule);
        });
    }

    /**
     * Load next up data from API
     */
    async loadNextUp() {
        try {
            console.log('[Next Up Panel] Loading next up data...');
            const response = await fetch('/launchpad/one-click-publication/api/next-up');
            const result = await response.json();
            
            if (result.success) {
                this.updateDisplay(result.data);
                return result.data;
            } else {
                console.error('[Next Up Panel] Error loading data:', result.error);
                this.showError('Failed to load calendar data');
            }
        } catch (error) {
            console.error('[Next Up Panel] Error:', error);
            this.showError('Network error loading data');
        }
        return null;
    }

    /**
     * Update the entire Next Up panel display
     */
    updateDisplay(data) {
        this.currentWeek = data.current_week;
        this.selectedIdea = data.selected_idea;
        this.alternativeIdeas = data.alternative_ideas;
        this.currentPostId = data.post_id;
        
        this.updateWeekInfo();
        this.updateSelectedIdea();
        this.updateAlternativeIdeas();
        this.updateScheduleDisplay(data);
        this.updateProductionButton(data.production_status);
        this.updatePostId(data.post_id);
    }

    /**
     * Update week information display
     */
    updateWeekInfo() {
        if (!this.currentWeek) return;
        
        const weekNumber = document.querySelector('.week-number');
        const weekDates = document.querySelector('.week-dates');
        
        if (weekNumber) {
            weekNumber.textContent = `Week ${this.currentWeek.week_number}`;
        }
        
        if (weekDates) {
            const startDay = this.currentWeek.start_date.split('-')[2];
            const endDay = this.currentWeek.end_date.split('-')[2];
            weekDates.textContent = `${this.currentWeek.month_name} ${startDay}-${endDay}, ${this.currentWeek.year}`;
        }
    }

    /**
     * Update selected idea display
     */
    updateSelectedIdea() {
        if (!this.selectedIdea) return;
        
        const ideaTitle = document.querySelector('.idea-title');
        const ideaDescription = document.querySelector('.idea-description');
        const ideaCategories = document.querySelector('.idea-categories');
        const ideaContentType = document.querySelector('.idea-content-type');
        const ideaPriority = document.querySelector('.idea-priority');
        
        if (ideaTitle) ideaTitle.textContent = this.selectedIdea.title;
        if (ideaDescription) ideaDescription.textContent = this.selectedIdea.description;
        if (ideaCategories) ideaCategories.textContent = this.selectedIdea.categories.join(', ');
        if (ideaContentType) ideaContentType.textContent = this.selectedIdea.content_type;
        if (ideaPriority) ideaPriority.textContent = this.selectedIdea.priority;
    }

    /**
     * Update Post ID display
     */
    updatePostId(postId) {
        const postIdValue = document.querySelector('.post-id-value');
        if (postIdValue) {
            postIdValue.textContent = postId || 'Not assigned';
            postIdValue.classList.remove('checking');
        }
    }

    /**
     * Update alternative ideas display
     */
    updateAlternativeIdeas() {
        const alternativesList = document.querySelector('.alternatives-list');
        if (!alternativesList || !this.alternativeIdeas.length) return;
        
        alternativesList.innerHTML = '';
        
        this.alternativeIdeas.forEach(idea => {
            const item = this.createAlternativeItem(idea);
            alternativesList.appendChild(item);
        });
    }

    /**
     * Create alternative idea item element
     */
    createAlternativeItem(idea) {
        const item = document.createElement('div');
        item.className = 'alternative-item';
        item.innerHTML = `
            <h5>${idea.title}</h5>
            <div class="alternative-details" style="display: none;">
                <p>${idea.description}</p>
                <div class="alternative-tags">
                    <span class="tag">${idea.content_type}</span>
                    <span class="tag priority-${idea.priority.toLowerCase()}">${idea.priority}</span>
                </div>
                <div class="action-buttons">
                    <button class="select-btn" onclick="nextUpPanel.selectIdea('${idea.id}')">
                        <i class="fas fa-check"></i> Select
                    </button>
                    <button class="cancel-btn" onclick="nextUpPanel.cancelIdeaSelection()">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                </div>
            </div>
        `;
        
        // Add click handler to toggle details
        item.querySelector('h5').addEventListener('click', (e) => {
            this.toggleAlternativeItem(e, idea);
        });
        
        return item;
    }

    /**
     * Toggle alternative idea details
     */
    toggleAlternativeItem(event, idea) {
        const item = event.target.closest('.alternative-item');
        const details = item.querySelector('.alternative-details');
        
        if (details.style.display === 'none') {
            // Close all other expanded items
            document.querySelectorAll('.alternative-details').forEach(d => {
                d.style.display = 'none';
            });
            // Open this one
            details.style.display = 'block';
            item.classList.add('expanded');
        } else {
            details.style.display = 'none';
            item.classList.remove('expanded');
        }
    }

    /**
     * Select an alternative idea
     */
    async selectIdea(ideaId) {
        console.log('[Next Up Panel] Selecting idea:', ideaId);
        
        try {
            // Find the selected idea from alternatives
            const selectedIdea = this.alternativeIdeas.find(idea => idea.id == ideaId);
            if (!selectedIdea) {
                this.showNotification('Idea not found', 'error');
                return;
            }
            
            // IMMEDIATE UI UPDATE - Update the display optimistically
            this.updateSelectedIdeaOptimistically(selectedIdea);
            
            // Show loading state
            this.showNotification('Selecting idea...', 'info');
            
            // Call API to select the idea
            const response = await fetch('/launchpad/one-click-publication/api/select-idea', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ idea_id: ideaId })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Close all expanded alternatives
                document.querySelectorAll('.alternative-details').forEach(d => {
                    d.style.display = 'none';
                });
                document.querySelectorAll('.alternative-item').forEach(item => {
                    item.classList.remove('expanded');
                });
                
                // Update the internal data structure
                this.selectedIdea = selectedIdea;
                this.alternativeIdeas = this.alternativeIdeas.filter(idea => idea.id != ideaId);
                
                // Add the previous selected idea to alternatives
                if (this.previousSelectedIdea) {
                    this.alternativeIdeas.unshift(this.previousSelectedIdea);
                }
                
                // Update alternatives display
                this.updateAlternativeIdeas();
                
                // Get updated Post ID from server
                await this.updatePostIdFromServer();
                
                this.showNotification('Idea selected successfully!', 'success');
            } else {
                // Revert the optimistic update on failure
                this.revertOptimisticUpdate();
                this.showNotification(`Failed to select idea: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('[Next Up Panel] Error selecting idea:', error);
            // Revert the optimistic update on error
            this.revertOptimisticUpdate();
            this.showNotification('Error selecting idea. Please try again.', 'error');
        }
    }

    /**
     * Update selected idea optimistically (immediate UI update)
     */
    updateSelectedIdeaOptimistically(idea) {
        // Store the previous selection for potential revert
        this.previousSelectedIdea = this.selectedIdea;
        
        // Update the selected idea display immediately
        const titleElement = document.querySelector('.idea-title');
        const descriptionElement = document.querySelector('.idea-description');
        const categoriesElement = document.querySelector('.idea-categories');
        const contentTypeElement = document.querySelector('.idea-content-type');
        const priorityElement = document.querySelector('.idea-priority');
        
        if (titleElement) titleElement.textContent = idea.title;
        if (descriptionElement) descriptionElement.textContent = idea.description;
        if (categoriesElement) categoriesElement.textContent = idea.categories.join(', ');
        if (contentTypeElement) contentTypeElement.textContent = idea.content_type;
        if (priorityElement) priorityElement.textContent = idea.priority;
        
        // Update Post ID optimistically - check if this idea has an existing post
        this.updatePostIdOptimistically(idea);
        
        // Add visual feedback with CSS classes
        const selectedIdeaContainer = document.querySelector('.selected-idea');
        if (selectedIdeaContainer) {
            selectedIdeaContainer.classList.add('updating');
            setTimeout(() => {
                selectedIdeaContainer.classList.remove('updating');
            }, 500);
        }
    }
    
    /**
     * Revert optimistic update on failure
     */
    revertOptimisticUpdate() {
        if (this.previousSelectedIdea) {
            this.updateSelectedIdeaOptimistically(this.previousSelectedIdea);
            this.previousSelectedIdea = null;
        }
    }
    
    /**
     * Update Post ID optimistically - show checking state
     */
    updatePostIdOptimistically(idea) {
        const postIdElement = document.querySelector('.post-id-value');
        if (postIdElement) {
            postIdElement.textContent = 'Checking...';
            postIdElement.classList.add('checking');
        }
    }
    
    /**
     * Update Post ID from server response
     */
    async updatePostIdFromServer() {
        try {
            const response = await fetch('/launchpad/one-click-publication/api/next-up');
            const data = await response.json();
            
            if (data.success) {
                this.updatePostId(data.data.post_id);
            }
        } catch (error) {
            console.log('[Next Up Panel] Could not update Post ID from server');
        }
    }

    /**
     * Cancel idea selection
     */
    cancelIdeaSelection() {
        // Close all expanded alternatives
        document.querySelectorAll('.alternative-details').forEach(d => {
            d.style.display = 'none';
        });
        document.querySelectorAll('.alternative-item').forEach(item => {
            item.classList.remove('expanded');
        });
    }

    /**
     * Update schedule display
     */
    updateScheduleDisplay(data) {
        const scheduleDate = document.querySelector('.schedule-date');
        const scheduleRelative = document.querySelector('.schedule-relative');
        
        if (scheduleDate) {
            scheduleDate.textContent = data.scheduled_date || 'Not scheduled';
        }
        if (scheduleRelative) {
            scheduleRelative.textContent = data.scheduled_relative || '';
        }
    }

    /**
     * Update production button based on status
     */
    updateProductionButton(status) {
        const productionBtn = document.querySelector('.production-btn');
        if (!productionBtn) return;
        
        const btnText = productionBtn.querySelector('.btn-text');
        const btnIcon = productionBtn.querySelector('i');
        
        // Remove all status classes
        productionBtn.classList.remove('loading', 'progress', 'completed');
        
        switch (status) {
            case 'not_started':
                btnText.textContent = 'Start Production';
                btnIcon.className = 'fas fa-play';
                break;
            case 'in_progress':
                btnText.textContent = 'View Progress';
                btnIcon.className = 'fas fa-eye';
                productionBtn.classList.add('progress');
                break;
            case 'completed':
                btnText.textContent = 'Completed';
                btnIcon.className = 'fas fa-check';
                productionBtn.classList.add('completed');
                break;
            default:
                btnText.textContent = 'Start Production';
                btnIcon.className = 'fas fa-play';
        }
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        // This would integrate with a notification system
        console.log(`[Next Up Panel] ${type.toUpperCase()}: ${message}`);
    }

    /**
     * Show error message
     */
    showError(message) {
        this.showNotification(message, 'error');
    }
}

// Export for use in other modules
window.NextUpPanel = NextUpPanel;
