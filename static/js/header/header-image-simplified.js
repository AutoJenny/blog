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
            const response = await fetch(`/header/api/posts/${this.postId}/get-header-image`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.image_prompt) {
                    // Show generated prompt panel and populate it
                    const promptPanel = document.getElementById('generated-prompt-panel');
                    const promptTextarea = document.getElementById('generated-prompt-textarea');
                    
                    if (promptPanel && promptTextarea) {
                        promptPanel.style.display = 'block';
                        promptTextarea.value = data.image_prompt;
                        
                        // Enable image generation button
                        const generateImagesBtn = document.getElementById('generate-images-btn');
                        if (generateImagesBtn) {
                            generateImagesBtn.disabled = false;
                        }
                    }
                }
            }
        } catch (error) {
            // No existing prompt is fine, just log it
            console.log('[HeaderImageSimplified] No existing compiled prompt found');
        }
    }
    
    // Load existing images if they were already generated
    async loadExistingImages() {
        try {
            // Check if raw landscape image exists
            const landscapePath = `/static/content/posts/${this.postId}/header/raw/header.png`;
            const landscapeImg = document.getElementById('raw-landscape-image');
            const landscapePlaceholder = document.getElementById('raw-landscape-placeholder');
            
            if (landscapeImg) {
                const testImg = new Image();
                testImg.onload = () => {
                    landscapeImg.src = testImg.src;
                    landscapeImg.style.display = 'block';
                    if (landscapePlaceholder) {
                        landscapePlaceholder.style.display = 'none';
                    }
                    // Show raw images panel
                    const rawImagesPanel = document.getElementById('raw-images-panel');
                    if (rawImagesPanel) {
                        rawImagesPanel.style.display = 'block';
                    }
                    console.log('[HeaderImageSimplified] Loaded existing landscape image:', testImg.src);
                };
                testImg.onerror = () => {
                    console.log('[HeaderImageSimplified] No existing raw landscape image found');
                };
                testImg.src = landscapePath + '?t=' + Date.now();
            }
            
            // Check if raw portrait image exists
            const portraitPath = `/static/content/posts/${this.postId}/header/portrait/raw/header_portrait.png`;
            const portraitImg = document.getElementById('raw-portrait-image');
            const portraitPlaceholder = document.getElementById('raw-portrait-placeholder');
            
            if (portraitImg) {
                const testPortraitImg = new Image();
                testPortraitImg.onload = () => {
                    portraitImg.src = testPortraitImg.src;
                    portraitImg.style.display = 'block';
                    if (portraitPlaceholder) {
                        portraitPlaceholder.style.display = 'none';
                    }
                    console.log('[HeaderImageSimplified] Loaded existing portrait image:', testPortraitImg.src);
                };
                testPortraitImg.onerror = () => {
                    console.log('[HeaderImageSimplified] No existing raw portrait image found');
                };
                testPortraitImg.src = portraitPath + '?t=' + Date.now();
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
            
            // Add button to generate LLM-imaging message in LLM Settings panel header
            const llmSettingsPanel = document.getElementById('llm-settings-panel');
            if (llmSettingsPanel) {
                const headerActions = llmSettingsPanel.querySelector('.header-actions');
                if (headerActions && !headerActions.querySelector('#generate-llm-message-btn')) {
                    const generateBtn = document.createElement('button');
                    generateBtn.id = 'generate-llm-message-btn';
                    generateBtn.className = 'btn-primary';
                    generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate LLM-Imaging Message';
                    generateBtn.style.cssText = 'padding: 0.5rem 1rem; border-radius: 4px; background: #3b82f6; color: white; border: none; cursor: pointer; font-weight: 600; margin-right: 0.5rem;';
                    generateBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        this.generateLLMMessage();
                    });
                    headerActions.insertBefore(generateBtn, headerActions.firstChild);
                }
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
            
            // Use the compile-header-prompt endpoint which uses LLM to generate the prompt
            let url = `/header/api/posts/${this.postId}/compile-header-prompt?illustration_method=${encodeURIComponent(this.illustrationMethod)}`;
            if (year) url += `&year=${year}`;
            if (week) url += `&week=${week}`;
            
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    theme_name: document.getElementById('theme-name-display')?.textContent,
                    expanded_idea: document.getElementById('expanded-idea-display')?.textContent,
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
        const generateBtn = document.getElementById('generate-images-btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.generateImages());
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
            
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    image_prompt: promptTextarea.value.trim(),
                    model_name: model,
                    parameters: {
                        size: landscapeSize,
                        portrait_size: portraitSize,
                        quality: quality
                    },
                    use_renderer: false
                })
            });
            
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
                    const landscapePath = data.raw_path || data.optimized_path;
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
                        portraitPath = data.raw_path?.replace('/header/raw/header.png', '/header/portrait/raw/header_portrait.png') ||
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
        const optimizeBtn = document.getElementById('optimize-image-btn');
        if (optimizeBtn) {
            optimizeBtn.addEventListener('click', () => this.optimizeImages());
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
                        portraitPath = data.optimized_path.replace('/header/optimized/header.jpg', '/header/portrait/optimized/header_portrait.jpg')
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
    if (window.postId && window.currentSubstage === 'header-image') {
        window.headerImageSimplified = new HeaderImageSimplified(window.postId);
    }
});

