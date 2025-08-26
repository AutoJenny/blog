# LLM Technical Implementation Guide - Launchpad Module

## Overview
This document provides detailed technical implementation instructions for integrating the Launchpad module with the centralized LLM Actions service on port 5002.

**Document Version**: 1.0  
**Created**: 2025-01-27  
**Status**: **IMPLEMENTATION GUIDE** - Ready for Development  
**Author**: AI Assistant  
**Reviewer**: User  

---

## 🎯 **IMPLEMENTATION OVERVIEW**

### **Integration Points**
1. **JavaScript Functions**: Replace mock LLM processing with API calls
2. **LLM Settings Panel**: Connect UI controls to LLM Actions service
3. **Error Handling**: Implement robust fallback mechanisms
4. **Configuration Sync**: Load/save settings from centralized service

### **File Modifications Required**
- `templates/facebook_feed_post_config.html` - Update LLM test functions
- `templates/includes/conversion_settings.html` - Connect settings panel
- `static/js/llm-integration.js` - New file for LLM service client
- `app.py` - Add LLM service health check endpoints

---

## 🛠️ **PHASE 1: BASIC API INTEGRATION**

### **Step 1: Create LLM Service Client**

Create a new file `static/js/llm-integration.js`:

```javascript
/**
 * LLM Actions Service Client
 * Handles communication with the centralized LLM service on port 5002
 */
class LLMActionsClient {
    constructor(baseUrl = 'http://localhost:5002') {
        this.baseUrl = baseUrl;
        this.timeout = 30000; // 30 seconds
        this.retryAttempts = 3;
        this.retryDelay = 1000; // 1 second
    }

    /**
     * Check if LLM Actions service is available
     */
    async checkHealth() {
        try {
            const response = await fetch(`${this.baseUrl}/health`, {
                method: 'GET',
                timeout: 5000
            });
            return response.ok;
        } catch (error) {
            console.warn('LLM Actions service health check failed:', error);
            return false;
        }
    }

    /**
     * Generate content using LLM Actions service
     */
    async generateContent(prompt, options = {}) {
        const {
            provider = 'ollama',
            model = 'llama3',
            temperature = 0.7,
            maxTokens = 1000,
            systemPrompt = null
        } = options;

        const requestBody = {
            provider,
            model,
            prompt,
            temperature: parseFloat(temperature),
            max_tokens: parseInt(maxTokens)
        };

        if (systemPrompt) {
            requestBody.system_prompt = systemPrompt;
        }

        try {
            const response = await fetch(`${this.baseUrl}/api/run-llm`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            return {
                success: true,
                content: result.response || result.content,
                metadata: {
                    model: result.model,
                    provider: result.provider,
                    tokens: result.usage?.total_tokens,
                    processingTime: result.processing_time
                }
            };
        } catch (error) {
            console.error('LLM content generation failed:', error);
            throw error;
        }
    }

    /**
     * Get available LLM providers
     */
    async getProviders() {
        try {
            const response = await fetch(`${this.baseUrl}/api/llm/providers`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.warn('Failed to get LLM providers:', error);
            return { providers: ['ollama'] }; // Fallback
        }
    }

    /**
     * Get available models for a provider
     */
    async getModels(provider = 'ollama') {
        try {
            const response = await fetch(`${this.baseUrl}/api/llm/models?provider=${provider}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.warn('Failed to get LLM models:', error);
            return { models: ['llama3', 'llama2'] }; // Fallback
        }
    }

    /**
     * Get current LLM configuration
     */
    async getConfig() {
        try {
            const response = await fetch(`${this.baseUrl}/api/llm/config`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.warn('Failed to get LLM config:', error);
            return this.getDefaultConfig();
        }
    }

    /**
     * Get default configuration
     */
    getDefaultConfig() {
        return {
            provider: 'ollama',
            model: 'llama3',
            temperature: 0.7,
            max_tokens: 1000,
            system_prompt: 'You are a social media content specialist. Convert blog posts into engaging social media posts following the specified platform requirements.'
        };
    }
}

