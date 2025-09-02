# LLM Technical Implementation Guide - Launchpad Module

## Overview
This document provides detailed technical implementation instructions for the working LLM integration in the Launchpad module, using direct Ollama integration for AI-powered content generation.

**Document Version**: 2.0  
**Created**: 2025-01-27  
**Last Updated**: 2025-08-27  
**Status**: **IMPLEMENTED** - Direct Ollama Integration Working  
**Author**: AI Assistant  
**Reviewer**: User  

---

## 🎯 **IMPLEMENTATION OVERVIEW**

### **Current Working System**
1. **Direct Ollama Integration**: Working endpoint at `/api/syndication/ollama/direct`
2. **LLM Settings Panel**: Fully functional with database persistence
3. **Frontend Integration**: Connected to working backend with real-time responses
4. **Error Handling**: Robust error handling with user feedback

### **File Modifications Completed**
- ✅ `app.py` - Added working Ollama endpoint
- ✅ `templates/includes/conversion_settings.html` - LLM Settings panel with persistence
- ✅ `templates/syndication_create_piece.html` - Connected to working LLM backend
- ✅ Database integration for LLM settings persistence

---

## 🛠️ **IMPLEMENTED: DIRECT OLLAMA INTEGRATION**

### **Step 1: Working Ollama Endpoint**

The working endpoint in `app.py`:

```python
@app.route('/api/syndication/ollama/direct', methods=['POST'])
def direct_ollama_request():
    """Direct LLM execution for syndication using Ollama."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract LLM parameters
        provider = data.get('provider', 'ollama')
        model = data.get('model', 'llama3.1:70b')
        prompt = data.get('prompt', '')
        temperature = float(data.get('temperature', 0.7))
        max_tokens = int(data.get('max_tokens', 1000))
        
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400
        
        # Call Ollama directly
        import requests
        ollama_response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': model,
                'prompt': prompt,
                'options': {
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            },
            timeout=60
        )
        
        if ollama_response.status_code == 200:
            # Ollama returns streaming JSON lines, we need to parse them
            response_lines = ollama_response.text.strip().split('\n')
            generated_text = ""
            
            for line in response_lines:
                if line.strip():
                    try:
                        line_data = json.loads(line)
                        if 'response' in line_data:
                            generated_text += line_data['response']
                    except json.JSONDecodeError:
                        continue  # Skip malformed lines
            
            return jsonify({
                'output': generated_text,
                'result': generated_text,
                'status': 'success',
                'model_used': model,
                'tokens_generated': len(generated_text.split())
            })
        else:
            return jsonify({'error': f'Ollama error: {ollama_response.status_code}'}), ollama_response.status_code
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Ollama: {e}")
        return jsonify({'error': f'Failed to connect to Ollama: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error executing LLM request: {e}")
        return jsonify({'error': f'Failed to execute LLM request: {str(e)}'}), 500
```

### **Step 2: Working Frontend Integration**

The working JavaScript in `syndication_create_piece.html`:

```javascript
async function processSectionWithLLM(sectionId, sectionIndex) {
    try {
        // Get selected tasks and LLM settings
        const selectedTasks = getSelectedTasks();
        const llmSettings = getLLMSettings();
        const sectionContent = getSectionContent(sectionId);
        
        // Assemble the LLM prompt
        const prompt = assembleLLMPrompt();
        
        // Prepare LLM request
        const llmRequest = {
            provider: llmSettings.provider || 'ollama',
            model: llmSettings.model || 'llama3.1:70b',
            prompt: prompt,
            temperature: parseFloat(llmSettings.temperature || '0.7'),
            max_tokens: parseInt(llmSettings.max_tokens || '1000')
        };
        
        // Send to LLM service
        const response = await fetch('/api/syndication/ollama/direct', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
            body: JSON.stringify(llmRequest)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
        
        if (result.status === 'success') {
            // Update piece content with LLM response
            updatePieceContent(result.output, sectionIndex);
            // Update debug panel
            updateDebugPanel(result, llmRequest);
        } else {
            throw new Error(result.error || 'Unknown error');
        }
        
        } catch (error) {
        console.error('Error processing section with LLM:', error);
        showErrorNotification('AI processing failed. Please try again.');
    }
}

function assembleLLMPrompt() {
    const platformName = document.getElementById('platformSelector').value;
    const processName = document.getElementById('processSelector').value;
    const channelType = document.getElementById('channelTypeSelector').value;
    const requirements = getRequirementsFromAccordion();
    
    const userPrompt = `You are a social media content specialist. Convert blog post sections into engaging social media posts following the specified platform requirements.

