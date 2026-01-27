/**
 * Content Control Board
 * 
 * Read-only planning surface for role-driven social posting.
 */

// Global reference for onclick handlers
let controlBoard;

class ContentControlBoard {
    constructor() {
        this.currentYear = null;
        this.currentWeek = null;
        this.weekData = null;
        this.viewMode = 'day'; // 'day' or 'role'
        
        // Set global reference
        controlBoard = this;
        
        this.init();
    }
    
    init() {
        // Get initial year/week from URL or use current
        const urlParams = new URLSearchParams(window.location.search);
        this.currentYear = parseInt(urlParams.get('year')) || new Date().getFullYear();
        this.currentWeek = parseInt(urlParams.get('week')) || this.getISOWeek(new Date());
        
        // Set week inputs
        document.getElementById('week-year').value = this.currentYear;
        document.getElementById('week-number').value = this.currentWeek;
        
        // Event listeners
        document.getElementById('btn-load-week').addEventListener('click', () => this.loadWeek());
        document.getElementById('btn-prev-week').addEventListener('click', () => this.navigateWeek(-1));
        document.getElementById('btn-next-week').addEventListener('click', () => this.navigateWeek(1));
        document.getElementById('btn-current-week').addEventListener('click', () => this.jumpToCurrentWeek());
        document.getElementById('btn-view-day').addEventListener('click', () => this.switchView('day'));
        document.getElementById('btn-view-role').addEventListener('click', () => this.switchView('role'));
        document.getElementById('btn-close-panel').addEventListener('click', () => this.closePanel());
        
        // Load initial data
        this.loadWeek();
        this.loadSundayPlanning();
    }
    
    getISOWeek(date) {
        const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
        const dayNum = d.getUTCDay() || 7;
        d.setUTCDate(d.getUTCDate() + 4 - dayNum);
        const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
        return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
    }
    
