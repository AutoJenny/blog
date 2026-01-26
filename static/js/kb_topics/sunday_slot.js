/**
 * Phase 2.6: Facebook Sunday DEPTH_LONG Slot UI
 * 
 * Minimal proof UI for generating and managing Sunday DEPTH_LONG posts.
 */

class SundaySlotManager {
    constructor() {
        this.currentPostId = null;
        this.currentYear = null;
        this.currentWeek = null;
        this.currentTopicId = null;
        this.currentSourceId = null;
        
        this.init();
    }
    
    init() {
        // Panel toggle
        const btnSunday = document.getElementById('btn-sunday-slot');
        const btnClose = document.getElementById('btn-close-sunday-panel');
        const panel = document.getElementById('sunday-slot-panel');
        
        if (btnSunday) {
            btnSunday.addEventListener('click', () => {
                panel.style.display = 'block';
                this.loadCurrentWeek();
            });
        }
        
        if (btnClose) {
            btnClose.addEventListener('click', () => {
                panel.style.display = 'none';
            });
        }
        
        // Week loader
        const btnLoadWeek = document.getElementById('btn-load-week');
        if (btnLoadWeek) {
            btnLoadWeek.addEventListener('click', () => {
                const year = parseInt(document.getElementById('sunday-week-year').value);
                const week = parseInt(document.getElementById('sunday-week-number').value);
                if (year && week) {
                    this.loadWeek(year, week);
                }
            });
        }
        
        // Topic selector
        const topicSelect = document.getElementById('sunday-topic-select');
        if (topicSelect) {
            topicSelect.addEventListener('change', (e) => {
                this.currentTopicId = parseInt(e.target.value);
                this.loadSourceArticles();
                this.updateGenerateButton();
            });
        }
        
        // Source selector
        const sourceSelect = document.getElementById('sunday-source-select');
        if (sourceSelect) {
            sourceSelect.addEventListener('change', (e) => {
                this.currentSourceId = parseInt(e.target.value);
                this.updateGenerateButton();
            });
        }
        
        // Action buttons
        const btnGenerate = document.getElementById('btn-generate-sunday');
        const btnRegenerate = document.getElementById('btn-regenerate-sunday');
        const btnApprove = document.getElementById('btn-approve-sunday');
        const btnSchedule = document.getElementById('btn-schedule-sunday');
        
        if (btnGenerate) {
            btnGenerate.addEventListener('click', () => this.generatePost());
        }
        if (btnRegenerate) {
            btnRegenerate.addEventListener('click', () => this.generatePost());
        }
        if (btnApprove) {
            btnApprove.addEventListener('click', () => this.approvePost());
        }
        if (btnSchedule) {
            btnSchedule.addEventListener('click', () => this.schedulePost());
        }
    }
    
    loadCurrentWeek() {
        const today = new Date();
        const year = today.getFullYear();
        const week = this.getISOWeek(today);
        
        document.getElementById('sunday-week-year').value = year;
        document.getElementById('sunday-week-number').value = week;
        
        this.loadWeek(year, week);
    }
    
    getISOWeek(date) {
        const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
        const dayNum = d.getUTCDay() || 7;
        d.setUTCDate(d.getUTCDate() + 4 - dayNum);
        const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
        return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
    }
    
    async loadWeek(year, week) {
        this.currentYear = year;
        this.currentWeek = week;
        
        // Check if rail exists
        try {
            const response = await fetch(`/api/content-roles/facebook/sunday/check?year=${year}&week=${week}`);
            const data = await response.json();
            
            if (!data.has_rail) {
                this.showError('No DEPTH_LONG rail configured for this week');
                return;
            }
        } catch (error) {
            console.error('Error checking rail:', error);
            this.showError('Error checking schedule rail');
            return;
        }
        
        // Load topics for this week
        await this.loadTopics();
        
        // Check if post already exists
        await this.checkExistingPost();
    }
    
    async loadTopics() {
        try {
            const response = await fetch('/api/kb-topics/topics');
            const data = await response.json();
            
            if (!data.success) {
                this.showError('Error loading topics');
                return;
            }
            
            const topicSelect = document.getElementById('sunday-topic-select');
            topicSelect.innerHTML = '<option value="">Select topic...</option>';
            
            // Get active topic for this week
            const rotaResponse = await fetch(`/api/kb-topics/rota?year=${this.currentYear}&week=${this.currentWeek}`);
            const rotaData = await rotaResponse.json();
            
            if (rotaData.success && rotaData.topic) {
                const topic = rotaData.topic;
                const option = document.createElement('option');
                option.value = topic.id;
                option.textContent = topic.topic_name;
                option.selected = true;
                topicSelect.appendChild(option);
                this.currentTopicId = topic.id;
            } else {
                // Add all active topics
                data.topics.forEach(topic => {
                    if (topic.is_active && !topic.is_excluded) {
                        const option = document.createElement('option');
                        option.value = topic.id;
                        option.textContent = topic.topic_name;
                        topicSelect.appendChild(option);
                    }
                });
            }
            
            await this.loadSourceArticles();
        } catch (error) {
            console.error('Error loading topics:', error);
            this.showError('Error loading topics');
        }
    }
    
