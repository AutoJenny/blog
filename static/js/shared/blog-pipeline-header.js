/**
 * Blog Pipeline Header - Shared functionality for all pages using the header
 * Handles post data loading, navigation highlighting, and header updates
 */

class BlogPipelineHeader {
    constructor() {
        this.postData = null;
        this.init();
    }

    init() {
        console.log('[Blog Pipeline Header] Initializing...');
        
        // Load post data when DOM is ready
        document.addEventListener('DOMContentLoaded', () => {
            console.log('[Blog Pipeline Header] DOM ready, loading post data...');
            this.loadPostData();
        });

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
        setTimeout(() => this.updateNavigationHighlighting(), 100);
        
        // If DOM is already loaded, load post data immediately with a longer delay
        if (document.readyState === 'loading') {
            console.log('[Blog Pipeline Header] DOM still loading, waiting for DOMContentLoaded...');
        } else {
            console.log('[Blog Pipeline Header] DOM already loaded, loading post data with delay...');
            // Update week/theme immediately for week-based pages
            this.updateWeekAndTheme();
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

        console.log('[Blog Pipeline Header] Header fields updated');
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
        
        // Try to get from post data (post-based)
        if (this.postData && this.postData.schedule) {
            year = this.postData.schedule.year;
            weekNumber = this.postData.schedule.week_number;
            selectedTheme = this.postData.schedule.selected_theme_title;
            
            // If schedule doesn't have theme but has idea_id, fetch it
            if (!selectedTheme && this.postData.schedule.idea_id) {
                try {
                    const ideaResp = await fetch(`/planning/api/calendar/ideas/${this.postData.schedule.idea_id}`);
                    if (ideaResp.ok) {
                        const ideaData = await ideaResp.json();
                        const idea = ideaData.idea || ideaData;
                        if (idea && idea.idea_title) {
                            selectedTheme = idea.idea_title;
                        }
                    }
                } catch (e) {
                    console.warn('[Blog Pipeline Header] Error fetching theme from idea_id:', e);
                }
            }
            
            // If still no theme and we have week info, check week schedule
            if (!selectedTheme && year && weekNumber) {
                try {
                    const weekResp = await fetch(`/planning/api/calendar/schedule/${year}/${weekNumber}`);
                    if (weekResp.ok) {
                        const weekData = await weekResp.json();
                        if (weekData.schedule && Array.isArray(weekData.schedule) && weekData.schedule.length > 0) {
                            const scheduleWithIdea = weekData.schedule.find(s => s.idea_id);
                            if (scheduleWithIdea && scheduleWithIdea.idea_id) {
                                const ideaResp = await fetch(`/planning/api/calendar/ideas/${scheduleWithIdea.idea_id}`);
                                if (ideaResp.ok) {
                                    const ideaData = await ideaResp.json();
                                    const idea = ideaData.idea || ideaData;
                                    if (idea && idea.idea_title) {
                                        selectedTheme = idea.idea_title;
                                    }
                                }
                            }
                        }
                    }
                    
                    // If still no theme selected, auto-select first available theme for this week
                    if (!selectedTheme && weekNumber) {
                        try {
                            const ideasResp = await fetch(`/planning/api/calendar/ideas/week/${weekNumber}`);
                            if (ideasResp.ok) {
                                const ideasData = await ideasResp.json();
                                const ideas = Array.isArray(ideasData) ? ideasData : (ideasData?.ideas || []);
                                
                                // Find themes (item_classification === 'theme')
                                const themes = ideas.filter(i => 
                                    (i.item_classification || 'idea').toLowerCase() === 'theme'
                                );
                                
                                if (themes.length > 0) {
                                    // Auto-select first theme (already sorted by priority from API)
                                    const firstTheme = themes[0];
                                    selectedTheme = firstTheme.idea_title;
                                    
                                    // Auto-select this theme in the schedule
                                    try {
                                        const selectResp = await fetch('/planning/api/calendar/select-theme', {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({
                                                idea_id: firstTheme.id,
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
            if (postId && postId !== '0' && parseInt(postId) !== 0) {
                // Post-based: fetch schedule - but also check week schedule for theme
                try {
                    const resp = await fetch(`/planning/api/posts/${postId}`);
                    if (resp.ok) {
                        const data = await resp.json();
                        if (data.schedule) {
                            year = data.schedule.year;
                            weekNumber = data.schedule.week_number;
                            selectedTheme = data.schedule.selected_theme_title;
                            
                            // If no theme from post schedule but we have week info, check week schedule
                            if (!selectedTheme && year && weekNumber) {
                                const weekResp = await fetch(`/planning/api/calendar/schedule/${year}/${weekNumber}`);
                                if (weekResp.ok) {
                                    const weekData = await weekResp.json();
                                    if (weekData.schedule && Array.isArray(weekData.schedule) && weekData.schedule.length > 0) {
                                        const scheduleWithIdea = weekData.schedule.find(s => s.idea_id);
                                        if (scheduleWithIdea && scheduleWithIdea.idea_id) {
                                            const ideaResp = await fetch(`/planning/api/calendar/ideas/${scheduleWithIdea.idea_id}`);
                                            if (ideaResp.ok) {
                                                const ideaData = await ideaResp.json();
                                                const idea = ideaData.idea || ideaData;
                                                if (idea && idea.idea_title) {
                                                    selectedTheme = idea.idea_title;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                } catch (e) {
                    console.warn('[Blog Pipeline Header] Error fetching schedule:', e);
                }
            } else {
                // Week-based: get from localStorage, window variables, or URL params
                const savedYear = localStorage.getItem('calendar-week-view-year');
                const savedWeek = localStorage.getItem('calendar-week-view-week');
                
                // Also check window variables (set by templates)
                if (window.year && window.weekNumber) {
                    year = window.year;
                    weekNumber = window.weekNumber;
                } else if (savedYear && savedWeek) {
                    year = parseInt(savedYear);
                    weekNumber = parseInt(savedWeek);
                }
                
                if (year && weekNumber) {
                    // Fetch theme for this week
                    try {
                        const resp = await fetch(`/planning/api/calendar/schedule/${year}/${weekNumber}`);
                        if (resp.ok) {
                            const data = await resp.json();
                            if (data.schedule && Array.isArray(data.schedule) && data.schedule.length > 0) {
                                // Find schedule entry with idea_id (selected theme)
                                const scheduleWithIdea = data.schedule.find(s => s.idea_id);
                                if (scheduleWithIdea && scheduleWithIdea.idea_id) {
                                    // Fetch the idea details to get the title
                                    const ideaResp = await fetch(`/planning/api/calendar/ideas/${scheduleWithIdea.idea_id}`);
                                    if (ideaResp.ok) {
                                        const ideaData = await ideaResp.json();
                                        // Handle both {idea: {...}} and direct {...} response formats
                                        const idea = ideaData.idea || ideaData;
                                        if (idea && idea.idea_title) {
                                            selectedTheme = idea.idea_title;
                                        }
                                    }
                                }
                            }
                        }
                        
                        // If no theme selected yet, check if themes exist for this week and auto-select first one
                        if (!selectedTheme && weekNumber && year) {
                            try {
                                const ideasResp = await fetch(`/planning/api/calendar/ideas/week/${weekNumber}`);
                                if (ideasResp.ok) {
                                    const ideasData = await ideasResp.json();
                                    const ideas = Array.isArray(ideasData) ? ideasData : (ideasData?.ideas || []);
                                    
                                    // Find themes (item_classification === 'theme')
                                    const themes = ideas.filter(i => 
                                        (i.item_classification || 'idea').toLowerCase() === 'theme'
                                    );
                                    
                                    if (themes.length > 0) {
                                        // Auto-select first theme (already sorted by priority from API)
                                        const firstTheme = themes[0];
                                        selectedTheme = firstTheme.idea_title;
                                        
                                        // Auto-select this theme in the schedule
                                        try {
                                            const selectResp = await fetch('/planning/api/calendar/select-theme', {
                                                method: 'POST',
                                                headers: { 'Content-Type': 'application/json' },
                                                body: JSON.stringify({
                                                    idea_id: firstTheme.id,
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
        
        // Update theme
        if (selectedTheme) {
            themeEl.textContent = selectedTheme;
        } else {
            themeEl.textContent = 'Unselected theme';
        }
    }

    getStageName() {
        // No prefix needed - just show week info and theme
        return '';
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
        if (path.includes('/title-summary')) return 'title-summary';
        if (path.includes('/header-image')) return 'header-image';
        if (path.includes('/seo-meta')) return 'seo-meta';
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
                'optimise': 'Resize, compress, and watermark images generated in the prior step.'
            },
            'header': {
                'title-summary': 'Generate post title, subtitle, slug, and summary blurb.',
                'header-image': 'Create header image with caption and alt text.',
                'seo-meta': 'Generate SEO metadata including meta title, description, and tags.',
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