    async loadWeek() {
        const year = parseInt(document.getElementById('week-year').value);
        const week = parseInt(document.getElementById('week-number').value);
        
        if (!year || !week) {
            alert('Please enter valid year and week');
            return;
        }
        
        this.currentYear = year;
        this.currentWeek = week;
        
        try {
            const response = await fetch(`/api/planning/content-control-board/week-data?year=${year}&week=${week}`);
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to load week data');
            }
            
            this.weekData = data;
            this.render();
            
        } catch (error) {
            console.error('Error loading week data:', error);
            alert('Error loading week data: ' + error.message);
        }
    }
    
    render() {
        if (!this.weekData) return;
        
        // Update active topic
        this.renderTopicInfo();
        
        // Render based on view mode
        if (this.viewMode === 'day') {
            this.renderDayView();
        } else {
            this.renderRoleView();
        }
    }
    
    navigateWeek(delta) {
        let newWeek = this.currentWeek + delta;
        let newYear = this.currentYear;
        
        if (newWeek < 1) {
            newWeek = 52;
            newYear -= 1;
        } else if (newWeek > 52) {
            newWeek = 1;
            newYear += 1;
        }
        
        document.getElementById('week-year').value = newYear;
        document.getElementById('week-number').value = newWeek;
        this.loadWeek();
    }
    
    jumpToCurrentWeek() {
        const today = new Date();
        const year = today.getFullYear();
        const week = this.getISOWeek(today);
        
        document.getElementById('week-year').value = year;
        document.getElementById('week-number').value = week;
        this.loadWeek();
    }
    
    async loadSundayPlanning() {
        try {
            const today = new Date();
            const currentYear = today.getFullYear();
            const currentWeek = this.getISOWeek(today);
            
            // Load next 6 Sundays
            const sundaySlots = [];
            for (let i = 0; i < 6; i++) {
                const weekOffset = i;
                let year = currentYear;
                let week = currentWeek + weekOffset;
                
                // Handle year rollover
                if (week > 52) {
                    week = week - 52;
                    year += 1;
                }
                
                // Get Sunday date for this week
                const sundayDate = this.getSundayDate(year, week);
                
                // Load week data for this Sunday
                try {
                    const response = await fetch(`/api/planning/content-control-board/week-data?year=${year}&week=${week}`);
                    const data = await response.json();
                    
                    if (data.success) {
                        // Find Sunday slot (day 6 in 0-indexed, day 7 in ISO)
                        const sundaySlot = data.schedule.find(s => s.day === 6 && s.role === 'DEPTH_LONG');
                        const post = sundaySlot && sundaySlot.posts && sundaySlot.posts.length > 0 ? sundaySlot.posts[0] : null;
                        
                        sundaySlots.push({
                            year: year,
                            week: week,
                            date: sundayDate,
                            slot: sundaySlot,
                            post: post,
                            topic: data.active_topic
                        });
                    }
                } catch (error) {
                    console.error(`Error loading week ${year}-W${week}:`, error);
                    // Add placeholder slot
                    sundaySlots.push({
                        year: year,
                        week: week,
                        date: sundayDate,
                        slot: null,
                        post: null,
                        topic: null
                    });
                }
            }
            
            this.renderSundayPlanning(sundaySlots);
            
        } catch (error) {
            console.error('Error loading Sunday planning:', error);
        }
    }
    
    getSundayDate(year, week) {
        // Get first day of ISO week (Monday)
        const jan4 = new Date(year, 0, 4);
        const jan4Day = jan4.getDay() || 7; // Convert 0 (Sunday) to 7
        const weekStart = new Date(year, 0, 4 - jan4Day + 1);
        weekStart.setDate(weekStart.getDate() + (week - 1) * 7);
        
        // Sunday is 6 days after Monday
        const sunday = new Date(weekStart);
        sunday.setDate(sunday.getDate() + 6);
        
        return sunday;
    }
    
    renderSundayPlanning(sundaySlots) {
        const grid = document.getElementById('sunday-slots-grid');
        if (!grid) return;
        
        grid.innerHTML = '';
        
        sundaySlots.forEach(slot => {
            const card = document.createElement('div');
            card.className = 'sunday-slot-card';
            
            const hasPost = slot.post !== null;
            const hasTopic = slot.topic !== null;
            const status = hasPost ? slot.post.status : 'empty';
            const statusClass = this.getStatusClass(status);
            
            card.innerHTML = `
                <div class="sunday-slot-header">
                    <div class="sunday-date">
                        <div class="sunday-date-main">${slot.date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}</div>
                        <div class="sunday-date-week">Week ${slot.week}, ${slot.year}</div>
                    </div>
                    <div class="sunday-status ${statusClass}">
                        <span class="status-indicator ${statusClass}"></span>
                        <span class="status-text">${this.getStatusDisplayName(status)}</span>
                    </div>
                </div>
                <div class="sunday-slot-content">
                    ${hasTopic ? `
                        <div class="sunday-topic">
                            <strong>Topic:</strong> ${slot.topic.topic_name || 'No topic name'}
                        </div>
                    ` : `
                        <div class="sunday-topic no-topic">
                            <em>No topic selected</em>
                        </div>
                    `}
                    ${hasPost ? `
                        <div class="sunday-post-preview">
                            <div class="preview-text">${slot.post.preview || 'No preview'}</div>
                        </div>
                    ` : `
                        <div class="sunday-post-preview empty">
                            <em>No post generated</em>
                        </div>
                    `}
                </div>
                <div class="sunday-slot-actions">
                    <button class="btn btn-sm btn-primary" onclick="controlBoard.loadWeekForSunday(${slot.year}, ${slot.week})">
                        View Week
                    </button>
                    ${hasPost ? `
                        <button class="btn btn-sm btn-secondary" onclick="controlBoard.showPostDetails(${slot.post.id})">
                            View Post
                        </button>
                    <button class="btn btn-sm btn-primary" onclick="window.open('/preview/post/${slot.post.id}?channel=facebook', '_blank', 'noopener')">
                        <i class="fas fa-eye"></i> Preview
                    </button>
                    ` : ''}
                </div>
            `;
            
            grid.appendChild(card);
        });
    }
    
    getStatusClass(status) {
        const statusMap = {
            'empty': 'empty',
            'generated': 'generated',
            'validation_failed': 'failed',
            'approved': 'approved',
            'scheduled': 'scheduled',
            'published': 'published'
        };
        return statusMap[status] || 'empty';
    }
    
    loadWeekForSunday(year, week) {
        document.getElementById('week-year').value = year;
        document.getElementById('week-number').value = week;
        this.loadWeek();
        
        // Scroll to matrix view
        document.getElementById('day-view').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    renderTopicInfo() {
        const topicInfo = document.getElementById('topic-info');
        const topicName = document.getElementById('topic-name');
        const topicSource = document.getElementById('topic-source');
        
        if (this.weekData.active_topic) {
            const topic = this.weekData.active_topic;
            topicName.textContent = topic.topic_name || 'No topic name';
            topicSource.textContent = `KB Cluster (${topic.article_count} articles)`;
            topicInfo.style.display = 'flex';
        } else {
            topicInfo.style.display = 'none';
        }
    }
    
    renderDayView() {
        const matrixBody = document.getElementById('matrix-body');
        if (!matrixBody) {
            console.error('Matrix body element not found');
            return;
        }
        
        matrixBody.innerHTML = '';
        
        const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        
        // Build schedule map by day
        const scheduleByDay = {};
        if (this.weekData.schedule) {
            this.weekData.schedule.forEach(slot => {
                if (!scheduleByDay[slot.day]) {
                    scheduleByDay[slot.day] = [];
                }
                scheduleByDay[slot.day].push(slot);
            });
        }
        
        console.log('Schedule by day:', scheduleByDay);
        
        // Create rows for each day
        for (let dayNum = 0; dayNum < 7; dayNum++) {
            const row = document.createElement('tr');
            
            // Day header
            const dayCell = document.createElement('td');
            dayCell.className = 'day-cell';
            dayCell.textContent = days[dayNum];
            row.appendChild(dayCell);
            
            // Facebook cell (only active channel in v1)
            const facebookCell = document.createElement('td');
            facebookCell.className = 'matrix-cell';
            
            const daySlots = scheduleByDay[dayNum] || [];
            const facebookSlot = daySlots.find(s => s.platform === 'facebook');
            
            if (facebookSlot) {
                // Check for conflicts
                if (facebookSlot.has_conflict && facebookSlot.conflicts && facebookSlot.conflicts.length > 0) {
                    facebookCell.className += ' has-conflict';
                    facebookCell.innerHTML = this.renderConflictCell(facebookSlot);
                    facebookCell.addEventListener('click', () => this.showConflictDetails(facebookSlot));
                } else if (facebookSlot.posts && facebookSlot.posts.length > 0) {
                    const post = facebookSlot.posts[0]; // Take first post if multiple
                    facebookCell.className += ' has-post';
                    facebookCell.innerHTML = this.renderCellContent(post, facebookSlot);
                    facebookCell.addEventListener('click', () => this.showPostDetails(post.id));
                } else {
                    facebookCell.className += ' empty';
                    facebookCell.innerHTML = this.renderEmptyCell(facebookSlot);
                }
            } else {
                // No rail configured for this day yet (v1 only has Sunday)
                facebookCell.className += ' empty';
                facebookCell.innerHTML = '<div class="empty-slot"><div class="empty-message">Slot not yet configured</div></div>';
            }
            
            row.appendChild(facebookCell);
            
            // Placeholder cells for other channels
            for (let i = 0; i < 3; i++) {
                const placeholderCell = document.createElement('td');
                placeholderCell.className = 'matrix-cell disabled';
                placeholderCell.innerHTML = '<div class="empty-slot">Coming Soon</div>';
                row.appendChild(placeholderCell);
            }
            
            matrixBody.appendChild(row);
        }
        
        // Show day view, hide role view
        document.getElementById('day-view').style.display = 'block';
        document.getElementById('role-view').style.display = 'none';
    }
    
    renderCellContent(post, slot) {
        const roleClass = post.role ? post.role.toLowerCase().replace('_', '-') : 'legacy';
        const statusClass = post.status || 'empty';
        const roleInfo = this.getRoleInfo(post.role);
        const roleDisplayName = this.getRoleDisplayName(post.role || 'LEGACY');
        
        // v1.1: Make role badge clickable (link to Roles Reference)
        const roleBadgeHtml = post.role ? `
            <a href="/planning/content-roles#${post.role.toLowerCase()}" class="role-badge-link" onclick="event.stopPropagation();">
                <div class="role-badge ${roleClass}" title="${roleInfo.tooltip}">${roleDisplayName}</div>
            </a>
        ` : `
            <div class="role-badge ${roleClass}" title="${roleInfo.tooltip}">${roleDisplayName}</div>
        `;
        
        return `
            <div class="cell-content">
                ${roleBadgeHtml}
                <div class="status-line">
                    <span class="status-indicator ${statusClass}"></span>
                    <span class="status-text">${this.getStatusDisplayName(post.status)}</span>
                </div>
                <div class="post-time">${slot.time || ''}</div>
                <div class="post-preview">${post.preview || 'No preview'}</div>
            </div>
        `;
    }
    
    renderEmptyCell(slot) {
        if (!slot || !slot.role) {
            return '<div class="cell-content empty"><div class="empty-message">No slot configured</div></div>';
        }
        
        const roleClass = slot.role.toLowerCase().replace('_', '-');
        const roleInfo = this.getRoleInfo(slot.role);
        const roleDisplayName = this.getRoleDisplayName(slot.role);
        
        // v1.1: Make role badge clickable (link to Roles Reference)
        return `
            <div class="cell-content empty">
                <a href="/planning/content-roles#${slot.role.toLowerCase()}" class="role-badge-link" onclick="event.stopPropagation();">
                    <div class="role-badge ${roleClass}" title="${roleInfo.tooltip}">
                        ${roleDisplayName}
                    </div>
                </a>
                <div class="post-time">${slot.time || ''}</div>
                <div class="empty-message">No post generated</div>
            </div>
        `;
    }
    
    renderConflictCell(slot) {
        const roleClass = slot.role.toLowerCase().replace('_', '-');
        const roleInfo = this.getRoleInfo(slot.role);
        const roleDisplayName = this.getRoleDisplayName(slot.role);
        const conflict = slot.conflicts[0]; // Show first conflict
        
        return `
            <div class="cell-content conflict">
                <a href="/planning/content-roles#${slot.role.toLowerCase()}" class="role-badge-link" onclick="event.stopPropagation();">
                    <div class="role-badge ${roleClass}" title="${roleInfo.tooltip}">
                        ${roleDisplayName}
                    </div>
                </a>
                <div class="conflict-warning">
                    <span class="conflict-icon">⚠️</span>
                    <span class="conflict-text">Conflict: ${conflict.content_type} post scheduled</span>
                </div>
                <div class="post-time">${slot.time || ''}</div>
                <div class="empty-message">Reserved for ${roleDisplayName}</div>
            </div>
        `;
    }
    
    showConflictDetails(slot) {
        const panelContent = document.getElementById('panel-content');
        const panelTitle = document.getElementById('panel-title');
        
        panelTitle.textContent = `Conflict: ${slot.day_name} ${slot.time}`;
        
        const roleClass = slot.role.toLowerCase().replace('_', '-');
        const roleDisplayName = this.getRoleDisplayName(slot.role);
        
        let conflictsHtml = '';
        slot.conflicts.forEach(conflict => {
            conflictsHtml += `
                <div class="conflict-item" style="border: 1px solid #ef4444; padding: 1rem; margin-bottom: 1rem; border-radius: 4px; background: #fef2f2;">
                    <h5 style="color: #dc2626; margin-top: 0;">Conflicting Post #${conflict.id}</h5>
                    <p><strong>Type:</strong> ${conflict.content_type}</p>
                    <p><strong>Status:</strong> ${this.getStatusDisplayName(conflict.status)}</p>
                    <p><strong>Scheduled:</strong> ${conflict.scheduled_date} ${conflict.scheduled_time || ''}</p>
                    ${conflict.product_name ? `<p><strong>Product:</strong> ${conflict.product_name}</p>` : ''}
                    ${conflict.idea_title ? `<p><strong>Idea:</strong> ${conflict.idea_title}</p>` : ''}
                    <p style="color: #dc2626; font-weight: 600; margin-top: 0.5rem;">${conflict.conflict_reason || 'This post conflicts with the Content Roles Framework.'}</p>
                </div>
            `;
        });
        
        panelContent.innerHTML = `
            <div class="panel-section">
                <h4>Conflict Detected</h4>
                <div style="background: #fef2f2; border: 2px solid #ef4444; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">
                    <p style="color: #dc2626; font-weight: 600; margin: 0;">
                        ⚠️ This slot is reserved for <strong>${roleDisplayName}</strong> posts per the Content Roles Framework.
                    </p>
                    <p style="margin-top: 0.5rem; margin-bottom: 0;">
                        Legacy posts scheduled for this slot conflict with the framework and should be rescheduled or removed.
                    </p>
                </div>
            </div>
            
            <div class="panel-section">
                <h4>Reserved Slot</h4>
                <div>
                    <p><strong>Day:</strong> ${slot.day_name}</p>
                    <p><strong>Time:</strong> ${slot.time}</p>
                    <p><strong>Role:</strong> <span class="role-badge ${roleClass}">${roleDisplayName}</span></p>
                    <p style="margin-top: 0.5rem;">
                        <a href="/planning/content-roles#${slot.role.toLowerCase()}" style="color: var(--color-primary, #2563eb); text-decoration: underline;">
                            Learn about ${roleDisplayName} →
                        </a>
                    </p>
                </div>
            </div>
            
            <div class="panel-section">
                <h4>Conflicting Posts</h4>
                <div>
                    ${conflictsHtml}
                </div>
            </div>
        `;
        
        this.openPanel();
    }
    
    renderRoleView() {
        const roleGroups = document.getElementById('role-groups');
        roleGroups.innerHTML = '';
        
        // Group posts by role
        const postsByRole = {};
        this.weekData.schedule.forEach(slot => {
            slot.posts.forEach(post => {
                const role = post.role || 'LEGACY';
                if (!postsByRole[role]) {
                    postsByRole[role] = [];
                }
                postsByRole[role].push({...post, day_name: slot.day_name, time: slot.time});
            });
        });
        
        // Add legacy posts (including conflicts)
        if (this.weekData.legacy_posts && this.weekData.legacy_posts.length > 0) {
            postsByRole['LEGACY'] = (postsByRole['LEGACY'] || []).concat(
                this.weekData.legacy_posts.map(p => ({...p, day_name: this.getDayName(p.scheduled_date)}))
            );
        }
        
        // Check for conflicts in legacy posts and add to Sunday slot if needed
        if (this.weekData.legacy_posts) {
            const conflicts = this.weekData.legacy_posts.filter(p => p.is_conflict);
            if (conflicts.length > 0) {
                // Find Sunday slot and add conflict indicator
                const sundaySlot = this.weekData.schedule.find(s => s.day === 6); // Sunday is day 6 (0-indexed)
                if (sundaySlot) {
                    // Add conflict flag to slot
                    sundaySlot.has_conflict = true;
                    sundaySlot.conflicts = conflicts;
                }
            }
        }
        
        // Render each role group
        const roleOrder = ['DEPTH_LONG', 'REASSURANCE', 'CULTURE', 'COMMERCE', 'AUTHORITY_SHORT', 'LEGACY'];
        
        roleOrder.forEach(role => {
            if (!postsByRole[role] || postsByRole[role].length === 0) {
                return;
            }
            
            const group = document.createElement('div');
            group.className = 'role-group';
            
            const roleClass = role.toLowerCase().replace('_', '-');
            
            group.innerHTML = `
                <div class="role-group-header">
                    <span class="role-badge ${roleClass}">${this.getRoleDisplayName(role)}</span>
                    <span class="role-group-count">${postsByRole[role].length} post(s)</span>
                </div>
                <div class="role-group-posts" id="role-posts-${role}"></div>
            `;
            
            const postsContainer = group.querySelector(`#role-posts-${role}`);
            
            postsByRole[role].forEach(post => {
                const postItem = document.createElement('div');
                postItem.className = 'role-post-item';
                postItem.innerHTML = `
                    <div>
                        <div class="post-day-time">${post.day_name} ${post.scheduled_time || ''}</div>
                        <div class="post-preview">${post.preview || 'No preview'}</div>
                        <div class="post-status">${this.getStatusDisplayName(post.status)}</div>
                    </div>
                    <button class="btn btn-secondary" onclick="controlBoard.showPostDetails(${post.id})">View</button>
                `;
                postsContainer.appendChild(postItem);
            });
            
            roleGroups.appendChild(group);
        });
        
        // Show role view, hide day view
        document.getElementById('day-view').style.display = 'none';
        document.getElementById('role-view').style.display = 'block';
    }
    
    switchView(mode) {
        this.viewMode = mode;
        
        // Update button states
        document.getElementById('btn-view-day').classList.toggle('active', mode === 'day');
        document.getElementById('btn-view-role').classList.toggle('active', mode === 'role');
        
        // Re-render
        this.render();
    }
    
    async showPostDetails(postId) {
        try {
            const response = await fetch(`/api/planning/content-control-board/post/${postId}`);
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to load post details');
            }
            
            this.renderPostDetails(data.post);
            this.openPanel();
            
        } catch (error) {
            console.error('Error loading post details:', error);
            alert('Error loading post details: ' + error.message);
        }
    }
    
    renderPostDetails(post) {
        const panelContent = document.getElementById('panel-content');
        const panelTitle = document.getElementById('panel-title');
        
        panelTitle.textContent = `Post #${post.id}`;
        
        const roleClass = post.role ? post.role.toLowerCase().replace('_', '-') : 'legacy';
        const validationReport = post.validation_report_json || {};
        const isValid = validationReport.valid !== false;
        const roleInfo = this.getRoleInfo(post.role);
        
        // v1.1: Simplified role section with link to reference
        const roleSection = post.role ? `
            <div class="panel-section">
                <h4>Role</h4>
                <div>
                    <a href="/planning/content-roles#${post.role.toLowerCase()}" class="role-badge-link">
                        <span class="role-badge ${roleClass}">${this.getRoleDisplayName(post.role)}</span>
                    </a>
                    <p style="margin-top: 0.5rem; font-size: 0.875rem;">
                        <a href="/planning/content-roles#${post.role.toLowerCase()}" style="color: var(--color-primary, #2563eb); text-decoration: underline;">
                            What this role does →
                        </a>
                    </p>
                </div>
            </div>
        ` : `
            <div class="panel-section">
                <h4>Role</h4>
                <div>
                    <span class="role-badge ${roleClass}">${this.getRoleDisplayName('LEGACY')}</span>
                </div>
            </div>
        `;
        
        // Phase 3.6: Angle section (if angle exists)
        const angleSection = post.angle_id ? `
            <div class="panel-section">
                <h4>Angle</h4>
                <div>
                    <p><strong>Name:</strong> ${post.angle_name || 'N/A'}</p>
                    ${post.angle_narrative_intent ? `<p style="font-size: 0.875rem; color: var(--color-text-light, #666); margin-top: 0.5rem;">${post.angle_narrative_intent}</p>` : ''}
                    ${post.angle_usage_count !== undefined ? `
                        <p style="font-size: 0.875rem; margin-top: 0.5rem;">
                            <strong>Usage:</strong> Used ${post.angle_usage_count} time(s)
                            ${post.angle_last_used_year && post.angle_last_used_week ? 
                                `, last used Week ${post.angle_last_used_week} of ${post.angle_last_used_year}` : ''}
                        </p>
                    ` : ''}
                </div>
            </div>
        ` : (post.role === 'DEPTH_LONG' ? `
            <div class="panel-section">
                <h4>Angle</h4>
                <div>
                    <p style="color: var(--color-text-light, #666); font-size: 0.875rem;">Not selected</p>
                </div>
            </div>
        ` : '');
        
        panelContent.innerHTML = `
            ${roleSection}
            
            ${angleSection}
            
            <div class="panel-section">
                <h4>Schedule</h4>
                <div>
                    <p><strong>Platform:</strong> ${post.platform || 'N/A'}</p>
                    <p><strong>Date:</strong> ${post.scheduled_date || 'Not scheduled'}</p>
                    <p><strong>Time:</strong> ${post.scheduled_time || 'N/A'}</p>
                </div>
            </div>
            
            ${post.topic_id ? `
            <div class="panel-section">
                <h4>Topic</h4>
                <div>
                    <p><strong>Name:</strong> ${post.topic_name || 'N/A'}</p>
                    ${post.topic_description ? `<p>${post.topic_description}</p>` : ''}
                </div>
            </div>
            ` : ''}
            
            ${post.source_page_id ? `
            <div class="panel-section">
                <h4>Source</h4>
                <div>
                    <p><strong>Article:</strong> ${post.source_article_name || `ID: ${post.source_page_id}`}</p>
                </div>
            </div>
            ` : ''}
            
            <div class="panel-section">
                <h4>Status</h4>
                <div>
                    <p><strong>Current:</strong> ${this.getStatusDisplayName(post.status)}</p>
                    ${post.approved_at ? `<p><strong>Approved:</strong> ${new Date(post.approved_at).toLocaleString()} by ${post.approved_by || 'system'}</p>` : ''}
                    <p><strong>Created:</strong> ${new Date(post.created_at).toLocaleString()}</p>
                </div>
            </div>
            
            ${validationReport.valid !== undefined ? `
            <div class="panel-section">
                <h4>Validation</h4>
                <div class="validation-report ${isValid ? 'valid' : 'invalid'}">
                    <p><strong>Status:</strong> ${isValid ? '✓ Valid' : '✗ Invalid'}</p>
                    ${validationReport.word_count ? `<p>Word count: ${validationReport.word_count}</p>` : ''}
                    ${validationReport.paragraph_count ? `<p>Paragraphs: ${validationReport.paragraph_count}</p>` : ''}
                    ${validationReport.issues && validationReport.issues.length > 0 ? `
                        <ul class="validation-issues">
                            ${validationReport.issues.map(issue => `<li>${issue}</li>`).join('')}
                        </ul>
                    ` : ''}
                </div>
            </div>
            ` : ''}
            
            <div class="panel-section">
                <h4>Content</h4>
                <div class="panel-content-text">${(post.generated_content || post.generated_caption || 'No content').replace(/\n/g, '<br>')}</div>
                ${post.id ? `
                <div style="margin-top: 0.5rem;">
                    <button class="btn btn-primary btn-sm" onclick="window.open('/preview/post/${post.id}?channel=${(post.platform || 'facebook').toLowerCase()}', '_blank', 'noopener')">
                        <i class="fas fa-eye"></i> Preview
                    </button>
                </div>
                ` : ''}
            </div>
        `;
    }
    
    openPanel() {
        document.getElementById('drill-down-panel').classList.add('open');
    }
    
    closePanel() {
        document.getElementById('drill-down-panel').classList.remove('open');
    }
    
    getRoleDisplayName(role) {
        // v1.1: Simplified display names
        const names = {
            'REASSURANCE': 'Human Service',
            'AUTHORITY_SHORT': 'Quiet Authority',
            'DEPTH_LONG': 'Deep Dive',
            'CULTURE': 'Cultural Detail',
            'COMMERCE': 'Product Spotlight',
            'LEGACY': 'Legacy'
        };
        return names[role] || role;
    }
    
    getStatusDisplayName(status) {
        const names = {
            'empty': 'Empty',
            'generated': 'Generated',
            'validated_fail': 'Validation Failed',
            'validated_pass': 'Validated',
            'approved': 'Approved',
            'scheduled': 'Scheduled',
            'published': 'Published',
            'ready': 'Ready',
            'pending': 'Pending'
        };
        return names[status] || status || 'Unknown';
    }
    
    getDayName(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        return days[date.getDay()];
    }
    
    getRoleInfo(role) {
        // v1.1: Shortened tooltips (one line only)
        const roleInfo = {
            'REASSURANCE': {
                tooltip: 'Human Service — reduce anxiety, signal approachability (Saturday)',
                shortDesc: 'Reduce anxiety and friction. Give people permission to engage comfortably.'
            },
            'AUTHORITY_SHORT': {
                tooltip: 'Quiet Authority — establish credibility through facts (future)',
                shortDesc: 'Establish quiet credibility through factual context or reframing.'
            },
            'DEPTH_LONG': {
                tooltip: 'Deep Dive — long-form expertise (Sunday)',
                shortDesc: 'Demonstrate embedded knowledge and judgement.'
            },
            'CULTURE': {
                tooltip: 'Cultural Detail — personality and rhythm (Mon/Wed/Fri)',
                shortDesc: 'Provide personality, rhythm, and familiarity.'
            },
            'COMMERCE': {
                tooltip: 'Product Spotlight — make products visible (Tue/Thu)',
                shortDesc: 'Make products visible and concrete.'
            },
            'LEGACY': {
                tooltip: 'Legacy post (created before Content Roles Framework)',
                shortDesc: 'Legacy post'
            }
        };
        
        return roleInfo[role] || { tooltip: role || 'Unknown role', shortDesc: '' };
    }
}

// Initialize when DOM is ready
let controlBoard;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        controlBoard = new ContentControlBoard();
    });
} else {
    controlBoard = new ContentControlBoard();
}
