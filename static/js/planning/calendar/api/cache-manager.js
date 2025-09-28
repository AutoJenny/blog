/**
 * Cache Manager Module
 * Handles data caching and memory management
 */

class CacheManager {
    constructor() {
        this.cache = new Map();
        this.maxSize = 100; // Maximum number of cache entries
        this.defaultTTL = 5 * 60 * 1000; // 5 minutes in milliseconds
    }

    // Generate cache key from parameters
    generateKey(prefix, ...params) {
        return `${prefix}:${params.join(':')}`;
    }

    // Set cache entry with TTL
    set(key, value, ttl = this.defaultTTL) {
        const now = Date.now();
        const entry = {
            value: value,
            expires: now + ttl,
            created: now
        };
        
        this.cache.set(key, entry);
        
        // Remove oldest entries if cache is full
        if (this.cache.size > this.maxSize) {
            const oldestKey = this.cache.keys().next().value;
            this.cache.delete(oldestKey);
        }
    }

    // Get cache entry if not expired
    get(key) {
        const entry = this.cache.get(key);
        if (!entry) {
            return null;
        }
        
        const now = Date.now();
        if (now > entry.expires) {
            this.cache.delete(key);
            return null;
        }
        
        return entry.value;
    }

    // Check if key exists and is not expired
    has(key) {
        const entry = this.cache.get(key);
        if (!entry) {
            return false;
        }
        
        const now = Date.now();
        if (now > entry.expires) {
            this.cache.delete(key);
            return false;
        }
        
        return true;
    }

    // Delete specific cache entry
    delete(key) {
        return this.cache.delete(key);
    }

    // Clear all cache entries
    clear() {
        this.cache.clear();
    }

    // Invalidate cache entries by prefix
    invalidateByPrefix(prefix) {
        const keysToDelete = [];
        for (const key of this.cache.keys()) {
            if (key.startsWith(prefix)) {
                keysToDelete.push(key);
            }
        }
        
        keysToDelete.forEach(key => this.cache.delete(key));
    }

    // Get cache statistics
    getStats() {
        const now = Date.now();
        let expired = 0;
        let active = 0;
        
        for (const [key, entry] of this.cache.entries()) {
            if (now > entry.expires) {
                expired++;
            } else {
                active++;
            }
        }
        
        return {
            total: this.cache.size,
            active: active,
            expired: expired,
            maxSize: this.maxSize
        };
    }

    // Clean up expired entries
    cleanup() {
        const now = Date.now();
        const keysToDelete = [];
        
        for (const [key, entry] of this.cache.entries()) {
            if (now > entry.expires) {
                keysToDelete.push(key);
            }
        }
        
        keysToDelete.forEach(key => this.cache.delete(key));
        return keysToDelete.length;
    }

    // Cache categories data
    setCategories(categories) {
        this.set('categories', categories, 10 * 60 * 1000); // 10 minutes
    }

    getCategories() {
        return this.get('categories');
    }

    // Cache week data
    setWeekData(year, weekNumber, data) {
        const key = this.generateKey('week', year, weekNumber);
        this.set(key, data, 2 * 60 * 1000); // 2 minutes
    }

    getWeekData(year, weekNumber) {
        const key = this.generateKey('week', year, weekNumber);
        return this.get(key);
    }

    // Cache calendar data
    setCalendarData(year, data) {
        const key = this.generateKey('calendar', year);
        this.set(key, data, 5 * 60 * 1000); // 5 minutes
    }

    getCalendarData(year) {
        const key = this.generateKey('calendar', year);
        return this.get(key);
    }

    // Invalidate all week data for a year
    invalidateYear(year) {
        this.invalidateByPrefix(`week:${year}:`);
        this.invalidateByPrefix(`calendar:${year}`);
    }

    // Invalidate specific week data
    invalidateWeek(year, weekNumber) {
        const key = this.generateKey('week', year, weekNumber);
        this.delete(key);
    }
}

export default CacheManager;
