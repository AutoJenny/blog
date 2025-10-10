/**
 * One-Click Blog Manager - JavaScript Module
 * Handles all interactions and state management for the One-Click Blog automation system
 */

class OneClickBlogManager {
    constructor() {
        this.currentPostId = null;
        this.automationState = {};
        this.alerts = [];
        this.pollingInterval = null;
        this.settings = this.loadSettings();
        this.init();
    }

    init() {
        console.log('[One-Click Blog] Initializing...');
        this.loadNextUp();
        this.loadPipelineStatus();
        this.loadBlogQueue();
        this.loadAlerts();
        this.setupEventListeners();
        this.startPolling();
        console.log('[One-Click Blog] Initialized successfully');
    }

    // ===== Next Up Panel Methods =====
    
    async loadNextUp() {
        try {
            const response = await fetch('/launchpad/one-click-blog/api/next-up');
            const data = await response.json();
            
            if (data.success) {
                this.updateNextUpDisplay(data.data);
            } else {
                console.error('[One-Click Blog] Error loading next up data:', data.error);
                this.showNotification('Failed to load calendar data', 'error');
            }
        } catch (error) {
            console.error('[One-Click Blog] Error loading next up data:', error);
            this.showNotification('Failed to load calendar data', 'error');
        }
    }

    updateNextUpDisplay(data) {
        // Update week info
        document.querySelector('.week-number').textContent = `Week ${data.current_week.week_number}`;
        document.querySelector('.week-dates').textContent = `${data.current_week.month_name} ${data.current_week.start_date.split('-')[2]}-${data.current_week.end_date.split('-')[2]}, ${data.current_week.year}`;
        
        // Update selected idea
        const ideaContent = document.querySelector('.idea-content');
        ideaContent.querySelector('h4').textContent = data.selected_idea.title;
        ideaContent.querySelector('p').textContent = data.selected_idea.description;
        
        // Update tags
        const tagsContainer = ideaContent.querySelector('.idea-tags');
        tagsContainer.innerHTML = '';
        
        // Add category tags
        if (data.selected_idea.categories && data.selected_idea.categories.length > 0) {
            data.selected_idea.categories.forEach(category => {
                const tag = document.createElement('span');
                tag.className = 'tag';
                tag.textContent = category;
                tagsContainer.appendChild(tag);
            });
        }
        
        // Add content type tag if available
        if (data.selected_idea.content_type) {
            const contentTypeTag = document.createElement('span');
            contentTypeTag.className = 'tag';
            contentTypeTag.textContent = data.selected_idea.content_type.charAt(0).toUpperCase() + data.selected_idea.content_type.slice(1);
            tagsContainer.appendChild(contentTypeTag);
        }
        
        // Add priority tag
        const priorityTag = document.createElement('span');
        priorityTag.className = 'tag priority-high';
        const priorityText = data.selected_idea.priority === 'mandatory' ? 'Mandatory' : 
                           data.selected_idea.priority === 'random' ? 'Random' : 
                           data.selected_idea.priority.charAt(0).toUpperCase() + data.selected_idea.priority.slice(1);
        priorityTag.textContent = priorityText;
        tagsContainer.appendChild(priorityTag);
        
        // Update schedule display
        const scheduleDate = document.querySelector('.schedule-date');
        const scheduleRelative = document.querySelector('.schedule-relative');
        
        if (scheduleDate) {
            scheduleDate.textContent = data.scheduled_date || 'Not scheduled';
        }
        if (scheduleRelative) {
            scheduleRelative.textContent = data.scheduled_relative || '';
        }
        
        // Update production button based on status
        this.updateProductionButton(data.production_status);
        
        // Update alternative ideas
        this.updateAlternativeIdeas(data.alternative_ideas);
        
        // Update timeline labels
        this.updateTimelineLabels(data.current_week.week_number);
    }
    
    updateTimelineLabels(currentWeek) {
        const timelineLabels = document.querySelectorAll('.timeline-label');
        timelineLabels[0].textContent = `Week ${currentWeek}`;
        timelineLabels[1].textContent = `Week ${currentWeek + 1}`;
        timelineLabels[2].textContent = `Week ${currentWeek + 2}`;
    }
    