    async loadSourceArticles() {
        if (!this.currentTopicId) {
            return;
        }
        
        try {
            // Get topic content to find source articles
            const response = await fetch(`/api/kb-topics/topic/${this.currentTopicId}/content`);
            const data = await response.json();
            
            if (!data.success || !data.content) {
                this.showError('Error loading source articles');
                return;
            }
            
            const sourceSelect = document.getElementById('sunday-source-select');
            sourceSelect.innerHTML = '<option value="">Select source article...</option>';
            
            // Get article details
            const articleIds = data.content.source_article_ids || [];
            for (const articleId of articleIds) {
                try {
                    const articleResponse = await fetch(`/kb/article/${articleId}`);
                    if (articleResponse.ok) {
                        const articleData = await articleResponse.json();
                        if (articleData && articleData.name) {
                            const option = document.createElement('option');
                            option.value = articleId;
                            option.textContent = articleData.name;
                            sourceSelect.appendChild(option);
                        }
                    }
                } catch (e) {
                    // Skip if article not found
                }
            }
            
            // Auto-select first article if only one
            if (articleIds.length === 1) {
                sourceSelect.value = articleIds[0];
                this.currentSourceId = articleIds[0];
            }
            
            this.updateGenerateButton();
        } catch (error) {
            console.error('Error loading source articles:', error);
            this.showError('Error loading source articles');
        }
    }
    
    updateGenerateButton() {
        const btnGenerate = document.getElementById('btn-generate-sunday');
        const canGenerate = this.currentTopicId && this.currentSourceId && this.currentYear && this.currentWeek;
        btnGenerate.disabled = !canGenerate;
    }
    
    async generatePost() {
        if (!this.currentTopicId || !this.currentSourceId || !this.currentYear || !this.currentWeek) {
            this.showError('Please select topic and source article');
            return;
        }
        
        const btnGenerate = document.getElementById('btn-generate-sunday');
        btnGenerate.disabled = true;
        btnGenerate.textContent = 'Generating...';
        
        try {
            const response = await fetch('/api/content-roles/facebook/sunday/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    topic_id: this.currentTopicId,
                    source_page_id: this.currentSourceId,
                    rota_year: this.currentYear,
                    rota_week: this.currentWeek
                })
            });
            
            const data = await response.json();
            
            if (!data.success) {
                this.showError(data.error || 'Generation failed');
                btnGenerate.disabled = false;
                btnGenerate.textContent = 'Generate';
                return;
            }
            
            this.currentPostId = data.post_id;
            this.showGeneratedContent(data);
            
            btnGenerate.style.display = 'none';
            document.getElementById('btn-regenerate-sunday').style.display = 'inline-block';
            
            if (data.validation.valid) {
                document.getElementById('btn-approve-sunday').style.display = 'inline-block';
                document.getElementById('btn-approve-sunday').disabled = false;
            }
            
        } catch (error) {
            console.error('Error generating post:', error);
            this.showError('Error generating post');
            btnGenerate.disabled = false;
            btnGenerate.textContent = 'Generate';
        }
    }
    
    showGeneratedContent(data) {
        const preview = document.getElementById('sunday-slot-preview');
        const content = document.getElementById('sunday-preview-content');
        const meta = document.getElementById('sunday-preview-meta');
        const validation = document.getElementById('sunday-validation-results');
        
        content.textContent = data.content;
        meta.innerHTML = `
            <div>Word count: ${data.word_count}</div>
            <div>Status: ${data.validation.valid ? '✓ Valid' : '✗ Invalid'}</div>
        `;
        
        if (data.validation.issues && data.validation.issues.length > 0) {
            validation.innerHTML = `
                <h5>Validation Issues:</h5>
                <ul>
                    ${data.validation.issues.map(issue => `<li>${issue}</li>`).join('')}
                </ul>
            `;
        } else {
            validation.innerHTML = '<div class="validation-pass">✓ All validation checks passed</div>';
        }
        
        preview.style.display = 'block';
    }
    
    async approvePost() {
        if (!this.currentPostId) {
            return;
        }
        
        try {
            const response = await fetch(`/api/content-roles/facebook/sunday/${this.currentPostId}/approve`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({approved_by: 'user'})
            });
            
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('btn-approve-sunday').disabled = true;
                document.getElementById('btn-approve-sunday').textContent = '✓ Approved';
                document.getElementById('btn-schedule-sunday').style.display = 'inline-block';
                document.getElementById('btn-schedule-sunday').disabled = false;
            } else {
                this.showError(data.error || 'Approval failed');
            }
        } catch (error) {
            console.error('Error approving post:', error);
            this.showError('Error approving post');
        }
    }
    
    async schedulePost() {
        if (!this.currentPostId) {
            return;
        }
        
        try {
            const response = await fetch(`/api/content-roles/facebook/sunday/${this.currentPostId}/schedule`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('btn-schedule-sunday').disabled = true;
                document.getElementById('btn-schedule-sunday').textContent = '✓ Scheduled';
                this.showSuccess(`Post scheduled for ${data.scheduled_date} at ${data.scheduled_time}`);
            } else {
                this.showError(data.error || 'Scheduling failed');
            }
        } catch (error) {
            console.error('Error scheduling post:', error);
            this.showError('Error scheduling post');
        }
    }
    
    async checkExistingPost() {
        // TODO: Check if post already exists for this week
        // This would query posting_queue for role='DEPTH_LONG', rota_year, rota_week
    }
    
    showError(message) {
        // Simple error display - can be enhanced
        alert(message);
    }
    
    showSuccess(message) {
        // Simple success display - can be enhanced
        alert(message);
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new SundaySlotManager();
    });
} else {
    new SundaySlotManager();
}
