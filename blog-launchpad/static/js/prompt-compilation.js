// Prompt Compilation Module
// Extracted from syndication_create_piece.js for modularization

console.log('Prompt compilation module loading...');

function assembleLLMPrompt(processConfig, sectionContent) {
    console.log('assembleLLMPrompt called with:', { processConfig, sectionContent });
    
    if (!processConfig) {
        console.log('No process config, returning error');
        return 'No process configuration available';
    }
    if (!sectionContent) {
        console.log('No section content, returning error');
        return 'No section content available';
    }
    
    // Get actual platform and process information
    const platformSelector = document.getElementById('platformSelector');
    const processSelector = document.getElementById('processSelector');
    const selectedPlatform = platformSelector.options[platformSelector.selectedIndex];
    const selectedProcess = processSelector.options[processSelector.selectedIndex];
    
    console.log('Selected platform:', selectedPlatform);
    console.log('Selected process:', selectedProcess);
    
    const platformName = selectedPlatform ? selectedPlatform.textContent : 'Unknown Platform';
    const processName = selectedProcess ? selectedProcess.textContent.split(' (')[0] : 'Unknown Process';
    // Clean up the channel type to be more LLM-friendly
    let channelType = selectedProcess ? selectedProcess.textContent.includes('(') ? selectedProcess.textContent.split('(')[1].replace(')', '') : 'N/A' : 'N/A';
    
    // Convert technical terms to natural language
    if (channelType === 'feed_post') {
        channelType = 'feed post';
    } else if (channelType === 'story_post') {
        channelType = 'story post';
    } else if (channelType === 'reels_caption') {
        channelType = 'reels caption';
    } else if (channelType === 'group_post') {
        channelType = 'group post';
    }
    
    console.log('Channel type after conversion:', channelType);
    
    console.log('Extracted platform/process info:', { platformName, processName, channelType });
    
    // Get requirements from the Channel Requirements accordion
    const requirementsAccordion = document.getElementById('mvpRequirementsAccordion');
    console.log('Requirements accordion found:', requirementsAccordion);
    
    let requirements = [];
    
    if (requirementsAccordion) {
        const requirementItems = requirementsAccordion.querySelectorAll('.requirement-item');
        console.log('Found requirement items:', requirementItems.length);
        
        requirementItems.forEach((item, index) => {
            const keyElement = item.querySelector('.badge');
            const valueElement = item.querySelector('strong');
            console.log(`Requirement ${index + 1}:`, { keyElement: keyElement?.textContent, valueElement: valueElement?.textContent });
            
            if (keyElement && valueElement) {
                requirements.push(`${keyElement.textContent}: ${valueElement.textContent}`);
            }
        });
    }
    
    const requirementsText = requirements.length > 0 ? requirements.join('\n') : 'No specific requirements';
    console.log('Final requirements text:', requirementsText);
    
    // Get LLM settings for the actual prompt
    const llmSettings = getLLMSettings();
    console.log('LLM settings:', llmSettings);
    
    const systemPrompt = llmSettings.system_prompt || 'You are a social media content specialist. Convert blog post sections into engaging social media posts following the specified platform requirements.';
    const userPrompt = llmSettings.user_prompt_template || 'Convert this blog post section into a {platform} {channel_type} post. Follow these requirements: {requirements}';
    
    console.log('Base prompts:', { systemPrompt, userPrompt });
    
    // Replace placeholders with actual values
    let finalUserPrompt = userPrompt
        .replace('{platform}', platformName)
        .replace('{channel_type}', channelType)
        .replace('{requirements}', requirementsText);
    
    console.log('Final user prompt after replacement:', finalUserPrompt);
    
    // Build the three structured parts
    // Get the System Prompt and User Prompt Template from the LLM Settings panel
    const systemPromptElement = document.getElementById('llmSystemPrompt');
    const userPromptTemplateElement = document.getElementById('llmUserPromptTemplate');
    
    let currentSystemPrompt = 'No system prompt configured';
    let currentUserPromptTemplate = 'No user prompt template configured';
    
    if (systemPromptElement) {
        currentSystemPrompt = systemPromptElement.value || systemPromptElement.textContent || 'No system prompt configured';
    }
    
    if (userPromptTemplateElement) {
        currentUserPromptTemplate = userPromptTemplateElement.value || userPromptTemplateElement.textContent || 'No user prompt template configured';
    }
    
    // Get the selected platform and channel type values
    const currentPlatformSelector = document.getElementById('platformSelector');
    
    let currentSelectedPlatform = 'No platform selected';
    let currentSelectedChannelType = 'No channel type selected';
    
    if (currentPlatformSelector) {
        currentSelectedPlatform = currentPlatformSelector.options[currentPlatformSelector.selectedIndex]?.text || 'No platform selected';
    }
    
    // Get channel type from the process configuration displayed in debugProcessName
    const debugProcessName = document.getElementById('debugProcessName');
    if (debugProcessName && debugProcessName.textContent !== 'No process selected') {
        let currentChannelType = debugProcessName.textContent.includes('(') ? debugProcessName.textContent.split('(')[1].replace(')', '') : 'N/A';
        
        // Convert technical terms to natural language
        if (currentChannelType === 'feed_post') {
            currentChannelType = 'feed post';
        } else if (currentChannelType === 'story_post') {
            currentChannelType = 'story post';
        } else if (currentChannelType === 'reels_caption') {
            currentChannelType = 'reels caption';
        } else if (currentChannelType === 'group_post') {
            currentChannelType = 'group post';
        }
        
        currentSelectedChannelType = currentChannelType;
    }
    
    // Substitute the placeholders in the user prompt template
    const substitutedUserPromptTemplate = currentUserPromptTemplate
        .replace(/{platform}/g, currentSelectedPlatform)
        .replace(/{channel_type}/g, currentSelectedChannelType);
    
    const systemTask = `${currentSystemPrompt}\n\n${substitutedUserPromptTemplate}`;
    
    const blogDetails = `Title: ${sectionContent.title || 'No title'}\nContent: ${sectionContent.content || 'No content'}`;
    
    const structuredRequirements = `- Tone: Conversational and engaging\n- Length: 150-200 characters\n- Include a clear call-to-action\n- Use up to 3 relevant hashtags\n\nReturn only the final Facebook post text, with no explanations or extra commentary.`;
    
    // Update the structured display
    if (typeof updateStructuredPromptDisplay === 'function') {
        updateStructuredPromptDisplay(systemTask, blogDetails, structuredRequirements);
    }
    
    // Build the full prompt for LLM (keeping backward compatibility)
    let prompt = `${systemTask}\n\n=== BLOG DETAILS ===\n${blogDetails}\n===================\n\nREQUIREMENTS:\n${structuredRequirements}`;
    
    console.log('Final assembled prompt:', prompt);
    return prompt;
}

