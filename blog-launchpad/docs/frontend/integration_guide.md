# Frontend Integration Guide

## Overview

This guide explains how to integrate the Unified Queue System into your frontend pages. The system provides a single API with filtering capabilities that can be used across all pages.

**Target Pages**:
- Daily Product Posts (`/daily-product-posts`)
- Facebook Feed Post (`/syndication/facebook/feed_post`)
- Social Media Command Center (`/social-media-command-center`)

---

## API Integration

### Base API Endpoint
All queue operations use: `/api/queue`

### Common JavaScript Functions

#### Load Queue Data
```javascript
async function loadQueueData(filters = {}) {
    try {
        // Build query string from filters
        const queryParams = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                queryParams.append(key, value);
            }
        });
        
        const response = await fetch(`/api/queue?${queryParams.toString()}`);
        const data = await response.json();
        
        if (data.success) {
            return data.items;
        } else {
            console.error('Error loading queue:', data.error);
            return [];
        }
    } catch (error) {
        console.error('Error loading queue:', error);
        return [];
    }
}
```

#### Add Item to Queue
```javascript
async function addToQueue(itemData) {
    try {
        const response = await fetch('/api/queue', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(itemData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            return { success: true, itemId: data.item_id };
        } else {
            return { success: false, error: data.error };
        }
    } catch (error) {
        return { success: false, error: error.message };
    }
}
```

