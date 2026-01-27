// Simple week-per-view calendar script

function getISOWeekInfo(date) {
  const target = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const dayNr = (target.getUTCDay() + 6) % 7; // Monday=0
  target.setUTCDate(target.getUTCDate() - dayNr + 3);
  const firstThursday = new Date(Date.UTC(target.getUTCFullYear(), 0, 4));
  const weekNumber = 1 + Math.round(((target - firstThursday) / 86400000 - 3 + ((firstThursday.getUTCDay() + 6) % 7)) / 7);
  const year = target.getUTCFullYear();
  return { year, weekNumber };
}

function getWeekStartDate(year, weekNumber) {
  const simple = new Date(Date.UTC(year, 0, 4 + (weekNumber - 1) * 7));
  const dow = (simple.getUTCDay() + 6) % 7;
  simple.setUTCDate(simple.getUTCDate() - dow);
  return simple; // Monday
}

function formatDate(d) {
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

async function fetchJSON(url) {
  const res = await fetch(url, { credentials: 'same-origin' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// Helper function to get platform icon class
function getPlatformIcon(platformName) {
  const platform = (platformName || 'facebook').toLowerCase();
  const iconMap = {
    'facebook': 'fab fa-facebook',
    'instagram': 'fab fa-instagram',
    'twitter': 'fab fa-twitter',
    'linkedin': 'fab fa-linkedin',
    'youtube': 'fab fa-youtube',
    'pinterest': 'fab fa-pinterest',
    'tiktok': 'fab fa-tiktok'
  };
  return iconMap[platform] || 'fas fa-share-alt'; // Default icon
}

// Helper function to build syndication URL
function getSyndicationUrl(platform, contentType) {
  const platformName = (platform || 'facebook').toLowerCase();
  const contentTypeSlug = (contentType || 'product_post').toLowerCase();
  // Convert content_type to URL format (e.g., 'product' -> 'product_post', 'blog_post' -> 'blog_post')
  const urlContentType = contentTypeSlug === 'product' ? 'product_post' : 
                         contentTypeSlug === 'blog' ? 'blog_post' : contentTypeSlug;
  return `/launchpad/syndication/${platformName}/${urlContentType}`;
}

// Helper function to build compact item card with action row (matching publication-schedule format)
function buildItemCard(item, options) {
  const { type, typeName, title, postId, postStatus, postExists, description, onInfo, onCreate } = options;
  
  const card = document.createElement('div');
  card.className = `item-card type-${type}`;
  
  // Type label
  const typeLabel = document.createElement('div');
  typeLabel.className = 'item-type-label';
  typeLabel.textContent = typeName || type;
  card.appendChild(typeLabel);
  
  // Title
  const titleEl = document.createElement('div');
  titleEl.className = 'item-title';
  titleEl.textContent = title || 'Untitled';
  card.appendChild(titleEl);
  
  // Compact action row: status + actions
  const actionRow = document.createElement('div');
  actionRow.className = 'compact-action-row';
  
  // Status line (non-clickable)
  const statusLine = document.createElement('div');
  statusLine.className = 'status-line';
  const statusBadge = document.createElement('span');
  statusBadge.className = postStatus ? `status-badge status-${postStatus}` : 'status-badge status-none';
  statusBadge.textContent = postStatus ? (postStatus.charAt(0).toUpperCase() + postStatus.slice(1)) : 'Not created';
  statusLine.appendChild(statusBadge);
  actionRow.appendChild(statusLine);
  
  // Action buttons
  const actions = document.createElement('div');
  actions.className = 'item-actions';
  
  if (postExists && postId) {
    // Rocket = open 1-click
    const rocketBtn = document.createElement('button');
    rocketBtn.className = 'icon-btn-compact btn-work-on';
    rocketBtn.title = 'Open 1‑click';
    rocketBtn.innerHTML = '<i class="fas fa-rocket"></i>';
    rocketBtn.onclick = (e) => {
      e.stopPropagation();
      window.location.href = `/launchpad/one-click-publication?post_id=${postId}&output=blog`;
    };
    actions.appendChild(rocketBtn);
  } else {
    // Play = create
    const createBtn = document.createElement('button');
    createBtn.className = 'icon-btn-compact btn-create';
    createBtn.title = 'Create post';
    createBtn.innerHTML = '<i class="fas fa-play"></i>';
    createBtn.onclick = (e) => {
      e.stopPropagation();
      // Create post logic here - will be handled by item-specific handlers
      if (onCreate) {
        onCreate(e);
      } else if (item._onCreate) {
        item._onCreate(e);
      }
    };
    actions.appendChild(createBtn);
  }
  
  // Info = open modal (same as card click)
  const infoBtn = document.createElement('button');
  infoBtn.className = 'icon-btn-compact btn-info';
  infoBtn.title = 'View details';
  infoBtn.innerHTML = '<i class="fas fa-info-circle"></i>';
  infoBtn.onclick = (e) => {
    e.stopPropagation();
    if (onInfo) {
      onInfo(e);
    }
  };
  actions.appendChild(infoBtn);
  
  actionRow.appendChild(actions);
  card.appendChild(actionRow);
  
  // Description (optional)
  if (description) {
    const descEl = document.createElement('div');
    descEl.className = 'item-description';
    descEl.textContent = description.length > 50 ? description.substring(0, 50) + '...' : description;
    card.appendChild(descEl);
  }
  
  return card;
}

function renderItems(container, items, type, year, week) {
  if (!items || !Array.isArray(items) || items.length === 0) return;
  
  // Check if unified-item-card is loaded
  if (typeof window.createUnifiedItemCard !== 'function') {
    console.error('window.createUnifiedItemCard is not available. Waiting for unified-item-card.js to load...');
    // Wait a bit and retry
    setTimeout(() => {
      if (typeof window.createUnifiedItemCard === 'function') {
        renderItems(container, items, type, year, week);
      } else {
        console.error('window.createUnifiedItemCard still not available after wait');
      }
    }, 100);
    return;
  }
  
  // Use current week context if not provided
  const itemYear = year || window.currentYear || new Date().getFullYear();
  const itemWeek = week || window.currentWeek || getISOWeekInfo(new Date()).weekNumber;
  
  items.forEach((item) => {
    // Use compact card format for all items
    // For posting_queue items (product, message), use posting_queue_id and check post_exists flag
    const postId = item.post_id || (item.post_exists ? item.posting_queue_id : null) || item.id;
    const postExists = !!(item.post_exists !== undefined ? item.post_exists : postId);
    // Use post_status if available, otherwise fall back to status field
    const postStatus = (item.post_status || item.status) ? (item.post_status || item.status).toLowerCase() : null;

    // Phase 5: Facebook Matrix v1 – Role-first, Angle-second labelling
    // Primary intent comes from Role; language/product/deep dive appear as angles.
    let primaryRole = item.role || null;
    let angleLabel = null;
    let typeName;

    if (type === 'idea') {
      typeName = 'Theme';
    } else if (type === 'recipe') {
      typeName = 'Recipe';
    } else if (type === 'profile') {
      typeName = 'Profile';
    } else if (type === 'weekly-word' || type === 'weekly-phrase' || type === 'weekly-insult') {
      // All weekly language content sits inside CULTURE slots for Matrix v1
      primaryRole = primaryRole || 'CULTURE';
      angleLabel = type === 'weekly-word'
        ? 'Language: Word'
        : type === 'weekly-phrase'
          ? 'Language: Phrase'
          : 'Language: Insult';
      typeName = angleLabel ? `${primaryRole} — ${angleLabel}` : primaryRole;
    } else if (type === 'product') {
      // Product posts are COMMERCE in Matrix v1
      primaryRole = primaryRole || 'COMMERCE';
      angleLabel = 'Product';
      typeName = `${primaryRole} — ${angleLabel}`;
    } else if (type === 'message') {
      // Messages are REASSURANCE in Matrix v1
      primaryRole = primaryRole || 'REASSURANCE';
      angleLabel = 'Message';
      typeName = `${primaryRole} — ${angleLabel}`;
    } else if (type === 'depth_long') {
      // Sunday Deep Dive – DEPTH_LONG role
      primaryRole = primaryRole || 'DEPTH_LONG';
      angleLabel = 'Deep Dive';
      typeName = `${primaryRole} — ${angleLabel}`;
    } else if (type === 'event') {
      typeName = item.event_recurrence_type === 'one_off' ? 'Special' : 'Annual';
    } else if (type === 'scheduled') {
      typeName = 'Syndication';
    } else {
      // Fallback: use role if present, otherwise raw type
      if (!primaryRole && item.role) {
        primaryRole = item.role;
      }
      typeName = primaryRole ? primaryRole.replace(/_/g, ' ') : type;
    }
    
    let title = item.title || item.theme_title || item.recipe_title || item.post_title || 'Untitled';
    // If multiple product posts for this day, add count indicator
    if (type === 'product' && item._multiple_count && item._multiple_count > 1) {
      title = `${title} (+${item._multiple_count - 1} more)`;
    }
    const description = item.description || item.theme_description || item.recipe_description || null;
    
    // Store year/week in item for info button
    item.year = item.year || itemYear;
    item.week = item.week || itemWeek;
    
    const card = window.createUnifiedItemCard(item, {
      type,
      category: type === 'idea' ? 'theme' : type,
      typeName,
      title,
      year: itemYear,
      week: itemWeek,
      onInfo: () => {
        // Item-specific info handling - open appropriate modal
        if (type === 'idea' || type === 'theme') {
          const itemId = item.id || item.theme_id || item.item_id;
          if (itemId) {
            const ideaModal = window.getIdeaModal ? window.getIdeaModal() : null;
            if (ideaModal) {
              ideaModal.openTheme(itemId);
              return;
            }
          }
        }
        if (type === 'profile') {
          const profileId = item.post_id || item.id;
          if (profileId) {
            const profileModal = window.getProfileModal ? window.getProfileModal() : null;
            if (profileModal) {
              profileModal.open(profileId);
              return;
            }
          }
        }
        if (type === 'recipe') {
          if (item.post_id) {
            // Navigate to pipeline (first workflow stage for recipes - drafting)
            if (window.navigateToPipeline && typeof window.navigateToPipeline === 'function') {
              window.navigateToPipeline(item, item.post_id);
            } else {
              // Fallback: navigate directly to drafting
              const y = item.year || itemYear;
              const w = item.week || itemWeek;
              let url = `/posts/${item.post_id}/sections/drafting`;
              if (y && w) {
                url += `?year=${y}&week=${w}`;
              }
              window.location.href = url;
            }
            return;
          } else if (item.id) {
            window.location.href = `/recipes`;
            return;
          }
        }
        if (type === 'event') {
          const eventId = item.id || item._eventId;
          if (eventId) {
            const ideaModal = window.getIdeaModal ? window.getIdeaModal() : null;
            if (ideaModal) {
              ideaModal.openEvent(eventId);
              return;
            }
          }
        }
        if (type === 'weekly-word' || type === 'weekly-phrase' || type === 'weekly-insult') {
          const itemId = item.item_id || item.id;
          if (itemId) {
            const ideaModal = window.getIdeaModal ? window.getIdeaModal() : null;
            if (ideaModal) {
              ideaModal.open(itemId);
              return;
            }
          }
        }
        // Fallback: navigate to week-view
        const y = item.year || itemYear;
        const w = item.week || itemWeek;
        window.location.href = `/planning/calendar?year=${y}&week=${w}&tab=week-view`;
      },
      onCreate: async (e, item, card) => {
        // Recipe: create post directly from calendar
        if (type === 'recipe' && typeof window.createRecipePostFromCalendar === 'function') {
          // Pass the full item so we can extract recipe_id, year, week
          await window.createRecipePostFromCalendar(item);
          return;
        }

        // Theme (week-view theme card): send user to Week Themes page for this week
        if (type === 'theme') {
          const y = item.year || itemYear;
          const w = item.week || itemWeek;
          window.location.href = `/planning/calendar/ideas/week/${w}?year=${y}&week=${w}`;
          return;
        }

        // Legacy idea type: open theme in idea modal
        if (type === 'idea' && item.id) {
          const ideaModal = window.getIdeaModal ? window.getIdeaModal() : null;
          if (ideaModal) {
            ideaModal.openTheme(item.id);
          }
        }
      },
      onClick: (e, item, card) => {
        // Item-specific click handlers
        if (type === 'idea' && item.id) {
          const ideaModal = window.getIdeaModal ? window.getIdeaModal() : null;
          if (ideaModal) ideaModal.openTheme(item.id);
        } else if (type === 'profile' && (item.post_id || item.id)) {
          const profileModal = window.getProfileModal ? window.getProfileModal() : null;
          if (profileModal) profileModal.open(item.post_id || item.id);
        } else if (type === 'recipe' && item.id) {
          // Recipe click handler
        } else if (type === 'event' && (item.id || item._eventId)) {
          const ideaModal = window.getIdeaModal ? window.getIdeaModal() : null;
          if (ideaModal) ideaModal.openEvent(item.id || item._eventId);
        }
      }
    });
    
    // Store original item data
    card.dataset.itemType = type;
    if (item.id) card.dataset.itemId = item.id;
    if (postId) card.dataset.postId = postId;
    
    console.log('Appending card to container:', container.id || container.className, 'card type:', type, 'title:', title);
    container.appendChild(card);
    console.log('Card appended, container now has', container.children.length, 'children');
  });
}

function renderAdvanceNotice(event, weekDates, year, weekNumber) {
  // Calculate advance notice period
  if (!event.advance_notice || event.advance_notice <= 0 || !event.start_date) return;
  
  const eventStartDate = new Date(event.start_date);
  // Normalize to midnight UTC for date-only comparison
  eventStartDate.setUTCHours(0, 0, 0, 0);
  
  // Calculate the start of the advance notice period (advance_notice weeks before event)
  // advance_notice is in weeks, so multiply by 7 to get days
  // Use setTime to avoid issues with setUTCDate when crossing month boundaries
  const advanceStart = new Date(eventStartDate);
  advanceStart.setTime(eventStartDate.getTime() - (event.advance_notice * 7 * 24 * 60 * 60 * 1000));
  advanceStart.setUTCHours(0, 0, 0, 0);
  
  // Calculate the end of the advance notice period (day before event)
  const advanceEnd = new Date(eventStartDate);
  advanceEnd.setUTCDate(eventStartDate.getUTCDate() - 1);
  advanceEnd.setUTCHours(23, 59, 59, 999);
  
  
  // Check if any part of the advance notice period falls within this week
  const weekStart = new Date(weekDates[0]);
  weekStart.setUTCHours(0, 0, 0, 0);
  const weekEnd = new Date(weekDates[6]);
  weekEnd.setUTCHours(23, 59, 59, 999);
  
  // If advance notice period doesn't overlap with this week, skip
  if (advanceEnd.getTime() < weekStart.getTime() || advanceStart.getTime() > weekEnd.getTime()) return;
  
  const eventTitle = event.event_title || 'Untitled Event';
  
  // Render advance notice for each day in this week that's in the advance notice period
  weekDates.forEach((date, dayIndex) => {
    const dayOfWeek = dayIndex + 1; // 1-7 (Mon-Sun)
    
    // Normalize date to midnight for comparison
    const dayDate = new Date(date);
    dayDate.setUTCHours(0, 0, 0, 0);
    
    // Check if this day is in the advance notice period (before event date, on or after advance start)
    if (dayDate.getTime() >= advanceStart.getTime() && dayDate.getTime() <= advanceEnd.getTime()) {
      // Determine which row to render advance notice in based on event recurrence type
      const rowPrefix = event.event_recurrence_type === 'one_off' ? 'special-events-row' : 'annual-events-row';
      const target = document.getElementById(`${rowPrefix}-day-${dayOfWeek}`);
      if (!target) return;
      
      // Determine if this is the "start" button day
      // Priority 1: If this IS the actual advance start date, it always gets the start button
      // Priority 2: If the actual advance start is NOT in this week, show start button on first day in THIS week
      
      const isActualAdvanceStart = dayDate.getTime() === advanceStart.getTime();
      
      // Check if the actual advance start date is anywhere in this week
      const advanceStartInThisWeek = weekDates.some(d => {
        const dNorm = new Date(d);
        dNorm.setUTCHours(0, 0, 0, 0);
        return dNorm.getTime() === advanceStart.getTime();
      });
      
      // If this IS the actual advance start date, it always gets the start button
      if (isActualAdvanceStart) {
        const advanceDiv = document.createElement('div');
        advanceDiv.className = 'item advance-notice advance-start';
        advanceDiv.dataset.eventId = event.id;
        advanceDiv.style.cursor = 'pointer';
        advanceDiv.title = `${eventTitle} - Advance notice (${event.advance_notice} weeks ahead)`;
        advanceDiv.innerHTML = `<span class="advance-name">${escapeHtml(eventTitle)}</span> <span class="advance-arrow">→</span>`;
        target.appendChild(advanceDiv);
        
        advanceDiv.addEventListener('click', (clickEvent) => {
          clickEvent.stopPropagation();
          const eventData = window.currentWeekEvents?.find(ev => ev.id === event.id);
          if (eventData) {
            const ideaModal = window.getIdeaModal ? window.getIdeaModal() : null;
            if (ideaModal) {
              ideaModal.open(null, eventData);
            }
          }
        });
        return; // Don't render intermediate items for this day if it's the actual start
      }
      
      // For all other days in the advance notice period, only show intermediate text
      // The start button ONLY appears on the actual advance start date (handled above)
      const isFirstDay = false;
      
      const advanceDiv = document.createElement('div');
      advanceDiv.className = 'item advance-notice';
      advanceDiv.dataset.eventId = event.id;
      advanceDiv.style.cursor = 'pointer';
      advanceDiv.title = `${eventTitle} - Advance notice (${event.advance_notice} weeks ahead)`;
      
      if (isFirstDay) {
        // Small button at the start of the period
        advanceDiv.className += ' advance-start';
        advanceDiv.innerHTML = `<span class="advance-name">${escapeHtml(eventTitle)}</span> <span class="advance-arrow">→</span>`;
      } else {
        // Small text with arrow for intermediate days
        advanceDiv.className += ' advance-intermediate';
        advanceDiv.innerHTML = `<span class="advance-text">${escapeHtml(eventTitle)}</span> <span class="advance-arrow">→</span>`;
      }
      
      target.appendChild(advanceDiv);
      
      // Add click handler to open event modal
      advanceDiv.addEventListener('click', (clickEvent) => {
        clickEvent.stopPropagation();
        const eventData = window.currentWeekEvents?.find(ev => ev.id === event.id);
        if (eventData) {
          const ideaModal = window.getIdeaModal ? window.getIdeaModal() : null;
          if (ideaModal) {
            ideaModal.open(null, eventData);
          }
        }
      });
    }
  });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

async function loadWeek(year, weekNumber) {
  console.log('[loadWeek] ===== CALLED =====');
  console.log('[loadWeek] Parameters:', { year, weekNumber });
  console.log('[loadWeek] window.createUnifiedItemCard available:', typeof window.createUnifiedItemCard);
  
  const weekYearEl = document.getElementById('week-year');
  const weekNumberEl = document.getElementById('week-number');
  
  if (!weekYearEl || !weekNumberEl) {
    console.error('[loadWeek] Week view elements not found, cannot load week');
    return;
  }
  
  console.log('[loadWeek] Setting week-year to:', year);
  console.log('[loadWeek] Setting week-number to:', weekNumber);
  weekYearEl.textContent = String(year);
  weekNumberEl.textContent = String(weekNumber);
  console.log('[loadWeek] After setting - week-year text:', weekYearEl.textContent);
  console.log('[loadWeek] After setting - week-number text:', weekNumberEl.textContent);
  
  // SINGLE SOURCE OF TRUTH: Update URL using WeekContext
  if (window.WeekContext) {
    window.WeekContext.setWeekContext(year, weekNumber);
  }
  
  
  // Clear the linksUpdated flag when week changes so links get re-updated
  if (typeof blogPipelineHeader !== 'undefined') {
    blogPipelineHeader.linksUpdated = false;
  }
  
  // Update nav links AFTER URL is updated and flag is cleared
  setTimeout(() => {
    if (typeof blogPipelineHeader !== 'undefined' && blogPipelineHeader.attachWeekParameterToNavLinks) {
      blogPipelineHeader.attachWeekParameterToNavLinks();
    }
  }, 50);
  
  // Update header week info and theme
  if (typeof blogPipelineHeader !== 'undefined' && blogPipelineHeader.updateWeekAndTheme) {
    await blogPipelineHeader.updateWeekAndTheme();
  }
  
  // Update Week Ideas link to point to current viewed week
  if (typeof setWeekIdeasLink === 'function') {
    setWeekIdeasLink();
  }

  const weekStart = getWeekStartDate(year, weekNumber);
  const dates = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(weekStart);
    d.setUTCDate(weekStart.getUTCDate() + i);
    dates.push(d);
    // Update day header title to include calendar day number on the right
    const dayEl = document.querySelector(`.day-header[data-day="${i + 1}"]`);
    const header = dayEl?.querySelector('.day-title');
    if (header) {
      const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
      const label = dayNames[i] || '';
      const dayNum = String(d.getUTCDate());
      header.innerHTML = `${label}<span class="day-num">${dayNum}</span>`;
    }
  }
  const weekDatesEl = document.getElementById('week-dates');
  if (weekDatesEl) {
    weekDatesEl.textContent = `${formatDate(dates[0])} – ${formatDate(dates[6])}`;
  }
  
  // Load and display KB topic for this week
  await loadWeekTopic(year, weekNumber);

  // Load data in parallel
  const ideasPromise = fetchJSON(`/planning/api/calendar/ideas/week/${weekNumber}`); // week-only
  const eventsPromise = fetchJSON(`/planning/api/calendar/events/${year}/${weekNumber}`);
  const schedulePromise = fetchJSON(`/planning/api/calendar/schedule/${year}/${weekNumber}`);
  // Fetch both product and blog_post syndication schedules
  const productSyndicationPromise = fetchJSON(`/launchpad/api/syndication/schedules?platform=facebook&content_type=product`);
  const blogPostSyndicationPromise = fetchJSON(`/launchpad/api/syndication/schedules?platform=facebook&content_type=blog_post`);
  // Fetch weekly social focus
  const socialFocusPromise = fetchJSON(`/planning/api/social-focus/week`);
  // Fetch profiles for this week
  const profilesPromise = fetchJSON(`/planning/api/calendar/profiles/${year}/${weekNumber}`);
  // Fetch recipes for this week
  const recipesPromise = fetchJSON(`/planning/api/calendar/recipes/${year}/${weekNumber}`);

  let ideas = [];
  let events = [];
  let schedule = [];
  let syndication = [];
  let socialFocuses = [];
  let profiles = [];
  let recipes = [];
  try {
    const [ideasRes, eventsRes, scheduleRes, productSyndicationRes, blogPostSyndicationRes, socialFocusRes, profilesRes, recipesRes] = await Promise.allSettled([ideasPromise, eventsPromise, schedulePromise, productSyndicationPromise, blogPostSyndicationPromise, socialFocusPromise, profilesPromise, recipesPromise]);
    if (ideasRes.status === 'fulfilled') {
      const ideasData = ideasRes.value;
      ideas = Array.isArray(ideasData) ? ideasData : (ideasData?.ideas || []);
    }
    if (eventsRes.status === 'fulfilled') {
      const eventsData = eventsRes.value;
      events = Array.isArray(eventsData) ? eventsData : (eventsData?.events || []);
    }
    if (scheduleRes.status === 'fulfilled') {
      const scheduleData = scheduleRes.value;
      schedule = Array.isArray(scheduleData) ? scheduleData : (scheduleData?.schedule || []);
      // Store full scheduleData for theme lookup (includes selected_theme_id at top level)
      window.currentScheduleData = scheduleData;
      console.log('Schedule data loaded:', {
        isArray: Array.isArray(scheduleData),
        hasSchedule: !!scheduleData?.schedule,
        scheduleLength: schedule.length,
        selected_theme_id: scheduleData?.selected_theme_id,
        scheduleDataKeys: scheduleData ? Object.keys(scheduleData) : []
      });
    }
    // Combine product and blog_post syndication schedules
    const productSchedules = productSyndicationRes.status === 'fulfilled' ? (productSyndicationRes.value.schedules || []) : [];
    const blogPostSchedules = blogPostSyndicationRes.status === 'fulfilled' ? (blogPostSyndicationRes.value.schedules || []) : [];
    syndication = [...productSchedules, ...blogPostSchedules].filter(s => s && s.is_active !== false);
    
    // Load social focus data
    if (socialFocusRes.status === 'fulfilled') {
      const socialFocusData = socialFocusRes.value;
      if (socialFocusData && socialFocusData.success && socialFocusData.focuses) {
        socialFocuses = socialFocusData.focuses;
      }
    }
    // Load profiles data
    if (profilesRes.status === 'fulfilled') {
      const profilesData = profilesRes.value;
      profiles = Array.isArray(profilesData) ? profilesData : (profilesData?.profiles || []);
    }
    // Load recipes data
    if (recipesRes.status === 'fulfilled') {
      const recipesData = recipesRes.value;
      // Handle both array response and object with error
      if (Array.isArray(recipesData)) {
        recipes = recipesData;
      } else if (recipesData?.recipes) {
        recipes = recipesData.recipes;
      } else if (recipesData?.error) {
        console.warn('Recipes API error:', recipesData.error);
        recipes = [];
      } else {
        recipes = [];
      }
    }
  } catch (e) {
    console.error('Error loading week data:', e);
    console.error('Stack trace:', e.stack);
    // Ignore; page still usable
  }
  
  // Check if we have the required row containers
  const blogRow = document.getElementById('blog-row');
  const socialPostsRow = document.getElementById('social-posts-row');
  const annualEventsRow = document.getElementById('annual-events-row');
  const specialEventsRow = document.getElementById('special-events-row');
  const syndicationRow = document.getElementById('syndication-row');
  
  if (!blogRow || !socialPostsRow || !annualEventsRow || !specialEventsRow || !syndicationRow) {
    console.error('Required row containers not found:', {
      blogRow: !!blogRow,
      socialPostsRow: !!socialPostsRow,
      annualEventsRow: !!annualEventsRow,
      specialEventsRow: !!specialEventsRow,
      syndicationRow: !!syndicationRow
    });
    return;
  }

  // Get filter toggles
  const toggleBlog = document.getElementById('toggle-blog');
  const showBlog = toggleBlog?.checked !== false;
  console.log('Filter toggles:', {
    toggleBlog: !!toggleBlog,
    showBlog,
    toggleBlogChecked: toggleBlog?.checked
  });
  const showAnnualEvents = document.getElementById('toggle-annual-events')?.checked !== false;
  const showSpecialEvents = document.getElementById('toggle-special-events')?.checked !== false;
  const showSyndication = document.getElementById('toggle-syndication')?.checked !== false;
  const showSocialPosts = document.getElementById('toggle-social-posts')?.checked !== false;

  // Build row grids cells for rows container
  const ensureRowCells = (rowId) => {
    const row = document.getElementById(rowId);
    console.log(`ensureRowCells called for ${rowId}, row found:`, !!row);
    if (!row) {
      console.error(`Row ${rowId} not found!`);
      return null;
    }
    row.innerHTML = '';
    const cells = [];
    for (let i = 1; i <= 7; i++) {
      const cell = document.createElement('div');
      cell.className = 'row-cell';
      cell.id = `${rowId}-day-${i}`;
      row.appendChild(cell);
      cells.push(cell);
    }
    console.log(`Created ${cells.length} cells for ${rowId}`);
    // Verify cells were created
    for (let i = 1; i <= 7; i++) {
      const checkCell = document.getElementById(`${rowId}-day-${i}`);
      if (!checkCell) {
        console.error(`Cell ${rowId}-day-${i} was not created!`);
      }
    }
    return cells;
  };

  console.log('About to create row cells');
  const blogCells = ensureRowCells('blog-row');
  console.log('blogCells created:', blogCells ? blogCells.length : 'null');
  const annualEventsCells = ensureRowCells('annual-events-row');
  const specialEventsCells = ensureRowCells('special-events-row');
  const syndicationCells = ensureRowCells('syndication-row');
  const socialPostsCells = ensureRowCells('social-posts-row');

  // Load themes from schedule (themes scheduled for this week)
  // NEW SYSTEM: Uses cyclic position-based logic (same as scheduling calendar)
  // DEPRECATED: Old week_number-based theme lookup is no longer used
  const themes = [];
  const scheduledThemeIds = new Set();
  
  // Get scheduleData from window (set earlier in loadWeek)
  const scheduleData = window.currentScheduleData || {};
  console.log('Building themes from scheduleData:', {
    hasScheduleData: !!scheduleData,
    selected_theme_id: scheduleData?.selected_theme_id,
    scheduleLength: schedule?.length || 0
  });
  
  // Check for selected_theme_id at top level (from new cyclic system)
  if (scheduleData && scheduleData.selected_theme_id) {
    const themeId = scheduleData.selected_theme_id;
    console.log('Found selected_theme_id:', themeId);
    if (!scheduledThemeIds.has(themeId)) {
      scheduledThemeIds.add(themeId);
      // Find the theme entry in schedule array to get title
      const themeEntry = schedule && Array.isArray(schedule) 
        ? schedule.find(s => (s.theme_id === themeId || s.selected_theme_id === themeId) && s.type === 'theme_selection')
        : null;
      console.log('Theme entry found in schedule:', themeEntry);
      
      themes.push({
        id: themeId,
        theme_title: themeEntry?.theme_title || 'Theme',
        theme_description: themeEntry?.theme_description,
        post_id: themeEntry?.post_id || null,
        post_status: themeEntry?.post_status || null,
        _selected: true,
        _fromSchedule: true,
        _from_cyclic_system: true
      });
      console.log('Added theme to themes array, themes.length:', themes.length);
    }
  }
  
  // Also check schedule array for theme_selection entries (new cyclic system format)
  if (schedule && Array.isArray(schedule)) {
    schedule.forEach(s => {
      // Check if schedule entry has a theme (theme_id, selected_theme_id, or theme_title)
      if (s.type === 'theme_selection' || s.theme_id || s.selected_theme_id || s.calendar_theme_id || s.theme_title) {
        const themeId = s.theme_id || s.selected_theme_id || s.calendar_theme_id;
        if (themeId && !scheduledThemeIds.has(themeId)) {
          scheduledThemeIds.add(themeId);
          themes.push({
            id: themeId,
            theme_title: s.theme_title || 'Unknown Theme',
            theme_description: s.theme_description,
            post_id: s.post_id || null,
            post_status: s.post_status || null,
            _selected: true,
            _fromSchedule: true,
            _from_cyclic_system: s._from_cyclic_system || false
          });
        }
      }
    });
  }
  
  // DEPRECATED: Old themes/week API now uses cyclic system too
  // Fetch theme for this week from themes API (now uses cyclic calculation)
  let perpetualThemesPromise = null;
  try {
    perpetualThemesPromise = fetchJSON(`/planning/api/calendar/themes/week/${weekNumber}?year=${year}`);
  } catch (e) {
    console.warn('Themes API not available yet:', e);
  }
  
  let perpetualThemes = [];
  if (perpetualThemesPromise) {
    try {
      const perpetualRes = await perpetualThemesPromise;
      const perpetualData = perpetualRes?.themes || [];
      perpetualThemes = Array.isArray(perpetualData) ? perpetualData : [];
      
      // Add perpetual themes that aren't already in scheduled themes
      // Note: These now come from cyclic system, not week_number lookup
      perpetualThemes.forEach(pt => {
        if (!scheduledThemeIds.has(pt.id)) {
          themes.push({
            ...pt,
            _selected: false,
            _fromSchedule: false,
            _from_cyclic_system: pt._from_cyclic_system || false
          });
        }
      });
    } catch (e) {
      console.warn('Error loading perpetual themes:', e);
    }
  }
  
  // Get weekly word, phrase, and insult from schedule (new cyclic system)
  let selectedWord = null;
  let selectedPhrase = null;
  let selectedInsult = null;
  let productPosts = []; // Product posts for social posts row
  
  if (schedule && Array.isArray(schedule)) {
    selectedWord = schedule.find(s => s.type === 'weekly_word') || null;
    selectedPhrase = schedule.find(s => s.type === 'weekly_phrase') || null;
    selectedInsult = schedule.find(s => s.type === 'weekly_insult') || null;
    // Filter product posts (type === 'product')
    productPosts = schedule.filter(s => s.type === 'product') || [];
  }

  // Toggle row visibility based on filters
  const blogSections = document.querySelectorAll('[data-filter="blog"]');
  const annualEventsSections = document.querySelectorAll('[data-filter="annual-events"]');
  const specialEventsSections = document.querySelectorAll('[data-filter="special-events"]');
  const syndicationSections = document.querySelectorAll('[data-filter="syndication"]');
  const socialPostsSections = document.querySelectorAll('[data-filter="social-posts"]');
  
  blogSections.forEach(section => section.classList.toggle('hidden', !showBlog));
  annualEventsSections.forEach(section => section.classList.toggle('hidden', !showAnnualEvents));
  specialEventsSections.forEach(section => section.classList.toggle('hidden', !showSpecialEvents));
  syndicationSections.forEach(section => section.classList.toggle('hidden', !showSyndication));
  socialPostsSections.forEach(section => section.classList.toggle('hidden', !showSocialPosts));

  // Ideas row removed - no longer rendering regular ideas

  // Split events into annual and special based on event_recurrence_type
  const annualEvents = [];
  const specialEvents = [];
  events.forEach((ev) => {
    // event_recurrence_type: 'annual' = annual, 'one_off' = special, null/undefined = annual (default/legacy)
    const recurrenceType = ev.event_recurrence_type;
    if (recurrenceType === 'one_off') {
      specialEvents.push(ev);
    } else {
      // Default to annual for null/undefined or explicit 'annual'
      annualEvents.push(ev);
    }
  });

  // Store events globally for click handler access
  window.currentWeekEvents = events;

  // Render annual events per day into Annual Events row
  if (showAnnualEvents && annualEventsCells) {
    annualEvents.forEach((ev) => {
      // Only render the main event icon if the event's actual date is in this week
      const eventStartDate = ev.start_date ? new Date(ev.start_date) : null;
      if (eventStartDate) {
        eventStartDate.setUTCHours(0, 0, 0, 0);
        const weekStartDate = new Date(dates[0]);
        weekStartDate.setUTCHours(0, 0, 0, 0);
        const weekEndDate = new Date(dates[6]);
        weekEndDate.setUTCHours(23, 59, 59, 999);
        
        // Check if the event's actual date falls within this week
        const eventInThisWeek = eventStartDate.getTime() >= weekStartDate.getTime() && 
                                eventStartDate.getTime() <= weekEndDate.getTime();
        
        if (eventInThisWeek) {
          // Only render the main event icon if the event date is actually in this week
          const dayIdx = ev.weekday || ev.day || 1; // 1..7
          const target = document.getElementById(`annual-events-row-day-${Math.min(Math.max(dayIdx, 1), 7)}`);
          renderItems(target, [ev], 'event', year, weekNumber);
        }
      } else {
        // Fallback: render if no start_date (shouldn't happen, but handle gracefully)
        const dayIdx = ev.weekday || ev.day || 1; // 1..7
        const target = document.getElementById(`annual-events-row-day-${Math.min(Math.max(dayIdx, 1), 7)}`);
        renderItems(target, [ev], 'event', year, weekNumber);
      }
      
      // Always render advance notice period if the event has one
      // (this will only show indicators for days in the advance period, not the main event)
      if (ev.advance_notice && ev.start_date) {
        renderAdvanceNotice(ev, dates, year, weekNumber);
      }
    });
  }

  // Render special events per day into Special Events row
  if (showSpecialEvents && specialEventsCells) {
    specialEvents.forEach((ev) => {
      // Only render the main event icon if the event's actual date is in this week
      const eventStartDate = ev.start_date ? new Date(ev.start_date) : null;
      if (eventStartDate) {
        eventStartDate.setUTCHours(0, 0, 0, 0);
        const weekStartDate = new Date(dates[0]);
        weekStartDate.setUTCHours(0, 0, 0, 0);
        const weekEndDate = new Date(dates[6]);
        weekEndDate.setUTCHours(23, 59, 59, 999);
        
        // Check if the event's actual date falls within this week
        const eventInThisWeek = eventStartDate.getTime() >= weekStartDate.getTime() && 
                                eventStartDate.getTime() <= weekEndDate.getTime();
        
        if (eventInThisWeek) {
          // Only render the main event icon if the event date is actually in this week
          const dayIdx = ev.weekday || ev.day || 1; // 1..7
          const target = document.getElementById(`special-events-row-day-${Math.min(Math.max(dayIdx, 1), 7)}`);
          renderItems(target, [ev], 'event', year, weekNumber);
        }
      } else {
        // Fallback: render if no start_date (shouldn't happen, but handle gracefully)
        const dayIdx = ev.weekday || ev.day || 1; // 1..7
        const target = document.getElementById(`special-events-row-day-${Math.min(Math.max(dayIdx, 1), 7)}`);
        renderItems(target, [ev], 'event', year, weekNumber);
      }
      
      // Always render advance notice period if the event has one
      // (this will only show indicators for days in the advance period, not the main event)
      if (ev.advance_notice && ev.start_date) {
        renderAdvanceNotice(ev, dates, year, weekNumber);
      }
    });
  }

  // Do not duplicate week themes into Ideas row; Ideas row reserved for non-week ideas (none yet)

  // Syndication schedules are recurring by weekday; render time per selected days
  if (showSyndication && syndication.length && syndicationCells) {
    // days in daily_posts_schedule are stored as JSON (likely numeric 1..7 or names). Normalize to numeric 1..7
    const normalizeDays = (days) => {
      if (!days) return [];
      if (Array.isArray(days)) return days.map(d => {
        if (typeof d === 'number') return d;
        const name = String(d).toLowerCase();
        const map = { monday:1, tuesday:2, wednesday:3, thursday:4, friday:5, saturday:6, sunday:7 };
        return map[name] || 1;
      });
      return [];
    };
    const toDisplayTime = (time) => {
      if (!time) return '';
      const [h, m] = String(time).split(':');
      const hour = parseInt(h || '0', 10);
      const ampm = hour >= 12 ? 'PM' : 'AM';
      const disp = hour === 0 ? 12 : (hour > 12 ? hour - 12 : hour);
      return `${disp}:${m || '00'} ${ampm}`;
    };
    syndication.forEach((s) => {
      const days = normalizeDays(s.days);
      const timeDisplay = toDisplayTime(s.time);
      days.forEach((d) => {
        const target = document.getElementById(`syndication-row-day-${Math.min(Math.max(d, 1), 7)}`);
        const operation = s.content_type === 'product' ? 'Product' : (s.content_type === 'blog_post' ? 'Blog' : (s.content_type || ''));
        const item = { 
          platform: s.platform || 'facebook', // Use platform for icon lookup
          channel: s.platform || 'Facebook', // Keep channel for compatibility
          content_type: s.content_type || 'product', // For URL generation
          operation: operation, 
          time_display: timeDisplay, 
          name: s.name || '', 
          _syndication: true 
        };
        renderItems(target, [item], 'scheduled', year, weekNumber);
      });
    });
  }
  
  // Render weekly words/phrases/insults and product posts into Social Posts row
  if (showSocialPosts && socialPostsCells) {
    // Word on Monday (day 1)
    if (selectedWord) {
      const wordTarget = document.getElementById('social-posts-row-day-1');
      if (wordTarget) {
        // Pass item as-is; renderItems will add "Word: " prefix and show description
        renderItems(wordTarget, [selectedWord], 'weekly-word', year, weekNumber);
      }
    }
    // Phrase on Wednesday (day 3)
    if (selectedPhrase) {
      const phraseTarget = document.getElementById('social-posts-row-day-3');
      if (phraseTarget) {
        // Pass item as-is; renderItems will add "Phrase: " prefix and show description
        renderItems(phraseTarget, [selectedPhrase], 'weekly-phrase', year, weekNumber);
      }
    }
    // Insult on Friday (day 5)
    if (selectedInsult) {
      const insultTarget = document.getElementById('social-posts-row-day-5');
      if (insultTarget) {
        // Pass item as-is; renderItems will add "Insult: " prefix and show description
        renderItems(insultTarget, [selectedInsult], 'weekly-insult', year, weekNumber);
      }
    }
    // Product posts - render on their actual scheduled_date
    // Group by day and show only one per day (the first one scheduled for that day)
    if (productPosts.length > 0) {
      // Group product posts by scheduled_date
      const postsByDay = {};
      productPosts.forEach((productPost) => {
        if (productPost.scheduled_date) {
          if (!postsByDay[productPost.scheduled_date]) {
            postsByDay[productPost.scheduled_date] = [];
          }
          postsByDay[productPost.scheduled_date].push(productPost);
        }
      });
      
      // Render one product post per day (the first one for that day)
      Object.keys(postsByDay).forEach((scheduledDate) => {
        const dayPosts = postsByDay[scheduledDate];
        if (dayPosts.length > 0) {
          // Use the first post for this day
          const productPost = dayPosts[0];
          
          try {
            const dateObj = new Date(scheduledDate + 'T00:00:00');
            // Get ISO weekday (1=Monday, 7=Sunday)
            // JavaScript getDay() returns 0=Sunday, 1=Monday, etc.
            const jsDay = dateObj.getDay();
            const dayIndex = jsDay === 0 ? 7 : jsDay; // Convert to ISO weekday (1=Mon, 7=Sun)
            
            const productTarget = document.getElementById(`social-posts-row-day-${dayIndex}`);
            if (productTarget) {
              // If multiple posts for this day, show count in title
              if (dayPosts.length > 1) {
                productPost._multiple_count = dayPosts.length;
              }
              renderItems(productTarget, [productPost], 'product', year, weekNumber);
            }
          } catch (e) {
            console.warn('Error parsing scheduled_date for product post:', scheduledDate, e);
          }
        }
      });
    }
    
    // Message posts - render on Saturday (day 6) only
    const messagePosts = schedule.filter(s => s.type === 'message');
    if (messagePosts.length > 0) {
      messagePosts.forEach((messagePost) => {
        if (messagePost.scheduled_date) {
          try {
            const dateObj = new Date(messagePost.scheduled_date + 'T00:00:00');
            // Get ISO weekday (1=Monday, 7=Sunday)
            const jsDay = dateObj.getDay();
            const dayIndex = jsDay === 0 ? 7 : jsDay; // Convert to ISO weekday (1=Mon, 7=Sun)
            
            // Messages should only be on Saturday (day 6)
            if (dayIndex === 6) {
              const messageTarget = document.getElementById(`social-posts-row-day-6`);
              if (messageTarget) {
                renderItems(messageTarget, [messagePost], 'message', year, weekNumber);
              }
            }
          } catch (e) {
            console.warn('Error parsing scheduled_date for message post:', messagePost.scheduled_date, e);
          }
        }
      });
    }
    
    // Role-based posts (e.g., DEPTH_LONG Sunday Deep Dive) - render on their scheduled_date
    const rolePosts = schedule.filter(s => s.role && s.posting_queue_id);
    if (rolePosts.length > 0) {
      rolePosts.forEach((rolePost) => {
        if (rolePost.scheduled_date) {
          try {
            const dateObj = new Date(rolePost.scheduled_date + 'T00:00:00');
            // Get ISO weekday (1=Monday, 7=Sunday)
            const jsDay = dateObj.getDay();
            const dayIndex = jsDay === 0 ? 7 : jsDay; // Convert to ISO weekday (1=Mon, 7=Sun)
            
            const roleTarget = document.getElementById(`social-posts-row-day-${dayIndex}`);
            if (roleTarget) {
              // Use role as type (e.g., 'depth_long') for rendering
              const roleType = rolePost.role.toLowerCase();
              renderItems(roleTarget, [rolePost], roleType, year, weekNumber);
            }
          } catch (e) {
            console.warn('Error parsing scheduled_date for role-based post:', rolePost.scheduled_date, e);
          }
        }
      });
    }
  }
  
  // Render consolidated Blog row: Theme (Mon), Recipe (Wed), Surname profile (Fri), Product profile (Sat)
  console.log('Checking if should render blog row:', { showBlog, blogCells: !!blogCells, blogCellsLength: blogCells?.length });
  if (showBlog && blogCells) {
    console.log('Rendering blog row, themes:', themes.length, 'schedule items:', schedule.length);
    // Theme for Monday
    const themeEntry = themes[0];
    if (themeEntry) {
      const target = document.getElementById('blog-row-day-1');
      console.log('Theme entry found:', themeEntry, 'target element:', !!target);
      if (target) {
        const themeItem = {
          id: themeEntry.id,
          title: themeEntry.theme_title || 'Theme',
          post_id: themeEntry.post_id || null,
          post_status: themeEntry.post_status || null,
          _theme: true
        };
        console.log('Calling renderItems for theme');
        renderItems(target, [themeItem], 'theme', year, weekNumber);
      } else {
        console.error('blog-row-day-1 element not found!');
      }
    } else {
      console.log('No theme entry found, themes array:', themes);
    }

    // Recipe for Wednesday
    const scheduleRecipe = schedule.find(s => s.type === 'recipe' || s.recipe_id || s.recipe_title) || recipes[0];
    if (scheduleRecipe) {
      const target = document.getElementById('blog-row-day-3');
      if (target) {
        const recipeItem = {
          id: scheduleRecipe.id || scheduleRecipe.recipe_id,
          recipe_id: scheduleRecipe.recipe_id || scheduleRecipe.id, // Ensure recipe_id is set
          post_id: scheduleRecipe.post_id || null, // Include post_id if recipe has a post
          title: scheduleRecipe.recipe_title || scheduleRecipe.title || 'Recipe',
          recipe_week_number: scheduleRecipe.recipe_week_number,
          _recipe: true,
          _definition: false, // Recipes from schedule are never definitions - they're scheduled items
          _scheduled: true
        };
        renderItems(target, [recipeItem], 'recipe', year, weekNumber);
      }
    }

    // Surname profile for Friday
    const surnameProfile = schedule.find(s => (s.type === 'post' && s.profile_type === 'surname')) || profiles.find(p => (p.profile_type === 'surname'));
    if (surnameProfile) {
      const target = document.getElementById('blog-row-day-5');
      if (target) {
        const profileItem = {
          id: surnameProfile.post_id || surnameProfile.id, // Use post_id as primary ID for profiles
          post_id: surnameProfile.post_id || surnameProfile.id, // Ensure post_id is set
          title: surnameProfile.post_title || surnameProfile.title || 'Surname Profile',
          profile_type: 'surname',
          _profile: true
        };
        renderItems(target, [profileItem], 'profile', year, weekNumber);
      }
    }

    // Product profile for Saturday
    const productProfile = schedule.find(s => (s.type === 'post' && s.profile_type === 'product')) || profiles.find(p => (p.profile_type === 'product'));
    if (productProfile) {
      const target = document.getElementById('blog-row-day-6');
      if (target) {
        const profileItem = {
          id: productProfile.post_id || productProfile.id, // Use post_id as primary ID for profiles
          post_id: productProfile.post_id || productProfile.id, // Ensure post_id is set
          title: productProfile.post_title || productProfile.title || 'Product Profile',
          profile_type: 'product',
          _profile: true
        };
        renderItems(target, [profileItem], 'profile', year, weekNumber);
      }
    }
  }
  
  // Render social focuses under day headers
  renderSocialFocuses(socialFocuses);
}

/**
 * Load and display KB topic for the current week
 */
async function loadWeekTopic(year, weekNumber) {
  console.log('[loadWeekTopic] ===== START =====');
  console.log('[loadWeekTopic] Loading topic for year:', year, 'week:', weekNumber);
  
  // Wait a bit for DOM to be ready if needed
  let topicEl = document.getElementById('week-topic');
  let topicNameEl = document.getElementById('week-topic-name');
  
  if (!topicEl || !topicNameEl) {
    console.warn('[loadWeekTopic] Topic elements not found immediately, waiting 100ms...');
    await new Promise(resolve => setTimeout(resolve, 100));
    topicEl = document.getElementById('week-topic');
    topicNameEl = document.getElementById('week-topic-name');
  }
  
  if (!topicEl || !topicNameEl) {
    console.error('[loadWeekTopic] Topic elements STILL not found after wait', { 
      topicEl: !!topicEl, 
      topicNameEl: !!topicNameEl,
      allElementsWithId: Array.from(document.querySelectorAll('[id*="topic"]')).map(el => el.id)
    });
    return; // Elements not found, skip
  }
  
  console.log('[loadWeekTopic] Elements found:', { topicEl: !!topicEl, topicNameEl: !!topicNameEl });
  
  try {
    // Construct URL - use relative path which should work from any page
    const url = `/api/kb-topics/rota?year=${year}&week=${weekNumber}`;
    const fullUrl = window.location.origin + url;
    console.log('[loadWeekTopic] Fetching URL:', fullUrl);
    console.log('[loadWeekTopic] Current page:', window.location.href);
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      credentials: 'same-origin'
    });
    
    console.log('[loadWeekTopic] Response status:', response.status, response.statusText);
    console.log('[loadWeekTopic] Response URL:', response.url);
    
    if (!response.ok) {
      // 404 or other error - no topic for this week
      const errorText = await response.text().catch(() => '');
      console.log('[loadWeekTopic] No topic found (status:', response.status, ')', errorText);
      topicEl.style.display = 'none';
      return;
    }
    
    const data = await response.json();
    console.log('[loadWeekTopic] Response:', data);
    
    if (data.success && data.topic && data.topic.name) {
      console.log('[loadWeekTopic] ✅ SUCCESS - Displaying topic:', data.topic.name);
      console.log('[loadWeekTopic] Topic element before:', topicEl.style.display);
      console.log('[loadWeekTopic] Topic element exists:', !!topicEl);
      console.log('[loadWeekTopic] Topic name element exists:', !!topicNameEl);
      
      topicNameEl.textContent = data.topic.name;
      topicEl.style.display = 'flex';
      
      console.log('[loadWeekTopic] Topic element after setting display:', topicEl.style.display);
      console.log('[loadWeekTopic] Topic element inline style:', topicEl.getAttribute('style'));
      console.log('[loadWeekTopic] Topic element computed style:', window.getComputedStyle(topicEl).display);
      console.log('[loadWeekTopic] Topic element visible:', topicEl.offsetParent !== null);
      console.log('[loadWeekTopic] Topic element textContent:', topicNameEl.textContent);
    } else {
      // No topic for this week
      console.log('[loadWeekTopic] ❌ No topic in response', data);
      topicEl.style.display = 'none';
    }
  } catch (error) {
    console.error('[loadWeekTopic] Error loading week topic:', error);
    topicEl.style.display = 'none';
  }
}

console.log('calendar-week-view.js module loaded');

(function init() {
  console.log('init() function called');
  
  // Wait for unified-item-card to be available
  if (typeof window.createUnifiedItemCard !== 'function') {
    console.log('Waiting for createUnifiedItemCard, retrying in 100ms...');
    setTimeout(init, 100);
    return;
  }
  
  // Check if week-view elements exist (only initialize if week-view tab is active)
  const weekViewContainer = document.querySelector('.calendar-week-view');
  if (!weekViewContainer) {
    console.log('Week view container not found, skipping initialization');
    return;
  }
  console.log('Week view container found');
  
  // Check for required elements - retry if not found (DOM might not be ready)
  const prevWeekBtn = document.getElementById('prev-week');
  const nextWeekBtn = document.getElementById('next-week');
  const weekYearEl = document.getElementById('week-year');
  const weekNumberEl = document.getElementById('week-number');
  
  if (!prevWeekBtn || !nextWeekBtn || !weekYearEl || !weekNumberEl) {
    console.log('Week view elements not found, retrying in 100ms...', {
      prevWeekBtn: !!prevWeekBtn,
      nextWeekBtn: !!nextWeekBtn,
      weekYearEl: !!weekYearEl,
      weekNumberEl: !!weekNumberEl
    });
    setTimeout(init, 100);
    return;
  }
  
  console.log('Week view elements found, proceeding with initialization');
  console.log('[init] Button check:', {
    prevWeekBtn: !!prevWeekBtn,
    nextWeekBtn: !!nextWeekBtn,
    nextWeekBtnId: nextWeekBtn?.id,
    nextWeekBtnVisible: nextWeekBtn ? window.getComputedStyle(nextWeekBtn).display !== 'none' : false
  });
  
  // SINGLE SOURCE OF TRUTH: Get week from URL parameters first
  const urlParams = new URLSearchParams(window.location.search);
  let year = parseInt(urlParams.get('year'));
  let week = parseInt(urlParams.get('week'));
  
  // If not in URL, fall back to current week
  if (!year || !week) {
    const now = new Date();
    const currentWeekInfo = getISOWeekInfo(now);
    year = year || currentWeekInfo.year;
    week = week || currentWeekInfo.weekNumber;
  }
  
  const state = {
    year: year,
    weekNumber: week
  };
  
  console.log('[init] Week from URL:', { year, week, urlYear: urlParams.get('year'), urlWeek: urlParams.get('week') });
  
  // Update WeekContext to match URL
  if (window.WeekContext) {
    window.WeekContext.setWeekContext(state.year, state.weekNumber);
  }
  
  // Clear the linksUpdated flag when week changes so links get re-updated
  if (typeof blogPipelineHeader !== 'undefined') {
    blogPipelineHeader.linksUpdated = false;
  }
  
  // Trigger header update
  if (typeof blogPipelineHeader !== 'undefined' && blogPipelineHeader.updateWeekAndTheme) {
    blogPipelineHeader.updateWeekAndTheme();
  }

  // Update nav links AFTER URL is set and flag is cleared
  setTimeout(() => {
    if (typeof blogPipelineHeader !== 'undefined' && blogPipelineHeader.attachWeekParameterToNavLinks) {
      blogPipelineHeader.attachWeekParameterToNavLinks();
    }
  }, 50);
  
  // Load initial week topic
  loadWeekTopic(state.year, state.weekNumber);

  prevWeekBtn.addEventListener('click', () => {
    // SINGLE SOURCE OF TRUTH: Get current week from WeekContext
    const currentWeek = window.WeekContext ? window.WeekContext.getWeekContextWithDefault() : { year: state.year, week: state.weekNumber };
    const start = getWeekStartDate(currentWeek.year, currentWeek.week);
    start.setUTCDate(start.getUTCDate() - 7);
    const info = getISOWeekInfo(start);
    loadWeek(info.year, info.weekNumber);
  });

  // Add click handler with better error handling
  if (nextWeekBtn) {
    console.log('[init] Attaching click handler to next-week button');
    nextWeekBtn.addEventListener('click', (e) => {
      console.log('[nextWeekBtn] ===== CLICKED VIA ADDEVENTLISTENER =====');
      console.log('[nextWeekBtn] Event:', e);
      e.preventDefault();
      e.stopPropagation();
      window.nextWeekClick();
    });
    // Create a global function that can be called from onclick
    window.nextWeekClick = function() {
      console.log('[nextWeekBtn] ===== CLICKED VIA GLOBAL FUNCTION =====');
      try {
        const currentWeek = window.WeekContext ? window.WeekContext.getWeekContextWithDefault() : { year: state.year, week: state.weekNumber };
        console.log('[nextWeekBtn] Current week:', currentWeek);
        const start = getWeekStartDate(currentWeek.year, currentWeek.week);
        start.setUTCDate(start.getUTCDate() + 7);
        const info = getISOWeekInfo(start);
        console.log('[nextWeekBtn] Navigating to:', info);
        loadWeek(info.year, info.weekNumber);
      } catch (error) {
        console.error('[nextWeekBtn] Error:', error);
      }
    };
    
    console.log('[init] Click handler attached to next-week button');
  } else {
    console.error('[init] nextWeekBtn not found, cannot attach click handler');
  }

  // "This week" button - recalculate current week from today's date
  const thisWeekBtn = document.getElementById('this-week-btn');
  if (thisWeekBtn) {
    thisWeekBtn.addEventListener('click', () => {
      // Use WeekContext's standard ISO week calculation if available
      const now = new Date();
      let currentWeekInfo;
      if (window.WeekContext && window.WeekContext.getISOWeekInfo) {
        currentWeekInfo = window.WeekContext.getISOWeekInfo(now);
      } else {
        currentWeekInfo = getISOWeekInfo(now);
      }
      
      // Get current URL to check if we're already on this week
      const currentUrl = new URL(window.location.href);
      const currentYear = parseInt(currentUrl.searchParams.get('year') || '0');
      const currentWeek = parseInt(currentUrl.searchParams.get('week') || '0');
      
      // Build new URL - use unified calendar route
      const newUrl = `/planning/calendar?year=${currentWeekInfo.year}&week=${currentWeekInfo.weekNumber}&tab=week-view`;
      
      // If we're already on this week, force a reload by calling loadWeek directly
      if (currentYear === currentWeekInfo.year && currentWeek === currentWeekInfo.weekNumber) {
        // Force reload by calling loadWeek directly
        loadWeek(currentWeekInfo.year, currentWeekInfo.weekNumber);
      } else {
        // Navigate to new week
        window.location.href = newUrl;
      }
    });
  }

  // Week picker - month/week list interface
  const pickerBtn = document.getElementById('week-picker-btn');
  const pickerPopup = document.getElementById('week-picker-popup');
  const pickerCancel = document.getElementById('week-picker-cancel');
  const pickerYear = document.getElementById('picker-year');
  const pickerYearPrev = document.getElementById('picker-year-prev');
  const pickerYearNext = document.getElementById('picker-year-next');
  const pickerMonths = document.getElementById('week-picker-months');
  
  if (!pickerBtn || !pickerPopup || !pickerCancel || !pickerYear || !pickerYearPrev || !pickerYearNext || !pickerMonths) {
    console.log('Week picker elements not found, skipping picker initialization');
  } else {
  
  let selectedPickerYear = state.year;

  // Function to get weeks for a month
  function getWeeksForMonth(year, month) {
    const weeks = [];
    const monthStart = new Date(Date.UTC(year, month, 1));
    const monthEnd = new Date(Date.UTC(year, month + 1, 0));
    
    // Find the week containing the first day of the month
    const firstWeekInfo = getISOWeekInfo(monthStart);
    let currentWeek = firstWeekInfo.weekNumber;
    let currentYear = firstWeekInfo.year;
    
    // If the first day is late in the week, might need previous week too
    const weekStart = getWeekStartDate(currentYear, currentWeek);
    if (weekStart.getUTCMonth() < month) {
      // This week mostly belongs to previous month, start from next week
      const nextWeekStart = new Date(weekStart);
      nextWeekStart.setUTCDate(nextWeekStart.getUTCDate() + 7);
      const nextWeekInfo = getISOWeekInfo(nextWeekStart);
      currentWeek = nextWeekInfo.weekNumber;
      currentYear = nextWeekInfo.year;
    }
    
    // Collect all weeks that overlap with this month
    while (true) {
      const weekStartDate = getWeekStartDate(currentYear, currentWeek);
      const weekEndDate = new Date(weekStartDate);
      weekEndDate.setUTCDate(weekEndDate.getUTCDate() + 6);
      
      // Check if this week overlaps with the month
      if (weekStartDate.getUTCMonth() === month && weekStartDate.getUTCFullYear() === year ||
          weekEndDate.getUTCMonth() === month && weekEndDate.getUTCFullYear() === year ||
          (weekStartDate.getUTCMonth() < month && weekEndDate.getUTCMonth() >= month && weekStartDate.getUTCFullYear() === year) ||
          (weekStartDate.getUTCMonth() > month && weekEndDate.getUTCMonth() <= month && weekStartDate.getUTCFullYear() === year)) {
        const weekInfo = { week: currentWeek, year: currentYear, startDate: new Date(weekStartDate) };
        weeks.push(weekInfo);
      } else if (weekStartDate.getUTCMonth() > month && weekStartDate.getUTCFullYear() === year) {
        // We've passed the month
        break;
      }
      
      // Move to next week
      currentWeek++;
      if (currentWeek > 52) {
        currentWeek = 1;
        currentYear++;
        if (currentYear > year) break;
      }
      
      // Safety check to avoid infinite loop
      if (weeks.length > 10) break;
    }
    
    return weeks;
  }

  // Function to render months and weeks for a year
  function renderYearWeeks(year) {
    pickerMonths.innerHTML = '';
    selectedPickerYear = year;
    
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                        'July', 'August', 'September', 'October', 'November', 'December'];
    
    for (let month = 0; month < 12; month++) {
      const weeks = getWeeksForMonth(year, month);
      if (weeks.length === 0) continue;
      
      const monthDiv = document.createElement('div');
      monthDiv.className = 'week-picker-month';
      
      const header = document.createElement('div');
      header.className = 'week-picker-month-header';
      header.textContent = monthNames[month];
      monthDiv.appendChild(header);
      
      const weeksContainer = document.createElement('div');
      weeksContainer.className = 'week-picker-weeks';
      
      weeks.forEach(({ week, year: weekYear, startDate }) => {
        const weekBtn = document.createElement('button');
        weekBtn.className = 'week-picker-week';
        weekBtn.type = 'button';
        
        // Format: "Week X: DD MMM - DD MMM"
        const weekEnd = new Date(startDate);
        weekEnd.setUTCDate(weekEnd.getUTCDate() + 6);
        const startStr = formatDate(startDate);
        const endStr = formatDate(weekEnd);
        weekBtn.textContent = `Week ${week}: ${startStr} – ${endStr}`;
        
        // Highlight if this is the currently selected week
        if (weekYear === state.year && week === state.weekNumber) {
          weekBtn.classList.add('selected');
        }
        
        weekBtn.addEventListener('click', () => {
          loadWeek(weekYear, week);
          pickerPopup.style.display = 'none';
        });
        
        weeksContainer.appendChild(weekBtn);
      });
      
      monthDiv.appendChild(weeksContainer);
      pickerMonths.appendChild(monthDiv);
    }
  }

  // Populate year dropdown
  function populateYearSelect() {
    pickerYear.innerHTML = '';
    const currentYear = new Date().getFullYear();
    for (let y = currentYear - 2; y <= currentYear + 3; y++) {
      const option = document.createElement('option');
      option.value = y;
      option.textContent = y;
      if (y === selectedPickerYear) {
        option.selected = true;
      }
      pickerYear.appendChild(option);
    }
  }

  pickerBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    selectedPickerYear = state.year;
    populateYearSelect();
    renderYearWeeks(selectedPickerYear);
    pickerPopup.style.display = pickerPopup.style.display === 'none' ? 'block' : 'none';
  });

  pickerYear.addEventListener('change', (e) => {
    selectedPickerYear = parseInt(e.target.value);
    renderYearWeeks(selectedPickerYear);
  });

  pickerYearPrev.addEventListener('click', () => {
    selectedPickerYear--;
    populateYearSelect();
    pickerYear.value = selectedPickerYear;
    renderYearWeeks(selectedPickerYear);
  });

  pickerYearNext.addEventListener('click', () => {
    selectedPickerYear++;
    populateYearSelect();
    pickerYear.value = selectedPickerYear;
    renderYearWeeks(selectedPickerYear);
  });

  pickerCancel.addEventListener('click', () => {
    pickerPopup.style.display = 'none';
  });

    // Close picker when clicking outside
    document.addEventListener('click', (e) => {
      if (!pickerPopup.contains(e.target) && e.target !== pickerBtn) {
        pickerPopup.style.display = 'none';
      }
    });
  }

  // Filter change handlers
  const attach = (id) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', () => {
      updateFilterVisuals();
      // Reload current week (filters don't change the week, just visibility)
      // SINGLE SOURCE OF TRUTH: Get from URL only
      let currentYear, currentWeek;
      if (window.WeekContext) {
        const weekContext = window.WeekContext.getWeekContextWithDefault();
        currentYear = weekContext.year;
        currentWeek = weekContext.week;
      } else {
        // Fallback: calculate current week from today's date
        const now = new Date();
        const currentWeekInfo = getISOWeekInfo(now);
        currentYear = currentWeekInfo.year;
        currentWeek = currentWeekInfo.weekNumber;
      }
      loadWeek(currentYear, currentWeek);
    });
  };
      attach('toggle-blog');
      attach('toggle-annual-events');
      attach('toggle-special-events');
      attach('toggle-syndication');
      attach('toggle-social-posts');

  function updateFilterVisuals() {
    const map = [
      { id: 'toggle-blog', cls: 'filter-blog' },
      { id: 'toggle-annual-events', cls: 'filter-annual-events' },
      { id: 'toggle-special-events', cls: 'filter-special-events' },
      { id: 'toggle-syndication', cls: 'filter-syndication' },
      { id: 'toggle-social-posts', cls: 'filter-social-posts' },
    ];
    map.forEach(({ id, cls }) => {
      const input = document.getElementById(id);
      if (!input) return;
      
      // Find the label that contains this checkbox
      const label = input.closest('label');
      if (label) {
        // Toggle 'active' class based on checkbox state
        label.classList.toggle('active', input.checked);
      }
    });
  }

  updateFilterVisuals();

  // Load the saved week (or current week if none saved)
  console.log('[init] ===== LOADING WEEK =====');
  console.log('[init] State from URL:', state);
  console.log('[init] URL params:', { year: urlParams.get('year'), week: urlParams.get('week') });
  console.log('[init] Calling loadWeek with:', { year: state.year, week: state.weekNumber });
  loadWeek(state.year, state.weekNumber).catch(err => {
    console.error('[init] Error in loadWeek:', err);
  });
})();