function getLLMSettings() {
    return {
        provider_id: document.getElementById('llmProviderSelect')?.value || '',
        model_id: document.getElementById('llmModelSelect')?.value || '',
        system_prompt: document.getElementById('llmSystemPrompt')?.value || '',
        user_prompt_template: document.getElementById('llmUserPromptTemplate')?.value || '',
        temperature: document.getElementById('llmTemperature')?.value || '0.7',
        max_tokens: document.getElementById('llmMaxTokens')?.value || '1000'
    };
}

// Export functions to global scope for compatibility
window.assembleLLMPrompt = assembleLLMPrompt;
window.getLLMSettings = getLLMSettings;

// Function to update the structured prompt display
function updateStructuredPromptDisplay(systemTask, blogDetails, requirements) {
    // Update System & Task section
    const systemTaskElement = document.getElementById('promptSystemTask');
    if (systemTaskElement) {
        systemTaskElement.textContent = systemTask || 'No prompt configured';
    }
    
    // Update Blog Details section
    const blogDetailsElement = document.getElementById('promptBlogDetails');
    if (blogDetailsElement) {
        blogDetailsElement.textContent = blogDetails || 'No blog content available';
    }
    
    // Update Requirements section
    const requirementsElement = document.getElementById('promptRequirements');
    if (requirementsElement) {
        requirementsElement.textContent = requirements || 'No requirements configured';
    }
}

// Export the update function
window.updateStructuredPromptDisplay = updateStructuredPromptDisplay;

