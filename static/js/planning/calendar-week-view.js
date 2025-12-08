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

function renderItems(container, items, type) {
  if (!items || !Array.isArray(items) || items.length === 0) return;
  
  items.forEach((item) => {
    const div = document.createElement('div');
    div.className = `item ${type}`;
    if (type === 'idea') {
      // Make all ideas clickable, even legacy ones without IDs
      if (item.id) {
        div.dataset.ideaId = item.id;
        div.title = 'Click to edit idea';
      } else {
        div.title = 'Click to add full details for this idea';
      }
      div.style.cursor = 'pointer';
    }
    if (type === 'event' && (item.id || item._eventId)) {
      div.dataset.eventId = item.id || item._eventId;
      div.style.cursor = 'pointer';
      div.title = 'Click to view/edit event';
      // Add class based on recurrence type
      if (item.event_recurrence_type === 'one_off') {
        div.classList.add('special');
      } else {
        // Default to annual for null/undefined or explicit 'annual'
        div.classList.add('annual');
      }
    }
    if (type === 'scheduled' && item._syndication) {
      // Syndication display: Platform icon + Operation — Time
      div.classList.add('syndication');
      div.style.cursor = 'pointer';
      div.style.display = 'flex';
      div.style.alignItems = 'center';
      div.style.gap = '6px';
      div.title = `Click to manage ${item.operation || 'Product'} posts on ${item.channel || 'Facebook'}`;
      
      // Create platform icon
      const icon = document.createElement('i');
      const platformName = (item.platform || item.channel || 'facebook').toLowerCase();
      icon.className = getPlatformIcon(platformName);
      icon.style.fontSize = '0.875rem';
      // Platform-specific icon colors
      icon.style.color = platformName === 'instagram' ? '#E1306C' : 
                         platformName === 'twitter' ? '#1DA1F2' :
                         platformName === 'linkedin' ? '#0077B5' :
                         '#93c5fd'; // Default blue for Facebook
      
      // Create text content
      const textSpan = document.createElement('span');
      textSpan.textContent = `${item.operation || 'Product'} — ${item.time_display || item.time || ''}`.trim();
      
      // Build URL for click
      const platform = (item.platform || item.channel || 'facebook').toLowerCase();
      const contentType = (item.content_type || (item.operation === 'Blog' ? 'blog_post' : 'product_post')).toLowerCase();
      const url = getSyndicationUrl(platform, contentType);
      
      // Make clickable
      div.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        window.location.href = url;
      };
      
      div.appendChild(icon);
      div.appendChild(textSpan);
    } else if (type === 'theme' && item._theme) {
      // Theme display: star icon + title
      div.classList.add('idea');
      div.classList.add('theme');
      div.style.display = 'flex';
      div.style.alignItems = 'center';
      div.style.gap = '6px';
      div.style.cursor = 'pointer';
      div.title = `Click to edit theme: ${item.title || 'Theme'}`;
      if (item.id) {
        div.dataset.themeId = item.id;
      }
      // Icon
      const icon = document.createElement('i');
      icon.className = 'fas fa-star';
      icon.style.fontSize = '0.875rem';
      icon.style.color = '#f97316';
      div.appendChild(icon);
      // Text
      const text = document.createElement('span');
      text.textContent = item.title || 'Theme';
      text.style.fontSize = '0.8rem';
      text.style.overflow = 'hidden';
      text.style.textOverflow = 'ellipsis';
      text.style.whiteSpace = 'nowrap';
      div.appendChild(text);
      
      // Add click handler to open theme modal
      if (item.id) {
        div.addEventListener('click', () => {
          const ideaModal = window.getIdeaModal ? window.getIdeaModal() : null;
          if (ideaModal) {
            ideaModal.openTheme(item.id);
          }
        });
      }
    } else if (type === 'profile' && item._profile) {
      // Profile display: Icon + Title
      div.classList.add('profile');
      div.style.cursor = 'pointer';
      div.style.display = 'flex';
      div.style.alignItems = 'center';
      div.style.gap = '6px';
      div.title = `Click to view/edit ${item.profile_type || 'product'} profile: ${item.title || 'Untitled'}`;
      div.dataset.profileId = item.id;
      
      // Create profile type icon
      const icon = document.createElement('i');
      const profileType = (item.profile_type || 'product').toLowerCase();
      icon.className = profileType === 'product' ? 'fas fa-briefcase' : 'fas fa-folder';
      icon.style.fontSize = '0.875rem';
      icon.style.color = profileType === 'product' ? '#0ea5e9' : '#6366f1';
      
      div.appendChild(icon);
      
      const text = document.createElement('span');
      text.textContent = item.title || 'Untitled Profile';
      text.style.fontSize = '0.8rem';
      text.style.overflow = 'hidden';
      text.style.textOverflow = 'ellipsis';
      text.style.whiteSpace = 'nowrap';
      div.appendChild(text);
      
      // Add click handler to open profile editor
      div.addEventListener('click', (e) => {
        e.stopPropagation();
        e.preventDefault();
        const profileId = item.post_id || item.id; // Use post_id as primary ID for profiles
        if (profileId) {
          const profileModal = window.getProfileModal ? window.getProfileModal() : null;
          if (profileModal) {
            profileModal.open(profileId);
          } else {
            // Fallback: navigate to profile page
            const profileUrl = `/planning/posts/${profileId}/profile`;
            window.location.href = profileUrl;
          }
        }
      });
    } else if (type === 'recipe' && item._recipe) {
      // Recipe display: Icon + Title + Create button (if definition)
      div.classList.add('recipe');
      div.style.display = 'flex';
      div.style.alignItems = 'center';
      div.style.gap = '6px';
      div.style.flexWrap = 'wrap';
      
      // Check if this is a definition (no post yet) or a scheduled post
      // Default to scheduled post if _definition is not explicitly true
      if (item._definition === true) {
        // Recipe definition - show as available with create button
        div.style.cursor = 'default';
        div.title = `Recipe definition: ${item.title || 'Untitled'} (click to create post)`;
        div.dataset.recipeDefId = item.id;
        div.dataset.recipeWeekNumber = item.recipe_week_number;
        
        // Create recipe icon (utensils icon)
        const icon = document.createElement('i');
        icon.className = 'fas fa-utensils';
        icon.style.fontSize = '0.875rem';
        icon.style.color = '#f59e0b';
        div.appendChild(icon);
        
        const text = document.createElement('span');
        text.textContent = item.title || 'Untitled Recipe';
        text.style.fontSize = '0.8rem';
        text.style.overflow = 'hidden';
        text.style.textOverflow = 'ellipsis';
        text.style.whiteSpace = 'nowrap';
        text.style.flex = '1';
        div.appendChild(text);
        
        // Create "Create Post" button for recipe definitions
        const createBtn = document.createElement('button');
        createBtn.className = 'recipe-create-btn-small';
        createBtn.innerHTML = '<i class="fas fa-plus"></i>';
        createBtn.title = 'Create recipe post';
        createBtn.style.cssText = `
          background: #d97706;
          color: white;
          border: none;
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 0.7rem;
          cursor: pointer;
          margin-left: auto;
          transition: background 0.2s;
        `;
        createBtn.onmouseover = () => createBtn.style.background = '#b45309';
        createBtn.onmouseout = () => createBtn.style.background = '#d97706';
        
        createBtn.addEventListener('click', async (e) => {
          e.stopPropagation();
          // Use window function if available, otherwise navigate
          if (typeof window.createRecipePostFromCalendar === 'function') {
            await window.createRecipePostFromCalendar(item.recipe_week_number, createBtn);
          } else {
            // Fallback: navigate to recipes page
            window.location.href = '/recipes';
          }
        });
        
        div.appendChild(createBtn);
      } else {
        // Scheduled recipe post - clickable
        div.style.cursor = 'pointer';
        div.title = `Click to view/edit recipe: ${item.title || 'Untitled'}`;
        div.dataset.recipeId = item.id || item.recipe_id;
        
        // Create recipe icon (utensils icon)
        const icon = document.createElement('i');
        icon.className = 'fas fa-utensils';
        icon.style.fontSize = '0.875rem';
        icon.style.color = '#f59e0b';
        div.appendChild(icon);
        
        const text = document.createElement('span');
        text.textContent = item.title || 'Untitled Recipe';
        text.style.fontSize = '0.8rem';
        text.style.overflow = 'hidden';
        text.style.textOverflow = 'ellipsis';
        text.style.whiteSpace = 'nowrap';
        div.appendChild(text);
        
        // Add click handler for scheduled posts
        // Recipes are in calendar_recipes table, not calendar_ideas
        // If recipe has a post, navigate to it; otherwise navigate to recipes page
        const recipeId = item.id || item.recipe_id;
        const postId = item.post_id;
        
        // Always make recipe clickable, even if no ID (shouldn't happen but be defensive)
        div.addEventListener('click', (e) => {
          e.stopPropagation();
          e.preventDefault();
          
          if (postId) {
            // Recipe has a post - navigate to it
            window.location.href = `/planning/posts/${postId}`;
          } else if (recipeId) {
            // Recipe definition without post - navigate to recipes page
            // Recipes are managed on the recipes page, not in the idea modal
            window.location.href = `/recipes`;
          } else {
            // Fallback: just go to recipes page
            window.location.href = `/recipes`;
          }
        });
      }
    } else if (type === 'weekly-word' || type === 'weekly-phrase' || type === 'weekly-insult') {
      // Weekly Word/Phrase/Insult display: Show as pill with title only (no description)
      div.classList.add('pill');
      div.style.cursor = 'pointer';
      div.style.padding = '6px 10px';
      div.style.borderRadius = '6px';
      div.style.backgroundColor = type === 'weekly-word' ? 'rgba(34, 197, 94, 0.15)' : 
                                  type === 'weekly-phrase' ? 'rgba(34, 197, 94, 0.15)' : 
                                  'rgba(239, 68, 68, 0.15)';
      div.style.border = `1px solid ${type === 'weekly-word' ? 'rgba(34, 197, 94, 0.3)' : 
                                         type === 'weekly-phrase' ? 'rgba(34, 197, 94, 0.3)' : 
                                         'rgba(239, 68, 68, 0.3)'}`;
      
      const itemId = item.item_id || item.id;
      if (itemId) {
        div.dataset.ideaId = itemId;
      }
      
      // Title with prefix only (no description)
      const titleText = item.title || item.idea_title || '';
      const titlePrefix = type === 'weekly-word' ? 'Word: ' : 
                         type === 'weekly-phrase' ? 'Phrase: ' : 
                         'Insult: ';
      
      div.textContent = titlePrefix + titleText;
      div.style.fontSize = '0.8rem';
      div.style.color = '#f1f5f9';
      div.style.fontWeight = '500';
      div.title = `Click to edit ${type === 'weekly-word' ? 'word' : type === 'weekly-phrase' ? 'phrase' : 'insult'}`;
      
      // Add click handler to open in idea modal
      if (itemId) {
        div.addEventListener('click', () => {
          const ideaModal = window.getIdeaModal ? window.getIdeaModal() : null;
          if (ideaModal) {
            ideaModal.open(itemId);
          }
        });
      }
    } else {
      div.textContent = item.title || item.idea_title || item.name || item.summary || item.event_title || 'Untitled';
    }
    if (type === 'idea' && item._selected) {
      div.classList.add('selected');
    }
    container.appendChild(div);
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
  document.getElementById('week-year').textContent = String(year);
  
  document.getElementById('week-number').textContent = String(weekNumber);
  
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
  document.getElementById('week-dates').textContent = `${formatDate(dates[0])} – ${formatDate(dates[6])}`;

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
    // Ignore; page still usable
  }

  // Get filter toggles
  const showBlog = document.getElementById('toggle-blog')?.checked !== false;
  const showAnnualEvents = document.getElementById('toggle-annual-events')?.checked !== false;
  const showSpecialEvents = document.getElementById('toggle-special-events')?.checked !== false;
  const showSyndication = document.getElementById('toggle-syndication')?.checked !== false;
  const showWordsPhrases = document.getElementById('toggle-words-phrases')?.checked !== false;

  // Build row grids cells for rows container
  const ensureRowCells = (rowId) => {
    const row = document.getElementById(rowId);
    if (!row) return null;
    row.innerHTML = '';
    const cells = [];
    for (let i = 1; i <= 7; i++) {
      const cell = document.createElement('div');
      cell.className = 'row-cell';
      cell.id = `${rowId}-day-${i}`;
      row.appendChild(cell);
      cells.push(cell);
    }
    return cells;
  };

  const blogCells = ensureRowCells('blog-row');
  const annualEventsCells = ensureRowCells('annual-events-row');
  const specialEventsCells = ensureRowCells('special-events-row');
  const syndicationCells = ensureRowCells('syndication-row');
  const wordsPhrasesCells = ensureRowCells('words-phrases-row');

  // Load themes from schedule (themes scheduled for this week)
  // NEW SYSTEM: Uses cyclic position-based logic (same as scheduling calendar)
  // DEPRECATED: Old week_number-based theme lookup is no longer used
  const themes = [];
  const scheduledThemeIds = new Set();
  
  // Get scheduleData from window (set earlier in loadWeek)
  const scheduleData = window.currentScheduleData || {};
  
  // Check for selected_theme_id at top level (from new cyclic system)
  if (scheduleData && scheduleData.selected_theme_id) {
    const themeId = scheduleData.selected_theme_id;
    if (!scheduledThemeIds.has(themeId)) {
      scheduledThemeIds.add(themeId);
      // Find the theme entry in schedule array to get title
      const themeEntry = schedule && Array.isArray(schedule) 
        ? schedule.find(s => (s.theme_id === themeId || s.selected_theme_id === themeId) && s.type === 'theme_selection')
        : null;
      
      themes.push({
        id: themeId,
        theme_title: themeEntry?.theme_title || 'Theme',
        theme_description: themeEntry?.theme_description,
        _selected: true,
        _fromSchedule: true,
        _from_cyclic_system: true
      });
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
  
  if (schedule && Array.isArray(schedule)) {
    selectedWord = schedule.find(s => s.type === 'weekly_word') || null;
    selectedPhrase = schedule.find(s => s.type === 'weekly_phrase') || null;
    selectedInsult = schedule.find(s => s.type === 'weekly_insult') || null;
  }

  // Toggle row visibility based on filters
  const blogSections = document.querySelectorAll('[data-filter="blog"]');
  const annualEventsSections = document.querySelectorAll('[data-filter="annual-events"]');
  const specialEventsSections = document.querySelectorAll('[data-filter="special-events"]');
  const syndicationSections = document.querySelectorAll('[data-filter="syndication"]');
  const wordsPhrasesSections = document.querySelectorAll('[data-filter="words-phrases"]');
  
  blogSections.forEach(section => section.classList.toggle('hidden', !showBlog));
  annualEventsSections.forEach(section => section.classList.toggle('hidden', !showAnnualEvents));
  specialEventsSections.forEach(section => section.classList.toggle('hidden', !showSpecialEvents));
  syndicationSections.forEach(section => section.classList.toggle('hidden', !showSyndication));
  wordsPhrasesSections.forEach(section => section.classList.toggle('hidden', !showWordsPhrases));

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
          renderItems(target, [ev], 'event');
        }
      } else {
        // Fallback: render if no start_date (shouldn't happen, but handle gracefully)
        const dayIdx = ev.weekday || ev.day || 1; // 1..7
        const target = document.getElementById(`annual-events-row-day-${Math.min(Math.max(dayIdx, 1), 7)}`);
        renderItems(target, [ev], 'event');
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
          renderItems(target, [ev], 'event');
        }
      } else {
        // Fallback: render if no start_date (shouldn't happen, but handle gracefully)
        const dayIdx = ev.weekday || ev.day || 1; // 1..7
        const target = document.getElementById(`special-events-row-day-${Math.min(Math.max(dayIdx, 1), 7)}`);
        renderItems(target, [ev], 'event');
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
        renderItems(target, [item], 'scheduled');
      });
    });
  }
  
  // Render weekly words/phrases/insults into Words & Phrases row
  if (showWordsPhrases && wordsPhrasesCells) {
    // Word on Monday (day 1)
    if (selectedWord) {
      const wordTarget = document.getElementById('words-phrases-row-day-1');
      if (wordTarget) {
        // Pass item as-is; renderItems will add "Word: " prefix and show description
        renderItems(wordTarget, [selectedWord], 'weekly-word');
      }
    }
    // Phrase on Wednesday (day 3)
    if (selectedPhrase) {
      const phraseTarget = document.getElementById('words-phrases-row-day-3');
      if (phraseTarget) {
        // Pass item as-is; renderItems will add "Phrase: " prefix and show description
        renderItems(phraseTarget, [selectedPhrase], 'weekly-phrase');
      }
    }
    // Insult on Friday (day 5)
    if (selectedInsult) {
      const insultTarget = document.getElementById('words-phrases-row-day-5');
      if (insultTarget) {
        // Pass item as-is; renderItems will add "Insult: " prefix and show description
        renderItems(insultTarget, [selectedInsult], 'weekly-insult');
      }
    }
  }
  
  // Render consolidated Blog row: Theme (Mon), Recipe (Wed), Surname profile (Fri), Product profile (Sat)
  if (showBlog && blogCells) {
    // Theme for Monday
    const themeEntry = themes[0];
    if (themeEntry) {
      const target = document.getElementById('blog-row-day-1');
      if (target) {
        const themeItem = {
          id: themeEntry.id,
          title: themeEntry.theme_title || 'Theme',
          _theme: true
        };
        renderItems(target, [themeItem], 'theme');
      }
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
        renderItems(target, [recipeItem], 'recipe');
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
        renderItems(target, [profileItem], 'profile');
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
        renderItems(target, [profileItem], 'profile');
      }
    }
  }
  
  // Render social focuses under day headers
  renderSocialFocuses(socialFocuses);
}

