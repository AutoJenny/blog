/**
 * Substage Management UI Controller
 */

const API_BASE = '/settings/api/substage-management';

let overviewData = null;
let postTypes = [];
let stages = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Substage management page loaded');
    
    try {
        initTabs();
        loadOverview();
        
        // Event listeners
        const refreshBtn = document.getElementById('refresh-btn');
        const postTypeSelector = document.getElementById('post-type-selector');
        const channelPostTypeSelector = document.getElementById('channel-post-type-selector');
        const outputChannelSelector = document.getElementById('output-channel-selector');
        const addSubstageBtn = document.getElementById('add-substage-btn');
        const overviewStageFilter = document.getElementById('overview-stage-filter');
        const overviewPostTypeFilter = document.getElementById('overview-post-type-filter');
        
        if (refreshBtn) refreshBtn.addEventListener('click', loadOverview);
        if (postTypeSelector) postTypeSelector.addEventListener('change', loadPostTypeConfig);
        if (channelPostTypeSelector) channelPostTypeSelector.addEventListener('change', loadOutputChannelConfig);
        if (outputChannelSelector) outputChannelSelector.addEventListener('change', loadOutputChannelConfig);
        if (addSubstageBtn) addSubstageBtn.addEventListener('click', showAddSubstageModal);
        if (overviewStageFilter) overviewStageFilter.addEventListener('change', renderUsageOverview);
        if (overviewPostTypeFilter) overviewPostTypeFilter.addEventListener('change', renderUsageOverview);
        
        console.log('Event listeners attached');
    } catch (error) {
        console.error('Error initializing page:', error);
        const contentEl = document.getElementById('post-types-content');
        if (contentEl) {
            contentEl.innerHTML = '<p class="text-red-400">Error initializing: ' + error.message + '</p>';
        }
    }
});

function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            
            // Update buttons
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update panels
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            document.getElementById(`${tabName}-tab`).classList.add('active');
            
            // Load tab-specific data
            if (tabName === 'post-types' && overviewData) {
                loadPostTypeConfig();
            } else if (tabName === 'output-channels' && overviewData) {
                loadOutputChannelConfig();
            } else if (tabName === 'substage-metadata' && overviewData) {
                renderSubstageMetadata();
            } else if (tabName === 'usage-overview' && overviewData) {
                renderUsageOverview();
            }
        });
    });
}

