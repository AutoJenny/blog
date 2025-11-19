/**
 * Simplified Header Image Generation Workflow
 * Handles the linear workflow: Input → Prompts → LLM → Generated Prompt → Image Settings → Images → Optimization → Optimized
 */

class HeaderImageSimplified {
    constructor(postId) {
        this.postId = postId;
        this.year = window.year;
        this.week = window.week;
        this.illustrationMethod = window.illustrationMethod || 'LLM-creation';
        this.init();
    }
    
    init() {
        this.loadInputData();
        this.loadLLMPrompts();
        this.loadExistingCompiledPrompt();
        this.loadExistingImages();
        this.setupLLMSettings();
        this.setupImageGeneration();
        this.setupOptimization();
        console.log('[HeaderImageSimplified] Initialized');
    }
    
    // Load existing compiled prompt from database
    async loadExistingCompiledPrompt() {
        try {
            // Use AbortController for timeout (browser compatible)
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            
            const response = await fetch(`/header/api/posts/${this.postId}/get-header-image`, {
                signal: controller.signal
            }).catch(() => {
                // Silently catch network errors and 404s - no header image exists yet, which is expected
                clearTimeout(timeoutId);
                return null;
            });
            
            clearTimeout(timeoutId);
            
            if (response && response.ok) {
                const data = await response.json();
                if (data.success && data.image_prompt) {
                    // Skip test prompts - they shouldn't be used
                    if (data.image_prompt.includes('TEST PROMPT FOR DEBUGGING')) {
                        console.warn('[HeaderImageSimplified] Skipping test prompt from database');
                        return;
                    }
                    
                    // Show generated prompt panel and populate it
                    const promptPanel = document.getElementById('generated-prompt-panel');
                    const promptTextarea = document.getElementById('generated-prompt-textarea');
                    
                    if (promptPanel && promptTextarea) {
                        promptPanel.style.display = 'block';
                        promptTextarea.value = data.image_prompt;
                        console.log('[HeaderImageSimplified] Loaded prompt from database:', data.image_prompt.substring(0, 100) + '...');
                        
                        // Enable image generation button
                        const generateImagesBtn = document.getElementById('generate-images-btn');
                        if (generateImagesBtn) {
                            generateImagesBtn.disabled = false;
                        }
                    }
                }
            }
            // Silently ignore 404s - no header image exists yet, which is expected
            // The fetch with catch() prevents console errors
        } catch (error) {
            // Silently ignore errors - no existing prompt is fine
            // Network errors are expected when no header image exists
        }
    }
    
    // Load existing images if they were already generated
    async loadExistingImages() {
        try {
            // Check if raw landscape image exists
            // Note: Header images use landscape/raw/ and portrait/raw/ subdirectories (same as section images)
            const landscapePath = `/static/content/posts/${this.postId}/header/landscape/raw/header.png`;
            const landscapeImg = document.getElementById('raw-landscape-image');
            const landscapePlaceholder = document.getElementById('raw-landscape-placeholder');
            
            if (landscapeImg) {
                // Use fetch to check if image exists before setting src (prevents 404 console errors)
                try {
                    const imgResponse = await fetch(landscapePath, { method: 'HEAD' });
                    if (imgResponse.ok) {
                        landscapeImg.src = landscapePath;
                        landscapeImg.style.display = 'block';
                        if (landscapePlaceholder) {
                            landscapePlaceholder.style.display = 'none';
                        }
                        // Show raw images panel
                        const rawImagesPanel = document.getElementById('raw-images-panel');
                        if (rawImagesPanel) {
                            rawImagesPanel.style.display = 'block';
                        }
                    } else {
                        // Image doesn't exist - show placeholder
                        if (landscapePlaceholder) {
                            landscapePlaceholder.style.display = 'block';
                        }
                    }
                } catch (err) {
                    // Silently fail - no image exists yet
                    if (landscapePlaceholder) {
                        landscapePlaceholder.style.display = 'block';
                    }
                }
            }
            
            // Check if raw portrait image exists
            const portraitPath = `/static/content/posts/${this.postId}/header/portrait/raw/header_portrait.png`;
            const portraitImg = document.getElementById('raw-portrait-image');
            const portraitPlaceholder = document.getElementById('raw-portrait-placeholder');
            
            if (portraitImg) {
                // Use fetch to check if image exists before setting src (prevents 404 console errors)
                try {
                    const imgResponse = await fetch(portraitPath, { method: 'HEAD' });
                    if (imgResponse.ok) {
                        portraitImg.src = portraitPath;
                        portraitImg.style.display = 'block';
                        if (portraitPlaceholder) {
                            portraitPlaceholder.style.display = 'none';
                        }
                    } else {
                        // Image doesn't exist - show placeholder (don't log 404)
                        if (portraitPlaceholder) {
                            portraitPlaceholder.style.display = 'block';
                        }
                    }
                } catch (err) {
                    // Silently fail - no image exists yet (don't log errors)
                    if (portraitPlaceholder) {
                        portraitPlaceholder.style.display = 'block';
                    }
                }
            }
        } catch (error) {
            console.log('[HeaderImageSimplified] No existing images found or error loading:', error);
        }
    }
    
