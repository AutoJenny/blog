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
            
            // Update preview link with correct post ID
            this.updatePreviewLink(postId);
            
            this.updateHeaderFields();
            console.log('[Blog Pipeline Header] Post data loaded successfully');
            
        } catch (error) {
            console.error('[Blog Pipeline Header] Error loading post data:', error);
        }
    }

    async updateHeaderFields() {
        // Update week info and theme (works for both post-based and week-based)
        await this.updateWeekAndTheme();
        
        // For recipe posts, also update recipe title
        const recipeEl = document.getElementById('pipeline-title-recipe');
        if (recipeEl) {
            this.updateRecipeTitle();
        }
        
        if (!this.postData || !this.postData.post) {
            console.warn('[Blog Pipeline Header] No post data available for update');
            return;
        }

        const post = this.postData.post;
        console.log('[Blog Pipeline Header] Updating header fields with post:', post);
        
        // Update status - show exactly what's in the database
        const postStatus = document.getElementById('post-status');
        if (postStatus) {
            postStatus.textContent = post.status || 'Unknown';
        }

        // Update created date - format as DD/MM/YYYY, HH:MM:SS
        const postCreated = document.getElementById('post-created');
        if (postCreated) {
            if (post.created_at) {
                const date = new Date(post.created_at);
                const day = String(date.getDate()).padStart(2, '0');
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const year = date.getFullYear();
                const hours = String(date.getHours()).padStart(2, '0');
                const minutes = String(date.getMinutes()).padStart(2, '0');
                const seconds = String(date.getSeconds()).padStart(2, '0');
                postCreated.textContent = `${day}/${month}/${year}, ${hours}:${minutes}:${seconds}`;
            } else {
                postCreated.textContent = 'Unknown';
            }
        }

        // Update updated date - format as DD/MM/YYYY, HH:MM:SS
        const postUpdated = document.getElementById('post-updated');
        if (postUpdated) {
            if (post.updated_at) {
                const date = new Date(post.updated_at);
                const day = String(date.getDate()).padStart(2, '0');
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const year = date.getFullYear();
                const hours = String(date.getHours()).padStart(2, '0');
                const minutes = String(date.getMinutes()).padStart(2, '0');
                const seconds = String(date.getSeconds()).padStart(2, '0');
                postUpdated.textContent = `${day}/${month}/${year}, ${hours}:${minutes}:${seconds}`;
            } else {
                postUpdated.textContent = 'Unknown';
            }
        }

        // Update taxonomy display
        await this.updateTaxonomyDisplay();

        // Instruction Set 8: Early stage indicator (from DB)
        await this.updateEarlyStageIndicator();
        // W2 Phase 3: Playbook panel (metadata-only; does not affect stage or automation)
        await this.updatePlaybookPanel();
        // W2 N2: Pipeline strip (Current / Next / Jump) from pipeline-state API
        await this.updatePipelineStrip();

        console.log('[Blog Pipeline Header] Header fields updated');
    }

    /**
     * W2 N2: Fetch pipeline-state and render Current / Next / Jump. Navigation only; no auto-execute.
     */
    async updatePipelineStrip() {
        const strip = document.getElementById('pipeline-nav-strip');
        const postId = this.getPostId();
        if (!strip || !postId || postId === '0' || parseInt(postId) === 0) return;
        try {
            const response = await fetch(`/api/posts/${postId}/pipeline-state`);
            if (!response.ok) return;
            const data = await response.json();
            if (!data.success || !data.substages) return;
            this.renderPipelineStrip(data);
        } catch (e) {
            console.warn('[Blog Pipeline Header] Pipeline strip fetch failed:', e);
        }
    }

    /**
     * Render Current, Next button, and Jump dropdown from pipeline-state payload.
     */
    renderPipelineStrip(data) {
        const strip = document.getElementById('pipeline-nav-strip');
        const currentEl = document.getElementById('pipeline-current');
        const nextBtn = document.getElementById('pipeline-next-btn');
        const jumpMenu = document.getElementById('pipeline-jump-menu');
        const jumpToggle = document.querySelector('.pipeline-jump-toggle');
        if (!strip || !currentEl || !nextBtn || !jumpMenu) return;

        const substages = data.substages || [];
        const reasons = data.reasons_blocked || {};
        const current = data.current || null;
        const next = data.next || null;

        const stageTitle = (s) => s ? s.charAt(0).toUpperCase() + s.slice(1) : '';
        const findSubstage = (stage, substage) => substages.find(s => s.stage === stage && s.substage === substage);

        // 1) Current
        if (current) {
            const sub = findSubstage(current.stage, current.substage);
            const label = sub ? sub.label : current.substage;
            currentEl.textContent = `Current: ${stageTitle(current.stage)} → ${label}`;
        } else {
            currentEl.textContent = 'Current: (stage complete)';
        }

        // 2) Next button
        if (!next) {
            nextBtn.style.display = 'none';
        } else {
            nextBtn.style.display = '';
            const sub = findSubstage(next.stage, next.substage);
            const label = sub ? sub.label : next.substage;
            const nextKey = `${next.stage}.${next.substage}`;
            const blockedReason = reasons[nextKey];
            nextBtn.textContent = `Next: ${stageTitle(next.stage)} → ${label}`;
            nextBtn.disabled = !!blockedReason;
            nextBtn.title = blockedReason || '';
            nextBtn.onclick = () => {
                if (nextBtn.disabled) return;
                const navSub = findSubstage(next.stage, next.substage);
                if (!navSub || !navSub.nav_url) return;
                let url = navSub.nav_url;
                const weekContext = window.WeekContext ? window.WeekContext.getWeekContext() : null;
                if (weekContext && weekContext.year && weekContext.week) {
                    url = url.includes('?') ? `${url}&year=${weekContext.year}&week=${weekContext.week}` : `${url}?year=${weekContext.year}&week=${weekContext.week}`;
                }
                window.location.href = url;
            };
        }

        // 3) Jump dropdown: list all substages, disabled when !can_execute, tooltip = reasons_blocked
        jumpMenu.innerHTML = '';
        substages.forEach(s => {
            const key = `${s.stage}.${s.substage}`;
            const isCurrent = current && current.stage === s.stage && current.substage === s.substage;
            const item = document.createElement('button');
            item.type = 'button';
            item.role = 'menuitem';
            item.className = 'pipeline-jump-item' + (isCurrent ? ' pipeline-jump-item-current' : '') + (!s.can_execute ? ' pipeline-jump-item-disabled' : '');
            item.textContent = `${stageTitle(s.stage)} → ${s.label}`;
            item.disabled = !s.can_execute;
            item.title = !s.can_execute && reasons[key] ? reasons[key] : '';
            item.addEventListener('click', () => {
                if (!s.can_execute) return;
                let url = s.nav_url;
                const weekContext = window.WeekContext ? window.WeekContext.getWeekContext() : null;
                if (weekContext && weekContext.year && weekContext.week) {
                    url = url.includes('?') ? `${url}&year=${weekContext.year}&week=${weekContext.week}` : `${url}?year=${weekContext.year}&week=${weekContext.week}`;
                }
                window.location.href = url;
            });
            jumpMenu.appendChild(item);
        });

        // Jump toggle: show/hide menu; close on outside click
        if (jumpToggle) {
            const closeMenu = () => {
                jumpMenu.classList.remove('pipeline-jump-menu-open');
                jumpToggle.setAttribute('aria-expanded', 'false');
                document.removeEventListener('click', closeMenu);
            };
            jumpToggle.onclick = (e) => {
                e.stopPropagation();
                const open = jumpMenu.classList.toggle('pipeline-jump-menu-open');
                jumpToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
                if (open) setTimeout(() => document.addEventListener('click', closeMenu), 0);
                else document.removeEventListener('click', closeMenu);
            };
        }

        // Expose pipeline-state globally for other pages (e.g. Ideas panel).
        // UI-only: does not auto-run, only shares state.
        window.BlogPipelineState = data;
        try {
            document.dispatchEvent(new CustomEvent('blog-pipeline-state-ready', { detail: data }));
        } catch (e) {
            // CustomEvent may not be supported in very old browsers; ignore
        }

        strip.style.display = 'flex';
        this.updateViewingLine(data);
    }

    /**
     * W2 Option B: Derive viewing context from current URL for the Viewing line.
     * Returns { label: "Planning → Ideas", stage: "ideas" } for mismatch check.
     */
    getViewingContextFromPath() {
        const path = window.location.pathname || '';
        // Post calendar routes: /planning/posts/<id>/calendar/<segment>
        const calendarMatch = path.match(/\/calendar\/([^/]+)/);
        if (calendarMatch) {
            const seg = calendarMatch[1];
            if (seg === 'ideas') return { label: 'Planning → Ideas', stage: 'ideas' };
            if (seg === 'structure') return { label: 'Planning → Structure', stage: 'structure' };
            if (seg === 'titling') return { label: 'Planning → Titling', stage: 'titling' };
            if (seg === 'metadata') return { label: 'Planning → Metadata', stage: 'metadata' };
            if (seg === 'authoring') return { label: 'Authoring', stage: 'authoring' };
            if (seg === 'imaging') return { label: 'Imaging', stage: 'imaging' };
            if (seg === 'review') return { label: 'Review', stage: 'review' };
        }
        // Concept routes: /planning/posts/<id>/concept/<segment>
        const conceptMatch = path.match(/\/concept\/([^/]+)/);
        if (conceptMatch) {
            const seg = conceptMatch[1];
            if (seg === 'brainstorm') return { label: 'Planning → Topic Brainstorming', stage: 'structure' };
            if (seg === 'section-structure' || seg === 'section_structure') return { label: 'Planning → Section Structure', stage: 'structure' };
            if (seg === 'topic-allocation' || seg === 'topic_allocation') return { label: 'Planning → Section Ideas', stage: 'structure' };
            if (seg === 'titling') return { label: 'Planning → Section Titling', stage: 'structure' };
        }
        // Authoring, imaging, header routes
        if (path.includes('/authoring/')) return { label: 'Authoring', stage: 'authoring' };
        if (path.includes('/imaging/')) return { label: 'Imaging', stage: 'imaging' };
        if (path.includes('/header/') || path.includes('title-summary') || path.includes('seo-meta') || path.includes('header-image')) return { label: 'Review', stage: 'review' };
        return { label: '(unknown)', stage: null };
    }

    /**
     * W2 Option B: Update the Viewing line. If viewing context ≠ pipeline current stage, show both.
     */
    updateViewingLine(data) {
        const el = document.getElementById('pipeline-viewing-line');
        if (!el) return;
        const viewing = this.getViewingContextFromPath();
        if (!viewing.label) {
            el.textContent = '';
            el.style.display = 'none';
            return;
        }
        const current = data && data.current || null;
        const substages = (data && data.substages) || [];
        const stageTitle = (s) => s ? s.charAt(0).toUpperCase() + s.slice(1) : '';
        const findSubstage = (stage, substage) => substages.find(s => s.stage === stage && s.substage === substage);

        const cursorStage = current ? current.stage : null;
        const viewingStage = viewing.stage;
        const mismatch = cursorStage && viewingStage && cursorStage !== viewingStage;

        let html = '';
        const displayViewing = viewing.label === '(unknown)' ? 'Viewing: (unknown)' : `Viewing: ${viewing.label}`;
        if (mismatch && current) {
            const sub = findSubstage(current.stage, current.substage);
            const label = sub ? sub.label : current.substage;
            html = `Pipeline cursor: ${stageTitle(current.stage)} → ${label}<br>${displayViewing}`;
        } else {
            html = displayViewing;
        }
        el.innerHTML = html;
        el.style.display = '';
    }

    async updateEarlyStageIndicator() {
        const el = document.getElementById('early-stage-value');
        const line = document.getElementById('early-stage-line');
        if (!el || !line) return;
        const postId = this.getPostId();
        if (!postId || postId === '0' || parseInt(postId) === 0) {
            line.style.display = 'none';
            return;
        }
        try {
            const res = await fetch(`/api/posts/${postId}/early-stage`);
            const data = await res.json();
            if (!data.success) {
                el.textContent = '—';
                return;
            }
            const stage = (data.workflow_stage || 'metadata').toUpperCase();
            const ideasCount = data.required_ideas_count ?? 0;
            const sectionsCount = data.sections_count ?? 0;
            if (stage === 'IDEAS') {
                el.textContent = `IDEAS (${ideasCount}/3 min)`;
            } else if (stage === 'STRUCTURE') {
                el.textContent = `STRUCTURE (${sectionsCount} sections)`;
            } else {
                el.textContent = stage;
            }
            line.style.display = '';
        } catch (e) {
            el.textContent = '—';
        }
    }

    /** W2 Phase 3: Show playbook tasks for current stage only. Does not gate; does not auto-run. */
    async updatePlaybookPanel() {
        const panel = document.getElementById('playbook-panel');
        const listEl = document.getElementById('playbook-tasks');
        if (!panel || !listEl) return;
        const postId = this.getPostId();
        if (!postId || postId === '0' || parseInt(postId) === 0) {
            panel.style.display = 'none';
            return;
        }
        const stagesWithPlaybook = ['ideas', 'authoring', 'review'];
        try {
            const [stageRes, playbookRes] = await Promise.all([
                fetch(`/api/posts/${postId}/early-stage`),
                fetch(`/api/posts/${postId}/playbook`)
            ]);
            const stageData = stageRes.ok ? await stageRes.json() : {};
            const playbookData = playbookRes.ok ? await playbookRes.json() : {};
            const currentStage = (stageData.workflow_stage || '').toLowerCase();
            if (!stagesWithPlaybook.includes(currentStage) || !playbookData.success || !playbookData.playbook || !playbookData.playbook[currentStage]) {
                panel.style.display = 'none';
                return;
            }
            const tasks = playbookData.playbook[currentStage] || [];
            const state = (playbookData.state && playbookData.state[currentStage]) || {};
            listEl.innerHTML = '';
            tasks.forEach(t => {
                const taskId = t.id;
                const label = t.label || taskId;
                const taskState = state[taskId] || {};
                const status = taskState.status || 'todo';
                const note = taskState.note || '';
                const li = document.createElement('li');
                li.className = 'playbook-task';
                li.style.marginBottom = '0.25rem';
                const statuses = currentStage === 'review' ? ['todo', 'done', 'skipped', 'fail'] : ['todo', 'done', 'skipped'];
                const btnSpan = document.createElement('span');
                btnSpan.style.marginLeft = '0.5rem';
                statuses.forEach(s => {
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.textContent = s;
                    btn.style.fontSize = '0.7rem';
                    btn.style.padding = '0.1rem 0.35rem';
                    btn.style.marginRight = '0.2rem';
                    btn.style.cursor = 'pointer';
                    if (s === status) btn.style.fontWeight = 'bold';
                    btn.addEventListener('click', () => this.setPlaybookTaskStatus(postId, currentStage, taskId, s, listEl, panel));
                    btnSpan.appendChild(btn);
                });
                li.appendChild(document.createTextNode(label));
                li.appendChild(btnSpan);
                if (status === 'fail' && note) {
                    const noteEl = document.createElement('div');
                    noteEl.style.fontSize = '0.7rem';
                    noteEl.style.color = '#cbd5e1';
                    noteEl.textContent = note;
                    li.appendChild(noteEl);
                }
                listEl.appendChild(li);
            });
            panel.style.display = tasks.length ? '' : 'none';
        } catch (e) {
            panel.style.display = 'none';
        }
    }

    async setPlaybookTaskStatus(postId, stage, taskId, status, listEl, panel) {
        const body = { stage, task_id: taskId, status };
        if (status === 'fail') {
            const note = window.prompt('Note (optional):');
            if (note !== null) body.note = note;
        }
        try {
            const res = await fetch(`/api/posts/${postId}/playbook`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const data = await res.json();
            if (data.success && listEl && panel) await this.updatePlaybookPanel();
        } catch (e) {
            console.warn('[Blog Pipeline Header] Playbook update failed:', e);
        }
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
            // Display theme_name and content_type_name (sub-category)
            if (taxonomy.theme_name) {
                if (taxonomy.content_type_name) {
                    taxonomyEl.textContent = `${taxonomy.theme_name}: ${taxonomy.content_type_name}`;
                } else {
                    taxonomyEl.textContent = taxonomy.theme_name;
                }
            } else {
                taxonomyEl.textContent = '';
            }
        } catch (error) {
            console.warn('[Blog Pipeline Header] Error updating taxonomy display:', error);
            taxonomyEl.textContent = '';
        }
    }

    async updateRecipeTitle() {
        const recipeEl = document.getElementById('pipeline-title-recipe');
        if (!recipeEl) return;
        
        const postId = this.getPostId();
        if (!postId || postId === '0' || parseInt(postId) === 0) {
            recipeEl.textContent = 'Recipe';
            return;
        }
        
        try {
            // Try multiple endpoints to get post title
            let postTitle = null;
            
            // Try /planning/api/posts/<post_id> first (most reliable)
            try {
                const postResp = await fetch(`/planning/api/posts/${postId}`);
                if (postResp.ok) {
                    const postData = await postResp.json();
                    // The API returns { post: { title: "...", ... } } structure
                    if (postData.post && postData.post.title) {
                        postTitle = postData.post.title;
                    } else if (postData.title) {
                        postTitle = postData.title;
                    }
                }
            } catch (e) {
                console.warn('[Blog Pipeline Header] Error fetching from planning API:', e);
            }
            
            // Fallback: try /post-info/api/post-info/<post_id>
            if (!postTitle) {
                try {
                    const postResp = await fetch(`/post-info/api/post-info/${postId}`);
                    if (postResp.ok) {
                        const postData = await postResp.json();
                        postTitle = postData.title;
                    }
                } catch (e) {
                    console.warn('[Blog Pipeline Header] Error fetching from post-info API:', e);
                }
            }
            
            // Use post title (should be set to recipe title when post is created)
            if (postTitle) {
                recipeEl.textContent = postTitle;
            } else {
                recipeEl.textContent = 'Recipe';
            }
        } catch (e) {
            console.warn('[Blog Pipeline Header] Error fetching recipe title:', e);
            recipeEl.textContent = 'Recipe';
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
                        if (postTypeData.success && postTypeData.post_type === 'themed') {
                            // For themed (blog/article) posts, show post title — not "Unselected theme"
                            const blogTitle = postTypeData.post_title || 'Blog post';
                            if (themeEl) {
                                themeEl.textContent = blogTitle;
                            }
                            return; // Don't continue with theme lookup
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
        let currentStage = window.currentStage || this.getCurrentStageFromURL();
        let currentSubstage = window.currentSubstage || this.getCurrentSubstageFromURL();
        
        // Normalize stage names (concept -> planning)
        if (currentStage === 'concept') {
            currentStage = 'planning';
        }

        console.log('[Blog Pipeline Header] Current stage:', currentStage, 'substage:', currentSubstage);

        // Show sub-stages line (ensure it's visible) - ALWAYS show if post_type is defined
        const subStagesLine = document.getElementById('sub-stages-line');
        if (subStagesLine) {
            // Always show sub-stages line if it exists (post_type is defined)
            subStagesLine.style.display = 'flex';
        }

        // Update main stage buttons (check both data-stage and data-stage-alias)
        const stageButtons = document.querySelectorAll('.stage-btn');
        stageButtons.forEach(button => {
            const stage = button.getAttribute('data-stage');
            const stageAlias = button.getAttribute('data-stage-alias');
            if (stage === currentStage || stageAlias === currentStage || 
                (currentStage === 'planning' && stageAlias === 'concept')) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });

        // Show/hide sub-stage groups based on current stage
        // Show the group for current stage, hide others
        const subStageGroups = document.querySelectorAll('.sub-stage-group');
        subStageGroups.forEach(group => {
            const groupStage = group.getAttribute('data-stage');
            const groupStageAlias = group.getAttribute('data-stage-alias');
            // Match if stage matches or alias matches, or if planning/concept match
            const matches = groupStage === currentStage || 
                          groupStageAlias === currentStage ||
                          (currentStage === 'planning' && (groupStage === 'planning' || groupStageAlias === 'concept')) ||
                          (currentStage === 'concept' && (groupStage === 'planning' || groupStageAlias === 'concept'));
            if (matches) {
                group.style.display = 'flex';
            } else {
                group.style.display = 'none';
            }
        });

        // Update sub-stage buttons (normalize substage names)
        const normalizedSubstage = this.normalizeSubstageName(currentSubstage);
        const subStageButtons = document.querySelectorAll('.sub-stage-btn');
        subStageButtons.forEach(button => {
            const substage = button.getAttribute('data-substage');
            const normalizedButtonSubstage = this.normalizeSubstageName(substage);
            // Compare both ways (with hyphens and underscores)
            const buttonHyphen = normalizedButtonSubstage.replace(/_/g, '-');
            const buttonUnderscore = normalizedButtonSubstage.replace(/-/g, '_');
            const currentHyphen = normalizedSubstage.replace(/_/g, '-');
            const currentUnderscore = normalizedSubstage.replace(/-/g, '_');
            
            if (normalizedButtonSubstage === normalizedSubstage ||
                buttonHyphen === currentHyphen ||
                buttonUnderscore === currentUnderscore ||
                substage === currentSubstage ||
                substage === currentSubstage.replace(/_/g, '-') ||
                substage === currentSubstage.replace(/-/g, '_')) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });

        // Update subtitle
        this.updateSubtitle(currentStage, currentSubstage);
    }
    
    normalizeSubstageName(substage) {
        if (!substage) return null;
        // Normalize substage names (e.g., 'brainstorm' -> 'topic_brainstorming')
        const substageMap = {
            'brainstorm': 'topic_brainstorming',
            'ideas': 'ideas',
            'taxonomy': 'taxonomy',
            'section-structure': 'section_structure',
            'section_structure': 'section_structure',
            'topic-allocation': 'topic_allocation',
            'topic_allocation': 'topic_allocation',
            'titling': 'section_titling',
            'section-titling': 'section_titling',
            'section_titling': 'section_titling',
            'drafting': 'drafting',
            'image-concepts': 'image_concepts',
            'image_concepts': 'image_concepts',
            'image-prompts': 'image_prompts',
            'image_prompts': 'image_prompts',
            'image-captions': 'image_captions',
            'image_captions': 'image_captions',
            'image-generation': 'image_generation',
            'image_generation': 'image_generation',
            'optimise': 'optimise',
            'title-summary': 'title_summary',
            'title_summary': 'title_summary',
            'header-image': 'header_image',
            'header_image': 'header_image',
            'seo-meta': 'seo_meta',
            'seo_meta': 'seo_meta'
        };
        return substageMap[substage] || substage.replace(/-/g, '_');
    }

    getCurrentStageFromURL() {
        const path = window.location.pathname;
        if (path.includes('/planning/')) return 'planning';  // Normalized from 'concept'
        if (path.includes('/authoring/')) return 'authoring';
        if (path.includes('/imaging/')) return 'imaging';
        if (path.includes('/header/')) return 'header';
        if (path.includes('/research/')) return 'research';
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
        // Planning substages
        if (path.includes('/calendar/ideas')) return 'ideas';
        if (path.includes('/calendar/taxonomy')) return 'taxonomy';
        if (path.includes('/concept/brainstorm')) return 'topic_brainstorming';
        if (path.includes('/concept/section-structure')) return 'section_structure';
        if (path.includes('/concept/topic-allocation')) return 'topic_allocation';
        if (path.includes('/concept/titling')) return 'section_titling';
        // Research substages
        if (path.includes('/research/sources')) return 'sources';
        if (path.includes('/research/visuals')) return 'visuals';
        if (path.includes('/research/prompts')) return 'prompts';
        if (path.includes('/research/verification')) return 'verification';
        // Authoring substages
        if (path.includes('/sections/drafting')) return 'drafting';
        if (path.includes('/sections/image-concepts') || path.includes('/sections/image_concepts')) return 'image_concepts';
        if (path.includes('/sections/image-prompts') || path.includes('/sections/image_prompts')) return 'image_prompts';
        if (path.includes('/sections/image-captions') || path.includes('/sections/image_captions')) return 'image_captions';
        // Imaging substages
        if (path.includes('/sections/image-generation')) return 'image_generation';
        if (path.includes('/sections/optimise')) return 'optimise';
        // Header substages
        if (path.includes('/title-summary')) return 'title_summary';
        if (path.includes('/header-image')) return 'header_image';
        if (path.includes('/seo-meta')) return 'seo_meta';
        if (path.includes('/product-match')) return 'product_match';
        if (path.includes('/final-review') || path.includes('/preview')) return 'final_review';
        return null;
    }

    updatePreviewLink(postId) {
        const previewLink = document.querySelector('.preview-button');
        if (previewLink && postId) {
            previewLink.setAttribute('href', `/preview/${postId}`);
            console.log(`[Blog Pipeline Header] Updated preview link to /preview/${postId}`);
        }
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
            // Normalize the substage name
            const normalizedSubstage = this.normalizeSubstageName(currentSubstage);
            
            if (normalizedSubstage) {
                // Try exact match first
                let subtitle = subtitles[currentStage]?.[normalizedSubstage];
                // Try with underscores
                if (!subtitle) {
                    subtitle = subtitles[currentStage]?.[normalizedSubstage.replace(/-/g, '_')];
                }
                // Try with hyphens
                if (!subtitle) {
                    subtitle = subtitles[currentStage]?.[normalizedSubstage.replace(/_/g, '-')];
                }
                // Try with original substage name
                if (!subtitle) {
                    subtitle = subtitles[currentStage]?.[currentSubstage];
                }
                if (subtitle) {
                    subtitleElement.textContent = subtitle;
                } else {
                    subtitleElement.textContent = '';
                }
            } else {
                subtitleElement.textContent = '';
            }
        }
    }
}

// Initialize the header when the script loads
console.log('[Blog Pipeline Header] Script loaded, creating instance...');
const blogPipelineHeader = new BlogPipelineHeader();
console.log('[Blog Pipeline Header] Instance created:', blogPipelineHeader);
