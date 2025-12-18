/**
 * One-Click Publication Main Controller
 * Orchestrates all micro-modules for the One-Click Publication system
 */

class OneClickPublicationController {
    constructor() {
        this.scheduleManager = null;
        this.nextUpPanel = null;
        this.pipelineManager = null;
        this.automationEngine = null;
        this.init();
    }

    init() {
        console.log('[One-Click Publication Controller] Initializing...');
        
        // Initialize micro-modules
        console.log('[One-Click Publication Controller] Creating ScheduleManager...');
        this.scheduleManager = new ScheduleManager();
        console.log('[One-Click Publication Controller] ScheduleManager created:', this.scheduleManager);
        
        console.log('[One-Click Publication Controller] Creating NextUpPanel...');
        this.nextUpPanel = new NextUpPanel();
        console.log('[One-Click Publication Controller] NextUpPanel created:', this.nextUpPanel);
        
        console.log('[One-Click Publication Controller] Creating PipelineManager...');
        // Get initial output channel from URL parameter, selector, or default to 'blog'
        const urlParams = new URLSearchParams(window.location.search);
        const urlOutputChannel = urlParams.get('output') || null;
        const outputChannelSelector = document.getElementById('output-channel-selector');
        let initialChannel = 'blog';
        if (urlOutputChannel) {
            initialChannel = urlOutputChannel.toLowerCase();
            // Set selector to match URL parameter
            if (outputChannelSelector) {
                outputChannelSelector.value = initialChannel;
            }
        } else if (outputChannelSelector) {
            initialChannel = outputChannelSelector.value;
        }
        this.pipelineManager = new PipelineManager(null, initialChannel);
        console.log('[One-Click Publication Controller] PipelineManager created:', this.pipelineManager);
        
        console.log('[One-Click Publication Controller] Creating AutomationEngine...');
        this.automationEngine = new AutomationEngine();
        console.log('[One-Click Publication Controller] AutomationEngine created:', this.automationEngine);
        console.log('[One-Click Publication Controller] AutomationEngine type:', typeof this.automationEngine);
        
        // Set up global event handlers
        console.log('[One-Click Publication Controller] Setting up global handlers...');
        this.setupGlobalHandlers();
        
        // Make modules globally accessible for HTML onclick handlers
        window.nextUpPanel = this.nextUpPanel;
        window.scheduleManager = this.scheduleManager;
        window.pipelineManager = this.pipelineManager;
        window.automationEngine = this.automationEngine;
        
        // Expose test function
        window.testUpdateTimestamps = () => {
            if (this.pipelineManager) {
                this.pipelineManager.testUpdateTimestamps();
            }
        };
        
        // Stub function for loadPipelineForPostType (if called from elsewhere)
        window.loadPipelineForPostType = async (postId, postType) => {
            console.log('[One-Click Publication Controller] loadPipelineForPostType called with:', postId, postType);
            
            // Update substage management link if function exists in template
            if (typeof updateSubstageManagementLink === 'function') {
                updateSubstageManagementLink();
            }
            if (this.pipelineManager && postId) {
                await this.pipelineManager.setPostId(postId);
            }
        };
        
        // Load initial data
        console.log('[One-Click Publication Controller] Loading initial data...');
        this.loadInitialData();
        
        console.log('[One-Click Publication Controller] ✅ Initialized successfully');
        console.log('[One-Click Publication Controller] Global showScheduleModal:', typeof window.showScheduleModal);
    }

    setupGlobalHandlers() {
        // Schedule button handler
        window.showScheduleModal = () => {
            console.log('[One-Click Publication Controller] showScheduleModal() called globally');
            console.log('[One-Click Publication Controller] scheduleManager:', this.scheduleManager);
            if (this.scheduleManager) {
                console.log('[One-Click Publication Controller] Calling scheduleManager.showScheduleModal()');
                this.scheduleManager.showScheduleModal();
            } else {
                console.error('[One-Click Publication Controller] scheduleManager is null!');
            }
        };

        // Schedule modal handlers
        window.closeScheduleModal = () => {
            this.scheduleManager.closeScheduleModal();
        };

        window.schedulePost = () => {
            this.handleSchedulePost();
        };

        // Production button handler
        window.handleProductionAction = () => {
            this.handleProductionAction();
        };
        
        // Automation handlers
        window.executeSubstage = (stage, substage) => {
            this.executeSubstage(stage, substage);
        };
        
        window.toggleAutomationMode = (stage, substage) => {
            this.toggleAutomationMode(stage, substage);
        };
        
        window.openSubstageEdit = (stage, substage) => {
            this.openSubstageEdit(stage, substage);
        };
    }

