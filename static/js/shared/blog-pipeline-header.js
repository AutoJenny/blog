/**
 * Blog Pipeline Header - Shared functionality for all pages using the header
 * Handles post data loading, navigation highlighting, and header updates
 */

class BlogPipelineHeader {
    constructor() {
        this.postData = null;
        this.linksUpdated = false; // Flag to prevent multiple updates
        this.init();
    }

    init() {
        console.log('[Blog Pipeline Header] Initializing...');
        
        // CRITICAL FIX: Use MutationObserver to catch links when they're added to DOM
        // This ensures we catch links even if they're added dynamically
        const attachWeekParams = () => {
            const navLinks = document.querySelectorAll('.stage-btn, .sub-stage-btn');
            if (navLinks.length > 0) {
                console.log('[Blog Pipeline Header] Links found, attempting to attach week params...');
                this.attachWeekParameterToNavLinks();
            }
        };
        
        // Set up MutationObserver to watch for link additions
        const observer = new MutationObserver((mutations) => {
            attachWeekParams();
        });
        
        const startObserver = () => {
            const headerContainer = document.querySelector('.blog-pipeline-header');
            if (headerContainer) {
                observer.observe(headerContainer, { 
                    childList: true, 
                    subtree: true,
                    attributes: true,
                    attributeFilter: ['href']
                });
                console.log('[Blog Pipeline Header] MutationObserver started');
            } else {
                console.warn('[Blog Pipeline Header] Header container not found for observer');
            }
        };
        
        document.addEventListener('DOMContentLoaded', () => {
            console.log('[Blog Pipeline Header] DOM ready, loading post data...');
            
            // Try to attach immediately
            attachWeekParams();
            
            // Start observer to catch any links added later
            startObserver();
            
            // Also try after a short delay as backup
            setTimeout(attachWeekParams, 200);
            
            this.loadPostData();
        });
        
        // If DOM already loaded when script loads, try immediately
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            attachWeekParams();
            startObserver();
        }

        // Also load when data tab is clicked
        document.addEventListener('click', (event) => {
            if (event.target && event.target.getAttribute('data-tab') === 'data') {
                console.log('[Blog Pipeline Header] Data tab clicked, loading post data...');
                setTimeout(() => this.loadPostData(), 100);
            }
        });

        // Initialize navigation highlighting
        this.updateNavigationHighlighting();
        
        // Also run after a short delay to catch pages that set window.currentStage after DOM ready
        setTimeout(() => {
            this.updateNavigationHighlighting();
            // DO NOT call attachWeekParameterToNavLinks here - it causes race conditions
        }, 100);
        
