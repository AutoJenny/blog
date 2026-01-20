/**
 * Unified Item Card Component
 * 
 * Single source of truth for rendering calendar item cards across all tabs:
 * - Week-view
 * - Publication-schedule
 * - Scheduling
 * 
 * Ensures consistent appearance, behavior, and status display.
 */

/**
 * Normalize category/type to consistent type name for CSS classes
 * @param {string} category - Category from API (e.g., 'theme', 'profile_product')
 * @param {string} type - Type from options (e.g., 'idea', 'recipe')
 * @returns {string} Normalized type for CSS class (e.g., 'theme', 'recipe', 'profile-product')
 */
function normalizeTypeForClass(category, type) {
    // If type is provided, use it (week-view uses 'idea' for themes)
    if (type) {
        const typeMap = {
            'idea': 'theme',
            'theme': 'theme',
            'recipe': 'recipe',
            'profile': 'profile',
            'weekly-word': 'weekly-word',
            'weekly-phrase': 'weekly-phrase',
            'weekly-insult': 'weekly-insult',
            'event': 'event',
            'scheduled': 'scheduled'
        };
        return typeMap[type] || type;
    }
    
    // Otherwise normalize category
    if (!category) return 'unknown';
    
    // Handle underscore-separated categories
    const normalized = category.replace(/_/g, '-').toLowerCase();
    
    // Map specific categories
    const categoryMap = {
        'theme': 'theme',
        'theme-selection': 'theme',
        'recipe': 'recipe',
        'profile-product': 'profile-product',
        'profile-surname': 'profile-surname',
        'profile': 'profile',
        'weekly-word': 'weekly-word',
        'weekly-phrase': 'weekly-phrase',
        'weekly-insult': 'weekly-insult',
        'word': 'weekly-word',
        'phrase': 'weekly-phrase',
        'insult': 'weekly-insult',
        'product': 'product',
        'product-post': 'product',
        'event': 'event'
    };
    
    return categoryMap[normalized] || normalized;
}

/**
 * Normalize type name for display label
 * @param {string} category - Category from API
 * @param {string} typeName - Type name from options
 * @param {string} typeNameFromItem - Type name from item data
 * @returns {string} Display name (e.g., 'Theme', 'Recipe')
 */