async function loadOverview() {
    try {
        console.log('Loading overview from:', `${API_BASE}/overview`);
        const response = await fetch(`${API_BASE}/overview`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('Overview response:', result);
        
        if (result.success && result.data) {
            overviewData = result.data;
            
            // Extract post types and stages
            postTypes = [...new Set(overviewData.substages.flatMap(s => Object.keys(s.post_types || {})))];
            stages = [...new Set(overviewData.substages.map(s => s.stage))].sort();
            
            console.log('Extracted post types:', postTypes);
            console.log('Extracted stages:', stages);
            
            // Populate selectors
            populatePostTypeSelectors();
            populateStageFilter();
            
            // Auto-select post type if provided in URL/context
            const initialPostType = document.getElementById('initial-post-type');
            if (initialPostType && initialPostType.value) {
                const postTypeSelector = document.getElementById('post-type-selector');
                if (postTypeSelector) {
                    postTypeSelector.value = initialPostType.value;
                    // Trigger change to load config
                    loadPostTypeConfig();
                }
            } else {
                // Remove loading indicators and update content
                const postTypesContent = document.getElementById('post-types-content');
                if (!postTypesContent) {
                    throw new Error('post-types-content element not found');
                }
                postTypesContent.innerHTML = '<p class="text-dark-text">Please select a post type from the dropdown above.</p>';
            }
            
            // Auto-select channel post type and output if provided
            const initialChannelPostType = document.getElementById('initial-channel-post-type');
            if (initialChannelPostType && initialChannelPostType.value) {
                const channelPostTypeSelector = document.getElementById('channel-post-type-selector');
                if (channelPostTypeSelector) {
                    channelPostTypeSelector.value = initialChannelPostType.value;
                    // If output channel is already selected, load config
                    const outputChannelSelector = document.getElementById('output-channel-selector');
                    if (outputChannelSelector && outputChannelSelector.value) {
                        loadOutputChannelConfig();
                    }
                }
            }
            
            // Load current tab
            const activeTabBtn = document.querySelector('.tab-btn.active');
            if (activeTabBtn) {
                const activeTab = activeTabBtn.dataset.tab;
                console.log('Active tab:', activeTab);
                if (activeTab === 'substage-metadata') {
                    renderSubstageMetadata();
                } else if (activeTab === 'usage-overview') {
                    renderUsageOverview();
                }
            } else {
                throw new Error('No active tab button found - page structure invalid');
            }
        } else {
            const errorMsg = result.error || 'API returned success=false with no error message';
            console.error('API error:', errorMsg);
            throw new Error(errorMsg);
        }
    } catch (error) {
        console.error('Error loading overview:', error);
        const contentEl = document.getElementById('post-types-content');
        if (contentEl) {
            contentEl.innerHTML = 
                '<p class="text-red-400">Error: ' + error.message + '</p>';
        }
        throw error; // Re-throw to prevent silent failure
    }
}

function populatePostTypeSelectors() {
    const selectors = [
        document.getElementById('post-type-selector'),
        document.getElementById('channel-post-type-selector'),
        document.getElementById('overview-post-type-filter')
    ];
    
    selectors.forEach(selector => {
        if (selector) {
            if (postTypes.length > 0) {
                selector.innerHTML = '<option value="">Select Post Type...</option>' +
                    postTypes.map(pt => `<option value="${pt}">${pt}</option>`).join('');
            } else {
                selector.innerHTML = '<option value="">No post types found</option>';
            }
        }
    });
    console.log('Populated post type selectors with', postTypes.length, 'types');
}

function populateStageFilter() {
    const filter = document.getElementById('overview-stage-filter');
    if (filter) {
        if (stages.length > 0) {
            filter.innerHTML = '<option value="">All Stages</option>' +
                stages.map(s => `<option value="${s}">${s}</option>`).join('');
        } else {
            filter.innerHTML = '<option value="">No stages found</option>';
        }
    }
    console.log('Populated stage filter with', stages.length, 'stages');
}

async function loadPostTypeConfig() {
    const postType = document.getElementById('post-type-selector').value;
    if (!postType) {
        document.getElementById('post-types-content').innerHTML = '<p class="text-dark-text">Please select a post type.</p>';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/post-types/${postType}`);
        const result = await response.json();
        
        if (result.success) {
            renderPostTypeConfig(postType, result.substages);
        } else {
            showError('Failed to load post type config');
        }
    } catch (error) {
        console.error('Error loading post type config:', error);
        showError('Error loading config: ' + error.message);
    }
}

function renderPostTypeConfig(postType, substages) {
    const container = document.getElementById('post-types-content');
    
    let html = '<div class="space-y-6">';
    
    for (const [stage, substageList] of Object.entries(substages)) {
        html += `
            <div class="stage-section">
                <h3 class="stage-title">${stage.charAt(0).toUpperCase() + stage.slice(1)}</h3>
                <div class="substages-list" data-stage="${stage}">
        `;
        
        substageList.forEach((sub, index) => {
            html += `
                <div class="substage-item" data-substage="${sub.key}">
                    <div class="flex items-center gap-3 flex-1">
                        <i class="fas fa-grip-vertical substage-drag-handle"></i>
                        <input type="checkbox" 
                               class="substage-checkbox" 
                               ${sub.active !== false ? 'checked' : ''}
                               data-substage="${sub.key}"
                               data-stage="${stage}">
                        <span class="text-white">${sub.label}</span>
                        <span class="text-dark-text text-sm">(${sub.key})</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-dark-text text-sm">Order:</span>
                        <input type="number" 
                               class="substage-order-input" 
                               value="${sub.order || index + 1}"
                               data-substage="${sub.key}"
                               data-stage="${stage}">
                    </div>
                </div>
            `;
        });
        
        html += `
                </div>
                <button class="mt-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition save-stage-btn"
                        data-stage="${stage}">
                    <i class="fas fa-save"></i> Save Changes
                </button>
            </div>
        `;
    }
    
    html += '</div>';
    container.innerHTML = html;
    
    // Bind event listeners
    container.querySelectorAll('.substage-checkbox').forEach(cb => {
        cb.addEventListener('change', handleSubstageToggle);
    });
    
    container.querySelectorAll('.save-stage-btn').forEach(btn => {
        btn.addEventListener('click', handleSaveStageOrder);
    });
    
    // Make draggable
    initDragAndDrop(container);
}

async function loadOutputChannelConfig() {
    const postType = document.getElementById('channel-post-type-selector').value;
    const outputChannel = document.getElementById('output-channel-selector').value;
    
    if (!postType || !outputChannel) {
        document.getElementById('output-channels-content').innerHTML = 
            '<p class="text-dark-text">Please select both post type and output channel.</p>';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/output-channels/${postType}/${outputChannel}`);
        const result = await response.json();
        
        if (result.success) {
            renderOutputChannelConfig(postType, outputChannel, result);
        } else {
            showError('Failed to load output channel config');
        }
    } catch (error) {
        console.error('Error loading output channel config:', error);
        showError('Error loading config: ' + error.message);
    }
}