Convert this blog post section into a ${platformName} ${channelType} post. Follow these requirements: ${requirements}

${getSectionContent()}`;
    
    return userPrompt;
}
```

### **Step 3: Working LLM Settings Panel**

The functional LLM Settings panel in `conversion_settings.html`:

```javascript
// Load LLM providers
async function loadLLMProviders() {
    try {
        const response = await fetch('/api/syndication/llm/providers');
        const providers = await response.json();
        
        const providerSelect = document.getElementById('llmProviderSelect');
        providerSelect.innerHTML = '<option value="">Select a provider...</option>';
        
        providers.forEach(provider => {
            const option = document.createElement('option');
            option.value = provider.id;
            option.textContent = provider.name;
            providerSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load LLM providers:', error);
    }
}

// Load LLM models for a provider
async function loadLLMModels(providerId) {
    try {
        const response = await fetch(`/api/syndication/llm/models/${providerId}`);
        const models = await response.json();
        
        const modelSelect = document.getElementById('llmModelSelect');
        modelSelect.innerHTML = '<option value="">Select a model...</option>';
        
        // Prefer faster, smaller models
        const preferredModels = ['mistral', 'llama3.1:8b', 'llama3.1:70b'];
        const sortedModels = models.sort((a, b) => {
            const aIndex = preferredModels.indexOf(a.name);
            const bIndex = preferredModels.indexOf(b.name);
            if (aIndex === -1 && bIndex === -1) return 0;
            if (aIndex === -1) return 1;
            if (bIndex === -1) return -1;
            return aIndex - bIndex;
        });
        
        sortedModels.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name;
            modelSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load LLM models:', error);
    }
}

// Save LLM settings
async function saveLLMSettings() {
    try {
        const settings = {
            provider: document.getElementById('llmProviderSelect').value,
            model: document.getElementById('llmModelSelect').value,
            temperature: document.getElementById('llmTemperature').value,
            max_tokens: document.getElementById('llmMaxTokens').value,
            retry_on_failure: document.getElementById('llmRetryOnFailure').checked,
            timeout: document.getElementById('llmTimeout').value,
            max_retries: document.getElementById('llmMaxRetries').value,
            system_prompt: document.getElementById('llmSystemPrompt').value,
            user_prompt_template: document.getElementById('llmUserPromptTemplate').value
        };
        
        const response = await fetch('/api/syndication/llm/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });
        
        if (response.ok) {
            console.log('LLM settings saved successfully');
        } else {
            console.error('Failed to save LLM settings');
        }
    } catch (error) {
        console.error('Error saving LLM settings:', error);
    }
}

// Load LLM settings
async function loadLLMSettings() {
    try {
        const response = await fetch('/api/syndication/llm/settings');
        const settings = await response.json();
        
        // Populate form fields
        if (settings.provider) document.getElementById('llmProviderSelect').value = settings.provider;
        if (settings.model) document.getElementById('llmModelSelect').value = settings.model;
        if (settings.temperature) document.getElementById('llmTemperature').value = settings.temperature;
        if (settings.max_tokens) document.getElementById('llmMaxTokens').value = settings.max_tokens;
        if (settings.retry_on_failure !== undefined) document.getElementById('llmRetryOnFailure').checked = settings.retry_on_failure;
        if (settings.timeout) document.getElementById('llmTimeout').value = settings.timeout;
        if (settings.max_retries) document.getElementById('llmMaxRetries').value = settings.max_retries;
        if (settings.system_prompt) document.getElementById('llmSystemPrompt').value = settings.system_prompt;
        if (settings.user_prompt_template) document.getElementById('llmUserPromptTemplate').value = settings.user_prompt_template;
        
    } catch (error) {
        console.error('Error loading LLM settings:', error);
    }
}
```

---

## 🔧 **IMPLEMENTED: ENHANCED FEATURES**

### **Step 1: Debug Panel Integration**

The working debug panel in `syndication_create_piece.html`:

