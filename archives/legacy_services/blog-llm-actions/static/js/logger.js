/**
 * Logger Module
 * 
 * Responsibilities:
 * - Provides consistent logging across all modules
 * - Different log levels with color coding
 * - Module identification and timestamps
 * - Configurable for development/production
 * 
 * Usage: logger.debug('module-name', 'message')
 * 
 * @version 1.0
 */

// Logger configuration
const LOGGER_CONFIG = {
    // Log levels (0 = none, 1 = error only, 2 = warn+, 3 = info+, 4 = debug+)
    level: 4, // Default to debug level for development
    
    // Enable/disable timestamp
    showTimestamp: true,
    
    // Enable/disable module identification
    showModule: true,
    
    // Enable/disable colors (for browser console)
    useColors: true,
    
    // Prefix for all log messages
    prefix: '[LLM-ACTIONS]'
};

// Color codes for different log levels
const COLORS = {
    debug: '#6c757d',    // Gray
    info: '#007bff',     // Blue
    warn: '#ffc107',     // Yellow
    error: '#dc3545'     // Red
};

// Log level names
const LOG_LEVELS = {
    debug: 4,
    info: 3,
    warn: 2,
    error: 1
};

/**
 * Format timestamp for logging
 */
function formatTimestamp() {
    if (!LOGGER_CONFIG.showTimestamp) return '';
    const now = new Date();
    return `[${now.toLocaleTimeString()}] `;
}

/**
 * Format module name for logging
 */
function formatModule(moduleName) {
    if (!LOGGER_CONFIG.showModule || !moduleName) return '';
    return `[${moduleName}] `;
}

/**
 * Create styled log message
 */
function createLogMessage(level, moduleName, message, ...args) {
    const timestamp = formatTimestamp();
    const module = formatModule(moduleName);
    const prefix = LOGGER_CONFIG.prefix;
    
    let fullMessage = `${timestamp}${prefix} ${module}${message}`;
    
    if (LOGGER_CONFIG.useColors && COLORS[level]) {
        const color = COLORS[level];
        fullMessage = `%c${fullMessage}`;
        return [fullMessage, `color: ${color}`, ...args];
    }
    
    return [fullMessage, ...args];
}

/**
 * Main logger object
 */
const logger = {
    /**
     * Set log level
     * @param {string|number} level - Log level (debug, info, warn, error) or number (1-4)
     */
    setLevel(level) {
        if (typeof level === 'string') {
            LOGGER_CONFIG.level = LOG_LEVELS[level] || 4;
        } else {
            LOGGER_CONFIG.level = Math.max(1, Math.min(4, level));
        }
        this.info('logger', `Log level set to: ${LOGGER_CONFIG.level}`);
    },
    
    /**
     * Enable/disable colors
     * @param {boolean} enabled - Whether to use colors
     */
    setColors(enabled) {
        LOGGER_CONFIG.useColors = enabled;
        this.info('logger', `Colors ${enabled ? 'enabled' : 'disabled'}`);
    },
    
    /**
     * Enable/disable timestamps
     * @param {boolean} enabled - Whether to show timestamps
     */
    setTimestamps(enabled) {
        LOGGER_CONFIG.showTimestamp = enabled;
        this.info('logger', `Timestamps ${enabled ? 'enabled' : 'disabled'}`);
    },
    
    /**
     * Enable/disable module identification
     * @param {boolean} enabled - Whether to show module names
     */
    setModuleIdentification(enabled) {
        LOGGER_CONFIG.showModule = enabled;
        this.info('logger', `Module identification ${enabled ? 'enabled' : 'disabled'}`);
    },
    
    /**
     * Debug level logging
     * @param {string} moduleName - Name of the module logging
     * @param {string} message - Log message
     * @param {...any} args - Additional arguments
     */
    debug(moduleName, message, ...args) {
        if (LOGGER_CONFIG.level >= LOG_LEVELS.debug) {
            const logArgs = createLogMessage('debug', moduleName, message, ...args);
            console.log(...logArgs);
        }
    },
    
    /**
     * Info level logging
     * @param {string} moduleName - Name of the module logging
     * @param {string} message - Log message
     * @param {...any} args - Additional arguments
     */
    info(moduleName, message, ...args) {
        if (LOGGER_CONFIG.level >= LOG_LEVELS.info) {
            const logArgs = createLogMessage('info', moduleName, message, ...args);
            console.log(...logArgs);
        }
    },
    
    /**
     * Warning level logging
     * @param {string} moduleName - Name of the module logging
     * @param {string} message - Log message
     * @param {...any} args - Additional arguments
     */
    warn(moduleName, message, ...args) {
        if (LOGGER_CONFIG.level >= LOG_LEVELS.warn) {
            const logArgs = createLogMessage('warn', moduleName, message, ...args);
            console.warn(...logArgs);
        }
    },
    
    /**
     * Error level logging
     * @param {string} moduleName - Name of the module logging
     * @param {string} message - Log message
     * @param {...any} args - Additional arguments
     */
    error(moduleName, message, ...args) {
        if (LOGGER_CONFIG.level >= LOG_LEVELS.error) {
            const logArgs = createLogMessage('error', moduleName, message, ...args);
            console.error(...logArgs);
        }
    },
    
    /**
     * Log object/array data in a readable format
     * @param {string} moduleName - Name of the module logging
     * @param {string} label - Label for the data
     * @param {any} data - Data to log
     */
    data(moduleName, label, data) {
        if (LOGGER_CONFIG.level >= LOG_LEVELS.debug) {
            const timestamp = formatTimestamp();
            const module = formatModule(moduleName);
            const prefix = LOGGER_CONFIG.prefix;
            
            console.group(`${timestamp}${prefix} ${module}${label}`);
            console.log(data);
            console.groupEnd();
        }
    },
    
    /**
     * Log function entry/exit for debugging
     * @param {string} moduleName - Name of the module
     * @param {string} functionName - Name of the function
     * @param {string} action - 'enter' or 'exit'
     * @param {any} data - Optional data to log
     */
    trace(moduleName, functionName, action, data = null) {
        if (LOGGER_CONFIG.level >= LOG_LEVELS.debug) {
            const timestamp = formatTimestamp();
            const module = formatModule(moduleName);
            const prefix = LOGGER_CONFIG.prefix;
            const arrow = action === 'enter' ? '→' : '←';
            
            let message = `${timestamp}${prefix} ${module}${arrow} ${functionName}`;
            if (data) {
                message += ` (${JSON.stringify(data)})`;
            }
            
            console.log(`%c${message}`, `color: ${COLORS.debug}`);
        }
    },
    
    /**
     * Get current configuration
     * @returns {object} Current logger configuration
     */
    getConfig() {
        return { ...LOGGER_CONFIG };
    }
};

// Export to global scope
window.logger = logger;

// Log initialization
logger.info('logger', 'Logger module initialized');
logger.debug('logger', 'Logger configuration:', LOGGER_CONFIG); 