    updateProductionButton(status) {
        const button = document.getElementById('production-btn');
        const btnText = button.querySelector('.btn-text');
        const icon = button.querySelector('i');
        
        // Remove existing status classes
        button.classList.remove('loading', 'progress', 'completed');
        
        switch (status) {
            case 'not_started':
                btnText.textContent = 'Start Production';
                icon.className = 'fas fa-rocket';
                button.className = 'btn btn-primary production-btn';
                break;
            case 'in_progress':
                btnText.textContent = 'In Progress';
                icon.className = 'fas fa-spinner fa-spin';
                button.className = 'btn btn-warning production-btn progress';
                break;
            case 'completed':
                btnText.textContent = 'View Progress';
                icon.className = 'fas fa-check-circle';
                button.className = 'btn btn-success production-btn completed';
                break;
            case 'failed':
                btnText.textContent = 'Retry Production';
                icon.className = 'fas fa-exclamation-triangle';
                button.className = 'btn btn-danger production-btn';
                break;
            default:
                btnText.textContent = 'Start Production';
                icon.className = 'fas fa-rocket';
                button.className = 'btn btn-primary production-btn';
        }
    }
    
    handleProductionAction() {
        const button = document.getElementById('production-btn');
        const status = button.classList.contains('completed') ? 'completed' : 
                      button.classList.contains('progress') ? 'in_progress' : 
                      button.classList.contains('loading') ? 'loading' : 'not_started';
        
        switch (status) {
            case 'not_started':
            case 'failed':
                this.startProduction();
                break;
            case 'in_progress':
                this.showNotification('Production is already in progress', 'info');
                break;
            case 'completed':
                this.viewProgress();
                break;
        }
    }
    
    updateAlternativeIdeas(alternativeIdeas) {
        const alternativesList = document.getElementById('alternatives-list');
        
        if (!alternativeIdeas || alternativeIdeas.length === 0) {
            alternativesList.innerHTML = '<div class="no-alternatives">No alternative ideas available</div>';
            return;
        }
        
        alternativesList.innerHTML = '';
        alternativeIdeas.forEach(idea => {
            const alternativeItem = document.createElement('div');
            alternativeItem.className = 'alternative-item';
            alternativeItem.onclick = (e) => this.toggleAlternativeItem(e, idea);
            
            alternativeItem.innerHTML = `
                <h5>${idea.title}</h5>
                <div class="alternative-details">
                    <p>${idea.description}</p>
                    <div class="alternative-tags">
                        ${idea.categories.map(cat => `<span class="tag">${cat}</span>`).join('')}
                        ${idea.content_type ? `<span class="tag">${idea.content_type.charAt(0).toUpperCase() + idea.content_type.slice(1)}</span>` : ''}
                        <span class="tag">${idea.priority === 'mandatory' ? 'Mandatory' : idea.priority === 'random' ? 'Random' : idea.priority}</span>
                    </div>
                    <div class="action-buttons">
                        <button class="select-btn" onclick="event.stopPropagation(); oneClickBlogManager.selectIdea(${idea.id})">
                            <i class="fas fa-check"></i> Select
                        </button>
                        <button class="cancel-btn" onclick="event.stopPropagation(); oneClickBlogManager.cancelIdeaSelection()">
                            <i class="fas fa-times"></i> Cancel
                        </button>
                    </div>
                </div>
            `;
            
            alternativesList.appendChild(alternativeItem);
        });
    }
    
    toggleAlternativeItem(event, idea) {
        event.stopPropagation();
        const item = event.currentTarget;
        const isExpanded = item.classList.contains('expanded');
        
        // Close all other expanded items
        document.querySelectorAll('.alternative-item.expanded').forEach(expandedItem => {
            if (expandedItem !== item) {
                expandedItem.classList.remove('expanded');
            }
        });
        
        // Toggle current item
        if (isExpanded) {
            item.classList.remove('expanded');
        } else {
            item.classList.add('expanded');
        }
    }

