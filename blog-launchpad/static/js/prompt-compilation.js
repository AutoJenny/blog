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
    
            // Get prompts from database via UI elements (dynamic)
            const systemPrompt = llmSettings.system_prompt || 'No system prompt configured';
            const userPrompt = llmSettings.user_prompt_template || 'No user prompt template configured';
    
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
    
    // Get requirements from database (dynamic) - this should come from channel_requirements table
    const structuredRequirements = 'Requirements will be loaded from database';
    
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
    const defaultSystemTask = `${systemPrompt}\n\n${substitutedUserPromptTemplate}`;
    
    // Get dynamic blog details and requirements from the Input Assembly panel
    const dynamicBlogDetails = getDynamicBlogDetails();
    const dynamicRequirements = getDynamicRequirements();
    
    // Update both panels with the same content
    updateStructuredPromptDisplay(defaultSystemTask, dynamicBlogDetails, dynamicRequirements);
    
    // Also update the Input Assembly panel to ensure synchronization
    updateInputAssemblyPanel(defaultSystemTask, dynamicBlogDetails, dynamicRequirements);
}

// Helper function to get dynamic blog details from Input Assembly panel
function getDynamicBlogDetails() {
    const blogDetailsElement = document.getElementById('dynamicBlogDetails');
    if (blogDetailsElement && blogDetailsElement.textContent && blogDetailsElement.textContent !== 'Loading blog details...') {
        return blogDetailsElement.textContent;
    }
    // Fallback to default if not loaded yet
    return 'POST TITLE: No post selected\n\nSECTION TITLE: No section selected\n\nSECTION OUTLINE: No section selected\n\nSECTION TEXT: No section selected';
}

// Helper function to get dynamic requirements from Input Assembly panel
function getDynamicRequirements() {
    const requirementsElement = document.getElementById('dynamicRequirements');
    if (requirementsElement && requirementsElement.innerHTML && requirementsElement.innerHTML !== 'Loading requirements...') {
        // Convert <br> tags back to \n for the Final Assembled Prompt
        return requirementsElement.innerHTML.replace(/<br>/g, '\n');
    }
    // Fallback to default if not loaded yet
    // Requirements should come from database - this is a placeholder
    return 'Requirements will be loaded from database';
}

// Function to update the Input Assembly panel to ensure synchronization
function updateInputAssemblyPanel(systemTask, blogDetails, requirements) {
    // Update the table display with the actual content
    const tableSystemPrompt = document.getElementById('tableSystemPrompt');
    const tableUserPromptTemplate = document.getElementById('tableUserPromptTemplate');
    
    if (tableSystemPrompt) {
        tableSystemPrompt.textContent = systemTask.split('\n\n')[0]; // Just the system prompt part
    }
    
    if (tableUserPromptTemplate) {
        tableUserPromptTemplate.textContent = systemTask.split('\n\n')[1] || ''; // Just the user prompt part
    }
    
    // Update blog details if available
    const dynamicBlogDetailsElement = document.getElementById('dynamicBlogDetails');
    if (dynamicBlogDetailsElement && blogDetails && blogDetails !== 'Loading blog details...') {
        dynamicBlogDetailsElement.textContent = blogDetails;
    }
    
    // Update requirements if available
    const dynamicRequirementsElement = document.getElementById('dynamicRequirements');
    if (dynamicRequirementsElement && requirements && requirements !== 'Loading requirements...') {
        // Convert \n to <br> tags for HTML display
        const htmlContent = requirements.replace(/\n/g, '<br>');
        dynamicRequirementsElement.innerHTML = htmlContent;
    }
}

// Export the initialization function
window.initializeStructuredPromptDisplay = initializeStructuredPromptDisplay;

