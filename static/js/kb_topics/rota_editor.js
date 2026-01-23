/**
 * KB Topic Rota Editor
 * Drag-and-drop interface for managing weekly topic schedule
 */

class RotaEditor {
    constructor() {
        this.topics = [];
        this.parentGroups = {};
        this.rota = {};
        this.similarityMap = {};
        this.currentYear = new Date().getFullYear();
        this.startDate = null;
        this.colors = this.generateColors(20);
        
        this.init();
    }
    
    generateColors(count) {
        const colors = [];
        const hueStep = 360 / count;
        for (let i = 0; i < count; i++) {
            const hue = i * hueStep;
            colors.push(`hsl(${hue}, 70%, 50%)`);
        }
        return colors;
    }
    
    async init() {
        await this.loadData();
        this.renderTopicLibrary();
        this.renderTimeline();
        this.setupEventListeners();
        this.updateStats();
    }
    
    async loadData() {
        try {
            const response = await fetch('/api/kb-topics/rota-editor/data');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${await response.text()}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to load data');
            }
            
            this.topics = data.topics || [];
            this.parentGroups = data.parent_groups || {};
            this.rota = data.rota || {};
            this.similarityMap = data.similarity_map || {};
            
            // Calculate start date (next Monday)
            const today = new Date();
            const daysUntilMonday = (7 - today.getDay() + 1) % 7 || 7;
            this.startDate = new Date(today);
            this.startDate.setDate(today.getDate() + daysUntilMonday);
            
            console.log(`Loaded ${this.topics.length} topics, ${Object.keys(this.rota).length} rota entries`);
            
        } catch (error) {
            console.error('Error loading data:', error);
            this.showStatus('Error loading data: ' + error.message, 'error');
            alert('Failed to load data: ' + error.message);
        }
    }
    
    renderTopicLibrary() {
        const tree = document.getElementById('topic-tree');
        tree.innerHTML = '';
        
            // Group topics by parent
            const groups = {};
            const parentTopics = this.topics.filter(t => t.level === 1);
            
            parentTopics.forEach(parent => {
                groups[parent.id] = {
                    parent: parent,
                    children: this.topics.filter(t => t.parent_id === parent.id)
                };
            });
            
            // Also include Level 1 topics that don't have children as their own group
            this.topics.forEach(topic => {
                if (topic.level === 1 && !groups[topic.id]) {
                    groups[topic.id] = {
                        parent: topic,
                        children: []
                    };
                }
            });
        
        // Render groups
        Object.values(groups).forEach((group, index) => {
            const parent = group.parent;
            const color = this.colors[index % this.colors.length];
            
            const groupDiv = document.createElement('div');
            groupDiv.className = 'parent-group';
            groupDiv.dataset.parentId = parent.id;
            
            const header = document.createElement('div');
            header.className = 'parent-group-header expanded';
            const childCount = group.children.length;
            header.innerHTML = `
                <span style="color: ${color}">●</span>
                <span style="flex: 1; margin-left: 0.5rem;">${parent.name}</span>
                <span style="font-size: 0.75rem; color: var(--color-text-light);">
                    ${childCount > 0 ? `(${childCount} sub-topics)` : '(no sub-topics)'}
                </span>
            `;
            header.onclick = () => this.toggleGroup(groupDiv);
            
            const childrenDiv = document.createElement('div');
            childrenDiv.className = 'parent-group-children';
            
            // Add parent topic (Level 1)
            const parentCard = this.createTopicCard(parent, color);
            childrenDiv.appendChild(parentCard);
            
            // Add child topics (Level 2)
            group.children.forEach(child => {
                const childCard = this.createTopicCard(child, color);
                childrenDiv.appendChild(childCard);
            });
            
            groupDiv.appendChild(header);
            groupDiv.appendChild(childrenDiv);
            tree.appendChild(groupDiv);
        });
    }
    
    createTopicCard(topic, parentColor) {
        const template = document.getElementById('topic-card-template');
        const card = template.content.cloneNode(true).querySelector('.topic-card');
        
        card.dataset.topicId = topic.id;
        card.dataset.parentId = topic.parent_id || topic.id;
        card.dataset.parentColor = parentColor;
        
        card.querySelector('.topic-level-badge').textContent = `L${topic.level}`;
        card.querySelector('.topic-level-badge').dataset.level = topic.level;
        card.querySelector('.topic-type-badge').textContent = topic.type;
        card.querySelector('.topic-type-badge').dataset.type = topic.type;
        card.querySelector('.topic-name').textContent = topic.name;
        card.querySelector('.article-count').textContent = topic.article_count;
        card.querySelector('.parent-indicator').style.background = parentColor;
        
        // Setup drag
        card.draggable = true;
        card.addEventListener('dragstart', (e) => this.handleDragStart(e, topic));
        card.addEventListener('dragend', (e) => this.handleDragEnd(e));
        
        return card;
    }
    
    renderTimeline() {
        const container = document.getElementById('timeline-container');
        container.innerHTML = '';
        
        const scrollDiv = document.createElement('div');
        scrollDiv.className = 'timeline-scroll';
        
        // Generate 144 weeks (2.8 years)
        for (let week = 1; week <= 144; week++) {
            const weekDate = new Date(this.startDate);
            weekDate.setDate(this.startDate.getDate() + (week - 1) * 7);
            
            const year = weekDate.getFullYear();
            const isoWeek = this.getISOWeek(weekDate);
            const weekKey = `${year}_W${isoWeek}`;
            
            const weekColumn = this.createWeekColumn(week, year, isoWeek, weekDate, weekKey);
            scrollDiv.appendChild(weekColumn);
        }
        
        container.appendChild(scrollDiv);
    }
    
    createWeekColumn(weekNum, year, isoWeek, date, weekKey) {
        const template = document.getElementById('week-column-template');
        const column = template.content.cloneNode(true).querySelector('.week-column');
        
        column.dataset.week = weekNum;
        column.dataset.year = year;
        column.dataset.isoWeek = isoWeek;
        column.dataset.weekKey = weekKey;
        
        column.querySelector('.week-num').textContent = weekNum;
        column.querySelector('.week-date').textContent = this.formatDate(date);
        
        const content = column.querySelector('.week-content');
        const rotaEntry = this.rota[weekKey];
        
        if (rotaEntry && rotaEntry.length > 0) {
            const topic = rotaEntry[0];
            const topicData = this.topics.find(t => t.id === topic.topic_id);
            if (topicData) {
                // Find parent topic to get color
                const parentId = topicData.parent_id || topicData.id;
                // Find the Level 1 parent topic
                const parentTopic = this.topics.find(t => t.id === parentId && t.level === 1) || 
                                   this.topics.find(t => t.id === parentId);
                const allLevel1Topics = this.topics.filter(t => t.level === 1).sort((a, b) => a.id - b.id);
                const parentIndex = allLevel1Topics.findIndex(t => t.id === parentId);
                const colorIndex = parentIndex >= 0 ? parentIndex % this.colors.length : 0;
                const color = this.colors[colorIndex];
                
                const card = this.createTopicCard(topicData, color);
                card.draggable = true;
                content.innerHTML = '';
                content.appendChild(card);
            } else {
                console.warn(`Topic ${topic.topic_id} not found in topics list`);
                content.innerHTML = '<div class="week-placeholder">Topic not found</div>';
            }
        } else {
            // Ensure placeholder is shown
            if (!content.querySelector('.week-placeholder')) {
                content.innerHTML = '<div class="week-placeholder">Drop topic here</div>';
            }
        }
        
        // Setup drop zone
        content.addEventListener('dragover', (e) => this.handleDragOver(e));
        content.addEventListener('drop', (e) => this.handleDrop(e, weekKey, year, isoWeek, date));
        content.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        
        return column;
    }
    
    handleDragStart(e, topic) {
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('topic-id', topic.id);
        e.dataTransfer.setData('topic-data', JSON.stringify(topic));
        e.currentTarget.classList.add('dragging');
    }
    
    handleDragEnd(e) {
        e.currentTarget.classList.remove('dragging');
        document.querySelectorAll('.drag-over, .drag-invalid').forEach(el => {
            el.classList.remove('drag-over', 'drag-invalid');
        });
    }
    
    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        
        const dropZone = e.currentTarget;
        const topicId = parseInt(e.dataTransfer.getData('topic-id'));
        
        if (!topicId) return;
        
        // Validate placement
        const weekKey = dropZone.closest('.week-column').dataset.weekKey;
        const week = parseInt(dropZone.closest('.week-column').dataset.week);
        const year = parseInt(dropZone.closest('.week-column').dataset.year);
        
        const isValid = this.validatePlacement(topicId, week, year);
        
        if (isValid) {
            dropZone.classList.add('drag-over');
            dropZone.classList.remove('drag-invalid');
        } else {
            dropZone.classList.add('drag-invalid');
            dropZone.classList.remove('drag-over');
        }
    }
    
    handleDragLeave(e) {
        e.currentTarget.classList.remove('drag-over', 'drag-invalid');
    }
    
    async handleDrop(e, weekKey, year, isoWeek, date) {
        e.preventDefault();
        const dropZone = e.currentTarget;
        dropZone.classList.remove('drag-over', 'drag-invalid');
        
        const topicId = parseInt(e.dataTransfer.getData('topic-id'));
        const topicData = JSON.parse(e.dataTransfer.getData('topic-data'));
        
        if (!topicId) return;
        
        // Remove from old location if exists
        document.querySelectorAll('.week-content').forEach(weekContent => {
            const card = weekContent.querySelector(`[data-topic-id="${topicId}"]`);
            if (card && weekContent !== dropZone) {
                weekContent.innerHTML = '<div class="week-placeholder">Drop topic here</div>';
            }
        });
        
        // Add to new location
        const parentId = topicData.parent_id || topicData.id;
        const parentGroup = Object.keys(this.parentGroups).find(id => 
            this.parentGroups[id].some(t => (t.parent_id || t.id) == parentId)
        );
        const colorIndex = parseInt(parentGroup) % this.colors.length;
        const color = this.colors[colorIndex];
        
        const card = this.createTopicCard(topicData, color);
        card.draggable = true;
        dropZone.innerHTML = '';
        dropZone.appendChild(card);
        
        // Update rota data
        this.rota[weekKey] = [{
            topic_id: topicId,
            year: year,
            week: isoWeek,
            date: date.toISOString().split('T')[0]
        }];
        
        this.updateStats();
        this.showStatus(`Topic scheduled for week ${isoWeek}`, 'success');
    }
    
    validatePlacement(topicId, week, year) {
        const topic = this.topics.find(t => t.id === topicId);
        if (!topic) return false;
        
        const topicParent = topic.parent_id || topic.id;
        
        // Check adjacent weeks
        for (let w = Math.max(1, week - 1); w <= Math.min(144, week + 1); w++) {
            if (w === week) continue;
            
            const weekDate = new Date(this.startDate);
            weekDate.setDate(this.startDate.getDate() + (w - 1) * 7);
            const checkYear = weekDate.getFullYear();
            const checkIsoWeek = this.getISOWeek(weekDate);
            const checkKey = `${checkYear}_W${checkIsoWeek}`;
            
            const entry = this.rota[checkKey];
            if (entry && entry.length > 0) {
                const existingTopic = this.topics.find(t => t.id === entry[0].topic_id);
                if (existingTopic) {
                    const existingParent = existingTopic.parent_id || existingTopic.id;
                    if (existingParent === topicParent) {
                        return false; // Same parent in adjacent week
                    }
                }
            }
        }
        
        return true;
    }
    
    toggleGroup(groupDiv) {
        const header = groupDiv.querySelector('.parent-group-header');
        const children = groupDiv.querySelector('.parent-group-children');
        
        header.classList.toggle('expanded');
        header.classList.toggle('collapsed');
        children.classList.toggle('collapsed');
    }
    
    setupEventListeners() {
        // Search
        document.getElementById('topic-search').addEventListener('input', (e) => {
            this.filterTopics(e.target.value);
        });
        
        // Filter by type
        document.getElementById('topic-filter-type').addEventListener('change', (e) => {
            this.filterByType(e.target.value);
        });
        
        // Auto-arrange
        document.getElementById('btn-auto-arrange').addEventListener('click', () => {
            this.autoArrange();
        });
        
        // Save draft
        document.getElementById('btn-save-draft').addEventListener('click', () => {
            this.saveDraft();
        });
        
        // Apply to schedule
        document.getElementById('btn-apply').addEventListener('click', () => {
            this.applyToSchedule();
        });
        
        // Jump to week
        document.getElementById('btn-jump').addEventListener('click', () => {
            this.jumpToWeek();
        });
    }
    
    filterTopics(searchTerm) {
        const term = searchTerm.toLowerCase();
        document.querySelectorAll('.topic-card').forEach(card => {
            const name = card.querySelector('.topic-name').textContent.toLowerCase();
            if (name.includes(term)) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    }
    
    filterByType(type) {
        document.querySelectorAll('.topic-card').forEach(card => {
            const cardType = card.querySelector('.topic-type-badge').dataset.type;
            if (!type || cardType === type) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    }
    
    async autoArrange() {
        if (!confirm('This will regenerate the entire rota with all topics. This may take a moment. Continue?')) {
            return;
        }
        
        this.showStatus('Generating auto-arrangement...', 'info');
        const btn = document.getElementById('btn-auto-arrange');
        const originalText = btn.textContent;
        btn.disabled = true;
        btn.textContent = 'Generating...';
        
        try {
            const startDateStr = this.startDate.toISOString().split('T')[0];
            console.log('Auto-arrange request:', { start_date: startDateStr, weeks: null, include_all_topics: true });
            
            const response = await fetch('/api/kb-topics/regenerate-rota', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    start_date: startDateStr,
                    weeks: null,
                    include_all_topics: true
                })
            });
            
            console.log('Response status:', response.status, response.statusText);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Error response:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            const data = await response.json();
            console.log('Auto-arrange response:', data);
            
            if (data.success) {
                this.showStatus('Reloading data...', 'info');
                // Small delay to ensure database is updated
                await new Promise(resolve => setTimeout(resolve, 500));
                // Reload all data
                await this.loadData();
                // Re-render everything
                this.renderTopicLibrary();
                this.renderTimeline();
                this.updateStats();
                const message = data.message || `${data.rota_entries || 0} entries generated`;
                this.showStatus(`Auto-arrangement complete: ${message}`, 'success');
            } else {
                throw new Error(data.error || data.message || 'Auto-arrangement failed');
            }
        } catch (error) {
            console.error('Auto-arrange error:', error);
            this.showStatus('Error: ' + error.message, 'error');
            alert('Auto-arrange failed: ' + error.message + '\n\nCheck browser console for details.');
        } finally {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }
    
    async saveDraft() {
        const rotaData = this.collectRotaData();
        
        try {
            const response = await fetch('/api/kb-topics/rota-editor/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    rota: rotaData,
                    validate: false
                })
            });
            
            const data = await response.json();
            if (data.success) {
                this.showStatus('Draft saved', 'success');
            } else {
                throw new Error(data.error || 'Save failed');
            }
        } catch (error) {
            this.showStatus('Error: ' + error.message, 'error');
        }
    }
    
    async applyToSchedule() {
        if (!confirm('Apply this arrangement to the schedule? This will update the database.')) {
            return;
        }
        
        const rotaData = this.collectRotaData();
        
        try {
            const response = await fetch('/api/kb-topics/rota-editor/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    rota: rotaData,
                    validate: true
                })
            });
            
            const data = await response.json();
            if (data.success) {
                if (data.warnings && data.warnings.length > 0) {
                    const warningText = data.warnings.map(w => w.message || JSON.stringify(w)).join('\n');
                    alert('Applied with warnings:\n' + warningText);
                }
                this.showStatus('Schedule applied successfully', 'success');
            } else {
                throw new Error(data.error || 'Apply failed');
            }
        } catch (error) {
            this.showStatus('Error: ' + error.message, 'error');
        }
    }
    
    collectRotaData() {
        const rotaData = [];
        
        document.querySelectorAll('.week-column').forEach(column => {
            const week = parseInt(column.dataset.week);
            const year = parseInt(column.dataset.year);
            const isoWeek = parseInt(column.dataset.isoWeek);
            const weekKey = column.dataset.weekKey;
            
            const card = column.querySelector('.topic-card');
            if (card) {
                const topicId = parseInt(card.dataset.topicId);
                const weekDate = new Date(this.startDate);
                weekDate.setDate(this.startDate.getDate() + (week - 1) * 7);
                
                rotaData.push({
                    topic_id: topicId,
                    year: year,
                    week: isoWeek,
                    date: weekDate.toISOString().split('T')[0],
                    status: 'scheduled'
                });
            }
        });
        
        return rotaData;
    }
    
    jumpToWeek() {
        const weekNum = parseInt(document.getElementById('jump-to-week').value);
        if (weekNum >= 1 && weekNum <= 144) {
            const column = document.querySelector(`[data-week="${weekNum}"]`);
            if (column) {
                column.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
            }
        }
    }
    
    updateStats() {
        const scheduled = document.querySelectorAll('.week-content .topic-card').length;
        const total = this.topics.length;
        const unscheduled = total - scheduled;
        
        document.getElementById('stats-topics').textContent = `${total} topics`;
        document.getElementById('stats-scheduled').textContent = `${scheduled} scheduled`;
        document.getElementById('stats-unscheduled').textContent = `${unscheduled} unscheduled`;
    }
    
    showStatus(message, type = 'info') {
        const statusText = document.getElementById('status-text');
        statusText.textContent = message;
        statusText.className = `status-${type}`;
        
        setTimeout(() => {
            statusText.textContent = 'Ready';
            statusText.className = '';
        }, 3000);
    }
    
    getISOWeek(date) {
        const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
        const dayNum = d.getUTCDay() || 7;
        d.setUTCDate(d.getUTCDate() + 4 - dayNum);
        const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
        return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
    }
    
    formatDate(date) {
        return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new RotaEditor();
});