    cancelIdeaSelection() {
        console.log('[One-Click Blog] Cancelling idea selection');
        
        // Close all expanded alternatives
        document.querySelectorAll('.alternative-item.expanded').forEach(item => {
            item.classList.remove('expanded');
        });
        
        this.showNotification('Idea selection cancelled', 'info');
    }

    selectIdea(ideaId) {
        console.log(`[One-Click Blog] Selecting idea ${ideaId}`);
        
        // Close all expanded alternatives
        document.querySelectorAll('.alternative-item.expanded').forEach(item => {
            item.classList.remove('expanded');
        });
        
        // This would normally make an API call to update the selection
        // For now, simulate selecting the idea
        this.showNotification(`Selected idea ${ideaId}. This would update the calendar selection.`, 'success');
        
        // In a real implementation, this would:
        // 1. Call API to update the selected idea
        // 2. Refresh the Next Up panel with new selection
        // 3. Update the calendar ideas page if it's open
    }

    startProduction() {
        console.log('[One-Click Blog] Starting production...');
        this.showNotification('Starting automation pipeline...', 'info');
        
        // Update button to show progress
        this.updateProductionButton('in_progress');
        
        // This would normally make an API call to start automation
        // For now, simulate starting
        setTimeout(() => {
            this.showNotification('Automation started successfully', 'success');
            this.loadPipelineStatus(); // Refresh pipeline status
        }, 1000);
    }
    
    viewProgress() {
        console.log('[One-Click Blog] Viewing progress...');
        this.showNotification('Opening progress view...', 'info');
        // This would open a detailed progress modal or navigate to progress page
    }

    showScheduleModal() {
        // Load current schedule data into the modal
        this.loadCurrentScheduleData();
        document.getElementById('schedule-modal').style.display = 'flex';
    }
    
    loadCurrentScheduleData() {
        // Get current schedule data from the display
        const scheduleDate = document.querySelector('.schedule-date').textContent;
        const scheduleRelative = document.querySelector('.schedule-relative').textContent;
        
        // Parse the current date if it's not "Not scheduled"
        if (scheduleDate && scheduleDate !== 'Not scheduled') {
            // Convert "Oct 10, 2025" to "2025-10-10" format
            const dateObj = new Date(scheduleDate);
            if (!isNaN(dateObj.getTime())) {
                document.getElementById('publish-date').value = dateObj.toISOString().split('T')[0];
            }
        } else {
            // Default to today if no schedule
            const today = new Date();
            document.getElementById('publish-date').value = today.toISOString().split('T')[0];
        }
        
        // Default time to 14:00
        document.getElementById('publish-time').value = '14:00';
    }

    closeScheduleModal() {
        document.getElementById('schedule-modal').style.display = 'none';
    }