    async loadInitialData() {
        console.log('[One-Click Publication Controller] Loading initial data...');
        
        try {
            // Get URL parameters
            const urlParams = new URLSearchParams(window.location.search);
            const urlPostId = urlParams.get('post_id');
            const category = urlParams.get('category');
            const itemId = urlParams.get('item_id');
            const year = urlParams.get('year');
            const week = urlParams.get('week');
            const outputChannel = urlParams.get('output') || this.pipelineManager.currentOutputChannel || 'blog';

            if (window.updateOneClickActionRow) {
                window.updateOneClickActionRow({
                    postStatus: urlParams.get('status'),
                    hasPost: !!urlPostId,
                    postId: urlPostId,
                    year,
                    week
                });
            }
            
            // If we have calendar item context but no post_id, load the calendar item
            // We can load by itemId OR by category+year+week (which will resolve the item)
            if (!urlPostId && category && (itemId || (year && week))) {
                console.log('[One-Click Publication Controller] Loading calendar item:', category, itemId || `${year}/${week}`);
                await this.loadCalendarItem(category, itemId, year, week, outputChannel);
                return;
            }
            
            // Load next up data (only if we don't have specific item context)
            if (!category && !itemId) {
                await this.nextUpPanel.loadNextUp();
                await this.scheduleManager.loadCurrentSchedule();
            }
            
            // Update substage management link with initial context (if function exists)
            if (typeof updateSubstageManagementLink === 'function') {
                updateSubstageManagementLink();
            }
            
            // Initialize pipeline with post ID (prioritize URL parameter, then Next Up)
            let postIdToUse = null;
            if (urlPostId) {
                postIdToUse = parseInt(urlPostId);
                console.log('[One-Click Publication Controller] Using post ID from URL:', postIdToUse);
            } else if (!category && !itemId) {
                postIdToUse = this.nextUpPanel.currentPostId;
                if (postIdToUse) {
                    console.log('[One-Click Publication Controller] Using post ID from Next Up panel:', postIdToUse);
                }
            }
            
            if (postIdToUse) {
                console.log('[One-Click Publication Controller] Setting pipeline to post:', postIdToUse);
                await this.pipelineManager.setPostId(postIdToUse, outputChannel);
            } else {
                console.log('[One-Click Publication Controller] No post ID available for pipeline');
            }
            
            console.log('[One-Click Publication Controller] Initial data loaded');
        } catch (error) {
            console.error('[One-Click Publication Controller] Error loading initial data:', error);
        }
    }