#### Update Queue Item
```javascript
async function updateQueueItem(itemId, updates) {
    try {
        const response = await fetch(`/api/queue/${itemId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updates)
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        return { success: false, error: error.message };
    }
}
```

#### Delete Queue Item
```javascript
async function deleteQueueItem(itemId) {
    try {
        const response = await fetch(`/api/queue/${itemId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        return { success: false, error: error.message };
    }
}
```

#### Clear Queue
```javascript
async function clearQueue(filters = {}) {
    try {
        const queryParams = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                queryParams.append(key, value);
            }
        });
        
        const response = await fetch(`/api/queue/clear?${queryParams.toString()}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        return { success: false, error: error.message };
    }
}
```

---

## Page-Specific Integration

### Daily Product Posts Page

#### Load Product Items
```javascript
async function loadProductQueue() {
    const items = await loadQueueData({
        content_type: 'product',
        platform: 'facebook',
        channel_type: 'feed_post'
    });
    
    renderProductQueue(items);
}
```

#### Add Product to Queue
```javascript
async function addProductToQueue(productId, content, scheduleData) {
    const itemData = {
        platform: 'facebook',
        channel_type: 'feed_post',
        content_type: 'product',
        product_id: productId,
        generated_content: content,
        scheduled_date: scheduleData.date,
        scheduled_time: scheduleData.time,
        schedule_name: scheduleData.name,
        timezone: scheduleData.timezone,
        status: 'ready'
    };
    
    const result = await addToQueue(itemData);
    
    if (result.success) {
        // Reload queue to show new item
        await loadProductQueue();
        showNotification('Product added to queue successfully!', 'success');
    } else {
        showNotification('Error adding product: ' + result.error, 'error');
    }
}
```

#### Render Product Queue
```javascript
function renderProductQueue(items) {
    const container = document.getElementById('queue-container');
    
    if (items.length === 0) {
        container.innerHTML = '<p>No items in queue</p>';
        return;
    }
    
    let html = '<div class="queue-items">';
    
    items.forEach(item => {
        html += `
            <div class="queue-item" data-id="${item.id}">
                <div class="item-content">
                    <h4>${item.product_name}</h4>
                    <p>${item.generated_content}</p>
                    <div class="item-meta">
                        <span class="status status-${item.status}">${item.status}</span>
                        <span class="scheduled">${formatDateTime(item.scheduled_timestamp)}</span>
                    </div>
                </div>
                <div class="item-actions">
                    <button onclick="editQueueItem(${item.id})">Edit</button>
                    <button onclick="deleteQueueItem(${item.id})">Delete</button>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}
```

### Facebook Feed Post Page

#### Load Blog Post Items
```javascript
async function loadBlogPostQueue() {
    const items = await loadQueueData({
        content_type: 'blog_post',
        platform: 'facebook',
        channel_type: 'feed_post'
    });
    
    renderBlogPostQueue(items);
}
```

#### Add Blog Post to Queue
```javascript
async function addBlogPostToQueue(postId, sectionId, content, scheduleData) {
    const itemData = {
        platform: 'facebook',
        channel_type: 'feed_post',
        content_type: 'blog_post',
        post_id: postId,
        section_id: sectionId,
        generated_content: content,
        scheduled_date: scheduleData.date,
        scheduled_time: scheduleData.time,
        schedule_name: scheduleData.name,
        timezone: scheduleData.timezone,
        status: 'ready'
    };
    
    const result = await addToQueue(itemData);
    
    if (result.success) {
        await loadBlogPostQueue();
        showNotification('Blog post added to queue successfully!', 'success');
    } else {
        showNotification('Error adding blog post: ' + result.error, 'error');
    }
}
```

#### Render Blog Post Queue
```javascript
function renderBlogPostQueue(items) {
    const container = document.getElementById('queue-container');
    
    if (items.length === 0) {
        container.innerHTML = '<p>No blog post items in queue</p>';
        return;
    }
    
    let html = '<div class="queue-items">';
    
    items.forEach(item => {
        html += `
            <div class="queue-item" data-id="${item.id}">
                <div class="item-content">
                    <h4>${item.post_title}</h4>
                    <h5>${item.section_title}</h5>
                    <p>${item.generated_content}</p>
                    <div class="item-meta">
                        <span class="status status-${item.status}">${item.status}</span>
                        <span class="scheduled">${formatDateTime(item.scheduled_timestamp)}</span>
                    </div>
                </div>
                <div class="item-actions">
                    <button onclick="editQueueItem(${item.id})">Edit</button>
                    <button onclick="deleteQueueItem(${item.id})">Delete</button>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}
```

### Social Media Command Center

#### Load All Items with Filtering
```javascript
async function loadUnifiedQueue(filters = {}) {
    const items = await loadQueueData(filters);
    renderUnifiedQueue(items);
}

// Apply filters from UI
function applyFilters() {
    const filters = {
        content_type: document.getElementById('content-type-filter').value,
        platform: document.getElementById('platform-filter').value,
        status: document.getElementById('status-filter').value,
        date_from: document.getElementById('date-from').value,
        date_to: document.getElementById('date-to').value
    };
    
    loadUnifiedQueue(filters);
}
```

#### Render Unified Queue
```javascript
function renderUnifiedQueue(items) {
    const container = document.getElementById('timeline-body');
    
    if (items.length === 0) {
        container.innerHTML = '<tr><td colspan="7">No items found</td></tr>';
        return;
    }
    
    let html = '';
    
    items.forEach(item => {
        const date = new Date(item.scheduled_timestamp);
        const dateStr = date.toLocaleDateString();
        const timeStr = date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        html += `
            <tr data-id="${item.id}">
                <td>
                    <img src="${item.product_image || item.post_image || '/static/images/default-thumb.png'}" 
                         alt="Thumbnail" class="item-thumbnail">
                </td>
                <td>
                    <div class="datetime">
                        <div class="date">${dateStr}</div>
                        <div class="time">${timeStr}</div>
                    </div>
                </td>
                <td>
                    <span class="platform platform-${item.platform}">${item.platform}</span>
                </td>
                <td>
                    <span class="content-type content-type-${item.content_type}">${item.content_type}</span>
                </td>
                <td class="content-preview">
                    <div class="content-title">${item.product_name || item.post_title || 'Untitled'}</div>
                    <div class="content-text">${item.generated_content.substring(0, 100)}...</div>
                </td>
                <td>
                    <span class="status status-${item.status}">${item.status}</span>
                </td>
                <td>
                    <div class="actions">
                        <button onclick="editQueueItem(${item.id})" class="btn-edit">Edit</button>
                        <button onclick="deleteQueueItem(${item.id})" class="btn-delete">Delete</button>
                    </div>
                </td>
            </tr>
        `;
    });
    
    container.innerHTML = html;
}
```

---

## Filtering UI Components

### Filter Controls HTML
```html
<div class="filter-controls">
    <div class="filter-group">
        <label for="content-type-filter">Content Type:</label>
        <select id="content-type-filter">
            <option value="">All Types</option>
            <option value="product">Products</option>
            <option value="blog_post">Blog Posts</option>
            <option value="event">Events</option>
        </select>
    </div>
    
    <div class="filter-group">
        <label for="platform-filter">Platform:</label>
        <select id="platform-filter">
            <option value="">All Platforms</option>
            <option value="facebook">Facebook</option>
            <option value="instagram">Instagram</option>
            <option value="twitter">Twitter</option>
        </select>
    </div>
    
    <div class="filter-group">
        <label for="status-filter">Status:</label>
        <select id="status-filter">
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="ready">Ready</option>
            <option value="published">Published</option>
            <option value="failed">Failed</option>
        </select>
    </div>
    
    <div class="filter-group">
        <label for="date-from">From Date:</label>
        <input type="date" id="date-from">
    </div>
    
    <div class="filter-group">
        <label for="date-to">To Date:</label>
        <input type="date" id="date-to">
    </div>
    
    <div class="filter-group">
        <button onclick="applyFilters()" class="btn-apply">Apply Filters</button>
        <button onclick="clearFilters()" class="btn-clear">Clear</button>
    </div>
</div>
```

### Filter JavaScript
```javascript
function applyFilters() {
    const filters = {
        content_type: document.getElementById('content-type-filter').value,
        platform: document.getElementById('platform-filter').value,
        status: document.getElementById('status-filter').value,
        date_from: document.getElementById('date-from').value,
        date_to: document.getElementById('date-to').value
    };
    
    // Remove empty filters
    Object.keys(filters).forEach(key => {
        if (!filters[key]) {
            delete filters[key];
        }
    });
    
    loadQueueData(filters).then(items => {
        renderQueue(items);
    });
}

function clearFilters() {
    document.getElementById('content-type-filter').value = '';
    document.getElementById('platform-filter').value = '';
    document.getElementById('status-filter').value = '';
    document.getElementById('date-from').value = '';
    document.getElementById('date-to').value = '';
    
    loadQueueData().then(items => {
        renderQueue(items);
    });
}
```

---

## CSS Styling

### Queue Item Styling
```css
.queue-item {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    background: #fff;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.queue-item:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.item-content h4 {
    margin: 0 0 8px 0;
    color: #333;
}

.item-content p {
    margin: 0 0 12px 0;
    color: #666;
    line-height: 1.4;
}

.item-meta {
    display: flex;
    gap: 12px;
    align-items: center;
}

.status {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
}

.status-pending { background: #fef3c7; color: #92400e; }
.status-ready { background: #d1fae5; color: #065f46; }
.status-published { background: #dbeafe; color: #1e40af; }
.status-failed { background: #fee2e2; color: #991b1b; }

.scheduled {
    color: #666;
    font-size: 14px;
}

.item-actions {
    display: flex;
    gap: 8px;
    margin-top: 12px;
}

.item-actions button {
    padding: 6px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    background: #fff;
    cursor: pointer;
    font-size: 14px;
}

.item-actions button:hover {
    background: #f5f5f5;
}
```

### Filter Controls Styling
```css
.filter-controls {
    display: flex;
    gap: 16px;
    align-items: end;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 8px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}

.filter-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.filter-group label {
    font-size: 14px;
    font-weight: 600;
    color: #333;
}

.filter-group select,
.filter-group input {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

.btn-apply,
.btn-clear {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
}

.btn-apply {
    background: #007bff;
    color: white;
}

.btn-apply:hover {
    background: #0056b3;
}

.btn-clear {
    background: #6c757d;
    color: white;
}

.btn-clear:hover {
    background: #545b62;
}
```

---

## Error Handling

### Global Error Handler
```javascript
function handleApiError(error, context = '') {
    console.error(`API Error ${context}:`, error);
    
    let message = 'An error occurred';
    
    if (error.error) {
        message = error.error;
    } else if (error.message) {
        message = error.message;
    }
    
    showNotification(message, 'error');
}

// Usage in API calls
async function loadQueueData(filters = {}) {
    try {
        // ... API call
    } catch (error) {
        handleApiError(error, 'loading queue data');
        return [];
    }
}
```

### User-Friendly Notifications
```javascript
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}
```

---

## Performance Optimization

### Debounced Filtering
```javascript
let filterTimeout;

function applyFiltersDebounced() {
    clearTimeout(filterTimeout);
    filterTimeout = setTimeout(() => {
        applyFilters();
    }, 300);
}

// Use on input change
document.getElementById('content-type-filter').addEventListener('change', applyFiltersDebounced);
```

### Pagination
```javascript
let currentPage = 0;
const pageSize = 20;

async function loadQueueDataPaginated(filters = {}) {
    const items = await loadQueueData({
        ...filters,
        limit: pageSize,
        offset: currentPage * pageSize
    });
    
    return items;
}

function nextPage() {
    currentPage++;
    loadQueueDataPaginated(currentFilters).then(renderQueue);
}

function previousPage() {
    if (currentPage > 0) {
        currentPage--;
        loadQueueDataPaginated(currentFilters).then(renderQueue);
    }
}
```

---

## Testing

### Unit Tests
```javascript
// Test API functions
describe('Queue API', () => {
    test('loadQueueData returns items', async () => {
        const items = await loadQueueData({ content_type: 'product' });
        expect(Array.isArray(items)).toBe(true);
    });
    
    test('addToQueue creates new item', async () => {
        const result = await addToQueue({
            platform: 'facebook',
            channel_type: 'feed_post',
            content_type: 'product',
            product_id: 123,
            generated_content: 'Test content'
        });
        
        expect(result.success).toBe(true);
        expect(result.itemId).toBeDefined();
    });
});
```

### Integration Tests
```javascript
// Test page integration
describe('Daily Product Posts Integration', () => {
    test('loads product items on page load', async () => {
        await loadProductQueue();
        const items = document.querySelectorAll('.queue-item');
        expect(items.length).toBeGreaterThan(0);
    });
});
```

---

*This integration guide is maintained by the Blog Launchpad development team. Last updated: 2025-01-27*
