// Posting Control Utilities: time formatting and next-post calculations

window.PostingControlUtils = (function() {
  function formatTimeForDisplay(time) {
    const [hoursStr, minutesStr] = (time || '17:00').split(':');
    const hour = parseInt(hoursStr || '17', 10);
    const minutes = (minutesStr || '00').padStart(2, '0');
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
    return `${displayHour}:${minutes} ${ampm}`;
  }

  function getDayName(dayNumber) {
    const days = ['', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return days[dayNumber] || '';
  }

  function formatSchedulePattern(days, time, timezone) {
    const tz = timezone || 'UTC';
    const timeFormatted = formatTimeForDisplay(time);
    if (!Array.isArray(days) || days.length === 0) return `No days selected at ${timeFormatted} ${tz}`;
    if (days.length === 7) return `Every day at ${timeFormatted} ${tz}`;
    const isWeekdays = days.length === 5 && days.includes(1) && days.includes(2) && days.includes(3) && days.includes(4) && days.includes(5);
    if (isWeekdays) return `Weekdays at ${timeFormatted} ${tz}`;
    const isWeekends = days.length === 2 && days.includes(6) && days.includes(7);
    if (isWeekends) return `Weekends at ${timeFormatted} ${tz}`;
    const dayNames = days.map(getDayName).join(', ');
    return `${dayNames} at ${timeFormatted} ${tz}`;
  }

  function calculateNextPostTime(days, time, timezone) {
    const tz = timezone || 'UTC';
    const now = new Date();
    const today = now.getDay() || 7; // Convert Sunday (0) to 7
    if (!Array.isArray(days) || days.length === 0) return 'No posts scheduled';

    // Find next selected day starting today
    let nextDay = null;
    for (let i = 0; i < 7; i++) {
      const checkDay = ((today + i - 1) % 7) + 1;
      if (days.includes(checkDay)) { nextDay = checkDay; break; }
    }
    if (!nextDay) return 'No posts scheduled';

    const nextPostDate = new Date(now);
    const daysUntilNext = nextDay > today ? nextDay - today : (7 - today) + nextDay;
    nextPostDate.setDate(nextPostDate.getDate() + (daysUntilNext % 7));

    const [hoursStr, minutesStr] = (time || '17:00').split(':');
    nextPostDate.setHours(parseInt(hoursStr || '17', 10), parseInt(minutesStr || '0', 10), 0, 0);

    const dayName = getDayName(nextDay);
    const timeFormatted = formatTimeForDisplay(time || '17:00');
    if (daysUntilNext === 0) return `Today at ${timeFormatted} ${tz}`;
    if (daysUntilNext === 1) return `Tomorrow at ${timeFormatted} ${tz}`;
    return `${dayName} at ${timeFormatted} ${tz}`;
  }

  return {
    formatTimeForDisplay,
    getDayName,
    formatSchedulePattern,
    calculateNextPostTime,
  };
})();


