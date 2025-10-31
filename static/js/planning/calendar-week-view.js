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
    }
    if (type === 'scheduled' && item._syndication) {
      // Syndication display: Channel — Operation — Time
      div.textContent = `${item.channel || 'Facebook'} — ${item.operation || 'Product'} — ${item.time_display || item.time || ''}`.trim();
      div.classList.add('syndication');
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
      const target = document.getElementById(`events-row-day-${dayOfWeek}`);
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

  let ideas = [];
  let events = [];
  let schedule = [];
  let syndication = [];
  try {
    const [ideasRes, eventsRes, scheduleRes, productSyndicationRes, blogPostSyndicationRes] = await Promise.allSettled([ideasPromise, eventsPromise, schedulePromise, productSyndicationPromise, blogPostSyndicationPromise]);
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

  const eventsCells = ensureRowCells('events-row');
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
      const normalize = (s) => (s || '').toLowerCase().trim();
      const selectedSeeds = new Set((schedule || []).map(sc => normalize(sc.post_idea_seed)).filter(Boolean));
      const selectedTitles = new Set((schedule || []).map(sc => normalize(sc.post_title)).filter(Boolean));
      const ideaTitle = normalize(i.idea_title);
      const isSelected = selectedSeeds.has(ideaTitle) ||
        selectedTitles.has(ideaTitle) ||
        Array.from(selectedTitles).some(st => st.includes(ideaTitle) || ideaTitle.includes(st));
      themes.push({ ...i, _selected: isSelected });
    } else {
      // Regular idea (not a theme)
      regularIdeas.push(i);
    }
  });

  // Toggle row visibility based on filters
  const themesSection = document.querySelector('[data-filter="themes"]');
  const eventsSection = document.querySelector('[data-filter="events"]');
  const ideasSection = document.querySelector('[data-filter="ideas"]');
  const syndicationSection = document.querySelector('[data-filter="syndication"]');
  
  if (themesSection) themesSection.classList.toggle('hidden', !showThemes);
  if (eventsSection) eventsSection.classList.toggle('hidden', !showEvents);
  if (ideasSection) ideasSection.classList.toggle('hidden', !showIdeas);
  if (syndicationSection) syndicationSection.classList.toggle('hidden', !showSyndication);

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

  // Render events per day into Events row
  if (showEvents && eventsCells) {
    // Store events globally for click handler access
    window.currentWeekEvents = events;
    events.forEach((ev) => {
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
          const target = document.getElementById(`events-row-day-${Math.min(Math.max(dayIdx, 1), 7)}`);
          renderItems(target, [ev], 'event');
        }
      } else {
        // Fallback: render if no start_date (shouldn't happen, but handle gracefully)
        const dayIdx = ev.weekday || ev.day || 1; // 1..7
        const target = document.getElementById(`events-row-day-${Math.min(Math.max(dayIdx, 1), 7)}`);
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
        const item = { channel: s.platform || 'Facebook', operation: operation, time_display: timeDisplay, name: s.name || '', _syndication: true };
        renderItems(target, [item], 'scheduled');
      });
    });
  }
}

(function init() {
  const now = new Date();
  const { year, weekNumber } = getISOWeekInfo(now);
  let state = { year, weekNumber };

  document.getElementById('prev-week').addEventListener('click', () => {
    const start = getWeekStartDate(state.year, state.weekNumber);
    start.setUTCDate(start.getUTCDate() - 7);
    const info = getISOWeekInfo(start);
    state = { year: info.year, weekNumber: info.weekNumber };
    loadWeek(state.year, state.weekNumber);
  });

  document.getElementById('next-week').addEventListener('click', () => {
    const start = getWeekStartDate(state.year, state.weekNumber);
    start.setUTCDate(start.getUTCDate() + 7);
    const info = getISOWeekInfo(start);
    state = { year: info.year, weekNumber: info.weekNumber };
    loadWeek(state.year, state.weekNumber);
  });

  // Filter change handlers
  const attach = (id) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', () => {
      updateFilterVisuals();
      loadWeek(state.year, state.weekNumber);
    });
  };
  attach('toggle-themes');
  attach('toggle-ideas');
  attach('toggle-events');
  attach('toggle-syndication');

  function updateFilterVisuals() {
    const map = [
      { id: 'toggle-ideas', cls: 'filter-ideas' },
      { id: 'toggle-events', cls: 'filter-events' },
      { id: 'toggle-syndication', cls: 'filter-syndication' },
    ];
    map.forEach(({ id, cls }) => {
      const input = document.getElementById(id);
      const label = input ? input.closest('.' + cls) : null;
      if (label) {
        if (input.checked) label.classList.add('active');
        else label.classList.remove('active');
      }
    });
  }

  updateFilterVisuals();

  loadWeek(state.year, state.weekNumber);
})();