// Facebook Matrix v1 – fixed Role/Angle hints per day (ISO 1=Mon..7=Sun)
const FACEBOOK_MATRIX_ROLES = {
  1: 'CULTURE',
  2: 'CULTURE',
  3: 'REASSURANCE',
  4: 'CULTURE',
  5: 'AUTHORITY_SHORT',
  6: 'COMMERCE',
  7: 'DEPTH_LONG',
};

const FACEBOOK_MATRIX_ANGLE_HINTS = {
  1: 'Language: Word',
  2: 'Language: Phrase',
  3: null,
  4: 'Language: Insult',
  5: null,
  6: 'Product Spotlight',
  7: 'Deep Dive',
};

// Social Focus Functions (dates line)
function renderSocialFocuses(focuses) {
  // Create a map of day_of_week -> focus for quick lookup
  const focusMap = {};
  focuses.forEach(focus => {
    focusMap[focus.day_of_week] = focus;
  });
  
  // Update each day header
  for (let day = 1; day <= 7; day++) {
    const focusEl = document.querySelector(`.social-focus[data-day="${day}"]`);
    if (focusEl) {
      const role = FACEBOOK_MATRIX_ROLES[day] || '';
      const angleHint = FACEBOOK_MATRIX_ANGLE_HINTS[day] || '';
      const focus = focusMap[day];
      const legacyLabel = focus && focus.social_focus ? focus.social_focus : null;

      // Phase 5: Role-first, legacy labels as optional UI hints only
      const parts = [];
      if (role) parts.push(role);
      if (angleHint) parts.push(angleHint);
      if (legacyLabel) parts.push(legacyLabel);

      focusEl.textContent = parts.join(' — ') || 'No focus set';

      if (legacyLabel && focus && focus.id) {
        focusEl.classList.remove('empty');
        focusEl.dataset.focusId = focus.id;
      } else {
        focusEl.classList.add('empty');
        focusEl.removeAttribute('data-focus-id');
      }
    }
  }
}