```javascript
function updateDebugPanel(result, request) {
    // Update RAW LLM RESPONSE
    const debugRawResponse = document.getElementById('debugRawResponse');
    if (debugRawResponse) {
        debugRawResponse.value = result.output || result.result || 'No response received';
    }
    
    // Update LLM REQUEST (WHAT WE'RE SENDING)
    const debugAssembledPrompt = document.getElementById('debugAssembledPrompt');
    if (debugAssembledPrompt) {
        const previewRequest = {
            provider: request.provider,
            model: request.model,
            temperature: request.temperature,
            max_tokens: request.max_tokens,
            prompt_preview: request.prompt.substring(0, 200) + (request.prompt.length > 200 ? '...' : '')
        };
        debugAssembledPrompt.value = JSON.stringify(previewRequest, null, 2);
    }
    
    // Update LLM Status
    const llmStatus = document.getElementById('llmStatus');
    if (llmStatus) {
        llmStatus.textContent = 'Processing Complete';
    }
    
    // Update Last Processed
    const llmLastProcessed = document.getElementById('llmLastProcessed');
    if (llmLastProcessed) {
        llmLastProcessed.textContent = new Date().toLocaleTimeString();
    }
}

function prefillDebugPanelWithLLMSettings() {
    const debugLLMPrompt = document.getElementById('debugLLMPrompt');
    const llmSystemPrompt = document.getElementById('llmSystemPrompt');
    
    if (debugLLMPrompt && llmSystemPrompt && llmSystemPrompt.value) {
        debugLLMPrompt.value = llmSystemPrompt.value;
    } else if (debugLLMPrompt) {
        debugLLMPrompt.value = 'System prompt not configured yet';
    }
}

function updateDebugPanelFromRequirements() {
    const debugConstraints = document.getElementById('debugConstraints');
    const debugStyleGuide = document.getElementById('debugStyleGuide');
    
    if (debugConstraints || debugStyleGuide) {
        const requirements = getRequirementsFromAccordion();
        
        if (debugConstraints) {
            const constraints = requirements
                .filter(req => req.requirement_key.toLowerCase().includes('constraint') || 
                              req.requirement_key.toLowerCase().includes('rule') ||
                              req.requirement_key.toLowerCase().includes('requirement'))
                .map(req => req.requirement_value)
                .join(', ');
            debugConstraints.value = constraints || 'No constraints found';
        }
        
        if (debugStyleGuide) {
            const styleGuide = requirements
                .filter(req => req.requirement_key.toLowerCase().includes('style') || 
                              req.requirement_key.toLowerCase().includes('tone') ||
                              req.requirement_key.toLowerCase().includes('voice') ||
                              req.requirement_key.toLowerCase().includes('guideline'))
                .map(req => req.requirement_value)
                .join(', ');
            debugStyleGuide.value = styleGuide || 'No style guide found';
        }
    }
}

function updateDebugPanelSectionContent(sectionId) {
    const debugSectionContent = document.getElementById('debugSectionContent');
    if (!debugSectionContent) return;
    
    const sectionItem = document.querySelector(`[data-section-id="${sectionId}"]`);
    if (sectionItem) {
        const titleElement = sectionItem.querySelector('.section-title');
        const polishedElement = sectionItem.querySelector('.section-polished');
        
        if (titleElement && polishedElement) {
            const title = titleElement.textContent.trim();
            const polished = polishedElement.innerHTML
                .replace(/<[^>]*>/g, '') // Remove HTML tags
                .replace(/\s+/g, ' ') // Clean up whitespace
                .trim();
            
            debugSectionContent.value = `Title: ${title}\n\nContent: ${polished}`;
        }
    }
}
```

### **Step 2: Start Ollama Button**

The working Start Ollama button:

```javascript
// Start Ollama button handler
if (startOllamaBtn) {
    startOllamaBtn.addEventListener('click', async function() {
        console.log('Start Ollama button clicked!');
        const originalText = this.textContent;
        this.textContent = 'Starting...';
        this.disabled = true;
        this.classList.add('btn-secondary');
        this.classList.remove('btn-success');
        
        try {
            document.getElementById('llmStatus').textContent = 'Starting Ollama...';
            const response = await fetch('http://localhost:11434/api/tags');
            
            if (response.ok) {
                const data = await response.json();
                console.log('Ollama models available:', data);
                document.getElementById('llmStatus').textContent = 'Ollama Running';
                document.getElementById('llmLastProcessed').textContent = new Date().toLocaleTimeString();
                alert(`Ollama is running! Available models: ${data.models.map(m => m.name).join(', ')}`);
                this.textContent = 'Ollama Running';
                this.classList.remove('btn-secondary');
                this.classList.add('btn-info');
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Error starting Ollama:', error);
            document.getElementById('llmStatus').textContent = 'Ollama Error';
            alert(`Error starting Ollama: ${error.message}\n\nPlease ensure Ollama is running on port 11434.`);
            this.textContent = originalText;
            this.disabled = false;
            this.classList.remove('btn-secondary');
            this.classList.add('btn-success');
        }
    });
}
```