function normalizeTypeName(category, typeName, typeNameFromItem) {
    if (typeName) return typeName;
    if (typeNameFromItem) return typeNameFromItem;
    
    if (!category) return 'Item';
    
    const nameMap = {
        'theme': 'Theme',
        'theme_selection': 'Theme',
        'recipe': 'Recipe',
        'profile_product': 'Product Profile',
        'profile_surname': 'Surname Profile',
        'profile': 'Profile',
        'weekly_word': 'Word',
        'weekly_phrase': 'Phrase',
        'weekly_insult': 'Insult',
        'word': 'Word',
        'phrase': 'Phrase',
        'insult': 'Insult',
        'product': 'product',
        'product-post': 'product',
        'event': 'Event'
    };
    
    return nameMap[category] || category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Determine if post exists and get status
 * @param {Object} item - Item data
 * @returns {Object} { postExists: boolean, postStatus: string|null }
 */
function determinePostStatus(item) {
  // Only treat an item as having a post when post_id (or explicit post_exists) is set.
  // Never fall back to item.id, because that is the source item's id (e.g., theme id),
  // not a post id. Using item.id here is what caused themes to open the wrong post.
  const hasPostId = item.post_id !== null && item.post_id !== undefined;
  const postId = hasPostId ? item.post_id : null;
  
  // Check if post exists (explicit flag or real post_id)
  const postExists = !!(
    item.post_exists === true ||
    hasPostId
  );
  
  // Get post status
  let postStatus = null;
  if (item.post_status) {
    postStatus = String(item.post_status).trim().toLowerCase();
  } else if (postExists && !item.post_status) {
    // If post exists but no status, default to 'draft'
    postStatus = 'draft';
  }
  
  return {
    postExists,
    postId,
    postStatus
  };
}

/**
 * Get title from item (handles different data structures)
 * @param {Object} item - Item data
 * @param {string} fallbackTitle - Fallback title from options
 * @returns {string} Title
 */
function getItemTitle(item, fallbackTitle) {
    return fallbackTitle ||
           item.title ||
           item.theme_title ||
           item.recipe_title ||
           item.post_title ||
           item.idea_title ||
           'Untitled';
}

/**
 * Get description from item
 * @param {Object} item - Item data
 * @param {string} fallbackDescription - Fallback description from options
 * @returns {string|null} Description (truncated to 50 chars if provided)
 */
function getItemDescription(item, fallbackDescription) {
    const desc = fallbackDescription ||
                 item.description ||
                 item.theme_description ||
                 item.recipe_description ||
                 item.idea_description ||
                 null;
    
    if (!desc) return null;
    
    // Truncate to 50 characters
    return desc.length > 50 ? desc.substring(0, 50) + '...' : desc;
}

/**
 * Navigate to the pipeline page for a post
 * @param {Object} item - Item data
 * @param {number} postId - Post ID
 */
function navigateToPipeline(item, postId) {
    const category = item.category || '';
    const year = item.year;
    const week = item.week;
    
    let workflowUrl = null;
    
    // Determine first workflow stage based on category
    if (category === 'recipe') {
        // Recipes: taxonomy redirects to drafting, so go directly to drafting
        workflowUrl = `/posts/${postId}/sections/drafting`;
    } else if (category === 'theme') {
        // Themes start at Planning -> Ideas
        workflowUrl = `/planning/posts/${postId}/calendar/ideas`;
    } else if (category === 'profile_product' || category === 'profile_surname') {
        // Profiles start at Planning -> Taxonomy
        workflowUrl = `/planning/posts/${postId}/calendar/taxonomy`;
    } else {
        // Default: Planning -> Ideas
        workflowUrl = `/planning/posts/${postId}/calendar/ideas`;
    }
    
    // Add year/week params if available
    if (year && week) {
        workflowUrl += `?year=${year}&week=${week}`;
    }
    
    console.log('[Unified Item Card] Navigating to pipeline:', workflowUrl);
    window.location.href = workflowUrl;
}

/**
 * Create unified item card
 * 
 * @param {Object} item - Item data (from API)
 * @param {Object} options - Configuration options
 * @param {string} options.type - Type for CSS class (e.g., 'theme', 'recipe')
 * @param {string} options.category - Category from API (e.g., 'theme', 'profile_product')
 * @param {string} options.typeName - Display name (e.g., 'Theme', 'Recipe')
 * @param {string} options.title - Title (overrides item title)
 * @param {string} options.description - Description (overrides item description)
 * @param {number} options.year - Year context
 * @param {number} options.week - Week context
 * @param {Function} options.onCreate - Create button handler
 * @param {Function} options.onWorkOn - Rocket button handler (1-click)
 * @param {Function} options.onInfo - Info button handler
 * @param {Function} options.onClick - Card click handler
 * @param {boolean} options.draggable - Make card draggable
 * @param {Object} options.dataset - Additional data attributes
 * @returns {HTMLElement} Card element
 */
function createUnifiedItemCard(item, options = {}) {
    // Normalize options
    const type = options.type || null;
    const category = options.category || item.category || null;
    const typeClass = normalizeTypeForClass(category, type);
    const typeName = normalizeTypeName(category, options.typeName, item.type_name);
    const title = getItemTitle(item, options.title);
    
    // For language items, don't show description at all
    // Check all possible ways language items might be identified
    const isLanguageItem = typeClass === 'weekly-word' || typeClass === 'weekly-phrase' || typeClass === 'weekly-insult' ||
                          (category && (category === 'weekly_word' || category === 'weekly_phrase' || category === 'weekly_insult' ||
                                       category === 'word' || category === 'phrase' || category === 'insult')) ||
                          (type && (type === 'weekly-word' || type === 'weekly-phrase' || type === 'weekly-insult' ||
                                   type === 'word' || type === 'phrase' || type === 'insult')) ||
                          (item.type && (item.type === 'weekly_word' || item.type === 'weekly_phrase' || item.type === 'weekly_insult')) ||
                          (item.category && (item.category === 'weekly_word' || item.category === 'weekly_phrase' || item.category === 'weekly_insult'));
    
    // For product posts, also don't show description (redundant)
    const isProductPost = typeClass === 'product' || category === 'product' || type === 'product' || type === 'product-post' ||
                         item.type === 'product' || item.category === 'product';
    
    const description = (isLanguageItem || isProductPost) ? null : getItemDescription(item, options.description);
    
    // Determine post status
    const { postExists, postId, postStatus } = determinePostStatus(item);
    
    // Create card element
    const card = document.createElement('div');
    card.className = `item-card type-${typeClass}`;
    
    // Add data attributes
    if (category) card.dataset.category = category;
    if (item.item_id) card.dataset.itemId = item.item_id;
    if (item.id) card.dataset.id = item.id;
    if (postId) card.dataset.postId = postId;
    if (options.year) card.dataset.year = options.year;
    if (options.week) card.dataset.week = options.week;
    if (options.channel) card.dataset.channel = options.channel;
    
    // Add additional dataset attributes
    if (options.dataset) {
        Object.keys(options.dataset).forEach(key => {
            card.dataset[key] = options.dataset[key];
        });
    }
    
    // Type label
    const typeLabel = document.createElement('div');
    typeLabel.className = 'item-type-label';
    typeLabel.textContent = typeName;
    card.appendChild(typeLabel);
    
    // Title (clickable to navigate to pipeline if post exists)
    const titleEl = document.createElement('div');
    titleEl.className = 'item-title';
    titleEl.textContent = title;
    if (postExists && postId) {
        titleEl.style.cursor = 'pointer';
        titleEl.style.textDecoration = 'underline';
        titleEl.style.textDecorationStyle = 'dotted';
        titleEl.title = 'Click to open pipeline';
        titleEl.onclick = (e) => {
            e.stopPropagation();
            console.log('[Unified Item Card] Title clicked for item:', item, 'postId:', postId);
            if (typeof navigateToPipeline === 'function') {
                navigateToPipeline(item, postId);
            } else if (window.navigateToPipeline && typeof window.navigateToPipeline === 'function') {
                window.navigateToPipeline(item, postId);
            } else {
                console.error('[Unified Item Card] navigateToPipeline function not found');
                // Fallback: navigate directly
                const category = item.category || '';
                let url;
                if (category === 'recipe') {
                    url = `/posts/${postId}/sections/drafting`;
                } else if (category === 'theme') {
                    url = `/planning/posts/${postId}/calendar/ideas`;
                } else {
                    url = `/planning/posts/${postId}/calendar/taxonomy`;
                }
                if (item.year && item.week) {
                    url += `?year=${item.year}&week=${item.week}`;
                }
                window.location.href = url;
            }
        };
    }
    card.appendChild(titleEl);
    
    // Compact action row: status + actions
    const actionRow = document.createElement('div');
    actionRow.className = 'compact-action-row';
    
    // Status line (non-clickable) - hide for language items and product posts
    const isLanguageItemForStatus = typeClass === 'weekly-word' || typeClass === 'weekly-phrase' || typeClass === 'weekly-insult' ||
                                    category === 'weekly_word' || category === 'weekly_phrase' || category === 'weekly_insult' ||
                                    type === 'word' || type === 'phrase' || type === 'insult';
    const isProductPostForStatus = typeClass === 'product' || category === 'product' || type === 'product' || type === 'product-post';
    if (!isLanguageItemForStatus && !isProductPostForStatus) {
        const statusLine = document.createElement('div');
        statusLine.className = 'status-line';
        const statusBadge = document.createElement('span');
        statusBadge.className = postStatus ? `status-badge status-${postStatus}` : 'status-badge status-none';
        statusBadge.textContent = postStatus ? (postStatus.charAt(0).toUpperCase() + postStatus.slice(1)) : 'Not created';
        statusLine.appendChild(statusBadge);
        actionRow.appendChild(statusLine);
    }
    
    // Action buttons
    const actions = document.createElement('div');
    actions.className = 'item-actions';
    
    // Start button - shown when post doesn't exist (prominent text button)
    if (!postExists) {
        const startBtn = document.createElement('button');
        startBtn.className = 'btn-start btn-primary';
        startBtn.innerHTML = '<i class="fas fa-play" style="margin-right: 0.25rem;"></i> Start';
        startBtn.title = 'Start work on this item';
        startBtn.style.cssText = 'padding: 0.5rem 1rem; font-size: 0.875rem; font-weight: 600; border-radius: 6px; background: #3b82f6; color: white; border: none; cursor: pointer; transition: all 0.2s; white-space: nowrap;';
        startBtn.onmouseover = function() { this.style.background = '#2563eb'; this.style.transform = 'translateY(-1px)'; };
        startBtn.onmouseout = function() { this.style.background = '#3b82f6'; this.style.transform = 'translateY(0)'; };
        startBtn.onclick = (e) => {
            e.stopPropagation();
            if (options.onCreate) {
                options.onCreate(e, item, card);
            }
        };
        actions.appendChild(startBtn);
    }
    
    // Pipeline button - shown when post exists (navigates to first workflow stage)
    if (postExists && postId) {
        const pipelineBtn = document.createElement('button');
        pipelineBtn.className = 'icon-btn-compact btn-pipeline';
        pipelineBtn.title = 'Open pipeline';
        pipelineBtn.innerHTML = '<i class="fas fa-sitemap"></i>';
        pipelineBtn.onclick = (e) => {
            e.stopPropagation();
            console.log('[Unified Item Card] Pipeline button clicked for item:', item, 'postId:', postId);
            if (typeof navigateToPipeline === 'function') {
                navigateToPipeline(item, postId);
            } else if (window.navigateToPipeline && typeof window.navigateToPipeline === 'function') {
                window.navigateToPipeline(item, postId);
            } else {
                console.error('[Unified Item Card] navigateToPipeline function not found');
                // Fallback: navigate directly
                const category = item.category || '';
                let url;
                if (category === 'recipe') {
                    url = `/posts/${postId}/sections/drafting`;
                } else if (category === 'theme') {
                    url = `/planning/posts/${postId}/calendar/ideas`;
                } else {
                    url = `/planning/posts/${postId}/calendar/taxonomy`;
                }
                if (item.year && item.week) {
                    url += `?year=${item.year}&week=${item.week}`;
                }
                window.location.href = url;
            }
        };
        actions.appendChild(pipelineBtn);
    }
    
    // Rocket button (work on / 1-click) - shown when post exists
    if (postExists && postId) {
        const rocketBtn = document.createElement('button');
        rocketBtn.className = 'icon-btn-compact btn-work-on';
        rocketBtn.title = 'Open 1‑click';
        rocketBtn.innerHTML = '<i class="fas fa-rocket"></i>';
        rocketBtn.onclick = (e) => {
            e.stopPropagation();
            if (options.onWorkOn) {
                options.onWorkOn(e, item, card);
            } else {
                // Default: navigate to one-click
                window.location.href = `/launchpad/one-click-publication?post_id=${postId}&output=blog`;
            }
        };
        actions.appendChild(rocketBtn);
    }
    
    // Info button - only show if post doesn't exist (pipeline button handles navigation when post exists)
    if (!postExists) {
        const infoBtn = document.createElement('button');
        infoBtn.className = 'icon-btn-compact btn-info';
        infoBtn.title = 'View details';
        infoBtn.innerHTML = '<i class="fas fa-info-circle"></i>';
        infoBtn.onclick = (e) => {
            e.stopPropagation();
            if (options.onInfo) {
                options.onInfo(e, item, card);
            }
        };
        actions.appendChild(infoBtn);
    }
    
    actionRow.appendChild(actions);
    card.appendChild(actionRow);
    
    // Description (optional)
    if (description) {
        const descEl = document.createElement('div');
        descEl.className = 'item-description';
        descEl.textContent = description;
        card.appendChild(descEl);
    }
    
    // Card click handler
    if (options.onClick) {
        card.onclick = (e) => {
            if (e.target.closest('.icon-btn-compact')) return; // Buttons handled separately
            options.onClick(e, item, card);
        };
    }
    
    // Make draggable if requested
    if (options.draggable) {
        card.draggable = true;
        if (options.onDragStart) {
            card.addEventListener('dragstart', (e) => options.onDragStart(e, item, card));
        }
        if (options.onDragEnd) {
            card.addEventListener('dragend', (e) => options.onDragEnd(e, item, card));
        }
    }
    
    return card;
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { createUnifiedItemCard, normalizeTypeForClass, normalizeTypeName, determinePostStatus, navigateToPipeline };
}

// Expose to window for use in other scripts
window.navigateToPipeline = navigateToPipeline;

// Make available globally
window.createUnifiedItemCard = createUnifiedItemCard;
window.normalizeTypeForClass = normalizeTypeForClass;
window.normalizeTypeName = normalizeTypeName;
window.determinePostStatus = determinePostStatus;

