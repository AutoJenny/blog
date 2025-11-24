// Product Match Page JavaScript

console.log('[Product Match Page] Script loading...');

class ProductMatchPage {
    constructor() {
        this.postId = window.postId;
        this.hasEmbeddings = window.hasEmbeddings === true || window.hasEmbeddings === 'true';
        this.currentSelection = {
            product: null,
            category: null,
            supplier: null
        };
        
        this.initializeElements();
        this.bindEvents();
        
        if (this.hasEmbeddings) {
            this.loadProductMatches();
        } else {
            this.showNoEmbeddingsMessage();
        }
    }
    
    initializeElements() {
        this.statusPanel = document.getElementById('status-panel');
        this.statusMessage = document.getElementById('status-message');
        this.matchesContainer = document.getElementById('matches-container');
        this.selectedMatchPanel = document.getElementById('selected-match-panel');
        this.selectedMatchContent = document.getElementById('selected-match-content');
        this.actionButtons = document.getElementById('action-buttons');
        this.saveSelectionBtn = document.getElementById('save-selection-btn');
        this.regenerateBtn = document.getElementById('regenerate-btn');
        
        this.productsList = document.getElementById('products-list');
        this.categoriesList = document.getElementById('categories-list');
        this.suppliersList = document.getElementById('suppliers-list');
        
        console.log('[Product Match] Elements initialized:', {
            selectedMatchPanel: !!this.selectedMatchPanel,
            selectedMatchContent: !!this.selectedMatchContent
        });
    }
    
    bindEvents() {
        if (this.saveSelectionBtn) {
            this.saveSelectionBtn.addEventListener('click', () => this.saveSelection());
        }
        
        if (this.regenerateBtn) {
            this.regenerateBtn.addEventListener('click', () => this.regenerateMatches());
        }
    }
    
    showNoEmbeddingsMessage() {
        if (this.statusMessage) {
            this.statusMessage.innerHTML = '<p style="color: #f59e0b;">No embeddings found. Please generate embeddings on the SEO Meta page first.</p>';
        }
    }
    