// Function to initialize the structured prompt display with default content
function initializeStructuredPromptDisplay() {
    // Get the System Prompt and User Prompt Template from the LLM Settings panel
    const systemPromptElement = document.getElementById('llmSystemPrompt');
    const userPromptTemplateElement = document.getElementById('llmUserPromptTemplate');
    
    let systemPrompt = 'No system prompt configured';
    let userPromptTemplate = 'No user prompt template configured';
    
    // Check if the textarea has actual content (not just placeholder)
    if (systemPromptElement && systemPromptElement.value && systemPromptElement.value.trim() !== '') {
        systemPrompt = systemPromptElement.value;
    } else if (systemPromptElement && systemPromptElement.textContent && systemPromptElement.textContent.trim() !== '') {
        systemPrompt = systemPromptElement.textContent;
    }
    
    if (userPromptTemplateElement && userPromptTemplateElement.value && userPromptTemplateElement.value.trim() !== '') {
        userPromptTemplate = userPromptTemplateElement.value;
    } else if (userPromptTemplateElement && userPromptTemplateElement.textContent && userPromptTemplateElement.textContent.trim() !== '') {
        userPromptTemplate = userPromptTemplateElement.textContent;
    }
    
    // Get the selected platform and channel type values
    const platformSelector = document.getElementById('platformSelector');
    
    let selectedPlatform = 'No platform selected';
    let selectedChannelType = 'No channel type selected';
    
    console.log('Platform selector found:', platformSelector);
    if (platformSelector) {
        console.log('Platform selector options:', platformSelector.options);
        console.log('Platform selector selectedIndex:', platformSelector.selectedIndex);
        selectedPlatform = platformSelector.options[platformSelector.selectedIndex]?.text || 'No platform selected';
        console.log('Selected platform:', selectedPlatform);
    }
    
    // Get channel type from the process selector
    const processSelector = document.getElementById('processSelector');
    console.log('Process selector found:', processSelector);
    
    if (processSelector && processSelector.selectedIndex > 0) {
        const selectedProcessOption = processSelector.options[processSelector.selectedIndex];
        console.log('Selected process option:', selectedProcessOption);
        
        if (selectedProcessOption && selectedProcessOption.textContent.includes('(')) {
            let channelType = selectedProcessOption.textContent.split('(')[1].replace(')', '');
            console.log('Extracted channel type:', channelType);
            
            // Convert technical terms to natural language
            if (channelType === 'feed_post') {
                channelType = 'feed post';
            } else if (channelType === 'story_post') {
                channelType = 'story post';
            } else if (channelType === 'reels_caption') {
                channelType = 'reels caption';
            } else if (channelType === 'group_post') {
                channelType = 'group post';
            }
            
            selectedChannelType = channelType;
            console.log('Final selected channel type:', selectedChannelType);
        }
    }
    
    console.log('Final values - Platform:', selectedPlatform, 'Channel Type:', selectedChannelType);
    
    // Substitute the placeholders in the user prompt template
    const substitutedUserPromptTemplate = userPromptTemplate
        .replace(/{platform}/g, selectedPlatform)
        .replace(/{channel_type}/g, selectedChannelType);
    
    console.log('Substituted user prompt template:', substitutedUserPromptTemplate);
    
    // Update the table display with the actual content
    const tableSystemPrompt = document.getElementById('tableSystemPrompt');
    const tableUserPromptTemplate = document.getElementById('tableUserPromptTemplate');
    
    if (tableSystemPrompt) {
        tableSystemPrompt.textContent = systemPrompt;
    }
    
    if (tableUserPromptTemplate) {
        tableUserPromptTemplate.textContent = substitutedUserPromptTemplate;
    }
    
    // Combine them for the first section
    const defaultSystemTask = `${systemPrompt}\n\n${userPromptTemplate}`;
    const defaultBlogDetails = `Title: [Blog title will appear here]\nContent: [Blog content will appear here]`;
    const defaultRequirements = `- Tone: Conversational and engaging\n- Length: 150-200 characters\n- Include a clear call-to-action\n- Use up to 3 relevant hashtags\n\nReturn only the final Facebook post text, with no explanations or extra commentary.`;
    
    updateStructuredPromptDisplay(defaultSystemTask, defaultBlogDetails, defaultRequirements);
}

// Export the initialization function
window.initializeStructuredPromptDisplay = initializeStructuredPromptDisplay;

// Function to update the prompt display when platform/process changes
function updatePromptDisplayOnChange() {
    console.log('updatePromptDisplayOnChange called - updating prompt display');
    initializeStructuredPromptDisplay();
}

// Function to wait for LLM settings to be loaded before initializing
function waitForLLMSettingsAndInitialize() {
    console.log('Waiting for LLM settings to be loaded...');
    
    // Try to get LLM settings directly from the API
    fetch('/api/syndication/llm/settings')
        .then(response => response.json())
        .then(data => {
            console.log('LLM settings loaded from API:', data);
            if (data.settings && data.settings.user_prompt_template && data.settings.user_prompt_template.value) {
                console.log('Using API data for prompt template:', data.settings.user_prompt_template.value);
                // Update the textarea with the API data
                const userPromptTemplateElement = document.getElementById('llmUserPromptTemplate');
                if (userPromptTemplateElement) {
                    userPromptTemplateElement.value = data.settings.user_prompt_template.value;
                }
                // Now initialize the display
                initializeStructuredPromptDisplay();
            } else {
                console.log('No API data, falling back to textarea check...');
                checkTextareaAndInitialize();
            }
        })
        .catch(error => {
            console.error('Error loading LLM settings from API:', error);
            console.log('Falling back to textarea check...');
            checkTextareaAndInitialize();
        });
}

