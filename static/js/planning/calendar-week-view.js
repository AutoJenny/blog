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

  let ideas = [];
  let events = [];
  let schedule = [];
  let syndication = [];
  let socialFocuses = [];
  try {
    const [ideasRes, eventsRes, scheduleRes, productSyndicationRes, blogPostSyndicationRes, socialFocusRes] = await Promise.allSettled([ideasPromise, eventsPromise, schedulePromise, productSyndicationPromise, blogPostSyndicationPromise, socialFocusPromise]);
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
  } catch (e) {
    console.error('Error loading week data:', e);
    // Ignore; page still usable
  }

  // Get filter toggles
  const showThemes = document.getElementById('toggle-themes')?.checked !== false;
  const showIdeas = document.getElementById('toggle-ideas')?.checked !== false;
  const showEvents = document.getElementById('toggle-events')?.checked !== false;
  const showSyndication = document.getElementById('toggle-syndication')?.checked !== false;

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

  const annualEventsCells = ensureRowCells('annual-events-row');
  const specialEventsCells = ensureRowCells('special-events-row');
  const ideasCells = ensureRowCells('ideas-row');
  const syndicationCells = ensureRowCells('syndication-row');

  // Classify items by their proper type using item_classification field
  const themes = [];
  const regularIdeas = [];
  ideas.forEach(i => {
    // Use item_classification field: 'theme' or 'idea' (defaults to 'idea' if not set)
    const classification = (i.item_classification || 'idea').toLowerCase();
    if (classification === 'theme') {
      // Check if theme is selected (appears in schedule)
      // Primary check: if idea_id matches in schedule
      const selectedIdeaIds = new Set((schedule || []).map(sc => sc.idea_id).filter(Boolean));
      const isSelectedById = selectedIdeaIds.has(i.id);
      
      // Fallback: check title matching (for legacy posts created before idea_id was stored)
      const normalize = (s) => (s || '').toLowerCase().trim();
      const selectedSeeds = new Set((schedule || []).map(sc => normalize(sc.post_idea_seed)).filter(Boolean));
      const selectedTitles = new Set((schedule || []).map(sc => normalize(sc.post_title)).filter(Boolean));
      const ideaTitle = normalize(i.idea_title);
      const isSelectedByTitle = selectedSeeds.has(ideaTitle) ||
        selectedTitles.has(ideaTitle) ||
        Array.from(selectedTitles).some(st => st.includes(ideaTitle) || ideaTitle.includes(st));
      
      themes.push({ ...i, _selected: isSelectedById || isSelectedByTitle });
    } else {
      // Regular idea (not a theme)
      regularIdeas.push(i);
    }
  });

  // Toggle row visibility based on filters
  // Note: Both annual and special event rows have data-filter="events", so querySelectorAll
  const themesSections = document.querySelectorAll('[data-filter="themes"]');
  const eventsSections = document.querySelectorAll('[data-filter="events"]');
  const ideasSections = document.querySelectorAll('[data-filter="ideas"]');
  const syndicationSections = document.querySelectorAll('[data-filter="syndication"]');
  
  themesSections.forEach(section => section.classList.toggle('hidden', !showThemes));
  eventsSections.forEach(section => section.classList.toggle('hidden', !showEvents));
  ideasSections.forEach(section => section.classList.toggle('hidden', !showIdeas));
  syndicationSections.forEach(section => section.classList.toggle('hidden', !showSyndication));

  // Render Themes as week-wide themes: single row spanning the week
  const weekThemesContainer = document.getElementById('week-themes');
  if (weekThemesContainer) {
    weekThemesContainer.innerHTML = '';
    if (showThemes && themes.length) {
      renderItems(weekThemesContainer, themes, 'idea');
    }
  }

  // Render regular ideas per day into Ideas row
  if (showIdeas && ideasCells && regularIdeas.length) {
    regularIdeas.forEach((idea) => {
      // Ideas are assigned to a specific weekday (default to Monday if not set)
      const dayIdx = idea.weekday || idea.day || 1; // 1..7
      const target = document.getElementById(`ideas-row-day-${Math.min(Math.max(dayIdx, 1), 7)}`);
      if (target) renderItems(target, [idea], 'idea');
    });
  }

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
  if (showEvents && annualEventsCells) {
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
  if (showEvents && specialEventsCells) {
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
    const start = getWeekStartDate(state.year, state.weekNumber);
    start.setUTCDate(start.getUTCDate() - 7);
    const info = getISOWeekInfo(start);
    loadWeek(info.year, info.weekNumber);
  });

  document.getElementById('next-week').addEventListener('click', () => {
    const start = getWeekStartDate(state.year, state.weekNumber);
    start.setUTCDate(start.getUTCDate() + 7);
    const info = getISOWeekInfo(start);
    loadWeek(info.year, info.weekNumber);
  });

  // "This week" button
  document.getElementById('this-week-btn').addEventListener('click', () => {
    loadWeek(currentWeekInfo.year, currentWeekInfo.weekNumber);
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
        currentYear = currentWeekInfo.year;
        currentWeek = currentWeekInfo.weekNumber;
      }
      loadWeek(currentYear, currentWeek);
    });
  };
  attach('toggle-themes');
  attach('toggle-ideas');
  attach('toggle-events');
  attach('toggle-syndication');

  function updateFilterVisuals() {
    const map = [
      { id: 'toggle-themes', cls: 'filter-themes' },
      { id: 'toggle-ideas', cls: 'filter-ideas' },
      { id: 'toggle-events', cls: 'filter-events' },
      { id: 'toggle-syndication', cls: 'filter-syndication' },
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
  
  ensureInit();
})();


