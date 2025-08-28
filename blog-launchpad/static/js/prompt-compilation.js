// Prompt Compilation Module
// Extracted from syndication_create_piece.js for modularization

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
    const systemTask = `You are a social media content specialist.\n\nYour task: Create an engaging Facebook post based on the blog details below.`;
    
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
    const defaultSystemTask = `You are a social media content specialist.\n\nYour task: Create an engaging Facebook post based on the blog details below.`;
    const defaultBlogDetails = `Title: [Blog title will appear here]\nContent: [Blog content will appear here]`;
    const defaultRequirements = `- Tone: Conversational and engaging\n- Length: 150-200 characters\n- Include a clear call-to-action\n- Use up to 3 relevant hashtags\n\nReturn only the final Facebook post text, with no explanations or extra commentary.`;
    
    updateStructuredPromptDisplay(defaultSystemTask, defaultBlogDetails, defaultRequirements);
}

// Export the initialization function
window.initializeStructuredPromptDisplay = initializeStructuredPromptDisplay;