// Fallback function to check textarea content
function checkTextareaAndInitialize() {
    const userPromptTemplateElement = document.getElementById('llmUserPromptTemplate');
    
    console.log('User prompt template element found:', userPromptTemplateElement);
    if (userPromptTemplateElement) {
        console.log('Textarea value:', userPromptTemplateElement.value);
        console.log('Textarea textContent:', userPromptTemplateElement.textContent);
        console.log('Textarea innerHTML:', userPromptTemplateElement.innerHTML);
    }
    
    if (userPromptTemplateElement && userPromptTemplateElement.value && userPromptTemplateElement.value.trim() !== '') {
        console.log('LLM settings loaded from textarea, initializing prompt display');
        initializeStructuredPromptDisplay();
    } else {
        console.log('LLM settings not yet loaded, retrying in 500ms...');
        setTimeout(checkTextareaAndInitialize, 500);
    }
    
    // Force initialization after 3 seconds as a fallback
    setTimeout(() => {
        console.log('Forcing initialization after timeout...');
        initializeStructuredPromptDisplay();
    }, 3000);
}

// Function to set up event listeners for real-time updates
function setupPromptUpdateListeners() {
    console.log('Setting up prompt update listeners...');
    
    // Listen for changes to the User Prompt Template textarea
    const userPromptTemplateElement = document.getElementById('llmUserPromptTemplate');
    if (userPromptTemplateElement) {
        console.log('Found User Prompt Template element, adding input listener');
        userPromptTemplateElement.addEventListener('input', function() {
            console.log('User Prompt Template changed, updating display...');
            updatePromptDisplayOnChange();
        });
    }
    
    // Listen for changes to the System Prompt textarea
    const systemPromptElement = document.getElementById('llmSystemPrompt');
    if (systemPromptElement) {
        console.log('Found System Prompt element, adding input listener');
        systemPromptElement.addEventListener('input', function() {
            console.log('System Prompt changed, updating display...');
            updatePromptDisplayOnChange();
        });
    }
}

// Function to update the blog details display with dynamic content
function updateBlogDetailsDisplay() {
    console.log('Updating blog details display...');
    
    // Get the current post title
    const postTitleElement = document.getElementById('postTitle');
    const postTitle = postTitleElement ? postTitleElement.textContent : 'No post selected';
    
    // Get the selected section (first checked checkbox)
    const checkedCheckboxes = document.querySelectorAll('.task-checkbox:checked');
    let selectedSection = null;
    
    if (checkedCheckboxes.length > 0) {
        const firstCheckedIndex = parseInt(checkedCheckboxes[0].dataset.sectionIndex);
        // Get section data from the sections array (we'll need to access this)
        const sectionsData = window.currentSectionsData || [];
        selectedSection = sectionsData[firstCheckedIndex];
    }
    
    // Build the blog details content
    let blogDetailsContent = '';
    
    if (selectedSection) {
        blogDetailsContent = `POST TITLE: ${postTitle}\n\nSECTION TITLE: ${selectedSection.title || 'No section title'}\n\nSECTION OUTLINE: ${selectedSection.content || 'No section outline'}\n\nSECTION TEXT: ${selectedSection.polished || 'No section text'}`;
    } else {
        blogDetailsContent = `POST TITLE: ${postTitle}\n\nSECTION TITLE: No section selected\n\nSECTION OUTLINE: No section selected\n\nSECTION TEXT: No section selected`;
    }
    
    // Update the display
    const blogDetailsElement = document.getElementById('dynamicBlogDetails');
    if (blogDetailsElement) {
        blogDetailsElement.textContent = blogDetailsContent;
        console.log('Blog details updated:', blogDetailsContent);
    } else {
        console.error('Blog details element not found');
    }
}

// Export the update function
window.updatePromptDisplayOnChange = updatePromptDisplayOnChange;
window.setupPromptUpdateListeners = setupPromptUpdateListeners;
window.waitForLLMSettingsAndInitialize = waitForLLMSettingsAndInitialize;
window.updateBlogDetailsDisplay = updateBlogDetailsDisplay;