function renderOutputChannelConfig(postType, outputChannel, config) {
    const container = document.getElementById('output-channels-content');
    
    let html = `
        <div class="mb-4 p-4 bg-[#23273a] rounded-lg border border-dark-border">
            <label class="flex items-center gap-2">
                <input type="checkbox" 
                       id="use-post-type-config" 
                       ${config.use_post_type_config ? 'checked' : ''}>
                <span class="text-white">Use Post Type Configuration (inherit from ${postType})</span>
            </label>
        </div>
    `;
    
    if (!config.use_post_type_config && config.substages) {
        for (const [stage, substageList] of Object.entries(config.substages)) {
            html += `
                <div class="stage-section">
                    <h3 class="stage-title">${stage.charAt(0).toUpperCase() + stage.slice(1)}</h3>
                    <div class="substages-list" data-stage="${stage}">
            `;
            
            substageList.forEach((sub, index) => {
                html += `
                    <div class="substage-item" data-substage="${sub.key}">
                        <div class="flex items-center gap-3 flex-1">
                            <input type="checkbox" 
                                   class="substage-checkbox" 
                                   ${sub.active !== false ? 'checked' : ''}
                                   data-substage="${sub.key}"
                                   data-stage="${stage}">
                            <span class="text-white">${sub.key}</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="text-dark-text text-sm">Order:</span>
                            <input type="number" 
                                   class="substage-order-input" 
                                   value="${sub.order || index + 1}"
                                   data-substage="${sub.key}"
                                   data-stage="${stage}">
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                    <button class="mt-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition save-stage-btn"
                            data-stage="${stage}">
                        <i class="fas fa-save"></i> Save Changes
                    </button>
                </div>
            `;
        }
    } else {
        html += '<p class="text-dark-text">Using post type configuration. No channel-specific overrides.</p>';
    }
    
    container.innerHTML = html;
}

function renderSubstageMetadata() {
    if (!overviewData) {
        throw new Error('Overview data not loaded');
    }
    
    const container = document.getElementById('substage-metadata-content');
    if (!container) {
        throw new Error('substage-metadata-content element not found');
    }
    
    let html = '<div class="overflow-x-auto"><table class="usage-matrix w-full">';
    html += '<thead><tr><th>Key</th><th>Label</th><th>Stage</th><th>Route Function</th><th>Order</th><th>Active</th><th>Actions</th></tr></thead><tbody>';
    
    overviewData.substages.forEach(sub => {
        html += `
            <tr>
                <td>${sub.key}</td>
                <td>${sub.label}</td>
                <td>${sub.stage}</td>
                <td>${sub.route_function || '-'}</td>
                <td>${sub.order}</td>
                <td>${sub.is_active ? '<span class="active">✓</span>' : '<span class="inactive">✗</span>'}</td>
                <td>
                    <button class="px-2 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-sm edit-substage-btn"
                            data-key="${sub.key}">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

function renderUsageOverview() {
    if (!overviewData) {
        throw new Error('Overview data not loaded');
    }
    
    const stageFilter = document.getElementById('overview-stage-filter').value;
    const postTypeFilter = document.getElementById('overview-post-type-filter').value;
    
    const container = document.getElementById('usage-overview-content');
    if (!container) {
        throw new Error('usage-overview-content element not found');
    }
    
    // Filter substages
    let filteredSubstages = overviewData.substages;
    if (stageFilter) {
        filteredSubstages = filteredSubstages.filter(s => s.stage === stageFilter);
    }
    
    let html = '<div class="usage-matrix"><table class="w-full">';
    html += '<thead><tr><th>Substage</th>';
    
    // Add columns for each post type
    postTypes.forEach(pt => {
        if (!postTypeFilter || pt === postTypeFilter) {
            html += `<th>${pt}</th>`;
        }
    });
    
    html += '</tr></thead><tbody>';
    
    filteredSubstages.forEach(sub => {
        html += `<tr><td>${sub.label} (${sub.key})</td>`;
        
        postTypes.forEach(pt => {
            if (!postTypeFilter || pt === postTypeFilter) {
                const usage = sub.post_types?.[pt];
                if (usage) {
                    const stages = Object.keys(usage);
                    const activeStages = stages.filter(s => usage[s].active);
                    html += `<td>${activeStages.length > 0 ? `<span class="active">${activeStages.join(', ')}</span>` : '<span class="inactive">-</span>'}</td>`;
                } else {
                    html += '<td><span class="inactive">-</span></td>';
                }
            }
        });
        
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

async function handleSubstageToggle(event) {
    const checkbox = event.target;
    const substageKey = checkbox.dataset.substage;
    const stage = checkbox.dataset.stage;
    const postType = document.getElementById('post-type-selector').value;
    const isActive = checkbox.checked;
    
    try {
        const response = await fetch(`${API_BASE}/substage/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                substage_key: substageKey,
                post_type: postType,
                stage: stage,
                output_channel: null,
                is_active: isActive
            })
        });
        
        const result = await response.json();
        if (result.success) {
            showSuccess('Substage toggled successfully');
            // Reload to refresh UI
            loadPostTypeConfig();
        } else {
            showError(result.error || 'Failed to toggle substage');
            checkbox.checked = !isActive; // Revert
        }
    } catch (error) {
        console.error('Error toggling substage:', error);
        showError('Error: ' + error.message);
        checkbox.checked = !isActive; // Revert
    }
}

