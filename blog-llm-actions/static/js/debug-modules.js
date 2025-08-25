/**
 * Debug Module Loading
 * 
 * This script helps debug module loading issues by checking if all modules
 * are properly loaded and accessible.
 */

console.log('=== LLM Actions Module Debug ===');

// Check if logger is available
if (window.logger) {
    console.log('✅ Logger module loaded');
    window.logger.info('debug', 'Debug script started');
} else {
    console.error('❌ Logger module not found');
}

// Check all expected modules
const expectedModules = [
    'configManager',
    'promptManager', 
    'uiConfig',
    'fieldSelector',
    'messageManager',
    'accordionManager'
];

console.log('Checking module availability...');
expectedModules.forEach(moduleName => {
    // Check both old window registration and new LLM_STATE.modules registration
    const moduleOnWindow = window[moduleName];
    const moduleInState = window.LLM_STATE?.modules?.[moduleName];
    
    if (moduleOnWindow) {
        console.log(`✅ ${moduleName} module loaded (window registration)`);
        if (typeof moduleOnWindow.initialize === 'function') {
            console.log(`   - Has initialize method`);
        } else {
            console.warn(`   - Missing initialize method`);
        }
    } else if (moduleInState) {
        console.log(`✅ ${moduleName} module loaded (LLM_STATE.modules registration)`);
        if (typeof moduleInState.initialize === 'function') {
            console.log(`   - Has initialize method`);
        } else {
            console.warn(`   - Missing initialize method`);
        }
    } else {
        console.error(`❌ ${moduleName} module not found (neither window nor LLM_STATE.modules)`);
    }
});

// Check global state objects
const expectedStates = [
    'CONFIG_STATE',
    'LLM_STATE'
];

console.log('Checking global state objects...');
expectedStates.forEach(stateName => {
    if (window[stateName]) {
        console.log(`✅ ${stateName} available`);
        if (stateName === 'LLM_STATE' && window.LLM_STATE.modules) {
            console.log(`   - LLM_STATE.modules contains:`, Object.keys(window.LLM_STATE.modules));
        }
    } else {
        console.error(`❌ ${stateName} not found`);
    }
});

// Check orchestrator
if (window.llmOrchestrator) {
    console.log('✅ LLM Orchestrator available');
    if (window.llmOrchestrator.initialized) {
        console.log('   - Orchestrator is initialized');
    } else {
        console.log('   - Orchestrator is not yet initialized');
    }
} else {
    console.error('❌ LLM Orchestrator not found');
}

console.log('=== Debug Complete ==='); 