    async loadProductMatches() {
        try {
            if (this.statusMessage) {
                this.statusMessage.textContent = 'Loading matches...';
            }
            
            // Build URL - only include year/week for themed posts
            const postType = (window.postType || '').toLowerCase().trim();
            const nonThemedTypes = ['recipe', 'profile', 'generated'];
            const isNonThemedPost = nonThemedTypes.includes(postType);
            
            let url = `/header/api/posts/${this.postId}/product-matches`;
            if (!isNonThemedPost) {
                const urlParams = new URLSearchParams(window.location.search);
                const year = urlParams.get('year') || (window.year && window.year !== 'null' ? window.year : null);
                const week = urlParams.get('week') || (window.week && window.week !== 'null' ? window.week : null);
                if (year && week) {
                    url += `?year=${year}&week=${week}`;
                }
            }
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success) {
                this.displayMatches(data.matches, data.best_match, data.current_selection);
                if (this.actionButtons) {
                    this.actionButtons.style.display = 'block';
                }
            } else {
                if (this.statusMessage) {
                    this.statusMessage.innerHTML = `<p style="color: #ef4444;">${data.error || 'Failed to load matches'}</p>`;
                }
            }
        } catch (error) {
            console.error('[Product Match Page] Error loading matches:', error);
            if (this.statusMessage) {
                this.statusMessage.innerHTML = '<p style="color: #ef4444;">Error loading matches. Please try again.</p>';
            }
        }
    }
    
    displayMatches(matches, bestMatch, currentSelection) {
        // Hide status, show matches
        if (this.statusPanel) {
            this.statusPanel.style.display = 'none';
        }
        if (this.matchesContainer) {
            this.matchesContainer.style.display = 'block';
        }
        
        // Display products
        if (matches.products && matches.products.length > 0) {
            this.displayMatchList('products', matches.products, currentSelection);
        } else {
            document.getElementById('products-section').style.display = 'none';
        }
        
        // Display categories
        if (matches.categories && matches.categories.length > 0) {
            this.displayMatchList('categories', matches.categories, currentSelection);
        } else {
            document.getElementById('categories-section').style.display = 'none';
        }
        
        // Display suppliers
        if (matches.suppliers && matches.suppliers.length > 0) {
            this.displayMatchList('suppliers', matches.suppliers, currentSelection);
        } else {
            document.getElementById('suppliers-section').style.display = 'none';
        }
        
        // Load current selections from overrides
        let hasManualSelection = false;
        if (currentSelection && Object.keys(currentSelection).length > 0) {
            // Check for product selection (new format or legacy)
            const productId = currentSelection.selected_product_id || 
                             (currentSelection.selected_type === 'product' ? currentSelection.selected_id : null);
            if (productId) {
                const productMatch = this.findMatchInList('products', productId, matches);
                if (productMatch) {
                    this.currentSelection.product = productMatch;
                    hasManualSelection = true;
                }
            }
            
            // Check for category selection (new format or legacy)
            const categoryId = currentSelection.selected_category_id || 
                              (currentSelection.selected_type === 'category' ? currentSelection.selected_id : null);
            if (categoryId) {
                const categoryMatch = this.findMatchInList('categories', categoryId, matches);
                if (categoryMatch) {
                    this.currentSelection.category = categoryMatch;
                    hasManualSelection = true;
                }
            }
            
            // Check for supplier selection (new format or legacy)
            const supplierId = currentSelection.selected_supplier_id || 
                             (currentSelection.selected_type === 'supplier' ? currentSelection.selected_id : null);
            if (supplierId) {
                const supplierMatch = this.findMatchInList('suppliers', supplierId, matches);
                if (supplierMatch) {
                    this.currentSelection.supplier = supplierMatch;
                    hasManualSelection = true;
                }
            }
        }
        
        // Auto-select best match if no manual selection exists
        if (!hasManualSelection && bestMatch && bestMatch.match) {
            const bestType = bestMatch.type;
            const bestMatchData = bestMatch.match;
            if (bestType === 'product') {
                this.currentSelection.product = bestMatchData;
            } else if (bestType === 'category') {
                this.currentSelection.category = bestMatchData;
            } else if (bestType === 'supplier') {
                this.currentSelection.supplier = bestMatchData;
            }
        }
        
        // Always auto-select top product and top category if not already selected
        let autoSelected = false;
        if (!this.currentSelection.product && matches.products && matches.products.length > 0) {
            this.currentSelection.product = matches.products[0];
            autoSelected = true;
            console.log('[Product Match] Auto-selected top product:', matches.products[0].name);
        }
        if (!this.currentSelection.category && matches.categories && matches.categories.length > 0) {
            this.currentSelection.category = matches.categories[0];
            autoSelected = true;
            console.log('[Product Match] Auto-selected top category:', matches.categories[0].name);
        }
        
        console.log('[Product Match] After auto-selection:', {
            product: this.currentSelection.product ? this.currentSelection.product.name : null,
            category: this.currentSelection.category ? this.currentSelection.category.name : null
        });
        
        // Display selected matches
        this.displaySelectedMatches();
        
        // Auto-save if we just auto-selected (and there were no previous manual selections)
        if (autoSelected && !hasManualSelection) {
            console.log('[Product Match] Auto-saving initial selections...');
            this.autoSaveSelections();
        }
    }
    
    displayMatchList(type, items, currentSelection) {
        const listElement = document.getElementById(`${type}-list`);
        if (!listElement) return;
        
        listElement.innerHTML = '';
        
        items.forEach((item, index) => {
            const matchItem = document.createElement('div');
            matchItem.className = 'match-item';
            
            // Check if this item is selected
            let isSelected = false;
            if (currentSelection) {
                if (type === 'product' && this.currentSelection.product && this.currentSelection.product.id === item.id) {
                    isSelected = true;
                } else if (type === 'category' && this.currentSelection.category && this.currentSelection.category.id === item.id) {
                    isSelected = true;
                } else if (type === 'supplier' && this.currentSelection.supplier && this.currentSelection.supplier.id === item.id) {
                    isSelected = true;
                }
            }
            
            if (isSelected) {
                matchItem.classList.add('selected');
            }
            
            const score = (item.score * 100).toFixed(1);
            const scoreColor = item.score > 0.8 ? '#10b981' : item.score > 0.6 ? '#f59e0b' : '#64748b';
            
            matchItem.innerHTML = `
                <div class="match-item-content">
                    <div class="match-item-header">
                        <span class="match-item-name">${this.escapeHtml(item.name)}</span>
                        <span class="match-item-id">ID: ${item.id}</span>
                        <span class="match-item-score" style="background: ${scoreColor}">${score}%</span>
                    </div>
                    ${item.metadata && item.metadata.description ? 
                        `<div class="match-item-description">${this.escapeHtml(item.metadata.description.substring(0, 150))}${item.metadata.description.length > 150 ? '...' : ''}</div>` : 
                        ''}
                </div>
                <button class="match-select-btn" data-type="${type}" data-id="${item.id}" data-name="${this.escapeHtml(item.name)}">
                    ${isSelected ? '<i class="fas fa-check"></i> Selected' : 'Select'}
                </button>
            `;
            
            // Add click handler
            const selectBtn = matchItem.querySelector('.match-select-btn');
            selectBtn.addEventListener('click', () => {
                this.selectMatch(type, item.id, item.name, item);
            });
            
            listElement.appendChild(matchItem);
        });
    }
    
    selectMatch(type, id, name, matchData) {
        // Update current selection for this type
        if (type === 'product') {
            this.currentSelection.product = matchData;
        } else if (type === 'category') {
            this.currentSelection.category = matchData;
        } else if (type === 'supplier') {
            this.currentSelection.supplier = matchData;
        }
        
        // Update UI
        this.displaySelectedMatches();
        
        // Update selected state in lists - clear all buttons of this type, then mark current
        document.querySelectorAll(`.match-select-btn[data-type="${type}"]`).forEach(btn => {
            btn.closest('.match-item').classList.remove('selected');
            if (btn.dataset.id !== String(id)) {
                btn.innerHTML = 'Select';
            }
        });
        
        const selectedBtn = document.querySelector(`.match-select-btn[data-type="${type}"][data-id="${id}"]`);
        if (selectedBtn) {
            selectedBtn.closest('.match-item').classList.add('selected');
            selectedBtn.innerHTML = '<i class="fas fa-check"></i> Selected';
        }
    }
    
    displaySelectedMatches() {
        if (!this.selectedMatchPanel || !this.selectedMatchContent) {
            console.warn('[Product Match] Selected match panel elements not found', {
                panel: !!this.selectedMatchPanel,
                content: !!this.selectedMatchContent
            });
            return;
        }
        
        console.log('[Product Match] Current selections state:', {
            product: this.currentSelection.product ? {
                id: this.currentSelection.product.id,
                name: this.currentSelection.product.name
            } : null,
            category: this.currentSelection.category ? {
                id: this.currentSelection.category.id,
                name: this.currentSelection.category.name
            } : null,
            supplier: this.currentSelection.supplier ? {
                id: this.currentSelection.supplier.id,
                name: this.currentSelection.supplier.name
            } : null
        });
        
        const selections = [];
        
        // Product selection
        if (this.currentSelection.product) {
            const match = this.currentSelection.product;
            const score = ((match.score || 0) * 100).toFixed(1);
            selections.push({
                type: 'product',
                typeLabel: 'Product',
                typeIcon: 'fa-box',
                id: match.id,
                name: match.name,
                score: score,
                description: match.metadata && match.metadata.description ? match.metadata.description : ''
            });
            console.log('[Product Match] Added product selection:', match.name, 'ID:', match.id);
        }
        
        // Category selection
        if (this.currentSelection.category) {
            const match = this.currentSelection.category;
            const score = ((match.score || 0) * 100).toFixed(1);
            selections.push({
                type: 'category',
                typeLabel: 'Category',
                typeIcon: 'fa-tags',
                id: match.id,
                name: match.name,
                score: score,
                description: match.metadata && match.metadata.description ? match.metadata.description : ''
            });
            console.log('[Product Match] Added category selection:', match.name, 'ID:', match.id);
        }
        
        // Supplier selection (optional)
        if (this.currentSelection.supplier) {
            const match = this.currentSelection.supplier;
            const score = ((match.score || 0) * 100).toFixed(1);
            selections.push({
                type: 'supplier',
                typeLabel: 'Supplier',
                typeIcon: 'fa-industry',
                id: match.id,
                name: match.name,
                score: score,
                description: match.metadata && match.metadata.description ? match.metadata.description : ''
            });
        }
        
        if (selections.length === 0) {
            console.warn('[Product Match] No selections to display - hiding panel');
            this.selectedMatchPanel.style.display = 'none';
            return;
        }
        
        console.log('[Product Match] Displaying', selections.length, 'selections');
        this.selectedMatchPanel.style.display = 'block';
        
        // Build HTML for all selections
        let html = '';
        selections.forEach(sel => {
            html += `
                <div class="selected-match-info">
                    <div class="selected-match-header">
                        <i class="fas ${sel.typeIcon}"></i>
                        <span class="selected-match-type">${sel.typeLabel}</span>
                        <span class="selected-match-id">ID: ${sel.id}</span>
                        <span class="selected-match-score">${sel.score}% match</span>
                    </div>
                    <div class="selected-match-name">${this.escapeHtml(sel.name)}</div>
                    ${sel.description ? 
                        `<div class="selected-match-description">${this.escapeHtml(sel.description)}</div>` : 
                        ''}
                </div>
            `;
        });
        
        this.selectedMatchContent.innerHTML = html;
    }
    
    findMatchInList(type, id, allMatches) {
        const list = allMatches[type] || [];
        return list.find(item => item.id === id);
    }
    
    async autoSaveSelections() {
        // Silently save selections without user interaction
        try {
            const postType = (window.postType || '').toLowerCase().trim();
            const nonThemedTypes = ['recipe', 'profile', 'generated'];
            const isNonThemedPost = nonThemedTypes.includes(postType);
            
            // Save product selection if exists
            if (this.currentSelection.product) {
                let url = `/header/api/posts/${this.postId}/update-product-match`;
                if (!isNonThemedPost) {
                    const urlParams = new URLSearchParams(window.location.search);
                    const year = urlParams.get('year') || (window.year && window.year !== 'null' ? window.year : null);
                    const week = urlParams.get('week') || (window.week && window.week !== 'null' ? window.week : null);
                    if (year && week) {
                        url += `?year=${year}&week=${week}`;
                    }
                }
                
                await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        selected_type: 'product',
                        selected_id: this.currentSelection.product.id
                    })
                });
            }
            
            // Save category selection if exists
            if (this.currentSelection.category) {
                let url = `/header/api/posts/${this.postId}/update-product-match`;
                if (!isNonThemedPost) {
                    const urlParams = new URLSearchParams(window.location.search);
                    const year = urlParams.get('year') || (window.year && window.year !== 'null' ? window.year : null);
                    const week = urlParams.get('week') || (window.week && window.week !== 'null' ? window.week : null);
                    if (year && week) {
                        url += `?year=${year}&week=${week}`;
                    }
                }
                
                await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        selected_type: 'category',
                        selected_id: this.currentSelection.category.id
                    })
                });
            }
            
            console.log('[Product Match] Auto-saved initial selections successfully');
        } catch (error) {
            console.error('[Product Match] Error auto-saving selections:', error);
            // Don't show alert for auto-save failures - user can manually save if needed
        }
    }
    
    async saveSelection() {
        // Check if at least one selection exists
        if (!this.currentSelection.product && !this.currentSelection.category && !this.currentSelection.supplier) {
            alert('Please select at least one product or category match');
            return;
        }
        
        try {
            if (this.saveSelectionBtn) {
                this.saveSelectionBtn.disabled = true;
                this.saveSelectionBtn.textContent = 'Saving...';
            }
            
            // Build URL
            const postType = (window.postType || '').toLowerCase().trim();
            const nonThemedTypes = ['recipe', 'profile', 'generated'];
            const isNonThemedPost = nonThemedTypes.includes(postType);
            
            // Save product selection if exists
            if (this.currentSelection.product) {
                let url = `/header/api/posts/${this.postId}/update-product-match`;
                if (!isNonThemedPost) {
                    const urlParams = new URLSearchParams(window.location.search);
                    const year = urlParams.get('year') || (window.year && window.year !== 'null' ? window.year : null);
                    const week = urlParams.get('week') || (window.week && window.week !== 'null' ? window.week : null);
                    if (year && week) {
                        url += `?year=${year}&week=${week}`;
                    }
                }
                
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        selected_type: 'product',
                        selected_id: this.currentSelection.product.id
                    })
                });
                
                const data = await response.json();
                if (!data.success) {
                    throw new Error(data.error || 'Failed to save product selection');
                }
            }
            
            // Save category selection if exists
            if (this.currentSelection.category) {
                let url = `/header/api/posts/${this.postId}/update-product-match`;
                if (!isNonThemedPost) {
                    const urlParams = new URLSearchParams(window.location.search);
                    const year = urlParams.get('year') || (window.year && window.year !== 'null' ? window.year : null);
                    const week = urlParams.get('week') || (window.week && window.week !== 'null' ? window.week : null);
                    if (year && week) {
                        url += `?year=${year}&week=${week}`;
                    }
                }
                
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        selected_type: 'category',
                        selected_id: this.currentSelection.category.id
                    })
                });
                
                const data = await response.json();
                if (!data.success) {
                    throw new Error(data.error || 'Failed to save category selection');
                }
            }
            
            // Success
            if (this.saveSelectionBtn) {
                this.saveSelectionBtn.textContent = 'Saved!';
                setTimeout(() => {
                    this.saveSelectionBtn.textContent = 'Save Selection';
                    this.saveSelectionBtn.disabled = false;
                }, 2000);
            }
            console.log('[Product Match Page] Selections saved successfully');
            
        } catch (error) {
            console.error('[Product Match Page] Error saving selection:', error);
            alert('Error saving selection: ' + error.message);
            if (this.saveSelectionBtn) {
                this.saveSelectionBtn.disabled = false;
                this.saveSelectionBtn.textContent = 'Save Selection';
            }
        }
    }
    
    async regenerateMatches() {
        try {
            if (this.regenerateBtn) {
                this.regenerateBtn.disabled = true;
                this.regenerateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Regenerating...';
            }
            
            // Build URL
            const postType = (window.postType || '').toLowerCase().trim();
            const nonThemedTypes = ['recipe', 'profile', 'generated'];
            const isNonThemedPost = nonThemedTypes.includes(postType);
            
            let url = `/header/api/posts/${this.postId}/regenerate-matches`;
            if (!isNonThemedPost) {
                const urlParams = new URLSearchParams(window.location.search);
                const year = urlParams.get('year') || (window.year && window.year !== 'null' ? window.year : null);
                const week = urlParams.get('week') || (window.week && window.week !== 'null' ? window.week : null);
                if (year && week) {
                    url += `?year=${year}&week=${week}`;
                }
            }
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayMatches(data.matches, data.best_match, this.currentSelection);
                console.log('[Product Match Page] Matches regenerated successfully');
            } else {
                alert('Failed to regenerate matches: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('[Product Match Page] Error regenerating matches:', error);
            alert('Error regenerating matches. Please try again.');
        } finally {
            if (this.regenerateBtn) {
                this.regenerateBtn.disabled = false;
                this.regenerateBtn.innerHTML = '<i class="fas fa-sync"></i> Regenerate Matches';
            }
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Toggle match section accordion
function toggleMatchSection(type) {
    const content = document.getElementById(`${type}-content`);
    const chevron = document.getElementById(`${type}-chevron`);
    
    if (content && chevron) {
        const isOpen = !content.classList.contains('collapsed');
        if (isOpen) {
            content.classList.add('collapsed');
            chevron.style.transform = 'rotate(-90deg)';
        } else {
            content.classList.remove('collapsed');
            chevron.style.transform = 'rotate(0deg)';
        }
    }
}

// Initialize page when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Product Match Page] Initializing page...');
    window.productMatchPage = new ProductMatchPage();
});