async function handleSaveStageOrder(event) {
    const btn = event.target.closest('.save-stage-btn');
    const stage = btn.dataset.stage;
    const postType = document.getElementById('post-type-selector').value;
    
    const substageList = btn.closest('.stage-section').querySelector('.substages-list');
    const substageItems = Array.from(substageList.querySelectorAll('.substage-item'));
    const substageKeys = substageItems.map(item => item.dataset.substage);
    
    try {
        const response = await fetch(`${API_BASE}/substage/reorder`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                post_type: postType,
                stage: stage,
                output_channel: null,
                substage_keys: substageKeys
            })
        });
        
        const result = await response.json();
        if (result.success) {
            showSuccess('Substages reordered successfully');
            loadPostTypeConfig();
        } else {
            showError(result.error || 'Failed to reorder substages');
        }
    } catch (error) {
        console.error('Error reordering substages:', error);
        showError('Error: ' + error.message);
    }
}

function initDragAndDrop(container) {
    // Simple drag and drop implementation
    const lists = container.querySelectorAll('.substages-list');
    lists.forEach(list => {
        const items = list.querySelectorAll('.substage-item');
        items.forEach(item => {
            item.draggable = true;
            item.addEventListener('dragstart', handleDragStart);
            item.addEventListener('dragover', handleDragOver);
            item.addEventListener('drop', handleDrop);
            item.addEventListener('dragend', handleDragEnd);
        });
    });
}

let draggedElement = null;

function handleDragStart(e) {
    draggedElement = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
}

function handleDragOver(e) {
    if (e.preventDefault) e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    
    const afterElement = getDragAfterElement(this.parentNode, e.clientY);
    if (afterElement == null) {
        this.parentNode.appendChild(draggedElement);
    } else {
        this.parentNode.insertBefore(draggedElement, afterElement);
    }
}

function handleDrop(e) {
    if (e.stopPropagation) e.stopPropagation();
    return false;
}

function handleDragEnd(e) {
    this.classList.remove('dragging');
    draggedElement = null;
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.substage-item:not(.dragging)')];
    
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

function showAddSubstageModal() {
    // Simple prompt for now - can be enhanced with a proper modal
    const key = prompt('Enter substage key:');
    if (!key) return;
    
    const label = prompt('Enter label:', key.replace('_', ' ').title());
    if (!label) return;
    
    const stage = prompt('Enter stage (calendar, planning, research, authoring, imaging, header, content):');
    if (!stage) return;
    
    // Create substage via API
    fetch(`${API_BASE}/substage-metadata`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            substage_key: key,
            label: label,
            stage: stage,
            display_order: 999
        })
    }).then(r => r.json()).then(result => {
        if (result.success) {
            showSuccess('Substage created successfully');
            loadOverview();
        } else {
            showError(result.error || 'Failed to create substage');
        }
    });
}

function showSuccess(message) {
    // Simple alert for now - can be enhanced with toast notifications
    alert('✓ ' + message);
}

function showError(message) {
    alert('✗ ' + message);
}

