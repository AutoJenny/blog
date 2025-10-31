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
  items.forEach((item) => {
    const div = document.createElement('div');
    div.className = `item ${type}`;
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

async function loadWeek(year, weekNumber) {
  document.getElementById('week-year').textContent = String(year);
  document.getElementById('week-number').textContent = String(weekNumber);

  const weekStart = getWeekStartDate(year, weekNumber);
  const dates = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(weekStart);
    d.setUTCDate(weekStart.getUTCDate() + i);
    dates.push(d);
    const body = document.getElementById(`day-${i + 1}`);
    if (body) body.innerHTML = '';
    // Update day header title to include calendar day number on the right
    const dayEl = document.querySelector(`.day[data-day="${i + 1}"]`);
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
  const syndicationPromise = fetchJSON(`/launchpad/api/syndication/schedules?platform=facebook&content_type=product`);

  let ideas = [];
  let events = [];
  let schedule = [];
  let syndication = [];
  try {
    const [ideasRes, eventsRes, scheduleRes, syndicationRes] = await Promise.allSettled([ideasPromise, eventsPromise, schedulePromise, syndicationPromise]);
    if (ideasRes.status === 'fulfilled') ideas = ideasRes.value.ideas || ideasRes.value || [];
    if (eventsRes.status === 'fulfilled') events = eventsRes.value.events || eventsRes.value || [];
    if (scheduleRes.status === 'fulfilled') schedule = scheduleRes.value.schedule || scheduleRes.value || [];
    if (syndicationRes.status === 'fulfilled') syndication = (syndicationRes.value.schedules || []).filter(s => s && s.is_active !== false);
  } catch (e) {
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

  // Separate ideas into themes (selected/used) and ideas (unselected/available)
  const normalize = (s) => (s || '').toLowerCase().trim();
  const selectedSeeds = new Set((schedule || []).map(sc => normalize(sc.post_idea_seed)).filter(Boolean));
  const selectedTitles = new Set((schedule || []).map(sc => normalize(sc.post_title)).filter(Boolean));
  const themes = [];
  const unselectedIdeas = [];
  ideas.forEach(i => {
    const ideaTitle = normalize(i.idea_title);
    const isSelected = selectedSeeds.has(ideaTitle) ||
      selectedTitles.has(ideaTitle) ||
      Array.from(selectedTitles).some(st => st.includes(ideaTitle) || ideaTitle.includes(st));
    if (isSelected) {
      themes.push({ ...i, _selected: true });
    } else {
      unselectedIdeas.push(i);
    }
  });

  // Render Themes as week-wide themes: single row spanning the week (only selected ideas)
  const weekThemesContainer = document.getElementById('week-themes');
  if (weekThemesContainer) {
    weekThemesContainer.innerHTML = '';
    if (showThemes) {
      if (themes.length) renderItems(weekThemesContainer, themes, 'idea');
      if (unselectedIdeas.length) renderItems(weekThemesContainer, unselectedIdeas, 'idea');
    }
  }

  // Render events per day into Events row
  if (showEvents && eventsCells) {
    events.forEach((ev) => {
      const dayIdx = ev.weekday || ev.day || 1; // 1..7
      const target = document.getElementById(`events-row-day-${Math.min(Math.max(dayIdx, 1), 7)}`);
      renderItems(target, [ev], 'event');
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
        const item = { channel: s.platform || 'Facebook', operation: s.content_type === 'product' ? 'Product' : (s.content_type || ''), time_display: timeDisplay, _syndication: true };
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