---

## 🚨 **IMPLEMENTED: ERROR HANDLING**

### **Step 1: Working Error Handling**

The current error handling implementation:

```javascript
try {
    const result = await processWithLLM(content, requirements);
    return result;
} catch (error) {
    console.error('LLM processing failed:', error);
    
    if (error.message.includes('Failed to connect to Ollama')) {
        showErrorNotification('AI service is not running. Please start Ollama and try again.');
    } else if (error.message.includes('timeout')) {
        showErrorNotification('AI service is taking too long to respond. Please try again.');
    } else {
        showErrorNotification('AI processing failed. Please try again later.');
    }
    
    return null;
}
```

### **Step 2: User-Friendly Error Display**

```javascript
function showErrorNotification(message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'alert alert-danger alert-dismissible fade show';
    notification.innerHTML = `
        <i class="fas fa-exclamation-triangle me-2"></i>
        ${message}
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

## 🔍 **IMPLEMENTED: TESTING & VALIDATION**

### **Step 1: Working API Testing**

Test the working endpoint:

```bash
# Test basic functionality
curl -X POST http://localhost:5001/api/syndication/ollama/direct \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "ollama",
    "model": "llama3.1:70b",
    "prompt": "What is 2+2?",
    "temperature": 0.7,
    "max_tokens": 100
  }'

# Expected response:
{
  "model_used": "llama3.1:70b",
  "output": "2 + 2 = 4",
  "result": "2 + 2 = 4",
  "status": "success",
  "tokens_generated": 5
}
```

### **Step 2: Health Check Endpoint**

Test Ollama connectivity:

```bash
# Test Ollama health
curl -X GET http://localhost:5001/api/syndication/ollama/test

# Expected response:
{
  "message": "Ollama is accessible",
  "models": [
    {
      "name": "llama3.1:70b",
      "model": "llama3.1:70b",
      "size": 42520412561
    }
  ],
  "status": "success"
}
```

---

## 📊 **IMPLEMENTED: MONITORING & LOGGING**

### **Step 1: Working Logging**

The current logging implementation:

```python
# Backend logging
logger.error(f"Error connecting to Ollama: {e}")
logger.error(f"Error executing LLM request: {e}")

# Frontend logging
console.log('LLM processing started');
console.log('Selected tasks:', selectedTasks);
console.log('LLM settings:', llmSettings);
console.log('LLM request:', llmRequest);
console.log('LLM response:', result);
```

### **Step 2: Performance Monitoring**

```javascript
// Performance tracking
const startTime = performance.now();
const result = await processWithLLM(content, requirements);
        const endTime = performance.now();
const processingTime = endTime - startTime;

console.log(`LLM processing completed in ${processingTime.toFixed(2)}ms`);
```

---

## 📝 **CHANGES LOG**

### **2025-01-27 - Document Creation**
- ✅ **Created comprehensive technical implementation guide**
- ✅ **Provided planned LLM Actions service integration code**
- ✅ **Included planned error handling and fallback mechanisms**

### **2025-08-27 - Major Update - Direct Ollama Implementation**
- ✅ **IMPLEMENTED direct Ollama integration**
- ✅ **Created working `/api/syndication/ollama/direct` endpoint**
- ✅ **Fixed streaming response handling for Ollama**
- ✅ **Connected frontend to working backend**
- ✅ **Implemented database persistence for LLM settings**
- ✅ **Added comprehensive error handling and debugging**
- ✅ **Added Start Ollama button for connectivity testing**
- ✅ **Updated status from IMPLEMENTATION GUIDE to IMPLEMENTED**

---

**Document Version**: 2.0  
**Last Updated**: 2025-08-27  
**Status**: **IMPLEMENTED** - Direct Ollama Integration Working  
**Next Review**: After Phase 2 feature completion
