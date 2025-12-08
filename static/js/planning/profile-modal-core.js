/**
 * Profile Modal Core
 * Main modal class for creating and editing Product & Category Profiles
 */

class ProfileModal {
    constructor() {
        this.currentProfileId = null;
        this.currentType = 'product'; // 'product' or 'category'
        this.currentWeek = null;
        this.currentYear = null;
        
        this.init();
    }

    init() {
        // Close button
        const closeBtn = document.getElementById('profile-modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }

        // Cancel button
        const cancelBtn = document.getElementById('profile-modal-cancel');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.close());
        }

        // Save button
        const saveBtn = document.getElementById('profile-modal-save');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.save());
        }

        // Delete button
        const deleteBtn = document.getElementById('profile-modal-delete');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => this.delete());
        }

        // Type selector radio buttons
        const typeRadios = document.querySelectorAll('input[name="profile-type"]');
        typeRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.switchType(e.target.value);
            });
        });

        // Type selector buttons
        const typeButtons = document.querySelectorAll('.profile-type-btn');
        typeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const type = btn.dataset.type;
                this.switchType(type);
                typeButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        // Product search
        const productSearch = document.getElementById('profile-product-search');
        if (productSearch) {
            let searchTimeout;
            productSearch.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.searchProducts(e.target.value);
                }, 300);
            });
        }

        // Category select
        const categorySelect = document.getElementById('profile-category-select');
        if (categorySelect) {
            categorySelect.addEventListener('change', (e) => {
                this.selectCategory(e.target.value);
            });
            this.loadCategories();
        }

        // Remove buttons
        const removeProduct = document.getElementById('remove-product');
        if (removeProduct) {
            removeProduct.addEventListener('click', () => {
                this.clearProduct();
            });
        }

        const removeCategory = document.getElementById('remove-category');
        if (removeCategory) {
            removeCategory.addEventListener('click', () => {
                this.clearCategory();
            });
        }

        // Close on backdrop click
        const modal = document.getElementById('profile-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.close();
                }
            });
        }
    }

    switchType(type) {
        this.currentType = type;
        
        // Update radio buttons - map 'surname' to 'category' since HTML only has product/category
        const mappedType = type === 'surname' ? 'category' : type;
        const radioButton = document.getElementById(`profile-type-${mappedType}`);
        if (radioButton) {
            radioButton.checked = true;
        }
        
        // Show/hide sections
        const productSection = document.getElementById('product-selection-section');
        const categorySection = document.getElementById('category-selection-section');
        
        if (type === 'product') {
            if (productSection) productSection.style.display = 'block';
            if (categorySection) categorySection.style.display = 'none';
        } else {
            if (productSection) productSection.style.display = 'none';
            if (categorySection) categorySection.style.display = 'block';
        }
    }

    async searchProducts(query) {
        if (!query || query.length < 2) {
            const results = document.getElementById('product-search-results');
            if (results) {
                results.classList.remove('show');
            }
            return;
        }

        try {
            const response = await fetch(`/api/clan/products?q=${encodeURIComponent(query)}&limit=10`);
            const data = await response.json();
            
            const results = document.getElementById('product-search-results');
            if (!results) return;

            // Handle different response formats
            const products = data.products || (Array.isArray(data) ? data : []);
            
            if (products.length > 0) {
                results.innerHTML = products.map(product => `
                    <div class="search-result-item" data-product-id="${product.id}" data-product-sku="${product.sku}">
                        <strong>${product.name}</strong>
                        ${product.supplier_name ? `<br><small>${product.supplier_name}</small>` : ''}
                        ${product.price ? `<br><small>£${product.price}</small>` : ''}
                    </div>
                `).join('');
                
                // Add click handlers
                results.querySelectorAll('.search-result-item').forEach(item => {
                    item.addEventListener('click', () => {
                        const productId = item.dataset.productId;
                        const productSku = item.dataset.productSku;
                        this.selectProduct(productId, productSku);
                    });
                });
                
                results.classList.add('show');
            } else {
                results.innerHTML = '<div class="search-result-item">No products found</div>';
                results.classList.add('show');
            }
        } catch (error) {
            console.error('Error searching products:', error);
        }
    }

    async selectProduct(productId, sku) {
        try {
            // Fetch full product details
            const response = await fetch(`/api/clan/products/${sku}/full`);
            const data = await response.json();
            
            if (data.success && data.product) {
                const product = data.product;
                
                // Update selected product display
                const selectedDiv = document.getElementById('selected-product');
                const nameEl = document.getElementById('selected-product-name');
                const producerEl = document.getElementById('selected-product-producer');
                const priceEl = document.getElementById('selected-product-price');
                const imageEl = document.getElementById('selected-product-image');
                
                if (nameEl) nameEl.textContent = product.name;
                if (producerEl) producerEl.textContent = product.supplier_name || 'Unknown producer';
                if (priceEl) priceEl.textContent = product.price ? `£${product.price}` : 'Price not available';
                if (imageEl) imageEl.src = product.image_url || '';
                
                if (selectedDiv) selectedDiv.style.display = 'flex';
                
                // Hide search results
                const results = document.getElementById('product-search-results');
                if (results) results.classList.remove('show');
                
                // Clear search input
                const searchInput = document.getElementById('profile-product-search');
                if (searchInput) searchInput.value = '';
                
                // Store selected product
                this.selectedProductId = productId;
                this.selectedProductSku = sku;
                this.selectedProduct = product;
            }
        } catch (error) {
            console.error('Error selecting product:', error);
            alert('Error loading product details');
        }
    }

    clearProduct() {
        const selectedDiv = document.getElementById('selected-product');
        if (selectedDiv) selectedDiv.style.display = 'none';
        this.selectedProductId = null;
        this.selectedProductSku = null;
        this.selectedProduct = null;
    }

    async loadCategories() {
        try {
            const response = await fetch('/launchpad/api/syndication/categories');
            const data = await response.json();
            
            if (data.success && data.categories) {
                const select = document.getElementById('profile-category-select');
                if (!select) return;
                
                select.innerHTML = '<option value="">-- Select Category --</option>';
                
                // Build category tree
                const buildOptions = (categories, parentId = null, level = 0) => {
                    const filtered = categories.filter(cat => cat.parent_id === parentId);
                    filtered.forEach(cat => {
                        const indent = '  '.repeat(level);
                        const option = document.createElement('option');
                        option.value = cat.id;
                        option.textContent = `${indent}${cat.name}`;
                        select.appendChild(option);
                        
                        // Recursively add children
                        buildOptions(categories, cat.id, level + 1);
                    });
                };
                
                buildOptions(data.categories);
            }
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    selectCategory(categoryId) {
        if (!categoryId) {
            this.clearCategory();
            return;
        }

        // Find category in loaded data (would need to store this)
        const select = document.getElementById('profile-category-select');
        const selectedOption = select.options[select.selectedIndex];
        
        if (selectedOption) {
            const selectedDiv = document.getElementById('selected-category');
            const nameEl = document.getElementById('selected-category-name');
            const pathEl = document.getElementById('selected-category-path');
            
            if (nameEl) nameEl.textContent = selectedOption.textContent.trim();
            if (pathEl) pathEl.textContent = selectedOption.textContent.trim();
            
            if (selectedDiv) selectedDiv.style.display = 'flex';
            
            this.selectedCategoryId = categoryId;
        }
    }

    clearCategory() {
        const selectedDiv = document.getElementById('selected-category');
        if (selectedDiv) selectedDiv.style.display = 'none';
        this.selectedCategoryId = null;
    }

    openNew(week = null, year = null) {
        this.currentProfileId = null;
        this.currentType = 'product';
        this.currentWeek = week;
        this.currentYear = year;
        
        // Get current week from calendar if not provided
        if (!week || !year) {
            const weekEl = document.getElementById('week-number');
            const yearEl = document.getElementById('week-year');
            if (weekEl) this.currentWeek = parseInt(weekEl.textContent);
            if (yearEl) this.currentYear = parseInt(yearEl.textContent);
        }
        
        // Update week display
        const weekDisplay = document.getElementById('profile-week-display');
        if (weekDisplay && this.currentWeek && this.currentYear) {
            weekDisplay.value = `Week ${this.currentWeek}, ${this.currentYear}`;
        }
        
        const yearInput = document.getElementById('profile-year');
        const weekInput = document.getElementById('profile-week-number');
        if (yearInput) yearInput.value = this.currentYear || '';
        if (weekInput) weekInput.value = this.currentWeek || '';
        
        this.resetForm();
        this.show();
    }

    async open(profileId) {
        this.currentProfileId = profileId;
        
        const modal = document.getElementById('profile-modal');
        const loading = document.getElementById('profile-modal-loading');
        const form = document.getElementById('profile-modal-form');
        
        if (modal) modal.style.display = 'flex';
        if (loading) loading.style.display = 'block';
        if (form) form.style.display = 'none';
        
        try {
            // Load profile data
            const response = await fetch(`/planning/api/profiles/${profileId}`);
            const data = await response.json();
            
            if (data.success && data.profile) {
                const profile = data.profile;
                // Map 'surname' to 'category' for the modal UI
                const modalType = profile.profile_type === 'surname' ? 'category' : (profile.profile_type || 'product');
                this.currentType = modalType;
                
                // Populate form
                this.populateForm(profile);
                
                // Show delete button
                const deleteBtn = document.getElementById('profile-modal-delete');
                if (deleteBtn) deleteBtn.style.display = 'block';
            } else {
                alert('Error loading profile');
                this.close();
            }
        } catch (error) {
            console.error('Error loading profile:', error);
            alert('Error loading profile');
            this.close();
        } finally {
            if (loading) loading.style.display = 'none';
            if (form) form.style.display = 'block';
        }
    }

    populateForm(profile) {
        // Title
        const titleInput = document.getElementById('profile-title');
        if (titleInput) titleInput.value = profile.title || '';
        
        // Standfirst
        const standfirstInput = document.getElementById('profile-standfirst');
        if (standfirstInput) standfirstInput.value = profile.profile_standfirst || '';
        
        // Type
        this.switchType(this.currentType);
        
        // Product or Category selection
        if (this.currentType === 'product' && profile.profile_product_id) {
            // Load and display product
            // This would need product SKU or another way to fetch
        } else if (this.currentType === 'category' && profile.profile_category_id) {
            this.selectCategory(profile.profile_category_id);
        }
    }

    resetForm() {
        const form = document.getElementById('profile-modal-form');
        if (form) form.reset();
        
        this.clearProduct();
        this.clearCategory();
        
        // Hide delete button
        const deleteBtn = document.getElementById('profile-modal-delete');
        if (deleteBtn) deleteBtn.style.display = 'none';
        
        // Reset type
        this.switchType('product');
    }

    async save() {
        const form = document.getElementById('profile-modal-form');
        if (!form) return;
        
        // Validate
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        // Validate selection
        if (this.currentType === 'product' && !this.selectedProductId) {
            alert('Please select a product');
            return;
        }
        
        if (this.currentType === 'category' && !this.selectedCategoryId) {
            alert('Please select a category');
            return;
        }
        
        // Build data
        const formData = {
            profile_type: this.currentType,
            title: document.getElementById('profile-title').value,
            profile_standfirst: document.getElementById('profile-standfirst').value,
            year: document.getElementById('profile-year').value,
            week_number: document.getElementById('profile-week-number').value,
            weekday: document.getElementById('profile-weekday').value || null
        };
        
        if (this.currentType === 'product') {
            formData.profile_product_id = this.selectedProductId;
            if (this.selectedProduct) {
                formData.profile_producer_name = this.selectedProduct.supplier_name;
            }
        } else {
            formData.profile_category_id = this.selectedCategoryId;
        }
        
        try {
            const url = this.currentProfileId 
                ? `/planning/api/profiles/${this.currentProfileId}`
                : '/planning/api/profiles';
            const method = this.currentProfileId ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Reload calendar week view
                if (window.loadWeek && this.currentYear && this.currentWeek) {
                    await window.loadWeek(this.currentYear, this.currentWeek);
                }
                this.close();
            } else {
                this.showError(data.error || 'Error saving profile');
            }
        } catch (error) {
            console.error('Error saving profile:', error);
            this.showError('Error saving profile');
        }
    }

    async delete() {
        if (!this.currentProfileId) return;
        
        if (!confirm('Are you sure you want to delete this profile?')) {
            return;
        }
        
        try {
            const response = await fetch(`/planning/api/profiles/${this.currentProfileId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Reload calendar week view
                if (window.loadWeek && this.currentYear && this.currentWeek) {
                    await window.loadWeek(this.currentYear, this.currentWeek);
                }
                this.close();
            } else {
                this.showError(data.error || 'Error deleting profile');
            }
        } catch (error) {
            console.error('Error deleting profile:', error);
            this.showError('Error deleting profile');
        }
    }

    showError(message) {
        const errorEl = document.getElementById('profile-modal-error');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
            setTimeout(() => {
                errorEl.style.display = 'none';
            }, 5000);
        }
    }

    show() {
        const modal = document.getElementById('profile-modal');
        if (modal) modal.style.display = 'flex';
    }

    close() {
        const modal = document.getElementById('profile-modal');
        if (modal) modal.style.display = 'none';
        this.resetForm();
    }
}

// Initialize and expose globally
let profileModalInstance = null;

function getProfileModal() {
    if (!profileModalInstance) {
        profileModalInstance = new ProfileModal();
    }
    return profileModalInstance;
}

// Expose globally
window.getProfileModal = getProfileModal;