(function init() {
  // SINGLE SOURCE OF TRUTH: Get week context from URL only
  let state;
  if (window.WeekContext) {
    const weekContext = window.WeekContext.getWeekContextWithDefault();
    state = {
      year: weekContext.year,
      weekNumber: weekContext.week
    };
    // If URL didn't have week params, update URL with default
    const urlContext = window.WeekContext.getWeekContext();
    if (!urlContext && window.WeekContext) {
      window.WeekContext.setWeekContext(state.year, state.weekNumber);
    }
  } else {
    // Fallback if WeekContext not loaded (shouldn't happen)
    const now = new Date();
    const currentWeekInfo = getISOWeekInfo(now);
    state = {
      year: currentWeekInfo.year,
      weekNumber: currentWeekInfo.weekNumber
    };
  }
  
  // SINGLE SOURCE OF TRUTH: Update URL using WeekContext
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

  document.getElementById('prev-week').addEventListener('click', () => {
    // SINGLE SOURCE OF TRUTH: Get current week from WeekContext
    const currentWeek = window.WeekContext ? window.WeekContext.getWeekContextWithDefault() : { year: state.year, week: state.weekNumber };
    const start = getWeekStartDate(currentWeek.year, currentWeek.week);
    start.setUTCDate(start.getUTCDate() - 7);
    const info = getISOWeekInfo(start);
    loadWeek(info.year, info.weekNumber);
  });

  document.getElementById('next-week').addEventListener('click', () => {
    // SINGLE SOURCE OF TRUTH: Get current week from WeekContext
    const currentWeek = window.WeekContext ? window.WeekContext.getWeekContextWithDefault() : { year: state.year, week: state.weekNumber };
    const start = getWeekStartDate(currentWeek.year, currentWeek.week);
    start.setUTCDate(start.getUTCDate() + 7);
    const info = getISOWeekInfo(start);
    loadWeek(info.year, info.weekNumber);
  });

  // "This week" button - recalculate current week from today's date
  document.getElementById('this-week-btn').addEventListener('click', () => {
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
    
    // Build new URL
    const newUrl = `/planning/posts/${window.postId || 0}/calendar/week-view?year=${currentWeekInfo.year}&week=${currentWeekInfo.weekNumber}`;
    
    // If we're already on this week, force a reload by adding a timestamp
    if (currentYear === currentWeekInfo.year && currentWeek === currentWeekInfo.weekNumber) {
      // Force reload by calling loadWeek directly
      loadWeek(currentWeekInfo.year, currentWeekInfo.weekNumber);
    } else {
      // Navigate to new week
      window.location.href = newUrl;
    }
  });

  // Week picker - month/week list interface
  const pickerBtn = document.getElementById('week-picker-btn');
  const pickerPopup = document.getElementById('week-picker-popup');
  const pickerCancel = document.getElementById('week-picker-cancel');
  const pickerYear = document.getElementById('picker-year');
  const pickerYearPrev = document.getElementById('picker-year-prev');
  const pickerYearNext = document.getElementById('picker-year-next');
  const pickerMonths = document.getElementById('week-picker-months');
  
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
      attach('toggle-words-phrases');

  function updateFilterVisuals() {
    const map = [
      { id: 'toggle-blog', cls: 'filter-blog' },
      { id: 'toggle-annual-events', cls: 'filter-annual-events' },
      { id: 'toggle-special-events', cls: 'filter-special-events' },
      { id: 'toggle-syndication', cls: 'filter-syndication' },
      { id: 'toggle-words-phrases', cls: 'filter-words-phrases' },
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
  loadWeek(state.year, state.weekNumber);
})();

// Social Focus Functions
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
      const focus = focusMap[day];
      if (focus && focus.social_focus) {
        focusEl.textContent = focus.social_focus;
        focusEl.classList.remove('empty');
        focusEl.dataset.focusId = focus.id;
      } else {
        focusEl.textContent = 'No focus set';
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
  window.createRecipePostFromCalendar = async function(recipeWeekNumber, button) {
    if (!button) {
      // Try to find button from event target
      button = event?.target?.closest('.recipe-create-btn-small') || event?.target;
    }
    
    const originalHTML = button?.innerHTML || '';
    const originalTitle = button?.title || '';
    
    // Update button state
    if (button) {
      button.disabled = true;
      button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
      button.title = 'Creating...';
      button.style.cursor = 'not-allowed';
    }
    
    try {
      // Get current year and week from URL or state
      const urlParams = new URLSearchParams(window.location.search);
      const year = parseInt(urlParams.get('year')) || new Date().getFullYear();
      const weekNumber = parseInt(urlParams.get('week')) || getISOWeekInfo(new Date()).week;
      
      const response = await fetch(`/api/recipes/${recipeWeekNumber}/create-post`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          year: year,
          week_number: weekNumber,
          weekday: 1 // Default to Monday
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Show success
        if (button) {
          button.innerHTML = '<i class="fas fa-check"></i>';
          button.style.background = '#10b981';
          button.title = 'Created!';
        }
        
        // Reload page after a short delay to show the new post
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        // Show error
        if (button) {
          button.innerHTML = '<i class="fas fa-times"></i>';
          button.style.background = '#ef4444';
          button.title = data.error || 'Error';
          
          // Reset after 3 seconds
          setTimeout(() => {
            button.innerHTML = originalHTML;
            button.style.background = '#d97706';
            button.title = originalTitle;
            button.disabled = false;
            button.style.cursor = 'pointer';
          }, 3000);
        } else {
          alert(`Error: ${data.error || 'Failed to create recipe post'}`);
        }
      }
    } catch (error) {
      console.error('Error creating recipe post:', error);
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
        alert('Error creating recipe post. Please try again.');
      }
    }
  }
  
  ensureInit();
})();


