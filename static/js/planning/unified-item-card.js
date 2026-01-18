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
        'event': 'event',
        'product': 'product'
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
        'event': 'Event',
        'product': 'Product'
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
    const description = isLanguageItem ? null : getItemDescription(item, options.description);
    
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
    
    // Title
    const titleEl = document.createElement('div');
    titleEl.className = 'item-title';
    titleEl.textContent = title;
    card.appendChild(titleEl);
    
    // Compact action row: status + actions
    const actionRow = document.createElement('div');
    actionRow.className = 'compact-action-row';
    
    // Status line (non-clickable) - hide for language items
    const isLanguageItemForStatus = typeClass === 'weekly-word' || typeClass === 'weekly-phrase' || typeClass === 'weekly-insult' ||
                                    category === 'weekly_word' || category === 'weekly_phrase' || category === 'weekly_insult' ||
                                    type === 'word' || type === 'phrase' || type === 'insult';
    if (!isLanguageItemForStatus) {
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
    
    // Play button (create) - shown when post doesn't exist
    if (!postExists) {
        const createBtn = document.createElement('button');
        createBtn.className = 'icon-btn-compact btn-create';
        createBtn.title = 'Create post';
        createBtn.innerHTML = '<i class="fas fa-play"></i>';
        createBtn.onclick = (e) => {
            e.stopPropagation();
            if (options.onCreate) {
                options.onCreate(e, item, card);
            }
        };
        actions.appendChild(createBtn);
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
    
    // Info button (always shown)
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
    module.exports = { createUnifiedItemCard, normalizeTypeForClass, normalizeTypeName, determinePostStatus };
}

// Make available globally
window.createUnifiedItemCard = createUnifiedItemCard;
window.normalizeTypeForClass = normalizeTypeForClass;
window.normalizeTypeName = normalizeTypeName;
window.determinePostStatus = determinePostStatus;

