/**
 * Profile Header Image - JavaScript for profile post header image generation
 * Handles product-specific header image workflow
 */

// Global accordion toggle function for profile header panels
function toggleAccordion(contentId, iconId) {
    const content = document.getElementById(contentId);
    const icon = document.getElementById(iconId);
    if (content && icon) {
        const isCurrentlyOpen = !content.classList.contains('collapsed');
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
        console.log(`[Profile Header Image] Accordion ${contentId} toggled to ${isCurrentlyOpen ? 'closed' : 'open'}`);
    } else {
        console.error(`[Profile Header Image] Accordion elements not found: contentId=${contentId}, iconId=${iconId}`);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('[Profile Header Image] Initializing...');
    
    // Load product information
    loadProductInfo();
    
    // Load product images
    loadProductImages();
    
    // Initialize prompt generation
    initPromptGeneration();
    
    // Load existing images if they were already generated
    loadExistingImages();
    
    // Check if prompt already exists and enable button if so
    // Wait a bit for DOM to be fully ready
    setTimeout(() => {
        checkExistingPrompt();
    }, 1000);
    
    console.log('[Profile Header Image] Initialized');
});

/**
 * Load existing images if they were already generated
 */
async function loadExistingImages() {
    try {
        console.log('[Profile Header Image] Checking for existing images...');
        
        // Check if raw landscape image exists
        const landscapePath = `/static/content/posts/${window.postId}/header/landscape/raw/header.png`;
        const landscapeImg = document.getElementById('raw-landscape-image');
        const landscapePlaceholder = document.getElementById('raw-landscape-placeholder');
        
        if (landscapeImg) {
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
                        console.log('[Profile Header Image] Landscape image found and displayed');
                    }
                }
            } catch (err) {
                // Silently fail - no image exists yet
            }
        }
        
        // Check if raw portrait image exists
        const portraitPath = `/static/content/posts/${window.postId}/header/portrait/raw/header_portrait.png`;
        const portraitImg = document.getElementById('raw-portrait-image');
        const portraitPlaceholder = document.getElementById('raw-portrait-placeholder');
        
        if (portraitImg) {
            try {
                const imgResponse = await fetch(portraitPath, { method: 'HEAD' });
                if (imgResponse.ok) {
                    portraitImg.src = portraitPath;
                    portraitImg.style.display = 'block';
                    if (portraitPlaceholder) {
                        portraitPlaceholder.style.display = 'none';
                    }
                    console.log('[Profile Header Image] Portrait image found and displayed');
                }
            } catch (err) {
                // Silently fail - no image exists yet
            }
        }
        
        // Check if optimized images exist
        const optimizedLandscapePath = `/static/content/posts/${window.postId}/header/optimized/header.jpg`;
        const optimizedPortraitPath = `/static/content/posts/${window.postId}/header/portrait/optimized/header_portrait.jpg`;
        
        const optimizedLandscapeImg = document.getElementById('optimized-landscape-image');
        const optimizedPortraitImg = document.getElementById('optimized-portrait-image');
        const optimizedLandscapePlaceholder = document.getElementById('optimized-landscape-placeholder');
        const optimizedPortraitPlaceholder = document.getElementById('optimized-portrait-placeholder');
        
        if (optimizedLandscapeImg) {
            try {
                const imgResponse = await fetch(optimizedLandscapePath, { method: 'HEAD' });
                if (imgResponse.ok) {
                    optimizedLandscapeImg.src = optimizedLandscapePath;
                    optimizedLandscapeImg.style.display = 'block';
                    if (optimizedLandscapePlaceholder) {
                        optimizedLandscapePlaceholder.style.display = 'none';
                    }
                    // Show optimized images panel
                    const optimizedPanel = document.getElementById('optimized-images-panel');
                    if (optimizedPanel) {
                        optimizedPanel.style.display = 'block';
                        console.log('[Profile Header Image] Optimized landscape image found and displayed');
                    }
                }
            } catch (err) {
                // Silently fail
            }
        }
        
        if (optimizedPortraitImg) {
            try {
                const imgResponse = await fetch(optimizedPortraitPath, { method: 'HEAD' });
                if (imgResponse.ok) {
                    optimizedPortraitImg.src = optimizedPortraitPath;
                    optimizedPortraitImg.style.display = 'block';
                    if (optimizedPortraitPlaceholder) {
                        optimizedPortraitPlaceholder.style.display = 'none';
                    }
                    console.log('[Profile Header Image] Optimized portrait image found and displayed');
                }
            } catch (err) {
                // Silently fail
            }
        }
    } catch (error) {
        console.log('[Profile Header Image] Error loading existing images:', error);
    }
}

