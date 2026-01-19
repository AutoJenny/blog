/**
 * Taxonomy Assignment JavaScript
 * Handles taxonomy assignment UI and API interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    const postId = window.postId;
    // CRITICAL: Load assignedPostId from localStorage if available, otherwise use postId
    const storageKey = `taxonomy_assigned_post_${postId}`;
    let assignedPostId = localStorage.getItem(storageKey) ? parseInt(localStorage.getItem(storageKey)) : postId;
    
    // DOM elements
    const themeSelect = document.getElementById('theme-select');
    const contentTypeSelect = document.getElementById('content-type-select');
    const formatSelect = document.getElementById('format-select');
    const generateBtn = document.getElementById('generate-taxonomy-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    const saveStatus = document.getElementById('save-status');
    const currentTaxonomyDisplay = document.getElementById('current-taxonomy');
    const commonAssetsDisplay = document.getElementById('common-assets-display');
    const commonAssetsList = document.getElementById('common-assets-list');
    const generationStatus = document.getElementById('generation-status');
    const reasoningDisplay = document.getElementById('reasoning-display');
    const reasoningText = document.getElementById('reasoning-text');
    
    let themes = [];
    let contentTypes = [];
    let formats = [];
    let currentTaxonomy = null;
    
    // Load taxonomy data and current assignment
    async function initialize() {
        try {
            await loadTaxonomyData();
            await loadCurrentTaxonomy();
            setupEventListeners();
        } catch (error) {
            console.error('Error initializing taxonomy assignment:', error);
            currentTaxonomyDisplay.innerHTML = '<div class="alert alert-error">Error loading taxonomy data</div>';
        }
    }
    
    // Load all taxonomy items from API
    async function loadTaxonomyData() {
        try {
            // Load themes
            const themesResponse = await fetch('/api/taxonomy/items?tier=category');
            const themesData = await themesResponse.json();
            if (themesData.success) {
                themes = themesData.items;
                populateThemeSelect();
            }
            
            // Load formats
            const formatsResponse = await fetch('/api/taxonomy/items?tier=format');
            const formatsData = await formatsResponse.json();
            if (formatsData.success) {
                formats = formatsData.items;
                populateFormatSelect();
            }
        } catch (error) {
            console.error('Error loading taxonomy data:', error);
            throw error;
        }
    }
    
    // Load current taxonomy assignment for post
    async function loadCurrentTaxonomy() {
        try {
            // CRITICAL: Use assignedPostId if available (from previous generation), otherwise find correct post
            let targetPostId = assignedPostId || postId;
            
            // If we don't have an assignedPostId, find the correct post for the viewed week
            if (!assignedPostId) {
                // Get week context from URL
                let year, week;
                if (window.WeekContext) {
                    const weekContext = window.WeekContext.getWeekContext();
                    if (weekContext) {
                        year = weekContext.year;
                        week = weekContext.week;
                    }
                }
                
                // If we have week context, find the post for that week's theme
                if (year && week) {
                    try {
                        const scheduleResponse = await fetch(`/planning/api/calendar/schedule/${year}/${week}`);
                        const scheduleData = await scheduleResponse.json();
                        if (scheduleData.schedule && Array.isArray(scheduleData.schedule) && scheduleData.schedule.length > 0) {
                            // Find the theme for this week
                            const weekThemeSchedule = scheduleData.schedule.find(s => s.theme_id || s.calendar_theme_id);
                            if (weekThemeSchedule && (weekThemeSchedule.theme_id || weekThemeSchedule.calendar_theme_id)) {
                                // Use backend endpoint to find post by theme_id
                                const themeId = weekThemeSchedule.theme_id || weekThemeSchedule.calendar_theme_id;
                                const postByThemeResp = await fetch(`/planning/api/posts/by-theme/${themeId}`);
                                if (postByThemeResp.ok) {
                                    const postByThemeData = await postByThemeResp.json();
                                    if (postByThemeData.success && postByThemeData.post_id) {
                                        targetPostId = postByThemeData.post_id;
                                        assignedPostId = targetPostId; // Remember it for future operations
                                        localStorage.setItem(storageKey, assignedPostId.toString());
                                        console.log(`[Taxonomy Display] Using post ${targetPostId} for week ${year}/${week} theme - saved to localStorage`);
                                    }
                                }
                            }
                        }
                    } catch (e) {
                        console.warn('Could not find post for week, using provided post_id:', e);
                    }
                }
            }
            
            const response = await fetch(`/planning/api/posts/${targetPostId}/taxonomy`);
            const data = await response.json();
            
            if (data.success && data.taxonomy.theme_id) {
                currentTaxonomy = data.taxonomy;
                displayCurrentTaxonomy(data.taxonomy);
                
                // CRITICAL: Update assignedPostId to the post we just loaded from, and persist it
                if (targetPostId !== assignedPostId) {
                    assignedPostId = targetPostId;
                    localStorage.setItem(storageKey, assignedPostId.toString());
                    console.log(`[Taxonomy] Updated assignedPostId to ${assignedPostId} after loading taxonomy`);
                }
                
                // Pre-select in form
                themeSelect.value = data.taxonomy.theme_id;
                await loadContentTypesForTheme(data.taxonomy.theme_id);
                contentTypeSelect.value = data.taxonomy.content_type_id;
                formatSelect.value = data.taxonomy.format_id;
                
                // Update common assets
                displayCommonAssets(data.taxonomy.content_type_assets);
                
                // Enable save button
            } else {
                currentTaxonomyDisplay.innerHTML = '<div class="taxonomy-item"><div class="taxonomy-item-value">No taxonomy assigned yet</div></div>';
            }
        } catch (error) {
            console.error('Error loading current taxonomy:', error);
            currentTaxonomyDisplay.innerHTML = '<div class="alert alert-error">Error loading current taxonomy</div>';
        }
    }
    
    // Populate content category dropdown
    function populateThemeSelect() {
        themeSelect.innerHTML = '<option value="">-- Select Content Category --</option>';
        themes.forEach(theme => {
            const option = document.createElement('option');
            option.value = theme.id;
            option.textContent = theme.display_name;
            themeSelect.appendChild(option);
        });
    }
    
    // Populate format dropdown
    function populateFormatSelect() {
        formatSelect.innerHTML = '<option value="">-- Select Format --</option>';
        formats.forEach(format => {
            const option = document.createElement('option');
            option.value = format.id;
            option.textContent = format.display_name;
            formatSelect.appendChild(option);
        });
    }
    
    // Load content types for selected content category
    async function loadContentTypesForTheme(themeId) {
        if (!themeId) {
            contentTypeSelect.innerHTML = '<option value="">-- Select Content Category first --</option>';
            contentTypeSelect.disabled = true;
            return;
        }
        
        try {
            const response = await fetch(`/api/taxonomy/content-types?theme_id=${themeId}`);
            const data = await response.json();
            
            if (data.success) {
                contentTypes = data.content_types;
                populateContentTypeSelect();
                contentTypeSelect.disabled = false;
            }
        } catch (error) {
            console.error('Error loading content types:', error);
            contentTypeSelect.innerHTML = '<option value="">Error loading content types</option>';
        }
    }
    
    // Populate content type dropdown
    function populateContentTypeSelect() {
        contentTypeSelect.innerHTML = '<option value="">-- Select Content Type --</option>';
        contentTypes.forEach(ct => {
            const option = document.createElement('option');
            option.value = ct.id;
            option.textContent = ct.display_name;
            contentTypeSelect.appendChild(option);
        });
    }
    
    // Display current taxonomy
    function displayCurrentTaxonomy(taxonomy) {
        let html = '';
        
        if (taxonomy.theme_name) {
            html += `<div class="taxonomy-item">
                <div class="taxonomy-item-label">Content Category</div>
                <div class="taxonomy-item-value">${escapeHtml(taxonomy.theme_name)}</div>
            </div>`;
        }
        
        if (taxonomy.content_type_name) {
            html += `<div class="taxonomy-item">
                <div class="taxonomy-item-label">Content Type</div>
                <div class="taxonomy-item-value">${escapeHtml(taxonomy.content_type_name)}</div>
            </div>`;
        }
        
        if (taxonomy.format_name) {
            html += `<div class="taxonomy-item">
                <div class="taxonomy-item-label">Format</div>
                <div class="taxonomy-item-value">${escapeHtml(taxonomy.format_name)}</div>
            </div>`;
        }
        
        currentTaxonomyDisplay.innerHTML = html || '<div class="taxonomy-item-value">No taxonomy assigned</div>';
    }
    
    // Display common assets
    function displayCommonAssets(assets) {
        if (!assets || assets.length === 0) {
            commonAssetsDisplay.style.display = 'none';
            return;
        }
        
        commonAssetsList.innerHTML = assets.map(asset => 
            `<span class="asset-badge">${escapeHtml(asset)}</span>`
        ).join('');
        commonAssetsDisplay.style.display = 'block';
    }
    
    // Generate taxonomy using LLM
    async function generateTaxonomy() {
            // CRITICAL: Get expanded idea for the CORRECT week, not just the post_id
        try {
            // SINGLE SOURCE OF TRUTH: Read year/week from URL only
            let year, week;
            if (window.WeekContext) {
                const weekContext = window.WeekContext.getWeekContext();
                if (weekContext) {
                    year = weekContext.year;
                    week = weekContext.week;
                }
            }
            
            // Check for subtitle (the expanded idea description generated at ideas stage)
            let postDataUrl = `/planning/api/posts/${postId}`;
            if (year && week) {
                postDataUrl += `?year=${year}&week=${week}`;
            }
            
            const postDataResponse = await fetch(postDataUrl);
            const postData = await postDataResponse.json();
            
            // Check for subtitle (the expanded idea description) - this is what we now use instead of expanded_idea
            const expandedIdea = postData.post?.subtitle || postData.post?.expanded_idea;
            
            if (!expandedIdea || expandedIdea.trim() === '') {
                alert('Please generate a subtitle (expanded idea description) first at the Ideas stage before assigning taxonomy.');
                return;
            }
            
            // CRITICAL: Determine the correct post_id for taxonomy assignment
            // If we're viewing a different week than the post's schedule, we should assign
            // taxonomy to the post that's actually scheduled for this week, OR to any post
            // that has the week's theme
            let targetPostId = postId;
            
            if (year && week) {
                // Try to find the post scheduled for this week
                try {
                    const scheduleResponse = await fetch(`/planning/api/calendar/schedule/${year}/${week}`);
                    const scheduleData = await scheduleResponse.json();
                    if (scheduleData.schedule && Array.isArray(scheduleData.schedule) && scheduleData.schedule.length > 0) {
                        // STEP 1: Look for a post directly scheduled for this week
                        const weekSchedule = scheduleData.schedule.find(s => s.post_id && s.idea_id);
                        if (weekSchedule && weekSchedule.post_id) {
                            targetPostId = weekSchedule.post_id;
                            console.log(`Taxonomy will be assigned to post ${targetPostId} (scheduled for week ${year}/${week})`);
                        } else {
                            // STEP 2: If no post_id in schedule, find the theme and look for ANY post with that theme
                            const weekThemeSchedule = scheduleData.schedule.find(s => s.idea_id && !s.post_id);
                            if (weekThemeSchedule && weekThemeSchedule.idea_id) {
                                console.log(`Week ${year}/${week} has theme idea_id ${weekThemeSchedule.idea_id}, searching for post with this theme...`);
                                // Query for any post that has this theme in its schedule
                                const postsWithThemeResponse = await fetch(`/planning/api/calendar/schedule/${year}/${week}`);
                                // Actually, we need to query differently - find all schedule entries with this idea_id
                                // For now, log this and use the theme's idea_id to find posts
                                // The backend should handle finding the post by theme
                                console.log(`Will use theme idea_id ${weekThemeSchedule.idea_id} to find post`);
                            }
                        }
                    }
                } catch (e) {
                    console.warn('Could not find post for week, using provided post_id:', e);
                }
            }
            
            // Show loading state
            generationStatus.style.display = 'flex';
            generateBtn.disabled = true;
            
            // Call LLM generation API - pass year/week so backend can find correct post
            // Use subtitle as expanded_idea (they're the same thing - subtitle is the expanded idea description)
            const requestBody = {
                post_id: targetPostId,  // Use the correct post_id for the week (or fallback)
                expanded_idea: expandedIdea  // This is now the subtitle from the ideas stage
            };
            
            // CRITICAL: Pass year/week parameters so backend can override post_id if wrong
            if (year && week) {
                requestBody.year = parseInt(year);
                requestBody.week_number = parseInt(week);
            }
            
            const response = await fetch('/planning/api/taxonomy/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });
            
            const data = await response.json();
            
            if (data.success) {
                // CRITICAL: Update assignedPostId to the post that actually received the taxonomy
                if (data.assigned_post_id) {
                    assignedPostId = data.assigned_post_id;
                    // Persist to localStorage so it survives page reloads
                    localStorage.setItem(storageKey, assignedPostId.toString());
                    console.log(`[Taxonomy] Taxonomy assigned to post ${assignedPostId} (was ${postId}) - saved to localStorage`);
                }
                
                // Populate form with generated taxonomy
                themeSelect.value = data.taxonomy.theme_id;
                await loadContentTypesForTheme(data.taxonomy.theme_id);
                contentTypeSelect.value = data.taxonomy.content_type_id;
                formatSelect.value = data.taxonomy.format_id;
                
                // Load and display common assets
                const contentTypeResponse = await fetch(`/api/taxonomy/items/${data.taxonomy.content_type_id}`);
                const contentTypeData = await contentTypeResponse.json();
                if (contentTypeData.success) {
                    displayCommonAssets(contentTypeData.item.common_assets || []);
                }
                
                // Display reasoning
                if (data.taxonomy.reasoning) {
                    reasoningText.textContent = data.taxonomy.reasoning;
                    reasoningDisplay.style.display = 'block';
                }
                
                // Update save button state
                // Reload current taxonomy display (will use correct post_id)
                await loadCurrentTaxonomy();
            } else {
                // Show detailed error message
                let errorMsg = `Error generating taxonomy: ${data.error}`;
                if (data.debug_info) {
                    errorMsg += '\n\nDebug information:';
                    if (data.debug_info.response_preview) {
                        errorMsg += `\nResponse preview: ${data.debug_info.response_preview}`;
                    }
                    if (data.debug_info.json_content) {
                        errorMsg += `\nJSON content: ${data.debug_info.json_content}`;
                    }
                    if (data.debug_info.parse_error) {
                        errorMsg += `\nParse error: ${data.debug_info.parse_error}`;
                    }
                }
                alert(errorMsg);
                console.error('Taxonomy generation error:', data);
            }
        } catch (error) {
            console.error('Error generating taxonomy:', error);
            alert('Error generating taxonomy. Please try again.');
        } finally {
            generationStatus.style.display = 'none';
            generateBtn.disabled = false;
            // Auto-save after generation completes
            autoSaveTaxonomy();
        }
    }
    
    // Auto-save taxonomy assignment (debounced)
    let saveTimeout = null;
    async function autoSaveTaxonomy() {
        const themeId = parseInt(themeSelect.value);
        const contentTypeId = parseInt(contentTypeSelect.value);
        const formatId = parseInt(formatSelect.value);
        
        // Only save if all three fields are selected
        if (!themeId || !contentTypeId || !formatId) {
            return;
        }
        
        // Clear existing timeout
        if (saveTimeout) {
            clearTimeout(saveTimeout);
        }
        
        // Debounce: save after 500ms of no changes
        saveTimeout = setTimeout(async () => {
            try {
                // CRITICAL: Use assignedPostId (the correct post) instead of postId from URL
                const savePostId = assignedPostId || postId;
                console.log(`[Taxonomy] Auto-saving taxonomy to post ${savePostId}`);
                
                const response = await fetch(`/planning/api/posts/${savePostId}/taxonomy`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        theme_id: themeId,
                        content_type_id: contentTypeId,
                        format_id: formatId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Ensure assignedPostId is persisted
                    localStorage.setItem(storageKey, assignedPostId.toString());
                    // Reload current taxonomy display
                    await loadCurrentTaxonomy();
                    
                    // Show saved indicator
                    if (saveStatus) {
                        saveStatus.style.display = 'block';
                        setTimeout(() => {
                            saveStatus.style.display = 'none';
                        }, 2000);
                    }
                    
                    console.log('[Taxonomy] Auto-saved successfully');
                } else {
                    console.error('[Taxonomy] Auto-save failed:', data.error);
                }
            } catch (error) {
                console.error('[Taxonomy] Error auto-saving taxonomy:', error);
            }
        }, 500);
    }
    
    // Setup event listeners
    function setupEventListeners() {
        // Content category selection changes content types
        themeSelect.addEventListener('change', async function() {
            const themeId = parseInt(this.value);
            await loadContentTypesForTheme(themeId);
            contentTypeSelect.value = '';
            formatSelect.value = '';
            commonAssetsDisplay.style.display = 'none';
            autoSaveTaxonomy(); // Auto-save when category changes
        });
        
        // Content type selection shows common assets
        contentTypeSelect.addEventListener('change', async function() {
            const contentTypeId = parseInt(this.value);
            if (contentTypeId) {
                try {
                    const response = await fetch(`/api/taxonomy/items/${contentTypeId}`);
                    const data = await response.json();
                    if (data.success && data.item.common_assets) {
                        displayCommonAssets(data.item.common_assets);
                    }
                } catch (error) {
                    console.error('Error loading content type details:', error);
                }
            } else {
                commonAssetsDisplay.style.display = 'none';
            }
            autoSaveTaxonomy(); // Auto-save when content type changes
        });
        
        // Format selection - auto-save on change
        formatSelect.addEventListener('change', autoSaveTaxonomy);
        
        // Generate button
        generateBtn.addEventListener('click', generateTaxonomy);
        
        // Cancel button
        cancelBtn.addEventListener('click', function() {
            window.location.href = `/planning/posts/${postId}/concept/brainstorm`;
        });
    }
    
    // Utility function
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Initialize
    initialize();
});

