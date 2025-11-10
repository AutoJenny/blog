/**
 * Content Generator Modal Core
 * Main modal class for generating blog posts from products/categories
 */

class ContentGeneratorModal {
    constructor() {
        this.currentSourceType = 'product'; // 'product' or 'category'
        this.selectedProductId = null;
        this.selectedCategoryId = null;
        this.currentWeek = null;
        this.currentYear = null;
        this.generatedContent = null;
        this.suggestionsPanelOpen = false;
        
        this.init();
    }

    init() {
        // Close button
        const closeBtn = document.getElementById('content-generator-modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }

        // Cancel button
        const cancelBtn = document.getElementById('content-generator-modal-cancel');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.close());
        }

        // Generate button
        const generateBtn = document.getElementById('content-generator-modal-generate');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.generate());
        }

        // Save button
        const saveBtn = document.getElementById('content-generator-modal-save');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.save());
        }

        // Preview button
        const previewBtn = document.getElementById('content-generator-modal-preview');
        if (previewBtn) {
            previewBtn.addEventListener('click', () => this.preview());
        }

        // Type selector radio buttons
        const typeRadios = document.querySelectorAll('input[name="content-generator-type"]');
        typeRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.switchType(e.target.value);
            });
        });

        // Product search - attach event listener
        const productSearch = document.getElementById('content-generator-product-search');
        if (productSearch) {
            let searchTimeout;
            productSearch.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                const query = e.target.value.trim();
                if (query.length >= 2) {
                    searchTimeout = setTimeout(() => {
                        this.searchProducts(query);
                    }, 300);
                } else {
                    // Clear results if query is too short
                    const resultsDiv = document.getElementById('content-generator-product-search-results');
                    if (resultsDiv) resultsDiv.innerHTML = '';
                }
            });
            
            // Also add a keypress handler for Enter key
            productSearch.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    clearTimeout(searchTimeout);
                    const query = e.target.value.trim();
                    if (query.length >= 2) {
                        this.searchProducts(query);
                    }
                }
            });
        }

        // Category select
        const categorySelect = document.getElementById('content-generator-category-select');
        if (categorySelect) {
            categorySelect.addEventListener('change', (e) => {
                this.selectCategory(e.target.value);
            });
            this.loadCategories();
        }

        // Remove buttons
        const removeProduct = document.getElementById('content-generator-remove-product');
        if (removeProduct) {
            removeProduct.addEventListener('click', () => {
                this.clearProduct();
            });
        }

        const removeCategory = document.getElementById('content-generator-remove-category');
        if (removeCategory) {
            removeCategory.addEventListener('click', () => {
                this.clearCategory();
            });
        }

        // Suggestions toggle
        const toggleSuggestions = document.getElementById('content-generator-toggle-suggestions');
        if (toggleSuggestions) {
            toggleSuggestions.addEventListener('click', () => {
                this.toggleSuggestionsPanel();
            });
        }

        // Get suggestions button
        const getSuggestionsBtn = document.getElementById('content-generator-get-suggestions');
        if (getSuggestionsBtn) {
            getSuggestionsBtn.addEventListener('click', () => {
                this.getSuggestions();
            });
        }

        // Generation type change
        const generationTypeSelect = document.getElementById('content-generator-generation-type');
        if (generationTypeSelect) {
            generationTypeSelect.addEventListener('change', () => {
                this.updateGenerationTypeOptions();
            });
        }

        // Close on backdrop click
        const modalEl = document.getElementById('content-generator-modal');
        if (modalEl) {
            modalEl.addEventListener('click', (e) => {
                if (e.target === modalEl) {
                    this.close();
                }
            });
        }
    }

    switchType(type) {
        this.currentSourceType = type;
        
        // Show/hide appropriate selection groups
        const productGroup = document.getElementById('product-selection-group');
        const categoryGroup = document.getElementById('category-selection-group');
        const featureOption = document.getElementById('content-generator-type-feature');
        
        if (type === 'product') {
            if (productGroup) productGroup.style.display = 'block';
            if (categoryGroup) categoryGroup.style.display = 'none';
            if (featureOption) featureOption.style.display = 'none';
            this.clearCategory();
        } else {
            if (productGroup) productGroup.style.display = 'none';
            if (categoryGroup) categoryGroup.style.display = 'block';
            if (featureOption) featureOption.style.display = 'block';
            this.clearProduct();
        }
        
        this.updateGenerationTypeOptions();
    }

    updateGenerationTypeOptions() {
        const generationType = document.getElementById('content-generator-generation-type');
        if (!generationType) return;
        
        // Hide/show options based on source type
        const comparisonOption = generationType.querySelector('option[value="comparison"]');
        if (comparisonOption) {
            comparisonOption.style.display = this.currentSourceType === 'product' ? 'block' : 'none';
        }
    }

    async searchProducts(query) {
        if (!query || query.length < 2) {
            const resultsDiv = document.getElementById('content-generator-product-search-results');
            if (resultsDiv) resultsDiv.innerHTML = '';
            return;
        }

        const resultsDiv = document.getElementById('content-generator-product-search-results');
        if (!resultsDiv) {
            console.warn('Search results div not found');
            return;
        }
        
        // Show loading state
        resultsDiv.innerHTML = '<div class="search-result-empty">Searching...</div>';

        try {
            const response = await fetch(`/api/clan/products?q=${encodeURIComponent(query)}&limit=10`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Response is not JSON');
            }
            
            const data = await response.json();
            
            // Handle different response formats - /api/clan/products returns array directly
            const products = Array.isArray(data) ? data : (data.products || []);
            
            if (products && products.length > 0) {
                resultsDiv.innerHTML = products.map(product => `
                    <div class="search-result-item" data-product-id="${product.id}">
                        <div class="search-result-info">
                            <strong>${this.escapeHtml(product.name || 'Unnamed Product')}</strong>
                            ${product.supplier_name ? `<br><small>${this.escapeHtml(product.supplier_name)}</small>` : ''}
                            ${product.sku ? `<br><small>SKU: ${this.escapeHtml(product.sku)}</small>` : ''}
                        </div>
                    </div>
                `).join('');
                
                // Add click handlers
                resultsDiv.querySelectorAll('.search-result-item').forEach(item => {
                    item.style.cursor = 'pointer';
                    item.addEventListener('click', () => {
                        const productId = parseInt(item.dataset.productId);
                        const product = products.find(p => p.id === productId);
                        if (product) {
                            this.selectProduct(productId, product);
                        } else {
                            this.showError('Product not found in results');
                        }
                    });
                });
            } else {
                resultsDiv.innerHTML = '<div class="search-result-empty">No products found</div>';
            }
        } catch (error) {
            console.error('Error searching products:', error);
            resultsDiv.innerHTML = `<div class="search-result-empty" style="color: #ef4444;">Error: ${this.escapeHtml(error.message)}</div>`;
            this.showError('Failed to search products: ' + error.message);
        }
    }

    async selectProduct(productId, productData = null) {
        this.selectedProductId = productId;
        
        // If productData provided from search, use it directly
        if (productData) {
            // Product data is already available from search results
        } else {
            // Try to fetch from search results cache or re-search
            // For now, we'll use the product data that should have been passed
            console.warn('Product data not provided, using ID only');
            productData = { id: productId };
        }
        
        // Update UI
        const selectedDiv = document.getElementById('content-generator-selected-product');
        const searchInput = document.getElementById('content-generator-product-search');
        const resultsDiv = document.getElementById('content-generator-product-search-results');
        
        if (selectedDiv) {
            document.getElementById('content-generator-product-name').textContent = productData.name || 'Unnamed Product';
            document.getElementById('content-generator-product-producer').textContent = productData.supplier_name || '';
            document.getElementById('content-generator-product-price').textContent = productData.price ? `£${productData.price}` : '';
            
            const img = document.getElementById('content-generator-product-image');
            if (img && productData.image_url) {
                img.src = productData.image_url;
                img.style.display = 'block';
            } else if (img) {
                img.style.display = 'none';
            }
            
            selectedDiv.style.display = 'block';
        }
        
        if (searchInput) searchInput.value = productData.name || '';
        if (resultsDiv) resultsDiv.innerHTML = '';
    }

    clearProduct() {
        this.selectedProductId = null;
        const selectedDiv = document.getElementById('content-generator-selected-product');
        const searchInput = document.getElementById('content-generator-product-search');
        const resultsDiv = document.getElementById('content-generator-product-search-results');
        
        if (selectedDiv) selectedDiv.style.display = 'none';
        if (searchInput) searchInput.value = '';
        if (resultsDiv) resultsDiv.innerHTML = '';
    }

    async loadCategories() {
        try {
            // Use the same endpoint as profile modal
            const response = await fetch('/launchpad/api/syndication/categories');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            
            const select = document.getElementById('content-generator-category-select');
            if (!select) return;
            
            select.innerHTML = '<option value="">-- Select Category --</option>';
            
            // Handle different response formats
            const categories = data.categories || (data.success && data.categories ? data.categories : []) || (Array.isArray(data) ? data : []);
            
            if (categories && categories.length > 0) {
                // Build category tree if parent_id exists
                const buildOptions = (cats, parentId = null, level = 0) => {
                    const filtered = cats.filter(cat => (cat.parent_id || null) === parentId);
                    filtered.forEach(cat => {
                        const indent = '  '.repeat(level);
                        const option = document.createElement('option');
                        option.value = cat.id;
                        option.textContent = `${indent}${cat.name || 'Unnamed Category'}`;
                        select.appendChild(option);
                        
                        // Recursively add children
                        buildOptions(cats, cat.id, level + 1);
                    });
                };
                
                buildOptions(categories);
            }
        } catch (error) {
            console.error('Error loading categories:', error);
            this.showError('Failed to load categories');
        }
    }

    selectCategory(categoryId) {
        this.selectedCategoryId = categoryId ? parseInt(categoryId) : null;
        
        if (!this.selectedCategoryId) {
            this.clearCategory();
            return;
        }
        
        // Update UI
        const select = document.getElementById('content-generator-category-select');
        const selectedDiv = document.getElementById('content-generator-selected-category');
        
        if (select && selectedDiv) {
            const selectedOption = select.options[select.selectedIndex];
            document.getElementById('content-generator-category-name').textContent = selectedOption.textContent;
            document.getElementById('content-generator-category-path').textContent = `Category ID: ${categoryId}`;
            selectedDiv.style.display = 'block';
        }
    }

    clearCategory() {
        this.selectedCategoryId = null;
        const selectedDiv = document.getElementById('content-generator-selected-category');
        const select = document.getElementById('content-generator-category-select');
        
        if (selectedDiv) selectedDiv.style.display = 'none';
        if (select) select.value = '';
    }

    toggleSuggestionsPanel() {
        this.suggestionsPanelOpen = !this.suggestionsPanelOpen;
        const panel = document.getElementById('content-generator-suggestions-panel');
        const toggle = document.getElementById('content-generator-toggle-suggestions');
        
        if (panel) {
            panel.style.display = this.suggestionsPanelOpen ? 'block' : 'none';
        }
        
        if (toggle) {
            const icon = toggle.querySelector('i');
            if (icon) {
                icon.className = this.suggestionsPanelOpen ? 'fas fa-chevron-up' : 'fas fa-chevron-down';
            }
        }
    }

    async getSuggestions() {
        const queryInput = document.getElementById('content-generator-suggestions-query');
        const query = queryInput ? queryInput.value.trim() : '';
        const resultsDiv = document.getElementById('content-generator-suggestions-results');
        
        if (!resultsDiv) return;
        
        resultsDiv.innerHTML = '<div class="loading">Loading suggestions...</div>';
        
        try {
            const response = await fetch('/api/content/suggest-ideas', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query || 'interesting Scottish products',
                    limit: 10
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.suggestions && data.suggestions.length > 0) {
                resultsDiv.innerHTML = data.suggestions.map(suggestion => `
                    <div class="suggestion-item" data-type="${suggestion.type}" data-id="${suggestion.id}">
                        <div class="suggestion-info">
                            <strong>${this.escapeHtml(suggestion.name)}</strong>
                            <small>${this.escapeHtml(suggestion.reason || '')}</small>
                            <span class="suggestion-score">Score: ${(suggestion.score || 0).toFixed(2)}</span>
                        </div>
                    </div>
                `).join('');
                
                // Add click handlers
                resultsDiv.querySelectorAll('.suggestion-item').forEach(item => {
                    item.addEventListener('click', () => {
                        const type = item.dataset.type;
                        const id = parseInt(item.dataset.id);
                        
                        if (type === 'product') {
                            this.switchType('product');
                            this.selectProduct(id);
                        } else if (type === 'category') {
                            this.switchType('category');
                            this.selectCategory(id);
                        }
                    });
                });
            } else {
                resultsDiv.innerHTML = '<div class="suggestion-empty">No suggestions found</div>';
            }
        } catch (error) {
            console.error('Error getting suggestions:', error);
            resultsDiv.innerHTML = '<div class="suggestion-error">Failed to load suggestions</div>';
        }
    }

    async generate() {
        // Validate selection
        if (this.currentSourceType === 'product' && !this.selectedProductId) {
            this.showError('Please select a product');
            return;
        }
        
        if (this.currentSourceType === 'category' && !this.selectedCategoryId) {
            this.showError('Please select a category');
            return;
        }
        
        // Get generation options
        const generationType = document.getElementById('content-generator-generation-type')?.value || 'deep_dive';
        const tone = document.getElementById('content-generator-tone')?.value || 'warm';
        const length = document.getElementById('content-generator-length')?.value || 'medium';
        
        // Show loading
        this.setLoading(true, 'Generating content...');
        this.hideError();
        
        try {
            const response = await fetch('/api/content/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_type: this.currentSourceType,
                    source_id: this.currentSourceType === 'product' ? this.selectedProductId : this.selectedCategoryId,
                    generation_type: generationType,
                    tone: tone,
                    length: length
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.generatedContent = data;
                this.showPreview(data);
            } else {
                this.showError(data.error || 'Generation failed');
            }
        } catch (error) {
            console.error('Error generating content:', error);
            this.showError('Failed to generate content: ' + error.message);
        } finally {
            this.setLoading(false);
        }
    }

    async preview() {
        // Similar to generate but uses preview endpoint
        if (this.currentSourceType === 'product' && !this.selectedProductId) {
            this.showError('Please select a product');
            return;
        }
        
        if (this.currentSourceType === 'category' && !this.selectedCategoryId) {
            this.showError('Please select a category');
            return;
        }
        
        const generationType = document.getElementById('content-generator-generation-type')?.value || 'deep_dive';
        
        this.setLoading(true, 'Generating preview...');
        this.hideError();
        
        try {
            const response = await fetch('/api/content/preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_type: this.currentSourceType,
                    source_id: this.currentSourceType === 'product' ? this.selectedProductId : this.selectedCategoryId,
                    generation_type: generationType
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.preview) {
                this.showPreview(data.preview, false);
            } else {
                this.showError(data.error || 'Preview failed');
            }
        } catch (error) {
            console.error('Error previewing content:', error);
            this.showError('Failed to preview content: ' + error.message);
        } finally {
            this.setLoading(false);
        }
    }

    showPreview(data, isGenerated = true) {
        const previewSection = document.getElementById('content-generator-preview-section');
        const headlineInput = document.getElementById('content-generator-preview-headline');
        const standfirstInput = document.getElementById('content-generator-preview-standfirst');
        const sectionsDiv = document.getElementById('content-generator-preview-sections');
        const generateBtn = document.getElementById('content-generator-modal-generate');
        const saveBtn = document.getElementById('content-generator-modal-save');
        const previewBtn = document.getElementById('content-generator-modal-preview');
        
        if (previewSection) previewSection.style.display = 'block';
        if (headlineInput) headlineInput.value = data.title || data.headline || '';
        if (standfirstInput) standfirstInput.value = data.standfirst || '';
        
        if (sectionsDiv && data.sections) {
            sectionsDiv.innerHTML = data.sections.map((section, index) => `
                <div class="preview-section-item">
                    <div class="preview-section-header">
                        <strong>${this.escapeHtml(section.heading || `Section ${index + 1}`)}</strong>
                    </div>
                    <div class="preview-section-content">
                        ${this.escapeHtml((section.content || '').substring(0, 200))}${(section.content || '').length > 200 ? '...' : ''}
                    </div>
                </div>
            `).join('');
        }
        
        if (isGenerated) {
            if (generateBtn) generateBtn.style.display = 'none';
            if (saveBtn) saveBtn.style.display = 'inline-block';
            if (previewBtn) previewBtn.style.display = 'inline-block';
        } else {
            if (generateBtn) generateBtn.style.display = 'inline-block';
            if (saveBtn) saveBtn.style.display = 'none';
            if (previewBtn) previewBtn.style.display = 'inline-block';
        }
    }

    async save() {
        if (!this.generatedContent || !this.generatedContent.post_id) {
            this.showError('No generated content to save');
            return;
        }
        
        // Get current week/year from calendar
        const weekNumber = this.currentWeek || parseInt(document.getElementById('week-number')?.textContent || '0');
        const year = this.currentYear || parseInt(document.getElementById('week-year')?.textContent || new Date().getFullYear());
        
        if (!weekNumber) {
            this.showError('Unable to determine week number');
            return;
        }
        
        // Update headline/standfirst if edited
        const headlineInput = document.getElementById('content-generator-preview-headline');
        const standfirstInput = document.getElementById('content-generator-preview-standfirst');
        
        if (headlineInput && headlineInput.value !== this.generatedContent.title) {
            // Update post title via API
            try {
                await fetch(`/api/posts/${this.generatedContent.post_id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title: headlineInput.value })
                });
            } catch (error) {
                console.error('Error updating title:', error);
            }
        }
        
        // Schedule post in calendar
        try {
            const weekday = 1; // Default to Monday
            await fetch('/planning/api/calendar/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    post_id: this.generatedContent.post_id,
                    year: year,
                    week_number: weekNumber,
                    weekday: weekday
                })
            });
            
            // Close modal and navigate to taxonomy page
            this.close();
            window.dispatchEvent(new CustomEvent('content-generated', { detail: { post_id: this.generatedContent.post_id } }));
            
            // Navigate to taxonomy page (generated posts start there)
            const taxonomyUrl = `/planning/posts/${this.generatedContent.post_id}/calendar/taxonomy`;
            window.location.href = taxonomyUrl;
        } catch (error) {
            console.error('Error scheduling post:', error);
            this.showError('Post created but failed to schedule in calendar');
        }
    }

    openNew(week = null, year = null) {
        this.currentWeek = week;
        this.currentYear = year;
        this.reset();
        
        const modal = document.getElementById('content-generator-modal');
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    close() {
        const modal = document.getElementById('content-generator-modal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.reset();
    }

    reset() {
        this.selectedProductId = null;
        this.selectedCategoryId = null;
        this.generatedContent = null;
        this.currentSourceType = 'product';
        
        // Reset form
        const form = document.getElementById('content-generator-modal-form');
        if (form) form.reset();
        
        // Reset UI
        this.clearProduct();
        this.clearCategory();
        this.hideError();
        this.setLoading(false);
        
        const previewSection = document.getElementById('content-generator-preview-section');
        const generateBtn = document.getElementById('content-generator-modal-generate');
        const saveBtn = document.getElementById('content-generator-modal-save');
        const previewBtn = document.getElementById('content-generator-modal-preview');
        
        if (previewSection) previewSection.style.display = 'none';
        if (generateBtn) generateBtn.style.display = 'inline-block';
        if (saveBtn) saveBtn.style.display = 'none';
        if (previewBtn) previewBtn.style.display = 'none';
        
        // Reset type selector
        const productRadio = document.getElementById('content-generator-type-product');
        if (productRadio) productRadio.checked = true;
        this.switchType('product');
    }

    setLoading(loading, text = 'Loading...') {
        const loadingDiv = document.getElementById('content-generator-modal-loading');
        const loadingText = document.getElementById('content-generator-loading-text');
        const body = document.getElementById('content-generator-modal-body');
        const form = document.getElementById('content-generator-modal-form');
        
        if (loadingDiv) loadingDiv.style.display = loading ? 'flex' : 'none';
        if (loadingText) loadingText.textContent = text;
        if (body) body.style.opacity = loading ? '0.6' : '1';
        if (form) form.style.pointerEvents = loading ? 'none' : 'auto';
    }

    showError(message) {
        const errorDiv = document.getElementById('content-generator-modal-error');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    }

    hideError() {
        const errorDiv = document.getElementById('content-generator-modal-error');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global instance
let contentGeneratorModalInstance = null;

function getContentGeneratorModal() {
    if (!contentGeneratorModalInstance) {
        contentGeneratorModalInstance = new ContentGeneratorModal();
    }
    return contentGeneratorModalInstance;
}