/**
 * Check if a prompt already exists and enable the button if so
 */
async function checkExistingPrompt() {
    try {
        // First check the textarea
        const promptText = document.getElementById('generated-prompt-text');
        if (promptText && promptText.value.trim()) {
            console.log('[Profile Header Image] Existing prompt found in textarea, enabling button');
            const generateBtn = document.getElementById('generate-images-btn');
            if (generateBtn) {
                generateBtn.disabled = false;
            }
            return;
        }
        
        // If not in textarea, check database
        console.log('[Profile Header Image] Checking database for existing prompt...');
        try {
            const response = await fetch(`/header/api/posts/${window.postId}/get-header-image`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.image_prompt) {
                    console.log('[Profile Header Image] Existing prompt found in database, populating and enabling button');
                    // Populate the textarea
                    if (promptText) {
                        promptText.value = data.image_prompt;
                        const display = document.getElementById('generated-prompt-display');
                        if (display) {
                            display.style.display = 'block';
                        }
                    }
                    // Enable button
                    const generateBtn = document.getElementById('generate-images-btn');
                    if (generateBtn) {
                        generateBtn.disabled = false;
                        generateBtn.style.opacity = '1';
                        generateBtn.style.cursor = 'pointer';
                        generateBtn.title = '';
                        console.log('[Profile Header Image] Button enabled');
                    }
                } else {
                    console.log('[Profile Header Image] No existing prompt in database');
                }
            } else if (response.status === 404) {
                // 404 is expected when no header image exists yet - not an error
                console.log('[Profile Header Image] No header image found yet (404 is normal)');
            } else {
                console.warn('[Profile Header Image] Unexpected response status:', response.status);
            }
        } catch (error) {
            // Silently handle network errors - not critical
            console.log('[Profile Header Image] Could not check for existing prompt:', error.message);
        }
    } catch (error) {
        console.log('[Profile Header Image] Error checking existing prompt:', error);
    }
}

/**
 * Load product information for the profile post
 */
async function loadProductInfo() {
    try {
        const response = await fetch(`/planning/api/posts/${window.postId}`);
        const data = await response.json();
        
        if (data.success && data.post && data.post.profile_product_id) {
            const productId = data.post.profile_product_id;
            
            // Fetch product data using the products API endpoint
            const productResponse = await fetch(`/products/api/${productId}/full`);
            const productData = await productResponse.json();
            
            if (productData.success && productData.product_data) {
                const product = productData.product_data;
                
                // Display product information
                const nameDisplay = document.getElementById('product-name-display');
                const typeDisplay = document.getElementById('product-type-display');
                const descDisplay = document.getElementById('product-description-display');
                
                if (nameDisplay) {
                    nameDisplay.textContent = product.name || 'Unknown';
                }
                
                if (typeDisplay) {
                    // Try to get product type from additional_data or category
                    const productType = product.additional_data?.product_type || 
                                       (product.category_ids && product.category_ids[0]) || 
                                       'Product';
                    typeDisplay.textContent = productType;
                }
                
                if (descDisplay) {
                    const description = product.short_description || 
                                      product.description || 
                                      'No description available';
                    // Strip HTML tags for display
                    const textDesc = description.replace(/<[^>]*>/g, '').substring(0, 300);
                    descDisplay.textContent = textDesc + (description.length > 300 ? '...' : '');
                }
            } else {
                console.error('Failed to load product data');
                showError('product-info-display', 'Failed to load product information');
            }
        } else {
            console.error('No product linked to this profile post');
            showError('product-info-display', 'No product linked to this profile post');
        }
    } catch (error) {
        console.error('Error loading product info:', error);
        showError('product-info-display', 'Error loading product information');
    }
}