    async loadCalendarItem(category, itemId, year, week, outputChannel) {
        try {
            console.log('[One-Click Publication Controller] Loading calendar item:', {category, itemId, year, week, outputChannel});
            
            // Fetch calendar item data from API
            const params = new URLSearchParams();
            params.set('category', category);
            if (itemId) params.set('item_id', itemId);
            if (year) params.set('year', year);
            if (week) params.set('week', week);
            params.set('output', outputChannel);
            
            const response = await fetch(`/launchpad/one-click-publication/api/calendar-item?${params.toString()}`);
            const result = await response.json();
            
            if (result.success) {
                const itemData = result.data;
                
                // Use resolved item_id if we didn't have one
                const resolvedItemId = itemData.item_id || itemId;
                
                // Normalize outputChannel (ensure it's lowercase and valid)
                const normalizedOutputChannel = (outputChannel || 'blog').toLowerCase().trim();
                
                console.log('[One-Click Publication Controller] Calendar item loaded:', {
                    category,
                    itemId: resolvedItemId,
                    postId: itemData.post_id,
                    outputChannel: normalizedOutputChannel,
                    title: itemData.title
                });
                
                // Display item information
                this.displayCalendarItem(itemData, category, resolvedItemId, year, week, normalizedOutputChannel);
                
                // If post_id exists, load pipeline
                if (itemData.post_id) {
                    console.log('[One-Click Publication Controller] Post already exists, loading pipeline for post_id:', itemData.post_id);
                    await this.pipelineManager.setPostId(itemData.post_id, normalizedOutputChannel);
                } else {
                    // Auto-create for blog output to mirror prior workflow; fallback to manual button
                    console.log('[One-Click Publication Controller] No post_id found, checking auto-create conditions...', {
                        outputChannel: normalizedOutputChannel,
                        isBlog: normalizedOutputChannel === 'blog',
                        category,
                        itemId: resolvedItemId
                    });
                    
                    const autoCreateKey = `${category}-${resolvedItemId || ''}-${year || ''}-${week || ''}-${normalizedOutputChannel}`;
                    
                    // Check persistent storage for previous attempts (with expiration)
                    const hasAttempted = this.hasAutoCreateAttempted(autoCreateKey);
                    
                    if (normalizedOutputChannel === 'blog' && !hasAttempted) {
                        console.log('[One-Click Publication Controller] Auto-create conditions met, creating post...');
                        // Mark attempt in persistent storage (5 minute expiration)
                        this.markAutoCreateAttempted(autoCreateKey, 5 * 60 * 1000); // 5 minutes
                        const created = await this.autoCreatePostFromCalendarItem(category, resolvedItemId, year, week, normalizedOutputChannel, itemData);
                        if (created) {
                            // Clear attempt on successful creation (allows retry if needed)
                            this.clearAutoCreateAttempt(autoCreateKey);
                        } else {
                            console.log('[One-Click Publication Controller] Auto-create failed, showing manual button');
                            this.showCreatePostOption(itemData, category, resolvedItemId, year, week, normalizedOutputChannel);
                        }
                    } else {
                        console.log('[One-Click Publication Controller] Auto-create conditions not met, showing manual button', {
                            outputChannel: normalizedOutputChannel,
                            isBlog: normalizedOutputChannel === 'blog',
                            alreadyAttempted: hasAttempted
                        });
                        this.showCreatePostOption(itemData, category, resolvedItemId, year, week, normalizedOutputChannel);
                    }
                }
            } else {
                console.error('[One-Click Publication Controller] Error loading calendar item:', result.error);
                alert(`Error loading item: ${result.error}`);
            }
        } catch (error) {
            console.error('[One-Click Publication Controller] Error loading calendar item:', error);
            alert(`Error loading calendar item: ${error.message}`);
        }
    }