// Global instance
window.llmClient = new LLMActionsClient();
```

### **Step 2: Update LLM Test Function**

Modify the `testLLM()` function in `templates/facebook_feed_post_config.html`:

```javascript
// Replace the existing testLLM function with this:
async function testLLM() {
    const blogContent = document.getElementById('blogContent').value;
    if (!blogContent.trim()) {
        alert('Please enter some blog content to test.');
        return;
    }

    // Show loading state
    const resultDiv = document.getElementById('llmResult');
    const rewrittenContent = document.getElementById('rewrittenContent');
    const appliedRules = document.getElementById('appliedRules');
    
    resultDiv.style.display = 'block';
    rewrittenContent.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing with LLM...';
    appliedRules.innerHTML = 'Analyzing requirements...';

    try {
        // Check if LLM Actions service is available
        const isHealthy = await window.llmClient.checkHealth();
        
        if (isHealthy) {
            // Use real LLM service
            await processWithRealLLM(blogContent);
        } else {
            // Fall back to mock processing
            console.warn('LLM Actions service unavailable, using fallback');
            await processWithMockLLM(blogContent);
        }
    } catch (error) {
        console.error('LLM processing failed:', error);
        // Fall back to mock processing
        await processWithMockLLM(blogContent);
    }
}

/**
 * Process content with real LLM Actions service
 */
async function processWithRealLLM(blogContent) {
    const requirements = {{ requirements|tojson }};
    
    // Assemble prompt from requirements
    const prompt = assemblePrompt(blogContent, requirements);
    
    // Get LLM settings from the UI
    const llmSettings = getLLMSettingsFromUI();
    
    try {
        // Generate content using LLM Actions service
        const result = await window.llmClient.generateContent(prompt, llmSettings);
        
        if (result.success) {
            // Display real LLM results
            displayLLMResults(result.content, requirements);
        } else {
            throw new Error('LLM generation failed');
        }
    } catch (error) {
        console.error('Real LLM processing failed:', error);
        throw error; // This will trigger fallback to mock
    }
}

/**
 * Process content with mock LLM (fallback)
 */
async function processWithMockLLM(blogContent) {
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Use existing mock implementation
    const mockResponse = generateMockLLMResponse(blogContent);
    displayLLMResults(mockResponse.content, mockResponse.rules);
}

/**
 * Assemble prompt from blog content and requirements
 */
function assemblePrompt(blogContent, requirements) {
    const requirementsText = requirements.map(req => 
        `- ${req.requirement_key}: ${req.requirement_value}`
    ).join('\n');
    
    return `Convert this blog post section into a Facebook Feed Post.

Blog Content:
${blogContent}

Requirements:
${requirementsText}

Please create engaging, Facebook-optimized content that follows all requirements.`;
}

/**
 * Get LLM settings from the UI
 */
function getLLMSettingsFromUI() {
    // Get values from LLM Settings panel
    const provider = document.getElementById('llmProvider')?.value || 'ollama';
    const model = document.getElementById('llmModel')?.value || 'llama3';
    const temperature = parseFloat(document.getElementById('temperatureRange')?.value || '0.7');
    const maxTokens = parseInt(document.getElementById('maxTokens')?.value || '1000');
    const systemPrompt = document.getElementById('systemPrompt')?.value || '';
    
    return {
        provider,
        model,
        temperature,
        maxTokens,
        systemPrompt: systemPrompt || null
    };
}

/**
 * Display LLM results
 */
function displayLLMResults(content, rules) {
    const rewrittenContent = document.getElementById('rewrittenContent');
    const appliedRules = document.getElementById('appliedRules');
    
    rewrittenContent.innerHTML = content;
    appliedRules.innerHTML = rules;
}
```

### **Step 3: Connect LLM Settings Panel**

Update the LLM Settings panel in `templates/includes/conversion_settings.html` to load configuration from the service:

```javascript
// Add this JavaScript to the conversion_settings.html file
document.addEventListener('DOMContentLoaded', function() {
    // Initialize LLM Settings panel
    initializeLLMSettings();
});

/**
 * Initialize LLM Settings panel with service configuration
 */
async function initializeLLMSettings() {
    try {
        // Check if LLM Actions service is available
        if (window.llmClient && await window.llmClient.checkHealth()) {
            await loadLLMConfiguration();
        } else {
            console.warn('LLM Actions service unavailable, using default settings');
            setDefaultLLMSettings();
        }
    } catch (error) {
        console.error('Failed to initialize LLM settings:', error);
        setDefaultLLMSettings();
    }
}

/**
 * Load LLM configuration from service
 */