        // If DOM is already loaded, load post data immediately with a longer delay
        if (document.readyState === 'loading') {
            console.log('[Blog Pipeline Header] DOM still loading, waiting for DOMContentLoaded...');
        } else {
            console.log('[Blog Pipeline Header] DOM already loaded, loading post data with delay...');
            // For week-view pages, wait for loadWeek() to set window.year/weekNumber first
            // Delay updateWeekAndTheme to allow week-view scripts to initialize
            // Check if we're on a week-view page by looking for week-controls element
            const isWeekViewPage = document.querySelector('.week-controls') !== null;
            if (isWeekViewPage) {
                // On week-view pages, wait longer for week-view script to initialize
                setTimeout(() => {
                    this.updateWeekAndTheme();
                }, 300);
            } else {
                // On other pages, wait a bit longer to allow page scripts to set WeekContext
                // Pages with URL params need time for scripts to execute
                setTimeout(() => {
                    // Check if WeekContext has year/week before calling
                    const weekContext = window.WeekContext ? window.WeekContext.getWeekContext() : null;
                    if (weekContext && weekContext.year && weekContext.week) {
                        this.updateWeekAndTheme();
                    } else {
                        // Wait a bit more if WeekContext not ready
                        setTimeout(() => this.updateWeekAndTheme(), 200);
                    }
                    // DO NOT call attachWeekParameterToNavLinks here - it causes race conditions
                }, 300);
            }
            setTimeout(() => this.loadPostData(), 500);
        }
    }

    async loadPostData() {
        try {
            const postId = this.getPostId();
            if (!postId || postId === '0' || parseInt(postId) === 0) {
                console.log('[Blog Pipeline Header] Post ID not found or is 0 (week-based view), skipping post data load');
                return;
            }

            console.log('[Blog Pipeline Header] Loading post data for ID:', postId);
            
            const response = await fetch(`/planning/api/posts/${postId}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.postData = data;
            
            console.log('[Blog Pipeline Header] Post data received:', data);
            this.updateHeaderFields();
            console.log('[Blog Pipeline Header] Post data loaded successfully');
            
        } catch (error) {
            console.error('[Blog Pipeline Header] Error loading post data:', error);
        }
    }

    async updateHeaderFields() {
        // Update week info and theme (works for both post-based and week-based)
        await this.updateWeekAndTheme();
        
        if (!this.postData || !this.postData.post) {
            console.warn('[Blog Pipeline Header] No post data available for update');
            return;
        }

        const post = this.postData.post;
        console.log('[Blog Pipeline Header] Updating header fields with post:', post);
        
        // Update status
        const postStatus = document.getElementById('post-status');
        console.log('[Blog Pipeline Header] post-status element:', postStatus);
        if (postStatus) {
            postStatus.textContent = post.status || 'Unknown';
            console.log('[Blog Pipeline Header] Updated status to:', post.status);
        }

        // Update created date
        const postCreated = document.getElementById('post-created');
        console.log('[Blog Pipeline Header] post-created element:', postCreated);
        if (postCreated) {
            postCreated.textContent = post.created_at ? 
                new Date(post.created_at).toLocaleString() : 'Unknown';
            console.log('[Blog Pipeline Header] Updated created date to:', post.created_at);
        }

        // Update updated date
        const postUpdated = document.getElementById('post-updated');
        console.log('[Blog Pipeline Header] post-updated element:', postUpdated);
        if (postUpdated) {
            postUpdated.textContent = post.updated_at ? 
                new Date(post.updated_at).toLocaleString() : 'Unknown';
            console.log('[Blog Pipeline Header] Updated updated date to:', post.updated_at);
        }

        // Update taxonomy display
        await this.updateTaxonomyDisplay();

        console.log('[Blog Pipeline Header] Header fields updated');
    }

    async updateTaxonomyDisplay() {
        const taxonomyEl = document.getElementById('pipeline-title-taxonomy');
        if (!taxonomyEl) return;

        const postId = this.getPostId();
        if (!postId || postId === '0' || parseInt(postId) === 0) {
            taxonomyEl.textContent = '';
            return;
        }

        // SINGLE SOURCE OF TRUTH: Get viewed week from URL only
        const weekContext = window.WeekContext ? window.WeekContext.getWeekContext() : null;
        let viewedYear, viewedWeek;
        if (weekContext) {
            viewedYear = weekContext.year;
            viewedWeek = weekContext.week;
        }

        try {
            // First check if post's scheduled week matches viewed week
            let weekMismatch = false;
            let targetPostId = postId;
            
            if (viewedYear && viewedWeek) {
                const scheduleResp = await fetch(`/planning/api/posts/${postId}`);
                if (scheduleResp.ok) {
                    const postData = await scheduleResp.json();
                    if (postData.schedule && postData.schedule.year && postData.schedule.week_number) {
                        const scheduledYear = postData.schedule.year;
                        const scheduledWeek = postData.schedule.week_number;
                        if (scheduledYear !== viewedYear || scheduledWeek !== viewedWeek) {
                            weekMismatch = true;
                            
                            // CRITICAL: Find the post that has the viewed week's theme
                            try {
                                // Get the week's schedule to find the theme
                                const weekScheduleResp = await fetch(`/planning/api/calendar/schedule/${viewedYear}/${viewedWeek}`);
                                if (weekScheduleResp.ok) {
                                    const weekScheduleData = await weekScheduleResp.json();
                                    if (weekScheduleData.schedule && Array.isArray(weekScheduleData.schedule)) {
                                        // Find the theme for this week
                                        const weekThemeEntry = weekScheduleData.schedule.find(s => s.idea_id);
                                        
                                        if (weekThemeEntry && weekThemeEntry.idea_id) {
                                            // Find a post that has this theme (any week)
                                            const allSchedulesResp = await fetch(`/planning/api/calendar/schedule/${viewedYear}/${viewedWeek}`);
                                            // Actually, we need to search differently - find posts by theme idea_id
                                            // Let's try to find it from the schedule entries
                                            const postWithTheme = weekScheduleData.schedule.find(s => s.post_id && s.idea_id === weekThemeEntry.idea_id);
                                            
                                            if (postWithTheme && postWithTheme.post_id) {
                                                targetPostId = postWithTheme.post_id;
                                                console.log(`[Blog Pipeline Header] Week mismatch detected. Found post ${targetPostId} with week ${viewedYear}/${viewedWeek} theme`);
                                            } else {
                                                // No post scheduled for this week, but find ANY post with this theme
                                                // Use backend endpoint to find post by theme idea_id
                                                const postByThemeResp = await fetch(`/planning/api/posts/by-theme/${weekThemeEntry.idea_id}`);
                                                if (postByThemeResp.ok) {
                                                    const postByThemeData = await postByThemeResp.json();
                                                    if (postByThemeData.success && postByThemeData.post_id) {
                                                        targetPostId = postByThemeData.post_id;
                                                        console.log(`[Blog Pipeline Header] Found post ${targetPostId} with theme idea_id ${weekThemeEntry.idea_id}`);
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            } catch (e) {
                                console.warn('[Blog Pipeline Header] Error finding post with week theme:', e);
                            }
                        }
                    }
                }
            }

            // Fetch taxonomy for the target post (either original or week's theme post)
            const response = await fetch(`/planning/api/posts/${targetPostId}/taxonomy`);
            if (!response.ok) {
                taxonomyEl.textContent = '';
                return;
            }

            const data = await response.json();
            if (!data.success || !data.taxonomy) {
                taxonomyEl.textContent = '';
                return;
            }

            const taxonomy = data.taxonomy;
            // Display as "Category: Type" where Category is theme_name and Type is content_type_name
            if (taxonomy.theme_name && taxonomy.content_type_name) {
                taxonomyEl.textContent = `${taxonomy.theme_name}: ${taxonomy.content_type_name}`;
            } else {
                taxonomyEl.textContent = '';
            }
        } catch (error) {
            console.warn('[Blog Pipeline Header] Error updating taxonomy display:', error);
            taxonomyEl.textContent = '';
        }
    }

    async updateWeekAndTheme() {
        const prefixEl = document.getElementById('pipeline-title-prefix');
        const weekInfoEl = document.getElementById('pipeline-title-week-info');
        const themeEl = document.getElementById('pipeline-title-theme');
        
        if (!prefixEl || !weekInfoEl || !themeEl) return;
        
        // Determine stage name from current path
        const stageName = this.getStageName();
        if (stageName) {
            prefixEl.textContent = stageName + ': ';
        } else {
            prefixEl.textContent = '';
        }
        
        let year, weekNumber, selectedTheme;
        
        // SINGLE SOURCE OF TRUTH: URL query parameters only
        const weekContext = window.WeekContext ? window.WeekContext.getWeekContext() : null;
        if (weekContext) {
            year = weekContext.year;
            weekNumber = weekContext.week;
        }
        
        console.log('[Blog Pipeline Header] updateWeekAndTheme called. Year:', year, 'Week:', weekNumber, 'WeekContext:', weekContext);
        
        // PRIORITY 2: If we have viewed week, fetch theme for that week (not post schedule)
        if (year && weekNumber) {
            console.log('[Blog Pipeline Header] Fetching theme for year/week:', year, weekNumber);
            // Fetch theme for the currently viewed week
            try {
                const weekResp = await fetch(`/planning/api/calendar/schedule/${year}/${weekNumber}`);
                if (weekResp.ok) {
                    const weekData = await weekResp.json();
                    console.log('[Blog Pipeline Header] Schedule API response:', { selected_theme_id: weekData.selected_theme_id, schedule_length: weekData.schedule?.length });
                    
                    // PRIORITY 1: Check schedule array for theme_selection entries first (most reliable)
                    if (weekData.schedule && Array.isArray(weekData.schedule) && weekData.schedule.length > 0) {
                        const themeSelection = weekData.schedule.find(s => s.type === 'theme_selection');
                        console.log('[Blog Pipeline Header] theme_selection found:', themeSelection);
                        if (themeSelection && themeSelection.theme_title) {
                            selectedTheme = themeSelection.theme_title;
                            console.log('[Blog Pipeline Header] Set selectedTheme from theme_selection:', selectedTheme);
                        }
                    }
                    
                    // PRIORITY 2: Check for selected_theme_id at top level (from cyclic system)
                    if (!selectedTheme && weekData.selected_theme_id) {
                        console.log('[Blog Pipeline Header] Found selected_theme_id:', weekData.selected_theme_id);
                        // Try to find in schedule first
                        const themeEntry = weekData.schedule && Array.isArray(weekData.schedule)
                            ? weekData.schedule.find(s => s.theme_id === weekData.selected_theme_id || s.selected_theme_id === weekData.selected_theme_id)
                            : null;
                        if (themeEntry && themeEntry.theme_title) {
                            selectedTheme = themeEntry.theme_title;
                        } else {
                            // Fallback: fetch theme by ID directly
                            try {
                                const themeResp = await fetch(`/planning/api/calendar/themes/${weekData.selected_theme_id}`);
                                if (themeResp.ok) {
                                    const themeData = await themeResp.json();
                                    const theme = themeData.theme || themeData;
                                    if (theme && theme.theme_title) {
                                        selectedTheme = theme.theme_title;
                                        console.log('[Blog Pipeline Header] Set selectedTheme from API fetch:', selectedTheme);
                                    }
                                }
                            } catch (e) {
                                console.warn('[Blog Pipeline Header] Error fetching theme by selected_theme_id:', e);
                            }
                        }
                    }
                }
                
                // If no theme selected yet, check perpetual themes for this week
                if (!selectedTheme && weekNumber && year) {
                    try {
                        const themesResp = await fetch(`/planning/api/calendar/themes/week/${weekNumber}`);
                        if (themesResp.ok) {
                            const themesData = await themesResp.json();
                            const themes = Array.isArray(themesData.themes) ? themesData.themes : [];
                            
                            if (themes.length > 0) {
                                // Auto-select first theme (already sorted by priority from API)
                                const firstTheme = themes[0];
                                selectedTheme = firstTheme.theme_title;
                            }
                        }
                    } catch (e) {
                        console.warn('[Blog Pipeline Header] Error checking for themes:', e);
                    }
                }
            } catch (e) {
                console.warn('[Blog Pipeline Header] Error fetching theme from week schedule:', e);
            }
        }
        
        // PRIORITY 3: Try to get from post data (post-based) - only if window vars not set
        if (!year && !weekNumber && this.postData && this.postData.schedule) {
            year = this.postData.schedule.year;
            weekNumber = this.postData.schedule.week_number;
            selectedTheme = this.postData.schedule.selected_theme_title;
            
            // CRITICAL: Do NOT fetch ideas and display them as themes! Ideas are NOT themes!
            // If schedule doesn't have theme_id, it simply has no theme - do not fallback to idea_id
            
            // If still no theme and we have week info, check week schedule (ONLY for theme_id, NOT idea_id)
            if (!selectedTheme && year && weekNumber) {
                try {
                    const weekResp = await fetch(`/planning/api/calendar/schedule/${year}/${weekNumber}`);
                    if (weekResp.ok) {
                        const weekData = await weekResp.json();
                        if (weekData.schedule && Array.isArray(weekData.schedule) && weekData.schedule.length > 0) {
                            // CRITICAL: Only check for theme_id - NEVER use idea_id as theme
                            const scheduleWithTheme = weekData.schedule.find(s => s.theme_id || s.calendar_theme_id || s.theme_title);
                            if (scheduleWithTheme && (scheduleWithTheme.theme_id || scheduleWithTheme.calendar_theme_id)) {
                                if (scheduleWithTheme.theme_title) {
                                    selectedTheme = scheduleWithTheme.theme_title;
                                } else {
                                    const themeId = scheduleWithTheme.theme_id || scheduleWithTheme.calendar_theme_id;
                                    try {
                                        const themeResp = await fetch(`/planning/api/calendar/themes/${themeId}`);
                                        if (themeResp.ok) {
                                            const themeData = await themeResp.json();
                                            const theme = themeData.theme || themeData;
                                            if (theme && theme.theme_title) {
                                                selectedTheme = theme.theme_title;
                                            }
                                        }
                                    } catch (e) {
                                        console.warn('[Blog Pipeline Header] Error fetching week theme:', e);
                                    }
                                }
                            }
                            // NOTE: We do NOT check idea_id - ideas are NOT themes!
                        }
                    }
                    
                    // If still no theme selected, auto-select first available theme for this week
                    if (!selectedTheme && weekNumber) {
                        try {
                            const themesResp = await fetch(`/planning/api/calendar/themes/week/${weekNumber}`);
                            if (themesResp.ok) {
                                const themesData = await themesResp.json();
                                const themes = Array.isArray(themesData.themes) ? themesData.themes : [];
                                
                                if (themes.length > 0) {
                                    // Auto-select first theme (already sorted by priority from API)
                                    const firstTheme = themes[0];
                                    selectedTheme = firstTheme.theme_title;
                                    
                                    // Auto-select this theme in the schedule
                                    try {
                                        const selectResp = await fetch('/planning/api/calendar/select-theme', {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({
                                                theme_id: firstTheme.id,
                                                year: year,
                                                week_number: weekNumber
                                            })
                                        });
                                        if (selectResp.ok) {
                                            console.log('[Blog Pipeline Header] Auto-selected theme:', selectedTheme);
                                        }
                                    } catch (e) {
                                        console.warn('[Blog Pipeline Header] Error auto-selecting theme:', e);
                                    }
                                }
                            }
                        } catch (e) {
                            console.warn('[Blog Pipeline Header] Error checking for themes:', e);
                        }
                    }
                } catch (e) {
                    console.warn('[Blog Pipeline Header] Error fetching theme from week schedule:', e);
                }
            }
        } else {
            // Try to get from template variables (week-based or post-based without schedule)
            const postId = this.getPostId();
            // Only fetch post schedule if we don't have window.year/weekNumber (viewed week takes priority)
            if (!year && !weekNumber && postId && postId !== '0' && parseInt(postId) !== 0) {
                // Post-based: fetch schedule - but also check week schedule for theme
                try {
                    const resp = await fetch(`/planning/api/posts/${postId}`);
                    if (resp.ok) {
                        const data = await resp.json();
                        if (data.schedule) {
                            // Only use post schedule if WeekContext wasn't set (viewed week takes priority)
                            // WeekContext from URL parameters takes absolute priority
                            if (!year || !weekNumber) {
                                year = data.schedule.year;
                                weekNumber = data.schedule.week_number;
                            }
                            selectedTheme = data.schedule.selected_theme_title;
                            
                            // If no theme from post schedule but we have week info, check week schedule (ONLY for theme_id)
                            if (!selectedTheme && year && weekNumber) {
                                const weekResp = await fetch(`/planning/api/calendar/schedule/${year}/${weekNumber}`);
                                if (weekResp.ok) {
                                    const weekData = await weekResp.json();
                                    if (weekData.schedule && Array.isArray(weekData.schedule) && weekData.schedule.length > 0) {
                                        // CRITICAL: Only check for theme_id - NEVER use idea_id as theme
                                        const scheduleWithTheme = weekData.schedule.find(s => s.theme_id || s.calendar_theme_id || s.theme_title);
                                        if (scheduleWithTheme && (scheduleWithTheme.theme_id || scheduleWithTheme.calendar_theme_id)) {
                                            if (scheduleWithTheme.theme_title) {
                                                selectedTheme = scheduleWithTheme.theme_title;
                                            } else {
                                                const themeId = scheduleWithTheme.theme_id || scheduleWithTheme.calendar_theme_id;
                                                try {
                                                    const themeResp = await fetch(`/planning/api/calendar/themes/${themeId}`);
                                                    if (themeResp.ok) {
                                                        const themeData = await themeResp.json();
                                                        const theme = themeData.theme || themeData;
                                                        if (theme && theme.theme_title) {
                                                            selectedTheme = theme.theme_title;
                                                        }
                                                    }
                                                } catch (e) {
                                                    console.warn('[Blog Pipeline Header] Error fetching week theme:', e);
                                                }
                                            }
                                        }
                                        // NOTE: We do NOT check idea_id - ideas are NOT themes!
                                    }
                                }
                            }
                        }
                    }
                } catch (e) {
                    console.warn('[Blog Pipeline Header] Error fetching schedule:', e);
                }
            } else {
                // Week-based: get from URL only
                const weekContext = window.WeekContext ? window.WeekContext.getWeekContext() : null;
                if (weekContext) {
                    year = weekContext.year;
                    weekNumber = weekContext.week;
                }
                
                if (year && weekNumber) {
                    // Fetch theme for this week
                    try {
                        const resp = await fetch(`/planning/api/calendar/schedule/${year}/${weekNumber}`);
                        if (resp.ok) {
                            const data = await resp.json();
                            
                            // NEW SYSTEM: Check for selected_theme_id at top level (from cyclic system)
                            if (data.selected_theme_id) {
                                // Find theme entry in schedule array to get title
                                const themeEntry = data.schedule && Array.isArray(data.schedule)
                                    ? data.schedule.find(s => (s.type === 'theme_selection' || s.theme_id === data.selected_theme_id || s.selected_theme_id === data.selected_theme_id))
                                    : null;
                                
                                if (themeEntry && themeEntry.theme_title) {
                                    selectedTheme = themeEntry.theme_title;
                                } else {
                                    // Fallback: fetch theme by ID
                                    try {
                                        const themeResp = await fetch(`/planning/api/calendar/themes/${data.selected_theme_id}`);
                                        if (themeResp.ok) {
                                            const themeData = await themeResp.json();
                                            const theme = themeData.theme || themeData;
                                            if (theme && theme.theme_title) {
                                                selectedTheme = theme.theme_title;
                                            }
                                        }
                                    } catch (e) {
                                        console.warn('[Blog Pipeline Header] Error fetching theme:', e);
                                    }
                                }
                            } else if (data.schedule && Array.isArray(data.schedule) && data.schedule.length > 0) {
                                // Fallback: Check schedule array for theme_selection entries
                                // CRITICAL: Only check for theme_id - NEVER use idea_id as theme
                                const scheduleWithTheme = data.schedule.find(s => 
                                    s.type === 'theme_selection' || 
                                    s.theme_id || 
                                    s.selected_theme_id || 
                                    s.calendar_theme_id || 
                                    s.theme_title
                                );
                                if (scheduleWithTheme && (scheduleWithTheme.theme_id || scheduleWithTheme.selected_theme_id || scheduleWithTheme.calendar_theme_id)) {
                                    if (scheduleWithTheme.theme_title) {
                                        selectedTheme = scheduleWithTheme.theme_title;
                                    } else {
                                        const themeId = scheduleWithTheme.theme_id || scheduleWithTheme.selected_theme_id || scheduleWithTheme.calendar_theme_id;
                                        try {
                                            const themeResp = await fetch(`/planning/api/calendar/themes/${themeId}`);
                                            if (themeResp.ok) {
                                                const themeData = await themeResp.json();
                                                const theme = themeData.theme || themeData;
                                                if (theme && theme.theme_title) {
                                                    selectedTheme = theme.theme_title;
                                                }
                                            }
                                        } catch (e) {
                                            console.warn('[Blog Pipeline Header] Error fetching theme:', e);
                                        }
                                    }
                                }
                                // NOTE: We do NOT check idea_id - ideas are NOT themes!
                            }
                        }
                        
                        // If no theme selected yet, check if themes exist for this week and auto-select first one
                        if (!selectedTheme && weekNumber && year) {
                            try {
                                const themesResp = await fetch(`/planning/api/calendar/themes/week/${weekNumber}`);
                                if (themesResp.ok) {
                                    const themesData = await themesResp.json();
                                    const themes = Array.isArray(themesData.themes) ? themesData.themes : [];
                                    
                                    if (themes.length > 0) {
                                        // Auto-select first theme (already sorted by priority from API)
                                        const firstTheme = themes[0];
                                        selectedTheme = firstTheme.theme_title;
                                        
                                        // Auto-select this theme in the schedule
                                        try {
                                            const selectResp = await fetch('/planning/api/calendar/select-theme', {
                                                method: 'POST',
                                                headers: { 'Content-Type': 'application/json' },
                                                body: JSON.stringify({
                                                    theme_id: firstTheme.id,
                                                    year: year,
                                                    week_number: weekNumber
                                                })
                                            });
                                            if (selectResp.ok) {
                                                console.log('[Blog Pipeline Header] Auto-selected theme:', selectedTheme);
                                                // After auto-selecting, update the display immediately
                                                themeEl.textContent = selectedTheme;
                                            }
                                        } catch (e) {
                                            console.warn('[Blog Pipeline Header] Error auto-selecting theme:', e);
                                        }
                                    }
                                }
                            } catch (e) {
                                console.warn('[Blog Pipeline Header] Error checking for themes:', e);
                            }
                        }
                    } catch (e) {
                        console.warn('[Blog Pipeline Header] Error fetching theme:', e);
                    }
                }
            }
        }
        
        // Update week info
        if (year && weekNumber) {
            // Calculate date span for the week
            const weekStart = this.getWeekStartDate(year, weekNumber);
            const weekEnd = new Date(weekStart);
            weekEnd.setUTCDate(weekEnd.getUTCDate() + 6);
            
            const startStr = this.formatDate(weekStart);
            const endStr = this.formatDate(weekEnd);
            weekInfoEl.textContent = `${startStr} – ${endStr}, Week ${weekNumber}`;
        } else {
            weekInfoEl.textContent = '';
        }
        
        // CRITICAL: In calendar week-view, calendar is WEEK-CENTRIC, not post-centric
        // The post_id is only for navigation through pipeline stages, NOT for displaying post data
        // We should NOT fetch or display any post information in calendar week view
        const isCalendarWeekView = this.isCalendarWeekViewContext();
        if (isCalendarWeekView) {
            // In calendar week view, don't fetch post data or override template defaults
            // The template already shows "Profile" or "Recipe" - leave it as is
            // Just continue to theme lookup for themed posts
            // (Profile/Recipe posts will have already been handled by template, so theme lookup won't run)
        } else {
            // In other contexts (planning, authoring, etc.), fetch and display post data
            const postId = this.getPostId();
            if (postId && postId !== '0' && parseInt(postId) !== 0) {
                try {
                    // Check post type from API
                    const postTypeResp = await fetch(`/api/post-type-pipeline/posts/${postId}/pipeline`);
                    if (postTypeResp.ok) {
                        const postTypeData = await postTypeResp.json();
                        if (postTypeData.success && postTypeData.post_type === 'recipe') {
                            // For recipe posts, show the recipe title instead of theme
                            const recipeTitle = postTypeData.post_title || 'Recipe';
                            if (themeEl) {
                                themeEl.textContent = recipeTitle;
                            }
                            return; // Don't continue with theme lookup
                        }
                        if (postTypeData.success && postTypeData.post_type === 'profile') {
                            // For profile posts, show the profile title instead of theme
                            const profileTitle = postTypeData.post_title || 'Profile';
                            if (themeEl) {
                                themeEl.textContent = profileTitle;
                            }
                            return; // Don't continue with theme lookup
                        }
                        if (postTypeData.success && postTypeData.post_type === 'generated') {
                            // For generated posts with "Products & Producers" content type, show post title instead of theme
                            if (postTypeData.content_type_slug === 'products-producers') {
                                const generatedTitle = postTypeData.post_title || 'Generated Post';
                                if (themeEl) {
                                    themeEl.textContent = generatedTitle;
                                }
                                return; // Don't continue with theme lookup
                            }
                            // For other generated posts, fall through to theme lookup
                        }
                    }
                } catch (e) {
                    console.warn('[Blog Pipeline Header] Error checking post type:', e);
                }
            }
        }
        
        // Update theme
        if (selectedTheme) {
            themeEl.textContent = selectedTheme;
            console.log('[Blog Pipeline Header] Theme updated to:', selectedTheme);
        } else {
            themeEl.textContent = 'Unselected theme';
            console.warn('[Blog Pipeline Header] No theme found. Year:', year, 'Week:', weekNumber);
        }
    }

    getStageName() {
        // No prefix needed - just show week info and theme
        return '';
    }
    
    attachWeekParameterToNavLinks() {
        // SINGLE SOURCE OF TRUTH: Read ONLY from URL query parameters
        const weekContext = window.WeekContext ? window.WeekContext.getWeekContext() : null;
        
        // If URL has no week params, don't modify links
        if (!weekContext) {
            console.log('[Blog Pipeline Header] No week params in URL, skipping link update');
            return;
        }
        
        const year = weekContext.year;
        const weekNumber = weekContext.week;
        const currentUrl = window.location.href;
        
        // Check if links exist - if not, this function was called too early
        const navLinks = document.querySelectorAll('.stage-btn, .sub-stage-btn');
        if (navLinks.length === 0) {
            console.log('[Blog Pipeline Header] No nav links found yet, cannot attach week params');
            return;
        }
        
        // CRITICAL: Clear the flag if URL week/year has changed
        // This ensures we update links when week changes
        const lastUpdatedUrl = sessionStorage.getItem('lastNavLinksUrl');
        if (lastUpdatedUrl && lastUpdatedUrl !== currentUrl) {
            console.log('[Blog Pipeline Header] URL changed, clearing update flag');
            this.linksUpdated = false;
            // Clear old cache entries
            for (let i = 0; i < sessionStorage.length; i++) {
                const key = sessionStorage.key(i);
                if (key && key.startsWith('navLinksUpdated_')) {
                    sessionStorage.removeItem(key);
                }
            }
        }
        
        // Check if we've already updated links for THIS exact URL
        // This prevents redundant updates but allows updates when URL changes
        if (this.linksUpdated && lastUpdatedUrl === currentUrl) {
            console.log('[Blog Pipeline Header] Links already updated for this URL, skipping');
            return;
        }
        
        console.log(`[Blog Pipeline Header] Attaching week params: year=${year}, week=${weekNumber} to ${navLinks.length} links (URL: ${currentUrl})`);
        
        // Get valid post_id (handle post_id=0 by using saved post)
        const currentPostId = this.getPostId();
        let validPostId = currentPostId;
        
        if (!validPostId || validPostId === '0' || parseInt(validPostId) === 0) {
            // Try localStorage for post_id (don't fetch async - that causes race conditions)
            const savedPostId = localStorage.getItem('blogForgeSelectedPostId');
            if (savedPostId && parseInt(savedPostId) > 0) {
                validPostId = savedPostId;
                console.log(`[Blog Pipeline Header] Using saved post_id from localStorage: ${validPostId}`);
            }
            // NOTE: We DON'T do async fetch here - it causes race conditions
            // If post_id=0, just leave it as 0 in the links
        }
        
        // Attach week/year params to ALL navigation links immediately and synchronously
        let updatedCount = 0;
        navLinks.forEach(link => {
            let href = link.getAttribute('href');
            if (!href) {
                console.log('[Blog Pipeline Header] Link has no href, skipping:', link);
                return;
            }
            
            const originalHref = href;
            
            // Replace post_id=0 with valid post_id if we have one
            if (validPostId && validPostId !== '0' && parseInt(validPostId) !== 0) {
                href = href.replace(/\/posts\/0\//g, `/posts/${validPostId}/`);
            }
            
            // Use WeekContext helper to attach week params
            const newHref = window.WeekContext 
                ? window.WeekContext.attachWeekToUrl(href, year, weekNumber)
                : href;
            
            link.setAttribute('href', newHref);
            
            if (originalHref !== newHref) {
                updatedCount++;
                console.log(`[Blog Pipeline Header] Updated link: ${originalHref} -> ${newHref}`);
            }
        });
        
        // Mark as updated for this URL
        sessionStorage.setItem('lastNavLinksUrl', currentUrl);
        this.linksUpdated = true;
        
        console.log(`[Blog Pipeline Header] Updated ${updatedCount} of ${navLinks.length} links`);
    }
    
    updateNavLinksWithPostId(postId, year, weekNumber) {
        // Update all navigation links with the found post_id and week params
        const navLinks = document.querySelectorAll('.stage-btn, .sub-stage-btn');
        navLinks.forEach(link => {
            let href = link.getAttribute('href');
            if (!href) return;
            
            // Replace any post_id with the found one
            href = href.replace(/\/posts\/\d+\//g, `/posts/${postId}/`);
            
            // Add/update query parameters
            const url = new URL(href, window.location.origin);
            url.searchParams.set('year', year);
            url.searchParams.set('week', weekNumber);
            link.setAttribute('href', url.pathname + url.search);
        });
    }

    getWeekStartDate(year, weekNumber) {
        const simple = new Date(Date.UTC(year, 0, 4 + (weekNumber - 1) * 7));
        const dow = (simple.getUTCDay() + 6) % 7;
        simple.setUTCDate(simple.getUTCDate() - dow);
        return simple; // Monday
    }

    formatDate(d) {
        return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    }

    getPostId() {
        console.log('[Blog Pipeline Header] Getting post ID...');
        
        // Try to get post ID from various sources
        const urlMatch = window.location.pathname.match(/\/posts\/(\d+)/);
        console.log('[Blog Pipeline Header] URL match:', urlMatch);
        if (urlMatch) {
            console.log('[Blog Pipeline Header] Found post ID from URL:', urlMatch[1]);
            return urlMatch[1];
        }

        if (window.postId) {
            console.log('[Blog Pipeline Header] Found post ID from window.postId:', window.postId);
            return window.postId;
        }

        // Try to get from data attributes
        const postIdElement = document.querySelector('[data-post-id]');
        console.log('[Blog Pipeline Header] Post ID element:', postIdElement);
        if (postIdElement) {
            const postId = postIdElement.getAttribute('data-post-id');
            console.log('[Blog Pipeline Header] Found post ID from data attribute:', postId);
            return postId;
        }

        console.warn('[Blog Pipeline Header] No post ID found');
        return null;
    }

    updateNavigationHighlighting() {
        // Get current stage and substage
        const currentStage = window.currentStage || this.getCurrentStageFromURL();
        const currentSubstage = window.currentSubstage || this.getCurrentSubstageFromURL();

        console.log('[Blog Pipeline Header] Current stage:', currentStage, 'substage:', currentSubstage);

        // Update main stage buttons
        const stageButtons = document.querySelectorAll('.stage-btn');
        stageButtons.forEach(button => {
            const stage = button.getAttribute('data-stage');
            if (stage === currentStage) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });

        // Update sub-stage buttons
        const subStageButtons = document.querySelectorAll('.sub-stage-btn');
        subStageButtons.forEach(button => {
            const substage = button.getAttribute('data-substage');
            if (substage === currentSubstage) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });

        // Update subtitle
        this.updateSubtitle(currentStage, currentSubstage);
    }

    getCurrentStageFromURL() {
        const path = window.location.pathname;
        if (path.includes('/planning/')) return 'concept';
        if (path.includes('/authoring/')) return 'authoring';
        if (path.includes('/imaging/')) return 'imaging';
        if (path.includes('/header/')) return 'header';
        return null;
    }

    isCalendarWeekViewContext() {
        // Check if we're in a calendar week-view context
        // This can be determined by:
        // 1. URL path contains '/calendar/week-view'
        // 2. window.currentSubstage is 'week-view' and window.currentStage is 'calendar'
        // 3. Presence of week-view specific elements
        
        const path = window.location.pathname;
        const isWeekViewPath = path.includes('/calendar/week-view');
        
        const currentStage = window.currentStage;
        const currentSubstage = window.currentSubstage;
        const isWeekViewSubstage = currentStage === 'calendar' && currentSubstage === 'week-view';
        
        // Check for week-view specific elements
        const hasWeekControls = document.querySelector('.week-controls') !== null;
        const hasWeekViewContainer = document.querySelector('.calendar-week-view') !== null;
        
        return isWeekViewPath || (isWeekViewSubstage && (hasWeekControls || hasWeekViewContainer));
    }

    getCurrentSubstageFromURL() {
        const path = window.location.pathname;
        if (path.includes('/calendar')) return 'calendar';
        if (path.includes('/concept')) return 'concept';
        if (path.includes('/author-first-drafts')) return 'author-first-drafts';
        if (path.includes('/fix_language')) return 'fix-language';
        if (path.includes('/image_concepts')) return 'image-concepts';
        if (path.includes('/image_prompts')) return 'image-prompts';
        if (path.includes('/image_captions')) return 'image-captions';
        if (path.includes('/image-generation')) return 'image-generation';
        if (path.includes('/photo-selection')) return 'photo-selection';
        if (path.includes('/title-summary')) return 'title-summary';
        if (path.includes('/header-image')) return 'header-image';
        if (path.includes('/seo-meta')) return 'seo-meta';
        if (path.includes('/product-match')) return 'product-match';
        if (path.includes('/publishing-details')) return 'publishing-details';
        if (path.includes('/final-review')) return 'final-review';
        return null;
    }

    updateSubtitle(currentStage, currentSubstage) {
        const subtitles = {
            'calendar': {
                'view': 'Weekly view of your content schedule - 52 weeks organized by month',
                'ideas': 'AI-powered suggestions based on seasons, trends, and content gaps.'
            },
            'concept': {
                'brainstorm': 'Generate 50+ topic ideas and curate the best ones for your content.',
                'grouping': 'Group your generated topics into 6-8 thematic clusters for logical organization.',
                'titling': 'Create compelling titles and descriptions for each section, defining scope and boundaries.',
                'outline': 'Create a detailed content outline with logical flow and structure.'
            },
            'authoring': {
                'author-first-drafts': 'Create initial draft content for each section.',
                'fix-language': 'Refine and improve language, flow, and readability.',
                'image-concepts': 'Develop visual concepts and image requirements.',
                'image-prompts': 'Generate detailed prompts for AI image creation.',
                'image-captions': 'Create engaging captions and alt text for images.'
            },
            'imaging': {
                'image-generation': 'Generate high-quality images using AI based on your prompts.',
                'photo-selection': 'Search and select photos from Pexels and Unsplash for your sections.',
                'optimise': 'Resize, compress, and watermark images generated in the prior step.'
            },
            'header': {
                'title-summary': 'Generate post title, subtitle, slug, and summary blurb.',
                'header-image': 'Create header image with caption and alt text.',
                'seo-meta': 'Generate SEO metadata including meta title, description, and tags.',
                'product-match': 'Select matching products and categories based on vector similarity.',
                'publishing-details': 'Set author, word count, publish date, and status.',
                'final-review': 'Review and finalize all header elements before publishing.'
            }
        };

        const subtitleElement = document.getElementById('subtitle');
        if (subtitleElement && currentStage && currentSubstage) {
            const subtitle = subtitles[currentStage]?.[currentSubstage];
            if (subtitle) {
                subtitleElement.textContent = subtitle;
            }
        }
    }
}

// Initialize the header when the script loads
console.log('[Blog Pipeline Header] Script loaded, creating instance...');
const blogPipelineHeader = new BlogPipelineHeader();
console.log('[Blog Pipeline Header] Instance created:', blogPipelineHeader);