    async autoCreatePostFromCalendarItem(category, itemId, year, week, outputChannel, itemData) {
        try {
            console.log('[One-Click Publication Controller] Auto-creating post from calendar item:', { category, itemId, year, week, outputChannel });
            
            if (!itemId) {
                console.error('[One-Click Publication Controller] Cannot auto-create: missing itemId');
                return false;
            }
            
            const resp = await fetch('/launchpad/one-click-publication/api/create-post-from-item', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    category,
                    item_id: itemId,
                    year,
                    week,
                    output_channel: outputChannel
                })
            });
            
            if (!resp.ok) {
                const errorText = await resp.text();
                console.error('[One-Click Publication Controller] Auto-create HTTP error:', resp.status, errorText);
                return false;
            }
            
            const result = await resp.json();
            console.log('[One-Click Publication Controller] Auto-create response:', result);
            
            if (result.success && result.post_id) {
                if (result.existing) {
                    console.log('[One-Click Publication Controller] Existing post found, reloading with post_id:', result.post_id);
                } else {
                    console.log('[One-Click Publication Controller] Post created successfully, reloading with post_id:', result.post_id);
                }
                // Clear attempt on successful response (whether new or existing)
                const autoCreateKey = `${category}-${itemId || ''}-${year || ''}-${week || ''}-${outputChannel}`;
                this.clearAutoCreateAttempt(autoCreateKey);
                // Reload with post_id so pipeline can load immediately
                const url = new URL(window.location.href);
                url.searchParams.set('post_id', result.post_id);
                url.searchParams.delete('item_id'); // post_id becomes primary
                url.searchParams.delete('category'); // Clean up calendar item params
                url.searchParams.delete('year');
                url.searchParams.delete('week');
                window.location.href = url.toString();
                return true;
            }
            console.warn('[One-Click Publication Controller] Auto-create skipped or failed:', result);
            return false;
        } catch (err) {
            console.error('[One-Click Publication Controller] Error auto-creating post:', err);
            return false;
        }
    }

    /**
     * Check if auto-create has been attempted for this key (with expiration)
     * Uses sessionStorage for per-tab tracking
     * @param {string} key - Unique key for the calendar item
     * @returns {boolean} - True if attempt exists and hasn't expired
     */
    hasAutoCreateAttempted(key) {
        try {
            const storageKey = `autoCreate_${key}`;
            const stored = sessionStorage.getItem(storageKey);
            if (!stored) return false;
            
            const { timestamp, expiresAt } = JSON.parse(stored);
            const now = Date.now();
            
            // Check if expired
            if (now > expiresAt) {
                sessionStorage.removeItem(storageKey);
                return false;
            }
            
            return true;
        } catch (e) {
            console.warn('[One-Click Publication Controller] Error checking auto-create attempt:', e);
            return false;
        }
    }

    /**
     * Mark that auto-create has been attempted for this key
     * @param {string} key - Unique key for the calendar item
     * @param {number} expirationMs - Expiration time in milliseconds (default: 5 minutes)
     */
    markAutoCreateAttempted(key, expirationMs = 5 * 60 * 1000) {
        try {
            const storageKey = `autoCreate_${key}`;
            const now = Date.now();
            const data = {
                timestamp: now,
                expiresAt: now + expirationMs
            };
            sessionStorage.setItem(storageKey, JSON.stringify(data));
        } catch (e) {
            console.warn('[One-Click Publication Controller] Error marking auto-create attempt:', e);
        }
    }

    /**
     * Clear auto-create attempt for this key
     * @param {string} key - Unique key for the calendar item
     */
    clearAutoCreateAttempt(key) {
        try {
            const storageKey = `autoCreate_${key}`;
            sessionStorage.removeItem(storageKey);
        } catch (e) {
            console.warn('[One-Click Publication Controller] Error clearing auto-create attempt:', e);
        }
    }

    displayCalendarItem(itemData, category, itemId, year, week, outputChannel) {
        // Update the selected post title area with calendar item info
        const titleEl = document.getElementById('post-title-text');
        const subtitleEl = document.getElementById('selected-post-subtitle');
        const postTypeBadge = document.getElementById('post-type-badge');
        
        if (titleEl) {
            titleEl.textContent = itemData.title || itemData.idea_title || itemData.theme_title || 'Calendar Item';
        }
        
        if (subtitleEl) {
            const categoryName = category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
            subtitleEl.textContent = `${categoryName} • Week ${week || 'N/A'}, ${year || 'N/A'}`;
        }
        
        // Update post type badge based on category
        if (postTypeBadge) {
            let postType = 'Themed';
            let badgeClass = 'type-themed';
            
            if (category === 'recipe') {
                postType = 'Recipe';
                badgeClass = 'type-recipe';
            } else if (category === 'weekly_word') {
                postType = 'Word of the Day';
                badgeClass = 'type-weekly-word';
            } else if (category === 'weekly_phrase') {
                postType = 'Phrase of the Day';
                badgeClass = 'type-weekly-phrase';
            } else if (category === 'weekly_insult') {
                postType = 'Insult of the Day';
                badgeClass = 'type-weekly-insult';
            } else if (category === 'profile_product' || category === 'profile_surname') {
                postType = 'Profile';
                badgeClass = 'type-profile';
            }
            
            postTypeBadge.textContent = postType;
            postTypeBadge.className = `status-badge ${badgeClass}`;
            postTypeBadge.style.display = 'inline-block';
        }
        
        // Store item context for create post
        this.currentCalendarItem = {
            category,
            itemId,
            year,
            week,
            outputChannel,
            itemData
        };

        if (window.updateOneClickActionRow) {
            window.updateOneClickActionRow({
                postStatus: itemData.post_status,
                hasPost: !!itemData.post_id,
                postId: itemData.post_id,
                year,
                week
            });
        }
    }

    showCreatePostOption(itemData, category, itemId, year, week, outputChannel) {
        // Add a "Create Post" button in the post selector area
        const postSelector = document.getElementById('pipeline-post-selector');
        const selectorControl = postSelector ? postSelector.closest('.selector-control') : null;
        const selectorHeader = postSelector ? postSelector.closest('.selector-header') : null;
        
        // Check if button already exists
        const existingBtn = document.querySelector('.create-post-from-item-btn');
        if (existingBtn) {
            existingBtn.remove(); // Remove old button if it exists
        }
        
        // Create button
        const createBtn = document.createElement('button');
        createBtn.className = 'btn btn-primary create-post-from-item-btn';
        createBtn.innerHTML = '<i class="fas fa-plus" style="margin-right: 6px;"></i>Create Post from Calendar Item';
        createBtn.style.marginTop = '10px';
        createBtn.style.padding = '8px 16px';
        createBtn.style.fontSize = '0.875rem';
        createBtn.onclick = () => this.createPostFromCalendarItem();
        
        // Add button to selector control or header
        if (selectorControl && selectorControl.parentElement) {
            selectorControl.parentElement.appendChild(createBtn);
        } else if (selectorHeader) {
            selectorHeader.appendChild(createBtn);
        } else if (postSelector && postSelector.parentElement) {
            postSelector.parentElement.appendChild(createBtn);
        }
    }

    async createPostFromCalendarItem() {
        if (!this.currentCalendarItem) {
            alert('No calendar item context available');
            return;
        }
        
        const { category, itemId, year, week, outputChannel, itemData } = this.currentCalendarItem;
        
        try {
            const response = await fetch('/launchpad/one-click-publication/api/create-post-from-item', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    category,
                    item_id: itemId,
                    year,
                    week,
                    output_channel: outputChannel
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Reload with the new post_id
                const url = new URL(window.location.href);
                url.searchParams.set('post_id', result.post_id);
                url.searchParams.delete('item_id'); // Keep category for reference but post_id is primary now
                window.location.href = url.toString();
            } else {
                alert(`Error creating post: ${result.error}`);
            }
        } catch (error) {
            console.error('[One-Click Publication Controller] Error creating post:', error);
            alert(`Error creating post: ${error.message}`);
        }
    }

    async handleSchedulePost() {
        const dateInput = document.getElementById('publish-date');
        const timeInput = document.getElementById('publish-time');
        
        if (!dateInput || !timeInput) {
            console.error('[One-Click Publication Controller] Schedule inputs not found');
            return;
        }

        const newDate = dateInput.value;
        const newTime = timeInput.value;
        
        if (!newDate || !newTime) {
            console.error('[One-Click Publication Controller] Missing date or time');
            return;
        }

        console.log('[One-Click Publication Controller] Scheduling post for:', newDate, newTime);
        
        const success = await this.scheduleManager.updateSchedule(newDate, newTime);
        
        if (success) {
            this.showNotification('Schedule updated successfully!', 'success');
        } else {
            this.showNotification('Failed to update schedule', 'error');
        }
    }

    handleProductionAction() {
        const productionBtn = document.querySelector('.production-btn');
        if (!productionBtn) return;
        
        const btnText = productionBtn.querySelector('.btn-text').textContent;
        
        switch (btnText) {
            case 'Start Production':
                this.startProduction();
                break;
            case 'View Progress':
                this.viewProgress();
                break;
            case 'Completed':
                this.viewCompleted();
                break;
        }
    }

    async startProduction() {
        console.log('[One-Click Publication Controller] Starting production...');
        
        // Get the post ID from Next Up panel
        const postId = this.nextUpPanel?.currentPostId;
        if (!postId) {
            this.showNotification('No post available to start production', 'error');
            return;
        }
        
        try {
            // Update button state to show progress
            const productionBtn = document.querySelector('.production-btn');
            if (productionBtn) {
                productionBtn.classList.add('loading');
                const btnText = productionBtn.querySelector('.btn-text');
                const btnIcon = productionBtn.querySelector('i');
                if (btnText) btnText.textContent = 'Loading...';
                if (btnIcon) btnIcon.className = 'fas fa-spinner fa-spin';
            }
            
            // Load pipeline data for this post
            console.log('[One-Click Publication Controller] Loading pipeline data for post:', postId);
            if (this.pipelineManager) {
                await this.pipelineManager.loadPipelineData(postId);
            }
            
            // Scroll to pipeline section
            const pipelineSection = document.querySelector('.pipeline-tracker');
            if (pipelineSection) {
                pipelineSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                
                // Highlight the section briefly
                pipelineSection.style.transition = 'box-shadow 0.3s';
                pipelineSection.style.boxShadow = '0 0 20px rgba(59, 130, 246, 0.5)';
                setTimeout(() => {
                    pipelineSection.style.boxShadow = '';
                }, 2000);
            }
            
            // Update button to "View Progress" state
            if (productionBtn) {
                productionBtn.classList.remove('loading');
                productionBtn.classList.add('progress');
                const btnText = productionBtn.querySelector('.btn-text');
                const btnIcon = productionBtn.querySelector('i');
                if (btnText) btnText.textContent = 'View Progress';
                if (btnIcon) btnIcon.className = 'fas fa-eye';
            }
            
            this.showNotification('Production started! View pipeline progress below.', 'success');
        } catch (error) {
            console.error('[One-Click Publication Controller] Error starting production:', error);
            this.showNotification('Error starting production: ' + error.message, 'error');
            
            // Reset button state
            const productionBtn = document.querySelector('.production-btn');
            if (productionBtn) {
                productionBtn.classList.remove('loading');
                const btnText = productionBtn.querySelector('.btn-text');
                const btnIcon = productionBtn.querySelector('i');
                if (btnText) btnText.textContent = 'Start Production';
                if (btnIcon) btnIcon.className = 'fas fa-rocket';
            }
        }
    }

    viewProgress() {
        console.log('[One-Click Publication Controller] Viewing progress...');
        this.showNotification('Opening progress view...', 'info');
        // This would open a detailed progress modal
    }

    viewCompleted() {
        console.log('[One-Click Publication Controller] Viewing completed post...');
        this.showNotification('Opening completed post...', 'info');
        // This would open the completed post
    }

    showNotification(message, type = 'info') {
        // Simple notification system - could be enhanced
        console.log(`[One-Click Publication Controller] ${type.toUpperCase()}: ${message}`);
        
        // Create a simple notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
            color: white;
            border-radius: 4px;
            z-index: 10000;
            font-size: 14px;
        `;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
    
    /**
     * Execute a substage
     */
    async executeSubstage(stage, substage) {
        console.log(`[One-Click Publication Controller] Executing ${stage}/${substage}`);
        
        if (!this.automationEngine) {
            console.error('[One-Click Publication Controller] AutomationEngine not initialized');
            return;
        }
        
        const postId = this.pipelineManager?.currentPostId || this.nextUpPanel?.currentPostId;
        if (!postId) {
            console.error('[One-Click Publication Controller] No post ID available');
            this.showNotification('No post selected', 'error');
            return;
        }
        
        try {
            this.showNotification(`Running ${substage}...`, 'info');
            
            // Get current output channel
            const outputChannel = this.pipelineManager?.currentOutputChannel || 'blog';
            const selector = document.getElementById('output-channel-selector');
            const channel = selector ? selector.value : outputChannel;
            
            const result = await this.automationEngine.executeSubstage(stage, substage, postId, { output: channel });
            
            if (result.success) {
                this.showNotification(`${substage} completed successfully!`, 'success');
                // Refresh pipeline data immediately
                if (this.pipelineManager) {
                    console.log(`[One-Click Publication Controller] Refreshing pipeline data for post ${postId}`);
                    const outputChannel = this.pipelineManager.currentOutputChannel || 'blog';
                    await this.pipelineManager.loadPipelineData(postId, outputChannel);
                }
            } else {
                this.showNotification(`Failed: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('[One-Click Publication Controller] Error executing substage:', error);
            this.showNotification(`Error: ${error.message}`, 'error');
        }
    }
    
    /**
     * Toggle automation mode for a substage
     */
    async toggleAutomationMode(stage, substage) {
        console.log(`[One-Click Publication Controller] Toggling automation mode for ${stage}/${substage}`);
        console.log('[One-Click Publication Controller] automationEngine:', this.automationEngine);
        console.log('[One-Click Publication Controller] automationEngine type:', typeof this.automationEngine);
        
        if (!this.automationEngine) {
            console.error('[One-Click Publication Controller] AutomationEngine not initialized');
            return;
        }
        
        const currentMode = this.automationEngine.getAutomationMode(stage, substage);
        const modes = ['manual', 'automatic', 'hold'];
        const currentIndex = modes.indexOf(currentMode);
        const nextMode = modes[(currentIndex + 1) % modes.length];
        
        try {
            const success = await this.automationEngine.updateAutomationMode(stage, substage, nextMode);
            
            if (success) {
                this.updateAutomationModeDisplay(stage, substage, nextMode);
                this.showNotification(`${substage} set to ${nextMode}`, 'success');
            } else {
                this.showNotification(`Failed to update ${substage} mode`, 'error');
            }
        } catch (error) {
            console.error('[One-Click Publication Controller] Error toggling automation mode:', error);
            this.showNotification(`Error: ${error.message}`, 'error');
        }
    }
    
    /**
     * Update automation mode display in UI
     */
    updateAutomationModeDisplay(stage, substage, mode) {
        const elementId = `automation-mode-${stage}-${substage}`;
        const element = document.getElementById(elementId);
        
        if (element) {
            element.textContent = this.automationEngine.getModeDisplayText(mode);
            element.className = `automation-mode ${this.automationEngine.getModeCssClass(mode)}`;
        }
    }
    
    /**
     * Open substage edit page
     */
    openSubstageEdit(stage, substage) {
        console.log('[One-Click Publication Controller] openSubstageEdit called with:', stage, substage);
        
        // Try multiple methods to get post ID
        let postId = this.pipelineManager?.currentPostId || this.nextUpPanel?.currentPostId;
        
        // Fallback: try to get from DOM
        if (!postId) {
            const postIdElement = document.querySelector('.post-id-value');
            if (postIdElement && postIdElement.textContent && postIdElement.textContent !== 'Loading...') {
                postId = postIdElement.textContent.trim();
                console.log('[One-Click Publication Controller] Got post ID from DOM:', postId);
            }
        }
        
        // Fallback: try to get from URL or use default
        if (!postId) {
            // Try to extract from current URL if we're on a post-specific page
            const urlMatch = window.location.pathname.match(/\/posts\/(\d+)/);
            if (urlMatch) {
                postId = urlMatch[1];
                console.log('[One-Click Publication Controller] Got post ID from URL:', postId);
            }
        }
        
        // Final fallback: use a default post ID for testing
        if (!postId) {
            postId = '69'; // Default to post 69 for testing
            console.log('[One-Click Publication Controller] Using default post ID:', postId);
        }
        
        console.log('[One-Click Publication Controller] Final postId:', postId);
        
        if (!postId) {
            console.error('[One-Click Publication Controller] No post ID available');
            this.showNotification('No post selected', 'error');
            return;
        }
        
        // Map substages to their edit URLs
        const substageUrls = {
            'planning': {
                'topic_brainstorming': `/planning/posts/${postId}/concept/brainstorm`,
                'section_structure': `/planning/posts/${postId}/concept/section-structure`,
                'topic_allocation': `/planning/posts/${postId}/concept/topic-allocation`,
                'section_titling': `/planning/posts/${postId}/concept/titling`
            },
            'authoring': {
                'author_first_drafts': `/authoring/posts/${postId}/sections/author-first-drafts`,
                'image_concepts': `/authoring/posts/${postId}/sections/image-concepts`,
                'image_prompts': `/authoring/posts/${postId}/sections/image-prompts`
            },
            'imaging': {
                'image_generation': `/imaging/posts/${postId}/sections`,
                'optimize_images': `/imaging/posts/${postId}/optimize`
            }
        };
        
        const url = substageUrls[stage]?.[substage];
        console.log('[One-Click Publication Controller] Generated URL:', url);
        if (url) {
            console.log('[One-Click Publication Controller] Navigating to:', url);
            window.location.href = url;
        } else {
            console.error('[One-Click Publication Controller] Unknown substage:', stage, substage);
            this.showNotification(`Edit page not found for ${substage}`, 'error');
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.oneClickPublicationController = new OneClickPublicationController();
});