async function loadLLMConfiguration() {
    try {
        const [providers, models, config] = await Promise.all([
            window.llmClient.getProviders(),
            window.llmClient.getModels(),
            window.llmClient.getConfig()
        ]);
        
        // Populate provider options
        populateProviderOptions(providers.providers || []);
        
        // Populate model options
        populateModelOptions(models.models || []);
        
        // Load current configuration
        loadCurrentConfig(config);
        
        // Update status
        updateLLMStatus('Connected to LLM Actions service', 'success');
    } catch (error) {
        console.error('Failed to load LLM configuration:', error);
        setDefaultLLMSettings();
        updateLLMStatus('Using default settings (service unavailable)', 'warning');
    }
}

/**
 * Populate provider options
 */
function populateProviderOptions(providers) {
    const providerSelect = document.getElementById('llmProvider');
    if (!providerSelect) return;
    
    providerSelect.innerHTML = '';
    providers.forEach(provider => {
        const option = document.createElement('option');
        option.value = provider;
        option.textContent = provider.charAt(0).toUpperCase() + provider.slice(1);
        providerSelect.appendChild(option);
    });
}

/**
 * Populate model options
 */
function populateModelOptions(models) {
    const modelSelect = document.getElementById('llmModel');
    if (!modelSelect) return;
    
    modelSelect.innerHTML = '';
    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = model;
        modelSelect.appendChild(option);
    });
}

/**
 * Load current configuration into UI
 */
function loadCurrentConfig(config) {
    // Set provider
    const providerSelect = document.getElementById('llmProvider');
    if (providerSelect && config.provider) {
        providerSelect.value = config.provider;
    }
    
    // Set model
    const modelSelect = document.getElementById('llmModel');
    if (modelSelect && config.model) {
        modelSelect.value = config.model;
    }
    
    // Set temperature
    const temperatureRange = document.getElementById('temperatureRange');
    const temperatureValue = document.getElementById('temperatureValue');
    if (temperatureRange && config.temperature) {
        temperatureRange.value = config.temperature;
        if (temperatureValue) {
            temperatureValue.textContent = config.temperature;
        }
    }
    
    // Set max tokens
    const maxTokensInput = document.getElementById('maxTokens');
    if (maxTokensInput && config.max_tokens) {
        maxTokensInput.value = config.max_tokens;
    }
    
    // Set system prompt
    const systemPromptTextarea = document.getElementById('systemPrompt');
    if (systemPromptTextarea && config.system_prompt) {
        systemPromptTextarea.value = config.system_prompt;
    }
}

/**
 * Set default LLM settings
 */
function setDefaultLLMSettings() {
    const defaultConfig = {
        provider: 'ollama',
        model: 'llama3',
        temperature: 0.7,
        max_tokens: 1000,
        system_prompt: 'You are a social media content specialist. Convert blog posts into engaging social media posts following the specified platform requirements.'
    };
    
    loadCurrentConfig(defaultConfig);
}

/**
 * Update LLM status display
 */
