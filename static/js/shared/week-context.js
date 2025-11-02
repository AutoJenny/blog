/**
 * Week Context Manager
 * 
 * SINGLE SOURCE OF TRUTH: URL Query Parameters
 * 
 * This module provides a centralized way to read and manage week/year context.
 * URL query parameters (?year=X&week=Y) are the ONLY source of truth.
 * 
 * NO localStorage, NO window variables, NO other persistence mechanisms.
 */

/**
 * Get the current week context from URL query parameters
 * @returns {{year: number, week: number}|null} Week context or null if not in URL
 */
function getWeekContext() {
    const urlParams = new URLSearchParams(window.location.search);
    const year = urlParams.get('year');
    const week = urlParams.get('week');
    
    if (year && week) {
        return {
            year: parseInt(year, 10),
            week: parseInt(week, 10)
        };
    }
    
    return null;
}

/**
 * Get the current week context, with fallback to current week if not in URL
 * Used only for initial page loads when URL doesn't have week context yet
 * @returns {{year: number, week: number}} Week context (never null)
 */
function getWeekContextWithDefault() {
    const context = getWeekContext();
    if (context) {
        return context;
    }
    
    // Calculate current ISO week
    const now = new Date();
    const currentWeekInfo = getISOWeekInfo(now);
    
    return {
        year: currentWeekInfo.year,
        week: currentWeekInfo.weekNumber
    };
}

/**
 * Update the URL with new week context
 * Uses history.replaceState to update URL without page reload
 * @param {number} year - Year
 * @param {number} week - Week number
 */
function setWeekContext(year, week) {
    const url = new URL(window.location.href);
    url.searchParams.set('year', year);
    url.searchParams.set('week', week);
    window.history.replaceState({ year, week }, '', url);
}

/**
 * Attach week context to a URL string
 * @param {string} href - Base URL
 * @param {number|null} year - Year (if null, uses current context)
 * @param {number|null} week - Week (if null, uses current context)
 * @returns {string} URL with week parameters added
 */
function attachWeekToUrl(href, year = null, week = null) {
    const context = year !== null && week !== null 
        ? { year, week }
        : getWeekContext();
    
    if (!context) {
        return href; // No week context available, return URL as-is
    }
    
    try {
        const url = new URL(href, window.location.origin);
        url.searchParams.set('year', context.year);
        url.searchParams.set('week', context.week);
        return url.pathname + url.search;
    } catch (e) {
        // If href is relative, try simpler approach
        const separator = href.includes('?') ? '&' : '?';
        return `${href}${separator}year=${context.year}&week=${context.week}`;
    }
}

/**
 * Get ISO week info for a date
 * Helper function for calculating current week
 * Uses ISO 8601 standard (week starts Monday, first week contains Jan 4)
 */
function getISOWeekInfo(date) {
    const target = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    const dayNr = (target.getUTCDay() + 6) % 7; // Monday=0
    target.setUTCDate(target.getUTCDate() - dayNr + 3);
    const firstThursday = new Date(Date.UTC(target.getUTCFullYear(), 0, 4));
    const weekNumber = 1 + Math.round(((target - firstThursday) / 86400000 - 3 + ((firstThursday.getUTCDay() + 6) % 7)) / 7);
    const year = target.getUTCFullYear();
    return { year, weekNumber };
}

// Export functions for use in other scripts
window.WeekContext = {
    getWeekContext,
    getWeekContextWithDefault,
    setWeekContext,
    attachWeekToUrl,
    getISOWeekInfo
};