// Social Focus Modal Management
(function initSocialFocusModal() {
  let modal, editModal, modalTitle, modalBody, closeBtns, editBtn, saveBtn;
  let currentFocusData = null;
  
  function getElements() {
    modal = document.getElementById('social-focus-modal');
    editModal = document.getElementById('social-focus-edit-modal');
    modalTitle = document.getElementById('social-focus-modal-title');
    modalBody = document.getElementById('social-focus-modal-body');
    closeBtns = [
      document.getElementById('social-focus-modal-close'),
      document.getElementById('social-focus-modal-close-btn'),
      document.getElementById('social-focus-edit-modal-close'),
      document.getElementById('social-focus-edit-modal-cancel-btn')
    ];
    editBtn = document.getElementById('social-focus-modal-edit-btn');
    saveBtn = document.getElementById('social-focus-edit-modal-save-btn');
  }
  
  // Wait for DOM and ensure elements are available
  function ensureInit() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        setTimeout(init, 200);
      });
    } else {
      setTimeout(init, 200);
    }
  }
  
  // Set up click handler immediately (before init) so it works even if init is delayed
  document.addEventListener('click', async (e) => {
    const focusEl = e.target.closest('.social-focus');
    if (focusEl) {
      e.preventDefault();
      e.stopPropagation();
      
      // Ensure elements are available
      getElements();
      
      // Check if it has a focus ID (not empty)
      if (focusEl.dataset.focusId && !focusEl.classList.contains('empty')) {
        const dayOfWeek = parseInt(focusEl.dataset.day);
        
        console.log('Clicked social focus for day:', dayOfWeek, 'Focus ID:', focusEl.dataset.focusId);
        
        try {
          const response = await fetch(`/planning/api/social-focus/day/${dayOfWeek}`);
          if (response.ok) {
            const data = await response.json();
            console.log('Social focus API response:', data);
            if (data.success && data.focus) {
              currentFocusData = data.focus;
              showFocusModal(data.focus);
            } else {
              console.error('API returned success but no focus data');
            }
          } else {
            console.error('Failed to load social focus:', response.status);
            const errorData = await response.json().catch(() => ({}));
            console.error('Error details:', errorData);
          }
        } catch (error) {
          console.error('Error loading social focus:', error);
          alert('Error loading social focus details: ' + error.message);
        }
      } else {
        // No focus set for this day
        console.log('No social focus set for this day');
      }
    }
  });
  
  function init() {
    getElements();
    
    if (!modal || !editModal) {
      console.warn('Social focus modal elements not found, retrying...');
      setTimeout(init, 500);
      return;
    }
    
    console.log('Social focus modal initialized');
    
    // Close modal handlers
    closeBtns.forEach(btn => {
      if (btn) {
        btn.addEventListener('click', () => {
          if (modal) modal.style.display = 'none';
          if (editModal) editModal.style.display = 'none';
        });
      }
    });
    
    // Click outside to close
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
      });
    }
    if (editModal) {
      editModal.addEventListener('click', (e) => {
        if (e.target === editModal) editModal.style.display = 'none';
      });
    }
    
    // Save button handler for edit modal
    if (saveBtn) {
      saveBtn.addEventListener('click', async () => {
        const focusId = parseInt(document.getElementById('social-focus-edit-id').value);
        const data = {
          social_focus: document.getElementById('social-focus-edit-focus').value,
          format: document.getElementById('social-focus-edit-format').value,
          purpose: document.getElementById('social-focus-edit-purpose').value,
          example: document.getElementById('social-focus-edit-example').value
        };
        
        try {
          const response = await fetch(`/planning/api/social-focus/${focusId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
          });
          
          if (response.ok) {
            const result = await response.json();
            if (result.success) {
              editModal.style.display = 'none';
              // Reload social focuses
              const socialFocusRes = await fetch(`/planning/api/social-focus/week`);
              if (socialFocusRes.ok) {
                const focusData = await socialFocusRes.json();
                if (focusData.success) {
                  renderSocialFocuses(focusData.focuses);
                }
              }
            }
          } else {
            const error = await response.json();
            alert(`Error: ${error.error || 'Failed to save'}`);
          }
        } catch (error) {
          console.error('Error saving social focus:', error);
          alert('Error saving social focus');
        }
      });
    }
  }
  
  function showFocusModal(focus) {
    getElements(); // Ensure we have latest references
    if (!modal || !modalBody || !modalTitle) {
      console.error('Modal elements not found:', { modal: !!modal, modalBody: !!modalBody, modalTitle: !!modalTitle });
      return;
    }
    
    console.log('Showing modal for focus:', focus);
    
    const dayNames = ['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    modalTitle.textContent = `${dayNames[focus.day_of_week]} - ${focus.social_focus}`;
    
    modalBody.innerHTML = `
      <div class="social-focus-detail">
        <div class="social-focus-detail-label">Social Focus</div>
        <div class="social-focus-detail-value">${escapeHtml(focus.social_focus || 'Not set')}</div>
      </div>
      <div class="social-focus-detail">
        <div class="social-focus-detail-label">Format</div>
        <div class="social-focus-detail-value">${escapeHtml(focus.format || 'Not set')}</div>
      </div>
      <div class="social-focus-detail">
        <div class="social-focus-detail-label">Purpose</div>
        <div class="social-focus-detail-value">${escapeHtml(focus.purpose || 'Not set')}</div>
      </div>
      <div class="social-focus-detail">
        <div class="social-focus-detail-label">Example</div>
        <div class="social-focus-detail-value">${escapeHtml(focus.example || 'Not set')}</div>
      </div>
    `;
    
    if (editBtn) {
      editBtn.style.display = 'block';
      editBtn.onclick = () => {
        if (modal) modal.style.display = 'none';
        showEditModal(focus);
      };
    }
    
    if (modal) {
      modal.style.display = 'flex';
      console.log('Modal displayed');
    } else {
      console.error('Modal element is null');
    }
  }
  
  function showEditModal(focus) {
    if (!editModal) return;
    
    document.getElementById('social-focus-edit-id').value = focus.id;
    document.getElementById('social-focus-edit-day').value = focus.day_of_week;
    document.getElementById('social-focus-edit-focus').value = focus.social_focus || '';
    document.getElementById('social-focus-edit-format').value = focus.format || '';
    document.getElementById('social-focus-edit-purpose').value = focus.purpose || '';
    document.getElementById('social-focus-edit-example').value = focus.example || '';
    
    const dayNames = ['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    document.getElementById('social-focus-edit-modal-title').textContent = `Edit ${dayNames[focus.day_of_week]} Social Focus`;
    
      editModal.style.display = 'flex';
  }
  
  // Function to create recipe post from calendar view
  // Expose to window for access from renderItems
  window.createRecipePostFromCalendar = async function(itemOrRecipeId, button) {
    // Handle both old signature (recipeId) and new signature (item object)
    let item;
    if (typeof itemOrRecipeId === 'object' && itemOrRecipeId !== null) {
      item = itemOrRecipeId;
    } else {
      // Legacy: if passed a number, try to construct item from current context
      console.warn('createRecipePostFromCalendar called with legacy recipeId parameter. Please update to pass item object.');
      const urlParams = new URLSearchParams(window.location.search);
      const year = parseInt(urlParams.get('year')) || new Date().getFullYear();
      const week = parseInt(urlParams.get('week')) || getISOWeekInfo(new Date()).week;
      item = {
        category: 'recipe',
        item_id: itemOrRecipeId,
        recipe_id: itemOrRecipeId,
        id: itemOrRecipeId,
        year: year,
        week: week,
        channel: 'blog'
      };
    }
    
    if (!button) {
      // Try to find button from event target
      button = event?.target?.closest('.btn-start') || event?.target?.closest('.recipe-create-btn-small') || event?.target;
    }
    
    const originalHTML = button?.innerHTML || '';
    const originalTitle = button?.title || '';
    
    // Update button state
    if (button) {
      button.disabled = true;
      button.innerHTML = '<i class="fas fa-spinner fa-spin" style="margin-right: 0.25rem;"></i> Creating...';
      button.title = 'Creating...';
      button.style.cursor = 'not-allowed';
    }
    
    try {
      // Get item_id from various possible fields
      const item_id = item.item_id || item.id || item.recipe_id;
      
      // Get year and week from item or URL
      const urlParams = new URLSearchParams(window.location.search);
      const year = item.year || parseInt(urlParams.get('year')) || new Date().getFullYear();
      const week = item.week || parseInt(urlParams.get('week')) || getISOWeekInfo(new Date()).week;
      
      const requestBody = {
        category: 'recipe',
        item_id: item_id,
        year: year,
        week: week,
        output_channel: item.channel || 'blog'
      };
      
      console.log('[createRecipePostFromCalendar] Request body:', requestBody);
      
      if (!requestBody.item_id) {
        throw new Error('Recipe ID is missing. Cannot create post without item_id.');
      }
      
      const response = await fetch('/launchpad/one-click-publication/api/create-post-from-item', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });
      
      if (!response.ok) {
        let errorText;
        try {
          const errorJson = await response.json();
          errorText = errorJson.error || errorJson.message || JSON.stringify(errorJson);
        } catch (e) {
          errorText = await response.text();
        }
        throw new Error(errorText || `HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      console.log('[createRecipePostFromCalendar] API response:', result);
      
      if (result.success && result.post_id) {
        // Navigate to the first workflow stage (taxonomy for recipes)
        const postId = result.post_id;
        let workflowUrl = `/planning/posts/${postId}/calendar/taxonomy`;
        if (year && week) {
          workflowUrl += `?year=${year}&week=${week}`;
        }
        
        console.log('[createRecipePostFromCalendar] Navigating to:', workflowUrl);
        window.location.href = workflowUrl;
      } else {
        throw new Error(result.error || 'Failed to create post');
      }
    } catch (error) {
      console.error('[createRecipePostFromCalendar] Error creating recipe post:', error);
      
      // Show error
      if (button) {
        button.innerHTML = '<i class="fas fa-times"></i>';
        button.style.background = '#ef4444';
        button.title = 'Error';
        
        // Reset after 3 seconds
        setTimeout(() => {
          button.innerHTML = originalHTML;
          button.style.background = '#d97706';
          button.title = originalTitle;
          button.disabled = false;
          button.style.cursor = 'pointer';
        }, 3000);
      } else {
        alert(`Error creating recipe post: ${error.message || 'Please try again.'}`);
      }
    }
  }
  
  ensureInit();
})();