function updateLLMStatus(message, type = 'info') {
    const statusElement = document.querySelector('.llm-settings-panel .status-indicator span');
    if (statusElement) {
        statusElement.textContent = message;
        
        // Update status styling
        const statusContainer = statusElement.closest('.status-indicator');
        if (statusContainer) {
            statusContainer.className = `status-indicator ${type}`;
        }
    }
}
```

---

## 🔧 **PHASE 2: ENHANCED INTEGRATION**

### **Step 1: Add Configuration Persistence**

Create a new endpoint in `app.py` for saving LLM settings:

```python
@app.route('/api/syndication/llm-settings', methods=['GET', 'POST'])
def llm_settings():
    """Handle LLM settings for syndication module."""
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['provider', 'model', 'temperature', 'max_tokens']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            # Save settings to database (implement as needed)
            # For now, we'll just return success
            return jsonify({
                'status': 'success',
                'message': 'LLM settings saved successfully',
                'settings': data
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # GET request - return current settings
    try:
        # Load settings from database (implement as needed)
        # For now, return default settings
        default_settings = {
            'provider': 'ollama',
            'model': 'llama3',
            'temperature': 0.7,
            'max_tokens': 1000,
            'system_prompt': 'You are a social media content specialist...'
        }
        return jsonify(default_settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### **Step 2: Add Health Check Endpoint**

Add a health check endpoint to monitor LLM Actions service:

```python
@app.route('/api/syndication/llm-health', methods=['GET'])
def llm_health_check():
    """Check health of LLM Actions service."""
    try:
        import requests
        
        # Check LLM Actions service health
        response = requests.get('http://localhost:5002/health', timeout=5)
        
        if response.ok:
            return jsonify({
                'status': 'healthy',
                'llm_service': 'available',
                'response_time': response.elapsed.total_seconds()
            })
        else:
            return jsonify({
                'status': 'degraded',
                'llm_service': 'unavailable',
                'http_status': response.status_code
            })
    except requests.exceptions.RequestException as e:
        return jsonify({
            'status': 'unhealthy',
            'llm_service': 'unreachable',
            'error': str(e)
        }), 503
    except Exception as e:
        return jsonify({
            'status': 'error',
            'llm_service': 'unknown',
            'error': str(e)
        }), 500
```

---

## 🚨 **ERROR HANDLING IMPLEMENTATION**

### **Step 1: Enhanced Error Handling**

Update the LLM client with better error handling:

```javascript
/**
 * Enhanced error handling for LLM operations
 */
class LLMErrorHandler {
    static handleError(error, context = '') {
        console.error(`LLM Error in ${context}:`, error);
        
        // Categorize errors
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            return {
                type: 'network_error',
                message: 'Network error - LLM service may be unavailable',
                userMessage: 'Unable to connect to AI service. Please check your connection.',
                retryable: true
            };
        }
        
        if (error.message.includes('HTTP 500')) {
            return {
                type: 'service_error',
                message: 'LLM service internal error',
                userMessage: 'AI service is experiencing issues. Please try again later.',
                retryable: true
            };
        }
        
        if (error.message.includes('timeout')) {
            return {
                type: 'timeout_error',
                message: 'LLM request timed out',
                userMessage: 'AI service is taking too long to respond. Please try again.',
                retryable: true
            };
        }
        
        return {
            type: 'unknown_error',
            message: error.message,
            userMessage: 'An unexpected error occurred. Please try again.',
            retryable: false
        };
    }
    
    static async retryOperation(operation, maxRetries = 3, delay = 1000) {
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                return await operation();
            } catch (error) {
                if (attempt === maxRetries) {
                    throw error;
                }
                
                console.warn(`LLM operation failed (attempt ${attempt}/${maxRetries}), retrying...`);
                await new Promise(resolve => setTimeout(resolve, delay * attempt));
            }
        }
    }
}
```

### **Step 2: User-Friendly Error Display**

Add error display functions to the UI:

```javascript
/**
 * Display user-friendly error messages
 */
function displayLLMError(error, context = '') {
    const errorInfo = LLMErrorHandler.handleError(error, context);
    
    // Update status display
    updateLLMStatus(errorInfo.userMessage, 'error');
    
    // Show error notification
    showErrorNotification(errorInfo.userMessage, errorInfo.retryable);
    
    // Log detailed error for debugging
    console.error('LLM Error Details:', {
        context,
        error: error.message,
        stack: error.stack,
        userMessage: errorInfo.userMessage
    });
}

/**
 * Show error notification
 */
function showErrorNotification(message, retryable = false) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'alert alert-danger alert-dismissible fade show';
    notification.innerHTML = `
        <i class="fas fa-exclamation-triangle me-2"></i>
        ${message}
        ${retryable ? '<button type="button" class="btn btn-sm btn-outline-danger ms-2" onclick="retryLastOperation()">Retry</button>' : ''}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    const container = document.querySelector('.container-fluid');
    container.insertBefore(notification, container.firstChild);
    
    // Auto-dismiss after 10 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 10000);
}
```

---

## 🔍 **TESTING IMPLEMENTATION**

### **Step 1: Unit Tests**

Create test file `tests/test_llm_integration.py`:

```python
import unittest
import requests
from unittest.mock import patch, Mock

class TestLLMIntegration(unittest.TestCase):
    def setUp(self):
        self.base_url = 'http://localhost:5001'
        self.llm_service_url = 'http://localhost:5002'
    
    def test_llm_health_check(self):
        """Test LLM health check endpoint."""
        response = requests.get(f'{self.base_url}/api/syndication/llm-health')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('llm_service', data)
    
    @patch('requests.get')
    def test_llm_health_check_service_unavailable(self, mock_get):
        """Test health check when LLM service is unavailable."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection refused")
        
        response = requests.get(f'{self.base_url}/api/syndication/llm-health')
        self.assertEqual(response.status_code, 503)
        
        data = response.json()
        self.assertEqual(data['status'], 'unhealthy')
        self.assertEqual(data['llm_service'], 'unreachable')
    
    def test_llm_settings_endpoint(self):
        """Test LLM settings endpoint."""
        # Test GET request
        response = requests.get(f'{self.base_url}/api/syndication/llm-settings')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('provider', data)
        self.assertIn('model', data)
        self.assertIn('temperature', data)
        
        # Test POST request
        test_settings = {
            'provider': 'ollama',
            'model': 'llama3',
            'temperature': 0.8,
            'max_tokens': 1500
        }
        
        response = requests.post(
            f'{self.base_url}/api/syndication/llm-settings',
            json=test_settings
        )
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'success')

if __name__ == '__main__':
    unittest.main()
```

### **Step 2: Integration Tests**

Create integration test file `tests/test_llm_end_to_end.py`:

```python
import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestLLMEndToEnd(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome()  # or appropriate driver
        self.driver.get('http://localhost:5001/syndication/facebook/feed-post')
    
    def tearDown(self):
        self.driver.quit()
    
    def test_llm_test_interface(self):
        """Test the complete LLM test interface workflow."""
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'blogContent'))
        )
        
        # Enter test content
        blog_input = self.driver.find_element(By.ID, 'blogContent')
        blog_input.send_keys('This is a test blog post about social media marketing.')
        
        # Click test button
        test_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Test LLM')]")
        test_button.click()
        
        # Wait for processing
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.ID, 'llmResult'))
        )
        
        # Verify results are displayed
        result_div = self.driver.find_element(By.ID, 'llmResult')
        self.assertTrue(result_div.is_displayed())
        
        # Check if content was generated
        rewritten_content = self.driver.find_element(By.ID, 'rewrittenContent')
        content_text = rewritten_content.text
        self.assertNotIn('Processing with LLM...', content_text)
        self.assertGreater(len(content_text), 50)  # Should have substantial content

if __name__ == '__main__':
    unittest.main()
```

---

## 📊 **MONITORING & LOGGING**

### **Step 1: Add Logging to LLM Client**

```javascript
/**
 * Enhanced logging for LLM operations
 */
class LLMLogger {
    static log(level, message, data = {}) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            level,
            message,
            data,
            context: 'LLM Integration'
        };
        
        // Console logging
        switch (level) {
            case 'debug':
                console.debug(`[LLM] ${message}`, data);
                break;
            case 'info':
                console.info(`[LLM] ${message}`, data);
                break;
            case 'warn':
                console.warn(`[LLM] ${message}`, data);
                break;
            case 'error':
                console.error(`[LLM] ${message}`, data);
                break;
        }
        
        // Send to monitoring service if available
        this.sendToMonitoring(logEntry);
    }
    
    static sendToMonitoring(logEntry) {
        // Implementation for sending logs to monitoring service
        // This could be Sentry, LogRocket, or custom endpoint
        if (window.monitoringService) {
            window.monitoringService.log(logEntry);
        }
    }
}
```

### **Step 2: Performance Monitoring**

```javascript
/**
 * Performance monitoring for LLM operations
 */
class LLMPerformanceMonitor {
    static startTimer(operation) {
        return {
            operation,
            startTime: performance.now(),
            startTimestamp: Date.now()
        };
    }
    
    static endTimer(timer) {
        const endTime = performance.now();
        const duration = endTime - timer.startTime;
        
        // Log performance metrics
        LLMLogger.log('info', 'LLM operation completed', {
            operation: timer.operation,
            duration: duration.toFixed(2),
            startTime: timer.startTimestamp,
            endTime: Date.now()
        });
        
        // Update UI with performance info
        this.updatePerformanceDisplay(duration);
        
        return duration;
    }
    
    static updatePerformanceDisplay(duration) {
        const processingTimeElement = document.getElementById('llmProcessingTime');
        if (processingTimeElement) {
            processingTimeElement.textContent = `${duration.toFixed(1)}s`;
        }
    }
}
```

---

## 📝 **CHANGES LOG**

### **2025-01-27 - Document Creation**
- ✅ **Created comprehensive technical implementation guide**
- ✅ **Provided Phase 1 implementation code**
- ✅ **Included error handling and fallback mechanisms**
- ✅ **Added testing and monitoring implementations**
- ✅ **Documented all required file modifications**

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-27  
**Status**: **IMPLEMENTATION GUIDE** - Ready for Development  
**Next Review**: After Phase 1 implementation completion