    // Panel 1: Load Input Data (always visible)
    async loadInputData() {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const year = urlParams.get('year') || this.year;
            const week = urlParams.get('week') || this.week;
            
            let url = `/header/api/posts/${this.postId}/prompt-assembly-data?illustration_method=${encodeURIComponent(this.illustrationMethod)}`;
            if (year) url += `&year=${year}`;
            if (week) url += `&week=${week}`;
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success) {
                const themeDisplay = document.getElementById('theme-name-display');
                const ideaDisplay = document.getElementById('expanded-idea-display');
                
                if (themeDisplay) {
                    themeDisplay.textContent = data.theme_name || 'No theme selected';
                }
                if (ideaDisplay) {
                    ideaDisplay.textContent = data.expanded_idea || 'No expanded idea generated';
                }
            }
        } catch (error) {
            console.error('[HeaderImageSimplified] Error loading input data:', error);
        }
    }
    
    // Panel 2: Load LLM Prompts (default open)
    async loadLLMPrompts() {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const year = urlParams.get('year') || this.year;
            const week = urlParams.get('week') || this.week;
            
            let url = `/header/api/posts/${this.postId}/prompt-assembly-data?illustration_method=${encodeURIComponent(this.illustrationMethod)}`;
            if (year) url += `&year=${year}`;
            if (week) url += `&week=${week}`;
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success) {
                const systemDisplay = document.getElementById('system-prompt-display');
                const taskDisplay = document.getElementById('task-prompt-display');
                
                if (systemDisplay) {
                    systemDisplay.textContent = data.system_prompt || 'No system prompt found';
                }
                if (taskDisplay) {
                    taskDisplay.textContent = data.task_prompt || 'No task prompt found';
                }
            }
        } catch (error) {
            console.error('[HeaderImageSimplified] Error loading LLM prompts:', error);
        }
    }
    
    // Panel 3: Setup LLM Settings for prompt generation
    setupLLMSettings() {
        // Wait for LLM Settings panel to be initialized
        setTimeout(() => {
            // Initialize LLM Settings panel if available
            if (typeof LLMSettingsPanel !== 'undefined') {
                window.headerLLMSettings = new LLMSettingsPanel({
                    postId: this.postId,
                    onSettingsChange: () => {
                        // Settings changed
                    }
                });
            }
            
            // Attach listener to existing generate-llm-message-btn button
            const existingBtn = document.getElementById('generate-llm-message-btn');
            if (existingBtn) {
                // Remove any existing listeners by cloning
                const newBtn = existingBtn.cloneNode(true);
                existingBtn.parentNode.replaceChild(newBtn, existingBtn);
                // Attach listener to new button
                newBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.generateLLMMessage();
                });
                console.log('[HeaderImageSimplified] LLM message button listener attached');
            } else {
                console.error('[HeaderImageSimplified] generate-llm-message-btn not found!');
            }
        }, 500);
    }
    
    // Generate LLM-imaging message (Panel 4)
    async generateLLMMessage() {
        try {
            const btn = document.getElementById('generate-llm-message-btn');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
            }
            
            // Get LLM settings
            const provider = document.getElementById('llm-provider-select')?.value || 'Ollama';
            const model = document.getElementById('llm-model-select')?.value || 'llama3.2:latest';
            
            // Get theme and expanded idea
            const urlParams = new URLSearchParams(window.location.search);
            const year = urlParams.get('year') || this.year;
            const week = urlParams.get('week') || this.week;
            
            // Validate input data - reject placeholder text
            const themeName = document.getElementById('theme-name-display')?.textContent?.trim();
            const expandedIdea = document.getElementById('expanded-idea-display')?.textContent?.trim();
            
            const PLACEHOLDER_TEXTS = ['Loading...', 'No theme selected', 'No expanded idea generated', ''];
            let theme_name = themeName;
            let expanded_idea = expandedIdea;
            
            // Check if data is valid
            if (!theme_name || PLACEHOLDER_TEXTS.includes(theme_name) || 
                !expanded_idea || PLACEHOLDER_TEXTS.includes(expanded_idea)) {
                console.log('[HeaderImageSimplified] Invalid input data detected, fetching from API...');
                // Fetch from API first
                await this.loadInputData();
                // Retry with fresh data
                const freshTheme = document.getElementById('theme-name-display')?.textContent?.trim();
                const freshIdea = document.getElementById('expanded-idea-display')?.textContent?.trim();
                if (!freshTheme || PLACEHOLDER_TEXTS.includes(freshTheme) || 
                    !freshIdea || PLACEHOLDER_TEXTS.includes(freshIdea)) {
                    alert('Error: Theme and expanded idea data not available. Please ensure the Planning stage is complete.');
                    return;
                }
                // Use fresh data
                theme_name = freshTheme;
                expanded_idea = freshIdea;
            }
            
            console.log('[HeaderImageSimplified] Sending to API - theme_name:', theme_name?.substring(0, 50), 'expanded_idea:', expanded_idea?.substring(0, 50));
            
            // Use the compile-header-prompt endpoint which uses LLM to generate the prompt
            let url = `/header/api/posts/${this.postId}/compile-header-prompt?illustration_method=${encodeURIComponent(this.illustrationMethod)}`;
            if (year) url += `&year=${year}`;
            if (week) url += `&week=${week}`;
            
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    theme_name: theme_name,
                    expanded_idea: expanded_idea,
                    model: model,
                    provider: provider
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.compiled_prompt) {
                // Show generated prompt panel
                const promptPanel = document.getElementById('generated-prompt-panel');
                const promptTextarea = document.getElementById('generated-prompt-textarea');
                
                if (promptPanel) {
                    promptPanel.style.display = 'block';
                    // Scroll to it
                    promptPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
                if (promptTextarea) {
                    promptTextarea.value = data.compiled_prompt;
                }
                
                // Enable image generation button
                const generateImagesBtn = document.getElementById('generate-images-btn');
                if (generateImagesBtn) {
                    generateImagesBtn.disabled = false;
                }
            } else {
                alert('Error generating prompt: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('[HeaderImageSimplified] Error generating LLM message:', error);
            alert('Error: ' + error.message);
        } finally {
            const btn = document.getElementById('generate-llm-message-btn');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-magic"></i> Generate LLM-Imaging Message';
            }
        }
    }
    
    // Panel 5: Setup Image Generation
    setupImageGeneration() {
        const setupBtn = () => {
            const generateBtn = document.getElementById('generate-images-btn');
            if (generateBtn) {
                // Clone to remove existing listeners
                const newBtn = generateBtn.cloneNode(true);
                generateBtn.parentNode.replaceChild(newBtn, generateBtn);
                // Attach listener
                newBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.generateImages();
                });
                console.log('[HeaderImageSimplified] Image generation button listener attached');
                return true; // Success
            } else {
                console.warn('[HeaderImageSimplified] generate-images-btn not found, retrying...');
                return false; // Not found
            }
        };
        
        // Try immediately
        if (!setupBtn()) {
            // Retry after short delay if not found
            setTimeout(() => {
                if (!setupBtn()) {
                    console.error('[HeaderImageSimplified] Failed to find generate-images-btn after retry!');
                }
            }, 200);
        }
    }
    
    // Generate Images (Panel 6)
    async generateImages() {
        try {
            const btn = document.getElementById('generate-images-btn');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
            }
            
            const promptTextarea = document.getElementById('generated-prompt-textarea');
            if (!promptTextarea || !promptTextarea.value.trim()) {
                alert('Please generate a prompt first');
                return;
            }
            
            const model = document.getElementById('image-model-select')?.value || 'gpt-image-1';
            const landscapeSize = document.getElementById('landscape-size')?.value || '1536x1024';
            const portraitSize = document.getElementById('portrait-size')?.value || '1024x1536';
            // gpt-image-1 uses 'high', 'medium', 'low', 'auto' - not 'hd'
            let quality = document.getElementById('image-quality')?.value || 'high';
            // Map 'hd' to 'high' for backwards compatibility
            if (quality === 'hd') {
                quality = 'high';
            }
            
            const urlParams = new URLSearchParams(window.location.search);
            const year = urlParams.get('year') || this.year;
            const week = urlParams.get('week') || this.week;
            
            let url = `/header/api/posts/${this.postId}/generate-header-image?illustration_method=${encodeURIComponent(this.illustrationMethod)}`;
            if (year) url += `&year=${year}`;
            if (week) url += `&week=${week}`;
            
            // Use the prompt from textarea, but validate it's not a test prompt
            const promptToUse = promptTextarea.value.trim();
            if (promptToUse.includes('TEST PROMPT FOR DEBUGGING') || promptToUse.length < 50) {
                console.warn('[HeaderImageSimplified] Invalid or test prompt detected, attempting to load from database...');
                // Try to reload the prompt from database first
                await this.loadExistingCompiledPrompt();
                const updatedPrompt = document.getElementById('generated-prompt-textarea')?.value.trim();
                if (updatedPrompt && !updatedPrompt.includes('TEST PROMPT')) {
                    console.log('[HeaderImageSimplified] Loaded valid prompt from database');
                } else {
                    alert('Please generate a valid prompt first using the "Generate LLM-Imaging Message" button.');
                    if (btn) {
                        btn.disabled = false;
                        btn.innerHTML = '<i class="fas fa-image"></i> Generate Images';
                    }
                    return;
                }
            }
            
            // Image generation can take 2-3 minutes, so we need a longer timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minute timeout
            
            let response;
            try {
                response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        image_prompt: document.getElementById('generated-prompt-textarea').value.trim(),
                        model_name: model,
                        parameters: {
                            size: landscapeSize,
                            portrait_size: portraitSize,
                            quality: quality
                        },
                        use_renderer: false
                    }),
                    signal: controller.signal
                });
                clearTimeout(timeoutId);
            } catch (fetchError) {
                clearTimeout(timeoutId);
                if (fetchError.name === 'AbortError') {
                    throw new Error('Request timed out after 5 minutes. Image generation may still be in progress.');
                }
                throw fetchError;
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Show raw images panel
                const rawImagesPanel = document.getElementById('raw-images-panel');
                if (rawImagesPanel) {
                    rawImagesPanel.style.display = 'block';
                    
                    // Scroll to raw images panel
                    setTimeout(() => {
                        rawImagesPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }, 100);
                }
                
                // Display landscape image (use raw_path for raw images panel)
                const landscapeImg = document.getElementById('raw-landscape-image');
                const landscapePlaceholder = document.getElementById('raw-landscape-placeholder');
                if (landscapeImg) {
                    // Prefer raw_path (web path to raw image), fallback to optimized
                    let landscapePath = data.raw_path;
                    // Ensure it starts with / if it's a web path
                    if (landscapePath && !landscapePath.startsWith('/') && !landscapePath.startsWith('http')) {
                        landscapePath = '/' + landscapePath;
                    }
                    if (!landscapePath) {
                        landscapePath = data.optimized_path;
                    }
                    if (landscapePath) {
                        // Use Image object to test load before setting src (handles errors gracefully)
                        const testImg = new Image();
                        testImg.onload = () => {
                            // Use the test image src (which may have cache bust) to ensure it loads
                            landscapeImg.src = testImg.src;
                            landscapeImg.style.display = 'block';
                            if (landscapePlaceholder) {
                                landscapePlaceholder.style.display = 'none';
                            }
                            console.log('[HeaderImageSimplified] Landscape image loaded successfully:', testImg.src);
                        };
                        testImg.onerror = () => {
                            console.error('[HeaderImageSimplified] Landscape image failed to load:', landscapePath);
                            // Show error message to user
                            if (landscapePlaceholder) {
                                landscapePlaceholder.textContent = 'Image failed to load. Path: ' + landscapePath + '. Retrying...';
                                landscapePlaceholder.style.color = '#ef4444';
                            }
                            // Retry with longer delay and cache bust - file might still be writing
                            setTimeout(() => {
                                testImg.src = landscapePath + (landscapePath.includes('?') ? '&' : '?') + 't=' + Date.now();
                            }, 2000);
                        };
                        // Add a small delay to ensure file is written to disk
                        setTimeout(() => {
                            testImg.src = landscapePath;
                        }, 1000);
                    } else {
                        console.error('[HeaderImageSimplified] No landscape path in response:', data);
                        if (landscapePlaceholder) {
                            landscapePlaceholder.textContent = 'No image path returned from server';
                            landscapePlaceholder.style.color = '#ef4444';
                        }
                    }
                }
                
                // Display portrait image if available
                // gpt-image-1 generates both landscape and portrait
                const portraitImg = document.getElementById('raw-portrait-image');
                const portraitPlaceholder = document.getElementById('raw-portrait-placeholder');
                if (portraitImg) {
                    // Check if response has portrait path
                    let portraitPath = data.portrait_path;
                    
                    // If not in response but portrait was generated, construct path
                    if (!portraitPath && data.portrait_generated) {
                        // Handle both old and new path structures
                        portraitPath = data.raw_path?.replace('/header/landscape/raw/header.png', '/header/portrait/raw/header_portrait.png')
                                     ?.replace('/header/raw/header.png', '/header/portrait/raw/header_portrait.png') ||
                                     `/static/content/posts/${this.postId}/header/portrait/raw/header_portrait.png`;
                    }
                    
                    // If still no path, try to load from expected location
                    if (!portraitPath) {
                        portraitPath = `/static/content/posts/${this.postId}/header/portrait/raw/header_portrait.png`;
                    }
                    
                    console.log('[HeaderImageSimplified] Attempting to load portrait image:', portraitPath, 'portrait_generated:', data.portrait_generated);
                    
                    // Try to load portrait image with retry logic
                    const img = new Image();
                    img.onload = () => {
                        portraitImg.src = img.src;
                        portraitImg.style.display = 'block';
                        if (portraitPlaceholder) {
                            portraitPlaceholder.style.display = 'none';
                        }
                        console.log('[HeaderImageSimplified] Portrait image loaded successfully:', img.src);
                    };
                    img.onerror = () => {
                        console.warn('[HeaderImageSimplified] Portrait image not found at:', portraitPath);
                        // Show message that portrait might still be generating
                        if (portraitPlaceholder && data.portrait_generated) {
                            portraitPlaceholder.textContent = 'Portrait image generating... Retrying...';
                            portraitPlaceholder.style.color = '#fbbf24';
                        }
                        // Retry with cache bust - might still be generating
                        setTimeout(() => {
                            const retryImg = new Image();
                            retryImg.onload = () => {
                                portraitImg.src = portraitPath + '?t=' + Date.now();
                                portraitImg.style.display = 'block';
                                if (portraitPlaceholder) {
                                    portraitPlaceholder.style.display = 'none';
                                }
                                console.log('[HeaderImageSimplified] Portrait image loaded on retry:', retryImg.src);
                            };
                            retryImg.onerror = () => {
                                console.warn('[HeaderImageSimplified] Portrait image still not found after retry');
                                if (portraitPlaceholder) {
                                    portraitPlaceholder.textContent = 'No portrait image generated yet';
                                    portraitPlaceholder.style.color = '#64748b';
                                }
                            };
                            retryImg.src = portraitPath + '?t=' + Date.now();
                        }, 3000);
                    };
                    // Add delay before first attempt to allow file to be written
                    setTimeout(() => {
                        img.src = portraitPath;
                    }, 1500);
                }
                
                // Enable optimization button
                const optimizeBtn = document.getElementById('optimize-image-btn');
                if (optimizeBtn) {
                    optimizeBtn.disabled = false;
                }
            } else {
                alert('Error generating images: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('[HeaderImageSimplified] Error generating images:', error);
            alert('Error: ' + error.message);
        } finally {
            const btn = document.getElementById('generate-images-btn');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-image"></i> Generate Images (Landscape + Portrait)';
            }
        }
    }
    
    // Panel 7: Setup Optimization
    setupOptimization() {
        const setupBtn = () => {
            const optimizeBtn = document.getElementById('optimize-image-btn');
            if (optimizeBtn) {
                // Clone to remove existing listeners
                const newBtn = optimizeBtn.cloneNode(true);
                optimizeBtn.parentNode.replaceChild(newBtn, optimizeBtn);
                // Attach listener
                newBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.optimizeImages();
                });
                console.log('[HeaderImageSimplified] Optimization button listener attached');
                return true; // Success
            } else {
                console.warn('[HeaderImageSimplified] optimize-image-btn not found, retrying...');
                return false; // Not found
            }
        };
        
        // Try immediately
        if (!setupBtn()) {
            // Retry after short delay if not found
            setTimeout(() => {
                if (!setupBtn()) {
                    console.error('[HeaderImageSimplified] Failed to find optimize-image-btn after retry!');
                }
            }, 200);
        }
    }
    
    // Optimize Images (Panel 8)
    async optimizeImages() {
        try {
            const btn = document.getElementById('optimize-image-btn');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Optimizing...';
            }
            
            const response = await fetch(`/header/api/posts/${this.postId}/optimize-header-image`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Show optimized images panel
                const optimizedPanel = document.getElementById('optimized-images-panel');
                if (optimizedPanel) {
                    optimizedPanel.style.display = 'block';
                    optimizedPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
                
                // Display optimized landscape image
                const landscapeImg = document.getElementById('optimized-landscape-image');
                const landscapePlaceholder = document.getElementById('optimized-landscape-placeholder');
                if (landscapeImg) {
                    const landscapePath = data.optimized_path || data.landscape_path;
                    if (landscapePath) {
                        landscapeImg.src = landscapePath;
                        landscapeImg.style.display = 'block';
                        if (landscapePlaceholder) {
                            landscapePlaceholder.style.display = 'none';
                        }
                    }
                }
                
                // Display optimized portrait image
                const portraitImg = document.getElementById('optimized-portrait-image');
                const portraitPlaceholder = document.getElementById('optimized-portrait-placeholder');
                if (portraitImg) {
                    // Try to get portrait path from response
                    let portraitPath = data.portrait_optimized_path || data.portrait_path;
                    
                    // If not in response, construct from landscape path
                    if (!portraitPath && data.optimized_path) {
                        // Handle both old and new path structures
                        portraitPath = data.optimized_path.replace('/header/landscape/optimized/header.jpg', '/header/portrait/optimized/header_portrait.jpg')
                                           .replace('/header/optimized/header.jpg', '/header/portrait/optimized/header_portrait.jpg')
                                           .replace('/header/landscape/raw/header.png', '/header/portrait/optimized/header_portrait.jpg')
                                           .replace('/header/raw/header.png', '/header/portrait/optimized/header_portrait.jpg');
                    }
                    
                    // Fallback: try expected location
                    if (!portraitPath) {
                        portraitPath = `/static/content/posts/${this.postId}/header/portrait/optimized/header_portrait.jpg`;
                    }
                    
                    // Try to load portrait optimized image
                    const img = new Image();
                    img.onload = () => {
                        portraitImg.src = portraitPath;
                        portraitImg.style.display = 'block';
                        if (portraitPlaceholder) {
                            portraitPlaceholder.style.display = 'none';
                        }
                    };
                    img.onerror = () => {
                        console.warn('[HeaderImageSimplified] Optimized portrait image not found at:', portraitPath);
                    };
                    img.src = portraitPath;
                }
            } else {
                alert('Error optimizing images: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('[HeaderImageSimplified] Error optimizing images:', error);
            alert('Error: ' + error.message);
        } finally {
            const btn = document.getElementById('optimize-image-btn');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-magic"></i> Optimize and Watermark';
            }
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[HeaderImageSimplified] DOMContentLoaded - postId:', window.postId, 'substage:', window.currentSubstage);
    if (window.postId && window.currentSubstage === 'header-image') {
        window.headerImageSimplified = new HeaderImageSimplified(window.postId);
    } else {
        console.error('[HeaderImageSimplified] Missing postId or wrong substage!', {
            postId: window.postId,
            substage: window.currentSubstage
        });
    }
});