/**
 * Load product images for reference
 */
async function loadProductImages() {
    try {
        const response = await fetch(`/planning/api/posts/${window.postId}`);
        const data = await response.json();
        
        if (data.success && data.post && data.post.profile_product_id) {
            const productId = data.post.profile_product_id;
            
            // Get product data to get SKU
            const productResponse = await fetch(`/products/api/${productId}/full`);
            const productData = await productResponse.json();
            
            if (productData.success && productData.product_data) {
                const product = productData.product_data;
                const sku = product.sku;
                
                if (sku) {
                    // Fetch all images using SKU
                    const imagesResponse = await fetch(`/api/clan/products/${sku}/full?all_images=true`);
                    const imagesData = await imagesResponse.json();
                    
                    if (imagesData.success && imagesData.product) {
                        const allImages = imagesData.product.all_images || [];
                        
                        // If no images array, use main image_url
                        if (allImages.length === 0 && product.image_url) {
                            allImages.push({
                                url: product.image_url,
                                alt: 'Main product image'
                            });
                        }
                        
                        displayProductImages(allImages);
                    } else {
                        // Fallback to main image
                        if (product.image_url) {
                            displayProductImages([{
                                url: product.image_url,
                                alt: 'Main product image'
                            }]);
                        }
                    }
                } else {
                    // No SKU, use main image if available
                    if (product.image_url) {
                        displayProductImages([{
                            url: product.image_url,
                            alt: 'Main product image'
                        }]);
                    } else {
                        const display = document.getElementById('product-images-display');
                        if (display) {
                            display.innerHTML = '<p style="color: #94a3b8;">No product images available</p>';
                        }
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error loading product images:', error);
        const display = document.getElementById('product-images-display');
        if (display) {
            display.innerHTML = '<p style="color: #dc2626;">Error loading product images</p>';
        }
    }
}

/**
 * Display product images in the reference panel
 */
function displayProductImages(images) {
    const display = document.getElementById('product-images-display');
    if (!display) return;
    
    if (images.length === 0) {
        display.innerHTML = '<p style="color: #94a3b8;">No product images available</p>';
        return;
    }
    
    display.innerHTML = '';
    images.forEach((img, index) => {
        const item = document.createElement('div');
        item.className = 'product-image-item';
        item.innerHTML = `
            <img src="${img.url}" alt="${img.alt || `Image ${index + 1}`}" />
            <p class="image-alt">${img.alt || `Image ${index + 1}`}</p>
        `;
        display.appendChild(item);
    });
}

/**
 * Initialize prompt generation functionality
 */
function initPromptGeneration() {
    const generateBtn = document.getElementById('generate-profile-header-prompt-btn');
    const copyBtn = document.getElementById('copy-prompt-btn');
    
    if (generateBtn) {
        generateBtn.addEventListener('click', async function() {
            await generateHeaderPrompt();
        });
    }
    
    if (copyBtn) {
        copyBtn.addEventListener('click', function() {
            const promptText = document.getElementById('generated-prompt-text');
            if (promptText) {
                promptText.select();
                document.execCommand('copy');
                copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                setTimeout(() => {
                    copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
                }, 2000);
            }
        });
    }
}

/**
 * Generate header image prompt for profile post
 */
async function generateHeaderPrompt() {
    const btn = document.getElementById('generate-profile-header-prompt-btn');
    const display = document.getElementById('generated-prompt-display');
    const promptText = document.getElementById('generated-prompt-text');
    
    if (!btn || !display || !promptText) return;
    
    // Disable button and show loading
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    
    try {
        // Fetch product and post data
        const postResponse = await fetch(`/planning/api/posts/${window.postId}`);
        const postData = await postResponse.json();
        
        if (!postData.success || !postData.post || !postData.post.profile_product_id) {
            throw new Error('No product linked to this profile post');
        }
        
        const productId = postData.post.profile_product_id;
        
        // Get product data to get SKU
        const productResponse = await fetch(`/products/api/${productId}/full`);
        const productResult = await productResponse.json();
        
        if (!productResult.success || !productResult.product_data) {
            throw new Error('Failed to load product data');
        }
        
        const product = productResult.product_data;
        const sku = product.sku;
        
        if (!sku) {
            throw new Error('Product SKU not found');
        }
        
        // Fetch product with all images using SKU
        const imagesResponse = await fetch(`/api/clan/products/${sku}/full?all_images=true`);
        const imagesData = await imagesResponse.json();
        
        if (!imagesData.success || !imagesData.product) {
            throw new Error('Failed to load product images');
        }
        
        const productWithImages = imagesData.product;
        
        // Get post title and summary from title-summary API
        let title = postData.post.title || product.name;
        let summary = '';
        
        try {
            const titleSummaryResponse = await fetch(`/header/api/posts/${window.postId}/get-title-summary`);
            if (titleSummaryResponse.ok) {
                const titleSummaryData = await titleSummaryResponse.json();
                if (titleSummaryData.title) {
                    title = titleSummaryData.title;
                }
                if (titleSummaryData.summary) {
                    summary = titleSummaryData.summary;
                }
                console.log('[Profile Header Image] Fetched title and summary from title-summary API');
            }
        } catch (error) {
            console.warn('[Profile Header Image] Could not fetch title/summary from API, using defaults:', error);
        }
        
        // Get main product image URL
        const productImageUrl = product.image_url || productWithImages.image_url || null;
        
        // Generate prompt via API
        const response = await fetch(`/header/api/posts/${window.postId}/generate-profile-header-prompt`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                product_name: product.name,
                product_description: product.short_description || product.description || '',
                product_type: product.additional_data?.product_type || '',
                post_title: title,
                post_summary: summary
            })
        });
        
        const result = await response.json();
        
        if (result.success && result.prompt) {
            promptText.value = result.prompt;
            display.style.display = 'block';
            
            // Store product image URL for use in image generation
            // Use the URL from API response if available, otherwise use the one we fetched
            const referenceImageUrl = result.reference_image_url || productImageUrl;
            if (referenceImageUrl) {
                promptText.dataset.referenceImageUrl = referenceImageUrl;
                window.profileReferenceImageUrl = referenceImageUrl;
            }
            
            // Enable image generation button (update its state)
            const generateBtn = document.getElementById('generate-images-btn');
            if (generateBtn) {
                generateBtn.disabled = false;
                generateBtn.style.opacity = '1';
                generateBtn.style.cursor = 'pointer';
                generateBtn.title = '';
                console.log('[Profile Header Image] Image generation button enabled');
            } else {
                console.error('[Profile Header Image] generate-images-btn not found when trying to enable');
            }
            
            // Auto-expand the panel
            const content = document.getElementById('profile-header-prompt-content');
            const icon = document.getElementById('profile-header-prompt-icon');
            if (content && icon) {
                content.classList.remove('collapsed');
                icon.classList.add('open');
            }
        } else {
            throw new Error(result.error || 'Failed to generate prompt');
        }
    } catch (error) {
        console.error('Error generating header prompt:', error);
        alert('Error generating header image prompt: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-magic"></i> Generate Header Image Prompt';
    }
}

/**
 * Show error message in a display element
 */
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<p style="color: #dc2626;">${message}</p>`;
    }
}

/**
 * Setup image generation button for profile posts
 */
function setupProfileImageGeneration() {
    const generateBtn = document.getElementById('generate-images-btn');
    if (generateBtn) {
        // Remove any existing listeners by cloning
        const newBtn = generateBtn.cloneNode(true);
        generateBtn.parentNode.replaceChild(newBtn, generateBtn);
        
        // Attach click listener to new button
        // We'll check for prompt inside the handler instead of disabling the button
        // This way users get feedback when clicking
        newBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            e.stopPropagation(); // Prevent accordion toggle
            console.log('[Profile Header Image] Generate button clicked');
            
            // Check if prompt exists
            const promptText = document.getElementById('generated-prompt-text') || 
                              document.getElementById('generated-prompt-textarea');
            if (!promptText || !promptText.value.trim()) {
                console.log('[Profile Header Image] No prompt found, opening prompt panel');
                // Auto-open the prompt generation panel
                const promptContent = document.getElementById('profile-header-prompt-content');
                const promptIcon = document.getElementById('profile-header-prompt-icon');
                if (promptContent && promptIcon) {
                    promptContent.classList.remove('collapsed');
                    promptIcon.classList.add('open');
                    // Scroll to the panel
                    promptContent.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
                alert('Please generate a header image prompt first by clicking "Generate Header Image Prompt" in the panel above.');
                return;
            }
            
            await generateProfileHeaderImage();
        });
        
        // Update button style based on whether prompt exists
        function updateButtonState() {
            const promptText = document.getElementById('generated-prompt-text') || 
                              document.getElementById('generated-prompt-textarea');
            const hasPrompt = promptText && promptText.value.trim();
            
            if (hasPrompt) {
                newBtn.disabled = false;
                newBtn.style.opacity = '1';
                newBtn.style.cursor = 'pointer';
                newBtn.title = '';
            } else {
                newBtn.disabled = false; // Don't disable, but style it differently
                newBtn.style.opacity = '0.6';
                newBtn.style.cursor = 'not-allowed';
                newBtn.title = 'Please generate a header image prompt first';
            }
        }
        
        // Check button state initially and set up observer
        updateButtonState();
        
        // Watch for changes to the prompt textarea
        const promptText = document.getElementById('generated-prompt-text');
        if (promptText) {
            promptText.addEventListener('input', updateButtonState);
            // Also check periodically in case prompt is set programmatically
            setInterval(updateButtonState, 1000);
        }
        
        console.log('[Profile Header Image] Image generation button listener attached, disabled:', newBtn.disabled);
    } else {
        console.error('[Profile Header Image] generate-images-btn not found!');
    }
}

/**
 * Generate header images for profile post with product image reference
 */
async function generateProfileHeaderImage() {
    console.log('[Profile Header Image] generateProfileHeaderImage called');
    const btn = document.getElementById('generate-images-btn');
    if (!btn) {
        console.error('[Profile Header Image] Generate button not found!');
        alert('Generate button not found. Please refresh the page.');
        return;
    }
    
    if (btn.disabled) {
        console.log('[Profile Header Image] Button is disabled');
        alert('Please generate a header image prompt first.');
        return;
    }
    
    // Get the generated prompt - check both possible IDs
    const promptTextarea = document.getElementById('generated-prompt-text') || 
                          document.getElementById('generated-prompt-textarea');
    if (!promptTextarea || !promptTextarea.value.trim()) {
        console.error('[Profile Header Image] No prompt found');
        alert('Please generate a header image prompt first.');
        return;
    }
    
    const imagePrompt = promptTextarea.value.trim();
    console.log('[Profile Header Image] Using prompt:', imagePrompt.substring(0, 100) + '...');
    
    // Get reference image URL from the prompt textarea data attribute or global variable
    const referenceImageUrl = promptTextarea.dataset.referenceImageUrl || 
                             window.profileReferenceImageUrl || 
                             null;
    
    // Get image generation settings
    const modelName = document.getElementById('image-model-select')?.value || 'gpt-image-1';
    const landscapeSize = document.getElementById('landscape-size')?.value || '1536x1024';
    const portraitSize = document.getElementById('portrait-size')?.value || '1024x1536';
    const quality = document.getElementById('image-quality')?.value || 'high';
    
    // Disable button and show loading
    btn.disabled = true;
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    
    try {
        console.log('[Profile Header Image] Sending request to generate images');
        const response = await fetch(`/header/api/posts/${window.postId}/generate-header-image`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image_prompt: imagePrompt,
                model_name: modelName,
                parameters: {
                    size: landscapeSize,
                    portrait_size: portraitSize,
                    quality: quality
                },
                reference_image_url: referenceImageUrl  // Pass product image URL
            })
        });
        
        const result = await response.json();
        console.log('[Profile Header Image] Response received:', result);
        
        if (result.success) {
            console.log('[Profile Header Image] Images generated successfully');
            console.log('[Profile Header Image] Landscape raw:', result.landscape_raw);
            console.log('[Profile Header Image] Portrait raw:', result.portrait_raw);
            
            // Display the generated images instead of reloading
            displayGeneratedImages(result);
        } else {
            console.error('[Profile Header Image] Generation failed:', result.error);
            throw new Error(result.error || 'Failed to generate images');
        }
    } catch (error) {
        console.error('[Profile Header Image] Error generating header images:', error);
        alert('Error generating header images: ' + error.message);
        btn.disabled = false;
        btn.innerHTML = originalHTML;
    }
}

/**
 * Display generated images in the UI
 */
function displayGeneratedImages(result) {
    console.log('[Profile Header Image] Displaying generated images:', result);
    
    // Show raw images panel
    const rawImagesPanel = document.getElementById('raw-images-panel');
    if (rawImagesPanel) {
        rawImagesPanel.style.display = 'block';
        console.log('[Profile Header Image] Raw images panel shown');
    } else {
        console.error('[Profile Header Image] Raw images panel not found!');
    }
    
    // Display landscape image
    const landscapeImg = document.getElementById('raw-landscape-image');
    const landscapePlaceholder = document.getElementById('raw-landscape-placeholder');
    if (landscapeImg && result.landscape_raw) {
        landscapeImg.src = result.landscape_raw;
        landscapeImg.style.display = 'block';
        if (landscapePlaceholder) {
            landscapePlaceholder.style.display = 'none';
        }
    }
    
    // Display portrait image
    const portraitImg = document.getElementById('raw-portrait-image');
    const portraitPlaceholder = document.getElementById('raw-portrait-placeholder');
    if (portraitImg && result.portrait_raw) {
        portraitImg.src = result.portrait_raw;
        portraitImg.style.display = 'block';
        if (portraitPlaceholder) {
            portraitPlaceholder.style.display = 'none';
        }
    }
    
    // Show optimized images panel if available
    if (result.landscape_optimized || result.portrait_optimized) {
        const optimizedPanel = document.getElementById('optimized-images-panel');
        if (optimizedPanel) {
            optimizedPanel.style.display = 'block';
            // Expand it
            const optContent = optimizedPanel.querySelector('.panel-content');
            const optIcon = optimizedPanel.querySelector('.panel-header i.fa-chevron-down');
            if (optContent) optContent.classList.remove('collapsed');
            if (optIcon) optIcon.classList.add('open');
        }
        
        // Display optimized landscape
        const optimizedLandscapeImg = document.getElementById('optimized-landscape-image');
        const optimizedLandscapePlaceholder = document.getElementById('optimized-landscape-placeholder');
        if (optimizedLandscapeImg && result.landscape_optimized) {
            optimizedLandscapeImg.src = result.landscape_optimized;
            optimizedLandscapeImg.style.display = 'block';
            if (optimizedLandscapePlaceholder) {
                optimizedLandscapePlaceholder.style.display = 'none';
            }
        }
        
        // Display optimized portrait
        const optimizedPortraitImg = document.getElementById('optimized-portrait-image');
        const optimizedPortraitPlaceholder = document.getElementById('optimized-portrait-placeholder');
        if (optimizedPortraitImg && result.portrait_optimized) {
            optimizedPortraitImg.src = result.portrait_optimized;
            optimizedPortraitImg.style.display = 'block';
            if (optimizedPortraitPlaceholder) {
                optimizedPortraitPlaceholder.style.display = 'none';
            }
        }
    }
    
    // Scroll to the images
    if (rawImagesPanel) {
        rawImagesPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

// Initialize image generation when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Profile Header Image] DOMContentLoaded - setting up image generation');
    // Wait a bit for all panels to be rendered
    setTimeout(() => {
        setupProfileImageGeneration();
    }, 500);
});