    async schedulePost() {
        const publishDate = document.getElementById('publish-date').value;
        const publishTime = document.getElementById('publish-time').value;
        const requireApproval = document.getElementById('require-approval').checked;
        const autoPublish = document.getElementById('auto-publish').checked;
        
        console.log('[One-Click Blog] Scheduling post:', {
            publishDate,
            publishTime,
            requireApproval,
            autoPublish
        });
        
        try {
            // Make API call to update schedule
            const response = await fetch('/launchpad/one-click-blog/api/update-schedule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    scheduled_date: publishDate,
                    scheduled_time: publishTime,
                    requires_approval: requireApproval,
                    auto_publish: autoPublish
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.closeScheduleModal();
                this.showNotification('Post scheduled successfully', 'success');
                
                // Refresh the Next Up data to show updated schedule
                await this.loadNextUp();
            } else {
                this.showNotification(`Failed to schedule: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('[One-Click Blog] Error scheduling post:', error);
            this.showNotification('Failed to schedule post', 'error');
        }
    }

    // ===== Pipeline Progress Methods =====
    
    async loadPipelineStatus(postId = null) {
        try {
            // Mock data for now - will be replaced with real API call
            const mockData = {
                post_id: 77,
                title: "Welsh Myths and Legends",
                current_stage: "authoring",
                current_substage: "author-first-drafts",
                overall_progress: 67,
                stages: {
                    calendar: {
                        status: "complete",
                        progress: 100,
                        substages: {
                            view: { status: "complete", completed_at: "2025-10-10T10:00:00Z" },
                            ideas: { status: "complete", completed_at: "2025-10-10T10:15:00Z" }
                        }
                    },
                    concept: {
                        status: "complete",
                        progress: 100,
                        substages: {
                            brainstorm: { status: "complete", completed_at: "2025-10-10T11:00:00Z" },
                            "section-structure": { status: "complete", completed_at: "2025-10-10T12:00:00Z" },
                            "topic-allocation": { status: "complete", completed_at: "2025-10-10T13:00:00Z" },
                            titling: { status: "complete", completed_at: "2025-10-10T14:00:00Z" },
                            outline: { status: "complete", completed_at: "2025-10-10T15:00:00Z" }
                        }
                    },
                    authoring: {
                        status: "in_progress",
                        progress: 60,
                        automation_mode: "manual",
                        substages: {
                            "author-first-drafts": { status: "in_progress", progress: 80 },
                            "fix-language": { status: "pending" },
                            "image-concepts": { status: "pending" },
                            "image-prompts": { status: "pending" },
                            "image-captions": { status: "pending" }
                        }
                    },
                    imaging: {
                        status: "pending",
                        progress: 0,
                        automation_mode: "auto",
                        substages: {
                            "image-generation": { status: "pending" },
                            optimise: { status: "pending" }
                        }
                    }
                },
                estimated_completion: "2025-10-12T16:00:00Z",
                last_action_at: "2025-10-10T15:30:00Z",
                error_count: 0
            };
            
            this.updatePipelineDisplay(mockData);
        } catch (error) {
            console.error('[One-Click Blog] Error loading pipeline status:', error);
        }
    }

    updatePipelineDisplay(data) {
        // Update overall progress
        const overallProgressFill = document.querySelector('.pipeline-tracker .progress-fill');
        const overallProgressText = document.querySelector('.pipeline-tracker .progress-text');
        overallProgressFill.style.width = `${data.overall_progress}%`;
        overallProgressText.textContent = `${data.overall_progress}%`;
        
        // Update each stage
        Object.keys(data.stages).forEach(stageKey => {
            const stage = data.stages[stageKey];
            this.updateStageDisplay(stageKey, stage);
        });
        
        // Update summary
        this.updatePipelineSummary(data);
    }

    updateStageDisplay(stageKey, stageData) {
        const stageElement = document.querySelector(`[onclick*="${stageKey}"]`).closest('.stage-accordion');
        
        // Update status
        const statusElement = stageElement.querySelector('.stage-status');
        statusElement.textContent = stageData.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
        statusElement.className = `stage-status ${stageData.status}`;
        
        // Update progress
        const progressFill = stageElement.querySelector('.stage-progress .progress-fill');
        const progressText = stageElement.querySelector('.stage-progress .progress-text');
        progressFill.style.width = `${stageData.progress}%`;
        progressText.textContent = `${stageData.progress}%`;
        
        // Update automation mode buttons
        const manualBtn = stageElement.querySelector('.mode-toggle.manual');
        const autoBtn = stageElement.querySelector('.mode-toggle.auto');
        
        if (stageData.automation_mode === 'manual') {
            manualBtn.classList.add('active');
            autoBtn.classList.remove('active');
        } else {
            autoBtn.classList.add('active');
            manualBtn.classList.remove('active');
        }
        
        // Update substages
        this.updateSubstages(stageKey, stageData.substages);
    }

    updateSubstages(stageKey, substages) {
        const substagesContainer = document.querySelector(`#${stageKey}-content .substages`);
        if (!substagesContainer) return;
        
        substagesContainer.innerHTML = '';
        
        Object.keys(substages).forEach(substageKey => {
            const substage = substages[substageKey];
            const substageElement = document.createElement('div');
            substageElement.className = `substage ${substage.status}`;
            
            let icon = '';
            let content = '';
            
            switch (substage.status) {
                case 'complete':
                    icon = '<i class="fas fa-check-circle"></i>';
                    content = `<span>${substageKey.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>`;
                    if (substage.completed_at) {
                        const completedAt = new Date(substage.completed_at);
                        content += `<span class="completed-at">Completed ${this.formatTimeAgo(completedAt)}</span>`;
                    }
                    break;
                case 'in_progress':
                    icon = '<i class="fas fa-spinner fa-spin"></i>';
                    content = `<span>${substageKey.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>`;
                    if (substage.progress) {
                        content += `
                            <div class="substage-progress">
                                <div class="progress-bar micro">
                                    <div class="progress-fill" style="width: ${substage.progress}%;"></div>
                                </div>
                                <span class="progress-text">${substage.progress}%</span>
                            </div>
                        `;
                    }
                    break;
                case 'pending':
                    icon = '<i class="fas fa-clock"></i>';
                    content = `<span>${substageKey.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>`;
                    content += '<span class="estimated-time">~30 min</span>';
                    break;
            }
            
            substageElement.innerHTML = icon + content;
            substagesContainer.appendChild(substageElement);
        });
    }

    updatePipelineSummary(data) {
        const summaryItems = document.querySelectorAll('.pipeline-summary .summary-item');
        
        // Estimated completion
        const completionDate = new Date(data.estimated_completion);
        summaryItems[0].innerHTML = `
            <i class="fas fa-clock"></i>
            <span>Estimated Completion: <strong>${completionDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}</strong></span>
        `;
        
        // Last action
        const lastActionDate = new Date(data.last_action_at);
        summaryItems[1].innerHTML = `
            <i class="fas fa-history"></i>
            <span>Last Action: <strong>${this.formatTimeAgo(lastActionDate)}</strong></span>
        `;
        
        // Errors
        summaryItems[2].innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>Errors: <strong>${data.error_count}</strong></span>
        `;
    }

    toggleStage(stageKey) {
        const content = document.getElementById(`${stageKey}-content`);
        const chevron = document.getElementById(`${stageKey}-chevron`);
        
        const isVisible = content.style.display !== 'none';
        content.style.display = isVisible ? 'none' : 'block';
        chevron.classList.toggle('open', !isVisible);
    }

    toggleMode(stage, mode) {
        console.log(`[One-Click Blog] Toggling ${stage} to ${mode} mode`);
        
        // Update UI
        const stageElement = document.querySelector(`[onclick*="${stage}"]`).closest('.stage-accordion');
        const manualBtn = stageElement.querySelector('.mode-toggle.manual');
        const autoBtn = stageElement.querySelector('.mode-toggle.auto');
        
        if (mode === 'manual') {
            manualBtn.classList.add('active');
            autoBtn.classList.remove('active');
        } else {
            autoBtn.classList.add('active');
            manualBtn.classList.remove('active');
        }
        
        // Save to settings
        this.settings.defaultAutomationMode[stage] = mode;
        this.saveSettings();
        
        this.showNotification(`${stage} mode set to ${mode}`, 'info');
    }

    reviewStage(stage) {
        console.log(`[One-Click Blog] Opening ${stage} stage for review`);
        // This would open the relevant stage page in a new tab
        const stageUrls = {
            calendar: '/planning/posts/77/calendar/view',
            concept: '/planning/posts/77/concept/brainstorm',
            authoring: '/authoring/posts/77/sections/author-first-drafts',
            imaging: '/imaging/posts/77/sections/image-generation'
        };
        
        if (stageUrls[stage]) {
            window.open(stageUrls[stage], '_blank');
        }
    }

    skipStage(stage) {
        console.log(`[One-Click Blog] Skipping ${stage} stage`);
        this.showNotification(`${stage} stage skipped`, 'warning');
    }

    // ===== Blog Queue Methods =====
    
    async loadBlogQueue(filters = {}) {
        try {
            // Mock data for now - will be replaced with real API call
            const mockData = {
                posts: [
                    {
                        post_id: 77,
                        title: "Welsh Myths and Legends",
                        week_number: 41,
                        week_dates: "Oct 7-13, 2025",
                        status: "in_progress",
                        current_stage: "authoring",
                        current_substage: "author-first-drafts",
                        progress: 67,
                        last_updated: "2025-10-10T15:30:00Z",
                        automation_mode: "manual"
                    },
                    {
                        post_id: 78,
                        title: "Halloween Traditions in Scottish Castles",
                        week_number: 42,
                        week_dates: "Oct 14-20, 2025",
                        status: "pending",
                        current_stage: "calendar",
                        current_substage: "view",
                        progress: 0,
                        last_updated: "2025-10-10T16:00:00Z",
                        automation_mode: "auto"
                    },
                    {
                        post_id: 76,
                        title: "Scottish Highland Wildlife in Autumn",
                        week_number: 40,
                        week_dates: "Sep 30 - Oct 6, 2025",
                        status: "published",
                        current_stage: "published",
                        current_substage: "clan.com",
                        progress: 100,
                        last_updated: "2025-10-07T14:00:00Z",
                        automation_mode: "completed"
                    }
                ],
                pagination: {
                    current_page: 1,
                    total_pages: 3,
                    total_posts: 45,
                    has_next: true,
                    has_prev: false
                }
            };
            
            this.updateBlogQueueDisplay(mockData);
        } catch (error) {
            console.error('[One-Click Blog] Error loading blog queue:', error);
        }
    }

    updateBlogQueueDisplay(data) {
        const queueList = document.querySelector('.queue-list');
        queueList.innerHTML = '';
        
        data.posts.forEach(post => {
            const postCard = this.createPostCard(post);
            queueList.appendChild(postCard);
        });
        
        // Update pagination
        this.updatePagination(data.pagination);
    }

    createPostCard(post) {
        const card = document.createElement('div');
        card.className = 'post-card';
        
        const statusClass = post.status.replace('_', '-');
        const lastUpdated = this.formatTimeAgo(new Date(post.last_updated));
        
        card.innerHTML = `
            <div class="post-header">
                <div class="post-info">
                    <h3>${post.title}</h3>
                    <div class="post-meta">
                        <span class="week-info">Week ${post.week_number} • ${post.week_dates}</span>
                        <span class="post-id">Post #${post.post_id}</span>
                    </div>
                </div>
                <div class="post-status">
                    <span class="status-badge ${statusClass}">${post.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                </div>
            </div>
            
            <div class="post-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${post.progress}%;"></div>
                </div>
                <span class="progress-text">${post.progress}% Complete</span>
            </div>
            
            <div class="post-details">
                <div class="current-stage">
                    <i class="fas fa-${this.getStageIcon(post.current_stage)}"></i>
                    <span>${post.current_stage.charAt(0).toUpperCase() + post.current_stage.slice(1)} • ${post.current_substage.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                </div>
                <div class="last-updated">
                    <i class="fas fa-clock"></i>
                    <span>Updated ${lastUpdated}</span>
                </div>
                <div class="automation-mode">
                    <i class="fas fa-${this.getModeIcon(post.automation_mode)}"></i>
                    <span>${post.automation_mode.charAt(0).toUpperCase() + post.automation_mode.slice(1)} Mode</span>
                </div>
            </div>
            
            <div class="post-actions">
                ${this.createPostActions(post)}
            </div>
        `;
        
        return card;
    }

    createPostActions(post) {
        let actions = `<button class="action-btn view" onclick="oneClickBlogManager.viewPost(${post.post_id})">
            <i class="fas fa-eye"></i> View
        </button>`;
        
        if (post.status === 'in_progress') {
            actions += `
                <button class="action-btn resume" onclick="oneClickBlogManager.resumePost(${post.post_id})">
                    <i class="fas fa-play"></i> Resume
                </button>
                <button class="action-btn pause" onclick="oneClickBlogManager.pausePost(${post.post_id})">
                    <i class="fas fa-pause"></i> Pause
                </button>
            `;
        } else if (post.status === 'pending') {
            actions += `
                <button class="action-btn start" onclick="oneClickBlogManager.startPost(${post.post_id})">
                    <i class="fas fa-play"></i> Start
                </button>
            `;
        } else if (post.status === 'published') {
            actions += `
                <button class="action-btn analytics" onclick="oneClickBlogManager.viewAnalytics(${post.post_id})">
                    <i class="fas fa-chart-line"></i> Analytics
                </button>
            `;
        }
        
        actions += `
            <button class="action-btn delete" onclick="oneClickBlogManager.deletePost(${post.post_id})">
                <i class="fas fa-trash"></i> Delete
            </button>
        `;
        
        return actions;
    }

    getStageIcon(stage) {
        const icons = {
            calendar: 'calendar-alt',
            concept: 'lightbulb',
            authoring: 'pen-nib',
            imaging: 'magic',
            published: 'check-circle'
        };
        return icons[stage] || 'circle';
    }

    getModeIcon(mode) {
        const icons = {
            manual: 'hand-paper',
            auto: 'robot',
            completed: 'check'
        };
        return icons[mode] || 'circle';
    }

    updatePagination(pagination) {
        const paginationInfo = document.querySelector('.pagination-info');
        paginationInfo.textContent = `Page ${pagination.current_page} of ${pagination.total_pages}`;
        
        const prevBtn = document.querySelector('.pagination-btn:first-child');
        const nextBtn = document.querySelector('.pagination-btn:last-child');
        
        prevBtn.disabled = !pagination.has_prev;
        nextBtn.disabled = !pagination.has_next;
    }

    filterQueue(filter) {
        console.log(`[One-Click Blog] Filtering queue by: ${filter}`);
        this.loadBlogQueue({ filter });
    }

    sortQueue(sortBy) {
        console.log(`[One-Click Blog] Sorting queue by: ${sortBy}`);
        this.loadBlogQueue({ sort: sortBy });
    }

    createNewPost() {
        console.log('[One-Click Blog] Creating new post');
        this.showNotification('Opening new post creation...', 'info');
        // This would open the new post creation flow
    }

    viewPost(postId) {
        console.log(`[One-Click Blog] Viewing post ${postId}`);
        // This would open the post in a new tab
        window.open(`/authoring/posts/${postId}/sections/author-first-drafts`, '_blank');
    }

    resumePost(postId) {
        console.log(`[One-Click Blog] Resuming post ${postId}`);
        this.showNotification(`Resuming automation for post ${postId}`, 'info');
    }

    pausePost(postId) {
        console.log(`[One-Click Blog] Pausing post ${postId}`);
        this.showNotification(`Pausing automation for post ${postId}`, 'warning');
    }

    startPost(postId) {
        console.log(`[One-Click Blog] Starting post ${postId}`);
        this.showNotification(`Starting automation for post ${postId}`, 'info');
    }

    deletePost(postId) {
        if (confirm(`Are you sure you want to delete post ${postId}?`)) {
            console.log(`[One-Click Blog] Deleting post ${postId}`);
            this.showNotification(`Post ${postId} deleted`, 'success');
            this.loadBlogQueue(); // Refresh the queue
        }
    }

    viewAnalytics(postId) {
        console.log(`[One-Click Blog] Viewing analytics for post ${postId}`);
        // This would open analytics in a new tab
        window.open(`/analytics/posts/${postId}`, '_blank');
    }

    nextPage() {
        console.log('[One-Click Blog] Loading next page');
        this.loadBlogQueue({ page: 2 });
    }

    // ===== Settings Methods =====
    
    toggleSettings() {
        const content = document.getElementById('settings-content');
        const chevron = document.getElementById('settings-chevron');
        
        const isVisible = content.style.display !== 'none';
        content.style.display = isVisible ? 'none' : 'block';
        chevron.classList.toggle('open', !isVisible);
    }

    loadSettings() {
        const defaultSettings = {
            defaultAutomationMode: {
                calendar: 'auto',
                concept: 'auto',
                authoring: 'manual',
                imaging: 'auto'
            },
            retrySettings: {
                maxRetries: 3,
                retryDelayMinutes: 5,
                exponentialBackoff: true
            },
            publicationTiming: {
                defaultPublishTime: '14:00',
                requireApproval: true,
                autoPublish: false
            },
            notifications: {
                browser: true,
                email: false,
                sound: false
            }
        };
        
        const saved = localStorage.getItem('oneClickBlogSettings');
        return saved ? { ...defaultSettings, ...JSON.parse(saved) } : defaultSettings;
    }

    saveSettings() {
        localStorage.setItem('oneClickBlogSettings', JSON.stringify(this.settings));
        this.showNotification('Settings saved successfully', 'success');
    }

    resetSettings() {
        if (confirm('Are you sure you want to reset all settings to defaults?')) {
            localStorage.removeItem('oneClickBlogSettings');
            this.settings = this.loadSettings();
            this.showNotification('Settings reset to defaults', 'info');
        }
    }

    // ===== Alert Methods =====
    
    async loadAlerts() {
        try {
            // Mock data for now - will be replaced with real API call
            const mockData = {
                alerts: [
                    {
                        id: 1,
                        alert_type: "stuck_post",
                        severity: "warning",
                        post_id: 76,
                        title: "Post #76 Stuck at Image Generation",
                        message: "Failed 3 times - needs manual attention",
                        action_url: "/launchpad/one-click-blog?post=76",
                        action_text: "View Post",
                        created_at: "2025-10-10T14:30:00Z"
                    },
                    {
                        id: 2,
                        alert_type: "ready_publish",
                        severity: "info",
                        post_id: 75,
                        title: "Post #75 Ready for Publication",
                        message: "Scheduled for today at 2:00 PM",
                        action_url: "/launchpad/one-click-blog?post=75&action=publish",
                        action_text: "Publish Now",
                        created_at: "2025-10-10T13:00:00Z"
                    }
                ],
                unread_count: 2
            };
            
            this.alerts = mockData.alerts;
            this.updateAlertBadge(mockData.unread_count);
        } catch (error) {
            console.error('[One-Click Blog] Error loading alerts:', error);
        }
    }

    updateAlertBadge(count) {
        // This would update the header alert badge
        console.log(`[One-Click Blog] Alert count: ${count}`);
    }

    dismissAlert(alertId) {
        console.log(`[One-Click Blog] Dismissing alert ${alertId}`);
        this.alerts = this.alerts.filter(alert => alert.id !== alertId);
        this.showNotification('Alert dismissed', 'info');
    }

    // ===== Utility Methods =====
    
    formatTimeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
        return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    startPolling() {
        // Poll for updates every 30 seconds
        this.pollingInterval = setInterval(() => {
            this.loadPipelineStatus();
            this.loadAlerts();
        }, 30000);
    }

    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    setupEventListeners() {
        // Close modal when clicking outside
        document.addEventListener('click', (e) => {
            const modal = document.getElementById('schedule-modal');
            if (e.target === modal) {
                this.closeScheduleModal();
            }
        });
        
        // Handle keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 's':
                        e.preventDefault();
                        this.saveSettings();
                        break;
                    case 'r':
                        e.preventDefault();
                        this.loadPipelineStatus();
                        break;
                }
            }
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.oneClickBlogManager = new OneClickBlogManager();
});

// Add notification styles
const notificationStyles = `
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    }
    
    .notification-success {
        border-left: 4px solid #10b981;
    }
    
    .notification-error {
        border-left: 4px solid #ef4444;
    }
    
    .notification-warning {
        border-left: 4px solid #f59e0b;
    }
    
    .notification-info {
        border-left: 4px solid #3b82f6;
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 12px;
        color: #e2e8f0;
    }
    
    .notification-content i {
        font-size: 1.125rem;
    }
    
    .notification-success .notification-content i {
        color: #10b981;
    }
    
    .notification-error .notification-content i {
        color: #ef4444;
    }
    
    .notification-warning .notification-content i {
        color: #f59e0b;
    }
    
    .notification-info .notification-content i {
        color: #3b82f6;
    }
    
    .notification-close {
        background: transparent;
        border: none;
        color: #94a3b8;
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        margin-left: auto;
    }
    
    .notification-close:hover {
        background: #334155;
        color: #e2e8f0;
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;

// Add styles to page
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);