// Function to update the prompt display when platform/process changes
function updatePromptDisplayOnChange() {
    console.log('updatePromptDisplayOnChange called - updating prompt display');
    initializeStructuredPromptDisplay();
    
    // Also update the Final Assembled Prompt system/task section
    const systemPromptElement = document.getElementById('llmSystemPrompt');
    const userPromptTemplateElement = document.getElementById('llmUserPromptTemplate');
    
    if (systemPromptElement && userPromptTemplateElement) {
        const systemPrompt = systemPromptElement.value || 'No system prompt configured';
        let userPromptTemplate = userPromptTemplateElement.value || 'No user prompt template configured';
        
        // Get the selected platform and channel type values for substitution
        const platformSelector = document.getElementById('platformSelector');
        const processSelector = document.getElementById('processSelector');
        
        if (platformSelector && processSelector && processSelector.selectedIndex > 0) {
            const selectedPlatform = platformSelector.options[platformSelector.selectedIndex]?.text || 'No platform selected';
            let channelType = 'No channel type selected';
            
            const selectedProcessOption = processSelector.options[processSelector.selectedIndex];
            if (selectedProcessOption && selectedProcessOption.textContent.includes('(')) {
                channelType = selectedProcessOption.textContent.split('(')[1].replace(')', '');
                // Convert technical terms to natural language
                if (channelType === 'feed_post') channelType = 'feed post';
                else if (channelType === 'story_post') channelType = 'story post';
                else if (channelType === 'reels_caption') channelType = 'reels caption';
                else if (channelType === 'group_post') channelType = 'group post';
            }
            
            // Substitute placeholders
            userPromptTemplate = userPromptTemplate
                .replace(/{platform}/g, selectedPlatform)
                .replace(/{channel_type}/g, channelType);
        }
        
        const combinedSystemTask = `${systemPrompt}\n\n${userPromptTemplate}`;
        
        // Update the Final Assembled Prompt system/task section
        const finalSystemTaskElement = document.getElementById('promptSystemTask');
        if (finalSystemTaskElement) {
            finalSystemTaskElement.textContent = combinedSystemTask;
            console.log('Final Assembled Prompt system/task synchronized');
        }
        
        // Also update the Final Assembled Prompt blog details and requirements sections
        // Get the current blog details and requirements from the Input Assembly panel
        const dynamicBlogDetailsElement = document.getElementById('dynamicBlogDetails');
        const dynamicRequirementsElement = document.getElementById('dynamicRequirements');
        
        if (dynamicBlogDetailsElement) {
            const finalBlogDetailsElement = document.getElementById('promptBlogDetails');
            if (finalBlogDetailsElement) {
                finalBlogDetailsElement.textContent = dynamicBlogDetailsElement.textContent;
                console.log('Final Assembled Prompt blog details synchronized');
            }
        }
        
        if (dynamicRequirementsElement) {
            const finalRequirementsElement = document.getElementById('promptRequirements');
            if (finalRequirementsElement) {
                // Convert HTML content back to plain text for the prompt
                const plainTextRequirements = dynamicRequirementsElement.textContent || dynamicRequirementsElement.innerText;
                finalRequirementsElement.textContent = plainTextRequirements;
                console.log('Final Assembled Prompt requirements synchronized');
            }
        }
    }
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
        
        // Synchronize the Final Assembled Prompt panel
        const finalBlogDetailsElement = document.getElementById('promptBlogDetails');
        if (finalBlogDetailsElement) {
            finalBlogDetailsElement.textContent = blogDetailsContent;
            console.log('Final Assembled Prompt blog details synchronized');
        }
    } else {
        console.error('Blog details element not found');
    }
}

// Function to update the requirements display with dynamic content from database
function updateRequirementsDisplay() {
    console.log('=== updateRequirementsDisplay() called ===');
    
    // Get the current platform and channel type
    const platformSelector = document.getElementById('platformSelector');
    const processSelector = document.getElementById('processSelector');
    
    console.log('Platform selector:', platformSelector);
    console.log('Process selector:', processSelector);
    
    if (!platformSelector || !processSelector || processSelector.selectedIndex === 0) {
        console.log('Platform or process not selected yet');
        return;
    }
    
    const selectedPlatform = platformSelector.options[platformSelector.selectedIndex]?.text;
    const selectedProcess = processSelector.options[processSelector.selectedIndex]?.textContent;
    
    console.log('Selected platform:', selectedPlatform);
    console.log('Selected process:', selectedProcess);
    
    if (!selectedPlatform || !selectedProcess) {
        console.log('Platform or process not available');
        return;
    }
    
    // Extract channel type from process text (e.g., "Facebook Feed Post (feed_post)")
    let channelType = 'feed_post'; // Default
    if (selectedProcess.includes('(')) {
        channelType = selectedProcess.split('(')[1].replace(')', '');
    }
    
    console.log('Fetching requirements for:', selectedPlatform, channelType);
    
    // Fetch requirements from the database
    // Map process selector value to channel type ID
    let channelTypeId = 1; // Default to feed_post ID
    if (processSelector.value === 'facebook_feed_post') {
        channelTypeId = 1; // feed_post
    } else if (processSelector.value === 'facebook_story_post') {
        channelTypeId = 2; // story_post (if it exists)
    } else if (processSelector.value === 'facebook_reels_caption') {
        channelTypeId = 3; // reels_caption (if it exists)
    } else if (processSelector.value === 'facebook_group_post') {
        channelTypeId = 4; // group_post (if it exists)
    }
    
    // Get the actual platform ID from the selected option
    const selectedPlatformOption = platformSelector.options[platformSelector.selectedIndex];
    let platformId = 1; // Default to Facebook (ID 1)
    
    // Map platform names to IDs
    if (platformSelector.value === 'facebook') {
        platformId = 1;
    } else if (platformSelector.value === 'twitter') {
        platformId = 2;
    } else if (platformSelector.value === 'linkedin') {
        platformId = 3;
    }
    
    console.log('Platform selector value:', platformSelector.value);
    console.log('Selected platform option:', selectedPlatformOption);
    console.log('Using platform ID:', platformId);
    console.log('Using channel type ID:', channelTypeId);
    
    const apiUrl = `/api/social-media/platforms/${platformId}/channels/${channelTypeId}/requirements`;
    console.log('API URL:', apiUrl);
    
    fetch(apiUrl)
        .then(response => {
            console.log('API response status:', response.status);
            if (response.status === 404) {
                throw new Error('Requirements not found for this platform/channel combination');
            }
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(requirements => {
            console.log('Requirements fetched:', requirements);
            
            // Validate response before parsing
            if (!requirements || !Array.isArray(requirements)) {
                console.error('Invalid requirements response:', requirements);
                throw new Error('Requirements response is not an array');
            }
            
            // Build the requirements content
            let requirementsContent = '';
            
            try {
                // Find specific requirements with safe property access
                const toneRequirement = requirements.find(r => r && r.requirement_key === 'tone_guidelines');
                const lengthRequirement = requirements.find(r => r && r.requirement_key === 'content_length');
                const ctaRequirement = requirements.find(r => r && r.requirement_key === 'cta_strategy');
                const hashtagRequirement = requirements.find(r => r && r.requirement_key === 'max_hashtags');
                const finalInstruction = requirements.find(r => r && r.requirement_key === 'final_instruction');
                const finalInstructionValue = finalInstruction ? finalInstruction.requirement_value : null;
            
                console.log('Found requirements:', {
                    toneRequirement,
                    lengthRequirement,
                    ctaRequirement,
                    hashtagRequirement,
                    finalInstruction: finalInstructionValue
                });
                
                // Build the display content
                if (toneRequirement) {
                    requirementsContent += `- Tone: ${toneRequirement.requirement_value}\n`;
                }
                
                if (lengthRequirement) {
                    requirementsContent += `- Length: ${lengthRequirement.requirement_value}\n`;
                }
                
                if (ctaRequirement) {
                    requirementsContent += `- Include a call-to-action\n`;
                }
                
                if (hashtagRequirement) {
                    requirementsContent += `- Use up to ${hashtagRequirement.requirement_value} relevant hashtags\n`;
                }
                
                // Add double line break before final instruction
                requirementsContent += '\n\n';
                
                // Make final instruction dynamic based on platform and channel
                if (finalInstructionValue) {
                    requirementsContent += finalInstructionValue;
                } else {
                    // Create dynamic instruction based on selected platform and channel
                    const platformName = platformSelector.options[platformSelector.selectedIndex]?.text || 'Facebook';
                    const channelType = processSelector.options[processSelector.selectedIndex]?.textContent?.split(' (')[0] || 'post';
                    requirementsContent += `Create the ${platformName} ${channelType} now:`;
                }
                
                console.log('Final requirements content:', requirementsContent);
                
                // Update the display
                const requirementsElement = document.getElementById('dynamicRequirements');
                console.log('Looking for requirements element with ID "dynamicRequirements"');
                console.log('Found element:', requirementsElement);
                if (requirementsElement) {
                    // Convert \n to <br> tags for proper HTML line breaks
                    const htmlContent = requirementsContent.replace(/\n/g, '<br>');
                    requirementsElement.innerHTML = htmlContent;
                    console.log('Requirements element updated successfully');
                    console.log('New content:', requirementsElement.innerHTML);
                    
                    // Synchronize the Final Assembled Prompt panel
                    const finalRequirementsElement = document.getElementById('promptRequirements');
                    if (finalRequirementsElement) {
                        finalRequirementsElement.textContent = requirementsContent;
                        console.log('Final Assembled Prompt requirements synchronized');
                    }
                } else {
                    console.error('Requirements element not found');
                }
            } catch (parseError) {
                console.error('Error parsing requirements:', parseError);
                // Fallback to default content
                const requirementsElement = document.getElementById('dynamicRequirements');
                if (requirementsElement) {
                    const platformName = platformSelector.options[platformSelector.selectedIndex]?.text || 'Facebook';
                    const channelType = processSelector.options[processSelector.selectedIndex]?.textContent?.split(' (')[0] || 'post';
                    // Requirements should come from database - this is a placeholder
                    const fallbackContent = `Requirements will be loaded from database for ${platformName} ${channelType}`;
                    const htmlContent = fallbackContent.replace(/\n/g, '<br>');
                    requirementsElement.innerHTML = htmlContent;
                }
            }
        })
        .catch(error => {
            console.error('Error fetching requirements:', error);
            // Fallback to default content
            const requirementsElement = document.getElementById('dynamicRequirements');
            if (requirementsElement) {
                // Create dynamic fallback content
                const platformName = platformSelector.options[platformSelector.selectedIndex]?.text || 'Facebook';
                const channelType = processSelector.options[processSelector.selectedIndex]?.textContent?.split(' (')[0] || 'post';
                // Requirements should come from database - this is a placeholder
                const fallbackContent = `Requirements will be loaded from database for ${platformName} ${channelType}`;
                // Convert \n to <br> tags for proper HTML line breaks
                const htmlContent = fallbackContent.replace(/\n/g, '<br>');
                requirementsElement.innerHTML = htmlContent;
            }
        });
}

// Export the update function
window.updatePromptDisplayOnChange = updatePromptDisplayOnChange;
window.setupPromptUpdateListeners = setupPromptUpdateListeners;
window.waitForLLMSettingsAndInitialize = waitForLLMSettingsAndInitialize;
window.updateBlogDetailsDisplay = updateBlogDetailsDisplay;
window.updateRequirementsDisplay = updateRequirementsDisplay;
window.getDynamicBlogDetails = getDynamicBlogDetails;
window.getDynamicRequirements = getDynamicRequirements;
window.updateInputAssemblyPanel = updateInputAssemblyPanel;
